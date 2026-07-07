from __future__ import annotations

import hashlib
import json
import sys
from typing import Any
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.request import urlopen


SUMMARY_FIELDS = {
    "server_endpoints.json": ("endpoints", "coverage"),
    "js_hooks.json": ("hooks", "coverage"),
    "node_api_schema.json": ("object_info_fields", "io_types", "coverage"),
}


def load_json_bytes(url: str) -> tuple[bytes, Any]:
    with urlopen(url) as response:
        body = response.read()
    return body, json.loads(body)


def bytes_for_checksum(url: str, body: bytes) -> bytes:
    if urlparse(url).scheme != "file":
        return body

    return body.replace(b"\r\n", b"\n")


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(
            "Usage: py -3.11 validate_artifact.py <site-base-url> <artifact-key>",
            file=sys.stderr,
        )
        return 1

    base_url, artifact_key = argv[1], argv[2]
    manifest_url = urljoin(base_url.rstrip("/") + "/", "artifacts/manifest.json")
    _, manifest = load_json_bytes(manifest_url)

    entry = manifest.get("artifacts", {}).get(artifact_key)
    if entry is None:
        print(f"Unknown artifact key: {artifact_key}", file=sys.stderr)
        return 1

    artifact_url = urljoin(base_url.rstrip("/") + "/", entry["current_url"])
    artifact_bytes, artifact = load_json_bytes(artifact_url)
    actual_sha256 = hashlib.sha256(bytes_for_checksum(artifact_url, artifact_bytes)).hexdigest()

    if actual_sha256 != entry["sha256"]:
        print(
            f"Checksum mismatch for {artifact_key}: {actual_sha256} != {entry['sha256']}",
            file=sys.stderr,
        )
        return 1

    summary_keys = SUMMARY_FIELDS.get(artifact_key, ())
    summary = {key: key in artifact for key in summary_keys}
    if "coverage" in artifact:
        summary["guaranteed_fields"] = artifact["coverage"].get("guaranteed_fields", [])
        summary["best_effort_fields"] = artifact["coverage"].get("best_effort_fields", [])

    print(json.dumps(
        {
            "artifact_key": artifact_key,
            "artifact_url": artifact_url,
            "checksum_valid": True,
            "strict_consumer_note": "Build strict tooling against guaranteed fields only.",
            "summary": summary,
        },
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
