---
title: "Start Here: Service Integration"
---

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-05-27
**Primary Sources:** `references/snapshots/2026-06-01/comfyui-core-v0.23.0/server.py`, `references/snapshots/2026-06-01/comfyui-core-v0.23.0/execution.py`
**Baseline verification status:** Citation paths were updated where mechanical drift was obvious, but prose claims in this page have not yet been fully re-reviewed against the current baseline.

## Who This Path Is For

You want to integrate ComfyUI with an external service or tool. This includes:

- embedding ComfyUI in another application
- driving workflows programmatically from a script or service
- using ComfyUI as a generation backend for a frontend application
- building automation around workflow execution

**Prerequisites:** basic HTTP/WebSocket knowledge and a running ComfyUI instance.

## First Practical Step

Make a `POST /prompt` call to your ComfyUI instance with a minimal prompt
dictionary and your `client_id`. Inspect the `prompt_id` in the response to
confirm the queue accepted your request. This confirms the API integration
surface is reachable.

## Two Integration Surfaces

### API-First Integration

ComfyUI exposes a full HTTP API and WebSocket interface. This is the
recommended path for service integration.

Key resources:

- [API Endpoints](../api/endpoints.md) -- complete route list with parameter
  documentation
- [WebSocket](../api/websocket.md) -- event stream for execution progress,
  completion, and errors
- [Prompt Submission](../api/prompt-submission.md) -- how to construct and send
  a prompt to the execution engine
- [History and Queue](../api/history-queue.md) -- poll or watch execution history
  and queue state

This approach treats ComfyUI as a remote generation service without
modifying its internals.

If you need the system map behind that flow before reading route details, start
with [Execution Pipeline](../architecture/execution-pipeline.md).

### Extension-Backed Integration

Add custom routes or hooks inside ComfyUI to expose internal state or
behavior to external tools.

Key resources:

- [Server Hooks](../hooks/server-hooks.md) -- react to execution events from
  inside ComfyUI
- [Extension Points](../hooks/extension-points.md) -- decide when a custom route
  is more truthful than a callback or pure API polling
- [API Endpoints](../api/endpoints.md) -- baseline routes to compare against any
  extension-owned endpoint

This approach is useful when you need tight integration with ComfyUI internals,
not just remote execution.

## API-First: Quick Reference

### Send a Prompt

```
POST /prompt
{"prompt": {...}, "client_id": "..."}
```

The response gives you a `prompt_id` to track execution.

### Monitor Execution Events (quick-reference subset)

Connect to the WebSocket at `/ws?client_id=...`. Messages include:

- `status` -- queue status snapshot sent on connect and broader queue updates
- `executing` -- node execution started for the prompt client
- `executed` -- node UI output emitted for the prompt client
- `execution_success` -- prompt completed
- `execution_error` -- prompt failed

This is a bounded quick-reference subset, not the full canonical event
inventory. Use [WebSocket](../api/websocket.md) for the retained event reference
and preview-channel details.

### Fetch Results

```
GET /history/{prompt_id}
```

Returns complete execution output including generated image paths.

See the API docs for full parameter and response documentation.

## Common Patterns

- **Queue management** -- use `GET /queue` to inspect queue state and `POST /queue`
  with `{"clear": true}` to clear pending queue items from an external scheduler
- **Batch processing** -- send multiple prompts sequentially or in parallel;
  use `client_id` to correlate results with requests
- **Model hot-swapping** -- pair API calls with file operations to swap
  models on disk between runs
- **Results polling** -- use `/history` with a retry loop in environments
  that cannot maintain long-lived WebSocket connections

## Constraints

Keep these boundaries explicit:

- local API behavior is not the same as frontend-only behavior
- custom routes are extension surfaces, not native API routes
- runtime-specific node state belongs to live `object_info`, not to the pinned
  canonical artifact contract

If your service also needs the repo's pinned artifact baseline for route,
hook, or schema-aware validation, start with
[Machine-Readable Artifacts](../reference/machine-readable-artifacts.md) and
[Artifact Consumer](artifact-consumer.md).

## When to Switch to Repo-Local Workflow Docs

Stay in the published docs path unless you are contributing changes to this
repository. If you begin editing repo docs, examples, or scripts, switch to the
repo's `CONTRIBUTING.md` file for workflow and verification guidance.

## Read Next

- [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md) -- canonical published artifact contract and support-artifact boundaries
- [Artifact Consumer](artifact-consumer.md) -- shortest retained route for manifest-first artifact use
- [Execution Pipeline](../architecture/execution-pipeline.md) -- execution-system map behind prompt validation, queueing, and history
- [API Endpoints](../api/endpoints.md) -- complete route reference
- [WebSocket](../api/websocket.md) -- event stream details
- [Prompt Submission](../api/prompt-submission.md) -- constructing prompts
- [History and Queue](../api/history-queue.md) -- polling and stored outputs
