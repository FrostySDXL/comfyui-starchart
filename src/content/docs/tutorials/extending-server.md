---
title: "Extending the Server"
---

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-04-30
**Primary Source:** https://docs.comfy.org/development/comfyui-server/comms_routes

## Primary Sources

- https://docs.comfy.org/development/comfyui-server/comms_routes
- https://docs.comfy.org/development/comfyui-server/comms_messages
- https://docs.comfy.org/custom-nodes/backend/lifecycle
- `references/snapshots/2026-04-30/comfyui-core-v0.20.1/server.py` (v0.20.1, commit 64b8457)

## Overview

Extending the ComfyUI server usually means one of two things:

- adding a custom HTTP route for client-to-server communication
- sending custom execution messages back to the client over the existing
  WebSocket/message system

The built-in server already exposes a large route surface, but custom
routes are the normal answer when an extension needs its own request
path, structured mutation, or lightweight API.

This page distinguishes:

- official behavior — native ComfyUI routes and message patterns
- upstream source behavior — what `server.py` currently implements
- community integration patterns — wrapper servers or extension-owned APIs
  built around ComfyUI, not part of native ComfyUI itself

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

## Community integration patterns

The following are useful design patterns seen in real projects, but they
are not native ComfyUI server features.

### 1. Extension-owned tool APIs

Some custom node packs add their own `/api/...` namespace for external
tools while still using standard ComfyUI prompt execution for generation.

Pattern-study example:

- `Acly/comfyui-tooling-nodes` adds `/api/etn/...` routes for cached image
  transfer, model inspection, and translation helpers

This is a good pattern when an extension needs tool-facing upload,
download, or metadata operations that do not fit cleanly into graph
execution alone.

### 2. Stateless façade servers in front of ComfyUI

Some projects keep ComfyUI itself behind another service that accepts a
friendlier or more scalable API, then translates requests into prompt
graphs and downstream result handling.

Pattern-study examples:

- `SaladTechnologies/comfyui-api` wraps ComfyUI with a stateless API,
  webhooks, storage backends, and remote asset download helpers
- `ai-dock/comfyui-api-wrapper` adds a FastAPI service with separate
  preprocess, generation, and postprocess stages plus workflow modifiers

These are useful production patterns when you need queue isolation,
storage integration, or a cleaner public API surface. They should be
documented as wrapper behavior, not as built-in ComfyUI endpoints.

### 3. Thin app-specific frontends

At the small end of the spectrum, some projects wrap one exported workflow
with a minimal user-facing web app.

Pattern-study example:

- `Tiefflieger06/comfyui-simple-frontend` uses a small Flask app and an
  exported API workflow as the backend template for a prompt form

This is often enough when you only need one or two opinionated user flows.

## Rule of thumb

- if the functionality belongs to your custom node or extension, add an
  extension-owned route
- if you need a separate product surface, auth model, or scaling layer,
  build a wrapper server in front of ComfyUI
- when documenting either approach, label wrapper-specific behavior as a
  community integration pattern rather than native ComfyUI behavior

## Read Next

- [Add Custom Routes](../how-to/add-custom-routes.md)
- [Server Hooks](../hooks/server-hooks.md)
