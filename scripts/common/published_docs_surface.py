#!/usr/bin/env python3
"""Shared helpers for bounded published docs surface generation."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

TITLE_RE = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)
EVIDENCE_RE = re.compile(r"^\s*\*\*Evidence:\*\*\s*(.+?)\s*$", re.MULTILINE)
GENERATED_BANNER_PREFIX = "<!-- GENERATED FILE:"
# Published-docs surface generation does not carry explicit generated-page
# exclusions here; is_generated_page() already skips pages with the generated
# banner. The corresponding safety-rail exclusions in
# scripts/verify/sidebar_navigation_coverage.py exist only to prevent noise
# if a generated page is intentionally restored to disk without a sidebar
# entry -- they serve the coverage verifier, not the docs-index generator.
GENERATED_PAGE_EXCLUSIONS: set[str] = set()

AUDIENCE_BY_PATH = {
    "start-here/author.md": "consumer",
    "start-here/artifact-consumer.md": "consumer",
    "start-here/extension-developer.md": "consumer",
    "reference/topic-scope.md": "contributor",
    "start-here/service-integration.md": "consumer",
    "start-here/tooling-builder.md": "consumer",
}


def load_sidebar_nav(nav_source: Path) -> list:
    if nav_source.suffix.lower() != ".json":
        raise ValueError(f"Unsupported nav source type: {nav_source}")
    nav = json.loads(nav_source.read_text(encoding="utf-8"))
    if not isinstance(nav, list):
        raise ValueError(f"{nav_source.name} is missing a valid top-level sidebar list")
    return nav


def normalize_rel_doc_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    if normalized.startswith("src/content/docs/"):
        normalized = normalized[len("src/content/docs/") :]
    return normalized


def flatten_sidebar_nav(
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
            normalized_path = normalize_rel_doc_path(path)
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
            pages.extend(flatten_sidebar_nav(child_items, child_section_path))

    return pages


def resolve_nav_source(repo_root: Path, nav_source: str | Path) -> Path:
    candidate = Path(nav_source)
    if candidate.is_absolute():
        return candidate
    return repo_root / candidate


def flatten_nav_from_source(repo_root: Path, nav_source: str | Path) -> list[dict[str, str]]:
    resolved_nav_source = resolve_nav_source(repo_root, nav_source)
    raw_nav = load_sidebar_nav(resolved_nav_source)
    return flatten_sidebar_nav(raw_nav)


def extract_title(text: str, fallback: str) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1])
                if isinstance(frontmatter, dict) and "title" in frontmatter:
                    title = frontmatter["title"]
                    if isinstance(title, str):
                        return title.strip()
            except yaml.YAMLError:
                pass
    match = TITLE_RE.search(text)
    return match.group(1).strip() if match else fallback


def extract_evidence(text: str) -> str | None:
    match = EVIDENCE_RE.search(text)
    return match.group(1).strip() if match else None


def extract_scope_summary(text: str) -> str | None:
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


def is_generated_page(text: str) -> bool:
    return text.lstrip().startswith(GENERATED_BANNER_PREFIX)


def build_page_entry(nav_entry: dict[str, str], docs_root: Path) -> dict[str, object] | None:
    relative_path = nav_entry["path"]
    if relative_path in GENERATED_PAGE_EXCLUSIONS:
        return None

    doc_path = docs_root / relative_path
    if not doc_path.exists() or doc_path.suffix.lower() != ".md":
        return None

    text = doc_path.read_text(encoding="utf-8")
    if is_generated_page(text):
        return None

    return {
        "title": extract_title(text, nav_entry["nav_label"]),
        "path": relative_path,
        "nav_section": nav_entry["nav_section"],
        "audience": AUDIENCE_BY_PATH.get(relative_path),
        "evidence": extract_evidence(text),
        "summary": extract_scope_summary(text),
    }


def build_published_docs_surface(
    repo_root: Path, nav_source: str | Path, docs_root: Path
) -> list[dict[str, object]]:
    nav_entries = flatten_nav_from_source(repo_root, nav_source)
    pages: list[dict[str, object]] = []
    seen_paths: set[str] = set()

    for nav_entry in nav_entries:
        path = nav_entry["path"]
        if path in seen_paths:
            continue
        seen_paths.add(path)
        page_entry = build_page_entry(nav_entry, docs_root)
        if page_entry is not None:
            pages.append(page_entry)

    return pages
