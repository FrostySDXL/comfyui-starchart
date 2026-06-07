#!/usr/bin/env python3
"""Watch bounded ComfyUI WebSocket events and skip binary preview frames."""

from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path

from websocket import WebSocketTimeoutException, create_connection

HELPER_PATH = Path(__file__).resolve().parents[1] / "prompt-submit-monitor-history" / "submit_and_monitor.py"
HELPER_SPEC = importlib.util.spec_from_file_location("prompt_submit_monitor_history", HELPER_PATH)
submit_and_monitor = importlib.util.module_from_spec(HELPER_SPEC)
HELPER_SPEC.loader.exec_module(submit_and_monitor)

WATCHED_EVENTS = submit_and_monitor.WATCHED_EVENTS
build_ws_url = submit_and_monitor.build_ws_url
compact_event_message = submit_and_monitor.compact_event_message
is_binary_frame = submit_and_monitor.is_binary_frame


def describe_frame(payload: object, prompt_id: str | None = None) -> str | None:
    if is_binary_frame(payload):
        return "binary preview frame skipped"

    message = json.loads(payload)
    message_type = message.get("type")
    data = message.get("data") or {}
    if message_type not in WATCHED_EVENTS:
        return None

    event_prompt_id = data.get("prompt_id")
    if prompt_id and event_prompt_id not in {None, prompt_id} and message_type != "status":
        return None
    return compact_event_message(message_type, data)


def watch_events(base_url: str, client_id: str, timeout_seconds: int, prompt_id: str | None = None) -> None:
    ws_url = build_ws_url(base_url, client_id)
    print(f"WebSocket: {ws_url}")
    deadline = time.time() + timeout_seconds

    with create_connection(ws_url, timeout=5) as ws:
        while time.time() < deadline:
            try:
                payload = ws.recv()
            except WebSocketTimeoutException:
                continue
            description = describe_frame(payload, prompt_id=prompt_id)
            if description:
                print(f"WS {description}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Watch bounded ComfyUI WebSocket events.")
    parser.add_argument("--url", required=True, help="Base ComfyUI URL, for example http://127.0.0.1:8188")
    parser.add_argument("--client-id", required=True, help="Client ID used for the WebSocket connection")
    parser.add_argument("--prompt-id", default=None, help="Optional prompt_id filter for prompt-scoped events")
    parser.add_argument("--timeout-seconds", type=int, default=60, help="Bounded WebSocket watch duration")
    args = parser.parse_args()

    watch_events(args.url, args.client_id, args.timeout_seconds, prompt_id=args.prompt_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
