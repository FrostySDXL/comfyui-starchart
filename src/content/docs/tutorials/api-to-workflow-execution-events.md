---
title: "API to Workflow: Execution Events"
---

# API to Workflow: Execution Events

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-04-30
**Primary Sources:**
- https://docs.comfy.org/development/comfyui-server/comms_messages
- `references/snapshots/2026-04-30/comfyui-core-v0.20.1/server.py` (v0.20.1, commit 64b8457)
- `references/snapshots/2026-04-30/comfyui-core-v0.20.1/execution.py` (v0.20.1, commit 64b8457)

## Who This Page Is For

You are integrating ComfyUI into an external service and need to
understand how execution lifecycle events flow from the server to a
connected client via WebSocket.

## Scope

This tutorial describes the sequence of WebSocket events emitted during
a prompt execution, what each event means, and how clients can use them
to track live progress.

## WebSocket Connection

Connect to `GET /ws` with an optional `clientId` query parameter:

```
ws://localhost:8188/ws?clientId=my-session-id
```

If `clientId` is provided, the server treats the connection as a
reconnect for that session. If absent, a new random session ID is
assigned.

Immediately after connection, the server sends a `status` message:

```json
{
  "type": "status",
  "data": {
    "status": {
      "exec_info": {
        "queue_remaining": 0
      }
    },
    "sid": "session-id"
  }
}
```

This initial WebSocket snapshot comes from `get_queue_info()`. It exposes the
lighter `exec_info.queue_remaining` count, not the full `queue_running` and
`queue_pending` lists from `GET /queue`.

## Event Sequence

A prompt execution produces this event sequence:

### 1. `execution_start`

Emitted when a prompt begins executing on the executor.

```json
{
  "type": "execution_start",
  "data": {
    "prompt_id": "<prompt_id>"
  }
}
```

This is the signal that the execution engine has picked up the prompt
from the queue and started processing.

### 2. `executing`

Emitted before a non-cached node executes. Fires in execution order for nodes
that actually enter `execute()`.

```json
{
  "type": "executing",
  "data": {
    "node": "3",
    "display_node": "3",
    "prompt_id": "<prompt_id>"
  }
}
```

The `node` value is the node ID string from the prompt graph. Cached nodes are
reported separately in `execution_cached`; they do not emit the normal per-node
`executing` event. One exception exists on reconnect: `server.py` can send a
minimal `executing` payload with only `node` for the node that is already in
progress.

### 3. `execution_cached`

Emitted when a node's outputs are already cached from a previous run
and no new computation is needed. Source: `execution.py` lines 745-753.

```json
{
  "type": "execution_cached",
  "data": {
    "nodes": ["1", "2"],
    "prompt_id": "<prompt_id>"
  }
}
```

The `nodes` array lists all node IDs whose results were reused from
cache. When cached results are used, the server emits an `executed`
event carrying the cached UI output so clients receive complete
information about what was produced.

### 4. `progress`

Emitted during execution of a node that implements ComfyUI's progress hook.

```json
{
  "type": "progress",
  "data": {
    "node": "3",
    "prompt_id": "<prompt_id>",
    "value": 6,
    "max": 10
  }
}
```

The official docs define `value` and `max` as the built-in progress counters.
Only nodes that implement the required hook emit this event.

### 5. `executed`

Emitted after a node produces UI output. The payload contains the UI-facing
`output` object that ComfyUI sends to the frontend, not the raw node return
tuple.

```json
{
  "type": "executed",
  "data": {
    "node": "3",
    "display_node": "3",
    "prompt_id": "<prompt_id>",
    "output": {
      "images": [
        {
          "filename": "ComfyUI_00001_.png",
          "subfolder": "",
          "type": "output"
        }
      ]
    }
  }
}
```

The `output` structure varies by node type. The source sends `output_ui` for
fresh results and `cached_ui.get("output", None)` when replaying cached UI, so
the field may be `null` if the cached node had no stored UI payload.

### 6. `execution_success`

