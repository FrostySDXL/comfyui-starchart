"""Read the published delta-summary support artifact."""

from __future__ import annotations

import json
import sys
import urllib.request


def _trim_base(base_url: str) -> str:
    return base_url.rstrip("/")


def _load_delta_summary(base_url: str) -> dict:
    url = f"{_trim_base(base_url)}/artifacts/delta-summary.json"
    with urllib.request.urlopen(url) as response:
        return json.load(response)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(
            "Usage: py -3.11 examples/consumers/python-artifact-delta-reader/read_delta_summary.py <published-site-base-url>",
            file=sys.stderr,
        )
        return 1

    payload = _load_delta_summary(argv[1])
    metadata = payload.get("metadata", {})
    artifacts = payload.get("artifacts", {})

    print(f"Old baseline: {metadata.get('old_version_key', 'unknown')}")
    print(f"New baseline: {metadata.get('new_version_key', 'unknown')}")

    for artifact_name in ("server_endpoints", "js_hooks", "node_api_schema"):
        summary = artifacts.get(artifact_name, {})
        print(
            f"{artifact_name}: added={summary.get('added_count', 0)} removed={summary.get('removed_count', 0)} changed={summary.get('changed_count', 0)}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
