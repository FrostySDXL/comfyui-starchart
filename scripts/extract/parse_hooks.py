import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from scripts.common.display_path import display_path
from scripts.common.path_normalization import normalize_repo_relative_path

REPO_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_PATH = REPO_ROOT / "references" / "raw" / "js_hooks.json"
INVOKE_RE = re.compile(r'invokeExtensions(Async)?\(\s*["\']([^"\']+)["\']')
HOOK_NAME_RE = re.compile(r"^\s*([A-Za-z0-9_]+)\?\(")
KNOWN_HOOKS = ["beforeRegisterNodeDef", "nodeCreated", "init", "setup"]

HOOK_COVERAGE = {
    "description": "Static extraction of documented and observed ComfyUI frontend extension hooks and declared extension fields.",
    "guaranteed_fields": [
        "hooks[].name",
        "hooks[].type",
        "hooks[].invoked_in",
        "extension_fields[].name",
        "extension_fields[].type_hint",
        "extension_fields[].required",
        "extension_fields[].defined_in",
        "extension_fields[].is_hook",
    ],
    "best_effort_fields": [
        "hooks[].description",
        "hooks[].defined_in",
        "hooks[].signature",
        "hooks[].arguments",
        "hooks[].return_type",
        "hooks[].invocation_style",
        "extension_fields[].description",
        "extension_fields[].traceability",
        "extension_fields[].is_index_signature",
    ],
    "deferred": [
        "unresolved hook definitions",
        "hooks referenced without nearby typed declarations",
    ],
}

MISSING_COMFY_EXTENSION_NOTE = "ComfyExtension interface not found"


def _split_signature_arguments(signature_text: str) -> list[str]:
    items = []
    current: list[str] = []
    depth = 0
    for char in signature_text:
        if char == "," and depth == 0:
            item = "".join(current).strip()
            if item:
                items.append(item)
            current = []
            continue
        if char in "([{<":
            depth += 1
        elif char in ")]}>" and depth > 0:
            depth -= 1
        current.append(char)
    item = "".join(current).strip()
    if item:
        items.append(item)
    return items


def _parse_hook_arguments(signature_text: str) -> list[dict]:
    arguments = []
    for item in _split_signature_arguments(signature_text):
        name, _, type_hint = item.partition(":")
        argument = {"name": name.strip()}
        if type_hint.strip():
            argument["type_hint"] = type_hint.strip()
        arguments.append(argument)
    return arguments


def _extract_typed_signature(lines: list[str], start_index: int) -> tuple[dict | None, int]:
    signature_lines: list[str] = []
    index = start_index
    paren_depth = 0
    while index < len(lines):
        candidate = lines[index]
        stripped = candidate.strip()
        if not stripped or stripped.startswith("//"):
            if signature_lines:
                break
            index += 1
            continue
        signature_lines.append(stripped)
        paren_depth += candidate.count("(") - candidate.count(")")
        combined = " ".join(signature_lines)
        if paren_depth <= 0 and "?" in combined and "):" in combined:
            match = re.match(r"^([A-Za-z0-9_]+)\?\((.*)\)\s*:\s*(.+)$", combined)
            if match:
                name, argument_text, return_type = match.groups()
                return {
                    "name": name,
                    "signature": combined,
                    "arguments": _parse_hook_arguments(argument_text.strip()),
                    "return_type": return_type.strip(),
                }, index + 1
            break
        index += 1
    return None, start_index


def _looks_like_known_hook_implementation(source_text: str, hook_name: str) -> bool:
    patterns = [
        rf"\b(?:async\s+)?{re.escape(hook_name)}\s*\(",
        rf"\b{re.escape(hook_name)}\s*:",
    ]
    return any(re.search(pattern, source_text) for pattern in patterns)


def clean_comment(block: str) -> str:
    lines = []
    for raw_line in block.splitlines():
        line = raw_line.strip()
        line = line.removeprefix("/**").removesuffix("*/").strip()
        if line.startswith("*"):
            line = line[1:].strip()
        if not line or line.startswith("@"):
            continue
        lines.append(line)
    return " ".join(lines)


def build_hook_coverage(extension_fields: list[dict]) -> dict:
    coverage = {
        "description": HOOK_COVERAGE["description"],
        "guaranteed_fields": list(HOOK_COVERAGE["guaranteed_fields"]),
        "best_effort_fields": list(HOOK_COVERAGE["best_effort_fields"]),
        "deferred": list(HOOK_COVERAGE["deferred"]),
    }
    if not extension_fields:
        coverage["deferred"].append(MISSING_COMFY_EXTENSION_NOTE)
    return coverage


