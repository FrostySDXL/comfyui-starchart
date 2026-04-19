# History and Queue

**Last Updated:** 2026-04-19
**Primary Source:** https://github.com/Comfy-Org/ComfyUI/blob/master/server.py

## Primary Sources

- https://github.com/Comfy-Org/ComfyUI/blob/master/server.py
- https://github.com/Comfy-Org/ComfyUI/blob/master/execution.py

## Overview

ComfyUI splits live scheduling state from completed execution records:

- queue routes tell you what is running or waiting right now
- history routes tell you what finished and what outputs were recorded

In practice, clients often use both. The WebSocket is best for live
updates, while `/queue` and `/history` are the stable HTTP surfaces for
polling, reconnect, and post-run inspection.

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
