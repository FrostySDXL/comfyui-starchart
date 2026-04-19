import argparse
import json
import re
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "references" / "raw" / "js_hooks.json"
INVOKE_RE = re.compile(r'invokeExtensions(?:Async)?\(\s*["\']([^"\']+)["\']')
KNOWN_HOOKS = ["beforeRegisterNodeDef", "nodeCreated", "init", "setup"]


def extract_hooks(source_text: str) -> list[dict]:
    discovered: dict[str, dict] = {}

    for name in INVOKE_RE.findall(source_text):
        discovered[name] = {
            "name": name,
            "type": "invokeExtensions",
            "description": "TODO: extracted hook",
            "parameters": [],
            "example_use": "TODO",
        }

    for name in KNOWN_HOOKS:
        if re.search(rf'\b{name}\b', source_text):
            discovered.setdefault(
                name,
                {
                    "name": name,
                    "type": "lifecycle",
                    "description": "TODO: extracted hook",
                    "parameters": [],
                    "example_use": "TODO",
                },
            )

    return [discovered[name] for name in sorted(discovered)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract ComfyUI frontend hooks to JSON")
    parser.add_argument("app_path", nargs="?", help="Path to ComfyUI web/app.js")
    args = parser.parse_args()

    if not args.app_path:
        parser.print_usage()
        return 1

    source_path = Path(args.app_path)
    source_text = source_path.read_text(encoding="utf-8")
    hooks = extract_hooks(source_text)

    payload = {
        "metadata": {
            "source": str(source_path),
            "extracted_date": datetime.now().strftime("%Y-%m-%d"),
            "version": "1.0.0",
        },
        "hooks": hooks,
    }

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {len(hooks)} hooks to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
