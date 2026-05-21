---
title: "Client ID"
---

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-05-21
**Primary Source:** ComfyUI core v0.22.0 `server.py` (pinned snapshot)
**Baseline verification status:** Verified against the current pinned baseline: core `v0.22.0`, frontend `v1.45.12`, snapshots `2026-05-21`.

## Primary Sources

- `references/snapshots/2026-05-21/comfyui-core-v0.22.0/server.py` (v0.22.0, commit a8d2519058ea766ca3b14916bcc01ecef5efd235)
- `references/snapshots/2026-05-21/comfyui-core-v0.22.0/execution.py` (v0.22.0, commit a8d2519058ea766ca3b14916bcc01ecef5efd235)

## Scope

`client_id` is the identifier that ties HTTP prompt submission to the
WebSocket client that should receive execution updates. It is not the
same thing as a prompt ID. A prompt ID identifies one queued workflow,
while `client_id` identifies the frontend session that should receive
targeted lifecycle events for that run.

This is why ComfyUI exposes both concepts:

- `prompt_id` tracks work units and history entries
- `client_id` targets real-time execution messages

## Request Usage

`client_id` appears explicitly in `POST /prompt`. When the handler sees
it in the request JSON, it copies the value into `extra_data`:

```json
{
  "prompt": {},
  "client_id": "frontend-session-id",
  "extra_data": {}
}
```

If the caller omits `client_id`, the prompt can still run, but execution
events are not tied to a specific client session in the same way.

## WebSocket Relationship

The WebSocket route uses a related but separate identifier:

- `GET /ws?clientId=...` accepts an optional query parameter named
  `clientId`
- if present, the socket reconnects under that session ID and replaces
  any old socket for the same ID
- if absent, the server generates a new random `sid`

On connect, the server sends a `status` message that includes the
resolved `sid`.

## WebSocket Targeting

When a prompt begins execution, `PromptExecutor.execute_async` checks for
`extra_data["client_id"]` and assigns it to `server.client_id`. From
that point onward, most execution lifecycle messages are sent only to
that client:

- `executing`
- `executed`
- `execution_start`
- `execution_cached`
- `execution_success`
- `execution_error`
- `execution_interrupted`

Queue `status` updates are different: they are broadcast rather than
targeted.

## Practical guidance

- submit a stable `client_id` with `POST /prompt` if your frontend needs
  per-client execution updates
- reconnect to the WebSocket using the same session ID when resuming a
  disconnected client
- do not confuse `client_id` with `prompt_id`; use the first for live
  message routing and the second for history lookup

## Read Next

- [History and Queue](history-queue.md)
- [Prompt Submission](prompt-submission.md)
- [WebSocket](websocket.md)
