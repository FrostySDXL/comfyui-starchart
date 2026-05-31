#!/usr/bin/env python3
"""Verify repo-local references path mentions in docs and extracted JSON metadata.

Usage:
    python scripts/verify/cross_references.py

Checks two bounded surfaces only:
    1. `references/...` path mentions inside published markdown docs
    2. source-path metadata inside `references/raw/*.json`

This script does not validate general intra-doc markdown links. The site build is
the broader guard for those navigation paths.

Exits 0 if all checked references are valid, exits 1 with a report of broken
references.
"""

import json
import re
import sys
from pathlib import Path

from scripts.common.path_normalization import normalize_repo_path

REPO_ROOT = Path(__file__).resolve().parents[2]

DOCS_DIR = REPO_ROOT / "src" / "content" / "docs"
REFERENCES_RAW_DIR = REPO_ROOT / "references" / "raw"
REFERENCES_SNAPSHOTS_DIR = REPO_ROOT / "references" / "snapshots"


def find_markdown_files(directory: Path) -> list[Path]:
    """Find all markdown files in a directory tree."""
    return sorted(directory.rglob("*.md"))


def find_json_files(directory: Path) -> list[Path]:
    """Find all JSON files in a directory."""
    return sorted(directory.glob("*.json"))


def extract_file_paths_from_markdown(content: str) -> list[str]:
    """Extract file path references from markdown content.

    Looks for patterns like:
    - `references/snapshots/...`
    - `references/raw/...`
    """
    paths = []
    # Match backtick-enclosed paths starting with references/
    for match in re.finditer(r"`(references/[^`]+)`", content):
        paths.append(match.group(1))
    # Match markdown link paths
    for match in re.finditer(r"\[([^\]]*)\]\(([^)]+)\)", content):
        target = match.group(2)
        if target.startswith("references/"):
            paths.append(target)
    return paths


def extract_source_paths_from_json(data: dict) -> list[str]:
    """Extract source file paths from JSON metadata."""
    paths = []
    metadata = data.get("metadata", {})
    if "source" in metadata:
        paths.append(metadata["source"])
    if "sources" in metadata:
        paths.extend(metadata["sources"])
    return paths


# Runtime-only artifacts and temporary directories that are not expected
# to exist on disk in a clean repo.
RUNTIME_ONLY_PATHS = {
    "references/raw/object_info_runtime.json",
    "references/_refresh_backups/",
}


def verify_markdown_references() -> list[tuple[str, str]]:
    """Verify all file path references in markdown docs exist on disk.

    Returns a list of (file, broken_path) tuples for missing references.
    """
    broken = []
    for md_file in find_markdown_files(DOCS_DIR):
        content = md_file.read_text(encoding="utf-8")
        for ref_path in extract_file_paths_from_markdown(content):
            # Normalize backslashes for Windows
            normalized = normalize_repo_path(ref_path)
            if normalized in RUNTIME_ONLY_PATHS:
                continue
            full_path = REPO_ROOT / normalized
            if not full_path.exists():
                broken.append((str(md_file.relative_to(REPO_ROOT)), ref_path))
    return broken


def verify_json_source_references() -> list[tuple[str, str]]:
    """Verify all source file paths in JSON metadata exist on disk.

    Returns a list of (json_file, broken_path) tuples for missing sources.
    """
    broken = []
    for json_file in find_json_files(REFERENCES_RAW_DIR):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        for source_path in extract_source_paths_from_json(data):
            # Normalize backslashes for Windows
            normalized = normalize_repo_path(source_path)
            full_path = REPO_ROOT / normalized
            if not full_path.exists():
                broken.append((str(json_file.relative_to(REPO_ROOT)), source_path))
    return broken


def main():
    """Run bounded references-path checks and report results."""
    errors = []

    md_broken = verify_markdown_references()
    if md_broken:
        print("BROKEN REFERENCES PATHS IN MARKDOWN DOCS:")
        for doc_file, ref_path in md_broken:
            print(f"  {doc_file} -> {ref_path}")
        errors.extend(md_broken)

    json_broken = verify_json_source_references()
    if json_broken:
        print("BROKEN SOURCE PATHS IN JSON METADATA:")
        for json_file, source_path in json_broken:
            print(f"  {json_file} -> {source_path}")
        errors.extend(json_broken)

    if not errors:
        print("All references-path checks are valid.")
        return 0
    else:
        print(f"\nFound {len(errors)} broken reference(s).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
