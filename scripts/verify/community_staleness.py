#!/usr/bin/env python3
"""Flag stale community metadata entries.

Checks ecosystem_packages.json and community_pages.json for entries whose
needs_review_after date has passed relative to today.

Usage:
    python scripts/verify/community_staleness.py

Exits 0 when nothing is stale, exits 1 with a report when stale entries exist.
"""

import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMUNITY_DIR = REPO_ROOT / "references" / "community"

TODAY = date.today()


def _parse_date(value: str) -> date:
    """Parse an ISO date string (YYYY-MM-DD)."""
    year, month, day = value.split("-")
    return date(int(year), int(month), int(day))


def check_stale(data: dict, filename: str, entry_key: str) -> list[str]:
    """Check entries for stale review dates."""
    stale = []
    entries = data.get(entry_key, [])
    for i, entry in enumerate(entries):
        needs_review = entry.get("needs_review_after", "")
        name = entry.get("name") or entry.get("page_path") or f"entry[{i}]"
        if needs_review:
            try:
                review_date = _parse_date(needs_review)
                if review_date < TODAY:
                    stale.append(f"{filename}: {name} (needs review after {needs_review})")
            except ValueError:
                stale.append(
                    f"{filename}: {name} has invalid needs_review_after date '{needs_review}'"
                )
    return stale


def main() -> int:
    stale_entries = []
    parse_errors = []
    json_files = sorted(COMMUNITY_DIR.glob("*.json"))

    for json_file in json_files:
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            parse_errors.append(f"{json_file.name}: invalid JSON: {e}")
            continue

        if json_file.name == "ecosystem_packages.json":
            stale_entries.extend(check_stale(data, json_file.name, "packages"))
        elif json_file.name == "community_pages.json":
            stale_entries.extend(check_stale(data, json_file.name, "pages"))

    if parse_errors:
        print(f"Found {len(parse_errors)} invalid community metadata file(s):")
        for error in parse_errors:
            print(f"  {error}")
        return 1

    if not stale_entries:
        print("No stale community metadata entries found.")
        return 0
    else:
        print(f"Found {len(stale_entries)} stale community metadata entry(s):")
        for entry in stale_entries:
            print(f"  {entry}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
