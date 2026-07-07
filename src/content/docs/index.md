---
title: "ComfyUI StarChart"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-06-26

## Scope

ComfyUI StarChart is a version-pinned, source-extracted companion reference for
ComfyUI developers. It publishes:

- a self-hostable Astro Starlight documentation site
- extracted JSON artifacts for selected ComfyUI API, hook, and schema surfaces
- repo-local maintainer tooling for refresh, verification, and publication

Use [docs.comfy.org](https://docs.comfy.org/) for the official human reference.
Use [Machine-Readable Artifacts](reference/machine-readable-artifacts.md) when
you need this repo's pinned JSON artifact contract.

## Fast Paths

Choose the shortest route for the job you need to finish:

| I want to... | Start here |
|--------------|------------|
| Load pinned ComfyUI routes, hooks, schemas, or WebSocket events as JSON | [Artifact Consumer](start-here/artifact-consumer.md) |
| Build an agent, integration, dashboard, or CI check against ComfyUI facts | [Tooling Builder](start-here/tooling-builder.md) |
| Submit, monitor, or retrieve work through a local ComfyUI API | [Local API Integration](start-here/service-integration.md) |
| Build a custom node with source-backed constraints | [Custom Node Author](start-here/author.md) |
| Extend ComfyUI through frontend or server hooks | [Extension Developer](start-here/extension-developer.md) |

If you only need the machine-readable entrypoint, start with
`artifacts/manifest.json`. It points to the canonical current and versioned
artifact copies, schemas, source metadata, and checksums.

## What You Can Use Immediately

- `artifacts/manifest.json` for canonical artifact discovery
- `artifacts/current/server_endpoints.json` for pinned local API routes
- `artifacts/current/js_hooks.json` for pinned frontend hook names
- `artifacts/current/node_api_schema.json` for pinned node schema surfaces
- `artifacts/current/websocket_events.json` for pinned live-event names
- `artifacts/docs-index.json` for bounded docs routing when an agent or tool
  needs a first page to read

If you are maintaining this repo rather than consuming it, switch to
`CONTRIBUTING.md` and `AGENTS.md` for repo-local workflow guidance.

## Retained Surface

The retained published surface stays intentionally small:

- **Start Here** for audience routing
- **Machine-Readable Reference** for artifacts, version pins, schemas, and live
  object-info boundaries
- **API** for route, prompt, queue, history, and WebSocket reference
- **Workflow and Architecture** for workflow JSON and execution-system context
- **Hooks** for frontend and server extension surfaces
- **Custom Nodes** for authoring guidance
- **Repository Policy** for evidence rules and editorial boundaries
- **Advanced** for durable secondary topics

## Artifact Entry Rule

When you need machine-readable inputs:

- use `artifacts/manifest.json` first for canonical artifact discovery
- use [Machine-Readable Artifacts](reference/machine-readable-artifacts.md) for
  contract interpretation
- use [Artifact Consumer](start-here/artifact-consumer.md) for the shortest
  consumer route through the retained surface

## StarChart vs Official Docs

Use the official docs when you need native human-facing product guidance,
current official workflows, or hosted-surface documentation from
[docs.comfy.org](https://docs.comfy.org/).

Use StarChart when you need pinned source-backed artifacts, retained cross-surface
reference pages, or bounded tooling guidance tied to this repo's current baseline.

Use both when you need to reconcile the current official guidance with the pinned
artifact and snapshot context this repo preserves.

## Scope Boundaries

- This site is a bounded, pinned companion reference.
- It is not the official docs.
- It is not a full maintainer handbook.
- It intentionally avoids republishing low-value routing, troubleshooting, and
  tutorial sprawl.

## Read Next

- [Start Here: Artifact Consumer](start-here/artifact-consumer.md)
- [Start Here: Tooling Builder](start-here/tooling-builder.md)
- [Start Here: Local API Integration](start-here/service-integration.md)
- [Machine-Readable Artifacts](reference/machine-readable-artifacts.md)
