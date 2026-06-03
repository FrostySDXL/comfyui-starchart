from __future__ import annotations

from scripts.common.path_normalization import has_backslashes
from scripts.verify.schema_common import _check_type, _type_label

EVENT_SOURCE_SCHEMA = {
    "source_file": (str, True),
    "source_function": ((str, type(None)), True),
    "line": ((int, type(None)), True),
    "method": (str, True),
}

EVENT_TRACEABILITY_SCHEMA = {
    "strategy": (str, True),
    "notes": (list, False),
    "source_file": ((str, type(None)), False),
    "source_function": ((str, type(None)), False),
}

WEBSOCKET_EVENT_SCHEMA = {
    "name": (str, True),
    "direction": (str, True),
    "server_sources": (list, True),
    "frontend_listeners": (list, True),
    "payload_fields": (list, False),
    "payload_notes": (list, False),
    "ast_scan_notes": (list, False),
    "traceability": (dict, True),
}

BINARY_EVENT_SCHEMA = {
    "name": (str, True),
    "enum_value": (int, False),
    "server_sources": (list, True),
    "frontend_listeners": (list, True),
    "payload_notes": (list, False),
    "traceability": (dict, True),
}

VALID_DIRECTIONS = {"server_to_client", "client_to_server", "bidirectional", "unknown"}


def _validate_shape(
    value: dict, schema: dict[str, tuple[object, bool]], filename: str, path: str
) -> list[str]:
    errors: list[str] = []
    for key, (expected_type, required) in schema.items():
        if key not in value:
            if required:
                errors.append(f"{filename}: {path} missing required key '{key}'")
            continue
        if not _check_type(value[key], expected_type):  # type: ignore[arg-type]
            errors.append(
                f"{filename}: {path}.{key} expected {_type_label(expected_type)}, got {type(value[key]).__name__}"  # type: ignore[arg-type]
            )
    return errors


def _validate_source_list(value: object, filename: str, path: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, list):
        return errors
    for index, source in enumerate(value):
        item_path = f"{path}[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{filename}: {item_path} expected dict, got {type(source).__name__}")
            continue
        errors.extend(_validate_shape(source, EVENT_SOURCE_SCHEMA, filename, item_path))
        source_file = source.get("source_file")
        if isinstance(source_file, str) and has_backslashes(source_file):
            errors.append(f"{filename}: {item_path}.source_file contains backslashes")
    return errors


def _validate_string_list(value: object, filename: str, path: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, list):
        return errors
    for index, item in enumerate(value):
        if not isinstance(item, str):
            errors.append(f"{filename}: {path}[{index}] expected str, got {type(item).__name__}")
    return errors


def _validate_traceability(value: object, filename: str, path: str) -> list[str]:
    if not isinstance(value, dict):
        return []
    errors = _validate_shape(value, EVENT_TRACEABILITY_SCHEMA, filename, path)
    errors.extend(_validate_string_list(value.get("notes"), filename, f"{path}.notes"))
    source_file = value.get("source_file")
    if isinstance(source_file, str) and has_backslashes(source_file):
        errors.append(f"{filename}: {path}.source_file contains backslashes")
    return errors


def _validate_event(entry: object, filename: str, path: str) -> list[str]:
    if not isinstance(entry, dict):
        return [f"{filename}: {path} expected dict, got {type(entry).__name__}"]
    errors = _validate_shape(entry, WEBSOCKET_EVENT_SCHEMA, filename, path)
    direction = entry.get("direction")
    if isinstance(direction, str) and direction not in VALID_DIRECTIONS:
        errors.append(f"{filename}: {path}.direction has unknown value '{direction}'")
    errors.extend(
        _validate_source_list(entry.get("server_sources"), filename, f"{path}.server_sources")
    )
    errors.extend(
        _validate_source_list(
            entry.get("frontend_listeners"), filename, f"{path}.frontend_listeners"
        )
    )
    for list_key in ("payload_fields", "payload_notes", "ast_scan_notes"):
        errors.extend(_validate_string_list(entry.get(list_key), filename, f"{path}.{list_key}"))
    errors.extend(
        _validate_traceability(entry.get("traceability"), filename, f"{path}.traceability")
    )
    return errors


def _validate_binary_event(entry: object, filename: str, path: str) -> list[str]:
    if not isinstance(entry, dict):
        return [f"{filename}: {path} expected dict, got {type(entry).__name__}"]
    errors = _validate_shape(entry, BINARY_EVENT_SCHEMA, filename, path)
    errors.extend(
        _validate_source_list(entry.get("server_sources"), filename, f"{path}.server_sources")
    )
    errors.extend(
        _validate_source_list(
            entry.get("frontend_listeners"), filename, f"{path}.frontend_listeners"
        )
    )
    errors.extend(
        _validate_string_list(entry.get("payload_notes"), filename, f"{path}.payload_notes")
    )
    errors.extend(
        _validate_traceability(entry.get("traceability"), filename, f"{path}.traceability")
    )
    return errors


def validate_websocket_events(data: dict, filename: str) -> list[str]:
    errors: list[str] = []
    for index, event in enumerate(data.get("events", [])):
        errors.extend(_validate_event(event, filename, f"events[{index}]"))
    for index, binary_event in enumerate(data.get("binary_events", [])):
        errors.extend(_validate_binary_event(binary_event, filename, f"binary_events[{index}]"))
    return errors
