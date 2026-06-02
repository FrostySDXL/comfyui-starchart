import argparse
import ast
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.common.display_path import display_path
from scripts.common.path_normalization import normalize_repo_relative_path

REPO_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_PATH = REPO_ROOT / "references" / "raw" / "node_api_schema.json"

OBJECT_INFO_FIELD_RE = re.compile(r"info\['([^']+)'\]")
COMFYTYPE_RE = re.compile(
    r'@comfytype\(io_type="([^"]+)"\)\s+class\s+(\w+)\(([^)]*)\):',
    re.MULTILINE,
)
INPUT_CLASS_RE = re.compile(r"class\s+Input\(([^)]+)\):")
INPUT_INIT_RE = re.compile(r"def\s+__init__\((.*?)\):", re.DOTALL)
OUTPUT_CLASS_RE = re.compile(r"class\s+Output\((?:Output)?\):")
OUTPUT_INIT_RE = re.compile(r"def\s+__init__\((.*?)\):", re.DOTALL)
SIMPLE_SHAPE_RE = re.compile(r'^(\w+Input)\s*=.*?\n"""\s*(.*?)\s*"""', re.MULTILINE | re.DOTALL)


def extract_object_info_fields(server_text: str) -> list[str]:
    node_info_match = re.search(
        r"def\s+node_info\(node_class\):(?P<body>.*?)(?:\n\s*@routes\.get\(|\n\s*return\s+info)",
        server_text,
        re.DOTALL,
    )
    target_text = node_info_match.group("body") if node_info_match else server_text
    fields: list[str] = []
    seen: set[str] = set()
    for field in OBJECT_INFO_FIELD_RE.findall(target_text):
        if field not in seen:
            seen.add(field)
            fields.append(field)
    return fields


def parse_parameters(signature_text: str) -> list[str]:
    """Parse parameter names from a function signature, respecting bracket nesting.

    Handles type hints like Dict[str, List[float]] by not splitting on
    commas inside brackets.
    """
    compact = " ".join(signature_text.replace("\n", " ").split())
    names: list[str] = []
    depth = 0
    current: list[str] = []
    for char in compact:
        if char == "," and depth == 0:
            item = "".join(current).strip()
            current = []
            if not item or item in {"self", "cls"}:
                continue
            if item.startswith("*"):
                continue
            name = item.split(":", 1)[0].split("=", 1)[0].strip()
            if name in {"self", "cls", "id"} or not name:
                continue
            names.append(name)
        else:
            if char in "([{":
                depth += 1
            elif char in ")]}":
                depth -= 1
            current.append(char)
    # Handle final item
    item = "".join(current).strip()
    if item and item not in {"self", "cls"} and not item.startswith("*"):
        name = item.split(":", 1)[0].split("=", 1)[0].strip()
        if name not in {"self", "cls", "id"} and name:
            names.append(name)
    return names


def parse_parameter_details(signature_text: str) -> list[dict]:
    """Parse parameter details from a Python signature."""
    compact = " ".join(signature_text.replace("\n", " ").split())
    details: list[dict] = []
    depth = 0
    current: list[str] = []

    def flush(item_text: str) -> None:
        item = item_text.strip()
        if not item or item in {"self", "cls"} or item.startswith("*"):
            return
        name_part, sep, remainder = item.partition(":")
        name = name_part.split("=", 1)[0].strip()
        if name in {"self", "cls", "id"} or not name:
            return

        type_hint = None
        default = None
        literal_values = None
        if sep:
            type_part, default_sep, default_part = remainder.partition("=")
            type_hint = type_part.strip() or None
            if default_sep:
                try:
                    default = ast.literal_eval(default_part.strip())
                except (SyntaxError, ValueError):
                    default = default_part.strip()
        else:
            _name_only, default_sep, default_part = item.partition("=")
            if default_sep:
                try:
                    default = ast.literal_eval(default_part.strip())
                except (SyntaxError, ValueError):
                    default = default_part.strip()

        if type_hint:
            literal_match = re.search(r"Literal\[(.*)\]", type_hint)
            if literal_match:
                literal_values = []
                for value_text in [part.strip() for part in literal_match.group(1).split(",")]:
                    try:
                        literal_values.append(ast.literal_eval(value_text))
                    except (SyntaxError, ValueError):
                        literal_values.append(value_text)

        detail = {
            "name": name,
            "location": "python_signature",
            "traceability": {
                "source_type": "source-backed",
                "strategy": "python_signature",
            },
        }
        if type_hint:
            detail["type_hint"] = type_hint
        if default is not None:
            detail["default"] = default
        if literal_values:
            detail["allowed_values"] = literal_values
        details.append(detail)

    for char in compact:
        if char == "," and depth == 0:
            flush("".join(current))
            current = []
            continue
        if char in "([{":
            depth += 1
        elif char in ")]}" and depth > 0:
            depth -= 1
        current.append(char)

    flush("".join(current))
    return details


