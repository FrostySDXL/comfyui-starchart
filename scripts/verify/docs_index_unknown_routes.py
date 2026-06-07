#!/usr/bin/env python3
"""Advisory audit for unknown docs-index route classifications."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_INDEX_PATH = REPO_ROOT / "public" / "artifacts" / "docs-index.json"
UNKNOWN_AUDIT_THRESHOLD_PERCENT = 10


def _unknown_route_rows(docs_index: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for page in docs_index.get("pages", []):
        if not isinstance(page, dict):
            continue
        page_path = str(page.get("path", ""))
        source = str(page.get("route_classification_source", "unknown"))
        route_entries = page.get("related_route_entries", [])
        if not isinstance(route_entries, list):
            continue
        for route_entry in route_entries:
            if not isinstance(route_entry, dict):
                continue
            route_type = str(route_entry.get("route_type", "unknown"))
            reason = str(route_entry.get("route_classification_reason", "metadata_not_provided"))
            if route_type == "unknown" or source == "unknown":
                rows.append(
                    {
                        "page": page_path,
                        "route": str(route_entry.get("route", "")),
                        "route_type": route_type,
                        "route_classification_source": source,
                        "route_classification_reason": reason,
                    }
                )
    unique_rows = {tuple(row.items()): row for row in rows}
    return sorted(
        unique_rows.values(),
        key=lambda row: (
            row["route_classification_reason"],
            row["page"],
            row["route"],
        ),
    )


def _total_route_entries(docs_index: dict[str, Any]) -> int:
    total = 0
    for page in docs_index.get("pages", []):
        if isinstance(page, dict) and isinstance(page.get("related_route_entries"), list):
            total += len(page["related_route_entries"])
    return total


def build_unknown_routes_report(docs_index: dict[str, Any]) -> str:
    rows = _unknown_route_rows(docs_index)
    reason_counts = Counter(row["route_classification_reason"] for row in rows)
    count_text = ", ".join(f"{reason}: {count}" for reason, count in sorted(reason_counts.items()))
    lines = [f"reason_counts: {{{count_text}}}"]

    total_routes = _total_route_entries(docs_index)
    unknown_percent = (len(rows) / total_routes * 100) if total_routes else 0
    if unknown_percent > UNKNOWN_AUDIT_THRESHOLD_PERCENT:
        lines.append(
            "UNKNOWN ROUTE AUDIT THRESHOLD EXCEEDED: "
            f"{len(rows)} of {total_routes} related_route_entries are unknown "
            f"({unknown_percent:.1f}% > {UNKNOWN_AUDIT_THRESHOLD_PERCENT}%)."
        )

    if not rows:
        lines.append("No unknown route classifications found.")
    else:
        lines.append("unknown_routes:")
        for row in rows:
            lines.append(
                "  "
                + " | ".join(
                    [
                        row["page"],
                        row["route"],
                        row["route_type"],
                        row["route_classification_source"],
                        row["route_classification_reason"],
                    ]
                )
            )
    return "\n".join(lines) + "\n"


def run_audit(docs_index_path: Path = DOCS_INDEX_PATH) -> int:
    if not docs_index_path.exists():
        print(f"docs-index file is missing: {docs_index_path}")
        return 1
    try:
        docs_index = json.loads(docs_index_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"docs-index file is unreadable: {exc}")
        return 1
    print(build_unknown_routes_report(docs_index), end="")
    return 0


def main() -> int:
    return run_audit()


if __name__ == "__main__":
    raise SystemExit(main())
