from __future__ import annotations

import json
import sys
from urllib.parse import urljoin
from urllib.request import urlopen


def load_json(url: str) -> dict:
    with urlopen(url) as response:
        return json.load(response)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(
            "Usage: py -3.11 read_manifest.py <site-base-url> <artifact-key>",
            file=sys.stderr,
        )
        return 1

    base_url, artifact_key = argv[1], argv[2]
    manifest_url = urljoin(base_url.rstrip("/") + "/", "artifacts/manifest.json")
    manifest = load_json(manifest_url)

    entry = manifest.get("artifacts", {}).get(artifact_key)
    if entry is None:
        print(f"Unknown artifact key: {artifact_key}", file=sys.stderr)
        return 1

    print(json.dumps(
        {
            "artifact_schema_version": manifest["artifact_schema_version"],
            "artifact_key": artifact_key,
            "current_url": entry["current_url"],
            "versioned_url": entry["versioned_url"],
            "sha256": entry["sha256"],
            "version": entry["version"],
            "commit": entry["commit"],
            "sources": entry["sources"],
        },
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