def _extract_nested_class_block(block: str, class_name: str) -> str | None:
    lines = block.splitlines()
    class_index = None
    class_indent = None

    for index, line in enumerate(lines):
        match = re.match(rf"^(\s*)class\s+{re.escape(class_name)}\([^)]*\):", line)
        if match:
            class_index = index
            class_indent = len(match.group(1))
            break

    if class_index is None or class_indent is None:
        return None

    collected = [lines[class_index]]
    for line in lines[class_index + 1 :]:
        if not line.strip():
            collected.append(line)
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= class_indent:
            break
        collected.append(line)

    return "\n".join(collected)


def _strip_inline_comment(value: str) -> str:
    return value.split("#", 1)[0].rstrip()


def _extract_class_level_type_hint(block: str) -> str | None:
    lines = block.splitlines()
    visible_lines: list[str] = []
    skip_indent: int | None = None

    for line in lines[1:]:
        if not line.strip():
            if skip_indent is None:
                visible_lines.append(line)
            continue

        indent = len(line) - len(line.lstrip())
        if skip_indent is not None:
            if indent > skip_indent:
                continue
            skip_indent = None

        if re.match(r"^\s+class\s+\w+", line):
            skip_indent = indent
            continue

        visible_lines.append(line)

    for line in visible_lines:
        match = re.match(r"^\s+Type\s*=\s*(.+)$", line)
        if match:
            type_hint = _strip_inline_comment(match.group(1).strip())
            return type_hint or None

    return None


def extract_io_types(io_text: str, io_path: str) -> list[dict]:
    matches = list(COMFYTYPE_RE.finditer(io_text))
    blocks_by_class_name: dict[str, tuple[str, list[str]]] = {}

    for index, match in enumerate(matches):
        _io_type, class_name, base_classes = match.groups()
        block_start = match.start()
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(io_text)
        block = io_text[block_start:block_end]
        bases = [base.strip() for base in base_classes.split(",") if base.strip()]
        blocks_by_class_name[class_name] = (block, bases)

    type_hint_cache: dict[str, str | None] = {}

    def resolve_type_hint(class_name: str, seen: set[str] | None = None) -> str | None:
        if class_name in type_hint_cache:
            return type_hint_cache[class_name]

        entry = blocks_by_class_name.get(class_name)
        if entry is None:
            return None

        block, base_classes = entry
        direct_type_hint = _extract_class_level_type_hint(block)
        if direct_type_hint is not None:
            type_hint_cache[class_name] = direct_type_hint
            return direct_type_hint

        seen = seen or set()
        if class_name in seen:
            type_hint_cache[class_name] = None
            return None
        seen.add(class_name)

        for base_class in base_classes:
            inherited = resolve_type_hint(base_class, seen)
            if inherited is not None:
                type_hint_cache[class_name] = inherited
                return inherited

        type_hint_cache[class_name] = None
        return None

    results: list[dict] = []

    for index, match in enumerate(matches):
        io_type, class_name, _base_classes = match.groups()
        block_start = match.start()
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(io_text)
        block = io_text[block_start:block_end]

        input_class_match = INPUT_CLASS_RE.search(block)
        input_class = input_class_match.group(1) if input_class_match else None

        input_params: list[str] = []
        input_parameter_details: list[dict] = []
        input_block = _extract_nested_class_block(block, "Input")
        init_match = INPUT_INIT_RE.search(input_block) if input_block else None
        if init_match:
            input_parameter_details = parse_parameter_details(init_match.group(1))
            input_params = [detail["name"] for detail in input_parameter_details]

        output_params: list[str] = []
        output_parameter_details: list[dict] = []
        output_class_match = OUTPUT_CLASS_RE.search(block)
        if output_class_match:
            output_block = (
                _extract_nested_class_block(block, "Output") or block[output_class_match.start() :]
            )
            output_init_match = OUTPUT_INIT_RE.search(output_block)
            if output_init_match:
                output_parameter_details = parse_parameter_details(output_init_match.group(1))
                output_params = [detail["name"] for detail in output_parameter_details]

        type_hint = resolve_type_hint(class_name)

        is_widget = False
        if input_class:
            is_widget = input_class == "WidgetInput" or input_class == "Combo.Input"

        results.append(
            {
                "io_type": io_type,
                "class_name": class_name,
                "input_class": input_class,
                "input_parameters": input_params,
                "output_parameters": output_params,
                "input_parameter_details": input_parameter_details,
                "output_parameter_details": output_parameter_details,
                "type_hint": type_hint,
                "defined_in": normalize_repo_relative_path(io_path, REPO_ROOT),
                "is_widget": is_widget,
            }
        )

    return results


