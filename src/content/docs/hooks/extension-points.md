---
title: "Extension Points"
---

**Evidence:** Official docs-backed from docs.comfy.org; Source-backed from pinned snapshots
**Last Updated:** 2026-05-13
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

This page is a chooser. It helps you decide which layer fits the job. It does
not define a complete plugin-architecture specification.

## Decision matrix

| Surface | Choose it when | Best for | Avoid when |
|---------|----------------|----------|------------|
| JavaScript hooks | The behavior is in the browser or editor | menus, widgets, node display, workflow-load UI behavior, editor lifecycle integration | the change needs new server state or a stable HTTP surface |
| Server callback hooks | You need to inspect or adjust prompt JSON before queueing | prompt preprocessing, metadata attachment, narrow request-time normalization | you need a broad Python hook catalog or long-lived runtime APIs |
| Runtime messages and events | You need live execution visibility | progress views, status overlays, execution monitoring, profiling-style observability | you need request/response control or prompt mutation |
| Custom routes | You need a concrete server API | dashboards, external integrations, request/response workflows, server-owned actions | the problem is UI-only or already covered by an existing hook |
| Custom nodes | The graph needs new capability | new inputs, outputs, computation, or workflow-building primitives | the job is only editor chrome or server transport plumbing |

## Choose by problem shape

### UI-only

If the change lives entirely in the editor, start with
[JavaScript Hooks](javascript-hooks.md). This is the default surface for node
menus, widget behavior, workflow-load UI adjustments, and other frontend-only
changes.

If the UI behavior is specifically about active subgraphs, traversal,
subgraph-aware identifiers, or widget promotion across graph boundaries, route
to [Subgraph Extension Behavior](subgraph-extension-behavior.md) after the main
hook-selection pass.

### Prompt preprocessing

If the change must inspect or normalize prompt JSON before validation and
queueing, use the callback-oriented server hook surface documented in
[Server Hooks](server-hooks.md).

### Runtime observability

If the goal is to watch execution progress, lifecycle, or status transitions,
use runtime messages and execution events. Treat these as an observability
surface, not as a large hook inventory.

### Request/response integration

If a frontend panel, service, or external tool needs a clear server endpoint,
prefer [Add Custom Routes](../how-to/add-custom-routes.md). A route is usually a
better fit than trying to force request/response work through callbacks or UI
hooks.

### Graph-capability extension

If workflows need a new operation, datatype, or graph-building primitive, build
or extend a custom node. Custom nodes are the main extension surface for adding
capability to the graph itself.

## Available entry points

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

## Boundary guidance

These surfaces are adjacent, but they are not interchangeable:

- JavaScript hooks shape frontend and editor behavior.
- Server callback hooks affect prompt submission before queueing.
- Runtime messages expose execution status after work is in motion.
- Custom routes expose explicit request/response APIs.
- Custom nodes extend what the workflow graph can do.

That boundary matters because many extension ideas cross layers. For example, a
runtime monitor may combine custom routes, runtime events, and frontend UI. The
surfaces can work together, but they do not collapse into one universal plugin
API.

## Supported-first guidance

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

Prefer hook-first or route-first designs before reaching for deeper patching.
If the official frontend hooks or a clear route surface can support the change,
use them instead of rewriting core methods or leaning on fragile internals.

## Anti-patterns to avoid

The official docs repeatedly warn against deep monkey-patching of app or
prototype internals unless there is no supported hook available.
Hook-first or route-first designs are more likely to survive upstream UI
changes.

Avoid treating routes, messages, callbacks, and custom nodes as different names
for the same extension API. They solve different classes of problems.

## Read Next

- [JavaScript Hooks](javascript-hooks.md)
- [Server Hooks](server-hooks.md)
- [Subgraph Extension Behavior](subgraph-extension-behavior.md)
- [Add Custom Routes](../how-to/add-custom-routes.md)
- [Extension Patterns](../extensions/patterns.md)
