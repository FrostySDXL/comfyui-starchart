import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = REPO_ROOT / "references" / "raw" / "server_endpoints.json"
OUTPUT_PATH = REPO_ROOT / "docs" / "reference" / "server-py-summary.md"


def build_markdown(data: dict) -> str:
    metadata = data.get("metadata", {})
    endpoints = data.get("endpoints", [])

    lines = [
        "# Server.py Summary",
        "",
        f"**Last Synced:** {metadata.get('extracted_date', 'unknown')}",
        f"**Source:** {metadata.get('source', 'unknown')}",
        "",
        "## Overview",
        "",
    ]

    if not endpoints:
        lines.extend(
            [
                "No extracted endpoints are available yet.",
                "",
                "Run `python scripts/extract/parse_server.py path/to/server.py` to populate this page.",
            ]
        )
        return "\n".join(lines) + "\n"

    lines.extend(
        [
            "Generated from `references/raw/server_endpoints.json`.",
            "",
            "## Route Summary",
            "",
            "| Method | Route | Description |",
            "| --- | --- | --- |",
        ]
    )

    for endpoint in endpoints:
        lines.append(
            f"| {endpoint.get('method', '')} | {endpoint.get('route', '')} | {endpoint.get('description', '')} |"
        )

    lines.extend(["", "## Update Process", "", "Regenerate this page after refreshing endpoint JSON."])
    return "\n".join(lines) + "\n"


def main() -> int:
    data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    OUTPUT_PATH.write_text(build_markdown(data), encoding="utf-8")
    print("Generated reference pages from JSON")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