def classify_hook(name: str) -> str:
    if name in {"init", "setup"}:
        return "app_lifecycle"
    if name in {"beforeRegisterNodeDef", "nodeCreated", "loadedGraphNode"}:
        return "node_lifecycle"
    if name in {"beforeConfigureGraph", "afterConfigureGraph"}:
        return "graph_lifecycle"
    if name in {"getCanvasMenuItems", "getNodeMenuItems", "getSelectionToolboxCommands"}:
        return "menu_extension"
    return "extension_api_method"


def extract_typed_hooks(source_text: str) -> list[dict]:
    hooks: list[dict] = []
    lines = source_text.splitlines()
    index = 0

    while index < len(lines):
        line = lines[index].strip()
        if line.startswith("/**"):
            comment_lines = [line]
            index += 1
            while index < len(lines):
                comment_lines.append(lines[index])
                if lines[index].strip().endswith("*/"):
                    index += 1
                    break
                index += 1

            while index < len(lines):
                candidate = lines[index]
                stripped = candidate.strip()
                if not stripped or stripped.startswith("//"):
                    index += 1
                    continue
                match = HOOK_NAME_RE.match(candidate)
                if match:
                    signature_data, next_index = _extract_typed_signature(lines, index)
                    if signature_data:
                        hooks.append(
                            {
                                **signature_data,
                                "description": clean_comment("\n".join(comment_lines)),
                            }
                        )
                        index = next_index
                break
            continue
        index += 1

    return hooks


def _extract_interface_body(source_text: str) -> str | None:
    match = re.search(r"\bexport\s+interface\s+ComfyExtension\b", source_text)
    if not match:
        return None

    open_index = source_text.find("{", match.end())
    if open_index == -1:
        raise ValueError("ComfyExtension interface block is missing an opening brace")

    depth = 0
    for index in range(open_index, len(source_text)):
        char = source_text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source_text[open_index + 1 : index]

    raise ValueError("ComfyExtension interface block is missing a closing brace")


def _normalize_type_hint(type_hint: str) -> str:
    return " ".join(type_hint.strip().split())


def _parse_method_field(declaration: str) -> tuple[str, bool, str] | None:
    match = re.match(r"^([A-Za-z0-9_]+)(\?)?\((.*)\)\s*:\s*(.+)$", declaration)
    if not match:
        return None
    name, optional, arguments, return_type = match.groups()
    return (
        name,
        optional != "?",
        f"({_normalize_type_hint(arguments)}) => {_normalize_type_hint(return_type)}",
    )


def _parse_property_field(declaration: str) -> tuple[str, bool, str, bool] | None:
    index_match = re.match(r"^\[([^\]]+)\]\s*:\s*(.+)$", declaration)
    if index_match:
        index_name, type_hint = index_match.groups()
        return f"[{_normalize_type_hint(index_name)}]", False, _normalize_type_hint(type_hint), True

    property_match = re.match(r"^([A-Za-z0-9_]+)(\?)?\s*:\s*(.+)$", declaration)
    if not property_match:
        return None
    name, optional, type_hint = property_match.groups()
    return name, optional != "?", _normalize_type_hint(type_hint), False


def _extract_extension_fields(comfy_types_text: str, source_path: str) -> list[dict]:
    interface_body = _extract_interface_body(comfy_types_text)
    if interface_body is None:
        return []

    fields: list[dict] = []
    lines = interface_body.splitlines()
    pending_comment: list[str] = []
    index = 0

    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped:
            index += 1
            continue

        if stripped.startswith("/**"):
            pending_comment = [stripped]
            index += 1
            while index < len(lines):
                pending_comment.append(lines[index])
                if lines[index].strip().endswith("*/"):
                    index += 1
                    break
                index += 1
            continue

        if stripped.startswith("//"):
            index += 1
            continue

        declaration_lines = [stripped.rstrip(";")]
        paren_depth = stripped.count("(") - stripped.count(")")
        while paren_depth > 0 and index + 1 < len(lines):
            index += 1
            next_line = lines[index].strip().rstrip(";")
            declaration_lines.append(next_line)
            paren_depth += next_line.count("(") - next_line.count(")")

        declaration = " ".join(part for part in declaration_lines if part)
        method = _parse_method_field(declaration)
        property_field = _parse_property_field(declaration) if method is None else None
        field_data = None
        if method:
            name, required, type_hint = method
            field_data = {
                "name": name,
                "type_hint": type_hint,
                "required": required,
            }
        elif property_field:
            name, required, type_hint, is_index_signature = property_field
            field_data = {
                "name": name,
                "type_hint": type_hint,
                "required": required,
            }
            if is_index_signature:
                field_data["is_index_signature"] = True

        if field_data:
            description = clean_comment("\n".join(pending_comment)) if pending_comment else ""
            field_data.update(
                {
                    "description": description,
                    "defined_in": source_path,
                    "traceability": {
                        "source_type": "source-backed",
                        "strategy": "comfy_extension_interface",
                    },
                }
            )
            fields.append(field_data)
        pending_comment = []
        index += 1

    return fields


