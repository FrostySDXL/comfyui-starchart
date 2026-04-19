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
}

# Endpoint schema: required keys and their types
ENDPOINT_SCHEMA = {
    "route": (str, True),
    "method": (str, True),
    "description": (str, True),
    "parameters": (list, True),
    "returns": (str, False),
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


def main():
    """Run schema validation for all JSON reference files."""
    all_errors = []
    json_files = sorted(REFERENCES_RAW_DIR.glob("*.json"))

    if not json_files:
        print("No JSON reference files found.")
        return 1

    for json_file in json_files:
        print(f"Validating {json_file.name}...")

        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            all_errors.append(f"{json_file.name}: invalid JSON: {e}")
            continue

        if not isinstance(data, dict):
            all_errors.append(f"{json_file.name}: top-level value is not a dict")
            continue

        # Validate top-level schema
        schema = SCHEMAS.get(json_file.name)
        if schema:
            errors = validate_top_level(data, schema, json_file.name)
            all_errors.extend(errors)

        # Validate metadata
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

        if not errors:
            print(f"  OK: schema valid")

    print()
    if not all_errors:
        print(f"All {len(json_files)} JSON file(s) pass schema validation.")
        return 0
    else:
        print(f"Found {len(all_errors)} schema violation(s):")
        for error in all_errors:
            print(f"  {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())