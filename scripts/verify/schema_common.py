from __future__ import annotations

from typing import Any, cast

from scripts.common.path_normalization import has_backslashes
from scripts.verify import published_schema_validation as _published_schema_validation

PUBLISHED_ARTIFACT_SCHEMAS = _published_schema_validation.PUBLISHED_ARTIFACT_SCHEMAS
load_published_artifact_schema = _published_schema_validation.load_published_artifact_schema
validate_against_published_artifact_schema = (
    _published_schema_validation.validate_against_published_artifact_schema
)

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
        "prompt_conditioning_surface": (dict, False),
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
    "guaranteed_fields": (list, False),
    "best_effort_fields": (list, False),
    "deferred": (list, True),
}

PROMPT_CONDITIONING_ENTRY_SCHEMA: dict[str, tuple[Any, bool]] = {
    "io_type": (str, True),
    "class_name": (str, True),
    "input_class": ((str, type(None)), False),
    "input_parameters": (list, False),
    "output_parameters": (list, False),
    "input_parameter_details": (list, False),
    "output_parameter_details": (list, False),
    "type_hint": ((str, type(None)), False),
    "defined_in": (str, False),
    "is_widget": (bool, False),
    "io_type_description": (str, False),
    "supports_multiline_parameter": (bool, False),
    "traceability": (dict, False),
}

PROMPT_CONDITIONING_SURFACE_SCHEMA = {
    "traceability": (dict, False),
    "text_input_io_types": (list, False),
    "conditioning_io_types": (list, False),
    "runtime_node_output_summary": (list, False),
}


def _check_type(value, expected_type) -> bool:
    if isinstance(expected_type, tuple):
        return isinstance(value, expected_type)
    return isinstance(value, expected_type)


def _type_label(expected_type) -> str:
    if isinstance(expected_type, tuple):
        return " | ".join(t.__name__ for t in expected_type)
    return expected_type.__name__


def _validate_schema_shape(
    data: dict,
    schema: dict[str, tuple[Any, bool]],
    filename: str,
    section: str,
) -> list[str]:
    """Validate *data* against *schema* of ``(expected_type, required)`` pairs.

    *section* is used in error messages (e.g. ``"top-level"``,
    ``"coverage"``, ``"prompt_conditioning_surface"``).
    """
    errors: list[str] = []
    for key, (expected_type, required) in schema.items():
        if key not in data:
            if required:
                errors.append(f"{filename}: {section} missing required key '{key}'")
            continue
        if not _check_type(data[key], expected_type):
            errors.append(
                f"{filename}: {section}.{key} expected {_type_label(expected_type)}, "
                f"got {type(data[key]).__name__}"
            )

    unexpected = set(data.keys()) - set(schema.keys())
    if unexpected:
        errors.append(f"{filename}: unexpected {section} keys: {sorted(unexpected)}")
    return errors


def validate_top_level(data: dict, schema: dict, filename: str) -> list[str]:
    return _validate_schema_shape(data, schema, filename, "top-level")


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
    errors.extend(_validate_schema_shape(coverage, schema, filename, "coverage"))

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


def validate_prompt_conditioning_surface(data: dict, filename: str) -> list[str]:
    errors: list[str] = []
    surface = data.get("prompt_conditioning_surface")
    if surface is None:
        return errors
    if not isinstance(surface, dict):
        return [
            f"{filename}: prompt_conditioning_surface expected dict, got {type(surface).__name__}"
        ]

    errors.extend(
        _validate_schema_shape(
            surface,
            PROMPT_CONDITIONING_SURFACE_SCHEMA,
            filename,
            "prompt_conditioning_surface",
        )
    )

    for list_key in ("text_input_io_types", "conditioning_io_types", "runtime_node_output_summary"):
        value = surface.get(list_key)
        if isinstance(value, list):
            inner_path = f"prompt_conditioning_surface.{list_key}"
            for index, item in enumerate(value):
                if not isinstance(item, dict):
                    errors.append(
                        f"{filename}: {inner_path}[{index}] expected dict, got {type(item).__name__}"
                    )
                    continue
                for field_name, (
                    expected_type,
                    required,
                ) in PROMPT_CONDITIONING_ENTRY_SCHEMA.items():
                    if field_name not in item:
                        if required:
                            errors.append(
                                f"{filename}: {inner_path}[{index}] missing required key '{field_name}'"
                            )
                        continue
                    if not _check_type(item[field_name], expected_type):
                        errors.append(
                            f"{filename}: {inner_path}[{index}].{field_name} expected {_type_label(expected_type)}, got {type(item[field_name]).__name__}"
                        )
                traceability = item.get("traceability")
                if isinstance(traceability, dict):
                    errors.extend(
                        validate_traceability(
                            traceability, filename, f"{inner_path}[{index}].traceability"
                        )
                    )

    return errors
