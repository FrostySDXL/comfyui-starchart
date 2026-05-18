---
title: "History and Queue"
---

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-05-18
**Primary Source:** ComfyUI core v0.20.1 `server.py` (pinned snapshot)

## Primary Sources

- `references/snapshots/2026-04-30/comfyui-core-v0.20.1/server.py` (v0.20.1, commit 64b8457)
- `references/snapshots/2026-04-30/comfyui-core-v0.20.1/execution.py` (v0.20.1, commit 64b8457)
- https://docs.comfy.org/development/comfyui-server/comms_routes

## Scope

ComfyUI splits live scheduling state from completed execution records:

- queue routes tell you what is running or waiting right now
- history routes tell you what finished and what outputs were recorded

In practice, clients often use both. The WebSocket is best for live
updates, while `/queue` and `/history` are the stable HTTP surfaces for
polling, reconnect, and post-run inspection.

Many community wrappers build their higher-level "wait for result" logic
on top of these same surfaces. That wrapper behavior can be useful to
study, but the native contract here is still the HTTP and WebSocket API
documented in ComfyUI's source.

This same area now also includes the `/api/jobs` routes. They combine
running queue state, pending queue state, and stored history into one
filtered lookup surface.

## Jobs API

### `GET /api/jobs`

This route is the server's unified job listing surface. It reads:

- running jobs from `self.prompt_queue.get_current_queue_volatile()`
- pending jobs from that same queue snapshot
- completed jobs from `self.prompt_queue.get_history()`

Before those queue-derived records are returned, the handler passes the
running and pending lists through `_remove_sensitive_from_queue()`.

Supported query parameters from the handler docstring and validation path:

- `status` — optional comma-separated status filter; accepted values are
  `pending`, `in_progress`, `completed`, and `failed`
- `workflow_id` — optional workflow filter
- `sort_by` — optional; must be `created_at` or `execution_duration`
- `sort_order` — optional; must be `asc` or `desc`
- `limit` — optional positive integer
- `offset` — optional integer; invalid integer values return HTTP 400,
  while negative values are clamped back to `0`

The response is a JSON object with:

- `jobs` — the filtered page of job records
- `pagination` — an object containing `offset`, `limit`, `total`, and
  `has_more`

The handler returns HTTP 400 when validation fails, including invalid
status names, unsupported sort fields, unsupported sort directions, or
non-integer pagination inputs.

### `GET /api/jobs/{job_id}`

This route returns one combined job record by ID.

The handler:

1. reads `job_id` from the route path
2. snapshots running and pending queue state
3. loads matching stored history with `get_history(prompt_id=job_id)`
4. sanitizes queue-derived records with `_remove_sensitive_from_queue()`
5. calls `get_job(job_id, running, queued, history)` to assemble the
   final response

The response behavior is:

- HTTP 200 with the matching job record when found
- HTTP 404 with `{"error": "Job not found"}` when no matching record exists
- HTTP 400 with `{"error": "job_id is required"}` if the path value is
  missing or empty

## Queue State

### `GET /queue`

The queue route returns two lists:

- `queue_running`
- `queue_pending`

These are derived from `self.prompt_queue.get_current_queue_volatile()`.
Before the response is sent, `_remove_sensitive_from_queue()` strips the
sensitive tuple field so secrets are not exposed through the API.

### `GET /prompt`

This related route returns the lighter `get_queue_info()` structure,
which currently exposes `exec_info.queue_remaining` rather than the full
running/pending lists.

### `POST /queue`

The mutating queue route supports:

- `{"clear": true}` to wipe pending queue items
- `{"delete": ["prompt-id-1", "prompt-id-2"]}` to remove specific jobs

It returns bare HTTP 200 on success.

## History Lookup

### `GET /history`

The aggregate history route supports optional query parameters:

- `max_items`
- `offset`

Those values are passed through to `self.prompt_queue.get_history()`.

### `GET /history/{prompt_id}`

This route returns the history entry for a single prompt ID.

### `POST /history`

The mutating history route supports:

- `{"clear": true}` to wipe all stored history
- `{"delete": ["prompt-id-1", "prompt-id-2"]}` to remove specific
  history items

It also returns bare HTTP 200 on success.

## What history stores

From the execution path in `execution.py`, completed runs build a
history result containing at least:

- `outputs` — UI-facing outputs keyed by node ID
- `meta` — node metadata associated with those outputs
- execution status information tracked alongside the prompt record

History is keyed by `prompt_id`, which makes it the natural lookup
surface after a client submits a prompt and later reconnects.

## Practical polling flow

Common client flow after `POST /prompt`:

1. record the returned `prompt_id`
2. use the WebSocket for live execution state when available
3. call `GET /queue` to detect whether the prompt is still running or
   pending
4. call `GET /history/{prompt_id}` once execution finishes

## Notes and caveats

- Queue state is intentionally sanitized before being returned.
- Queue order is influenced by the submission `number` and `front`
  fields from `POST /prompt`.
- History is persistent only within ComfyUI's prompt queue/history
  machinery, not a separate long-term database.

## Community polling patterns

Common wrapper behavior built on top of native routes:

- submit with `POST /prompt`
- capture `prompt_id`
- optionally correlate live events with `client_id`
- poll `GET /queue` until the prompt is no longer running or pending
- fetch `GET /history/{prompt_id}` to collect outputs

Pattern-study examples:

- `comfy-api-simplified` markets queue-and-wait automation over exported
  API workflows
- `sugarkwork/Comfyui_api_client` wraps prompt submission, output lookup,
  and workflow mutation in a Python client lifecycle

These are good examples of how people consume ComfyUI programmatically in
practice. They do not add new native queue or history semantics.

## Read Next

- [Client ID](client-id.md)
- [Prompt Submission](prompt-submission.md)
- [WebSocket](websocket.md)
