#!/usr/bin/env python3
"""Fetch runtime /object_info from a live ComfyUI instance and persist a pinned snapshot.

Usage:
    python scripts/extract/parse_from_api.py --url http://127.0.0.1:8188 --version v0.20.1 --commit <sha> --output references/raw/object_info_runtime.json

Exits 0 on success, exits 1 on HTTP/network/JSON decode failures.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from scripts.common import http_utils
from scripts.common.json_utils import compute_bytes_sha256

REPO_ROOT = Path(__file__).resolve().parents[2]


def fetch_object_info(url: str, timeout: int) -> tuple[dict, bytes]:
    """Fetch /object_info from a running ComfyUI instance.

    Returns the parsed JSON response plus raw response bytes.
    Raises RuntimeError on network, HTTP, or JSON decode failures.
    """
    endpoint = url.rstrip("/") + "/object_info"
    payload, data = http_utils.get_json_with_bytes(endpoint, timeout=timeout)

    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected dict response from {endpoint}, got {type(payload).__name__}")

    return payload, data


def compute_sha256(data: bytes) -> str:
    """Return the SHA-256 hex digest of data."""
    return compute_bytes_sha256(data)


def build_snapshot(
    url: str, version: str | None, commit: str | None, object_info: dict, raw_bytes: bytes
) -> dict:
    """Build a deterministic runtime snapshot payload."""
    return {
        "metadata": {
            "url": url.rstrip("/"),
            "version": version or "unversioned",
            "commit": commit or "",
            "extracted_date": datetime.now().strftime("%Y-%m-%d"),
            "response_sha256": compute_sha256(raw_bytes),
        },
        "object_info": object_info,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch runtime /object_info from a live ComfyUI instance and persist a pinned snapshot."
    )
    parser.add_argument("--url", required=True, help="Base URL of the running ComfyUI instance")
    parser.add_argument("--version", default=None, help="Pinned upstream version or tag")
    parser.add_argument("--commit", default=None, help="Pinned upstream commit hash")
    parser.add_argument(
        "--output", default="references/raw/object_info_runtime.json", help="Output JSON path"
    )
    parser.add_argument("--timeout", type=int, default=30, help="HTTP request timeout in seconds")
    args = parser.parse_args()

    try:
        payload, raw_bytes = fetch_object_info(args.url, args.timeout)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    snapshot = build_snapshot(args.url, args.version, args.commit, payload, raw_bytes)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted runtime object_info to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
