#!/usr/bin/env python3
"""Opt-in live ComfyUI smoke checks for repo-local examples only."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Any, cast

from scripts.common import http_utils

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROMPT_PATH = REPO_ROOT / "examples" / "api-calls" / "post-prompt.json"
DEFAULT_COMFYUI_ROOT = Path("D:/projects/comfyui-test-runtime")
EXAMPLE_EXTENSION_ROUTE = "/minimal-route-registration/ping"
REQUIRED_PROMPT_CLASS_TYPES = {
    "CheckpointLoaderSimple",
    "CLIPTextEncode",
    "EmptyLatentImage",
    "KSampler",
    "VAEDecode",
    "SaveImage",
}


def fetch_json(url: str, timeout: int) -> dict[str, Any]:
    return cast(dict[str, Any], http_utils.get_json(url, timeout=timeout))


def post_json(url: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    return cast(dict[str, Any], http_utils.post_json(url, payload, timeout=timeout))


def build_prompt_payload(prompt_path: Path, *, model_name: str, client_id: str) -> dict[str, Any]:
    payload = json.loads(prompt_path.read_text(encoding="utf-8"))
    payload["client_id"] = client_id
    replace_model_placeholder(payload, model_name)
    return cast(dict[str, Any], payload)


def replace_model_placeholder(value: Any, model_name: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "ckpt_name" and child == "YOUR_MODEL_NAME_HERE.safetensors":
                value[key] = model_name
            else:
                replace_model_placeholder(child, model_name)
    elif isinstance(value, list):
        for child in value:
            replace_model_placeholder(child, model_name)


def missing_required_prompt_classes(object_info: dict[str, Any]) -> list[str]:
    return sorted(REQUIRED_PROMPT_CLASS_TYPES - set(object_info))


def check_object_info(base_url: str, timeout: int) -> bool:
    object_info = fetch_json(f"{base_url.rstrip('/')}/object_info", timeout)
    missing = missing_required_prompt_classes(object_info)
    if missing:
        print(
            f"FAIL: /object_info missing prompt example node classes: {', '.join(missing)}",
            file=sys.stderr,
        )
        return False
    print("OK: /object_info includes prompt example node classes")
    return True


def check_prompt_submission(
    base_url: str, prompt_path: Path, model_name: str, timeout: int
) -> bool:
    client_id = f"starchart-example-smoke-{uuid.uuid4()}"
    payload = build_prompt_payload(prompt_path, model_name=model_name, client_id=client_id)
    response = post_json(f"{base_url.rstrip('/')}/prompt", payload, timeout)
    if not response.get("prompt_id"):
        print(f"FAIL: POST /prompt response lacks prompt_id: {response}", file=sys.stderr)
        return False
    print(f"OK: POST /prompt returned prompt_id={response['prompt_id']}")
    return True


def check_websocket_status(base_url: str, timeout: int) -> bool:
    try:
        from websocket import create_connection
    except ImportError:
        print("FAIL: websocket-client is not installed", file=sys.stderr)
        return False

    ws_url = base_url.rstrip("/").replace("https://", "wss://").replace("http://", "ws://")
    ws_url = f"{ws_url}/ws?clientId=starchart-example-smoke-{uuid.uuid4()}"
    ws = create_connection(ws_url, timeout=timeout)
    try:
        message = ws.recv()
    finally:
        ws.close()
    if not isinstance(message, str):
        print("FAIL: first WebSocket frame was binary, expected status JSON", file=sys.stderr)
        return False
    payload = json.loads(message)
    if payload.get("type") != "status":
        print(f"FAIL: first WebSocket message was not status: {payload}", file=sys.stderr)
        return False
    print("OK: WebSocket status event")
    return True


def check_extension_route(base_url: str, timeout: int) -> bool:
    payload = fetch_json(f"{base_url.rstrip('/')}{EXAMPLE_EXTENSION_ROUTE}", timeout)
    if payload.get("message") != "route ready":
        print(f"FAIL: extension route returned unexpected payload: {payload}", file=sys.stderr)
        return False
    print(f"OK: {EXAMPLE_EXTENSION_ROUTE}")
    return True


def check_expected_object_info_nodes(
    base_url: str, expected_nodes: list[str], timeout: int
) -> bool:
    object_info = fetch_json(f"{base_url.rstrip('/')}/object_info", timeout)
    missing = sorted(set(expected_nodes) - set(object_info))
    if missing:
        print(
            f"FAIL: /object_info missing expected example nodes: {', '.join(missing)}",
            file=sys.stderr,
        )
        return False
    print(f"OK: /object_info includes expected example nodes: {', '.join(expected_nodes)}")
    return True


def check_comfyui_root(comfyui_root: Path) -> bool:
    if not comfyui_root.exists():
        print(f"SKIP: ComfyUI runtime root not found: {comfyui_root}")
        return True
    custom_nodes = comfyui_root / "custom_nodes"
    if not custom_nodes.is_dir():
        print(f"FAIL: ComfyUI root lacks custom_nodes/: {comfyui_root}", file=sys.stderr)
        return False
    print(f"OK: ComfyUI root has custom_nodes/: {custom_nodes}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Opt-in examples-only smoke checks against live ComfyUI."
    )
    parser.add_argument("--url", required=True, help="Base URL of a running ComfyUI instance")
    parser.add_argument(
        "--timeout", type=int, default=30, help="Request/WebSocket timeout in seconds"
    )
    parser.add_argument(
        "--comfyui-root",
        default=str(DEFAULT_COMFYUI_ROOT),
        help="Optional local ComfyUI runtime root for custom_nodes sanity check",
    )
    parser.add_argument(
        "--model-name",
        default=None,
        help="Installed checkpoint filename for POST /prompt validation",
    )
    parser.add_argument(
        "--prompt-path", default=str(DEFAULT_PROMPT_PATH), help="Repo-local API prompt payload path"
    )
    parser.add_argument("--skip-prompt", action="store_true", help="Skip POST /prompt validation")
    parser.add_argument(
        "--skip-websocket", action="store_true", help="Skip WebSocket status validation"
    )
    parser.add_argument(
        "--expect-extension-route",
        action="store_true",
        help="Require minimal-route-registration example route to be installed and reachable",
    )
    parser.add_argument(
        "--expect-node",
        action="append",
        default=[],
        help="Require an installed example node ID in /object_info; may be repeated",
    )
    args = parser.parse_args()

    checks = [
        ("ComfyUI root", lambda: check_comfyui_root(Path(args.comfyui_root))),
        ("object_info prompt classes", lambda: check_object_info(args.url, args.timeout)),
    ]
    if not args.skip_websocket:
        checks.append(("WebSocket status", lambda: check_websocket_status(args.url, args.timeout)))
    if not args.skip_prompt:
        if not args.model_name:
            print("FAIL: --model-name is required unless --skip-prompt is set", file=sys.stderr)
            return 1
        checks.append(
            (
                "POST /prompt example",
                lambda: check_prompt_submission(
                    args.url, Path(args.prompt_path), args.model_name, args.timeout
                ),
            )
        )
    if args.expect_extension_route:
        checks.append(
            (
                "minimal route-registration route",
                lambda: check_extension_route(args.url, args.timeout),
            )
        )
    if args.expect_node:
        checks.append(
            (
                "expected example nodes",
                lambda: check_expected_object_info_nodes(args.url, args.expect_node, args.timeout),
            )
        )

    for name, check in checks:
        try:
            passed = check()
        except Exception as exc:
            print(f"FAIL: {name}: {exc}", file=sys.stderr)
            return 1
        if not passed:
            print(f"\nEXAMPLE RUNTIME SMOKE FAILED at {name}", file=sys.stderr)
            return 1

    print("\nAll requested example runtime smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
