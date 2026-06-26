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

## Who This Section Is For

Choose your starting point based on what you are building:

| Goal | Start Here |
|------|-----------|
| Build custom nodes | [Custom Node Author](start-here/author.md) |
| Extend ComfyUI (frontend or server) | [Extension Developer](start-here/extension-developer.md) |
| Integrate ComfyUI into an external service | [Service Integration](start-here/service-integration.md) |
| Build tools or agents against ComfyUI | [Tooling Builder](start-here/tooling-builder.md) |
| Consume published artifacts directly | [Artifact Consumer](start-here/artifact-consumer.md) |

If you are maintaining this repo rather than consuming it, switch to
`CONTRIBUTING.md` and `AGENTS.md` for repo-local workflow guidance.

## Retained Surface

The retained published surface stays intentionally small:

- **Start Here** for audience routing
- **Architecture** for system-shape context
- **API** for route, prompt, queue, history, and WebSocket reference
- **Hooks** for frontend and server extension surfaces
- **Custom Nodes** for authoring guidance
- **Reference** for artifacts, evidence rules, and editorial boundaries
- **Deep Dives** for a few durable advanced topics

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

- [Start Here: Custom Node Author](start-here/author.md)
- [Start Here: Extension Developer](start-here/extension-developer.md)
- [Start Here: Service Integration](start-here/service-integration.md)
- [Start Here: Tooling Builder](start-here/tooling-builder.md)
- [Start Here: Artifact Consumer](start-here/artifact-consumer.md)
- [Machine-Readable Artifacts](reference/machine-readable-artifacts.md)
- [Source Evidence Policy](reference/source-evidence-policy.md)
