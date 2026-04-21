# Start Here: Service Integration

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-04-21

## Who This Path Is For

You want to integrate ComfyUI with an external service or tool. This includes:

- embedding ComfyUI in another application
- driving workflows programmatically from a script or service
- using ComfyUI as a generation backend for a frontend application
- building automation around workflow execution

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

### Extension-Backed Integration

Add custom routes or hooks inside ComfyUI to expose internal state or
behavior to external tools.

Key resources:

- [Custom Routes](../how-to/add-custom-routes.md) -- add extension-owned HTTP
  endpoints
- [Server Hooks](../hooks/server-hooks.md) -- react to execution events from
  inside ComfyUI
- ComfyUI-Tooling-Nodes (community pattern) -- reference implementation of
  `/api/etn/...` routes for asset transfer and model inspection

This approach is useful when you need tight integration with ComfyUI internals,
not just remote execution.

## API-First: Quick Reference

### Send a Prompt

```
POST /prompt
{"prompt": {...}, "client_id": "..."}
```

The response gives you a `prompt_id` to track execution.

### Monitor Progress

Connect to the WebSocket at `/ws?client_id=...`. Messages include:

- `executing` -- node execution started
- `progress` -- node progress percentage
- `executing_node` -- which node is running
- `execution_success` -- prompt completed
- `execution_error` -- prompt failed

### Fetch Results

```
GET /history/{prompt_id}
```

Returns complete execution output including generated image paths.

See the API docs for full parameter and response documentation.

## Common Patterns

- **Queue management** -- use `/queue` and `/queue/clear` to control the
  execution queue from an external scheduler
- **Batch processing** -- send multiple prompts sequentially or in parallel;
  use `client_id` to correlate results with requests
- **Model hot-swapping** -- pair API calls with file operations to swap
  models on disk between runs
- **Results polling** -- use `/history` with a retry loop in environments
  that cannot maintain long-lived WebSocket connections

## Constraints

- Custom nodes that depend on direct client-server coordination (shared memory,
  file watches, or non-HTTP IPC) do not work in pure API mode
- Backend validation can differ from what the frontend allows -- prefer
  explicit, narrow interfaces over flexible or wildcard inputs
- API mode does not support frontend hooks -- if your workflow needs
  frontend JS behavior, you cannot fully automate it via the API

## Read Next

- [API Endpoints](../api/endpoints.md)
- [WebSocket](../api/websocket.md)
