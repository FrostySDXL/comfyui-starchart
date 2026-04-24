# Example: Benchmark Harness Skeleton

**Status:** Source-backed example

## What This Example Is

This directory is a minimal hybrid extension that demonstrates a small benchmark
or profiling harness for ComfyUI.

It keeps scope tight on purpose:

- register one Python-side metrics collector
- re-attach one progress handler during execution setup
- expose one read-only JSON route
- render one lightweight frontend panel with a manual refresh button

The example is meant to be studied and copied in small pieces. It is not a
production profiler and it does not persist history.

## Primary Sources

- `docs/how-to/add-custom-routes.md` - repo summary of the supported custom route pattern
- `docs/tutorials/extending-server.md` - repo summary of route and message usage
- `docs/hooks/server-hooks.md` - repo summary of prompt and execution surfaces
- `docs/tutorials/adding-background-metrics.md` - repo guidance for small metrics extensions
- `references/snapshots/2026-04-19/comfyui-core-v0.19.3/server.py` - pinned route registration and `/api` mirroring behavior
- `references/snapshots/2026-04-19/comfyui-core-v0.19.3/execution.py` - pinned execution path showing `reset_progress_state(...)` and `add_progress_handler(WebUIProgressHandler(self.server))`
- `references/snapshots/2026-04-19/comfyui-core-v0.19.3/comfy_execution/progress.py` - pinned `ProgressHandler` contract, registry behavior, and callback signatures
- `examples/custom-nodes/example-4-progress-ui/` - repo example for frontend event listeners and `WEB_DIRECTORY`
- `examples/custom-nodes/example-5-full-extension-package/` - repo example for package layout and frontend export pattern

## Files

- `__init__.py` - package entry point; creates the collector, installs the handler, and registers routes
- `metrics_collector.py` - in-memory per-node timing collector and pinned `ProgressHandler` implementation
- `routes.py` - `GET /benchmark-harness/stats` route registration
- `web/index.js` - small panel that fetches stats and refreshes on built-in execution events

## What It Implements

### 1. In-memory timing only

The collector records start and finish timestamps per `(prompt_id, node_id)` and
returns a compact summary:

- run count
- last duration in milliseconds
- total and average duration in milliseconds
- whether a finish arrived without a matching start

### 2. Supported route registration

The route follows the documented pattern based on `PromptServer.instance.routes`
and returns `web.json_response(...)`.

The pinned `server.py` snapshot also shows that ComfyUI mirrors ordinary routes
under `/api`, so this example is reachable at both:

- `/benchmark-harness/stats`
- `/api/benchmark-harness/stats`

### 3. Frontend refresh from built-in execution events

The frontend listens for built-in execution messages such as `executing`,
`executed`, `execution_success`, and `execution_error`, then re-fetches the JSON
route. This keeps the UI small and avoids custom message formats.

## Evidence Level

- Route registration through `PromptServer.instance.routes`: source-backed from pinned `server.py` and the repo route docs
- Frontend extension export through `WEB_DIRECTORY` and `app.registerExtension(...)`: source-backed in repo examples and official-doc summaries linked by repo docs
- Progress-handler registration path (`reset_progress_state(...)` followed by `add_progress_handler(...)`): source-backed from pinned `execution.py`
- Custom progress-handler contract (`name`, `enabled`, `set_registry(...)`, `start_handler(node_id, state, prompt_id)`, `update_handler(...)`, `finish_handler(...)`, `reset()`): source-backed from pinned `comfy_execution/progress.py`
- `start_handler` and `finish_handler` receive `node_id`, `state`, and `prompt_id`; this example looks up `class_type` and `display_node` through the registry's `dynprompt` instead of assuming those values are callback arguments
- Re-registering the custom handler by wrapping `reset_progress_state(...)` is a practical implementation pattern based on current pinned runtime behavior, not a separately documented stable extension API

## Limitations

- no disk persistence, archive support, or history browser
- no cache-hit inference beyond counting finishes without matching starts
- no attempt to replicate ProfilerX storage or UI features
- `update_handler(...)` is implemented as a no-op because this example only measures node start and finish timing
- the handler re-attachment logic is intentionally minimal and depends on the current pinned progress-reset lifecycle, so revisit it when updating snapshots or targeting newer ComfyUI versions

## Usage Notes

1. Copy this directory into a ComfyUI `custom_nodes/` environment.
2. Start ComfyUI.
3. Open the UI and use the `Benchmark Harness` panel to refresh stats.
4. Run a workflow and watch the panel update from the built-in execution events.

If the progress hook does not attach on a different ComfyUI version, check that
the runtime still exposes the pinned `ProgressHandler` registration path:
`comfy_execution.progress.add_progress_handler`, `reset_progress_state`, and a
handler object with `name`, `enabled`, `set_registry(...)`, and `reset()`.
