---
title: "Glossary"
---

**Evidence:** Official docs-backed from docs.comfy.org; Operational guidance for repo-local artifact terms
**Last Updated:** 2026-05-18

## Scope

This glossary defines repeated repository and artifact terms that appear across
the docs. It is an orientation aid, not a tutorial or a second reference set.

## Terms

### Workflow JSON / API format

The JSON representation of a ComfyUI workflow graph as used for programmatic
submission and interchange. In this docs set, the term is kept narrow: it names
the graph payload shape, not every transport or monitoring step around it.

### API mode

An integration mode that uses ComfyUI's HTTP and WebSocket surfaces without
loading the browser editor or its frontend extension registration path.

### Local API

The direct API surface exposed by a self-hosted ComfyUI instance, including
routes such as `/prompt`, `/queue`, `/history`, `/object_info`, and the `GET
/ws` WebSocket stream.

### Cloud API

The official hosted ComfyUI API surface. Treat it as a separate integration
surface rather than as a guaranteed drop-in synonym for local-instance behavior.

### Custom node

A ComfyUI extension that adds graph-executable capability. Custom nodes mainly
extend the server-side execution model, even when a package also ships frontend
behavior.

### Custom datatype

An author-defined uppercase type name used to pass extension-specific Python
objects or structured values between related nodes.

### Client ID

An optional identifier submitted with `POST /prompt` that tells the server which
WebSocket client should receive targeted execution messages for that prompt.

### Execution model inversion

The shift from older back-to-front recursive execution assumptions toward a
front-to-back topological execution model with more visible validation and lazy
evaluation behavior.

### Frontend extension

An editor-side extension that changes UI behavior, widgets, panels, or graph
interaction in the browser client.

### Manager

The official ComfyUI package-management surface for supported install, update,
and uninstall flows. In this docs set, Manager guidance stays separate from the
local API and runtime-automation surfaces.

### Registry publisher

The identity or account that publishes a custom node package into the official
registry-backed distribution flow.

### Pinned snapshot

A checked-in copy of upstream ComfyUI source stored under
`references/snapshots/`. The repo uses pinned snapshots to make extracted docs
and artifacts reproducible.

### Source-backed

A label used when a behavior claim is derived from official ComfyUI docs or a
pinned upstream source citation. See the
[Source Evidence Policy](source-evidence-policy.md).

### Operational guidance

A label used for repo-local process, maintenance, and workflow pages. It does
not raise the trust level of a ComfyUI behavior claim.

### Canonical raw artifact

A repo-local JSON output under `references/raw/` that acts as the canonical
extractor result before publication to `public/artifacts/`.

### Extracted artifact

A JSON file produced by an extractor script from pinned source snapshots.
Examples include `server_endpoints.json`, `js_hooks.json`, and
`node_api_schema.json`.

### Published artifact

A checked-in JSON file served from `public/artifacts/` as part of the built site.
Published artifacts mirror the bounded web-consumption surface.

### Artifact schema version

The version of this repo's bounded published artifact contract. It is separate
from the upstream ComfyUI version pin.

### Version key

The deterministic identifier used for versioned published artifact copies under
`public/artifacts/versions/<key>/`.

### Hidden input

A server-provided value injected into node execution without an explicit graph
link, such as prompt metadata, node identity, or extra PNG info.

### Partial execution

A prompt-submission option that narrows execution to selected output targets
instead of running every reachable output node in the graph.

### Prompt ID

The identifier returned by `POST /prompt` and used to track one queued workflow
through WebSocket events, queue/history lookups, and stored results.

### Route alias

A compatibility route automatically mirrored under `/api/...` for a non-static
server route that also exists at its original undecorated path.

### Session ID (sid)

The connection-scoped identifier assigned by the WebSocket server to a socket,
distinct from the `client_id` attached to prompt submission.

### V1 node

A legacy custom-node pattern based on class attributes such as `INPUT_TYPES`,
`RETURN_TYPES`, and `FUNCTION`, usually registered through
`NODE_CLASS_MAPPINGS`.

### V3 node

A newer custom-node pattern based on `io.Schema`, `execute()`, and structured
registration through a ComfyUI extension entrypoint.

### WebSocket lifecycle event

One of the JSON messages sent through `GET /ws` to report execution state, such
as `execution_start`, `executing`, `execution_cached`, `execution_success`, or
`execution_error`.

### Wildcard input

An input declared with a broad type such as `*`, usually requiring explicit
validation discipline because the backend accepts many possible linked values.

## Read Next

- [Machine-Readable Artifacts](machine-readable-artifacts.md)
- [Source Evidence Policy](source-evidence-policy.md)
- [What's New](../whats-new/index.md)
