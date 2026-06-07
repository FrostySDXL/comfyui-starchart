from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

PUBLISHED_ARTIFACT_SCHEMAS = {
    "manifest.json": "manifest.schema.json",
    "server_endpoints.json": "server_endpoints.schema.json",
    "js_hooks.json": "js_hooks.schema.json",
    "node_api_schema.json": "node_api_schema.schema.json",
    "websocket_events.json": "websocket_events.schema.json",
    "docs-index.json": "docs-index.schema.json",
    "delta-summary.json": "delta-summary.schema.json",
    "refresh-provenance.json": "refresh-provenance.schema.json",
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


def _resolve_json_schema_ref(ref: str, root_schema: dict) -> dict | None:
    """Resolve the local JSON Schema references used by checked-in schemas."""
    if not ref.startswith("#/"):
        return None
    target: Any = root_schema
    for part in ref.removeprefix("#/").split("/"):
        if not isinstance(target, dict) or part not in target:
            return None
        target = target[part]
    return target if isinstance(target, dict) else None


def _validate_json_schema_instance(
    instance, schema: dict, path: str, root_schema: dict | None = None
) -> list[str]:
    errors: list[str] = []
    if root_schema is None:
        root_schema = schema

    if "$ref" in schema:
        resolved_schema = _resolve_json_schema_ref(schema["$ref"], root_schema)
        if resolved_schema is None:
            return [f"{path}: unresolved schema reference {schema['$ref']!r}"]
        return _validate_json_schema_instance(instance, resolved_schema, path, root_schema)

    expected_type = schema.get("type")
    if expected_type is not None:
        allowed_types = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(_instance_matches_json_type(instance, json_type) for json_type in allowed_types):
            return [
                f"{path}: expected {_json_schema_type_label(expected_type)}, got {type(instance).__name__}"
            ]

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value {instance!r} not in enum {schema['enum']!r}")

    if "pattern" in schema and isinstance(instance, str):
        if not re.fullmatch(schema["pattern"], instance):
            errors.append(
                f"{path}: value {instance!r} does not match pattern {schema['pattern']!r}"
            )

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
                errors.extend(
                    _validate_json_schema_instance(value, properties[key], child_path, root_schema)
                )
                continue
            matched_pattern = False
            for pattern, pattern_schema in pattern_properties.items():
                if re.fullmatch(pattern, key):
                    matched_pattern = True
                    errors.extend(
                        _validate_json_schema_instance(
                            value, pattern_schema, child_path, root_schema
                        )
                    )
            if matched_pattern:
                continue
            if additional_properties is False:
                errors.append(f"{path}: unexpected key '{key}'")
            elif isinstance(additional_properties, dict):
                errors.extend(
                    _validate_json_schema_instance(
                        value, additional_properties, child_path, root_schema
                    )
                )

    if isinstance(instance, list) and "items" in schema:
        for index, item in enumerate(instance):
            errors.extend(
                _validate_json_schema_instance(
                    item, schema["items"], f"{path}[{index}]", root_schema
                )
            )
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
