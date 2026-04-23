#!/usr/bin/env python3
"""Poll a ComfyUI endpoint until it returns ready JSON."""

import argparse
import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def fetch_json(url: str, timeout: int) -> dict:
    """Fetch JSON from a URL and require a dict response."""
    req = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read())
    except HTTPError as exc:
        raise RuntimeError(f"HTTP error {exc.code} from {url}: {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"URL error reaching {url}: {exc.reason}") from exc
    except TimeoutError as exc:
        raise RuntimeError(f"Timeout reaching {url} after {timeout}s") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON from {url}: {exc}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected dict response from {url}, got {type(payload).__name__}")

    return payload


def wait_for_runtime(url: str, timeout: int, interval: float, require_non_empty: bool) -> int:
    """Poll a JSON endpoint until it is ready or the timeout expires."""
    deadline = time.monotonic() + timeout
    last_error = "no response yet"

    while True:
        try:
            payload = fetch_json(url, timeout=max(1, int(interval) or 1))
            if require_non_empty and not payload:
                last_error = f"{url} returned an empty dict"
            else:
                print(f"Ready: {url}")
                return 0
        except RuntimeError as exc:
            last_error = str(exc)

        if time.monotonic() >= deadline:
            print(f"ERROR: {url} not ready within {timeout}s. Last error: {last_error}", file=sys.stderr)
            return 1

        time.sleep(interval)


def main() -> int:
    parser = argparse.ArgumentParser(description="Wait for a ComfyUI JSON endpoint to become ready.")
    parser.add_argument("--url", required=True, help="Full endpoint URL to poll")
    parser.add_argument("--timeout", type=int, default=120, help="Total wait timeout in seconds")
    parser.add_argument("--interval", type=float, default=2.0, help="Polling interval in seconds")
    parser.add_argument(
        "--require-non-empty",
        action="store_true",
        help="Require the endpoint to return a non-empty dict before succeeding",
    )
    args = parser.parse_args()
    return wait_for_runtime(args.url, args.timeout, args.interval, args.require_non_empty)


if __name__ == "__main__":
    raise SystemExit(main())
