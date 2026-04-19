# Extension Patterns

**Last Updated:** 2026-04-19
**Primary Source:** https://docs.comfy.org/custom-nodes/js/javascript_hooks

## Primary Sources

- https://docs.comfy.org/custom-nodes/js/javascript_hooks
- https://docs.comfy.org/development/comfyui-server/comms_routes
- https://docs.comfy.org/development/comfyui-server/comms_messages
- https://docs.comfy.org/custom-nodes/overview

## Overview

Most ComfyUI extensions fall into a few repeatable architectural
patterns. The exact choice depends on where the behavior lives:

- frontend-only UI changes
- backend-only execution logic
- route-backed tools
- hybrid monitoring or panel extensions

The cleanest extensions keep each concern in its native layer instead of
forcing everything through one mechanism.

## Frontend vs Server Tradeoffs

### Frontend hooks

Use JavaScript hooks when you need to change how the editor behaves or
looks:

- `beforeRegisterNodeDef` for node-type-wide behavior
- `nodeCreated` for per-instance behavior
- `setup` for menus, listeners, and global UI integration

Strengths:

- direct UI control
- no extra HTTP routes required
- integrates naturally with existing Comfy client lifecycle

Costs:

- frontend-only behavior is not visible to API-mode clients
- monkey-patching beyond official hooks is fragile

### Backend nodes and routes

Use backend nodes when you need new graph-executable functionality. Use
custom routes when the frontend or external tooling needs an explicit
request/response API.

Strengths:

- clearer contracts
- reusable by workflows and scripts
- easier to keep deterministic than UI patches

Costs:

- extra route surfaces become public compatibility contracts
- pure routes do not help with editor UX unless paired with frontend code

### Hybrid extensions

Hybrid extensions combine:

- frontend hooks or panels
- backend routes or execution hooks
- message/event listening

This is the right pattern for profiling dashboards, custom control
panels, live inspectors, and tools that need both runtime data and UI.

## Composition Patterns

### 1. Node pack only

Adds one or more execution nodes, often with little or no custom JS.
This is the simplest and most stable extension family.

### 2. UI augmentation only

Adds menu items, widgets, graph conveniences, or display tweaks without
introducing new server execution behavior.

### 3. Route-backed panel

Adds a frontend panel plus one or more backend routes to fetch or mutate
state. Good for dashboards, management tools, and inspectors.

### 4. Runtime monitoring extension

Listens to built-in execution messages like `executing`, `progress`, and
`execution_success`, then combines them with server-side metrics or
history APIs. ProfilerX is the clearest example of this family.

### 5. Client/server hybrid node package

Adds custom nodes, frontend JS, and sometimes custom routes. This is the
most powerful pattern, but also the easiest to make brittle if UI and
backend assumptions drift.

## Practical guidance

- start with the narrowest architecture that solves the problem
- prefer official hooks over prototype hijacking
- prefer explicit routes over hidden side channels when frontend code
  needs server state
- treat hybrid extensions as real software systems, not quick patches
