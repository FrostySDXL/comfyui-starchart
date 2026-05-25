#!/usr/bin/env python3
"""Verify sidebar-data.json covers the hand-authored published docs tree.

Compares page paths declared in src/site/sidebar-data.json against actual
hand-authored markdown pages under src/content/docs/.

Fails if:
- a hand-authored published docs page exists on disk but is absent from sidebar data
- a sidebar page path does not exist on disk
- duplicate page paths appear in sidebar data

Generated-page exclusions are explicit so intentional generated surfaces do not
create noise.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = REPO_ROOT / "src" / "content" / "docs"
SIDEBAR_DATA_PATH = REPO_ROOT / "src" / "site" / "sidebar-data.json"
GENERATED_PAGE_EXCLUSIONS: set[str] = set()


def normalize_docs_path(path: str) -> str:
    return path.replace("\\", "/")


def load_sidebar_data(path: Path) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_sidebar_paths(entries: list[dict[str, object]]) -> tuple[list[str], list[str]]:
    paths: list[str] = []
    errors: list[str] = []

    def walk(items: list[dict[str, object]], trail: list[str]) -> None:
        for entry in items:
            label = entry.get("label")
            path = entry.get("path")
            child_items = entry.get("items")
            location = " / ".join([*trail, str(label)]) if label else " / ".join(trail) or "<root>"

            if isinstance(path, str):
                normalized = normalize_docs_path(path)
                if not normalized.endswith(".md"):
                    errors.append(f"Sidebar page path must end in .md: {normalized} ({location})")
                paths.append(normalized)
                continue

            if isinstance(child_items, list):
                if not label:
                    errors.append(f"Sidebar section is missing a label at {location}")
                walk(child_items, [*trail, str(label)])
                continue

            errors.append(f"Invalid sidebar entry at {location}: expected path or items")

    walk(entries, [])
    return paths, errors


def collect_hand_authored_docs_paths(docs_root: Path) -> set[str]:
    collected: set[str] = set()
    for markdown_file in sorted(docs_root.rglob("*.md")):
        relative_path = normalize_docs_path(str(markdown_file.relative_to(docs_root)))
        if relative_path in GENERATED_PAGE_EXCLUSIONS:
            continue
        collected.add(relative_path)
    return collected


def main() -> int:
    if not SIDEBAR_DATA_PATH.exists():
        print(f"ERROR: sidebar data file not found: {SIDEBAR_DATA_PATH}")
        return 1
    if not DOCS_ROOT.exists():
        print(f"ERROR: docs root not found: {DOCS_ROOT}")
        return 1

    sidebar_entries = load_sidebar_data(SIDEBAR_DATA_PATH)
    sidebar_paths, structural_errors = collect_sidebar_paths(sidebar_entries)
    sidebar_path_set = set(sidebar_paths)
    docs_paths = collect_hand_authored_docs_paths(DOCS_ROOT)

    duplicates = sorted({path for path in sidebar_paths if sidebar_paths.count(path) > 1})
    missing_from_sidebar = sorted(docs_paths - sidebar_path_set)
    missing_on_disk = sorted(path for path in sidebar_path_set if not (DOCS_ROOT / path).exists())

    errors: list[str] = []
    errors.extend(structural_errors)

    if duplicates:
        errors.append(f"Found {len(duplicates)} duplicate sidebar page path(s):")
        for path in duplicates:
            errors.append(f"  {path}")

    if missing_from_sidebar:
        errors.append(
            f"Found {len(missing_from_sidebar)} hand-authored docs page(s) missing from sidebar data:"
        )
        for path in missing_from_sidebar:
            errors.append(f"  {path}")

    if missing_on_disk:
        errors.append(
            f"Found {len(missing_on_disk)} sidebar page path(s) that do not exist on disk:"
        )
        for path in missing_on_disk:
            errors.append(f"  {path}")

    if errors:
        print("Sidebar navigation coverage violations found:")
        for error in errors:
            print(error)
        return 1

    print("Sidebar navigation coverage is complete.")
    print(f"  Sidebar page paths: {len(sidebar_path_set)}")
    print(f"  Hand-authored docs pages: {len(docs_paths)}")
    print(f"  Explicit generated exclusions: {len(GENERATED_PAGE_EXCLUSIONS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