def _runtime_input_type(value: object) -> list[str]:
    if isinstance(value, (list, tuple)) and value:
        return [str(value[0])]
    if isinstance(value, str):
        return [value]
    return []


def _runtime_input_types(node_info: dict) -> dict[str, list[str]]:
    input_info = node_info.get("input", {})
    if not isinstance(input_info, dict):
        return {}

    result: dict[str, list[str]] = {}
    for section_name in ["required", "optional", "hidden"]:
        section = input_info.get(section_name, {})
        if not isinstance(section, dict):
            continue
        for input_name, input_value in section.items():
            result[input_name] = _runtime_input_type(input_value)
    return result


def build_prompt_conditioning_surface(
    io_types: list[dict], runtime_object_info: dict | None = None
) -> dict:
    text_input_io_types = []
    conditioning_io_types = []

    for entry in io_types:
        io_type = entry.get("io_type")
        item = {
            "io_type": io_type,
            "class_name": entry.get("class_name"),
            "type_hint": entry.get("type_hint"),
            "is_widget": entry.get("is_widget"),
            "input_parameters": entry.get("input_parameters", []),
            "output_parameters": entry.get("output_parameters", []),
            "defined_in": entry.get("defined_in"),
        }
        if io_type == "STRING":
            item["supports_multiline_parameter"] = "multiline" in item["input_parameters"]
            text_input_io_types.append(item)
        if io_type == "CONDITIONING":
            conditioning_item = dict(item)
            conditioning_io_types.append(conditioning_item)

    runtime_node_output_summary = []
    if runtime_object_info:
        for class_name in sorted(runtime_object_info):
            node_info = runtime_object_info[class_name]
            if not isinstance(node_info, dict):
                continue
            input_types = _runtime_input_types(node_info)
            output_types = node_info.get("output", [])
            if not isinstance(output_types, list):
                output_types = []
            output_types = [str(output_type) for output_type in output_types]
            runtime_node_output_summary.append(
                {
                    "class_name": class_name,
                    "input_names": sorted(input_types),
                    "input_types": {name: input_types[name] for name in sorted(input_types)},
                    "output_types": output_types,
                    "output_includes_conditioning": "CONDITIONING" in output_types,
                }
            )

    return {
        "traceability": {
            "source_type": "source-backed",
            "strategy": "derived_from_io_type_definitions",
            "runtime_bounded_sections": ["runtime_node_output_summary"]
            if runtime_object_info
            else [],
        },
        "text_input_io_types": text_input_io_types,
        "conditioning_io_types": conditioning_io_types,
        "runtime_node_output_summary": runtime_node_output_summary,
    }


def extract_basic_input_shapes(basic_types_text: str) -> dict[str, str]:
    return {
        name: " ".join(description.split())
        for name, description in SIMPLE_SHAPE_RE.findall(basic_types_text)
    }


