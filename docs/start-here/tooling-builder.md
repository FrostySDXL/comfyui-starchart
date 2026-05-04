# Start Here: Tooling Builder

**Evidence:** Operational guidance
**Last Updated:** 2026-05-03

## Who This Path Is For

You are building tools, agents, or external services that interact with ComfyUI
programmatically. This includes:

- automation scripts that submit workflows
- IDE plugins or graph editors
- monitoring or profiling dashboards
- agents that discover or invoke nodes

**Prerequisites:** basic HTTP/WebSocket knowledge and familiarity with JSON.

## First Practical Step

Read [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md),
fetch `artifacts/manifest.json`, and inspect the three canonical published JSON
artifacts. Use `artifacts/docs-index.json` only when you need a bounded page
discovery layer for routing a tool or agent to the right docs page before
reading prose in full. If your tool later needs installed custom-node state, add
the runtime-only `object_info` capture path from
[Runtime and CI Operations](../reference/runtime-ci-operations.md).

## References That Matter Most

| Artifact | Location | Use for |
|----------|----------|---------|
| Canonical published artifacts | [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md) | Start with the published JSON contract, manifest, and bounded guarantees |
| Docs index support artifact | `artifacts/docs-index.json` | Route a tool or agent to likely relevant docs pages without full-site scraping |
| HTTP API routes | [`docs/api/endpoints.md`](../api/endpoints.md) | Submit prompts, poll history, manage queue |
| WebSocket events | [`docs/api/websocket.md`](../api/websocket.md) | Real-time execution progress and completion |
| Node schema reference | [Object Info](../reference/object-info.md) | Understand source-backed node metadata and optional runtime enrichment |
| Runtime-only capture | [Runtime and CI Operations](../reference/runtime-ci-operations.md) | Use `object_info_runtime.json` only for live-instance or hybrid workflows |
| Server hooks | [`docs/hooks/server-hooks.md`](../hooks/server-hooks.md) | Understand server-side extension points |
| JavaScript hooks | [`docs/hooks/javascript-hooks.md`](../hooks/javascript-hooks.md) | Understand frontend extension points |
| Worked examples | `examples/` | Concrete API calls and extension patterns |

## Standard API vs Extension Routes

- **Standard API** (`/prompt`, `/history`, `/queue`, `/object_info`) requires no
  server modifications and is documented in this repo's API reference. Use this
  for remote automation.
- **Extension routes** (`/api/etn/...` or custom routes) require a corresponding
  extension installed inside ComfyUI. Use this only when you need runtime state
  the standard API does not expose.

If you are unsure which you need, start with the standard API and move to
extension routes only after confirming the data you need is unavailable.

## Machine-Readable vs Prose-Only Artifacts

- **Machine-readable:** the three canonical published JSON artifacts documented in
  [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md), the
  bounded `docs-index.json` support artifact for page discovery, the repo-local
  copies under `references/raw/`, snapshot files under
  `references/snapshots/`, code in `examples/`, and API endpoint documentation.
- **Prose-only:** decision guides, tutorials, deep dives, and community pattern
  studies. These explain intent and tradeoffs but are not structured for parsing.

Build tooling against the canonical published artifacts first. Use
`docs-index.json` only as a lightweight routing aid into the prose docs. Move to
runtime capture only when your tool depends on the live installed-node state of
a real ComfyUI instance. Use prose pages for context and design decisions.

## When to Switch to Repo-Local Workflow Docs

Stay in the published docs path unless you are contributing changes to this
repository. If you begin editing repo docs, published artifacts, or scripts,
switch to the repo's `CONTRIBUTING.md` file for maintainer-grade workflow
guidance.

## Read Next

- [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md)
- [API Endpoints](../api/endpoints.md)
- [WebSocket Events](../api/websocket.md)
- [Object Info](../reference/object-info.md)
- [Runtime and CI Operations](../reference/runtime-ci-operations.md)
- [Decision Tree: API Integration](../decision-trees/api-integration.md)

If you want section-level routing before diving into reference pages, use the
[API Section Guide](../api/index.md), [Hooks Section Guide](../hooks/index.md),
and [Troubleshooting](../troubleshooting/index.md).
