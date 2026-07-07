"""Print a no-runtime StarChart artifact summary from checked-in files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = REPO_ROOT / "public" / "artifacts" / "manifest.json"
SERVER_ENDPOINTS_PATH = REPO_ROOT / "public" / "artifacts" / "current" / "server_endpoints.json"

KEY_ROUTES = [
    ("POST", "/prompt"),
    ("GET", "/queue"),
    ("GET", "/history/{prompt_id}"),
    ("GET", "/ws"),
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise TypeError(f"Expected JSON object in {path}")
    return data


def endpoint_pairs(server_endpoints: dict[str, Any]) -> set[tuple[str, str]]:
    endpoints = server_endpoints.get("endpoints")
    if not isinstance(endpoints, list):
        raise TypeError("server_endpoints.json must contain an endpoints list")

    pairs: set[tuple[str, str]] = set()
    for endpoint in endpoints:
        if not isinstance(endpoint, dict):
            continue
        method = endpoint.get("method")
        route = endpoint.get("route")
        if isinstance(method, str) and isinstance(route, str):
            pairs.add((method.upper(), route))
    return pairs


def main() -> int:
    manifest = load_json(MANIFEST_PATH)
    server_endpoints = load_json(SERVER_ENDPOINTS_PATH)

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise TypeError("manifest.json must contain an artifacts object")

    print("ComfyUI StarChart baseline")
    print(f"- version_key: {manifest.get('version_key')}")
    print(f"- artifact_schema_version: {manifest.get('artifact_schema_version')}")
    print("- canonical artifacts:")
    for artifact_name in sorted(artifacts):
        artifact = artifacts[artifact_name]
        version = artifact.get("version") if isinstance(artifact, dict) else None
        print(f"  - {artifact_name}: {version}")

    pairs = endpoint_pairs(server_endpoints)
    print("- key local API routes:")
    for method, route in KEY_ROUTES:
        status = "present" if (method, route) in pairs else "missing"
        print(f"  - {method} {route}: {status}")

    print(f"- endpoint count: {len(pairs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
