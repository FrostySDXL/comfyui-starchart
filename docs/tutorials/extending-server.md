# Extending the Server

**Last Updated:** 2026-04-19
**Primary Source:** https://docs.comfy.org/development/comfyui-server/comms_routes

## Primary Sources

- https://docs.comfy.org/development/comfyui-server/comms_routes
- https://docs.comfy.org/development/comfyui-server/comms_messages
- https://docs.comfy.org/custom-nodes/backend/lifecycle
- ComfyUI `server.py`

## Overview

Extending the ComfyUI server usually means one of two things:

- adding a custom HTTP route for client-to-server communication
- sending custom execution messages back to the client over the existing
  WebSocket/message system

The built-in server already exposes a large route surface, but custom
routes are the normal answer when an extension needs its own request
path, structured mutation, or lightweight API.

## Adding Routes

The official route docs show the standard pattern:

```python
from server import PromptServer
from aiohttp import web

routes = PromptServer.instance.routes

@routes.post('/my_new_path')
async def my_function(request):
    the_data = await request.post()
    return web.json_response({})
```

Important points:

- use `PromptServer.instance.routes` so your route is added to the live
  route table ComfyUI serves
- use `@routes.post` for mutations and `@routes.get` for reads
- parse the request according to payload style, for example `await
  request.post()` for form-style data or `await request.json()` for JSON
- return `web.json_response(...)` when the client expects structured data

The docs explicitly warn against defining the decorated route function as
an instance method unless you know exactly what you are doing. The safer
pattern is a module-level function that delegates to a classmethod or
helper.

## Serving Custom Data

ComfyUI's built-in route model and message model work well together:

- use routes when the client needs to request or update something on
  demand
- use server messages when the server should push execution-time events
  back to the client

The built-in message path uses `PromptServer.send_sync(...)`, and custom
extensions can do the same with a unique message type.

Typical server-side message send:

```python
PromptServer.instance.send_sync("my.custom.message", {"node": node_id})
```

Typical client-side listener:

```javascript
api.addEventListener("my.custom.message", messageHandler)
```

## Lifecycle considerations

The lifecycle docs still describe the legacy loading path clearly:

- custom node modules are discovered under `custom_nodes`
- `__init__.py` is executed when Comfy imports the module
- exported values such as `NODE_CLASS_MAPPINGS` and `WEB_DIRECTORY`
  control how the package is recognized and served

That means route registration code is usually executed during package
import time, not lazily on first use. If import-time code fails, ComfyUI
continues startup but reports the module as failed to load.

## Practical guidance

- add a custom route when you need request/response semantics
- add a custom message when you need push-style execution feedback
- keep route handlers thin and delegate real logic elsewhere
- use unique message names to avoid collisions with built-in events
