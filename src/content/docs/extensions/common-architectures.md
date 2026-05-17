---
title: "Common Architectures"
---

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-05-05
**Primary Source:** https://docs.comfy.org/custom-nodes/overview

## Primary Sources

- current ProfilerX rewrite: https://github.com/ryanontheinside/ComfyUI_ProfilerX
- https://docs.comfy.org/custom-nodes/overview
- https://docs.comfy.org/custom-nodes/js/javascript_hooks
- https://docs.comfy.org/development/comfyui-server/comms_routes

## Scope

This page documents the main extension architecture families observed across
the ComfyUI ecosystem and the tradeoffs each approach creates.

This page uses three evidence levels:

- official behavior -- stated in `docs.comfy.org`
- upstream source behavior -- visible in ComfyUI's own source tree
- community pattern examples -- useful repo patterns seen in the ecosystem,
  but not part of ComfyUI's contract

## Architecture Families

### Node suites

These packages primarily add many nodes under one namespace or category.
They are execution-centric and usually have the lowest maintenance risk.

Typical shape:

- Python node definitions
- registration layer
- little or no custom UI

Community pattern examples:

- large suites often split reusable logic into `modules/` or helper files
  instead of keeping every node in one file
- mature packs often ship example workflows, docs, or troubleshooting notes
  beside the nodes so users can understand intended graph composition
- some packs add bundle/helper nodes that reduce wiring for repeated graph
  structures

Examples for pattern study only:

- `ltdrdata/ComfyUI-Impact-Pack` shows a large active node suite with
  modules, docs, example workflows, JS, tests, and compatibility notes
- `ltdrdata/was-node-suite-comfyui` shows an older large-pack pattern with
  helper modules, resources, tests, and utility nodes such as bus/cache
  helpers

Those repos are useful examples of package organization, not authoritative
definitions of how custom nodes must be structured.

### UI overlays and menu tools

These extensions modify the editor experience rather than adding heavy
server behavior.

Typical shape:

- JS hook registration
- menu or panel UI
- optional event listeners

### Route-backed tools

These packages expose custom backend endpoints and pair them with
frontend controls.

Typical shape:

- `@routes.get` or `@routes.post` handlers
- frontend `fetchApi(...)` calls
- stable JSON contracts

Community pattern examples:

- tool-facing extensions often add a small extension-owned `/api/...`
  namespace instead of overloading graph execution routes
- some integrations use routes for upload/download or metadata lookup, then
  still rely on the normal prompt execution path for generation

Example for pattern study only:

- `Acly/comfyui-tooling-nodes` adds custom `/api/etn/...` routes for cached
  image transfer, translation, and model inspection to support external tool
  integrations

### Minimal hybrid packages

These packages stay server-side but combine one small node surface with one
small route surface in the same extension.

Typical shape:

- `__init__.py` exports `NODE_CLASS_MAPPINGS`
- `routes.py` registers `PromptServer.instance.routes` handlers
- a small README points readers back to the authoritative V1 contract when the
  node uses V1 registration

Use this shape when you need one graph-facing primitive and one request/response
endpoint, but do not need frontend JS yet. The repo's worked example lives at
`examples/extensions/hybrid-v1-route/`. For the V1 node contract that example
reuses, go to the [V1 Custom Node Reference](../custom-nodes/v1-reference.md).

### Metrics and monitoring dashboards

Profiler-style tools combine several layers:

- runtime event observation
- metrics collection in Python
- persistence/history storage
- frontend dashboard components

The current `ComfyUI_ProfilerX` rewrite is a strong example. Its active
registration path shows:

- Python backend files such as `__init__.py`, `handler.py`, `metrics.py`,
  `routes.py`, and `storage.py`
- frontend UI under `web/` with views, tabs, tables, and monitor/popup
  modules
- explicit REST endpoints for stats and archive management

Like many active extensions, the repo also contains legacy implementation files
from an older design. That is common in community extensions and is a reminder
to distinguish active integration paths from historical code.

### Full hybrid products

These combine nodes, frontend UI, routes, storage, and monitoring into a
larger product-style extension. They are powerful but need stronger
version discipline and clearer contracts.

Community pattern examples:

- pipe or bundle nodes to collapse repeated multi-input state into one graph
  value
- hook-provider nodes that encapsulate reusable execution-time behavior and
  can be combined declaratively
- repo-local docs and compatibility notices because these products often
  depend on specific upstream versions or companion packs

Example for pattern study only:

- `ltdrdata/ComfyUI-Impact-Pack` is a strong example of a hybrid product-like
  node pack that uses bundle types, hook providers, examples, and explicit
  compatibility notes

## Design Tradeoffs

### Simpler architectures

Node-only or hook-only extensions are easier to maintain and less likely
to break when ComfyUI changes.

### More capable architectures

Hybrid dashboards and route-backed tools can deliver much better user
experience, but they create more surfaces that must stay compatible:

- message/event assumptions
- route payload shapes
- frontend bundle behavior
- persistence formats

### Rule of thumb

- choose node suites for workflow capability
- choose JS-only overlays for editor UX
- choose route-backed tools for explicit control/data access
- choose full hybrids only when you genuinely need runtime state,
  storage, and UI together

## Discovery sources vs implementation sources

Some repositories are useful for discovery but should not be treated as
behavior references:

- `ComfyUI-Workflow/awesome-comfyui`
- `liusida/top-100-comfyui`

They are helpful for seeing which extension families are common and which
projects are active, but they do not define official APIs, upstream runtime
semantics, or required package structure.

## Read Next

- [Extension Patterns](patterns.md)
- [ProfilerX Analysis](profilerx-analysis.md)
