#!/usr/bin/env python3
"""Verify that hand-authored docs do not indent top-level markdown markers.

Usage:
    python scripts/verify/markdown_top_level_spacing.py

Fails when a docs markdown file contains leading spaces before top-level markdown
markers such as headings or metadata labels. These lines can render incorrectly
in MkDocs and leak raw markdown into the browser output.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "docs"

LEADING_SPACE_PATTERN = re.compile(
    r"^\s+(?:#{1,6}\s|\*\*[A-Za-z][^*]{0,120}:\*\*)"
)


def find_leading_space_issues(content: str) -> list[tuple[int, str]]:
    """Return line-numbered leading-space issues outside fenced code blocks."""
    issues: list[tuple[int, str]] = []
    in_fenced_code_block = False

    for line_number, line in enumerate(content.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fenced_code_block = not in_fenced_code_block
            continue

        if in_fenced_code_block:
            continue

        if LEADING_SPACE_PATTERN.match(line):
            issues.append((line_number, line))

    return issues


def verify_docs_directory(repo_root: Path, docs_dir: Path) -> list[tuple[str, int, str]]:
    """Return repo-relative issues for docs markdown files."""
    issues: list[tuple[str, int, str]] = []
    for md_file in sorted(docs_dir.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        for line_number, line in find_leading_space_issues(content):
            issues.append((str(md_file.relative_to(repo_root)).replace("\\", "/"), line_number, line))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify top-level markdown headings and metadata are not indented in docs/."
    )
    parser.parse_args()

    issues = verify_docs_directory(REPO_ROOT, DOCS_DIR)
    if not issues:
        print("No leading-space top-level markdown issues found.")
        return 0

    print("Leading-space top-level markdown issues found:")
    for relative_path, line_number, line in issues:
        print(f"  {relative_path}:{line_number}: {line}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
