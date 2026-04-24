# Start Here: Extension Developer

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-04-21

## Who This Path Is For

You want to extend ComfyUI beyond what custom nodes can express. This includes:

- frontend UI changes (custom widgets, sidebar panels, graph modifications)
- server-side behavior changes (custom routes, execution hooks)
- hybrid extensions that combine both

**Prerequisites:** familiarity with JavaScript or Python, depending on which layer you target.

## Two Extension Layers

### Frontend Extensions

JavaScript-based, run in the browser/editor context. Access the LiteGraph
canvas, node graph, and UI through hooks and the app object.

Key resources:

- [JavaScript Hooks](../hooks/javascript-hooks.md) -- `beforeRegisterNodeDef`,
  `nodeCreated`, `setup`, and other extension points
- [Extension Points](../hooks/extension-points.md) -- broader overview of what
  hooks are available
- Frontend extension examples in `examples/extensions/`

### Server Extensions

Python-based, run on the ComfyUI server process. Can add custom routes,
modify execution behavior, and expose new APIs.

Key resources:

- [Server Hooks](../hooks/server-hooks.md) -- execution callbacks and lifecycle hooks
- [API Endpoints](../api/endpoints.md) -- existing routes as reference for your own
- [Custom Routes](../how-to/add-custom-routes.md) -- how to add extension-owned routes
- [Extending Server](../tutorials/extending-server.md) -- worked tutorial

## Frontend vs Server Decision

| Goal | Layer |
|------|-------|
| Custom widgets, node UI tweaks | Frontend |
| Sidebar panels, graph commands | Frontend |
| Execution timing, node interception | Server hooks |
| New HTTP API for external tools | Custom routes |
| Metrics, profiling, monitoring | Hybrid (both layers) |

## Recommended Reading Order

1. [JavaScript Hooks](../hooks/javascript-hooks.md) -- core frontend extension API
2. [Server Hooks](../hooks/server-hooks.md) -- execution lifecycle callbacks
3. [Extension Patterns](../extensions/patterns.md) -- architectural patterns and
   when to use each approach
4. [Common Architectures](../extensions/common-architectures.md) -- composition
   patterns from real extensions
5. [ProfilerX Analysis](../extensions/profilerx-analysis.md) -- worked example of
   a hybrid extension

## Common Patterns to Study

- **Route-backed panel** -- frontend panel + backend routes (dashboards, inspectors)
- **Runtime monitoring** -- ProfilerX pattern: listen to execution events,
  expose metrics through a frontend panel
- **Hook-provider composition** -- community pattern (from Impact-Pack): hook
  nodes that expose configuration hooks to the graph

[Extension Patterns](../extensions/patterns.md) covers detailed tradeoffs.

## If You Are Building for Distribution

Read [Integrate with Manager](../how-to/integrate-with-manager.md) to understand
how extension packages get distributed. Frontend extensions that are part of
a node pack follow the same publication flow as pure node packages.

## First Practical Step

Create a `web/extensions/my_extension/` directory with a `my_extension.js` file
that registers an `app.registerExtension` call adding one `nodeCreated` hook.
Load ComfyUI, add a node to the graph, and verify your hook logs to the browser
console.

## Read Next

- [JavaScript Hooks](../hooks/javascript-hooks.md) -- core frontend extension API
- [Server Hooks](../hooks/server-hooks.md) -- execution lifecycle callbacks
- [Extension Patterns](../extensions/patterns.md) -- architectural tradeoffs
- [Decision Tree: API Integration](../decision-trees/api-integration.md) -- if you discover you need integration, not extension