def extract_extension_fields(source_map: dict[str, str], hook_names: set[str]) -> list[dict]:
    fields: list[dict] = []
    for source_path, source_text in source_map.items():
        source_fields = _extract_extension_fields(source_text, source_path)
        if source_fields:
            fields.extend(source_fields)

    for field in fields:
        field["is_hook"] = field["name"] in hook_names

    return fields


def extract_hooks(source_map: dict[str, str]) -> list[dict]:
    discovered: dict[str, dict] = {}

    for source_path, source_text in source_map.items():
        for hook_data in extract_typed_hooks(source_text):
            name = hook_data["name"]
            discovered.setdefault(
                name,
                {
                    "name": name,
                    "type": classify_hook(name),
                    "description": hook_data.get("description", ""),
                    "defined_in": source_path,
                    "invoked_in": [],
                    "signature": hook_data.get("signature"),
                    "arguments": hook_data.get("arguments", []),
                    "return_type": hook_data.get("return_type"),
                    "invocation_style": [],
                    "traceability": {
                        "source_type": "source-backed",
                        "strategy": "typed_definition",
                    },
                },
            )

    for source_path, source_text in source_map.items():
        for async_suffix, name in INVOKE_RE.findall(source_text):
            entry = discovered.setdefault(
                name,
                {
                    "name": name,
                    "type": classify_hook(name),
                    "description": "",
                    "defined_in": None,
                    "invoked_in": [],
                    "signature": None,
                    "arguments": [],
                    "return_type": None,
                    "invocation_style": [],
                    "traceability": {
                        "source_type": "source-backed",
                        "strategy": "invocation_only",
                    },
                },
            )
            if source_path not in entry["invoked_in"]:
                entry["invoked_in"].append(source_path)
            style = "async" if async_suffix else "sync"
            if style not in entry["invocation_style"]:
                entry["invocation_style"].append(style)

        for name in KNOWN_HOOKS:
            if _looks_like_known_hook_implementation(source_text, name):
                discovered.setdefault(
                    name,
                    {
                        "name": name,
                        "type": classify_hook(name),
                        "description": "",
                        "defined_in": None,
                        "invoked_in": [],
                        "signature": None,
                        "arguments": [],
                        "return_type": None,
                        "invocation_style": [],
                        "traceability": {
                            "source_type": "best-effort",
                            "strategy": "known_hook_fallback",
                        },
                    },
                )

    for hook in discovered.values():
        hook["invocation_style"] = sorted(hook.get("invocation_style", []))

    return [discovered[name] for name in sorted(discovered)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract ComfyUI frontend hooks to JSON")
    parser.add_argument("source_paths", nargs="*", help="Paths to pinned frontend source files")
    parser.add_argument("--version", default=None, help="Pinned upstream version or tag")
    parser.add_argument("--commit", default=None, help="Pinned upstream commit hash")
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="Output JSON path")
    args = parser.parse_args()

    if not args.source_paths:
        parser.print_usage()
        return 1

    source_paths = [Path(path) for path in args.source_paths]
    source_map = {
        normalize_repo_relative_path(source_path, REPO_ROOT): source_path.read_text(
            encoding="utf-8"
        )
        for source_path in source_paths
    }
    hooks = extract_hooks(source_map)
    extension_fields = extract_extension_fields(
        source_map, hook_names={hook["name"] for hook in hooks}
    )

    payload = {
        "metadata": {
            "sources": [normalize_repo_relative_path(path, REPO_ROOT) for path in source_paths],
            "extracted_date": datetime.now().strftime("%Y-%m-%d"),
            "version": args.version or "unversioned",
            "commit": args.commit,
        },
        "coverage": build_hook_coverage(extension_fields),
        "extension_fields": extension_fields,
        "hooks": hooks,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"Extracted {len(hooks)} hooks and {len(extension_fields)} extension fields "
        f"to {display_path(output_path)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
