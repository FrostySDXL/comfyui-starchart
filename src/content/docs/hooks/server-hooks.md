---
title: "Server Hooks"
---

**Evidence:** Official docs-backed from docs.comfy.org; Source-backed from pinned snapshots
**Last Updated:** 2026-05-19
**Primary Source:** ComfyUI core v0.21.1 `server.py` and `execution.py`, plus the pinned v0.19.3 `comfy_execution/progress.py` snapshot retained intentionally because the current pinned snapshot set still does not include an equivalent `comfy_execution/progress.py` path
**Baseline verification status:** Verified against the current pinned baseline: core `v0.21.1`, frontend `v1.45.9`, snapshots `2026-05-18`.

## Primary Sources

- https://docs.comfy.org/development/comfyui-server/comms_overview
- https://docs.comfy.org/development/comfyui-server/comms_messages
- https://docs.comfy.org/development/comfyui-server/comms_routes
- `references/snapshots/2026-05-18/comfyui-core-v0.21.1/server.py` (v0.21.1, commit 26515acd23fa291a8f5ab53c5997258598de0701)
- `references/snapshots/2026-05-18/comfyui-core-v0.21.1/execution.py` (v0.21.1, commit 26515acd23fa291a8f5ab53c5997258598de0701)
- `references/snapshots/2026-04-19/comfyui-core-v0.19.3/comfy_execution/progress.py` (v0.19.3, commit 308602640) -- intentionally retained because the current pinned snapshot set does not include an equivalent `comfy_execution/progress.py` path

## Scope

The current ComfyUI server exposes a small number of meaningful
server-side hook surfaces directly in Python. The most explicit one is
the prompt preprocessing hook chain stored in `self.on_prompt_handlers`.
Execution also exposes progress and lifecycle messaging through the
executor and WebSocket path, which is the main observability surface for
server-side integrations.

This page covers callback-oriented server hooks. Custom routes are also part of
the broader server-side extension surface, but they are a different extension
point and are documented separately in [Add Custom Routes](../how-to/add-custom-routes.md).

## Server-side surface boundaries

On the server side, three surfaces are easy to blur together:

- callback-oriented hooks
- runtime messages and events
- route-based extension surfaces

They overlap in real extensions, but they are not the same thing.

### Callback-oriented hooks

These are Python callbacks registered into server-controlled flow. In the
current pinned source, the clearest example is the prompt preprocessing chain
behind `add_on_prompt_handler(...)`.

### Runtime messages and events

These are the structured messages the executor and server emit during runtime.
They are most useful as an observability surface for UIs, dashboards, and
monitoring-style integrations.

### Route-based extension surfaces

These are explicit HTTP endpoints added by ComfyUI managers or extensions. When
you need new request/response behavior, routes are often the more concrete and
stable extension path than hoping for an additional Python callback hook.

## Hook Registration

### `add_on_prompt_handler(handler)`

`PromptServer` exposes:

```python
def add_on_prompt_handler(self, handler):
    self.on_prompt_handlers.append(handler)
```

That hook list is invoked by `trigger_on_prompt(json_data)` immediately
after the server reads the JSON body in `POST /prompt` and before queue
ordering, validation, and queue insertion happen.

In practice, this means an `on_prompt` handler can:

- inspect the submitted prompt payload
- add or normalize extra fields
- reject or reshape data indirectly by raising or returning modified JSON
- attach metadata before validation and queueing proceed

If a handler raises, the server logs a warning and continues processing
the remaining chain.

## Runtime messages and events

Execution-side observability is driven by `execution.py`.

### Progress handling

During `PromptExecutor.execute_async`, ComfyUI calls:

```python
add_progress_handler(WebUIProgressHandler(self.server))
```

That means the default Web UI is wired into execution progress through a
progress-handler abstraction rather than ad hoc prints or polling alone.

The pinned `comfy_execution/progress.py` snapshot defines the handler contract.
Custom handlers are registered by name, receive a registry through
`set_registry(...)`, and are called with these signatures:

- `start_handler(node_id, state, prompt_id)`
- `update_handler(node_id, value, max_value, state, prompt_id, image=None)`
- `finish_handler(node_id, state, prompt_id)`

The same file defines `NodeProgressState` with `state`, `value`, and `max`.

### Lifecycle messages

The executor sends structured events back through the server, including:

- `execution_start`
- `execution_cached`
- `executing`
- `executed`
- `execution_success`
- `execution_error`
- `execution_interrupted`

These messages are the practical server-side event stream available to
frontend clients and monitoring-style extensions.

Treat this as an event and observability surface. Do not read it as evidence of
a broad Python hook catalog.

## Route-based extension surfaces

The server-side extension story is broader than prompt callbacks. `server.py`
also shows route registration as a first-class way to extend behavior.

Examples in the pinned source include manager-owned route wiring such as:

- `user_manager.add_routes(...)`
- `model_file_manager.add_routes(...)`
- `custom_node_manager.add_routes(...)`
- `subgraph_manager.add_routes(...)`
- `node_replace_manager.add_routes(...)`

That matters because many integrations do not actually need a hook. They need a
new endpoint, a response body, or a server-owned operation. In those cases,
custom routes are often the better path.

## Observability implications

For metrics or profiler-style integrations, the current source shows two
main patterns:

- mutate or annotate prompt data before queueing with an on-prompt handler
- observe execution progress and lifecycle messages during runtime

That matches why tools like ProfilerX are better understood as hybrid
extensions: they need both prompt-time integration and runtime event
tracking.

## Choose which server-side surface fits

- choose prompt callbacks when you need to inspect or normalize prompt JSON
  before queueing
- choose runtime messages when you need live execution visibility
- choose custom routes when you need a concrete HTTP interface or new
  request/response behavior

## Limits of the current surface

- There is no large, formally documented Python hook catalog comparable
  to the JavaScript hook list.
- The source makes `on_prompt_handlers` explicit, but other server-side
  integration points are more architectural than declarative.
- If you need new server behavior, custom routes and manager-owned route
  registration are often a more concrete extension strategy than waiting
  for a dedicated hook.
- There is no universal cross-layer plugin API that merges callbacks,
  messages, routes, and frontend hooks into one supported abstraction.

## Read Next

- [JavaScript Hooks](javascript-hooks.md)
- [Extension Points](extension-points.md)
- [Add Custom Routes](../how-to/add-custom-routes.md)
