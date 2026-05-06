# Prompt Submission

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-05-05
**Primary Source:** ComfyUI core v0.20.1 `server.py` (pinned snapshot)

## Primary Sources

- `references/snapshots/2026-04-30/comfyui-core-v0.20.1/server.py` (v0.20.1, commit 64b8457)
- `references/snapshots/2026-04-30/comfyui-core-v0.20.1/execution.py` (v0.20.1, commit 64b8457)
- https://docs.comfy.org/development/comfyui-server/comms_routes

## Scope

`POST /prompt` is the main execution entrypoint. The handler accepts a
workflow payload, validates it, assigns queue priority, extracts
sensitive metadata, and enqueues the prompt for asynchronous execution.

Successful submission does not mean the workflow already ran; it means
the prompt passed validation and was placed on the execution queue.

This page describes native ComfyUI behavior first. Community client
libraries often wrap this endpoint with higher-level conveniences, but
those wrapper APIs are not the same thing as ComfyUI's public contract.

For direct local HTTP calls, the practical default base URL is
`http://127.0.0.1:8188`. Send the request body as JSON with
`Content-Type: application/json`.

## Request Structure

The handler recognizes these request fields directly:

- `prompt` — required workflow graph payload
- `prompt_id` — optional caller-supplied identifier; otherwise a UUID is
  generated
- `client_id` — optional target client for execution events
- `extra_data` — optional execution metadata
- `partial_execution_targets` — optional output-node subset for partial
  execution
- `number` — optional explicit queue ordering value
- `front` — optional flag that pushes queue priority forward by negating
  the generated number

Only `prompt` has API-level requiredness in the pinned handler. The other fields
are optional or conditional. This matters if you inspect
`server_endpoints.json`: that artifact can expose parameter-level
source-access requiredness as a bounded static hint, but the prose page is the
authority for the branch-conditioned `/prompt` request contract in this
baseline.

Minimal request shape:

```json
{
  "prompt": {},
  "client_id": "frontend-session-id",
  "extra_data": {}
}
```

## Validation Behavior

Before anything is queued, `server.py` calls `execution.validate_prompt`.
The validation logic in `execution.py` checks that:

- every node has a `class_type`
- each referenced node type exists
- the workflow has at least one eligible output node
- required inputs exist
- linked inputs are valid `[node_id, slot_index]` pairs
- linked output types match expected input types
- literal values can be coerced to supported primitive types
- `min` and `max` bounds are respected
- combo/list values are part of the allowed options
- node-specific validation hooks succeed when present

Validation returns both a success flag and a `node_errors` structure.
The prompt is only queued if at least one requested output validates
successfully.

## Queueing Behavior

After validation succeeds, the handler:

- applies node replacements via `node_replace_manager`
- copies `client_id` into `extra_data`
- removes keys listed in `execution.SENSITIVE_EXTRA_DATA_KEYS` from the
  public `extra_data` bundle before queue insertion
- stamps `extra_data["create_time"]` in milliseconds
- enqueues a tuple containing queue number, prompt ID, prompt payload,
  filtered `extra_data`, outputs to execute, and a separate sensitive
  field bundle

Queue order is based on `number`. If `front: true` is supplied and no
explicit number is provided, the generated queue number is negated so
that the job runs earlier.

If neither `number` nor `front` is provided, the server uses its internal queue
counter. If `client_id`, `extra_data`, or `partial_execution_targets` are
omitted, the handler continues without them.

## Response and Execution Flow

Successful submission returns:

```json
{
  "prompt_id": "...",
  "number": 12,
  "node_errors": {}
}
```

Invalid prompts return HTTP 400 with an `error` object plus
`node_errors`.

Once queued, the usual follow-on flow is:

1. watch `GET /queue` or the WebSocket `status` event for queue state
2. receive `execution_start`, `executing`, `executed`, and related
   lifecycle events on the WebSocket for the matching `client_id`
3. inspect `GET /history/{prompt_id}` after completion for stored output
   and metadata

## Client targeting

`client_id` is the bridge between HTTP submission and the WebSocket.
When `execute_async` begins, it copies the submitted `client_id` into
`server.client_id`, and most execution lifecycle events are then sent to
that specific client rather than broadcast globally.

## Community client patterns

The following patterns show up in community libraries and are useful to
document as client conventions, not as native `/prompt` semantics.

### Workflow export conversion

Some clients accept editor-exported `workflow.json` and convert it to the
API graph shape before submission.

Pattern-study example:

- `sugarkwork/Comfyui_api_client` advertises automatic conversion from
  editor workflow format to API format

That conversion is a client convenience layer. `/prompt` itself expects an
API-valid prompt graph.

### Title-based parameter editing

Some wrappers let callers mutate workflows by node title or class name,
instead of editing node IDs directly.

Pattern-study examples:

- `sugarkwork/Comfyui_api_client`
- `comfy-api-simplified`

This is ergonomic for scripting, but it depends on client-side workflow
inspection and often assumes titles are unique. ComfyUI's `/prompt` route
does not provide title-based mutation on its own.

### Queue-and-wait helpers

Many clients wrap a larger flow around `POST /prompt`:

1. submit prompt
2. correlate by `prompt_id` and optional `client_id`
3. watch the WebSocket and/or poll queue state
4. read `/history/{prompt_id}` for final outputs

Pattern-study examples:

- `comfy-api-simplified` exposes queue-and-wait helpers
- `sugarkwork/Comfyui_api_client` exposes generate-style client methods

That orchestration is the common way people consume ComfyUI in practice,
but it is built on top of `/prompt`, WebSocket events, and history lookup
rather than replacing them.

## Read Next

- [API Endpoints](endpoints.md)
- [WebSocket](websocket.md)
