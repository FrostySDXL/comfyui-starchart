---
title: "ComfyUI StarChart"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-05-24

## Scope

This documentation section is the reduced published surface for ComfyUI
builders. It keeps the durable reference pages, start-here routes, and artifact
consumer guidance that remain useful after the surface reset.

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
