---
title: "Start Here: Tooling Builder"
---

**Evidence:** Official docs-backed from docs.comfy.org; Source-backed from pinned snapshots; Operational guidance
**Last Updated:** 2026-05-27
**Baseline verification status:** Citation paths were updated where mechanical drift was obvious, but prose claims in this page have not yet been fully re-reviewed against the current baseline.

## Scope

This page is a start-here route for builders. It helps you choose the right
ComfyUI tooling surface, then points you to the next page. It does not try to
reteach the full API, Manager, or extension architecture.

## Who This Path Is For

Use this path when you are building tools, agents, editors, dashboards, or
external services that need to interact with ComfyUI programmatically.

Common examples:

- automation scripts that submit workflows
- agent or assistant tooling that inspects node capability
- external services that run or monitor prompts
- custom editors, wrappers, or graph-aware tooling

**Prerequisites:** basic HTTP or WebSocket knowledge and comfort reading JSON.

## Choose Your Surface First

Start by deciding where your tool will run and what it needs from ComfyUI.

| Surface | Choose it when | What to watch for |
|---------|----------------|-------------------|
| Local API | You control a self-hosted ComfyUI instance and need direct prompt submission, queue inspection, history lookup, or node discovery | This is the clearest baseline tooling path in this repo. Frontend-only behaviors do not carry over into API mode. |
| Cloud API | You are integrating with the official hosted cloud surface instead of a local instance | Treat cloud behavior as a separate surface. Official docs describe parts of it as experimental, and compatibility endpoints can differ from local behavior. |
| MCP | You want model-assisted tool use through the official ComfyUI MCP server surface | Treat this as a bounded orchestration surface, not a replacement for the local API or published artifacts. Official docs describe it as experimental. |

If your code runs inside ComfyUI rather than outside it, you probably need a
custom node, frontend extension, server hook, or extension-owned route instead
of a pure tooling integration path. Use the retained extension and custom-node
pages when that boundary is still unclear.

## Start with Workflow JSON, Not Transport Details

For most builders, the first stable payload to understand is the workflow
itself.

- Treat **workflow JSON** as the interchange shape that describes the graph.
- Treat **API-format workflow submission** as the transport step that sends that
  graph to a concrete execution surface.
- Keep those ideas separate: workflow JSON tells you what will run, while the
  local API, cloud API, or MCP surface determines how you submit, observe, or
  retrieve results.

This page does not add a new workflow-format tutorial. Read the API and
reference pages next when you need exact request and response details.

## Pick the Right Discovery Surface

Use the most stable input that matches your job.

| Need | Start here | Why |
|------|------------|-----|
| Canonical pinned artifact discovery | [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md) | Start from `manifest.json` when you need version-pinned JSON artifacts and checksum-aware canonical discovery. |
| Live installed-node discovery | [Object Info](../reference/object-info.md) | `GET /object_info` reflects the current instance, including installed custom nodes. |
| Bounded routing support | [Artifact Consumer](artifact-consumer.md) | Use this when you need the shortest retained route for support-index usage and starter-example boundaries. |

Default rule: start from the canonical published artifacts when you need a
stable, pinned baseline. Add runtime capture only when your tool depends on the
installed state of a real instance.

For routing discipline:

- build against pinned artifacts when you need a stable baseline for routes, hooks, or schema-aware tooling
- query live runtime only when runtime-required tasks demand it, such as installed-node inspection or instance-specific validation
- use [Artifact Consumer](artifact-consumer.md) for the compact manifest-first contract and [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md) for the fuller support-artifact boundaries

## Local API Mental Model

For direct local HTTP calls, the practical default base URL is
`http://127.0.0.1:8188` unless your deployment changed it. When you submit JSON
to routes such as `POST /prompt`, send `Content-Type: application/json`.

Use these distinctions consistently:

- **Routes** such as `/prompt`, `/queue`, `/history`, and `/object_info` are the
  main request and polling surface.
- **WebSocket events** on `GET /ws` are the live execution stream for status,
  lifecycle messages, and previews.
- **Polling** with `GET /queue` and `GET /history/{prompt_id}` still matters.
  The WebSocket does not replace every later lookup.
- **Compatibility aliases** under `/api/...` exist in the pinned server, but
  this repo keeps the undecorated route path as the canonical tooling surface.

If you need the subsystem map behind those surfaces, read
[Execution Pipeline](../architecture/execution-pipeline.md) before going deeper
into route-level details.

If your tool needs direct file or image retrieval, read the route details for
`GET /view` and the history pages rather than assuming every output is pushed
through the WebSocket.

## Local API vs Cloud API vs MCP

These surfaces overlap, but they are not interchangeable.

### Local API

Use the local API when you need the clearest direct control over prompt
submission, queue monitoring, execution events, or live `object_info` access on
your own instance.

### Cloud API

Use the cloud API when your integration target is the official hosted service.
Keep the trust boundary explicit: cloud compatibility and result-retrieval flows
should be read from the cloud docs, not assumed from local API behavior.

### MCP

Use MCP when your main goal is tool-mediated interaction through an assistant or
agent workflow. Keep it conceptually separate from direct prompt-submission
integration. It is a higher-level tooling surface with its own limitations and
workflow-handling rules.

## Boundaries That Commonly Confuse Builders

- **Frontend extension behavior is not the same as API behavior.** If a node or
  package depends on frontend hooks, custom widgets, or connected client
  behavior, do not assume that pure API mode can reproduce it.
- **Runtime `object_info` is not the repo's canonical published contract.** Use
  runtime node data as instance-specific enrichment when needed.
- **Cloud and MCP should be treated as separate official surfaces.** Do not use
  this page to flatten them into "just another transport" for every tool.

## References That Matter Most

| Surface | Read next | Use for |
|---------|-----------|---------|
| Pinned JSON contract | [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md) | Manifest-first discovery and bounded consumer guarantees |
| Local routes | [API Endpoints](../api/endpoints.md) | Prompt submission, queue, history, file/view, and route semantics |
| Live events | [WebSocket](../api/websocket.md) | Progress, lifecycle messages, and preview delivery |
| Live node discovery | [Object Info](../reference/object-info.md) | Installed-node capability inspection |
| Shortest artifact-consumer route | [Artifact Consumer](artifact-consumer.md) | Support-index orientation and starter-example boundary |
| Execution model | [Execution Pipeline](../architecture/execution-pipeline.md) | Queueing, validation, and live-event responsibilities |

## Starter Examples

Use these bounded starter patterns when you want concrete consumer-side examples:

- `examples/consumers/prompt-submit-monitor-history/`
- `examples/consumers/python-manifest-reader/`
- `examples/consumers/javascript-docs-and-artifacts/`
- `examples/consumers/shell-jq-artifact-consumer/`
- `examples/consumers/artifacts-plus-live-api/`

These examples are starter patterns, not a supported SDK surface.

## When to Switch to Repo-Local Workflow Docs

Stay in the published docs path unless you are contributing to this repository.
If you start editing docs, scripts, or generated artifacts, switch to the
repo-local maintainer workflow in `CONTRIBUTING.md`.

## Read Next

- [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md)
- [Artifact Consumer](artifact-consumer.md)
- [Execution Pipeline](../architecture/execution-pipeline.md)
- [API Endpoints](../api/endpoints.md)
- [WebSocket](../api/websocket.md)
- [Object Info](../reference/object-info.md)
