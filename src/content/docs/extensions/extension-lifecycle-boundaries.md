---
title: "Extension Lifecycle Boundaries"
---

**Evidence:** Official docs-backed from docs.comfy.org; Source-backed from pinned snapshots
**Last Updated:** 2026-05-21
**Primary Sources:** https://docs.comfy.org/custom-nodes/js/javascript_hooks, https://docs.comfy.org/development/comfyui-server/comms_routes, `references/snapshots/2026-05-21/comfyui-core-v0.22.0/server.py`
**Baseline verification status:** Verified against the current pinned baseline: core `v0.22.0`, frontend `v1.45.12`, snapshots `2026-05-21`.

## Scope

This page maps the main lifecycle boundaries that extension authors cross when
they move between frontend hooks, custom routes, server hooks, and graph-facing
custom nodes.

It is a routing page, not a full hook catalog. Use it when you know you need an
extension surface but are still deciding which lifecycle phase owns the work.

## Who This Page Is For

- frontend extension authors deciding where a behavior should attach
- hybrid extension authors separating UI, request/response, and execution logic
- custom node authors who discovered they also need a route or frontend layer

## Lifecycle Map

| Phase | Surface | Use it when | Do not use it for |
|---|---|---|---|
| App startup | frontend `setup`-style extension registration | menus, listeners, panels, global UI wiring | graph-executable processing |
| Node-definition registration | frontend hook registration around node types | widget defaults, node-type UI behavior, per-type patching | request/response APIs |
| Node instance lifecycle | per-node frontend hooks such as node creation handling | graph-instance UI behavior and editor feedback | backend execution changes |
| HTTP request/response | custom routes on `PromptServer.instance.routes` | explicit JSON or form endpoints for UI code or external tools | prompt-time interception |
| Prompt or execution callbacks | server hooks | prompt preprocessing, execution-time observation, logging, side effects | frontend rendering |
| Graph execution | custom nodes | inputs, outputs, and workflow-visible processing | editor-only UX changes |

## Choose the Narrowest Surface First

Start with the smallest lifecycle surface that solves the problem:

1. if the behavior exists only in the editor, stay in the frontend layer
2. if you need explicit client-to-server data exchange, add a custom route
3. if you need to observe or influence prompt or execution flow, use server hooks
4. if the behavior must appear as part of the workflow graph, add a custom node

Packages often combine more than one surface, but the surfaces still have
different contracts. A route-backed panel is not the same thing as a custom
node, and a custom node is not a substitute for editor-only UX work.

## Common Boundary Mistakes

### Putting editor behavior in Python execution code

If the only goal is a graph overlay, panel, menu action, or widget interaction,
the Python node layer is too deep. Keep that work in the frontend extension.

### Adding a route when the standard API already exposes the data

If `/prompt`, `/history`, `/queue`, `/object_info`, or the WebSocket stream
already provide the needed data, prefer the standard API surface before adding a
new extension-owned route.

### Using a route for workflow-visible computation

Routes are a request/response surface. If users need the behavior inside the
graph itself, add a custom node and keep any route secondary.

### Mixing execution callbacks with UI state assumptions

Server hooks run on the server side. They can emit data or record state, but the
UI still needs its own frontend registration path to display or react to that
state.

## Practical Reading Order

1. [Extension Patterns](patterns.md)
2. [Add Custom Routes](../how-to/add-custom-routes.md)
3. [Server Hooks](../hooks/server-hooks.md)
4. [JavaScript Hooks](../hooks/javascript-hooks.md)
5. [Custom Node and Extension Boundaries](../troubleshooting/custom-node-and-extension-boundaries.md)

## Read Next

- [Route-Backed Panels and Tools](route-backed-panels-and-tools.md)
- [Common Architectures](common-architectures.md)
- [Start Here: Extension Developer](../start-here/extension-developer.md)
