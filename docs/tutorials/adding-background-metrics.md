# Adding Background Metrics

**Evidence:** Official docs-backed from docs.comfy.org; Community pattern study based on pinned external version
**Last Updated:** 2026-05-05
**Primary Source:** https://docs.comfy.org/development/comfyui-server/comms_messages

## Primary Sources

- https://github.com/ryanontheinside/ComfyUI_ProfilerX (community pattern example)
- https://docs.comfy.org/development/comfyui-server/comms_messages
- https://docs.comfy.org/development/comfyui-server/comms_routes
- `references/snapshots/2026-04-30/comfyui-core-v0.20.1/server.py` (v0.20.1, commit 64b8457f55cd7fb54ca7a956d9c73b505e903e0c) -- upstream source for built-in routes and message patterns
- `references/snapshots/2026-04-30/comfyui-core-v0.20.1/execution.py` (v0.20.1, commit 64b8457f55cd7fb54ca7a956d9c73b505e903e0c) -- upstream source for progress-handler registration during execution
- `references/snapshots/2026-04-19/comfyui-core-v0.19.3/comfy_execution/progress.py` (v0.19.3, commit 308602640) -- intentionally retained for the `ProgressHandler` callback contract because the current pinned v0.20.1 snapshot set does not include an equivalent `comfy_execution/progress.py` path

## Scope

Background workflow metrics are best implemented as a hybrid extension:

- collect timing and memory data in Python during execution
- persist summaries for later analysis
- expose stats through routes or messages
- render them in a lightweight frontend panel

Official Comfy docs and upstream runtime surfaces stay primary here.
ProfilerX is used as a community pattern example for how one active
extension implements those ideas in practice.

The current ProfilerX rewrite is especially useful as a reference because
its active registration path uses ComfyUI's pinned `ProgressHandler` API and
re-registers its handler when ComfyUI resets progress state for a new run.

## Hook Strategy

ProfilerX's documented strategy is a good model:

- attach a handler through the pinned `ProgressHandler` path
- re-inject the handler when the progress registry resets
- measure per-node timing in start/finish callbacks
- record RAM and VRAM usage during execution
- infer cache hits when finish events occur without matching starts
- aggregate statistics across runs

In the pinned upstream source, the core callback shape is explicit:

- `start_handler(node_id, state, prompt_id)`
- `finish_handler(node_id, state, prompt_id)`

If an extension needs `class_type` or display-node metadata, it has to derive
that from the registry or prompt graph rather than expecting extra callback
arguments.

That design is better than patching random executor internals because it
tracks runtime behavior through a supported instrumentation surface.

One caveat from the upstream repo: older patch-heavy files still exist beside
the newer handler-based path. When borrowing patterns, follow the active
registration flow, not every historical implementation file in the repository.

For a simpler implementation, combine:

- built-in execution messages like `executing`, `progress`, and
  `execution_success`
- `client_id`-targeted monitoring when a UI session is active
- `/history/{prompt_id}` for post-run lookup

## API Exposure

ProfilerX's README lists a clean REST surface:

- `GET /profilerx/stats`
- `GET /profilerx/archives`
- `POST /profilerx/archive`
- `POST /profilerx/archive/{filename}/load`
- `DELETE /profilerx/archive/{filename}`

That is a good example of how to expose metrics cleanly:

- one route for current stats
- dedicated archive/history management routes
- frontend polling or refresh against a stable JSON API

## Recommended architecture

If you are building a smaller metrics extension, use this layering:

1. Python metrics collector
2. execution hook or progress handler integration
3. optional persistence layer for history
4. one or two read-focused routes
5. frontend panel that reads the API and listens for built-in events

## Practical notes

- prefer official progress and message APIs over monkey-patching
- keep the metrics API read-heavy and simple
- store historical data in one well-defined local file or archive format
- separate collection, storage, and UI code so each layer can evolve

## Read Next

- [ProfilerX Analysis](../extensions/profilerx-analysis.md)
- [Monitor Execution](../how-to/monitor-execution.md)
- [Server Hooks](../hooks/server-hooks.md)
