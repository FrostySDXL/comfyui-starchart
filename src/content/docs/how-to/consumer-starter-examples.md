---
title: "Consumer Starter Examples"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-05-20

## Scope

This page points consumer-oriented readers to the small starter examples added in
this repository for artifact and docs discovery work. It does not introduce a
new client-library contract or replace the machine-readable artifact reference.

## Available Starter Examples

### Python: Prompt submit, execution monitoring, and history lookup

Repo path: `examples/consumers/prompt-submit-monitor-history/`

Use this example when you want one higher-level runtime-dependent flow for:

- submitting a workflow to `POST /prompt`
- watching a bounded subset of `GET /ws` execution messages
- correlating on `prompt_id` and `client_id`
- fetching `GET /history/{prompt_id}` after completion or timeout

This example requires a live ComfyUI runtime and the explicit Python
`websocket-client` dependency. It is still a starter pattern, not a supported
SDK contract.

### Python: Manifest-first canonical artifact loading

Repo path: `examples/consumers/python-manifest-reader/`

Use this example when you want the smallest safe Python flow for:

- loading `artifacts/manifest.json`
- resolving one canonical artifact URL from the manifest
- validating checksum metadata before use
- keeping strict parsing on guaranteed fields only

### JavaScript: Optional docs discovery plus manifest-based artifact loading

Repo path: `examples/consumers/javascript-docs-and-artifacts/`

Use this example when you want a small JavaScript-side pattern for:

- reading `artifacts/docs-index.json` as an optional routing aid
- locating likely docs pages for a tooling task
- keeping canonical artifact discovery on `artifacts/manifest.json`

### Shell + jq: Manifest-first endpoint discovery

Repo path: `examples/consumers/shell-jq-artifact-consumer/`

Use this example when you want a minimal shell flow for:

- reading `artifacts/manifest.json`
- resolving `server_endpoints.json`
- listing method and route pairs with `jq`
- optionally probing one standard zero-parameter `GET` route when a live runtime is available

This is the smallest non-Python, non-JavaScript consumer example in the repo.

### Shell: Artifacts plus optional live API interaction

Repo path: `examples/consumers/artifacts-plus-live-api/`

Use this example when you want a bounded two-phase flow for:

- confirming from artifacts that a standard route such as `GET /queue` belongs to the pinned baseline
- separating artifact discovery from live runtime interaction
- keeping the runtime-dependent step explicitly optional

This example intentionally stops short of prompt submission. It uses a simple
live `GET` route so the boundary between pinned artifacts and runtime-only state
stays clear.

## Contract Boundary

Treat all five directories as starter patterns only. They are intentionally
small, self-contained examples. They do not create a supported SDK,
installable client package, or broader productized consumer surface.

Runtime-dependent steps remain optional. The artifact-only portions should still
be readable and useful when no live ComfyUI runtime is available.

For the actual bounded artifact contract, read
[Machine-Readable Artifacts](../reference/machine-readable-artifacts.md).

## Read Next

- [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md)
- [Start Here: Tooling Builder](../start-here/tooling-builder.md)
- [Start Here: Service Integration](../start-here/service-integration.md)
