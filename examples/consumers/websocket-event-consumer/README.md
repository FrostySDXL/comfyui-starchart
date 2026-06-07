# WebSocket Event Consumer Example

**Status:** Runtime-dependent starter pattern
**Validation tiers:** static, offline unit-tested, pinned-source, opt-in runtime smoke

## What This Example Shows

This example connects to a live ComfyUI WebSocket endpoint, watches a bounded set
of known JSON event types, and ignores binary preview frames. It is designed to
pair with `examples/api-calls/post-prompt.sh`: use the same `client_id` value in
`COMFYUI_CLIENT_ID` and in this watcher so prompt submission and event tracking
refer to the same live client session.

## Boundaries

- This is not a supported SDK or reusable client library.
- It depends on a live ComfyUI runtime and `websocket-client` from
  `requirements.lock`.
- Event behavior must match the running instance; pinned docs and artifacts are
  guidance, not a substitute for runtime validation.
- Binary preview frames are intentionally skipped rather than decoded.

## Usage

Terminal 1:

```bash
py -3.11 examples/consumers/websocket-event-consumer/watch_events.py --url http://127.0.0.1:8188 --client-id 00000000-0000-4000-8000-000000000000
```

Terminal 2:

```bash
COMFYUI_CLIENT_ID=00000000-0000-4000-8000-000000000000 bash examples/api-calls/post-prompt.sh
```

Use a unique client ID for your own run. Simultaneous submissions that share a
`client_id` can make event correlation ambiguous.

Runtime-smoke validation for the WebSocket status path:

```bash
python scripts/verify/example_runtime_smoke.py --url http://127.0.0.1:8188 --comfyui-root D:/projects/comfyui-test-runtime --skip-prompt
```

## Read Next

- [`src/content/docs/api/websocket.md`](../../../src/content/docs/api/websocket.md)
- [`src/content/docs/api/prompt-submission.md`](../../../src/content/docs/api/prompt-submission.md)
- [`examples/consumers/prompt-submit-monitor-history/`](../prompt-submit-monitor-history/)
