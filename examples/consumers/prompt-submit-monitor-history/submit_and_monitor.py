#!/usr/bin/env python3
"""Submit one workflow, watch bounded WebSocket events, then fetch history."""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from websocket import WebSocketTimeoutException, create_connection

WATCHED_EVENTS = {
    "status",
    "execution_start",
    "execution_cached",
    "executing",
    "executed",
    "progress",
    "execution_success",
    "execution_error",
    "execution_interrupted",
}
TERMINAL_EVENTS = {"execution_success", "execution_error", "execution_interrupted"}


def build_ws_url(base_url: str, client_id: str) -> str:
    parsed = urllib.parse.urlparse(base_url)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    path = parsed.path.rstrip("/")
    ws_path = f"{path}/ws" if path else "/ws"
    query = urllib.parse.urlencode({"clientId": client_id})
    return urllib.parse.urlunparse((scheme, parsed.netloc, ws_path, "", query, ""))


def http_json(url: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def compact_event_message(message_type: str, data: dict) -> str:
    if message_type == "status":
        remaining = data.get("status", {}).get("exec_info", {}).get("queue_remaining")
        sid = data.get("sid")
        return f"status queue_remaining={remaining} sid={sid}"
    if message_type == "executing":
        return f"executing node={data.get('node')} prompt_id={data.get('prompt_id')}"
    if message_type == "executed":
        output_keys = sorted((data.get("output") or {}).keys())
        return f"executed node={data.get('node')} output_keys={output_keys} prompt_id={data.get('prompt_id')}"
    if message_type == "progress":
        return f"progress node={data.get('node')} value={data.get('value')}/{data.get('max')} prompt_id={data.get('prompt_id')}"
    if message_type in TERMINAL_EVENTS:
        return f"{message_type} prompt_id={data.get('prompt_id')}"
    return f"{message_type} prompt_id={data.get('prompt_id')}"


def monitor_prompt(base_url: str, prompt_id: str, client_id: str, timeout_seconds: int) -> str:
    ws_url = build_ws_url(base_url, client_id)
    print(f"WebSocket: {ws_url}")
    deadline = time.time() + timeout_seconds
    last_seen = "timeout"

    with create_connection(ws_url, timeout=5) as ws:
        while time.time() < deadline:
            try:
                raw = ws.recv()
            except WebSocketTimeoutException:
                continue

            if not isinstance(raw, str):
                print("WS binary preview frame received")
                continue

            message = json.loads(raw)
            message_type = message.get("type")
            data = message.get("data") or {}
            if message_type not in WATCHED_EVENTS:
                continue

            event_prompt_id = data.get("prompt_id")
            if event_prompt_id not in {None, prompt_id} and message_type != "status":
                continue

            print(f"WS {compact_event_message(message_type, data)}")
            last_seen = message_type
            if message_type in TERMINAL_EVENTS and event_prompt_id == prompt_id:
                return message_type

    print(f"Timeout reached after {timeout_seconds}s; continuing to history lookup")
    return last_seen


def fetch_history(base_url: str, prompt_id: str) -> dict:
    return http_json(f"{base_url.rstrip('/')}/history/{urllib.parse.quote(prompt_id, safe='')}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Submit one ComfyUI workflow, monitor bounded WebSocket events, and fetch history."
    )
    parser.add_argument("--url", required=True, help="Base ComfyUI URL, for example http://127.0.0.1:8188")
    parser.add_argument("--workflow", required=True, help="Path to an API-format workflow JSON file")
    parser.add_argument("--client-id", default=None, help="Optional stable client ID")
    parser.add_argument("--timeout-seconds", type=int, default=60, help="Bounded WebSocket wait time before history lookup")
    args = parser.parse_args()

    workflow_path = Path(args.workflow)
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    client_id = args.client_id or f"tooling-example-{uuid.uuid4()}"
    payload = {"prompt": workflow, "client_id": client_id}

    try:
        response = http_json(f"{args.url.rstrip('/')}/prompt", method="POST", payload=payload)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"Prompt submission failed with HTTP {exc.code}: {body}", file=sys.stderr)
        return 1

    prompt_id = response.get("prompt_id")
    if not prompt_id:
        print(f"Prompt submission response did not include prompt_id: {response}", file=sys.stderr)
        return 1

    print(f"Submitted prompt_id={prompt_id}")
    print(f"Queue number={response.get('number')}")
    last_event = monitor_prompt(args.url, prompt_id, client_id, args.timeout_seconds)

    try:
        history = fetch_history(args.url, prompt_id)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"History lookup failed with HTTP {exc.code}: {body}", file=sys.stderr)
        return 1

    history_keys = sorted(history.keys()) if isinstance(history, dict) else []
    print(f"History lookup keys={history_keys} last_event={last_event}")
    if prompt_id in history:
        prompt_history = history[prompt_id]
        outputs = sorted((prompt_history.get("outputs") or {}).keys())
        print(f"History entry found for prompt_id={prompt_id} output_nodes={outputs}")
    else:
        print(f"History response did not contain prompt_id={prompt_id}; timeout or retention state may explain this")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
