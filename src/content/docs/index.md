---
title: "ComfyUI StarChart"
---

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-05-20

## Scope

This documentation section covers ComfyUI development topics including API
endpoints, extension hooks, custom node authoring, and extension architecture.
It is a source-backed, version-pinned reference, not the official ComfyUI
documentation. See [docs.comfy.org](https://docs.comfy.org/) for official docs.

The repository also publishes machine-readable JSON artifacts extracted from
pinned upstream snapshots. See [Machine-Readable Artifacts](reference/machine-readable-artifacts.md)
for a catalog of available artifacts, stable URLs, and consumption guidance.
That page also documents the support-artifact pair `artifacts/docs-index.json`
and `artifacts/tooling-index.json`, which help with routing and task discovery
without replacing the canonical JSON references.

When choosing a machine-readable entry surface:

- use `artifacts/manifest.json` for canonical artifact discovery and checksum-aware loading
- use `artifacts/docs-index.json` for conservative page routing across published docs
- use `artifacts/tooling-index.json` for higher-level tooling-task routing, route relations, and next-read hints

Treat this docs site as a product with bounded audiences:

- **Consumers** use these published pages and artifacts to build against
  ComfyUI.
- **Contributors** use the published start-here pages first, then move into
  repo-local workflow docs only when a change crosses into maintainer-owned
  surfaces.
- **Maintainers** use repo-local files such as `CONTRIBUTING.md` and
  `AGENTS.md` for refresh, verifier, and release-style workflows that are not
  fully duplicated here.

## Who This Section Is For

Choose your starting point based on what you are building:

| Goal | Start Here |
|------|-----------|
| Build custom nodes | [Custom Node Author](start-here/author.md) |
| Extend ComfyUI (frontend or server) | [Extension Developer](start-here/extension-developer.md) |
| Integrate ComfyUI into an external service | [Service Integration](start-here/service-integration.md) |
| Contribute documentation | [Docs Contributor](start-here/docs-contributor.md) |
| Build tools or agents against ComfyUI | [Tooling Builder](start-here/tooling-builder.md) |

If you need repo-local maintainer workflow details after starting here, switch
to the repository's `CONTRIBUTING.md` file and only escalate further when your
change reaches scripts, CI, extracted references, or published artifacts.

## Orientation Aids

- [Glossary](reference/glossary.md) -- repeated repo and artifact terms used
  across the docs
- [Architecture Overview](architecture/overview.md) -- bounded conceptual map of
  the client, server, workflow, and tooling surfaces
- [What's New](whats-new/index.md) -- notable repo-visible changes that affect
  readers and contributors
- [Troubleshooting](troubleshooting/index.md) -- bounded confusion-reduction
  routes for integration, authoring, and extension-boundary questions

## Page Structure

This documentation is organized as follows:

- **Start Here** (`start-here/`) -- Audience-specific reading paths
- **Orientation** (`whats-new/`, `reference/glossary.md`, `troubleshooting/`,
  `known-limitations/`) -- Discoverability pages for repo terms, recent reader-
  visible changes, bounded troubleshooting, and verified limitations
- **Architecture** (`architecture/`) -- Bounded conceptual overview pages for
  system shape and major tooling surfaces
- **Section Guides** (`api/index.md`, `hooks/index.md`, `custom-nodes/index.md`,
  `tutorials/index.md`, `how-to/index.md`) -- Short hub pages for choosing the
  right page within a family
- **API Reference** (`api/`) -- HTTP endpoints, WebSocket events, prompt
  submission, queue, and history semantics
- **Hooks** (`hooks/`) -- JavaScript hooks, server hooks, and extension points
- **Custom Nodes** (`custom-nodes/`) -- V3-oriented node authoring, registration,
  datatypes, and best practices
- **Extensions** (`extensions/`) -- Extension architecture patterns and analysis
- **Tutorials** (`tutorials/`) -- Task-oriented guides that combine multiple
  concepts
- **How-To** (`how-to/`) -- Focused operational recipes
- **Decision Trees** (`decision-trees/`) -- Tradeoff guides for architectural choices
- **Reference** (`reference/`) -- Evidence policy, writing style guide, and
  machine-readable summaries
- **Ecosystem** (`ecosystem/`) -- Community tools and patterns
- **Deep Dives** (`deep-dives/`) -- Detailed analysis of specific tools

## Section Hubs

Use these short guides when you know the family you need but do not want to scan
every page in that section.

| Section | Hub |
|---------|-----|
| API | [API Section Guide](api/index.md) |
| Hooks | [Hooks Section Guide](hooks/index.md) |
| Custom Nodes | [Custom Nodes Section Guide](custom-nodes/index.md) |
| Tutorials | [Tutorials Section Guide](tutorials/index.md) |
| How-To | [How-To Section Guide](how-to/index.md) |

## Evidence Policy

Content in this repo distinguishes:

- **official ComfyUI behavior** -- stated in `docs.comfy.org`
- **upstream source behavior** -- from cited ComfyUI source files for a specific
  version or commit
- **community pattern** -- from external repositories, labeled as such

See [Source Evidence Policy](reference/source-evidence-policy.md) for the
full labeling rules.

## Current Version Pin

ComfyUI core `v0.21.1` and official frontend `v1.45.9`. Content written
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
