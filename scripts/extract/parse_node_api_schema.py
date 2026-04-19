import argparse
import json
import re
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "references" / "raw" / "node_api_schema.json"

OBJECT_INFO_FIELD_RE = re.compile(r"info\['([^']+)'\]")
COMFYTYPE_RE = re.compile(
    r'@comfytype\(io_type="([^"]+)"\)\s+class\s+(\w+)\([^)]*\):',
    re.MULTILINE,
)
INPUT_CLASS_RE = re.compile(r"class\s+Input\(([^)]+)\):")
INPUT_INIT_RE = re.compile(r"def\s+__init__\((.*?)\):", re.DOTALL)
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
    compact = " ".join(signature_text.replace("\n", " ").split())
    names: list[str] = []
    for chunk in compact.split(","):
        item = chunk.strip()
        if not item or item in {"self", "cls"}:
            continue
        if item.startswith("*"):
            continue
        name = item.split(":", 1)[0].split("=", 1)[0].strip()
        if name in {"self", "cls", "id"} or not name:
            continue
        names.append(name)
    return names


def extract_io_types(io_text: str) -> list[dict]:
    matches = list(COMFYTYPE_RE.finditer(io_text))
    results: list[dict] = []

    for index, match in enumerate(matches):
        io_type, class_name = match.groups()
        block_start = match.start()
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(io_text)
        block = io_text[block_start:block_end]

        input_class_match = INPUT_CLASS_RE.search(block)
        input_class = input_class_match.group(1) if input_class_match else None

        input_params: list[str] = []
        init_match = INPUT_INIT_RE.search(block)
        if init_match:
            input_params = parse_parameters(init_match.group(1))

        results.append(
            {
                "io_type": io_type,
                "class_name": class_name,
                "input_class": input_class,
                "input_parameters": input_params,
            }
        )

    return results


def extract_basic_input_shapes(basic_types_text: str) -> dict[str, str]:
    return {
        name: " ".join(description.split())
        for name, description in SIMPLE_SHAPE_RE.findall(basic_types_text)
    }


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

    payload = {
        "metadata": {
            "sources": [str(server_path), str(io_path), str(basic_types_path)],
            "extracted_date": datetime.now().strftime("%Y-%m-%d"),
            "version": args.version or "unversioned",
            "commit": args.commit,
        },
        "object_info_fields": extract_object_info_fields(server_text),
        "io_types": extract_io_types(io_text),
        "basic_input_shapes": extract_basic_input_shapes(basic_types_text),
    }

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted node API schema to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
