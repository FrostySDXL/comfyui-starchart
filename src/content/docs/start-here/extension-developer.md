---
title: "Start Here: Extension Developer"
---

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-07-23
**Primary Sources:** `references/snapshots/2026-07-23/comfyui-frontend-v1.48.4/src/scripts/app.ts`, `references/snapshots/2026-07-23/comfyui-frontend-v1.48.4/src/types/comfy.ts`, `references/snapshots/2026-07-23/comfyui-core-v0.28.0/server.py`, `references/snapshots/2026-07-23/comfyui-core-v0.28.0/nodes.py`, `references/snapshots/2026-07-23/comfyui-core-v0.28.0/comfy_api/latest/__init__.py`
**Baseline verification status:** Verified against the current pinned baseline: core v0.28.0, frontend v1.48.4, snapshots 2026-07-23.

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
- [Extension Points](../hooks/extension-points.md) -- when a custom route is more truthful than a callback

## Frontend vs Server Decision

| Goal | Layer |
|------|-------|
| Custom widgets, node UI tweaks | Frontend |
| Sidebar panels, graph commands | Frontend |
| Execution timing, node interception | Server hooks |
| New HTTP API for external tools | Custom routes |
| Metrics, profiling, monitoring | Hybrid (both layers) |

If your package combines nodes and routes, keep the node contract and the route
surface separate. A graph-executable node and an HTTP extension endpoint solve
different problems.

## Recommended Reading Order

1. [Architecture Overview](../architecture/overview.md) -- system shape and
   client/server boundary
2. [JavaScript Hooks](../hooks/javascript-hooks.md) and [Server Hooks](../hooks/server-hooks.md) -- core frontend and callback-oriented server surfaces
3. [Extension Points](../hooks/extension-points.md) -- chooser for hooks,
   routes, events, and custom nodes

## Common Patterns to Study

- **Route-backed panel** -- frontend panel + backend routes (dashboards, inspectors)
- **Minimal hybrid package** -- one small node + one custom route in the same
  Python package; see `examples/extensions/hybrid-v1-route/`
- **Runtime monitoring** -- ProfilerX pattern: listen to execution events,
  expose metrics through a frontend panel
- **Hook-provider composition** -- a hybrid pattern where graph-facing nodes and
  frontend or server extension code cooperate without collapsing into one layer

## If You Are Building for Distribution

Distribution details change faster than this reduced surface should carry. Keep
the retained pages focused on extension shape, hooks, routes, and boundaries.

## When to Switch to Repo-Local Workflow Docs

Stay in the published docs path unless you are contributing changes to this
repository itself. If you begin editing repo docs, examples, or scripts, switch
to the repo's `CONTRIBUTING.md` file for maintainer-grade workflow details.

## Read Next

- [JavaScript Hooks](../hooks/javascript-hooks.md) -- core frontend extension API
- [Architecture Overview](../architecture/overview.md) -- system map for server-owned extension surfaces
- [Server Hooks](../hooks/server-hooks.md) -- execution lifecycle callbacks
- [Extension Points](../hooks/extension-points.md) -- architectural chooser for retained extension surfaces
- [Start Here: Local API Integration](service-integration.md) -- if the problem is
  really API-first integration rather than an extension
