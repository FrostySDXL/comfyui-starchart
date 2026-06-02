#!/usr/bin/env python3
"""Runtime smoke verification against a live ComfyUI instance.

Runs a minimal, lightweight sequence of checks against a running ComfyUI
instance to verify basic API availability and shape consistency.

Usage:
    python scripts/verify/runtime_smoke.py --url http://127.0.0.1:8188
    python scripts/verify/runtime_smoke.py --url http://127.0.0.1:8188 --skip-prompt

Exits 0 if all checks pass, exits 1 on the first failure.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast

from scripts.common import http_utils
from scripts.common.display_path import display_path

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_PROMPT_PATH = REPO_ROOT / "examples" / "api-calls" / "post-prompt.json"


def _fetch_json(url: str, timeout: int = 30) -> dict:
    """Fetch JSON from a URL."""
    return cast(dict[str, Any], http_utils.get_json(url, timeout=timeout))


def _post_json(url: str, payload: dict, timeout: int = 30) -> dict:
    """POST JSON to a URL and return the response."""
    return cast(dict[str, Any], http_utils.post_json(url, payload, timeout=timeout))


def check_features(base_url: str, timeout: int) -> bool:
    """Verify GET /features returns a dict."""
    url = base_url.rstrip("/") + "/features"
    data = _fetch_json(url, timeout)
    if not isinstance(data, dict):
        print(f"FAIL: /features returned {type(data).__name__}, expected dict", file=sys.stderr)
        return False
    print("OK: /features")
    return True


def check_system_stats(base_url: str, timeout: int) -> bool:
    """Verify GET /system_stats returns a dict."""
    url = base_url.rstrip("/") + "/system_stats"
    data = _fetch_json(url, timeout)
    if not isinstance(data, dict):
        print(f"FAIL: /system_stats returned {type(data).__name__}, expected dict", file=sys.stderr)
        return False
    print("OK: /system_stats")
    return True


def check_object_info(base_url: str, timeout: int) -> bool:
    """Verify GET /object_info returns a dict with at least one node."""
    url = base_url.rstrip("/") + "/object_info"
    data = _fetch_json(url, timeout)
    if not isinstance(data, dict):
        print(f"FAIL: /object_info returned {type(data).__name__}, expected dict", file=sys.stderr)
        return False
    if not data:
        print("FAIL: /object_info returned empty dict", file=sys.stderr)
        return False
    print(f"OK: /object_info ({len(data)} nodes)")
    return True


def check_post_prompt(base_url: str, prompt_path: Path, timeout: int) -> bool:
    """Verify POST /prompt accepts a valid payload and returns a dict."""
    if not prompt_path.exists():
        print(f"SKIP: prompt payload not found at {display_path(prompt_path)}")
        return True

    payload = json.loads(prompt_path.read_text(encoding="utf-8"))
    url = base_url.rstrip("/") + "/prompt"
    try:
        data = _post_json(url, payload, timeout)
    except RuntimeError as exc:
        print(f"FAIL: POST /prompt failed: {exc}", file=sys.stderr)
        return False

    if not isinstance(data, dict):
        print(f"FAIL: POST /prompt returned {type(data).__name__}, expected dict", file=sys.stderr)
        return False
    print("OK: POST /prompt")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Runtime smoke verification against a live ComfyUI instance."
    )
    parser.add_argument("--url", required=True, help="Base URL of the running ComfyUI instance")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP request timeout in seconds")
    parser.add_argument("--skip-prompt", action="store_true", help="Skip POST /prompt check")
    parser.add_argument(
        "--prompt-path",
        default=str(DEFAULT_PROMPT_PATH),
        help="Path to the prompt JSON payload for POST /prompt",
    )
    args = parser.parse_args()

    checks = [
        ("GET /features", lambda: check_features(args.url, args.timeout)),
        ("GET /system_stats", lambda: check_system_stats(args.url, args.timeout)),
        ("GET /object_info", lambda: check_object_info(args.url, args.timeout)),
    ]

    if not args.skip_prompt:
        checks.append(
            (
                "POST /prompt",
                lambda: check_post_prompt(args.url, Path(args.prompt_path), args.timeout),
            )
        )

    for name, check in checks:
        if not check():
            print(f"\nSMOKE FAILED at {name}", file=sys.stderr)
            return 1

    print("\nAll runtime smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