def extract_typed_input_shapes(basic_types_text: str, basic_types_path: str) -> dict[str, dict]:
    """Extract TypedDict classes with their fields and descriptions."""
    result: dict[str, dict] = {}
    lines = basic_types_text.splitlines()
    i = 0
    while i < len(lines):
        match = re.match(r"class\s+(\w+)\(TypedDict\):", lines[i])
        if match:
            name = match.group(1)
            i += 1
            description = ""
            if i < len(lines) and '"""' in lines[i]:
                doc_lines = []
                i += 1
                while i < len(lines) and '"""' not in lines[i]:
                    doc_lines.append(lines[i].strip())
                    i += 1
                description = " ".join(doc_lines)
                i += 1

            fields: dict[str, dict] = {}
            while i < len(lines):
                line = lines[i]
                if not line.strip():
                    i += 1
                    continue
                indent = len(line) - len(line.lstrip())
                if indent == 0:
                    break
                field_match = re.match(r"\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*([^#\n]+)", line)
                if field_match:
                    field_name = field_match.group(1)
                    type_hint = field_match.group(2).strip()
                    i += 1
                    field_doc = ""
                    if i < len(lines) and '"""' in lines[i]:
                        i += 1
                        field_doc_lines = []
                        while i < len(lines) and '"""' not in lines[i]:
                            field_doc_lines.append(lines[i].strip())
                            i += 1
                        field_doc = " ".join(field_doc_lines)
                        i += 1
                    fields[field_name] = {"type": type_hint}
                    if field_doc:
                        fields[field_name]["description"] = field_doc
                    fields[field_name]["traceability"] = {
                        "source_type": "source-backed",
                        "strategy": "typed_dict_field",
                    }
                else:
                    i += 1

            result[name] = {
                "description": description,
                "defined_in": normalize_repo_relative_path(basic_types_path, REPO_ROOT),
                "fields": fields,
            }
        else:
            i += 1
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract ComfyUI node API and object_info schema details to JSON"
    )
    parser.add_argument("server_path", nargs="?", help="Path to pinned ComfyUI server.py")
    parser.add_argument("io_path", nargs="?", help="Path to pinned comfy_api latest _io.py")
    parser.add_argument(
        "basic_types_path",
        nargs="?",
        help="Path to pinned comfy_api latest basic_types.py",
    )
    parser.add_argument("--version", default=None, help="Pinned upstream version or tag")
    parser.add_argument("--commit", default=None, help="Pinned upstream commit hash")
    parser.add_argument(
        "--object-info-runtime-path",
        default=None,
        help="Optional path to a runtime object_info snapshot to merge into the schema",
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_PATH),
        help="Output JSON path",
    )
    args = parser.parse_args()

    if not args.server_path or not args.io_path or not args.basic_types_path:
        parser.print_usage()
        return 1

    server_path = Path(args.server_path)
    io_path = Path(args.io_path)
    basic_types_path = Path(args.basic_types_path)

    server_text = server_path.read_text(encoding="utf-8")
    io_text = io_path.read_text(encoding="utf-8")
    basic_types_text = basic_types_path.read_text(encoding="utf-8")

    runtime_snapshot = None
    if args.object_info_runtime_path:
        runtime_path = Path(args.object_info_runtime_path)
        if runtime_path.exists():
            runtime_snapshot = json.loads(runtime_path.read_text(encoding="utf-8"))
        else:
            print(
                f"WARNING: runtime snapshot not found at {display_path(runtime_path)}",
                file=sys.stderr,
            )

    source_sections = [
        "object_info_fields",
        "io_types",
        "basic_input_shapes",
        "typed_input_shapes",
        "prompt_conditioning_surface",
    ]
    runtime_sections = []
    if runtime_snapshot:
        runtime_sections.append("runtime_object_info")

    mode = "hybrid" if runtime_snapshot else "source-only"

    io_types = extract_io_types(io_text, str(io_path))
    runtime_object_info = runtime_snapshot.get("object_info", {}) if runtime_snapshot else None

    payload: dict[str, Any] = {
        "metadata": {
            "sources": [
                normalize_repo_relative_path(p, REPO_ROOT)
                for p in [server_path, io_path, basic_types_path]
            ],
            "extracted_date": datetime.now().strftime("%Y-%m-%d"),
            "version": args.version or "unversioned",
            "commit": args.commit,
            "provenance": {
                "mode": mode,
                "source_sections": source_sections,
                "runtime_sections": runtime_sections,
            },
        },
        "object_info_fields": extract_object_info_fields(server_text),
        "io_types": io_types,
        "prompt_conditioning_surface": build_prompt_conditioning_surface(
            io_types, runtime_object_info
        ),
        "basic_input_shapes": extract_basic_input_shapes(basic_types_text),
        "typed_input_shapes": extract_typed_input_shapes(basic_types_text, str(basic_types_path)),
        "coverage": {
            "description": (
                "Extracted from pinned source files with runtime /object_info enrichment."
                if runtime_snapshot
                else "Extracted from pinned source files only. "
                "Runtime-only data such as per-node INPUT_TYPES schemas and custom node types are deferred beyond pinned-snapshot extraction."
            ),
            "sources_covered": [
                normalize_repo_relative_path(server_path, REPO_ROOT),
                normalize_repo_relative_path(io_path, REPO_ROOT),
                normalize_repo_relative_path(basic_types_path, REPO_ROOT),
            ],
            "runtime_enriched": bool(runtime_snapshot),
            "guaranteed_fields": [
                "metadata",
                "object_info_fields",
                "io_types",
                "basic_input_shapes",
                "coverage",
            ],
            "best_effort_fields": [
                "typed_input_shapes",
                "prompt_conditioning_surface.text_input_io_types",
                "prompt_conditioning_surface.conditioning_io_types",
                "prompt_conditioning_surface.runtime_node_output_summary",
            ],
            "deferred": [
                "custom node definitions",
                "per-node INPUT_TYPES schemas",
            ]
            if runtime_snapshot
            else [
                "runtime /object_info response",
                "custom node definitions",
                "per-node INPUT_TYPES schemas",
            ],
        },
    }

    if runtime_snapshot:
        payload["runtime_object_info"] = runtime_object_info

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted node API schema to {display_path(output_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
