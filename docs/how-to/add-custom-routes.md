# Add Custom Routes

**Last Updated:** 2026-04-19
**Primary Source:** https://docs.comfy.org/development/comfyui-server/comms_routes

## Primary Sources

- https://docs.comfy.org/development/comfyui-server/comms_routes
- `references/snapshots/2026-04-19/comfyui-core-v0.19.3/server.py` (v0.19.3, commit 308602640)

## Evidence Levels

This page primarily describes official behavior documented on docs.comfy.org.
Route patterns are verified against the pinned ComfyUI core snapshot.

## Overview

Add a custom route when your extension needs explicit client-to-server
communication that does not fit naturally into prompt submission,
WebSocket status, or existing built-in endpoints.

Good candidates include:

- fetching extension-specific server state
- sending a button click or widget action to Python
- exposing a small read/write API for a dashboard or panel

## Route Implementation

Use the official pattern:

```python
from server import PromptServer
from aiohttp import web

routes = PromptServer.instance.routes

@routes.post('/my_new_path')
async def my_function(request):
    the_data = await request.post()
    return web.json_response({})
```

Key decisions:

- choose `@routes.get` for read-only behavior
- choose `@routes.post` for mutation or commands
- use `await request.post()` for `FormData`
- use `await request.json()` for JSON payloads
- return `web.json_response(...)` unless a bare status response is enough

Client-side usage from the official docs:

```javascript
import { api } from "../../scripts/api.js"

function send_message(node_id, message) {
  const body = new FormData()
  body.append("message", message)
  body.append("node_id", node_id)
  api.fetchApi("/my_new_path", { method: "POST", body })
}
```

## Safety Checks

- validate all incoming fields before acting on them
- keep route names unique and extension-scoped where possible
- do not bury decorated handlers inside classes unless you understand the
  decorator implications
- prefer thin route functions that call separate helpers or classmethods
- return stable JSON shapes so frontend code can depend on them

## Compatibility Notes

- built-in routes are defined in `server.py`; search for `@routes` when
  checking naming conflicts or existing behavior
- your route becomes part of your extension's public contract once UI or
  external tools depend on it
- if the route exists only for execution-time feedback, consider whether
  a custom WebSocket message would be simpler than a new HTTP endpoint
