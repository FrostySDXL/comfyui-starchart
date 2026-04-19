# WebSocket

**Last Updated:** 2026-04-19
**Primary Source:** https://github.com/Comfy-Org/ComfyUI/blob/master/server.py

## Primary Sources

- https://github.com/Comfy-Org/ComfyUI/blob/master/server.py
- https://github.com/Comfy-Org/ComfyUI/blob/master/execution.py

## Overview

ComfyUI uses `GET /ws` as the real-time channel for queue state,
execution lifecycle messages, UI output updates, and preview images.
The route is implemented with `aiohttp.WebSocketResponse` and is the
main mechanism that keeps the frontend in sync while a prompt runs.

Unlike the HTTP endpoints, the WebSocket also carries connection-scoped
identity. The server assigns or reuses a session ID (`sid`) and uses it
to target execution messages to the correct frontend client.

## Connection Flow

The handler accepts an optional `clientId` query parameter:

- if `clientId` is present, the server treats the connection as a
  reconnect and replaces the old socket for that session
- if it is absent, the server generates a new random session ID

Immediately after connection, the server sends a `status` message with:

- current queue summary from `get_queue_info()`
- the resolved `sid`

If the reconnecting client is also the currently executing client and a
node is already in progress, the server sends an `executing` message for
that node right away.

The first text message from the client may also be a feature negotiation
payload:

```json
{
  "type": "feature_flags",
  "data": {
    "some_client_feature": true
  }
}
```

When that happens, the server stores the client flags and responds with
its own `feature_flags` payload.

## Event Types

### JSON lifecycle events

The following events are visible in `server.py` and `execution.py`:

- `status` — queue status snapshot, including session ID on connect
- `feature_flags` — server feature capability response
- `executing` — emitted before a node executes; includes `node`,
  `display_node`, and `prompt_id`
- `executed` — emitted after a node produces UI output; includes node
  identifiers, UI output, and `prompt_id`
- `execution_start` — emitted when a prompt begins executing
- `execution_cached` — emitted with cached node IDs reused for a prompt
- `execution_success` — emitted when a prompt completes successfully
- `execution_error` — emitted when execution fails
- `execution_interrupted` — emitted when execution is interrupted

`add_message()` in `PromptExecutor` also adds a millisecond `timestamp`
to lifecycle messages before they are sent.

### Binary preview events

The server also sends binary image previews:

- `PREVIEW_IMAGE`
- `PREVIEW_IMAGE_WITH_METADATA`

These are dispatched through `send_bytes()` rather than `send_json()`.
`PREVIEW_IMAGE_WITH_METADATA` prefixes the image bytes with a JSON
metadata blob length and payload before the image content.

## Client targeting and broadcast behavior

Execution events are usually sent to the specific `client_id` attached
to the prompt. In `execute_async`, `server.client_id` is set from
`extra_data["client_id"]` when present, and node-level execution events
use that client as their target.

Queue `status` updates are broader: `queue_updated()` calls
`send_sync("status", ...)` without a specific `sid`, which broadcasts to
all connected sockets.

## Practical notes

- Use the WebSocket when you need live progress, node execution state, or
  preview frames.
- Use HTTP routes like `/history` and `/queue` when polling is simpler or
  when reconnecting after a disconnected session.
- Treat the WebSocket `sid` and the prompt `client_id` as related but not
  identical concepts: the socket assigns a session ID, while prompt
  submission chooses which client should receive execution events.
