# ComfyUI Knowledge Base

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-04-30

## Scope

This documentation section covers ComfyUI development topics including API
endpoints, extension hooks, custom node authoring, and extension architecture.
It is a source-backed, version-pinned reference, not the official ComfyUI
documentation. See [docs.comfy.org](https://docs.comfy.org/) for official docs.

The repository also publishes machine-readable JSON artifacts extracted from
pinned upstream snapshots. See [Machine-Readable Artifacts](reference/machine-readable-artifacts.md)
for a catalog of available artifacts, stable URLs, and consumption guidance.

## Who This Section Is For

Choose your starting point based on what you are building:

| Goal | Start Here |
|------|-----------|
| Build custom nodes | [Custom Node Author](start-here/author.md) |
| Extend ComfyUI (frontend or server) | [Extension Developer](start-here/extension-developer.md) |
| Integrate ComfyUI into an external service | [Service Integration](start-here/service-integration.md) |
| Contribute documentation | [Docs Contributor](start-here/docs-contributor.md) |
| Build tools or agents against ComfyUI | [Tooling Builder](start-here/tooling-builder.md) |

## Page Structure

This documentation is organized as follows:

- **API Reference** (`api/`) -- HTTP endpoints, WebSocket events, prompt
  submission, queue, and history semantics
- **Hooks** (`hooks/`) -- JavaScript hooks, server hooks, and extension points
- **Custom Nodes** (`custom-nodes/`) -- V3-oriented node authoring, registration,
  datatypes, and best practices
- **Extensions** (`extensions/`) -- Extension architecture patterns and analysis
- **Reference** (`reference/`) -- Evidence policy, writing style guide, and
  machine-readable summaries
- **Tutorials** (`tutorials/`) -- Task-oriented guides that combine multiple
  concepts
- **How-To** (`how-to/`) -- Focused operational recipes
- **Start Here** (`start-here/`) -- Audience-specific reading paths
- **Decision Trees** (`decision-trees/`) -- Tradeoff guides for architectural choices
- **Ecosystem** (`ecosystem/`) -- Community tools and patterns
- **Deep Dives** (`deep-dives/`) -- Detailed analysis of specific tools

## Evidence Policy

Content in this repo distinguishes:

- **official ComfyUI behavior** -- stated in `docs.comfy.org`
- **upstream source behavior** -- from cited ComfyUI source files for a specific
  version or commit
- **community pattern** -- from external repositories, labeled as such

See [Source Evidence Policy](reference/source-evidence-policy.md) for the
full labeling rules.

## Current Version Pin

ComfyUI core `v0.20.1` and official frontend `v1.44.13`. Content written
against other versions should note the version it applies to.

## Scope Boundaries

- [docs.comfy.org](https://docs.comfy.org/) is the official human reference for ComfyUI.
- This repo is a pinned, machine-readable companion for developers and tooling authors.
- For end-user tutorials and workflow guides, see community resources such as
  [comfyui-wiki.com](https://comfyui-wiki.com/).

## Read Next

- [Start Here: Custom Node Author](start-here/author.md)
- [Start Here: Extension Developer](start-here/extension-developer.md)
- [Start Here: Service Integration](start-here/service-integration.md)
- [Source Evidence Policy](reference/source-evidence-policy.md)
