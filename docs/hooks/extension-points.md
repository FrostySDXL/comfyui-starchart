# Extension Points

**Evidence:** Official docs-backed from docs.comfy.org; Source-backed from pinned snapshots
**Last Updated:** 2026-05-05
**Primary Source:** https://docs.comfy.org/custom-nodes/js/javascript_hooks

## Primary Sources

- https://docs.comfy.org/custom-nodes/js/javascript_hooks
- https://docs.comfy.org/custom-nodes/js/javascript_objects_and_hijacking
- `references/snapshots/2026-04-30/comfyui-core-v0.20.1/server.py` (v0.20.1, commit 64b8457)
- `references/snapshots/2026-04-30/comfyui-core-v0.20.1/execution.py` (v0.20.1, commit 64b8457)

## Scope

ComfyUI extension work splits across a few distinct surfaces rather than one
universal plugin API. In practice, you choose between frontend hooks,
server-hook callbacks, custom routes, and custom nodes depending on what you
are trying to change.

## Available Entry Points

### 1. JavaScript extension hooks

Official frontend hooks include:

- `init`
- `beforeRegisterNodeDef`
- `nodeCreated`
- `setup`
- related workflow lifecycle hooks such as `beforeConfigureGraph` and
  `afterConfigureGraph`

These are the preferred way to modify client-side behavior.

### 2. Server hooks

On the Python side, `PromptServer.add_on_prompt_handler()` lets code inspect or
modify prompt JSON before validation and queueing. This is the callback-oriented
server-hook surface documented in [Server Hooks](server-hooks.md).

### 3. Execution and progress events

Runtime observability flows through the executor and the server WebSocket
event stream:

- progress handling via `WebUIProgressHandler`
- lifecycle events like `executing`, `executed`, and `execution_error`

### 4. Custom routes and route-owning managers

`server.py` shows that ComfyUI is willing to add behavior by composing
route providers and manager objects such as:

- `user_manager.add_routes(...)`
- `model_file_manager.add_routes(...)`
- `custom_node_manager.add_routes(...)`
- `subgraph_manager.add_routes(...)`
- `node_replace_manager.add_routes(...)`
- internal sub-app mounting under `/internal`

This is the clearest pattern to follow when an extension needs a new API
surface rather than a UI-only customization. These routes are part of the
broader server-side extension surface, but they are distinct from the narrower
callback-oriented server hooks above.

### 5. Custom nodes

Custom nodes remain the main execution-surface extension point. They are
the right tool when you need new graph behavior, new inputs/outputs, or
new workflow-building primitives.

## Selection Guidance

Use the narrowest extension point that matches the problem:

- use JavaScript hooks for UI behavior, node display tweaks, menus, and
  client-only workflow interactions
- use prompt hooks when you need to inspect or augment prompt JSON before
  queueing
- use execution/progress events when you need runtime monitoring,
  profiling, or live status overlays
- use custom routes when UI code, dashboards, or external tools need
  structured server data through HTTP request/response endpoints
- use custom nodes when the workflow graph itself needs new capability

## Anti-pattern to avoid

The official docs repeatedly warn against deep monkey-patching of app or
prototype internals unless there is no supported hook available.
Hook-first or route-first designs are more likely to survive upstream UI
changes.

## Read Next

- [JavaScript Hooks](javascript-hooks.md)
- [Server Hooks](server-hooks.md)
- [Extension Patterns](../extensions/patterns.md)
