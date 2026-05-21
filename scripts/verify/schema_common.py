from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

from scripts.common.path_normalization import has_backslashes

PUBLISHED_ARTIFACT_SCHEMAS = {
    "server_endpoints.json": "server_endpoints.schema.json",
    "js_hooks.json": "js_hooks.schema.json",
    "node_api_schema.json": "node_api_schema.schema.json",
}

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

RETURN_SCHEMA = {
    "kind": (str, True),
    "summary": (str, True),
    "status_codes": (list, True),
    "fields": (list, True),
    "notes": (list, True),
    "traceability": (dict, False),
}

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

JSON_SCHEMA_TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "null": type(None),
}


def _check_type(value, expected_type) -> bool:
    if isinstance(expected_type, tuple):
        return isinstance(value, expected_type)
    return isinstance(value, expected_type)


def _type_label(expected_type) -> str:
    if isinstance(expected_type, tuple):
        return " | ".join(t.__name__ for t in expected_type)
    return expected_type.__name__


def validate_top_level(data: dict, schema: dict, filename: str) -> list[str]:
    errors = []
    for key, (expected_type, required) in schema.items():
        if key not in data:
            if required:
                errors.append(f"{filename}: missing required key '{key}'")
            continue
        if not isinstance(data[key], expected_type):
            errors.append(
                f"{filename}: key '{key}' expected {expected_type.__name__}, got {type(data[key]).__name__}"
            )

    unexpected = set(data.keys()) - set(schema.keys())
    if unexpected:
        errors.append(f"{filename}: unexpected top-level keys: {sorted(unexpected)}")
    return errors


def validate_metadata(data: dict, filename: str) -> list[str]:
    errors: list[str] = []
    metadata = data.get("metadata")
    if metadata is None:
        return errors
    if not isinstance(metadata, dict):
        errors.append(f"{filename}: metadata expected dict, got {type(metadata).__name__}")
        return errors

    field_specs = cast(list[tuple[str, type[Any], bool]], METADATA_FIELDS.get(filename, []))
    for field_name, expected_type, required in field_specs:
        if field_name not in metadata:
            if required:
                errors.append(f"{filename}: metadata missing required field '{field_name}'")
            continue
        value = metadata[field_name]
        if not isinstance(value, expected_type):
            errors.append(
                f"{filename}: metadata.{field_name} expected {expected_type.__name__}, got {type(value).__name__}"
            )

    if (
        filename in {"server_endpoints.json", "js_hooks.json", "node_api_schema.json"}
        and "source" in metadata
    ):
        errors.append(f"{filename}: metadata.source is not allowed; use metadata.sources list")

    version = metadata.get("version", "")
    if version and version != "unversioned" and not version.startswith("v"):
        errors.append(f"{filename}: metadata.version '{version}' should start with 'v'")

    commit = metadata.get("commit", "")
    if commit and not all(c in "0123456789abcdef" for c in commit.lower()):
        errors.append(f"{filename}: metadata.commit '{commit}' should be a hex SHA hash")

    sources = metadata.get("sources", [])
    if isinstance(sources, list):
        for index, source in enumerate(sources):
            if not isinstance(source, str):
                errors.append(
                    f"{filename}: metadata.sources[{index}] expected str, got {type(source).__name__}"
                )
                continue
            if has_backslashes(source):
                errors.append(
                    f"{filename}: metadata.sources contains backslashes; use forward slashes for cross-platform compatibility"
                )

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


def validate_community_metadata(data: dict, filename: str) -> list[str]:
    errors: list[str] = []
    metadata = data.get("metadata")
    if metadata is None:
        return errors
    if not isinstance(metadata, dict):
        errors.append(f"{filename}: metadata expected dict, got {type(metadata).__name__}")
        return errors
    field_specs = cast(
        list[tuple[str, type[Any], bool]], COMMUNITY_METADATA_FIELDS.get(filename, [])
    )
    for field_name, expected_type, required in field_specs:
        if field_name not in metadata:
            if required:
                errors.append(f"{filename}: metadata missing required field '{field_name}'")
            continue
        value = metadata[field_name]
        if not isinstance(value, expected_type):
            errors.append(
                f"{filename}: metadata.{field_name} expected {expected_type.__name__}, got {type(value).__name__}"
            )
    return errors


def validate_coverage(data: dict, filename: str) -> list[str]:
    if filename not in {"server_endpoints.json", "js_hooks.json", "node_api_schema.json"}:
        return []

    errors: list[str] = []
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
                f"{filename}: coverage.{key} expected {_type_label(expected_type)}, got {type(coverage[key]).__name__}"
            )

    unexpected = set(coverage.keys()) - set(schema.keys())
    if unexpected:
        errors.append(f"{filename}: unexpected coverage keys: {sorted(unexpected)}")

    for list_key in ("guaranteed_fields", "best_effort_fields", "deferred", "sources_covered"):
        value = coverage.get(list_key)
        if isinstance(value, list):
            for index, item in enumerate(value):
                if not isinstance(item, str):
                    errors.append(
                        f"{filename}: coverage.{list_key}[{index}] expected str, got {type(item).__name__}"
                    )
    return errors


