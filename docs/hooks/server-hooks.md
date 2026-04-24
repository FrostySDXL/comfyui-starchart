# Server Hooks

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-04-24
**Primary Source:** ComfyUI core v0.19.3 `server.py`, `execution.py`, and `comfy_execution/progress.py` (pinned snapshots)

## Primary Sources

- `references/snapshots/2026-04-19/comfyui-core-v0.19.3/server.py` (v0.19.3, commit 308602640)
- `references/snapshots/2026-04-19/comfyui-core-v0.19.3/execution.py` (v0.19.3, commit 308602640)
- `references/snapshots/2026-04-19/comfyui-core-v0.19.3/comfy_execution/progress.py` (v0.19.3, commit 308602640)

## Scope

The current ComfyUI server exposes a small number of meaningful
server-side hook surfaces directly in Python. The most explicit one is
the prompt preprocessing hook chain stored in `self.on_prompt_handlers`.
Execution also exposes progress and lifecycle messaging through the
executor and WebSocket path, which is the main observability surface for
server-side integrations.

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

## Metrics and Events

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

## Observability implications

For metrics or profiler-style integrations, the current source shows two
main patterns:

- mutate or annotate prompt data before queueing with an on-prompt handler
- observe execution progress and lifecycle messages during runtime

That matches why tools like ProfilerX are better understood as hybrid
extensions: they need both prompt-time integration and runtime event
tracking.

## Limits of the current surface

- There is no large, formally documented Python hook catalog comparable
  to the JavaScript hook list.
- The source makes `on_prompt_handlers` explicit, but other server-side
  integration points are more architectural than declarative.
- If you need new server behavior, custom routes and manager-owned route
  registration are often a more concrete extension strategy than waiting
  for a dedicated hook.

## Read Next

- [JavaScript Hooks](javascript-hooks.md)
- [Extension Points](extension-points.md)
