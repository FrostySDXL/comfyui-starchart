#!/usr/bin/env python3
"""Generate a bounded machine-readable index of published docs pages."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SIDEBAR_DATA = REPO_ROOT / "src" / "site" / "sidebar-data.json"
DEFAULT_NAV_SOURCE = SIDEBAR_DATA
DOCS_ROOT = REPO_ROOT / "src" / "content" / "docs"
OUTPUT_PATH = REPO_ROOT / "public" / "artifacts" / "docs-index.json"

TITLE_RE = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)
EVIDENCE_RE = re.compile(r"^\s*\*\*Evidence:\*\*\s*(.+?)\s*$", re.MULTILINE)
GENERATED_BANNER_PREFIX = "<!-- GENERATED FILE:"
GENERATED_PAGE_EXCLUSIONS = {
    "ecosystem/map.md",
    "reference/server-py-summary.md",
}

AUDIENCE_BY_PATH = {
    "start-here/author.md": "consumer",
    "start-here/extension-developer.md": "consumer",
    "start-here/service-integration.md": "consumer",
    "start-here/tooling-builder.md": "consumer",
    "start-here/docs-contributor.md": "contributor",
}


def _load_sidebar_nav(nav_source: Path) -> list:
    if nav_source.suffix.lower() != ".json":
        raise ValueError(f"Unsupported nav source type: {nav_source}")
    nav = json.loads(nav_source.read_text(encoding="utf-8"))
    if not isinstance(nav, list):
        raise ValueError(f"{nav_source.name} is missing a valid top-level sidebar list")
    return nav


def _normalize_rel_doc_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    if normalized.startswith("src/content/docs/"):
        normalized = normalized[len("src/content/docs/") :]
    elif normalized.startswith("docs/"):
        normalized = normalized[5:]
    return normalized


def _flatten_sidebar_nav(
    items: list[dict[str, object]], section_path: list[str] | None = None
) -> list[dict[str, str]]:
    section_path = section_path or []
    pages: list[dict[str, str]] = []

    for entry in items:
        if not isinstance(entry, dict):
            continue

        label = entry.get("label")
        path = entry.get("path")
        child_items = entry.get("items")
        docs_index_nav_section = entry.get("docs_index_nav_section")

        if isinstance(path, str):
            normalized_path = _normalize_rel_doc_path(path)
            if isinstance(docs_index_nav_section, str) and docs_index_nav_section.strip():
                nav_section = docs_index_nav_section.strip()
            elif section_path:
                nav_section = " / ".join(section_path)
            elif isinstance(label, str) and label.strip():
                nav_section = label.strip()
            else:
                nav_section = Path(normalized_path).stem

            nav_label = (
                label.strip()
                if isinstance(label, str) and label.strip()
                else Path(normalized_path).stem
            )
            pages.append(
                {
                    "nav_label": nav_label,
                    "nav_section": nav_section,
                    "path": normalized_path,
                }
            )
            continue

        if isinstance(child_items, list):
            child_section_path = list(section_path)
            if isinstance(label, str) and label.strip():
                child_section_path.append(label.strip())
            pages.extend(_flatten_sidebar_nav(child_items, child_section_path))

    return pages


def _resolve_nav_source(repo_root: Path, nav_source: str | Path | None) -> Path:
    candidate = Path(nav_source) if nav_source is not None else DEFAULT_NAV_SOURCE
    if candidate.is_absolute():
        return candidate
    return repo_root / candidate


def _flatten_nav_from_source(
    repo_root: Path, nav_source: str | Path | None = None
) -> list[dict[str, str]]:
    resolved_nav_source = _resolve_nav_source(repo_root, nav_source)
    raw_nav = _load_sidebar_nav(resolved_nav_source)
    return _flatten_sidebar_nav(raw_nav)


def _extract_title(text: str, fallback: str) -> str:
    match = TITLE_RE.search(text)
    return match.group(1).strip() if match else fallback


def _extract_evidence(text: str) -> str | None:
    match = EVIDENCE_RE.search(text)
    return match.group(1).strip() if match else None


def _extract_scope_summary(text: str) -> str | None:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != "## Scope":
            continue
        collected: list[str] = []
        started = False
        for candidate in lines[index + 1 :]:
            stripped = candidate.strip()
            if not stripped:
                if started:
                    break
                continue
            if stripped.startswith("## "):
                break
            collected.append(stripped)
            started = True
        if collected:
            return " ".join(collected)
        return None
    return None


def _is_generated_page(text: str) -> bool:
    return text.lstrip().startswith(GENERATED_BANNER_PREFIX)


def _build_page_entry(repo_root: Path, nav_entry: dict[str, str]) -> dict[str, object] | None:
    relative_path = nav_entry["path"]
    if relative_path in GENERATED_PAGE_EXCLUSIONS:
        return None

    doc_path = DOCS_ROOT / relative_path
    if not doc_path.exists() or doc_path.suffix.lower() != ".md":
        return None

    text = doc_path.read_text(encoding="utf-8")
    if _is_generated_page(text):
        return None

    return {
        "title": _extract_title(text, nav_entry["nav_label"]),
        "path": relative_path,
        "nav_section": nav_entry["nav_section"],
        "audience": AUDIENCE_BY_PATH.get(relative_path),
        "evidence": _extract_evidence(text),
        "summary": _extract_scope_summary(text),
    }


def build_docs_index(
    repo_root: Path = REPO_ROOT, nav_source: str | Path | None = None
) -> dict[str, object]:
    nav_entries = _flatten_nav_from_source(repo_root, nav_source)
    pages = []
    seen_paths: set[str] = set()

    for nav_entry in nav_entries:
        path = nav_entry["path"]
        if path in seen_paths:
            continue
        seen_paths.add(path)
        page_entry = _build_page_entry(repo_root, nav_entry)
        if page_entry is not None:
            pages.append(page_entry)

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