def validate_traceability(traceability: dict, filename: str, path: str) -> list[str]:
    errors = []
    for key, (expected_type, required) in TRACEABILITY_SCHEMA.items():
        if key not in traceability:
            if required:
                errors.append(f"{filename}: {path} missing required key '{key}'")
            continue
        if not _check_type(traceability[key], expected_type):
            errors.append(
                f"{filename}: {path}.{key} expected {_type_label(expected_type)}, got {type(traceability[key]).__name__}"
            )
    return errors


def validate_parameter_details(parameters: list, filename: str, path: str) -> list[str]:
    errors = []
    for index, parameter in enumerate(parameters):
        if not isinstance(parameter, dict):
            errors.append(f"{filename}: {path}[{index}] is not a dict")
            continue
        for key, (expected_type, required) in PARAMETER_SCHEMA.items():
            if key not in parameter:
                if required:
                    errors.append(f"{filename}: {path}[{index}] missing required key '{key}'")
                continue
            if not _check_type(parameter[key], expected_type):
                errors.append(
                    f"{filename}: {path}[{index}].{key} expected {_type_label(expected_type)}, got {type(parameter[key]).__name__}"
                )

        allowed_values = parameter.get("allowed_values", [])
        if isinstance(allowed_values, list):
            for value_index, value in enumerate(allowed_values):
                if not isinstance(value, (str, int, float, bool)):
                    errors.append(
                        f"{filename}: {path}[{index}].allowed_values[{value_index}] expected primitive, got {type(value).__name__}"
                    )

        traceability = parameter.get("traceability")
        if isinstance(traceability, dict):
            errors.extend(
                validate_traceability(traceability, filename, f"{path}[{index}].traceability")
            )
    return errors


def validate_returns(returns: dict, filename: str, path: str) -> list[str]:
    errors = []
    for key, (expected_type, required) in RETURN_SCHEMA.items():
        if key not in returns:
            if required:
                errors.append(f"{filename}: {path} missing required key '{key}'")
            continue
        if not _check_type(returns[key], expected_type):
            errors.append(
                f"{filename}: {path}.{key} expected {_type_label(expected_type)}, got {type(returns[key]).__name__}"
            )

    status_codes = returns.get("status_codes", [])
    if isinstance(status_codes, list):
        for index, code in enumerate(status_codes):
            if not isinstance(code, int):
                errors.append(
                    f"{filename}: {path}.status_codes[{index}] expected int, got {type(code).__name__}"
                )

    fields = returns.get("fields", [])
    if isinstance(fields, list):
        for index, field in enumerate(fields):
            if not isinstance(field, dict):
                errors.append(f"{filename}: {path}.fields[{index}] is not a dict")
                continue
            for key, (expected_type, required) in FIELD_SCHEMA.items():
                if key not in field:
                    if required:
                        errors.append(
                            f"{filename}: {path}.fields[{index}] missing required key '{key}'"
                        )
                    continue
                if not _check_type(field[key], expected_type):
                    errors.append(
                        f"{filename}: {path}.fields[{index}].{key} expected {_type_label(expected_type)}, got {type(field[key]).__name__}"
                    )

    notes = returns.get("notes", [])
    if isinstance(notes, list):
        for index, note in enumerate(notes):
            if not isinstance(note, str):
                errors.append(
                    f"{filename}: {path}.notes[{index}] expected str, got {type(note).__name__}"
                )

    traceability = returns.get("traceability")
    if isinstance(traceability, dict):
        errors.extend(validate_traceability(traceability, filename, f"{path}.traceability"))
    return errors


def load_published_artifact_schema(filename: str, published_schema_dir: Path) -> dict | None:
    schema_name = PUBLISHED_ARTIFACT_SCHEMAS.get(filename)
    if not schema_name:
        return None
    return json.loads((published_schema_dir / schema_name).read_text(encoding="utf-8"))


def _instance_matches_json_type(value, expected_type: str) -> bool:
    expected_python_type = cast(
        type[Any] | tuple[type[Any], ...], JSON_SCHEMA_TYPE_MAP[expected_type]
    )
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
    errors: list[str] = []
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


def validate_against_published_artifact_schema(
    data: dict, filename: str, published_schema_dir: Path
) -> list[str]:
    schema_name = PUBLISHED_ARTIFACT_SCHEMAS.get(filename)
    if not schema_name:
        return []

    schema_path = published_schema_dir / schema_name
    if not schema_path.exists():
        return [f"{filename}: published schema file not found: {schema_path}"]

    try:
        schema = load_published_artifact_schema(filename, published_schema_dir)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [f"{filename}: published schema file is invalid JSON: {exc}"]

    if schema is None:
        return []

    return [
        f"{filename}: published schema violation: {error}"
        for error in _validate_json_schema_instance(data, schema, filename)
    ]
