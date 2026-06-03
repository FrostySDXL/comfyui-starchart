#!/usr/bin/env python3
"""Scan for stale content markers in JSON and markdown files.

Usage:
    python scripts/verify/stale_content.py
    python scripts/verify/stale_content.py --max-age-days 90
    python scripts/verify/stale_content.py --check-version-refs

Exits 0 if no stale content found, exits 1 with a report of stale items.
"""

import argparse
import datetime
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCES_RAW_DIR = REPO_ROOT / "references" / "raw"
DOCS_DIR = REPO_ROOT / "src" / "content" / "docs"

STALE_MARKERS = [
    "TODO",
    "PLACEHOLDER",
    "FILL IN",
    "TBD",
    "FIXME",
    "HACK",
    "STALE",
    "OUTDATED",
    "DEPRECATED",
    "REMOVE",
    "TEMP",
    "WORKAROUND",
]

LAST_UPDATED_RE = re.compile(r"\*\*Last Updated:\*\*\s*(\d{4}-\d{2}-\d{2})")


def _display_path(path: Path) -> str:
    """Return a repo-relative path, with a cwd fallback for patched test roots."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path.relative_to(Path.cwd()))


def find_stale_in_json() -> list[tuple[str, int, str]]:
    """Find stale content markers in JSON reference files.

    Returns a list of (file, line_number, marker_text) tuples.
    """
    stale: list[tuple[str, int, str]] = []
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
                        _display_path(json_file),
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
        in_fenced_block = False
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith(("```", "~~~")):
                in_fenced_block = not in_fenced_block
                continue
            if in_fenced_block:
                continue
            for marker in STALE_MARKERS:
                if marker in line:
                    # Skip lines that are part of code blocks or are legitimate references
                    if stripped.startswith("|"):
                        continue
                    if marker == "TODO" and re.search(r'["`\']TODO["`\']', line):
                        continue
                    stale.append((_display_path(md_file), line_num, stripped[:100]))
                    break
        if in_fenced_block:
            stale.append(
                (
                    _display_path(md_file),
                    0,
                    "Unclosed fenced code block may hide stale markers",
                )
            )
    return stale


def find_stale_dates(max_age_days: int) -> list[tuple[str, int, str]]:
    """Flag pages whose Last Updated date exceeds max_age_days.

    Returns a list of (file, 0, message) tuples.
    """
    stale = []
    cutoff = datetime.date.today() - datetime.timedelta(days=max_age_days)
    for md_file in sorted(DOCS_DIR.rglob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        for line in text.splitlines():
            m = LAST_UPDATED_RE.search(line)
            if m:
                try:
                    date = datetime.date.fromisoformat(m.group(1))
                    if date < cutoff:
                        stale.append(
                            (
                                _display_path(md_file),
                                0,
                                f"Last Updated {m.group(1)} exceeds {max_age_days}-day threshold (cutoff {cutoff})",
                            )
                        )
                except ValueError:
                    pass
                break
    return stale


def _read_current_core_version() -> str | None:
    """Read the current pinned core version from server_endpoints.json."""
    server_file = REFERENCES_RAW_DIR / "server_endpoints.json"
    if server_file.exists():
        try:
            data = json.loads(server_file.read_text(encoding="utf-8"))
            version = data.get("metadata", {}).get("version", "")
            if version and version != "unversioned":
                return version
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
    return None


def find_stale_version_refs(current_version: str) -> list[tuple[str, int, str]]:
    """Flag references to old ComfyUI versions in prose docs.

    Returns a list of (file, line_number, message) tuples.
    """
    if not current_version:
        return []

    # Parse current major.minor from e.g. "v0.20.1"
    m = re.match(r"v(\d+)\.(\d+)\.(\d+)", current_version)
    if not m:
        return []
    cur_major, cur_minor = int(m.group(1)), int(m.group(2))

    stale = []
    # Match version references like v0.19.x, v0.18.x, etc. (older than current minor)
    version_ref_re = re.compile(r"v(\d+)\.(\d+)\.\d+")

    for md_file in sorted(DOCS_DIR.rglob("*.md")):
        if "whats-new" in md_file.parts or (
            md_file.name == "version-history.md" and "reference" in md_file.parts
        ):
            continue
        lines = md_file.read_text(encoding="utf-8").splitlines()
        for line_num, line in enumerate(lines, 1):
            for vm in version_ref_re.finditer(line):
                ref_major, ref_minor = int(vm.group(1)), int(vm.group(2))
                if ref_major < cur_major or (ref_major == cur_major and ref_minor < cur_minor):
                    if current_version not in line:
                        stale.append(
                            (
                                _display_path(md_file),
                                line_num,
                                f"References older ComfyUI version {vm.group(0)} (current pin: {current_version}): {line.strip()[:100]}",
                            )
                        )
                        break
    return stale


def main():
    """Run all stale content checks and report results."""
    parser = argparse.ArgumentParser(
        description="Scan for stale content markers in JSON and markdown files."
    )
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=None,
        help="Flag pages whose Last Updated date exceeds this many days (disabled by default).",
    )
    parser.add_argument(
        "--check-version-refs",
        action="store_true",
        help="Flag references to ComfyUI versions older than the current pinned version.",
    )
    args = parser.parse_args()

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

    if args.max_age_days:
        date_stale = find_stale_dates(args.max_age_days)
        if date_stale:
            found_any = True
            print(f"STALE DATES (>{args.max_age_days} days):")
            for file_path, line_num, detail in date_stale:
                print(f"  {file_path}: {detail}")
            print()

    if args.check_version_refs:
        current_version = _read_current_core_version()
        if current_version:
            version_stale = find_stale_version_refs(current_version)
            if version_stale:
                found_any = True
                print(f"STALE VERSION REFERENCES (current pin: {current_version}):")
                for file_path, line_num, detail in version_stale:
                    print(f"  {file_path}:{line_num}: {detail}")
                print()
        else:
            print("Warning: Could not determine current pinned version for version-ref check.")

    if not found_any:
        print("No stale content markers found.")
        return 0
    else:
        print("Found stale content.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
