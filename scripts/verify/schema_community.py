from __future__ import annotations

from scripts.verify.schema_common import _check_type, _type_label

PACKAGE_SCHEMA = {
    "slug": (str, True),
    "name": (str, True),
    "repo_url": ((str, type(None)), False),
    "registry_url": ((str, type(None)), False),
    "category": (str, True),
    "status": (str, True),
    "role_summary": (str, True),
    "notable_patterns": (list, False),
    "used_by": ((str, type(None)), False),
    "source_type": (str, True),
    "evidence_urls": (list, True),
    "pinned_external_version": ((str, type(None)), False),
    "pinned_commit": ((str, type(None)), False),
    "last_verified": (str, True),
    "needs_review_after": (str, True),
    "maintenance_tier": (str, True),
    "caveats": ((str, type(None)), False),
}

PAGE_SCHEMA = {
    "page_path": (str, True),
    "page_kind": (str, True),
    "evidence_label": (str, True),
    "source_type": (str, True),
    "last_verified": (str, True),
    "needs_review_after": (str, True),
    "maintenance_tier": (str, True),
    "generated_from": ((str, type(None)), False),
    "notes": ((str, type(None)), False),
}

ALLOWED_PACKAGE_CATEGORIES = {"package_manager", "registry", "node_pack", "tooling"}
ALLOWED_PACKAGE_STATUSES = {
    "Actively Maintained",
    "Community Supported",
    "Likely Unmaintained",
    "Unknown",
}
ALLOWED_PACKAGE_SOURCE_TYPES = {"official_project", "community_observation"}
ALLOWED_PAGE_KINDS = {
    "generated_catalog",
    "hand_authored_study",
    "hand_authored_tutorial",
    "hand_authored_guide",
    "hand_authored_policy",
}
ALLOWED_PAGE_SOURCE_TYPES = {"community_metadata", "pinned_external_repo", "hybrid", "repo_local"}


def validate_packages(data: dict, filename: str) -> list[str]:
    errors = []
    packages = data.get("packages", [])
    seen_slugs = set()
    for index, package in enumerate(packages):
        if not isinstance(package, dict):
            errors.append(f"{filename}: packages[{index}] is not a dict")
            continue
        for key, (expected_type, required) in PACKAGE_SCHEMA.items():
            if key not in package:
                if required:
                    errors.append(f"{filename}: packages[{index}] missing required key '{key}'")
                continue
            if not _check_type(package[key], expected_type):
                errors.append(
                    f"{filename}: packages[{index}].{key} expected {_type_label(expected_type)}, got {type(package[key]).__name__}"
                )

        notable_patterns = package.get("notable_patterns", [])
        if isinstance(notable_patterns, list):
            for pattern_index, pattern in enumerate(notable_patterns):
                if not isinstance(pattern, str):
                    errors.append(
                        f"{filename}: packages[{index}].notable_patterns[{pattern_index}] expected str, got {type(pattern).__name__}"
                    )

        evidence_urls = package.get("evidence_urls", [])
        if isinstance(evidence_urls, list):
            for url_index, url in enumerate(evidence_urls):
                if not isinstance(url, str):
                    errors.append(
                        f"{filename}: packages[{index}].evidence_urls[{url_index}] expected str, got {type(url).__name__}"
                    )

        slug = package.get("slug")
        if isinstance(slug, str):
            if slug in seen_slugs:
                errors.append(f"{filename}: duplicate slug '{slug}'")
            else:
                seen_slugs.add(slug)

        category = package.get("category")
        if isinstance(category, str) and category not in ALLOWED_PACKAGE_CATEGORIES:
            errors.append(f"{filename}: packages[{index}] has invalid category '{category}'")

        status = package.get("status")
        if isinstance(status, str) and status not in ALLOWED_PACKAGE_STATUSES:
            errors.append(f"{filename}: packages[{index}] has invalid status '{status}'")

        source_type = package.get("source_type")
        if isinstance(source_type, str) and source_type not in ALLOWED_PACKAGE_SOURCE_TYPES:
            errors.append(f"{filename}: packages[{index}] has invalid source_type '{source_type}'")
    return errors


def validate_pages(data: dict, filename: str) -> list[str]:
    errors = []
    pages = data.get("pages", [])
    seen_paths = set()
    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            errors.append(f"{filename}: pages[{index}] is not a dict")
            continue
        for key, (expected_type, required) in PAGE_SCHEMA.items():
            if key not in page:
                if required:
                    errors.append(f"{filename}: pages[{index}] missing required key '{key}'")
                continue
            if not _check_type(page[key], expected_type):
                errors.append(
                    f"{filename}: pages[{index}].{key} expected {_type_label(expected_type)}, got {type(page[key]).__name__}"
                )

        page_path = page.get("page_path")
        if isinstance(page_path, str):
            if "\\" in page_path:
                errors.append(
                    f"{filename}: pages[{index}].page_path uses backslashes; use forward slashes for cross-platform compatibility"
                )
            if page_path in seen_paths:
                errors.append(f"{filename}: duplicate page_path '{page_path}'")
            else:
                seen_paths.add(page_path)

        generated_from = page.get("generated_from")
        if isinstance(generated_from, str) and "\\" in generated_from:
            errors.append(
                f"{filename}: pages[{index}].generated_from uses backslashes; use forward slashes for cross-platform compatibility"
            )

        page_kind = page.get("page_kind")
        if isinstance(page_kind, str) and page_kind not in ALLOWED_PAGE_KINDS:
            errors.append(f"{filename}: pages[{index}] has invalid page_kind '{page_kind}'")

        source_type = page.get("source_type")
        if isinstance(source_type, str) and source_type not in ALLOWED_PAGE_SOURCE_TYPES:
            errors.append(f"{filename}: pages[{index}] has invalid source_type '{source_type}'")
    return errors
