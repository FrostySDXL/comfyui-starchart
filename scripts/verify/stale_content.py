#!/usr/bin/env python3
"""Scan for stale content markers in JSON and markdown files.

Usage:
    python scripts/verify/stale_content.py

Exits 0 if no stale content found, exits 1 with a report of stale items.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCES_RAW_DIR = REPO_ROOT / "references" / "raw"
DOCS_DIR = REPO_ROOT / "docs"

STALE_MARKERS = ["TODO", "PLACEHOLDER", "FILL IN", "TBD", "FIXME", "HACK"]


def find_stale_in_json() -> list[tuple[str, int, str]]:
    """Find stale content markers in JSON reference files.

    Returns a list of (file, line_number, marker_text) tuples.
    """
    stale = []
    for json_file in sorted(REFERENCES_RAW_DIR.glob("*.json")):
        try:
            content = json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        # Check string values recursively for TODO markers
        _find_stale_in_json_value(json_file, content, stale)
    return stale


def _find_stale_in_json_value(json_file: Path, value, stale: list, path: str = ""):
    """Recursively search JSON values for stale markers."""
    if isinstance(value, str):
        for marker in STALE_MARKERS:
            if marker in value:
                stale.append(
                    (
                        str(json_file.relative_to(Path.cwd())),
                        0,
                        f'{path}: {marker} in "{value[:80]}"',
                    )
                )
                break
    elif isinstance(value, dict):
        for k, v in value.items():
            _find_stale_in_json_value(json_file, v, stale, f"{path}.{k}" if path else k)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _find_stale_in_json_value(json_file, v, stale, f"{path}[{i}]")


def find_stale_in_markdown() -> list[tuple[str, int, str]]:
    """Find stale content markers in markdown doc files.

    Returns a list of (file, line_number, line_content) tuples.
    """
    stale = []
    for md_file in sorted(DOCS_DIR.rglob("*.md")):
        lines = md_file.read_text(encoding="utf-8").splitlines()
        for line_num, line in enumerate(lines, 1):
            for marker in STALE_MARKERS:
                if marker in line:
                    # Skip lines that are part of code blocks or are legitimate references
                    stripped = line.strip()
                    # Allow TODO in code examples within backtick blocks
                    if stripped.startswith("```") or stripped.startswith("|"):
                        continue
                    # Allow the word TODO in explanatory text only if it's clearly a task marker
                    # (not in a JSON value or code sample)
                    if marker == "TODO" and (
                        "returns" in line.lower() or "description" in line.lower()
                    ):
                        stale.append(
                            (str(md_file.relative_to(Path.cwd())), line_num, stripped[:100])
                        )
                    elif marker != "TODO":
                        stale.append(
                            (str(md_file.relative_to(Path.cwd())), line_num, stripped[:100])
                        )
                    break
    return stale


def main():
    """Run all stale content checks and report results."""
    found_any = False

    json_stale = find_stale_in_json()
    if json_stale:
        found_any = True
        print("STALE CONTENT IN JSON FILES:")
        for file_path, line_num, detail in json_stale:
            print(f"  {file_path}: {detail}")
        print()

    md_stale = find_stale_in_markdown()
    if md_stale:
        found_any = True
        print("STALE CONTENT IN MARKDOWN DOCS:")
        for file_path, line_num, detail in md_stale:
            print(f"  {file_path}:{line_num}: {detail}")
        print()

    if not found_any:
        print("No stale content markers found.")
        return 0
    else:
        total = len(json_stale) + len(md_stale)
        print(f"Found {total} stale content marker(s).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
