# Common Architectures

**Last Updated:** 2026-04-19
**Primary Source:** community extension repositories

## Primary Sources

- current ProfilerX rewrite: https://github.com/ryanontheinside/ComfyUI_ProfilerX
- https://docs.comfy.org/custom-nodes/overview
- https://docs.comfy.org/custom-nodes/js/javascript_hooks
- https://docs.comfy.org/development/comfyui-server/comms_routes

## Overview

Across ComfyUI extensions, a few architecture families keep recurring.
They differ mainly in how much they depend on the graph, the frontend,
and custom server state.

## Architecture Families

### Node suites

These packages primarily add many nodes under one namespace or category.
They are execution-centric and usually have the lowest maintenance risk.

Typical shape:

- Python node definitions
- registration layer
- little or no custom UI

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

### Metrics and monitoring dashboards

Profiler-style tools combine several layers:

- runtime event observation
- metrics collection in Python
- persistence/history storage
- frontend dashboard components

The current `ComfyUI_ProfilerX` rewrite is a strong example. Its repo
tree shows:

- Python backend files such as `handler.py`, `metrics.py`, `routes.py`,
  `storage.py`, and `profiler_core.py`
- frontend UI under `web/` with views, tabs, tables, and monitor/popup
  modules
- explicit REST endpoints for stats and archive management

### Full hybrid products

These combine nodes, frontend UI, routes, storage, and monitoring into a
larger product-style extension. They are powerful but need stronger
version discipline and clearer contracts.

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
