---
title: "ProfilerX Analysis"
---

**Evidence:** Community pattern study based on pinned external version
**Last Updated:** 2026-05-05
**Primary Source:** https://github.com/ryanontheinside/ComfyUI_ProfilerX

## Primary Sources

- https://github.com/ryanontheinside/ComfyUI_ProfilerX (community pattern example)
- ProfilerX `README.md`, `__init__.py`, `handler.py`, `routes.py`, `web/index.ts` (community repo)
- `references/snapshots/2026-04-30/comfyui-core-v0.20.1/server.py` (v0.20.1, commit 64b8457f55cd7fb54ca7a956d9c73b505e903e0c) -- upstream source for ComfyUI progress handler and route patterns
- `references/snapshots/2026-04-30/comfyui-core-v0.20.1/execution.py` (v0.20.1, commit 64b8457f55cd7fb54ca7a956d9c73b505e903e0c) -- upstream source for handler registration during execution
- `references/snapshots/2026-04-19/comfyui-core-v0.19.3/comfy_execution/progress.py` (v0.19.3, commit 308602640) -- intentionally retained for the `ProgressHandler` callback contract because the current pinned v0.20.1 snapshot set does not include an equivalent `comfy_execution/progress.py` path

## Scope

This page is a community extension case study, not a description of
native ComfyUI behavior.

ProfilerX is a high-value reference because it shows a full hybrid extension,
not just a single hook:

- runtime instrumentation in Python
- persisted profiling history
- route-backed JSON APIs
- a frontend panel registered into the ComfyUI UI

Its current upstream structure is also instructive for another reason: the repo
contains both the newer `ProgressHandler`-based path and older patch-heavy
files. The active registration path in `__init__.py` uses
`comfy_execution.progress`, re-injects its handler when ComfyUI resets progress
state, and registers web assets plus HTTP routes. That makes it a good example
of using a supported runtime hook while still acknowledging practical lifecycle
friction inside ComfyUI.

## Metrics Collection Model

The current source-backed flow is:

1. `__init__.py` creates storage and a `ProfilerXProgressHandler`
2. it patches `progress.reset_progress_state` so the handler gets re-added for
   each execution
3. `handler.py` receives `start_handler` and `finish_handler` callbacks per
   node
4. memory snapshots and peak tracking are collected around node execution
5. cache hits are inferred when `finish_handler` fires without a matching
   `start_handler`
6. completed run data is persisted through storage and exposed via routes
7. `web/index.ts` registers a frontend extension, adds a menu UI, and refreshes
   tabs when executions complete

The HTTP surface in `routes.py` is intentionally small:

- `GET /profilerx/stats`
- `GET /profilerx/archives`
- `POST /profilerx/archive`
- `POST /profilerx/archive/{filename}/load`
- `DELETE /profilerx/archive/{filename}`

One subtle but useful pattern: the stats route flushes in-progress handler data
before returning JSON, so the UI reads a coherent snapshot instead of stale
partially buffered state.

There is also visible source drift in the repository:

- `prestartup.py`, `server.py`, and `profiler_core.py` still show an older,
  more invasive monkey-patch design around `execution.*`
- `__init__.py` and `handler.py` show the newer `ProgressHandler` design

For documentation purposes, the newer registration path is the better reference,
but extension authors should note that upstream repos can contain legacy code
during transitions.

## Lessons for Extension Authors

Reusable patterns:

- prefer supported progress/event APIs before patching deep executor internals
- separate collection, storage, routes, and UI into distinct modules
- keep the REST contract narrow and JSON-first
- infer cache behavior from actual runtime signals instead of guessing from UI
- refresh frontend views from explicit execution events rather than polling only

Caveats:

- if ComfyUI resets handler registries between runs, your extension may need a
  re-registration step just like ProfilerX
- avoid copying legacy monkey-patch files blindly when the active upstream path
  has already moved to a safer hook
- route-backed dashboards become compatibility surfaces; version them mentally
  like public APIs
- profiling extensions should minimize overhead and keep disk writes batched or
  deferred where possible

## Read Next

- [Adding Background Metrics](../tutorials/adding-background-metrics.md)
- [Extension Patterns](patterns.md)
