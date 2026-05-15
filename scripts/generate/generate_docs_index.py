#!/usr/bin/env python3
"""Generate a bounded machine-readable index of published docs pages."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
MKDOCS_CONFIG = REPO_ROOT / "mkdocs.yml"
DOCS_ROOT = REPO_ROOT / "docs"
OUTPUT_PATH = DOCS_ROOT / "artifacts" / "docs-index.json"

TITLE_RE = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)
EVIDENCE_RE = re.compile(r"^\s*\*\*Evidence:\*\*\s*(.+?)\s*$", re.MULTILINE)
GENERATED_BANNER_PREFIX = "<!-- GENERATED FILE:"

AUDIENCE_BY_PATH = {
    "start-here/author.md": "consumer",
    "start-here/extension-developer.md": "consumer",
    "start-here/service-integration.md": "consumer",
    "start-here/tooling-builder.md": "consumer",
    "start-here/docs-contributor.md": "contributor",
}


def _load_nav(repo_root: Path) -> list:
    config = yaml.safe_load((repo_root / "mkdocs.yml").read_text(encoding="utf-8")) or {}
    nav = config.get("nav")
    if not isinstance(nav, list):
        raise ValueError("mkdocs.yml is missing a valid nav list")
    return nav


def _normalize_rel_doc_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    if normalized.startswith("docs/"):
        normalized = normalized[5:]
    return normalized


def _flatten_nav(items: list, section_path: list[str] | None = None) -> list[dict[str, str]]:
    section_path = section_path or []
    pages: list[dict[str, str]] = []
    for item in items:
        if isinstance(item, str):
            normalized_path = _normalize_rel_doc_path(item)
            pages.append(
                {
                    "nav_label": Path(normalized_path).stem,
                    "nav_section": " / ".join(section_path)
                    if section_path
                    else Path(normalized_path).stem,
                    "path": normalized_path,
                }
            )
            continue
        if not isinstance(item, dict) or len(item) != 1:
            continue
        label, value = next(iter(item.items()))
        if isinstance(value, str):
            pages.append(
                {
                    "nav_label": label,
                    "nav_section": " / ".join(section_path + [label]) if section_path else label,
                    "path": _normalize_rel_doc_path(value),
                }
            )
        elif isinstance(value, list):
            pages.extend(_flatten_nav(value, section_path + [label]))
    return pages


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
    doc_path = repo_root / "docs" / relative_path
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


def build_docs_index(repo_root: Path = REPO_ROOT) -> dict[str, object]:
    nav_entries = _flatten_nav(_load_nav(repo_root))
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
            "surface": "hand-authored published docs pages included in mkdocs nav",
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
        description="Generate docs/artifacts/docs-index.json from the MkDocs nav and published docs pages."
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_PATH),
        help="Output JSON path (defaults to docs/artifacts/docs-index.json)",
    )
    args = parser.parse_args()

    docs_index = build_docs_index(REPO_ROOT)
    output_path = Path(args.output)
    write_docs_index(docs_index, output_path)
    print(f"Generated docs index at {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
