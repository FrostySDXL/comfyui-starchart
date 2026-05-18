---
title: "Start Here: Extension Developer"
---

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-05-18

## Who This Path Is For

You want to extend ComfyUI beyond what custom nodes can express. This includes:

- frontend UI changes (custom widgets, sidebar panels, graph modifications)
- server-side behavior changes (custom routes, server hooks)
- hybrid extensions that combine both

**Prerequisites:** familiarity with JavaScript or Python, depending on which layer you target.

## First Practical Step

Create a `web/extensions/my_extension/` directory with a `my_extension.js` file
that registers an `app.registerExtension` call adding one `nodeCreated` hook.
Load ComfyUI, add a node to the graph, and verify your hook logs to the browser
console.

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

Within the broader server-side extension surface, keep these terms separate:

| Surface | What it is | Use it when |
|------|------|------|
| Server hooks | Callback-oriented prompt or execution integration points | You need prompt preprocessing or execution-time observation |
| Custom routes | Extension-owned HTTP endpoints registered on `PromptServer.instance.routes` | You need request/response access for UI code or external tools |
| Custom nodes | Graph-executable Python nodes | You need new workflow behavior or graph-facing primitives |
| Frontend hooks | Browser/editor hook surfaces | You need UI or graph-editor changes |

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

If your hybrid package includes a legacy V1 node plus a route, keep the node
contract in the authoritative
[V1 Custom Node Reference](../custom-nodes/v1-reference.md) and treat the route
as a separate server-side extension point.

## Recommended Reading Order

1. [Server-Side Composition](../architecture/server-side-composition.md) -- where routes, hooks, managers, and extension assets fit
2. [JavaScript Hooks](../hooks/javascript-hooks.md) and [Server Hooks](../hooks/server-hooks.md) -- core frontend and callback-oriented server surfaces
3. [Extension Patterns](../extensions/patterns.md) -- how to choose a stable implementation shape

## Deeper Reading

- [Common Architectures](../extensions/common-architectures.md) -- composition
  patterns from real extensions
- [ProfilerX Analysis](../extensions/profilerx-analysis.md) -- worked example of
  a hybrid extension

## Common Patterns to Study

- **Route-backed panel** -- frontend panel + backend routes (dashboards, inspectors)
- **Minimal hybrid package** -- one small V1 node + one custom route in the same
  Python package; see `examples/extensions/hybrid-v1-route/`
- **Runtime monitoring** -- ProfilerX pattern: listen to execution events,
  expose metrics through a frontend panel
- **Hook-provider composition** -- community pattern (from Impact-Pack): hook
  nodes that expose configuration hooks to the graph

[Extension Patterns](../extensions/patterns.md) covers detailed tradeoffs.

## If You Are Building for Distribution

Read [Integrate with Manager](../how-to/integrate-with-manager.md) to understand
how extension packages get distributed. Frontend extensions that are part of
a node pack follow the same publication flow as pure node packages.

## When to Switch to Repo-Local Workflow Docs

Stay in the published docs path unless you are contributing changes to this
repository itself. If you begin editing repo docs, examples, or scripts, switch
to the repo's `CONTRIBUTING.md` file for maintainer-grade workflow details.

## Read Next

- [JavaScript Hooks](../hooks/javascript-hooks.md) -- core frontend extension API
- [Server-Side Composition](../architecture/server-side-composition.md) -- system map for server-owned extension surfaces
- [Server Hooks](../hooks/server-hooks.md) -- execution lifecycle callbacks
- [Extension Patterns](../extensions/patterns.md) -- architectural tradeoffs
- [Decision Tree: API Integration](../decision-trees/api-integration.md) -- if you discover you need integration, not extension

If you want a short map of the hook surfaces before reading individual hook
pages, start with the [Hooks Section Guide](../hooks/index.md).

If you are unsure whether a problem belongs to a frontend extension, a Python
node, or both, see
[Custom Node and Extension Boundaries](../troubleshooting/custom-node-and-extension-boundaries.md).
