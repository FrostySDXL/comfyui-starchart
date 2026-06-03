#!/usr/bin/env python3
"""Validate JSON reference files against their expected schemas."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.verify.published_schema_validation import (
    validate_against_published_artifact_schema as _validate_against_published_artifact_schema,
)
from scripts.verify.schema_common import (
    SCHEMAS,
    validate_coverage,
    validate_metadata,
    validate_prompt_conditioning_surface,
    validate_server_runtime_contracts,
    validate_top_level,
)
from scripts.verify.schema_hooks import validate_hooks
from scripts.verify.schema_node_api import (
    validate_io_types,
    validate_object_info_runtime,
    validate_typed_input_shapes,
)
from scripts.verify.schema_server import validate_endpoints
from scripts.verify.schema_websocket_events import validate_websocket_events

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCES_RAW_DIR = REPO_ROOT / "references" / "raw"
PUBLISHED_SCHEMA_DIR = REPO_ROOT / "public" / "artifacts" / "schemas"
DOCS_INDEX_PATH = REPO_ROOT / "public" / "artifacts" / "docs-index.json"
SUPPORT_ARTIFACT_PATHS = [
    REPO_ROOT / "public" / "artifacts" / "delta-summary.json",
    REPO_ROOT / "public" / "artifacts" / "refresh-provenance.json",
]


def validate_against_published_artifact_schema(data: dict, filename: str) -> list[str]:
    """Compatibility wrapper that preserves the legacy two-argument call shape."""
    return _validate_against_published_artifact_schema(data, filename, PUBLISHED_SCHEMA_DIR)


def _validate_json_file(json_file: Path, all_errors: list[str]) -> None:
    print(f"Validating {json_file.name}...")

    try:
        data = json.loads(json_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        all_errors.append(f"{json_file.name}: invalid JSON: {exc}")
        return

    if not isinstance(data, dict):
        all_errors.append(f"{json_file.name}: top-level value is not a dict")
        return

    validation_errors: list[str] = []
    schema = SCHEMAS.get(json_file.name)
    if schema:
        validation_errors.extend(validate_top_level(data, schema, json_file.name))  # type: ignore[arg-type]

    if json_file.name in SCHEMAS:
        validation_errors.extend(validate_metadata(data, json_file.name))

    if json_file.name in {
        "server_endpoints.json",
        "js_hooks.json",
        "node_api_schema.json",
        "websocket_events.json",
    }:
        validation_errors.extend(validate_coverage(data, json_file.name))
    if json_file.name in {
        "server_endpoints.json",
        "js_hooks.json",
        "node_api_schema.json",
        "websocket_events.json",
        "docs-index.json",
        "delta-summary.json",
        "refresh-provenance.json",
    }:
        validation_errors.extend(validate_against_published_artifact_schema(data, json_file.name))

    if json_file.name == "server_endpoints.json":
        validation_errors.extend(validate_endpoints(data, json_file.name))
        validation_errors.extend(validate_server_runtime_contracts(data, json_file.name))
    elif json_file.name == "js_hooks.json":
        validation_errors.extend(validate_hooks(data, json_file.name))
    elif json_file.name == "node_api_schema.json":
        validation_errors.extend(validate_io_types(data, json_file.name))
        validation_errors.extend(validate_typed_input_shapes(data, json_file.name))
        validation_errors.extend(validate_prompt_conditioning_surface(data, json_file.name))
    elif json_file.name == "object_info_runtime.json":
        validation_errors.extend(validate_object_info_runtime(data, json_file.name))
    elif json_file.name == "websocket_events.json":
        validation_errors.extend(validate_websocket_events(data, json_file.name))

    all_errors.extend(validation_errors)
    if not validation_errors:
        print("  OK: schema valid")


def main() -> int:
    all_errors: list[str] = []
    json_files = sorted(REFERENCES_RAW_DIR.glob("*.json"))
    # manifest.json remains intentionally excluded from this schema-enforcement wave.
    all_json_files = json_files + [DOCS_INDEX_PATH, *SUPPORT_ARTIFACT_PATHS]

    if not all_json_files:
        print("No JSON reference files found.")
        return 1

    for json_file in all_json_files:
        _validate_json_file(json_file, all_errors)

    print()
    if not all_errors:
        print(f"All {len(all_json_files)} JSON file(s) pass schema validation.")
        return 0

    print(f"Found {len(all_errors)} schema violation(s):")
    for error in all_errors:
        print(f"  {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
