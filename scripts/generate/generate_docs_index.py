#!/usr/bin/env python3
"""Generate a bounded machine-readable index of published docs pages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.common.published_docs_surface import build_published_docs_surface

REPO_ROOT = Path(__file__).resolve().parents[2]

SIDEBAR_DATA = REPO_ROOT / "src" / "site" / "sidebar-data.json"
DEFAULT_NAV_SOURCE = SIDEBAR_DATA
DOCS_ROOT = REPO_ROOT / "src" / "content" / "docs"
OUTPUT_PATH = REPO_ROOT / "public" / "artifacts" / "docs-index.json"


def build_docs_index(
    repo_root: Path = REPO_ROOT, nav_source: str | Path | None = None
) -> dict[str, object]:
    resolved_nav_source = nav_source if nav_source is not None else DEFAULT_NAV_SOURCE
    pages = build_published_docs_surface(repo_root, resolved_nav_source, DOCS_ROOT)

    return {
        "artifact": "docs-index.json",
        "artifact_schema_version": "1.0.0",
        "scope": {
            "surface": "hand-authored published docs pages included in the checked-in docs navigation",
            "excludes": [
                "generated markdown pages",
                "built site output",
                "repo-local non-doc markdown",
                "full-text content extraction",
            ],
        },
        "pages": pages,
    }


def write_docs_index(docs_index: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(docs_index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate public/artifacts/docs-index.json from checked-in docs navigation data and published docs pages."
    )
    parser.add_argument(
        "--nav-source",
        default=str(DEFAULT_NAV_SOURCE),
        help=(
            "Navigation source path (defaults to src/site/sidebar-data.json and "
            "must point to checked-in sidebar JSON data)"
        ),
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_PATH),
        help="Output JSON path (defaults to public/artifacts/docs-index.json)",
    )
    args = parser.parse_args()

    docs_index = build_docs_index(REPO_ROOT, args.nav_source)
    output_path = Path(args.output)
    write_docs_index(docs_index, output_path)
    print(f"Generated docs index at {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
