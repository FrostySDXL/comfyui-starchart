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
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.common.path_normalization import has_backslashes

REFERENCES_RAW_DIR = REPO_ROOT / "references" / "raw"
REFERENCES_COMMUNITY_DIR = REPO_ROOT / "references" / "community"
PUBLISHED_SCHEMA_DIR = REPO_ROOT / "public" / "artifacts" / "schemas"

PUBLISHED_ARTIFACT_SCHEMAS = {
    "server_endpoints.json": "server_endpoints.schema.json",
    "js_hooks.json": "js_hooks.schema.json",
    "node_api_schema.json": "node_api_schema.schema.json",
}

# Schema definitions for each JSON reference file.
# Each schema is a dict of {key: (type, required)} where type is a Python type
# or tuple of types, and required is a bool.
SCHEMAS = {
    "server_endpoints.json": {
        "metadata": (dict, True),
        "coverage": (dict, True),
        "endpoints": (list, True),
    },
    "js_hooks.json": {
        "metadata": (dict, True),
        "coverage": (dict, True),
        "hooks": (list, True),
    },
    "node_api_schema.json": {
        "metadata": (dict, True),
        "object_info_fields": (list, True),
        "io_types": (list, True),
        "basic_input_shapes": (dict, True),
        "typed_input_shapes": (dict, False),
        "coverage": (dict, True),
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
        ("sources", list, True),
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

TRACEABILITY_SCHEMA = {
    "source_type": (str, True),
    "strategy": (str, True),
    "detail": (str, False),
}

PARAMETER_SCHEMA = {
    "name": (str, True),
    "location": (str, True),
    "type_hint": ((str, type(None)), False),
    "required": (bool, False),
    "default": ((str, int, float, bool, type(None)), False),
    "allowed_values": (list, False),
    "traceability": (dict, False),
}

# Structured return schema for endpoint responses.
# Legacy string placeholders are rejected; extractors must emit structured dicts.
RETURN_SCHEMA = {
    "kind": (str, True),
    "summary": (str, True),
    "status_codes": (list, True),
    "fields": (list, True),
    "notes": (list, True),
    "traceability": (dict, False),
}

# Field descriptor inside returns.fields
FIELD_SCHEMA = {
    "name": (str, True),
    "type_hint": (str, False),
    "description": (str, False),
}

COVERAGE_SCHEMA = {
    "description": (str, True),
    "guaranteed_fields": (list, True),
    "best_effort_fields": (list, True),
    "deferred": (list, True),
}

NODE_API_COVERAGE_SCHEMA = {
    "description": (str, True),
    "sources_covered": (list, True),
    "runtime_enriched": (bool, True),
    "deferred": (list, True),
}

# Hook schema: required keys and their types
HOOK_SCHEMA = {
    "name": (str, True),
    "type": (str, True),
    "description": (str, True),
    "defined_in": ((str, type(None)), True),
    "invoked_in": (list, True),
    "signature": ((str, type(None)), False),
    "arguments": (list, False),
    "return_type": ((str, type(None)), False),
    "invocation_style": (list, False),
    "traceability": (dict, False),
}

HOOK_ARGUMENT_SCHEMA = {
    "name": (str, True),
    "type_hint": ((str, type(None)), False),
}

# IO type schema
IO_TYPE_SCHEMA = {
    "io_type": (str, True),
    "class_name": (str, True),
    "input_class": ((str, type(None)), True),
    "input_parameters": (list, True),
    "output_parameters": (list, False),
    "input_parameter_details": (list, False),
    "output_parameter_details": (list, False),
    "type_hint": ((str, type(None)), False),
    "defined_in": (str, False),
    "is_widget": (bool, False),
}

TYPED_INPUT_SHAPE_SCHEMA = {
    "description": (str, True),
    "fields": (dict, True),
    "defined_in": (str, False),
}

TYPED_INPUT_FIELD_SCHEMA = {
    "type": (str, True),
    "description": (str, False),
    "traceability": (dict, False),
}


JSON_SCHEMA_TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "null": type(None),
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

    if filename in {"server_endpoints.json", "js_hooks.json", "node_api_schema.json"}:
        if "source" in metadata:
            errors.append(f"{filename}: metadata.source is not allowed; use metadata.sources list")

    # Check that version starts with 'v'
    version = metadata.get("version", "")
    if version and version != "unversioned" and not version.startswith("v"):
        errors.append(f"{filename}: metadata.version '{version}' should start with 'v'")

    # Check that commit is a hex string of reasonable length
    commit = metadata.get("commit", "")
    if commit and not all(c in "0123456789abcdef" for c in commit.lower()):
        errors.append(f"{filename}: metadata.commit '{commit}' should be a hex SHA hash")

    # Check that source/sources use forward slashes
    sources = metadata.get("sources", [])
    if isinstance(sources, list):
        for i, s in enumerate(sources):
            if not isinstance(s, str):
                errors.append(
                    f"{filename}: metadata.sources[{i}] expected str, got {type(s).__name__}"
                )
                continue
            if has_backslashes(s):
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


def validate_coverage(data: dict, filename: str) -> list[str]:
    """Validate coverage blocks for canonical artifacts."""
    if filename not in {
        "server_endpoints.json",
        "js_hooks.json",
        "node_api_schema.json",
    }:
        return []

    errors = []
    coverage = data.get("coverage")
    if coverage is None:
        return errors
    if not isinstance(coverage, dict):
        return [f"{filename}: coverage expected dict, got {type(coverage).__name__}"]

    schema = NODE_API_COVERAGE_SCHEMA if filename == "node_api_schema.json" else COVERAGE_SCHEMA
    for key, (expected_type, required) in schema.items():
        if key not in coverage:
            if required:
                errors.append(f"{filename}: coverage missing required key '{key}'")
            continue
        if not _check_type(coverage[key], expected_type):
            errors.append(
                f"{filename}: coverage.{key} expected {_type_label(expected_type)}, "
                f"got {type(coverage[key]).__name__}"
            )

    expected_keys = set(schema.keys())
    actual_keys = set(coverage.keys())
    unexpected = actual_keys - expected_keys
    if unexpected:
        errors.append(f"{filename}: unexpected coverage keys: {sorted(unexpected)}")

    for list_key in ("guaranteed_fields", "best_effort_fields", "deferred", "sources_covered"):
        value = coverage.get(list_key)
        if isinstance(value, list):
            for i, item in enumerate(value):
                if not isinstance(item, str):
                    errors.append(
                        f"{filename}: coverage.{list_key}[{i}] expected str, got {type(item).__name__}"
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


def validate_traceability(traceability: dict, filename: str, path: str) -> list[str]:
    """Validate a traceability/provenance object."""
    errors = []
    for key, (expected_type, required) in TRACEABILITY_SCHEMA.items():
        if key not in traceability:
            if required:
                errors.append(f"{filename}: {path} missing required key '{key}'")
            continue
        if not _check_type(traceability[key], expected_type):
            errors.append(
                f"{filename}: {path}.{key} expected {_type_label(expected_type)}, "
                f"got {type(traceability[key]).__name__}"
            )
    return errors


def validate_parameter_details(parameters: list, filename: str, path: str) -> list[str]:
    """Validate endpoint or io-parameter detail entries."""
    errors = []
    for i, parameter in enumerate(parameters):
        if not isinstance(parameter, dict):
            errors.append(f"{filename}: {path}[{i}] is not a dict")
            continue
        for key, (expected_type, required) in PARAMETER_SCHEMA.items():
            if key not in parameter:
                if required:
                    errors.append(f"{filename}: {path}[{i}] missing required key '{key}'")
                continue
            if not _check_type(parameter[key], expected_type):
                errors.append(
                    f"{filename}: {path}[{i}].{key} expected {_type_label(expected_type)}, "
                    f"got {type(parameter[key]).__name__}"
                )

        allowed_values = parameter.get("allowed_values", [])
        if isinstance(allowed_values, list):
            for j, value in enumerate(allowed_values):
                if not isinstance(value, (str, int, float, bool)):
                    errors.append(
                        f"{filename}: {path}[{i}].allowed_values[{j}] expected primitive, got {type(value).__name__}"
                    )

        traceability = parameter.get("traceability")
        if isinstance(traceability, dict):
            errors.extend(
                validate_traceability(traceability, filename, f"{path}[{i}].traceability")
            )
    return errors


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

    traceability = returns.get("traceability")
    if isinstance(traceability, dict):
        errors.extend(validate_traceability(traceability, filename, f"{path}.traceability"))

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

        parameters = ep.get("parameters")
        if isinstance(parameters, list):
            errors.extend(
                validate_parameter_details(parameters, filename, f"endpoints[{i}].parameters")
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

        arguments = hook.get("arguments", [])
        if isinstance(arguments, list):
            for j, argument in enumerate(arguments):
                if not isinstance(argument, dict):
                    errors.append(f"{filename}: hooks[{i}].arguments[{j}] is not a dict")
                    continue
                for key, (expected_type, required) in HOOK_ARGUMENT_SCHEMA.items():
                    if key not in argument:
                        if required:
                            errors.append(
                                f"{filename}: hooks[{i}].arguments[{j}] missing required key '{key}'"
                            )
                        continue
                    if not _check_type(argument[key], expected_type):
                        errors.append(
                            f"{filename}: hooks[{i}].arguments[{j}].{key} expected {_type_label(expected_type)}, "
                            f"got {type(argument[key]).__name__}"
                        )

        invocation_style = hook.get("invocation_style", [])
        if isinstance(invocation_style, list):
            for j, style in enumerate(invocation_style):
                if not isinstance(style, str):
                    errors.append(
                        f"{filename}: hooks[{i}].invocation_style[{j}] expected str, got {type(style).__name__}"
                    )

        traceability = hook.get("traceability")
        if isinstance(traceability, dict):
            errors.extend(validate_traceability(traceability, filename, f"hooks[{i}].traceability"))
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

        for detail_key in ("input_parameter_details", "output_parameter_details"):
            details = entry.get(detail_key)
            if isinstance(details, list):
                errors.extend(
                    validate_parameter_details(details, filename, f"io_types[{i}].{detail_key}")
                )
    return errors


def validate_typed_input_shapes(data: dict, filename: str) -> list[str]:
    """Validate typed_input_shapes enrichment blocks."""
    errors = []
    typed_input_shapes = data.get("typed_input_shapes", {})
    if not isinstance(typed_input_shapes, dict):
        return errors

    for shape_name, shape in typed_input_shapes.items():
        if not isinstance(shape, dict):
            errors.append(f"{filename}: typed_input_shapes['{shape_name}'] is not a dict")
            continue

        for key, (expected_type, required) in TYPED_INPUT_SHAPE_SCHEMA.items():
            if key not in shape:
                if required:
                    errors.append(
                        f"{filename}: typed_input_shapes['{shape_name}'] missing required key '{key}'"
                    )
                continue
            if not _check_type(shape[key], expected_type):
                errors.append(
                    f"{filename}: typed_input_shapes['{shape_name}'].{key} expected {_type_label(expected_type)}, "
                    f"got {type(shape[key]).__name__}"
                )

        fields = shape.get("fields", {})
        if isinstance(fields, dict):
            for field_name, field in fields.items():
                if not isinstance(field, dict):
                    errors.append(
                        f"{filename}: typed_input_shapes['{shape_name}'].fields['{field_name}'] is not a dict"
                    )
                    continue
                for key, (expected_type, required) in TYPED_INPUT_FIELD_SCHEMA.items():
                    if key not in field:
                        if required:
                            errors.append(
                                f"{filename}: typed_input_shapes['{shape_name}'].fields['{field_name}'] missing required key '{key}'"
                            )
                        continue
                    if not _check_type(field[key], expected_type):
                        errors.append(
                            f"{filename}: typed_input_shapes['{shape_name}'].fields['{field_name}'].{key} expected {_type_label(expected_type)}, "
                            f"got {type(field[key]).__name__}"
                        )

                traceability = field.get("traceability")
                if isinstance(traceability, dict):
                    errors.extend(
                        validate_traceability(
                            traceability,
                            filename,
                            f"typed_input_shapes['{shape_name}'].fields['{field_name}'].traceability",
                        )
                    )

    return errors


def load_published_artifact_schema(filename: str) -> dict | None:
    """Load a published artifact JSON Schema from public/artifacts/schemas/."""
    schema_name = PUBLISHED_ARTIFACT_SCHEMAS.get(filename)
    if not schema_name:
        return None
    return json.loads((PUBLISHED_SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))


def _instance_matches_json_type(value, expected_type: str) -> bool:
    expected_python_type = JSON_SCHEMA_TYPE_MAP[expected_type]
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, expected_python_type)


def _json_schema_type_label(expected_type) -> str:
    if isinstance(expected_type, list):
        return " | ".join(expected_type)
    return expected_type


def _validate_json_schema_instance(instance, schema: dict, path: str) -> list[str]:
    """Validate an instance against the supported JSON Schema subset used here."""
    errors = []

    expected_type = schema.get("type")
    if expected_type is not None:
        allowed_types = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(_instance_matches_json_type(instance, json_type) for json_type in allowed_types):
            return [
                f"{path}: expected {_json_schema_type_label(expected_type)}, got {type(instance).__name__}"
            ]

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value {instance!r} not in enum {schema['enum']!r}")

    if isinstance(instance, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        pattern_properties = schema.get("patternProperties", {})
        additional_properties = schema.get("additionalProperties", True)

        for key in required:
            if key not in instance:
                errors.append(f"{path}: missing required key '{key}'")

        for key, value in instance.items():
            child_path = f"{path}.{key}" if path else key
            if key in properties:
                errors.extend(_validate_json_schema_instance(value, properties[key], child_path))
                continue

            matched_pattern = False
            for pattern, pattern_schema in pattern_properties.items():
                if re.fullmatch(pattern, key):
                    matched_pattern = True
                    errors.extend(_validate_json_schema_instance(value, pattern_schema, child_path))
            if matched_pattern:
                continue

            if additional_properties is False:
                errors.append(f"{path}: unexpected key '{key}'")
            elif isinstance(additional_properties, dict):
                errors.extend(
                    _validate_json_schema_instance(value, additional_properties, child_path)
                )

    if isinstance(instance, list) and "items" in schema:
        for index, item in enumerate(instance):
            errors.extend(_validate_json_schema_instance(item, schema["items"], f"{path}[{index}]"))

    return errors


def validate_against_published_artifact_schema(data: dict, filename: str) -> list[str]:
    """Validate a canonical artifact against its published JSON Schema file."""
    schema_name = PUBLISHED_ARTIFACT_SCHEMAS.get(filename)
    if not schema_name:
        return []

    schema_path = PUBLISHED_SCHEMA_DIR / schema_name
    if not schema_path.exists():
        return [f"{filename}: published schema file not found: {schema_path}"]

    try:
        schema = load_published_artifact_schema(filename)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [f"{filename}: published schema file is invalid JSON: {exc}"]

    return [
        f"{filename}: published schema violation: {error}"
        for error in _validate_json_schema_instance(data, schema, filename)
    ]


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
            errors.append(f"{filename}: packages[{i}] has invalid source_type '{source_type}'")

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
            errors.append(f"{filename}: pages[{i}] has invalid source_type '{source_type}'")

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

    if json_file.name in {"server_endpoints.json", "js_hooks.json", "node_api_schema.json"}:
        errors = validate_coverage(data, json_file.name)
        all_errors.extend(errors)

        errors = validate_against_published_artifact_schema(data, json_file.name)
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
        errors = validate_typed_input_shapes(data, json_file.name)
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
        print("  OK: schema valid")


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
