#!/usr/bin/env python3
"""Validate JSON reference files against their expected schemas."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts.verify.schema_common import (
    COMMUNITY_SCHEMAS,
    SCHEMAS,
    validate_community_metadata,
    validate_coverage,
    validate_metadata,
    validate_returns,
    validate_top_level,
)
from scripts.verify.schema_common import (
    validate_against_published_artifact_schema as _validate_against_published_artifact_schema,
)
from scripts.verify.schema_community import validate_packages, validate_pages
from scripts.verify.schema_hooks import HOOK_ARGUMENT_SCHEMA, HOOK_SCHEMA, validate_hooks
from scripts.verify.schema_node_api import (
    IO_TYPE_SCHEMA,
    TYPED_INPUT_FIELD_SCHEMA,
    TYPED_INPUT_SHAPE_SCHEMA,
    validate_io_types,
    validate_object_info_runtime,
    validate_typed_input_shapes,
)
from scripts.verify.schema_server import ENDPOINT_SCHEMA, validate_endpoints

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCES_RAW_DIR = REPO_ROOT / "references" / "raw"
REFERENCES_COMMUNITY_DIR = REPO_ROOT / "references" / "community"
PUBLISHED_SCHEMA_DIR = REPO_ROOT / "public" / "artifacts" / "schemas"

__all__ = [
    "COMMUNITY_SCHEMAS",
    "ENDPOINT_SCHEMA",
    "HOOK_ARGUMENT_SCHEMA",
    "HOOK_SCHEMA",
    "IO_TYPE_SCHEMA",
    "SCHEMAS",
    "TYPED_INPUT_FIELD_SCHEMA",
    "TYPED_INPUT_SHAPE_SCHEMA",
    "validate_against_published_artifact_schema",
    "validate_community_metadata",
    "validate_coverage",
    "validate_endpoints",
    "validate_hooks",
    "validate_io_types",
    "validate_metadata",
    "validate_object_info_runtime",
    "validate_packages",
    "validate_pages",
    "validate_returns",
    "validate_top_level",
    "validate_typed_input_shapes",
    "main",
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
    schema = SCHEMAS.get(json_file.name) or COMMUNITY_SCHEMAS.get(json_file.name)
    if schema:
        validation_errors.extend(validate_top_level(data, schema, json_file.name))

    if json_file.name in COMMUNITY_SCHEMAS:
        validation_errors.extend(validate_community_metadata(data, json_file.name))
    else:
        validation_errors.extend(validate_metadata(data, json_file.name))

    if json_file.name in {"server_endpoints.json", "js_hooks.json", "node_api_schema.json"}:
        validation_errors.extend(validate_coverage(data, json_file.name))
        validation_errors.extend(validate_against_published_artifact_schema(data, json_file.name))

    if json_file.name == "server_endpoints.json":
        validation_errors.extend(validate_endpoints(data, json_file.name))
    elif json_file.name == "js_hooks.json":
        validation_errors.extend(validate_hooks(data, json_file.name))
    elif json_file.name == "node_api_schema.json":
        validation_errors.extend(validate_io_types(data, json_file.name))
        validation_errors.extend(validate_typed_input_shapes(data, json_file.name))
    elif json_file.name == "object_info_runtime.json":
        validation_errors.extend(validate_object_info_runtime(data, json_file.name))
    elif json_file.name == "ecosystem_packages.json":
        validation_errors.extend(validate_packages(data, json_file.name))
    elif json_file.name == "community_pages.json":
        validation_errors.extend(validate_pages(data, json_file.name))

    all_errors.extend(validation_errors)
    if not validation_errors:
        print("  OK: schema valid")


def main() -> int:
    all_errors: list[str] = []
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

    print(f"Found {len(all_errors)} schema violation(s):")
    for error in all_errors:
        print(f"  {error}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
