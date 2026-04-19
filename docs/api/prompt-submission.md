# Prompt Submission

**Last Updated:** 2026-04-19
**Primary Source:** https://github.com/Comfy-Org/ComfyUI/blob/master/server.py

## Primary Sources

- https://github.com/Comfy-Org/ComfyUI/blob/master/server.py
- https://github.com/Comfy-Org/ComfyUI/blob/master/execution.py

## Overview

`POST /prompt` is the main execution entrypoint. The handler accepts a
workflow payload, validates it, assigns queue priority, extracts
sensitive metadata, and enqueues the prompt for asynchronous execution.

Successful submission does not mean the workflow already ran; it means
the prompt passed validation and was placed on the execution queue.

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
