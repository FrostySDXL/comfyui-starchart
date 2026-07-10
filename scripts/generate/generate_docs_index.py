#!/usr/bin/env python3
"""Generate a bounded machine-readable index of published docs pages."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import warnings
from pathlib import Path
from typing import Any

from scripts.common.display_path import display_path
from scripts.common.published_docs_surface import (
    build_published_docs_surface_from_nav_entries,
    flatten_nav_from_source,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

SIDEBAR_DATA = REPO_ROOT / "src" / "site" / "sidebar-data.json"
DEFAULT_NAV_SOURCE = SIDEBAR_DATA
DOCS_ROOT = REPO_ROOT / "src" / "content" / "docs"
METADATA_PATH = REPO_ROOT / "references" / "docs-index-metadata.json"
OUTPUT_PATH = REPO_ROOT / "public" / "artifacts" / "docs-index.json"
SERVER_ENDPOINTS_PATH = REPO_ROOT / "references" / "raw" / "server_endpoints.json"
FALLBACK_METADATA_REVIEWED_AT = "2026-06-26"
FALLBACK_METADATA_BASELINE = "core-v0.26.0_frontend-v1.47.5_2026-06-26"

KNOWN_TASK_INTENTS = {
    "build-custom-node",
    "debug-api-integration",
    "discover-artifacts",
    "discover-hooks",
    "discover-routes",
    "extract-prompt-text",
    "inspect-conditioning-graph",
    "inspect-object-info",
    "inspect-prompt-payload",
    "lookup-history",
    "monitor-execution",
    "onboarding",
    "observe-server-lifecycle",
    "route-docs-task",
    "submit-prompt",
    "understand-architecture",
    "understand-prompt-topology",
}
KNOWN_ARTIFACT_FILENAMES = {
    "docs-index.json",
    "js_hooks.json",
    "manifest.json",
    "node_api_schema.json",
    "server_endpoints.json",
    "websocket_events.json",
}
DOCUMENTED_SUPPORT_ARTIFACT_FILENAMES = {
    "docs-index.json",
    "delta-summary.json",
    "manifest.json",
    "refresh-provenance.json",
}
# Runtime-only artifacts are excluded only when they are absent from manifest
# discovery, absent from the machine-readable support-artifact table, and consumed
# only by runtime fixtures/examples rather than retained published docs pages.
RUNTIME_ONLY_RELATED_ARTIFACT_EXCLUSIONS = frozenset({"object_info_runtime.json"})
KNOWN_STABILITY_TIERS = {
    "pinned-baseline",
    "runtime-dependent",
    "support-routing",
}
ROUTE_TYPE_VALUES = (
    "alias",
    "canonical",
    "deprecated",
    "external",
    "feature_flag",
    "unknown",
)
ROUTE_CLASSIFICATION_SOURCES = (
    "metadata",
    "server_endpoints_crossref",
    "unknown",
)
ROUTE_CLASSIFICATION_REASONS = (
    "crossref_ambiguous",
    "crossref_resolved",
    "crossref_route_missing",
    "metadata_and_crossref_conflict",
    "metadata_explicit",
    "metadata_not_provided",
)
ALLOWED_METADATA_KEYS = {
    "task_intents",
    "primary_task_intents",
    "excluded_task_intents",
    "related_artifacts",
    "related_routes",
    "related_route_entries",
    "related_events",
    "runtime_required",
    "stability_tier",
    "recommended_next_reads",
    "bare_next_read_reason",
    "metadata_reviewed_at",
    "metadata_baseline",
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
    return sorted(set(values))


def build_allowed_related_artifacts(repo_root: Path = REPO_ROOT) -> set[str]:
    """Build the allowed docs-index related-artifact set from disk-backed surfaces."""
    allowed = {
        path.name
        for path in (repo_root / "references" / "raw").glob("*.json")
        if path.name not in RUNTIME_ONLY_RELATED_ARTIFACT_EXCLUSIONS
    }
    manifest_path = repo_root / "public" / "artifacts" / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}
        artifacts = manifest.get("artifacts", {})
        if isinstance(artifacts, dict):
            allowed.update(str(name) for name in artifacts)
    allowed.update(DOCUMENTED_SUPPORT_ARTIFACT_FILENAMES)
    if not allowed - DOCUMENTED_SUPPORT_ARTIFACT_FILENAMES:
        allowed.update(KNOWN_ARTIFACT_FILENAMES)
    return allowed - set(RUNTIME_ONLY_RELATED_ARTIFACT_EXCLUSIONS)


def load_server_endpoint_routes(
    server_endpoints_path: Path = SERVER_ENDPOINTS_PATH,
) -> dict[str, int]:
    """Return route strings such as ``GET /queue`` mapped to occurrence counts."""
    if not server_endpoints_path.exists():
        return {}
    data = json.loads(server_endpoints_path.read_text(encoding="utf-8"))
    routes: dict[str, int] = {}
    for endpoint in data.get("endpoints", []):
        if not isinstance(endpoint, dict):
            continue
        method = endpoint.get("method")
        route = endpoint.get("route")
        if isinstance(method, str) and isinstance(route, str):
            key = f"{method} {route}"
            routes[key] = routes.get(key, 0) + 1
    return routes


def load_docs_index_metadata(metadata_path: Path = METADATA_PATH) -> dict[str, dict[str, object]]:
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{metadata_path.name} must contain a top-level object keyed by docs path")
    for key, value in data.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            raise ValueError("Metadata entries must map string docs paths to objects")
    return data


def load_metadata_freshness_defaults(repo_root: Path = REPO_ROOT) -> tuple[str, str]:
    """Return docs-index freshness defaults from the current artifact manifest."""
    manifest_path = repo_root / "public" / "artifacts" / "manifest.json"
    fallback_message = (
        f"using fallback docs-index metadata freshness because {display_path(manifest_path)} "
        "is unavailable or does not contain a date-suffixed version_key"
    )
    if not manifest_path.exists():
        warnings.warn(fallback_message, RuntimeWarning, stacklevel=2)
        return FALLBACK_METADATA_REVIEWED_AT, FALLBACK_METADATA_BASELINE
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        warnings.warn(fallback_message, RuntimeWarning, stacklevel=2)
        return FALLBACK_METADATA_REVIEWED_AT, FALLBACK_METADATA_BASELINE
    version_key = manifest.get("version_key")
    if not isinstance(version_key, str) or not version_key:
        warnings.warn(fallback_message, RuntimeWarning, stacklevel=2)
        return FALLBACK_METADATA_REVIEWED_AT, FALLBACK_METADATA_BASELINE
    match = re.search(r"_(\d{4}-\d{2}-\d{2})$", version_key)
    if not match:
        warnings.warn(fallback_message, RuntimeWarning, stacklevel=2)
        return FALLBACK_METADATA_REVIEWED_AT, version_key
    return match.group(1), version_key


def _nav_paths_from_entries(nav_entries: list[dict[str, str]]) -> set[str]:
    return {entry["path"] for entry in nav_entries}


def _expect_string_list(path: str, field_name: str, value: object) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{path}: {field_name} must be an array of strings")
    return list(value)


def _expect_route_entries(path: str, value: object) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{path}: related_route_entries must be an array of objects")
    entries: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"{path}: related_route_entries entries must be objects")
        route = item.get("route")
        route_type = item.get("route_type")
        if not isinstance(route, str) or not ROUTE_RE.match(route):
            raise ValueError(f"{path}: invalid related_route_entries route")
        if route_type not in ROUTE_TYPE_VALUES:
            raise ValueError(f"{path}: invalid route_type value: {route_type}")
        entries.append({"route": route, "route_type": route_type})
    return entries


def _validate_optional_date(path: str, value: object) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        raise ValueError(f"{path}: metadata_reviewed_at must be YYYY-MM-DD")
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{path}: metadata_reviewed_at must be YYYY-MM-DD") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"{path}: metadata_reviewed_at must be YYYY-MM-DD")


def validate_docs_index_metadata(
    metadata: dict[str, dict[str, object]],
    eligible_paths: set[str],
    nav_paths: set[str],
    allowed_artifacts: set[str] | None = None,
) -> None:
    resolved_allowed_artifacts = (
        build_allowed_related_artifacts(REPO_ROOT)
        if allowed_artifacts is None
        else allowed_artifacts
    )
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

        primary_task_intents = _expect_string_list(
            path, "primary_task_intents", entry.get("primary_task_intents", [])
        )
        invalid_primary_task_intents = sorted(set(primary_task_intents) - KNOWN_TASK_INTENTS)
        if invalid_primary_task_intents:
            raise ValueError(
                f"{path}: invalid primary_task_intents values: {', '.join(invalid_primary_task_intents)}"
            )
        if set(primary_task_intents) - set(task_intents):
            raise ValueError(
                f"{path}: primary_task_intents values must be a subset of task_intents"
            )

        excluded_task_intents = _expect_string_list(
            path, "excluded_task_intents", entry.get("excluded_task_intents", [])
        )
        invalid_excluded_task_intents = sorted(set(excluded_task_intents) - KNOWN_TASK_INTENTS)
        if invalid_excluded_task_intents:
            raise ValueError(
                f"{path}: invalid excluded_task_intents values: {', '.join(invalid_excluded_task_intents)}"
            )

        _validate_optional_date(path, entry.get("metadata_reviewed_at"))
        metadata_baseline = entry.get("metadata_baseline")
        if metadata_baseline is not None and not isinstance(metadata_baseline, str):
            raise ValueError(f"{path}: metadata_baseline must be a string or null")

        related_artifacts = _expect_string_list(
            path, "related_artifacts", entry.get("related_artifacts", [])
        )
        invalid_artifacts = sorted(set(related_artifacts) - resolved_allowed_artifacts)
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
        route_entries = _expect_route_entries(path, entry.get("related_route_entries"))
        extra_entry_routes = sorted(
            {route_entry["route"] for route_entry in route_entries} - set(related_routes)
        )
        if extra_entry_routes:
            raise ValueError(
                f"{path}: related_route_entries routes are not present in related_routes: {', '.join(extra_entry_routes)}"
            )

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
        bare_next_reads = sorted(
            target
            for target in recommended_next_reads
            if target in INTENTIONALLY_BARE_PAGE_ALLOWLIST
        )
        if bare_next_reads:
            bare_reason = entry.get("bare_next_read_reason")
            if not isinstance(bare_reason, str) or not bare_reason.strip():
                raise ValueError(
                    f"{path}: recommended_next_reads targets intentionally bare pages and requires bare_next_read_reason: "
                    + ", ".join(bare_next_reads)
                )

    # Validate that every allowlist entry corresponds to a retained published page.
    # Only apply when at least one allowlist page is present in the eligible
    # surface; this prevents the check from breaking temporary test fixtures
    # that don't contain any of the real allowlist pages.
    present_allowlist = INTENTIONALLY_BARE_PAGE_ALLOWLIST & eligible_paths
    if present_allowlist:
        stale_allowlist = sorted(INTENTIONALLY_BARE_PAGE_ALLOWLIST - eligible_paths)
        if stale_allowlist:
            raise ValueError(
                "Intentionally bare docs-index allowlist entries are not retained published docs pages: "
                + ", ".join(stale_allowlist)
            )

    unexpected_bare_pages = sorted(
        eligible_paths - set(metadata) - INTENTIONALLY_BARE_PAGE_ALLOWLIST
    )
    if unexpected_bare_pages:
        raise ValueError(
            "Retained published docs pages must declare tooling_metadata unless they are intentionally bare allowlisted pages. "
            "Unexpected bare pages: " + ", ".join(unexpected_bare_pages)
        )


def build_related_route_entries(
    entry: dict[str, Any],
    server_routes: dict[str, int] | None = None,
) -> tuple[list[dict[str, str]], str]:
    server_routes = server_routes or {}
    explicit_entries = {
        route_entry["route"]: route_entry["route_type"]
        for route_entry in _expect_route_entries("metadata", entry.get("related_route_entries"))
    }
    built: list[dict[str, str]] = []
    sources: set[str] = set()
    for route in _sorted_strings(list(entry.get("related_routes", []))):
        if route in explicit_entries:
            route_type = explicit_entries[route]
            if route in server_routes:
                crossref_type = (
                    "alias" if route.split(" ", 1)[1].startswith("/api/") else "canonical"
                )
                reason = (
                    "metadata_and_crossref_conflict"
                    if route_type != crossref_type
                    else "metadata_explicit"
                )
            else:
                reason = "metadata_explicit"
            sources.add("metadata")
        elif route in server_routes:
            route_type = "alias" if route.split(" ", 1)[1].startswith("/api/") else "canonical"
            reason = "crossref_ambiguous" if server_routes[route] > 1 else "crossref_resolved"
            sources.add("server_endpoints_crossref")
        else:
            route_type = "unknown"
            reason = "metadata_not_provided"
            sources.add("unknown")
        built.append(
            {
                "route": route,
                "route_type": route_type,
                "route_classification_reason": reason,
            }
        )
    if "metadata" in sources:
        source = "metadata"
    elif "server_endpoints_crossref" in sources:
        source = "server_endpoints_crossref"
    else:
        source = "unknown"
    return built, source


def metadata_matches_intent(metadata: dict[str, object], intent: str) -> bool:
    task_intents = set(
        _expect_string_list("metadata", "task_intents", metadata.get("task_intents", []))
    )
    excluded_task_intents = set(
        _expect_string_list(
            "metadata", "excluded_task_intents", metadata.get("excluded_task_intents", [])
        )
    )
    return intent in task_intents and intent not in excluded_task_intents


def normalize_tooling_metadata(
    entry: dict[str, Any],
    related_route_entries: list[dict[str, str]] | None = None,
    inbound_recommendations: list[str] | None = None,
    metadata_defaults: tuple[str, str] | None = None,
) -> dict[str, object]:
    default_reviewed_at, default_baseline = metadata_defaults or (
        FALLBACK_METADATA_REVIEWED_AT,
        FALLBACK_METADATA_BASELINE,
    )
    return {
        "metadata_reviewed_at": entry.get("metadata_reviewed_at", default_reviewed_at),
        "metadata_baseline": entry.get("metadata_baseline", default_baseline),
        "task_intents": _sorted_strings(list(entry.get("task_intents", []))),
        "primary_task_intents": _sorted_strings(list(entry.get("primary_task_intents", []))),
        "excluded_task_intents": _sorted_strings(list(entry.get("excluded_task_intents", []))),
        "related_artifacts": _sorted_strings(list(entry.get("related_artifacts", []))),
        "related_routes": _sorted_strings(list(entry.get("related_routes", []))),
        "related_route_entries": related_route_entries or [],
        "related_events": _sorted_strings(list(entry.get("related_events", []))),
        "runtime_required": entry.get("runtime_required", None),
        "stability_tier": entry.get("stability_tier", None),
        "recommended_next_reads": _sorted_strings(list(entry.get("recommended_next_reads", []))),
        "inbound_recommendations": _sorted_strings(inbound_recommendations or []),
    }


def build_docs_index(
    repo_root: Path = REPO_ROOT,
    nav_source: str | Path | None = None,
    metadata_path: Path | None = None,
    metadata: dict[str, dict[str, object]] | None = None,
) -> dict[str, object]:
    resolved_nav_source = nav_source if nav_source is not None else DEFAULT_NAV_SOURCE
    resolved_metadata_path = metadata_path if metadata_path is not None else METADATA_PATH
    nav_entries = flatten_nav_from_source(repo_root, resolved_nav_source)
    pages = build_published_docs_surface_from_nav_entries(nav_entries, DOCS_ROOT)
    eligible_paths: set[str] = {str(page["path"]) for page in pages}
    nav_paths = _nav_paths_from_entries(nav_entries)
    resolved_metadata = (
        metadata if metadata is not None else load_docs_index_metadata(resolved_metadata_path)
    )
    validate_docs_index_metadata(
        resolved_metadata,
        eligible_paths,
        nav_paths,
        allowed_artifacts=build_allowed_related_artifacts(repo_root),
    )
    server_routes = load_server_endpoint_routes(
        repo_root / "references" / "raw" / "server_endpoints.json"
    )
    metadata_defaults = load_metadata_freshness_defaults(repo_root)
    inbound_recommendations: dict[str, list[str]] = {path: [] for path in eligible_paths}
    for source_path, source_metadata in resolved_metadata.items():
        for target_path in _expect_string_list(
            source_path,
            "recommended_next_reads",
            source_metadata.get("recommended_next_reads", []),
        ):
            if isinstance(target_path, str) and target_path in inbound_recommendations:
                inbound_recommendations[target_path].append(source_path)

    merged_pages = []
    for page in pages:
        merged = dict(page)
        page_metadata = resolved_metadata.get(str(page["path"]))
        if page_metadata is not None:
            related_route_entries, route_classification_source = build_related_route_entries(
                page_metadata, server_routes
            )
            merged["related_route_entries"] = related_route_entries
            merged["route_classification_source"] = route_classification_source
            merged["tooling_metadata"] = normalize_tooling_metadata(
                page_metadata,
                related_route_entries=related_route_entries,
                inbound_recommendations=inbound_recommendations.get(str(page["path"]), []),
                metadata_defaults=metadata_defaults,
            )
        merged_pages.append(merged)

    return {
        "artifact": "docs-index.json",
        "artifact_schema_version": "1.2.0",
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
    print(f"Generated docs index at {display_path(output_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
