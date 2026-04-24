# ComfyUI Knowledge Base

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-04-21

## Scope

This documentation section covers ComfyUI development topics including API
endpoints, extension hooks, custom node authoring, and extension architecture.
It is a source-backed reference, not the official ComfyUI documentation.
See `docs.comfy.org` for official docs.

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

ComfyUI core `v0.19.3` and official frontend `v1.42.11`. Content written
against other versions should note the version it applies to.

## Read Next

- [Start Here: Custom Node Author](start-here/author.md)
- [Start Here: Extension Developer](start-here/extension-developer.md)
- [Start Here: Service Integration](start-here/service-integration.md)
- [Source Evidence Policy](reference/source-evidence-policy.md)
