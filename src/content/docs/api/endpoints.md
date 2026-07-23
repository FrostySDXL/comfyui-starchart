---
title: "API Endpoints"
---

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-07-23
**Primary Source:** ComfyUI core v0.28.0 `server.py` (pinned snapshot)
**Baseline verification status:** Verified against the current pinned baseline: core v0.28.0, frontend v1.48.4, snapshots 2026-07-23.

## Primary Sources

- `references/snapshots/2026-07-23/comfyui-core-v0.28.0/server.py` (v0.28.0, commit 700821e1364eaab0e8f21c538a2131719fec57bf)
- https://docs.comfy.org/development/comfyui-server/comms_routes
- https://docs.comfy.org/development/comfyui-server/comms_messages

## Scope

ComfyUI declares its HTTP and WebSocket surface directly in `server.py`
using `aiohttp` route decorators. The current file defines 27 primary
routes on `self.routes`, covering queue control, prompt submission,
file upload and viewing, node metadata, system inspection, and job
tracking.

One important implementation detail is easy to miss: after the base
routes are registered, ComfyUI also creates `/api`-prefixed copies of
every non-static route. That means most routes are reachable at both
their original path and an `/api` mirror, such as `/prompt` and
`/api/prompt`.

This repo does not promote those aliases into the canonical
machine-readable endpoint surface for this pinned baseline. The aliasing is
added generically in `add_routes()` as a delegation convenience, and routes
already declared under `/api` in the base list also receive a second alias pass.
For example, `GET /api/jobs`, `GET /api/jobs/{job_id}`,
`POST /api/jobs/cancel`, and `POST /api/jobs/{job_id}/cancel` also gain
`/api/api/jobs...` variants from the same loop. Use the undecorated route path
in the artifact and treat `/api/...` mirrors as snapshot-backed compatibility
behavior documented in prose.

## Endpoint Inventory

### Execution and queue control

- `GET /prompt` — returns queue summary info from `get_queue_info()`
- `POST /prompt` — validates and enqueues a workflow
- `GET /queue` — returns `queue_running` and `queue_pending`
- `POST /queue` — clears queued items or deletes specific prompt IDs
- `POST /interrupt` — interrupts processing; accepts optional JSON body
  `{"prompt_id": "..."}` for targeted interruption, otherwise does a
  global interrupt
- `POST /free` — sets unload/free-memory flags
- `GET /history` — returns prompt history with optional paging
- `GET /history/{prompt_id}` — returns history for one prompt
- `POST /history` — clears history or deletes specific items
- `GET /ws` — opens the status/execution WebSocket stream

### Node and capability discovery

- `GET /object_info` — returns metadata for all registered nodes
- `GET /object_info/{node_class}` — returns metadata for one node
- `GET /features` — returns negotiated server feature flags

### Files, models, and frontend assets

- `GET /` — serves the main frontend page
- `GET /embeddings` — lists embedding names
- `GET /models` — lists model folder categories
- `GET /models/{folder}` — lists model files for one folder
- `GET /extensions` — lists extension JavaScript paths
- `POST /upload/image` — uploads an image into ComfyUI storage
- `POST /upload/mask` — uploads a mask against an existing image
- `GET /view` — serves stored images, previews, or channel variants
- `GET /view_metadata/{folder_name}` — reads safetensors metadata

### System and job inspection

- `GET /system_stats` — returns nested `{system: {os, ram_total, ram_free, comfyui_version, deploy_environment, ...}, devices: [{name, type, index, vram_total, vram_free, ...}]}` with per-device VRAM breakdown, deployment-environment metadata, plus Python and package-version info. **Privacy note:** The `argv` field in this response exposes the full server command-line arguments, which may include local filesystem paths and configuration values.
- `GET /api/jobs` — returns filtered and paginated job listings
- `GET /api/jobs/{job_id}` — returns one job record
- `POST /api/jobs/{job_id}/cancel` — cancels one running or pending job by ID and returns `{"cancelled": true}` or `{"cancelled": false}`
- `POST /api/jobs/cancel` — accepts `{"job_ids": ["..."]}` and cancels each running or pending job in the batch; finished or unknown IDs are no-ops

## High-value route details

### `POST /prompt`

This is the core workflow submission route. The handler reads JSON,
passes it through `trigger_on_prompt`, validates the workflow with
`execution.validate_prompt`, copies `client_id` into `extra_data`, and
enqueues the request when validation succeeds.

For direct local HTTP calls, the practical default base URL is
`http://127.0.0.1:8188`. Send JSON with `Content-Type: application/json`.

Common request fields seen in the handler:

- `prompt` — required; the handler returns HTTP 400 when it is missing
- `prompt_id` — optional caller-supplied identifier
- `client_id` — optional client-targeting value copied into `extra_data`
- `extra_data` — optional execution metadata
- `partial_execution_targets` — optional partial-execution subset
- `number` — optional explicit queue ordering value
- `front` — optional queue-priority flag used only when `number` is not supplied

Success response shape:

```json
{
  "prompt_id": "...",
  "number": 12,
  "node_errors": {}
}
```

Failure path returns HTTP 400 with an `error` object and `node_errors`.

The current delta summary also marks `POST /prompt` as changed at the extracted
artifact level. The prose contract above covers the current pinned handler:
`prompt` is the only API-level required request field, while `number`, `front`,
`prompt_id`, `client_id`, `extra_data`, and `partial_execution_targets` are
optional or branch-conditioned request fields.

### `GET /ws`

The WebSocket route accepts an optional `clientId` query parameter.
When the socket opens, the server immediately sends a `status` message
containing queue state and the resolved session ID. If the reconnecting
client is also the currently executing client, the server also sends an
`executing` message for the current node.

The handler also supports feature-flag negotiation. If the first client
message is a JSON object with `type: "feature_flags"`, the server stores
the client flags and responds with its own feature flag payload.

### `GET /object_info`

This route builds node metadata by iterating `nodes.NODE_CLASS_MAPPINGS`
and returning per-node input, output, display, category, tooltip, and
capability metadata. It is the key discovery endpoint for dynamic UIs
and tooling that need to inspect available nodes programmatically.

## Notes and Caveats

- Base routes are duplicated under `/api` in `add_routes()`. Treat the
  `/api` prefix as a compatibility alias for non-static routes, not as the
  canonical machine-readable route surface for this repo.
- The native jobs routes are already declared with `/api` in the base route
  list, so the aliasing logic also creates `/api/api/jobs...` variants.
- Several routes deliberately return bare `HTTP 200` responses instead of
  JSON payloads for mutating operations like `/queue`, `/interrupt`,
  `/free`, and `/history` POSTs.
- Upload and view endpoints perform path and traversal validation in the
  handler before touching files.

## Read Next

- [Start Here: Local API Integration](../start-here/service-integration.md)
- [WebSocket](websocket.md)
- [Prompt Submission](prompt-submission.md)
- [History and Queue](history-queue.md)
- [Object Info](../reference/object-info.md)
- [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md)
