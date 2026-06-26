---
title: "Architecture Overview"
---

**Evidence:** Official docs-backed from docs.comfy.org; Source-backed from pinned snapshots
**Last Updated:** 2026-06-26
**Baseline verification status:** Verified against the current pinned baseline: core v0.26.0, frontend v1.47.5, snapshots 2026-06-26.

## Scope

This page is a bounded conceptual overview of ComfyUI architecture for readers
who need the system shape before diving into detailed reference pages.

It is not a full subsystem map, an exhaustive internal architecture reference,
or a replacement for the official docs.

If you need the deeper server-side map, continue to
[Execution Pipeline](execution-pipeline.md).

## What ComfyUI Is at a High Level

ComfyUI combines a workflow graph model, a Python execution server, and a
browser-based editor.

- The **workflow graph** describes nodes, links, and execution intent.
- The **server** validates prompts, executes work, exposes HTTP routes, and
  emits WebSocket events.
- The **client** renders the editor, widgets, and interactive graph behavior.

That split matters because some integration paths talk only to the server, while
others depend on a connected browser client.

## Workflow / Graph Model

The workflow is the core interchange unit.

- A workflow JSON document describes nodes and their connections.
- Prompt submission sends a workflow to an execution surface.
- History and output lookup happen after execution, not inside the workflow
  description itself.

This is why tooling should usually separate three questions:

1. What workflow graph is being described?
2. Which surface will execute it?
3. How will progress and results be observed?

## Client-Server Model

The pinned local API docs and official custom-node guidance both rely on a
client-server model.

- The **server side** owns execution, queue state, node metadata, files, and
  HTTP/WebSocket transport.
- The **client side** owns editor UI, widgets, graph interactions, and frontend
  extensions.

That boundary explains several common limitations:

- API mode can submit and monitor work, but it does not load the frontend.
- Frontend-only behavior does not automatically carry over into API-only tools.
- Tightly connected client-server node behavior should not be flattened into a
  generic API assumption.

## Local API vs Cloud API vs MCP

ComfyUI now exposes multiple official tooling surfaces. Treat them as related,
not identical.

### Local API

The local API is the most direct server-facing integration surface in this repo.
It centers on routes such as `/prompt`, `/queue`, `/history`, `/object_info`,
and the `GET /ws` execution stream.

### Cloud API

The cloud API is a separate official hosted surface. It should be treated as a
distinct execution and retrieval environment rather than as a guaranteed mirror
of local-instance behavior.

### MCP

The MCP server is a higher-level tool-integration surface for assistant or agent
workflows. It is conceptually different from direct local prompt submission and
from the repo's published JSON artifacts.

## Extension Surfaces

Two extension categories matter most at this level:

- **Custom nodes** add graph-executable capability.
- **Frontend extensions** add editor-side UI or interaction behavior.

Some packages contain both, but they should still be reasoned about as separate
surfaces. A workflow that depends on frontend extension behavior is not the same
thing as a workflow that can be reproduced from server-side API calls alone.

## Workflow JSON and Node Discovery

Two machine-facing surfaces recur across this docs set:

- **Workflow JSON** is the graph interchange surface.
- **`object_info`** is the runtime node-discovery surface for the current
  instance.

The repo's published artifacts complement those surfaces with a pinned baseline.
They do not replace live runtime discovery when installed custom-node state is
the thing you actually need to inspect.

## What This Page Does Not Try to Do

This page intentionally does not:

- map every internal subsystem
- document every route or message type
- reteach custom-node authoring or frontend hooks
- turn cloud or MCP into exhaustive reference sections

Use it as a mental-model page, then move to the narrower reference or start-here
surface that matches your task.

## Read Next

- [Execution Pipeline](execution-pipeline.md)
- [Start Here: Tooling Builder](../start-here/tooling-builder.md)
- [Extension Points](../hooks/extension-points.md)
- [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md)
