import argparse
import json
import re
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "references" / "raw" / "server_endpoints.json"
DECORATOR_RE = re.compile(r'@routes\.(route|get|post|ws)\(\s*["\']([^"\']+)["\']')
DOCSTRING_RE = re.compile(r'\s*[rubfRUBF]*(["\']{3})(.*?)\1', re.DOTALL)


def extract_endpoints(source_text: str) -> list[dict]:
    lines = source_text.splitlines()
    endpoints: list[dict] = []

    for index, line in enumerate(lines):
        match = DECORATOR_RE.search(line)
        if not match:
            continue

        decorator_kind, route = match.groups()
        method = decorator_kind.upper() if decorator_kind != "route" else "ROUTE"
        lookahead = "\n".join(lines[index + 1 : index + 12])
        doc_match = DOCSTRING_RE.search(lookahead)
        description = ""
        if doc_match:
            description = " ".join(doc_match.group(2).strip().split())

        endpoints.append(
            {
                "route": route,
                "method": method,
                "description": description,
                "parameters": [],
                "returns": "TODO",
            }
        )

    return endpoints


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract ComfyUI server routes to JSON")
    parser.add_argument("server_path", nargs="?", help="Path to ComfyUI server.py")
    args = parser.parse_args()

    if not args.server_path:
        parser.print_usage()
        return 1

    source_path = Path(args.server_path)
    source_text = source_path.read_text(encoding="utf-8")
    endpoints = extract_endpoints(source_text)

    payload = {
        "metadata": {
            "source": str(source_path),
            "extracted_date": datetime.now().strftime("%Y-%m-%d"),
            "version": "1.0.0",
        },
        "endpoints": endpoints,
    }

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {len(endpoints)} endpoints to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
