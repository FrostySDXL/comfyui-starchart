import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = REPO_ROOT / "references" / "raw" / "server_endpoints.json"
OUTPUT_PATH = REPO_ROOT / "docs" / "reference" / "server-py-summary.md"


def _format_returns(returns: dict) -> str:
    if not isinstance(returns, dict):
        return str(returns)
    kind = returns.get("kind", "unknown")
    summary = returns.get("summary", "")
    parts = [f"**{kind}**"]
    if summary:
        parts.append(summary)
    return " — ".join(parts)


def _escape_cell(value: object) -> str:
    text = str(value)
    return text.replace("|", r"\|").replace("\n", " ")


def _format_fields(fields: list[dict]) -> str:
    names = [field.get("name", "") for field in fields if field.get("name")]
    return ", ".join(names) if names else "-"


def _format_notes(notes: list[str]) -> str:
    return " ".join(note.strip() for note in notes if note.strip()) or "-"


def _format_sources(sources: object) -> str:
    if isinstance(sources, list):
        cleaned = [str(source) for source in sources if str(source).strip()]
        return ", ".join(cleaned) if cleaned else "unknown"
    if isinstance(sources, str) and sources.strip():
        return sources
    return "unknown"


def build_markdown(data: dict) -> str:
    metadata = data.get("metadata", {})
    endpoints = data.get("endpoints", [])

    lines = [
        "# Server.py Summary",
        "",
        f"**Last Synced:** {metadata.get('extracted_date', 'unknown')}",
        f"**Source:** {_format_sources(metadata.get('sources'))}",
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

    lines.extend(
        [
            "",
            "## Response Summary",
            "",
            "| Route | Kind | Status Codes | Summary |",
            "| --- | --- | --- | --- |",
        ]
    )

    for endpoint in endpoints:
        returns = endpoint.get("returns", {})
        if isinstance(returns, dict):
            kind = returns.get("kind", "unknown")
            summary = returns.get("summary", "")
            status_codes = ", ".join(str(code) for code in returns.get("status_codes", [])) or "-"
        else:
            kind = "unknown"
            summary = str(returns)
            status_codes = "-"
        lines.append(
            f"| {_escape_cell(endpoint.get('route', ''))} | {_escape_cell(kind)} | {_escape_cell(status_codes)} | {_escape_cell(summary)} |"
        )

    detailed_endpoints = [
        endpoint for endpoint in endpoints
        if isinstance(endpoint.get("returns"), dict)
        and (
            endpoint["returns"].get("fields")
            or endpoint["returns"].get("notes")
        )
    ]

    if detailed_endpoints:
        lines.extend(
            [
                "",
                "## Structured Return Details",
                "",
                "| Route | Fields | Notes |",
                "| --- | --- | --- |",
            ]
        )
        for endpoint in detailed_endpoints:
            returns = endpoint["returns"]
            lines.append(
                f"| {_escape_cell(endpoint.get('route', ''))} | {_escape_cell(_format_fields(returns.get('fields', [])))} | {_escape_cell(_format_notes(returns.get('notes', [])))} |"
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
