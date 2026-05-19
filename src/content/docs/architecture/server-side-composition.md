---
title: "Server-Side Composition"
---

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-05-19
**Primary Sources:**
- `references/snapshots/2026-05-18/comfyui-core-v0.21.1/server.py` (v0.21.1, commit 26515acd23fa291a8f5ab53c5997258598de0701)
- `references/snapshots/2026-05-18/comfyui-core-v0.21.1/execution.py` (v0.21.1, commit 26515acd23fa291a8f5ab53c5997258598de0701)
- `references/snapshots/2026-05-18/comfyui-frontend-v1.45.9/src/scripts/app.ts` (v1.45.9, commit 2dbf49fd9da0e0b809ee1f4e663148c79f730cc2)
- `references/snapshots/2026-05-18/comfyui-frontend-v1.45.9/src/types/comfy.ts` (v1.45.9, commit 2dbf49fd9da0e0b809ee1f4e663148c79f730cc2)
**Baseline verification status:** Verified against the current pinned baseline: core `v0.21.1`, frontend `v1.45.9`, snapshots `2026-05-18`.

## Scope

This page maps how ComfyUI composes its running server surface: route tables,
manager-owned subsystems, extension web assets, prompt hooks, and execution
integration points. It is not a route-by-route API reference and not a frontend
hook catalog.

## PromptServer as the Composition Root

At the pinned baseline, `PromptServer` is the main composition root.

It owns or coordinates:

- the main route table
- the `/internal` sub-application
- the WebSocket connection registry
- the prompt queue
- the execution-facing server message bridge

That makes it the place where request handling, execution status delivery, and
extension surfaces meet.

## Route Tables and Compatibility Aliases

`add_routes()` shows the main route composition pattern.

First, manager-owned route providers register onto the main route table. Then
the server creates compatibility aliases by mirroring non-static routes under an
`/api` prefix. After that it mounts the main routes, extension static assets,
templates, embedded docs, and the final static web root.

This matters because ComfyUI does not expose one single plugin registry for all
behavior. Instead, it composes a running app from several route-owning and
asset-owning subsystems.

## Manager-Owned Server Subsystems

The pinned `add_routes()` call chain shows a clear manager pattern:

- `user_manager`
- `model_file_manager`
- `custom_node_manager`
- `subgraph_manager`
- `node_replace_manager`

Those managers own narrower concerns than `PromptServer` itself. The server
coordinates them, but does not flatten them into one giant route definition
block.

Architecturally, this is the clearest evidence that ComfyUI prefers
subsystem-level composition over one universal extension API surface.

## Custom Nodes as a Separate Capability Surface

Custom nodes are part of server-side composition, but they solve a different
problem than routes or prompt hooks.

- custom nodes extend graph-executable capability
- custom routes extend request/response behavior
- prompt hooks intercept or adjust prompt submission flow

That distinction explains why a package can contain both nodes and routes
without those being the same kind of extension.

## Prompt Hooks Sit Before Validation and Queueing

`POST /prompt` shows where prompt hooks fit. The handler reads JSON, calls the
prompt-hook trigger, applies node replacements, then validates and queues the
graph.

That means prompt hooks are part of request preprocessing, not a generic runtime
hook system for every later execution stage.

## WebSocket Delivery Is a Server Concern, Not a Frontend Hook

The server owns socket tracking, event publishing, JSON event dispatch, and
binary preview delivery. The browser consumes those messages, but the event
transport itself belongs to the server-side composition layer.

This is why runtime monitoring features often become hybrid designs:

- server routes or queue state for structured data
- server WebSocket events for live execution visibility
- frontend UI for presentation and interaction

## Frontend Extension Assets Are Served Separately

The same composition method also mounts web extension directories under
`/extensions/<name>`.

That tells you two useful things:

- frontend extensions are served as web assets, not discovered through the
  prompt API
- API-only integrations do not automatically gain frontend extension behavior,
  because the browser/editor path is a separate runtime surface

## Why This Composition Model Matters

The pinned server design encourages a few good mental models:

- treat routes, nodes, hooks, and frontend assets as adjacent but distinct
  surfaces
- expect subsystem ownership rather than one monolithic server API file
- choose the narrowest extension surface that matches your problem

That is also why route-first, hook-first, and node-first decisions should be
made explicitly. They plug into different parts of the running system.

## What This Page Does Not Try to Do

This page does not:

- list every built-in route
- define every frontend hook signature
- document manager internals beyond their ownership role
- claim that all observed internal patterns are stable public contracts

Use it for system shape, then move to API, hooks, or custom-node docs for exact
implementation guidance.

## Read Next

- [Architecture Overview](overview.md)
- [Execution Pipeline](execution-pipeline.md)
- [Extension Points](../hooks/extension-points.md)
- [Add Custom Routes](../how-to/add-custom-routes.md)
- [Server.py Summary](../reference/server-py-summary.md)
