#!/usr/bin/env python3
"""Generate a bounded machine-readable index of published docs pages."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from scripts.common.published_docs_surface import (
    build_published_docs_surface,
    flatten_nav_from_source,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

SIDEBAR_DATA = REPO_ROOT / "src" / "site" / "sidebar-data.json"
DEFAULT_NAV_SOURCE = SIDEBAR_DATA
DOCS_ROOT = REPO_ROOT / "src" / "content" / "docs"
METADATA_PATH = REPO_ROOT / "references" / "docs-index-metadata.json"
OUTPUT_PATH = REPO_ROOT / "public" / "artifacts" / "docs-index.json"

KNOWN_TASK_INTENTS = {
    "build-custom-node",
    "debug-api-integration",
    "discover-artifacts",
    "discover-hooks",
    "discover-routes",
    "inspect-object-info",
    "lookup-history",
    "monitor-execution",
    "route-docs-task",
    "submit-prompt",
    "understand-architecture",
}
KNOWN_ARTIFACT_FILENAMES = {
    "docs-index.json",
    "js_hooks.json",
    "manifest.json",
    "node_api_schema.json",
    "server_endpoints.json",
}
KNOWN_STABILITY_TIERS = {
    "pinned-baseline",
    "runtime-dependent",
    "support-routing",
}
ALLOWED_METADATA_KEYS = {
    "task_intents",
    "related_artifacts",
    "related_routes",
    "related_events",
    "runtime_required",
    "stability_tier",
    "recommended_next_reads",
}
INTENTIONALLY_BARE_PAGE_ALLOWLIST = frozenset(
    {
        "reference/source-evidence-policy.md",
        "reference/writing-style-guide.md",
        "reference/version-pin-status.md",
        "reference/topic-scope.md",
    }
)
ROUTE_RE = re.compile(r"^[A-Z]+ /[^\s]+$")


def _sorted_strings(values: list[str]) -> list[str]:
    return sorted(values)


def load_docs_index_metadata(metadata_path: Path = METADATA_PATH) -> dict[str, dict[str, object]]:
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{metadata_path.name} must contain a top-level object keyed by docs path")
    for key, value in data.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            raise ValueError("Metadata entries must map string docs paths to objects")
    return data


def _nav_paths_for_validation(repo_root: Path, nav_source: str | Path) -> set[str]:
    return {entry["path"] for entry in flatten_nav_from_source(repo_root, nav_source)}


def _expect_string_list(path: str, field_name: str, value: object) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{path}: {field_name} must be an array of strings")
    return list(value)


def validate_docs_index_metadata(
    metadata: dict[str, dict[str, object]],
    eligible_paths: set[str],
    nav_paths: set[str],
) -> None:
    for path, entry in metadata.items():
        if path not in nav_paths:
            raise ValueError(
                f"{path}: metadata key does not exist in checked-in published docs navigation"
            )
        if path not in eligible_paths:
            raise ValueError(
                f"{path}: metadata key does not target a retained published docs page entry"
            )

        unknown_keys = sorted(set(entry.keys()) - ALLOWED_METADATA_KEYS)
        if unknown_keys:
            raise ValueError(f"{path}: unknown metadata keys: {', '.join(unknown_keys)}")

        task_intents = _expect_string_list(path, "task_intents", entry.get("task_intents", []))
        invalid_task_intents = sorted(set(task_intents) - KNOWN_TASK_INTENTS)
        if invalid_task_intents:
            allowed_task_intents = ", ".join(sorted(KNOWN_TASK_INTENTS))
            raise ValueError(
                f"{path}: invalid task_intents values: {', '.join(invalid_task_intents)}. "
                f"Allowed values: {allowed_task_intents}. "
                "If you are intentionally adding a new task intent, update "
                "KNOWN_TASK_INTENTS in scripts/generate/generate_docs_index.py."
            )

        related_artifacts = _expect_string_list(
            path, "related_artifacts", entry.get("related_artifacts", [])
        )
        invalid_artifacts = sorted(set(related_artifacts) - KNOWN_ARTIFACT_FILENAMES)
        if invalid_artifacts:
            raise ValueError(
                f"{path}: invalid related_artifacts values: {', '.join(invalid_artifacts)}"
            )

        related_routes = _expect_string_list(
            path, "related_routes", entry.get("related_routes", [])
        )
        invalid_routes = sorted(route for route in related_routes if not ROUTE_RE.match(route))
        if invalid_routes:
            raise ValueError(f"{path}: invalid related_routes values: {', '.join(invalid_routes)}")

        _expect_string_list(path, "related_events", entry.get("related_events", []))

        runtime_required = entry.get("runtime_required", None)
        if runtime_required is not None and not isinstance(runtime_required, bool):
            raise ValueError(f"{path}: runtime_required must be boolean or null")

        stability_tier = entry.get("stability_tier", None)
        if stability_tier is not None:
            if not isinstance(stability_tier, str):
                raise ValueError(f"{path}: stability_tier must be a string or null")
            if stability_tier not in KNOWN_STABILITY_TIERS:
                raise ValueError(f"{path}: invalid stability_tier value: {stability_tier}")

        recommended_next_reads = _expect_string_list(
            path, "recommended_next_reads", entry.get("recommended_next_reads", [])
        )
        broken_next_reads = sorted(
            target for target in recommended_next_reads if target not in eligible_paths
        )
        if broken_next_reads:
            raise ValueError(
                f"{path}: recommended_next_reads targets are not eligible published docs pages: {', '.join(broken_next_reads)}"
            )

    unexpected_bare_pages = sorted(
        eligible_paths - set(metadata) - INTENTIONALLY_BARE_PAGE_ALLOWLIST
    )
    if unexpected_bare_pages:
        raise ValueError(
            "Retained published docs pages must declare tooling_metadata unless they are intentionally bare allowlisted pages. "
            "Unexpected bare pages: " + ", ".join(unexpected_bare_pages)
        )


def normalize_tooling_metadata(entry: dict[str, object]) -> dict[str, object]:
    return {
        "task_intents": _sorted_strings(list(entry.get("task_intents", []))),
        "related_artifacts": _sorted_strings(list(entry.get("related_artifacts", []))),
        "related_routes": _sorted_strings(list(entry.get("related_routes", []))),
        "related_events": _sorted_strings(list(entry.get("related_events", []))),
        "runtime_required": entry.get("runtime_required", None),
        "stability_tier": entry.get("stability_tier", None),
        "recommended_next_reads": _sorted_strings(list(entry.get("recommended_next_reads", []))),
    }


def build_docs_index(
    repo_root: Path = REPO_ROOT,
    nav_source: str | Path | None = None,
    metadata_path: Path | None = None,
    metadata: dict[str, dict[str, object]] | None = None,
) -> dict[str, object]:
    resolved_nav_source = nav_source if nav_source is not None else DEFAULT_NAV_SOURCE
    resolved_metadata_path = metadata_path if metadata_path is not None else METADATA_PATH
    pages = build_published_docs_surface(repo_root, resolved_nav_source, DOCS_ROOT)
    eligible_paths = {page["path"] for page in pages}
    nav_paths = _nav_paths_for_validation(repo_root, resolved_nav_source)
    resolved_metadata = (
        metadata if metadata is not None else load_docs_index_metadata(resolved_metadata_path)
    )
    validate_docs_index_metadata(resolved_metadata, eligible_paths, nav_paths)

    merged_pages = []
    for page in pages:
        merged = dict(page)
        page_metadata = resolved_metadata.get(page["path"])
        if page_metadata is not None:
            merged["tooling_metadata"] = normalize_tooling_metadata(page_metadata)
        merged_pages.append(merged)

    return {
        "artifact": "docs-index.json",
        "artifact_schema_version": "1.1.0",
        "scope": {
            "surface": "hand-authored published docs pages included in the checked-in docs navigation with optional tooling-oriented enrichment",
            "excludes": [
                "generated markdown pages",
                "built site output",
                "repo-local non-doc markdown",
                "full-text content extraction",
            ],
        },
        "pages": merged_pages,
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
        "--metadata",
        default=str(METADATA_PATH),
        help="Docs-index metadata JSON path (defaults to references/docs-index-metadata.json)",
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_PATH),
        help="Output JSON path (defaults to public/artifacts/docs-index.json)",
    )
    args = parser.parse_args()

    metadata = load_docs_index_metadata(Path(args.metadata))
    docs_index = build_docs_index(
        repo_root=REPO_ROOT,
        nav_source=args.nav_source,
        metadata_path=Path(args.metadata),
        metadata=metadata,
    )
    output_path = Path(args.output)
    write_docs_index(docs_index, output_path)
    print(f"Generated docs index at {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