Emitted when a prompt completes without errors.

```json
{
  "type": "execution_success",
  "data": {
    "prompt_id": "<prompt_id>"
  }
}
```

At this point the prompt is no longer in the queue. Clients should
switch to `GET /history/{prompt_id}` for the complete output record.

### 7. `execution_error`

Emitted when execution fails. Source: `execution.py` `handle_execution_error()`.

```json
{
  "type": "execution_error",
  "data": {
    "prompt_id": "<prompt_id>",
    "node_id": "4",
    "node_type": "ImageScale",
    "executed": ["1", "2", "3"],
    "exception_message": "RuntimeError: dimension mismatch",
    "exception_type": "RuntimeError",
    "traceback": ["File ...", "  ..."],
    "current_inputs": [],
    "current_outputs": []
  }
}
```

`exception_message` and `exception_type` carry the error details. `traceback`
is the Python traceback as a list of string lines. `current_inputs` and
`current_outputs` describe the node state at the point of failure. `executed`
lists node IDs that finished before the error occurred.

### 8. `execution_interrupted`

Emitted when execution is stopped by a `POST /interrupt` call. Source:
`execution.py` `handle_execution_error()`.

```json
{
  "type": "execution_interrupted",
  "data": {
    "prompt_id": "<prompt_id>",
    "node_id": "4",
    "node_type": "ImageScale",
    "executed": ["1", "2", "3"]
  }
}
```

`node_type` identifies the node that was in progress. `executed` lists node IDs
that completed before the interrupt took effect.

## Complete Event Sequence

```
Server                                    Client
  |                                          |
  |--- status (queue state, sid) ----------->|
  |                                          |
  |--- execution_start --------------------->|
  |     {prompt_id: ...}                     |
  |                                          |
  |--- execution_cached (cached nodes) ----->|
  |     {nodes: ["2"], prompt_id: ...}      |
  |                                          |
  |--- executing (per non-cached node) ----->|
  |     {node: "1", prompt_id: ...}         |
  |                                          |
  |--- progress (hook-enabled nodes) ------->|
  |     {node: "1", value: 6, max: 10}      |
  |                                          |
  |--- executed (per node with output) ----->|
  |     {node: "3", output: {...}}           |
  |                                          |
  |--- execution_success -------------------->|
  |     {prompt_id: ...}                     |
  |                                          |
  |<-- GET /history/{prompt_id} ------------>|
  |     (retrieve full output record)         |
```

## Using Events in Practice

### Track overall progress

Use the official `progress` event when the executing node emits it. The
built-in counters are `value` out of `max`.

For nodes that do not emit `progress`, count `executing` events against the
non-cached portion of the graph. Do not expect one `executed` event per node:
`executed` is only sent when a node has UI output to forward to the client.

### Detect completion

Listen for `execution_success` or `execution_error`. After either event,
the prompt is no longer in the queue and history lookup will return
final results.

### Handle reconnection

If the WebSocket disconnects mid-execution:

1. Reconnect with the same `clientId` used during prompt submission
2. The server will immediately send `executing` for any node currently
   in progress
3. Continue listening from that point rather than replaying all events

### Get final outputs

After `execution_success`, call `GET /history/{prompt_id}` for the
complete output record. The history contains all node outputs and metadata
in a structured format that is more complete than the `executed` event
payloads alone.

## Limitations

- Events are scoped to the `client_id` attached to the prompt. If you
  submit without a `client_id`, you will not receive targeted execution
  events even if you connect with a WebSocket.
- Built-in progress counters are only available for nodes that emit the
  official `progress` event. Other nodes expose lifecycle events such as
  `executing`, `executed`, and the terminal execution messages instead.
- The `executed` event output structure varies by node type and is not
  normalized across node classes.

## Read Next

- [API to Workflow: Prompt Lifecycle](api-to-workflow-prompt-lifecycle.md)
- [WebSocket](../api/websocket.md)
- [History and Queue](../api/history-queue.md)
