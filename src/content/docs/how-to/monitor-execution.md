---
title: "Monitor Execution"
---

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-04-30
**Primary Source:** https://docs.comfy.org/development/comfyui-server/comms_messages

## Primary Sources

- https://docs.comfy.org/development/comfyui-server/comms_messages
- https://docs.comfy.org/development/comfyui-server/comms_routes
- `references/snapshots/2026-04-30/comfyui-core-v0.20.1/server.py` (v0.20.1, commit 64b8457)
- `references/snapshots/2026-04-30/comfyui-core-v0.20.1/execution.py` (v0.20.1, commit 64b8457)

## Scope

ComfyUI exposes execution state through two complementary channels:

- WebSocket/message events for live updates
- HTTP routes for queue snapshots and history lookup

Use the WebSocket for interactive monitoring and `/queue` plus
`/history` for polling or reconnect-safe state recovery.

## API Calls

### Live event stream

The `/ws` connection is the main real-time monitoring channel. Relevant
built-in message types include:

- `status` — queue state updates
- `execution_start` — a prompt begins
- `execution_cached` — cached nodes are reused
- `executing` — a node is about to run
- `executed` — a node emitted UI output
- `progress` — incremental progress for supported operations
- `execution_success` — prompt completed
- `execution_error` — prompt failed
- `execution_interrupted` — prompt was stopped

### Polling routes

For HTTP-side monitoring, the most useful routes are:

- `GET /prompt` — queue summary via `queue_remaining`
- `GET /queue` — running and pending queue entries
- `GET /history` — aggregate execution history
- `GET /history/{prompt_id}` — result and metadata for one run
- `GET /system_stats` — host, device, RAM, VRAM, and version info

## Operational Tips

- record `prompt_id` at submission time so you can correlate queue,
  history, and message events
- provide a stable `client_id` if you want execution events targeted to a
  specific frontend session
- use WebSocket listeners for dashboards and node-level progress views
- use `/history/{prompt_id}` as the reliable post-run lookup after
  reconnect or browser refresh
- use `/system_stats` for lightweight health panels, not just workflow
  tracking

## Caveats

- `executed` is not emitted for every completed node; it is only sent
  when a node returns UI output
- `status` is queue-oriented, not a full per-node execution log
- queue data is sanitized before API return to avoid exposing sensitive
  fields

## Read Next

- [WebSocket](../api/websocket.md)
- [API Endpoints](../api/endpoints.md)
