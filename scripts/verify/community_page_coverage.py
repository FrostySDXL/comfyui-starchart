#!/usr/bin/env python3
"""Verify community page coverage completeness.

Scans docs/**/*.md for pages carrying a community evidence label and compares
the result against references/community/community_pages.json.

Fails if:
- A markdown file with a community evidence label is not listed in community_pages.json
- A page listed in community_pages.json does not exist on disk

Usage:
    python scripts/verify/community_page_coverage.py

Exits 0 if coverage is complete, exits 1 with a report of gaps.
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.common.path_normalization import normalize_repo_path

DOCS_DIR = REPO_ROOT / "docs"
COMMUNITY_PAGES_JSON = REPO_ROOT / "references" / "community" / "community_pages.json"

# Evidence label patterns that indicate a page has a community component.
# These match the **Evidence:** line near the top of a page.
COMMUNITY_EVIDENCE_PATTERNS = [
    re.compile(r"community pattern", re.IGNORECASE),
]


def extract_evidence_label(content: str) -> str | None:
    """Return the exact evidence label text from a markdown page."""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("**Evidence:**"):
            return stripped.removeprefix("**Evidence:**").strip()
    return None


def has_community_evidence_label(content: str) -> bool:
    """Return True if the markdown content carries a community evidence label.

    Only checks lines that look like an Evidence label (e.g. `**Evidence:** ...`)
    to avoid false positives from pages that merely mention community patterns
    in their prose (such as style guides or checklists).
    """
    evidence_label = extract_evidence_label(content)
    if evidence_label:
        for pattern in COMMUNITY_EVIDENCE_PATTERNS:
            if pattern.search(evidence_label):
                return True
    return False


def find_community_labeled_pages(docs_dir: Path) -> set[str]:
    """Return a set of relative page paths (using forward slashes) that have
    a community evidence label in their markdown content."""
    labeled = set()
    for md_file in sorted(docs_dir.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        if has_community_evidence_label(content):
            rel_path = normalize_repo_path(md_file.relative_to(REPO_ROOT))
            labeled.add(rel_path)
    return labeled


def load_tracked_pages(json_path: Path) -> dict[str, dict]:
    """Return tracked community page metadata keyed by page_path."""
    data = json.loads(json_path.read_text(encoding="utf-8"))
    pages = data.get("pages", [])
    return {
        page["page_path"]: page for page in pages if isinstance(page, dict) and "page_path" in page
    }


def is_intentionally_tracked_without_community_label(metadata: dict) -> bool:
    """Return True for repo-local policy pages tracked for review scheduling."""
    return (
        metadata.get("source_type") == "repo_local"
        or metadata.get("page_kind") == "hand_authored_policy"
    )


def main() -> int:
    labeled_pages = find_community_labeled_pages(DOCS_DIR)
    tracked_pages = load_tracked_pages(COMMUNITY_PAGES_JSON)
    tracked_paths = set(tracked_pages)

    missing_from_json = labeled_pages - tracked_paths
    orphaned_in_json = tracked_paths - labeled_pages
    intentional_non_community_pages = {
        page_path
        for page_path in orphaned_in_json
        if is_intentionally_tracked_without_community_label(tracked_pages.get(page_path, {}))
    }
    unexpected_orphaned_in_json = orphaned_in_json - intentional_non_community_pages

    # Also check that tracked pages actually exist on disk
    missing_files = set()
    for page_path in tracked_paths:
        full_path = REPO_ROOT / page_path
        if not full_path.exists():
            missing_files.add(page_path)

    label_mismatches = []
    for page_path, metadata in tracked_pages.items():
        full_path = REPO_ROOT / page_path
        if not full_path.exists():
            continue
        evidence_label = extract_evidence_label(full_path.read_text(encoding="utf-8"))
        expected_label = metadata.get("evidence_label")
        if evidence_label != expected_label:
            label_mismatches.append((page_path, expected_label, evidence_label))

    errors = []
    warnings = []

    if missing_from_json:
        errors.append(
            f"Found {len(missing_from_json)} community-labeled page(s) missing from community_pages.json:"
        )
        for path in sorted(missing_from_json):
            errors.append(f"  {path}")

    if unexpected_orphaned_in_json:
        warnings.append(
            f"Found {len(unexpected_orphaned_in_json)} tracked page(s) with no community evidence label on disk:"
        )
        for path in sorted(unexpected_orphaned_in_json):
            warnings.append(f"  {path}")

    if missing_files:
        errors.append(f"Found {len(missing_files)} tracked page(s) that do not exist on disk:")
        for path in sorted(missing_files):
            errors.append(f"  {path}")

    if label_mismatches:
        errors.append(
            f"Found {len(label_mismatches)} tracked page(s) whose evidence label does not match community_pages.json:"
        )
        for page_path, expected_label, actual_label in sorted(label_mismatches):
            errors.append(f"  {page_path}")
            errors.append(f"    metadata: {expected_label!r}")
            errors.append(f"    doc:      {actual_label!r}")

    if warnings:
        print("Community page coverage warnings:")
        for warning in warnings:
            print(warning)
        print()

    if errors:
        print("Community page coverage violations found:")
        for error in errors:
            print(error)
        return 1
    else:
        print("Community page coverage is complete.")
        print(f"  Tracked pages: {len(tracked_paths)}")
        print(f"  Community-labeled pages on disk: {len(labeled_pages)}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
