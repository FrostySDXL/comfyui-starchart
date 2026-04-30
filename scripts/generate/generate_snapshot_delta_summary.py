#!/usr/bin/env python3
"""Generate a deterministic delta summary between two artifact baselines."""

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "artifacts" / "delta-summary.json"
CANONICAL_ARTIFACTS = [
    "server_endpoints.json",
    "js_hooks.json",
    "node_api_schema.json",
]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact_map(base_dir: Path) -> dict[str, dict]:
    artifacts = {}
    for name in CANONICAL_ARTIFACTS:
        path = base_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Missing required artifact: {path}")
        artifacts[name] = _load_json(path)
    return artifacts


def _json_key(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _compare_mapping(old_map: dict, new_map: dict) -> dict:
    old_keys = set(old_map)
    new_keys = set(new_map)
    shared_keys = old_keys & new_keys
    changed = sorted(key for key in shared_keys if _json_key(old_map[key]) != _json_key(new_map[key]))
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


def _node_sections(data: dict) -> dict[str, dict]:
    return {
        "object_info_fields": {field: field for field in data.get("object_info_fields", [])},
        "io_types": {
            f"{entry.get('io_type', '')}:{entry.get('class_name', '')}": entry
            for entry in data.get("io_types", [])
        },
        "typed_input_shapes": data.get("typed_input_shapes", {}),
    }


def build_delta_summary(old_artifacts: dict[str, dict], new_artifacts: dict[str, dict], old_label: str, new_label: str) -> dict:
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
            ),
            "node_api_schema": {
                "object_info_fields": _compare_mapping(old_node["object_info_fields"], new_node["object_info_fields"]),
                "io_types": _compare_mapping(old_node["io_types"], new_node["io_types"]),
                "typed_input_shapes": _compare_mapping(old_node["typed_input_shapes"], new_node["typed_input_shapes"]),
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a snapshot delta summary from two artifact baselines")
    parser.add_argument("--old", required=True, help="Directory containing the old baseline artifacts")
    parser.add_argument("--new", required=True, help="Directory containing the new baseline artifacts")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output JSON path")
    args = parser.parse_args()

    old_dir = Path(args.old)
    new_dir = Path(args.new)
    output_path = Path(args.output)

    old_artifacts = _artifact_map(old_dir)
    new_artifacts = _artifact_map(new_dir)
    summary = build_delta_summary(old_artifacts, new_artifacts, old_dir.as_posix(), new_dir.as_posix())

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Generated snapshot delta summary at {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
