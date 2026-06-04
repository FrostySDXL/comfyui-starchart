#!/usr/bin/env python3
"""Generate a deterministic delta summary between two artifact baselines."""

import argparse
import json
from pathlib import Path

from scripts.common.display_path import display_path
from scripts.common.json_utils import write_json

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "public" / "artifacts" / "delta-summary.json"
CANONICAL_ARTIFACTS = [
    "server_endpoints.json",
    "js_hooks.json",
    "node_api_schema.json",
    "websocket_events.json",
]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


REQUIRED_ARTIFACTS = [
    "server_endpoints.json",
    "js_hooks.json",
    "node_api_schema.json",
]


def _artifact_map(base_dir: Path) -> dict[str, dict]:
    artifacts = {}
    for name in CANONICAL_ARTIFACTS:
        path = base_dir / name
        if not path.exists():
            if name in REQUIRED_ARTIFACTS:
                raise FileNotFoundError(f"Missing required artifact: {path}")
            print(f"Warning: optional artifact not found, skipping: {path}")
            continue
        artifacts[name] = _load_json(path)
    return artifacts


def _json_key(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _normalize_snapshot_source_path(path: object) -> object:
    if not isinstance(path, str):
        return path
    normalized = path.replace("\\", "/")
    snapshot_marker = "references/snapshots/"
    snapshot_index = normalized.find(snapshot_marker)
    if snapshot_index != -1:
        snapshot_relative = normalized[snapshot_index + len(snapshot_marker) :]
        parts = snapshot_relative.split("/", 2)
        if len(parts) == 3:
            return parts[2]
    marker = "/src/"
    marker_index = normalized.find(marker)
    if marker_index != -1:
        return normalized[marker_index + 1 :]
    return normalized


def _normalize_hook_for_comparison(hook: dict) -> dict:
    traceability = hook.get("traceability")
    normalized_traceability = traceability
    if isinstance(traceability, dict):
        normalized_traceability = {
            "source_type": traceability.get("source_type"),
            "strategy": traceability.get("strategy"),
        }

    return {
        "name": hook.get("name"),
        "type": hook.get("type"),
        "description": hook.get("description"),
        "defined_in": _normalize_snapshot_source_path(hook.get("defined_in")),
        "invoked_in": sorted(
            _normalize_snapshot_source_path(path) for path in hook.get("invoked_in", [])
        ),
        "signature": hook.get("signature"),
        "arguments": hook.get("arguments", []),
        "return_type": hook.get("return_type"),
        "invocation_style": hook.get("invocation_style", []),
        "traceability": normalized_traceability,
    }


def _normalize_traceability_for_comparison(traceability: object) -> object:
    if isinstance(traceability, dict):
        return {
            "source_type": traceability.get("source_type"),
            "strategy": traceability.get("strategy"),
        }
    return traceability


def _normalize_node_schema_field_details(details: object) -> object:
    if not isinstance(details, list):
        return details
    normalized = []
    for detail in details:
        if isinstance(detail, dict):
            normalized.append(
                {
                    **detail,
                    "defined_in": _normalize_snapshot_source_path(detail.get("defined_in")),
                    "traceability": _normalize_traceability_for_comparison(
                        detail.get("traceability")
                    ),
                }
            )
        else:
            normalized.append(detail)
    return normalized


def _normalize_io_type_for_comparison(entry: dict) -> dict:
    return {
        "io_type": entry.get("io_type"),
        "class_name": entry.get("class_name"),
        "input_class": entry.get("input_class"),
        "input_parameters": entry.get("input_parameters", []),
        "output_parameters": entry.get("output_parameters", []),
        "input_parameter_details": _normalize_node_schema_field_details(
            entry.get("input_parameter_details", [])
        ),
        "output_parameter_details": _normalize_node_schema_field_details(
            entry.get("output_parameter_details", [])
        ),
        "type_hint": entry.get("type_hint"),
        "defined_in": _normalize_snapshot_source_path(entry.get("defined_in")),
        "is_widget": entry.get("is_widget"),
    }


def _normalize_typed_input_shape_field(field: object) -> object:
    if isinstance(field, dict):
        return {
            **field,
            "defined_in": _normalize_snapshot_source_path(field.get("defined_in")),
            "traceability": _normalize_traceability_for_comparison(field.get("traceability")),
        }
    return field


def _normalize_typed_input_shape_for_comparison(shape: object) -> object:
    if not isinstance(shape, dict):
        return shape  # basic_input_shapes values are plain type-name strings
    fields = shape.get("fields", {})
    normalized_fields = (
        {name: _normalize_typed_input_shape_field(value) for name, value in fields.items()}
        if isinstance(fields, dict)
        else fields
    )
    return {
        "description": shape.get("description"),
        "defined_in": _normalize_snapshot_source_path(shape.get("defined_in")),
        "fields": normalized_fields,
    }


def _compare_mapping(old_map: dict, new_map: dict, *, normalizer=None) -> dict:
    old_keys = set(old_map)
    new_keys = set(new_map)
    shared_keys = old_keys & new_keys
    changed = sorted(
        key
        for key in shared_keys
        if _json_key(normalizer(old_map[key]) if normalizer else old_map[key])
        != _json_key(normalizer(new_map[key]) if normalizer else new_map[key])
    )
    return {
        "old_count": len(old_map),
        "new_count": len(new_map),
        "added": sorted(new_keys - old_keys),
        "removed": sorted(old_keys - new_keys),
        "changed": changed,
    }


def _server_endpoint_map(data: dict) -> dict[str, dict]:
    return {
        f"{endpoint.get('method', 'UNKNOWN')} {endpoint.get('route', '')}": endpoint
        for endpoint in data.get("endpoints", [])
    }


def _hook_map(data: dict) -> dict[str, dict]:
    return {hook.get("name", ""): hook for hook in data.get("hooks", [])}


def _normalize_prompt_conditioning_entry(entry: dict) -> dict:
    """Normalize a single prompt conditioning entry for comparison."""
    return {
        **entry,
        "defined_in": _normalize_snapshot_source_path(entry.get("defined_in")),
        "traceability": _normalize_traceability_for_comparison(entry.get("traceability")),
    }


def _node_sections(data: dict) -> dict[str, dict]:
    prompt = data.get("prompt_conditioning_surface", {})
    prompt_text = prompt.get("text_input_io_types", [])
    prompt_cond = prompt.get("conditioning_io_types", [])
    return {
        "object_info_fields": {field: field for field in data.get("object_info_fields", [])},
        "io_types": {
            f"{entry.get('io_type', '')}:{entry.get('class_name', '')}": entry
            for entry in data.get("io_types", [])
        },
        "typed_input_shapes": data.get("typed_input_shapes", {}),
        "prompt_conditioning_surface": {
            "text_input_io_types": {
                f"{entry.get('io_type', '')}:{entry.get('class_name', '')}": entry
                for entry in prompt_text
            },
            "conditioning_io_types": {
                f"{entry.get('io_type', '')}:{entry.get('class_name', '')}": entry
                for entry in prompt_cond
            },
        },
        "basic_input_shapes": data.get("basic_input_shapes", {}),
    }


def _websocket_event_map(data: dict) -> dict[str, dict]:
    return {event.get("name", ""): event for event in data.get("events", [])}


def _binary_event_map(data: dict) -> dict[str, dict]:
    return {binary.get("name", ""): binary for binary in data.get("binary_events", [])}


def _normalize_websocket_event_for_comparison(event: dict) -> dict:
    """Normalize a websocket event for provenance-agnostic comparison.

    Strips snapshot-path prefixes from source_file values in server_sources
    and frontend_listeners, and normalizes traceability structure.
    """
    normalized_server_sources = []
    for src in event.get("server_sources", []):
        if isinstance(src, dict):
            normalized_server_sources.append(
                {
                    "source_file": _normalize_snapshot_source_path(src.get("source_file")),
                    "source_function": src.get("source_function"),
                }
            )
        else:
            normalized_server_sources.append(src)

    normalized_frontend_listeners = []
    for listener in event.get("frontend_listeners", []):
        if isinstance(listener, dict):
            normalized_frontend_listeners.append(
                {
                    "source_file": _normalize_snapshot_source_path(listener.get("source_file")),
                    "source_function": listener.get("source_function"),
                    "method": listener.get("method"),
                }
            )
        else:
            normalized_frontend_listeners.append(listener)

    return {
        "name": event.get("name"),
        "direction": event.get("direction"),
        "server_sources": normalized_server_sources,
        "frontend_listeners": normalized_frontend_listeners,
        "payload_fields": event.get("payload_fields", []),
        "payload_notes": event.get("payload_notes", []),
        "traceability": _normalize_traceability_for_comparison(event.get("traceability")),
    }


def _normalize_binary_event_for_comparison(binary: dict) -> dict:
    """Normalize a binary event for provenance-agnostic comparison."""
    normalized_server_sources = []
    for src in binary.get("server_sources", []):
        if isinstance(src, dict):
            normalized_server_sources.append(
                {
                    "source_file": _normalize_snapshot_source_path(src.get("source_file")),
                    "source_function": src.get("source_function"),
                }
            )
        else:
            normalized_server_sources.append(src)

    normalized_frontend_listeners = []
    for listener in binary.get("frontend_listeners", []):
        if isinstance(listener, dict):
            normalized_frontend_listeners.append(
                {
                    "source_file": _normalize_snapshot_source_path(listener.get("source_file")),
                    "source_function": listener.get("source_function"),
                    "method": listener.get("method"),
                }
            )
        else:
            normalized_frontend_listeners.append(listener)

    traceability = binary.get("traceability")
    normalized_traceability = traceability
    if isinstance(traceability, dict):
        normalized_traceability = {
            "source_file": _normalize_snapshot_source_path(traceability.get("source_file")),
            "source_function": traceability.get("source_function"),
            "strategy": traceability.get("strategy"),
        }

    return {
        "name": binary.get("name"),
        "enum_value": binary.get("enum_value"),
        "server_sources": normalized_server_sources,
        "frontend_listeners": normalized_frontend_listeners,
        "payload_notes": binary.get("payload_notes", []),
        "traceability": normalized_traceability,
    }


def build_delta_summary(
    old_artifacts: dict[str, dict], new_artifacts: dict[str, dict], old_label: str, new_label: str
) -> dict:
    old_node = _node_sections(old_artifacts["node_api_schema.json"])
    new_node = _node_sections(new_artifacts["node_api_schema.json"])
    return {
        "comparison": {
            "old": old_label,
            "new": new_label,
        },
        "notes": [
            "Deterministic artifact-to-artifact comparison only.",
            "Does not claim runtime truth or semantic compatibility beyond the compared JSON baselines.",
        ],
        "artifacts": {
            "server_endpoints": _compare_mapping(
                _server_endpoint_map(old_artifacts["server_endpoints.json"]),
                _server_endpoint_map(new_artifacts["server_endpoints.json"]),
            ),
            "js_hooks": _compare_mapping(
                _hook_map(old_artifacts["js_hooks.json"]),
                _hook_map(new_artifacts["js_hooks.json"]),
                normalizer=_normalize_hook_for_comparison,
            ),
            "node_api_schema": {
                "object_info_fields": _compare_mapping(
                    old_node["object_info_fields"], new_node["object_info_fields"]
                ),
                "io_types": _compare_mapping(
                    old_node["io_types"],
                    new_node["io_types"],
                    normalizer=_normalize_io_type_for_comparison,
                ),
                "typed_input_shapes": _compare_mapping(
                    old_node["typed_input_shapes"],
                    new_node["typed_input_shapes"],
                    normalizer=_normalize_typed_input_shape_for_comparison,
                ),
                "prompt_conditioning_surface": {
                    "text_input_io_types": _compare_mapping(
                        old_node["prompt_conditioning_surface"]["text_input_io_types"],
                        new_node["prompt_conditioning_surface"]["text_input_io_types"],
                        normalizer=_normalize_prompt_conditioning_entry,
                    ),
                    "conditioning_io_types": _compare_mapping(
                        old_node["prompt_conditioning_surface"]["conditioning_io_types"],
                        new_node["prompt_conditioning_surface"]["conditioning_io_types"],
                        normalizer=_normalize_prompt_conditioning_entry,
                    ),
                },
                "basic_input_shapes": _compare_mapping(
                    old_node["basic_input_shapes"],
                    new_node["basic_input_shapes"],
                    normalizer=_normalize_typed_input_shape_for_comparison,
                ),
            },
            "websocket_events": {
                "events": _compare_mapping(
                    _websocket_event_map(old_artifacts.get("websocket_events.json", {})),
                    _websocket_event_map(new_artifacts.get("websocket_events.json", {})),
                    normalizer=_normalize_websocket_event_for_comparison,
                ),
                "binary_events": _compare_mapping(
                    _binary_event_map(old_artifacts.get("websocket_events.json", {})),
                    _binary_event_map(new_artifacts.get("websocket_events.json", {})),
                    normalizer=_normalize_binary_event_for_comparison,
                ),
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a snapshot delta summary from two artifact baselines. "
            "After running refresh_snapshots.py, pass the auto-created "
            "references/_refresh_backups/raw_<timestamp> directory as --old."
        )
    )
    parser.add_argument(
        "--old",
        required=True,
        help="Directory containing the old baseline artifacts (typically the auto-created references/_refresh_backups/raw_<timestamp> path)",
    )
    parser.add_argument(
        "--new", required=True, help="Directory containing the new baseline artifacts"
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output JSON path")
    args = parser.parse_args()

    old_dir = Path(args.old)
    new_dir = Path(args.new)
    output_path = Path(args.output)

    old_artifacts = _artifact_map(old_dir)
    new_artifacts = _artifact_map(new_dir)
    summary = build_delta_summary(
        old_artifacts, new_artifacts, old_dir.as_posix(), new_dir.as_posix()
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Generated snapshot delta summary at {display_path(output_path)}")

    _update_provenance_delta_flag()
    return 0


def _update_provenance_delta_flag() -> None:
    """Update refresh-provenance.json published flag after successful delta-summary generation.

    Sets delta_summary_updated_by_refresh to true so the provenance record
    accurately reflects that this follow-up step completed.  No-op if the
    provenance file does not exist.
    """
    provenance_path = REPO_ROOT / "public" / "artifacts" / "refresh-provenance.json"
    if not provenance_path.is_file():
        return
    data = _load_json(provenance_path)
    published = data.setdefault("published", {})
    published["delta_summary_updated_by_refresh"] = True
    published.setdefault("provenance_path", "public/artifacts/refresh-provenance.json")
    write_json(provenance_path, data)
    print(f"Updated {display_path(provenance_path)} published flags.")


if __name__ == "__main__":
    raise SystemExit(main())
