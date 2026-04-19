import argparse
import json
import re
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "references" / "raw" / "js_hooks.json"
INVOKE_RE = re.compile(r'invokeExtensions(?:Async)?\(\s*["\']([^"\']+)["\']')
HOOK_NAME_RE = re.compile(r'^\s*([A-Za-z0-9_]+)\?\(')
KNOWN_HOOKS = ["beforeRegisterNodeDef", "nodeCreated", "init", "setup"]


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


def extract_typed_hooks(source_text: str) -> list[tuple[str, str]]:
    hooks: list[tuple[str, str]] = []
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
                    hooks.append((match.group(1), clean_comment("\n".join(comment_lines))))
                break
            continue
        index += 1

    return hooks


def extract_hooks(source_map: dict[str, str]) -> list[dict]:
    discovered: dict[str, dict] = {}

    for source_path, source_text in source_map.items():
        for name, description in extract_typed_hooks(source_text):
            discovered.setdefault(
                name,
                {
                    "name": name,
                    "type": classify_hook(name),
                    "description": description,
                    "defined_in": source_path,
                    "invoked_in": [],
                },
            )

    for source_path, source_text in source_map.items():
        for name in INVOKE_RE.findall(source_text):
            entry = discovered.setdefault(
                name,
                {
                    "name": name,
                    "type": classify_hook(name),
                    "description": "",
                    "defined_in": None,
                    "invoked_in": [],
                },
            )
            if source_path not in entry["invoked_in"]:
                entry["invoked_in"].append(source_path)

        for name in KNOWN_HOOKS:
            if re.search(rf'\b{name}\b', source_text):
                discovered.setdefault(
                    name,
                    {
                        "name": name,
                        "type": classify_hook(name),
                        "description": "",
                        "defined_in": None,
                        "invoked_in": [],
                    },
                )

    return [discovered[name] for name in sorted(discovered)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract ComfyUI frontend hooks to JSON")
    parser.add_argument("source_paths", nargs="*", help="Paths to pinned frontend source files")
    parser.add_argument("--version", default=None, help="Pinned upstream version or tag")
    parser.add_argument("--commit", default=None, help="Pinned upstream commit hash")
    args = parser.parse_args()

    if not args.source_paths:
        parser.print_usage()
        return 1

    source_paths = [Path(path) for path in args.source_paths]
    source_map = {
        str(source_path): source_path.read_text(encoding="utf-8")
        for source_path in source_paths
    }
    hooks = extract_hooks(source_map)

    payload = {
        "metadata": {
            "sources": [str(path) for path in source_paths],
            "extracted_date": datetime.now().strftime("%Y-%m-%d"),
            "version": args.version or "unversioned",
            "commit": args.commit,
        },
        "hooks": hooks,
    }

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {len(hooks)} hooks to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
