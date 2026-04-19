# Adding Background Metrics

**Last Updated:** 2026-04-19
**Primary Source:** https://github.com/ryanontheinside/ComfyUI_ProfilerX

## Primary Sources

- https://github.com/ryanontheinside/ComfyUI_ProfilerX
- https://docs.comfy.org/development/comfyui-server/comms_messages
- https://docs.comfy.org/development/comfyui-server/comms_routes

## Overview

Background workflow metrics are best implemented as a hybrid extension:

- collect timing and memory data in Python during execution
- persist summaries for later analysis
- expose stats through routes or messages
- render them in a lightweight frontend panel

The current ProfilerX rewrite is especially useful as a reference because
its README explicitly says it moved away from monkey-patching and now
uses ComfyUI's official `ProgressHandler` API.

## Hook Strategy

ProfilerX's documented strategy is a good model:

- attach a handler through the official `ProgressHandler` path
- measure per-node timing in start/finish callbacks
- record RAM and VRAM usage during execution
- infer cache hits when finish events occur without matching starts
- aggregate statistics across runs

That design is better than patching random executor internals because it
tracks runtime behavior through a supported instrumentation surface.

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
