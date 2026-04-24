#!/usr/bin/env python3
"""Validate JSON reference files against their expected schemas.

Checks that each JSON file in references/raw/ has the required top-level
keys, correct value types, and consistent metadata fields. Catches typos,
missing keys, and structural drift before they propagate to generated docs.

Usage:
    python scripts/verify/validate_schema.py

Exits 0 if all files are valid, exits 1 with a report of schema violations.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCES_RAW_DIR = REPO_ROOT / "references" / "raw"
REFERENCES_COMMUNITY_DIR = REPO_ROOT / "references" / "community"

# Schema definitions for each JSON reference file.
# Each schema is a dict of {key: (type, required)} where type is a Python type
# or tuple of types, and required is a bool.
SCHEMAS = {
    "server_endpoints.json": {
        "metadata": (dict, True),
        "endpoints": (list, True),
    },
    "js_hooks.json": {
        "metadata": (dict, True),
        "hooks": (list, True),
    },
    "node_api_schema.json": {
        "metadata": (dict, True),
        "object_info_fields": (list, True),
        "io_types": (list, True),
        "basic_input_shapes": (dict, True),
        "typed_input_shapes": (dict, False),
        "coverage": (dict, False),
        "runtime_object_info": (dict, False),
        "provenance": (dict, False),
    },
    "object_info_runtime.json": {
        "metadata": (dict, True),
        "object_info": (dict, True),
    },
}

# Community schema definitions
COMMUNITY_SCHEMAS = {
    "ecosystem_packages.json": {
        "metadata": (dict, True),
        "packages": (list, True),
    },
    "community_pages.json": {
        "metadata": (dict, True),
        "pages": (list, True),
    },
}

# Metadata field requirements per file type.
# (field_name, type, required)
METADATA_FIELDS = {
    "server_endpoints.json": [
        ("source", str, True),
        ("extracted_date", str, True),
        ("version", str, True),
        ("commit", str, True),
    ],
    "js_hooks.json": [
        ("sources", list, True),
        ("extracted_date", str, True),
        ("version", str, True),
        ("commit", str, True),
    ],
    "node_api_schema.json": [
        ("sources", list, True),
        ("extracted_date", str, True),
        ("version", str, True),
        ("commit", str, True),
    ],
    "object_info_runtime.json": [
        ("url", str, True),
        ("extracted_date", str, True),
        ("version", str, True),
        ("commit", str, True),
        ("response_sha256", str, True),
    ],
}

COMMUNITY_METADATA_FIELDS = {
    "ecosystem_packages.json": [
        ("schema_version", str, True),
        ("last_updated", str, True),
        ("description", str, True),
    ],
    "community_pages.json": [
        ("schema_version", str, True),
        ("last_updated", str, True),
        ("description", str, True),
    ],
}

# Package entry schema
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

# Page entry schema
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

ALLOWED_PACKAGE_CATEGORIES = {
    "package_manager",
    "registry",
    "node_pack",
    "tooling",
}

ALLOWED_PACKAGE_STATUSES = {
    "Actively Maintained",
    "Community Supported",
    "Likely Unmaintained",
    "Unknown",
}

ALLOWED_PACKAGE_SOURCE_TYPES = {
    "official_project",
    "community_observation",
}

ALLOWED_PAGE_KINDS = {
    "generated_catalog",
    "hand_authored_study",
    "hand_authored_tutorial",
    "hand_authored_guide",
    "hand_authored_policy",
}

ALLOWED_PAGE_SOURCE_TYPES = {
    "community_metadata",
    "pinned_external_repo",
    "hybrid",
    "repo_local",
}

# Endpoint schema: required keys and their types
# Note: `returns` is required and must be a structured dict.
# Legacy string values are no longer accepted.
ENDPOINT_SCHEMA = {
    "route": (str, True),
    "method": (str, True),
    "description": (str, True),
    "parameters": (list, True),
    "returns": (dict, True),
}

# Structured return schema for endpoint responses.
# Legacy string placeholders are rejected; extractors must emit structured dicts.
RETURN_SCHEMA = {
    "kind": (str, True),
    "summary": (str, True),
    "status_codes": (list, True),
    "fields": (list, True),
    "notes": (list, True),
}

# Field descriptor inside returns.fields
FIELD_SCHEMA = {
    "name": (str, True),
    "type_hint": (str, False),
    "description": (str, False),
}

# Hook schema: required keys and their types
HOOK_SCHEMA = {
    "name": (str, True),
    "type": (str, True),
    "description": (str, True),
    "defined_in": ((str, type(None)), True),
    "invoked_in": (list, True),
}

# IO type schema
IO_TYPE_SCHEMA = {
    "io_type": (str, True),
    "class_name": (str, True),
    "input_class": ((str, type(None)), True),
    "input_parameters": (list, True),
    "output_parameters": (list, False),
    "type_hint": ((str, type(None)), False),
    "defined_in": (str, False),
    "is_widget": (bool, False),
}


def validate_top_level(data: dict, schema: dict, filename: str) -> list[str]:
    """Validate top-level keys against schema."""
    errors = []
    for key, (expected_type, required) in schema.items():
        if key not in data:
            if required:
                errors.append(f"{filename}: missing required key '{key}'")
            continue
        if not isinstance(data[key], expected_type):
            errors.append(
                f"{filename}: key '{key}' expected {expected_type.__name__}, "
                f"got {type(data[key]).__name__}"
            )

    # Check for unexpected top-level keys
    expected_keys = set(schema.keys())
    actual_keys = set(data.keys())
    unexpected = actual_keys - expected_keys
    if unexpected:
        errors.append(f"{filename}: unexpected top-level keys: {sorted(unexpected)}")

    return errors


def validate_metadata(data: dict, filename: str) -> list[str]:
    """Validate metadata fields."""
    errors = []
    metadata = data.get("metadata")
    if metadata is None:
        # Already caught by top-level schema
        return errors

    fields = METADATA_FIELDS.get(filename, [])
    for field_name, expected_type, required in fields:
        if field_name not in metadata:
            if required:
                errors.append(f"{filename}: metadata missing required field '{field_name}'")
            continue
        value = metadata[field_name]
        if not isinstance(value, expected_type):
            errors.append(
                f"{filename}: metadata.{field_name} expected {expected_type.__name__}, "
                f"got {type(value).__name__}"
            )

    # Check that version starts with 'v'
    version = metadata.get("version", "")
    if version and version != "unversioned" and not version.startswith("v"):
        errors.append(
            f"{filename}: metadata.version '{version}' should start with 'v'"
        )

    # Check that commit is a hex string of reasonable length
    commit = metadata.get("commit", "")
    if commit and not all(c in "0123456789abcdef" for c in commit.lower()):
        errors.append(
            f"{filename}: metadata.commit '{commit}' should be a hex SHA hash"
        )

    # Check that source/sources use forward slashes
    source = metadata.get("source", "")
    if source and "\\" in source:
        errors.append(
            f"{filename}: metadata.source uses backslashes; use forward slashes for cross-platform compatibility"
        )
    sources = metadata.get("sources", [])
    if isinstance(sources, list):
        for s in sources:
            if isinstance(s, str) and "\\" in s:
                errors.append(
                    f"{filename}: metadata.sources contains backslashes; use forward slashes for cross-platform compatibility"
                )

    # Validate provenance if present
    provenance = metadata.get("provenance")
    if isinstance(provenance, dict):
        if "mode" in provenance and provenance["mode"] not in {"source-only", "hybrid"}:
            errors.append(
                f"{filename}: metadata.provenance.mode must be 'source-only' or 'hybrid', got '{provenance['mode']}'"
            )
        for key in ("source_sections", "runtime_sections"):
            if key in provenance and not isinstance(provenance[key], list):
                errors.append(
                    f"{filename}: metadata.provenance.{key} expected list, got {type(provenance[key]).__name__}"
                )

    return errors


def _check_type(value, expected_type) -> bool:
    """Check if value matches expected_type, which may be a single type or tuple of types."""
    if isinstance(expected_type, tuple):
        # Tuple of allowed types (e.g., (str, type(None)))
        return isinstance(value, expected_type)
    return isinstance(value, expected_type)


def _type_label(expected_type) -> str:
    """Human-readable label for an expected type."""
    if isinstance(expected_type, tuple):
        return " | ".join(t.__name__ for t in expected_type)
    return expected_type.__name__


def validate_returns(returns: dict, filename: str, path: str) -> list[str]:
    """Validate a structured returns dict against RETURN_SCHEMA."""
    errors = []
    for key, (expected_type, required) in RETURN_SCHEMA.items():
        if key not in returns:
            if required:
                errors.append(f"{filename}: {path} missing required key '{key}'")
            continue
        if not _check_type(returns[key], expected_type):
            errors.append(
                f"{filename}: {path}.{key} expected {_type_label(expected_type)}, "
                f"got {type(returns[key]).__name__}"
            )

    # Validate status_codes items are integers
    status_codes = returns.get("status_codes", [])
    if isinstance(status_codes, list):
        for j, code in enumerate(status_codes):
            if not isinstance(code, int):
                errors.append(
                    f"{filename}: {path}.status_codes[{j}] expected int, got {type(code).__name__}"
                )

    # Validate fields items
    fields = returns.get("fields", [])
    if isinstance(fields, list):
        for j, field in enumerate(fields):
            if not isinstance(field, dict):
                errors.append(f"{filename}: {path}.fields[{j}] is not a dict")
                continue
            for key, (expected_type, required) in FIELD_SCHEMA.items():
                if key not in field:
                    if required:
                        errors.append(
                            f"{filename}: {path}.fields[{j}] missing required key '{key}'"
                        )
                    continue
                if not _check_type(field[key], expected_type):
                    errors.append(
                        f"{filename}: {path}.fields[{j}].{key} expected {_type_label(expected_type)}, "
                        f"got {type(field[key]).__name__}"
                    )

    # Validate notes items are strings
    notes = returns.get("notes", [])
    if isinstance(notes, list):
        for j, note in enumerate(notes):
            if not isinstance(note, str):
                errors.append(
                    f"{filename}: {path}.notes[{j}] expected str, got {type(note).__name__}"
                )

    return errors


def validate_endpoints(data: dict, filename: str) -> list[str]:
    """Validate endpoint entries."""
    errors = []
    endpoints = data.get("endpoints", [])
    for i, ep in enumerate(endpoints):
        if not isinstance(ep, dict):
            errors.append(f"{filename}: endpoints[{i}] is not a dict")
            continue
        for key, (expected_type, required) in ENDPOINT_SCHEMA.items():
            if key not in ep:
                if required:
                    errors.append(f"{filename}: endpoints[{i}] missing required key '{key}'")
                continue
            if not _check_type(ep[key], expected_type):
                errors.append(
                    f"{filename}: endpoints[{i}].{key} expected {_type_label(expected_type)}, "
                    f"got {type(ep[key]).__name__}"
                )

        # Validate structured returns when present and a dict
        returns = ep.get("returns")
        if isinstance(returns, dict):
            errors.extend(validate_returns(returns, filename, f"endpoints[{i}].returns"))

    return errors


def validate_hooks(data: dict, filename: str) -> list[str]:
    """Validate hook entries."""
    errors = []
    hooks = data.get("hooks", [])
    for i, hook in enumerate(hooks):
        if not isinstance(hook, dict):
            errors.append(f"{filename}: hooks[{i}] is not a dict")
            continue
        for key, (expected_type, required) in HOOK_SCHEMA.items():
            if key not in hook:
                if required:
                    errors.append(f"{filename}: hooks[{i}] missing required key '{key}'")
                continue
            if not _check_type(hook[key], expected_type):
                errors.append(
                    f"{filename}: hooks[{i}].{key} expected {_type_label(expected_type)}, "
                    f"got {type(hook[key]).__name__}"
                )
    return errors


def validate_io_types(data: dict, filename: str) -> list[str]:
    """Validate io_types entries."""
    errors = []
    io_types = data.get("io_types", [])
    for i, entry in enumerate(io_types):
        if not isinstance(entry, dict):
            errors.append(f"{filename}: io_types[{i}] is not a dict")
            continue
        for key, (expected_type, required) in IO_TYPE_SCHEMA.items():
            if key not in entry:
                if required:
                    errors.append(f"{filename}: io_types[{i}] missing required key '{key}'")
                continue
            if not _check_type(entry[key], expected_type):
                errors.append(
                    f"{filename}: io_types[{i}].{key} expected {_type_label(expected_type)}, "
                    f"got {type(entry[key]).__name__}"
                )
    return errors


def validate_object_info_runtime(data: dict, filename: str) -> list[str]:
    """Validate runtime object_info snapshot entries."""
    errors = []
    object_info = data.get("object_info", {})
    if not isinstance(object_info, dict):
        errors.append(f"{filename}: object_info is not a dict")
        return errors

    for key, value in object_info.items():
        if not isinstance(key, str):
            errors.append(f"{filename}: object_info key {key!r} is not a string")
        if not isinstance(value, dict):
            errors.append(f"{filename}: object_info['{key}'] is not a dict")

    return errors


def validate_community_metadata(data: dict, filename: str) -> list[str]:
    """Validate community metadata fields."""
    errors = []
    metadata = data.get("metadata")
    if metadata is None:
        return errors

    fields = COMMUNITY_METADATA_FIELDS.get(filename, [])
    for field_name, expected_type, required in fields:
        if field_name not in metadata:
            if required:
                errors.append(f"{filename}: metadata missing required field '{field_name}'")
            continue
        value = metadata[field_name]
        if not isinstance(value, expected_type):
            errors.append(
                f"{filename}: metadata.{field_name} expected {expected_type.__name__}, "
                f"got {type(value).__name__}"
            )

    return errors


def validate_packages(data: dict, filename: str) -> list[str]:
    """Validate ecosystem package entries."""
    errors = []
    packages = data.get("packages", [])
    seen_slugs = set()
    for i, package in enumerate(packages):
        if not isinstance(package, dict):
            errors.append(f"{filename}: packages[{i}] is not a dict")
            continue
        for key, (expected_type, required) in PACKAGE_SCHEMA.items():
            if key not in package:
                if required:
                    errors.append(f"{filename}: packages[{i}] missing required key '{key}'")
                continue
            if not _check_type(package[key], expected_type):
                errors.append(
                    f"{filename}: packages[{i}].{key} expected {_type_label(expected_type)}, "
                    f"got {type(package[key]).__name__}"
                )

        # Validate notable_patterns items are strings
        notable_patterns = package.get("notable_patterns", [])
        if isinstance(notable_patterns, list):
            for j, pattern in enumerate(notable_patterns):
                if not isinstance(pattern, str):
                    errors.append(
                        f"{filename}: packages[{i}].notable_patterns[{j}] expected str, "
                        f"got {type(pattern).__name__}"
                    )

        # Validate evidence_urls items are strings
        evidence_urls = package.get("evidence_urls", [])
        if isinstance(evidence_urls, list):
            for j, url in enumerate(evidence_urls):
                if not isinstance(url, str):
                    errors.append(
                        f"{filename}: packages[{i}].evidence_urls[{j}] expected str, "
                        f"got {type(url).__name__}"
                    )

        slug = package.get("slug")
        if isinstance(slug, str):
            if slug in seen_slugs:
                errors.append(f"{filename}: duplicate slug '{slug}'")
            else:
                seen_slugs.add(slug)

        category = package.get("category")
        if isinstance(category, str) and category not in ALLOWED_PACKAGE_CATEGORIES:
            errors.append(f"{filename}: packages[{i}] has invalid category '{category}'")

        status = package.get("status")
        if isinstance(status, str) and status not in ALLOWED_PACKAGE_STATUSES:
            errors.append(f"{filename}: packages[{i}] has invalid status '{status}'")

        source_type = package.get("source_type")
        if isinstance(source_type, str) and source_type not in ALLOWED_PACKAGE_SOURCE_TYPES:
            errors.append(
                f"{filename}: packages[{i}] has invalid source_type '{source_type}'"
            )

    return errors


def validate_pages(data: dict, filename: str) -> list[str]:
    """Validate community page entries."""
    errors = []
    pages = data.get("pages", [])
    seen_paths = set()
    for i, page in enumerate(pages):
        if not isinstance(page, dict):
            errors.append(f"{filename}: pages[{i}] is not a dict")
            continue
        for key, (expected_type, required) in PAGE_SCHEMA.items():
            if key not in page:
                if required:
                    errors.append(f"{filename}: pages[{i}] missing required key '{key}'")
                continue
            if not _check_type(page[key], expected_type):
                errors.append(
                    f"{filename}: pages[{i}].{key} expected {_type_label(expected_type)}, "
                    f"got {type(page[key]).__name__}"
                )

        page_path = page.get("page_path")
        if isinstance(page_path, str):
            if "\\" in page_path:
                errors.append(
                    f"{filename}: pages[{i}].page_path uses backslashes; use forward slashes for cross-platform compatibility"
                )
            if page_path in seen_paths:
                errors.append(f"{filename}: duplicate page_path '{page_path}'")
            else:
                seen_paths.add(page_path)

        generated_from = page.get("generated_from")
        if isinstance(generated_from, str) and "\\" in generated_from:
            errors.append(
                f"{filename}: pages[{i}].generated_from uses backslashes; use forward slashes for cross-platform compatibility"
            )

        page_kind = page.get("page_kind")
        if isinstance(page_kind, str) and page_kind not in ALLOWED_PAGE_KINDS:
            errors.append(f"{filename}: pages[{i}] has invalid page_kind '{page_kind}'")

        source_type = page.get("source_type")
        if isinstance(source_type, str) and source_type not in ALLOWED_PAGE_SOURCE_TYPES:
            errors.append(
                f"{filename}: pages[{i}] has invalid source_type '{source_type}'"
            )

    return errors


def _validate_json_file(json_file: Path, all_errors: list[str]) -> None:
    """Validate a single JSON file and append errors to all_errors."""
    print(f"Validating {json_file.name}...")

    try:
        data = json.loads(json_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        all_errors.append(f"{json_file.name}: invalid JSON: {e}")
        return

    if not isinstance(data, dict):
        all_errors.append(f"{json_file.name}: top-level value is not a dict")
        return

    errors = []

    # Validate top-level schema
    schema = SCHEMAS.get(json_file.name) or COMMUNITY_SCHEMAS.get(json_file.name)
    if schema:
        errors = validate_top_level(data, schema, json_file.name)
        all_errors.extend(errors)

    # Validate metadata
    if json_file.name in COMMUNITY_SCHEMAS:
        errors = validate_community_metadata(data, json_file.name)
        all_errors.extend(errors)
    else:
        errors = validate_metadata(data, json_file.name)
        all_errors.extend(errors)

    # Validate entries based on file type
    if json_file.name == "server_endpoints.json":
        errors = validate_endpoints(data, json_file.name)
        all_errors.extend(errors)
    elif json_file.name == "js_hooks.json":
        errors = validate_hooks(data, json_file.name)
        all_errors.extend(errors)
    elif json_file.name == "node_api_schema.json":
        errors = validate_io_types(data, json_file.name)
        all_errors.extend(errors)
    elif json_file.name == "object_info_runtime.json":
        errors = validate_object_info_runtime(data, json_file.name)
        all_errors.extend(errors)
    elif json_file.name == "ecosystem_packages.json":
        errors = validate_packages(data, json_file.name)
        all_errors.extend(errors)
    elif json_file.name == "community_pages.json":
        errors = validate_pages(data, json_file.name)
        all_errors.extend(errors)

    if not errors:
        print(f"  OK: schema valid")


def main():
    """Run schema validation for all JSON reference files."""
    all_errors = []
    json_files = sorted(REFERENCES_RAW_DIR.glob("*.json"))
    community_files = sorted(REFERENCES_COMMUNITY_DIR.glob("*.json"))
    all_json_files = json_files + community_files

    if not all_json_files:
        print("No JSON reference files found.")
        return 1

    for json_file in all_json_files:
        _validate_json_file(json_file, all_errors)

    print()
    if not all_errors:
        print(f"All {len(all_json_files)} JSON file(s) pass schema validation.")
        return 0
    else:
        print(f"Found {len(all_errors)} schema violation(s):")
        for error in all_errors:
            print(f"  {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
