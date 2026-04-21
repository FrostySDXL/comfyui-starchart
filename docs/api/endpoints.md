# API Endpoints

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-04-21
**Primary Source:** ComfyUI core v0.19.3 `server.py` (pinned snapshot)

## Primary Sources

- `references/snapshots/2026-04-19/comfyui-core-v0.19.3/server.py` (v0.19.3, commit 308602640)
- https://docs.comfy.org/development/comfyui-server/comms_routes
- https://docs.comfy.org/development/comfyui-server/comms_messages

## Scope

ComfyUI declares its HTTP and WebSocket surface directly in `server.py`
using `aiohttp` route decorators. The current file defines 25 primary
routes on `self.routes`, covering queue control, prompt submission,
file upload and viewing, node metadata, system inspection, and job
tracking.

One important implementation detail is easy to miss: after the base
routes are registered, ComfyUI also creates `/api`-prefixed copies of
every non-static route. That means most routes are reachable at both
their original path and an `/api` mirror, such as `/prompt` and
`/api/prompt`.

## Endpoint Inventory

### Execution and queue control

- `GET /prompt` — returns queue summary info from `get_queue_info()`
- `POST /prompt` — validates and enqueues a workflow
- `GET /queue` — returns `queue_running` and `queue_pending`
- `POST /queue` — clears queued items or deletes specific prompt IDs
- `POST /interrupt` — interrupts all processing or one running prompt
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

- `GET /system_stats` — returns host, RAM, VRAM, Python, and version info
- `GET /api/jobs` — returns filtered and paginated job listings
- `GET /api/jobs/{job_id}` — returns one job record

## High-value route details

### `POST /prompt`

This is the core workflow submission route. The handler reads JSON,
passes it through `trigger_on_prompt`, validates the workflow with
`execution.validate_prompt`, copies `client_id` into `extra_data`, and
enqueues the request when validation succeeds.

Common request fields seen in the handler:

- `prompt`
- `prompt_id`
- `client_id`
- `extra_data`
- `partial_execution_targets`
- `number`
- `front`

Success response shape:

```json
{
  "prompt_id": "...",
  "number": 12,
  "node_errors": {}
}
```

Failure path returns HTTP 400 with an `error` object and `node_errors`.

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
  `/api` prefix as a compatibility alias for non-static routes.
- `GET /api/jobs` and `GET /api/jobs/{job_id}` are already declared with
  `/api` in the base route list, so the aliasing logic also creates
  `/api/api/jobs` variants unless upstream filters them elsewhere.
- Several routes deliberately return bare `HTTP 200` responses instead of
  JSON payloads for mutating operations like `/queue`, `/interrupt`,
  `/free`, and `/history` POSTs.
- Upload and view endpoints perform path and traversal validation in the
  handler before touching files.

## Read Next

- [WebSocket](websocket.md)
- [Prompt Submission](prompt-submission.md)
