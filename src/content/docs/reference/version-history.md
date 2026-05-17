---
title: "Version History"
---

# Version History

## Scope

This page is not a full release log. It is a compatibility-focused summary for
custom node and extension authors who need to track changes that can alter:

- node schema expectations
- frontend integration points
- server/runtime behavior
- Manager and packaging assumptions

Tooling builders and doc authors should use the same release-line anchors when
they need to decide which version-specific assumptions to re-check.

Use the official changelog to scan the release landscape. Use the exact GitHub
release page for the line you are targeting before making a version-specific
claim. Exact tags matter more than broad minor-version guesses because frontend
package bumps, Manager version changes, schema additions, and runtime fixes can
shift within the same general era.

Treat the sections below as review priorities surfaced by official changelog and
release-note summaries. They are not exhaustive compatibility guarantees.

**Evidence:** Official docs-backed from docs.comfy.org; Operational guidance
**Last Updated:** 2026-05-13
**Primary Sources:** https://docs.comfy.org/changelog/index, https://docs.comfy.org/api-reference/releases/get-release-notes, https://github.com/Comfy-Org/ComfyUI/releases

## Release-Line Compatibility Anchors

### v0.20.x

**Exact release anchor:** [v0.20.1](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.20.1)

**Compatibility-relevant changes**

- adds an OpenAPI 3.1 specification for the ComfyUI API
- bumps the frontend package through `1.42.15` and bumps Manager to `4.2.1`
- adds execution anti-cycle validation and expands intermediate-dtype handling
- adds range-type support and updates blueprints and subgraph naming

**What to re-check**

- API clients that assume an older route or schema-documentation surface
- frontend widgets or extension UI that assume older input-type behavior
- Manager/version-aware setup guidance and any blueprint or subgraph labels in docs
- execution assumptions around cycle handling or intermediate dtype behavior

### v0.19.x

**Exact release anchor:** [v0.19.0](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.19.0)

**Compatibility-relevant changes**

- adds the `CURVE` node, `has_intermediate_output`, Number Convert, and Image Histogram surfaces
- bumps the frontend package to `1.42.10` and moves Manager within the `4.1` line
- adds RAM-cache integration, asset registration after prompt execution, and more intermediate-device handling
- expands text-generation, detection, and API-node surfaces while continuing template and frontend movement

**What to re-check**

- node docs or custom widgets that depend on older datatype or interactive-UI assumptions
- frontend pinning, packaged assets, and display-name or metadata expectations
- Manager-aware instructions that assume an older version boundary
- runtime and memory-path assumptions around RAM caching, intermediate outputs, and asset routing

### v0.18.x

**Exact release anchor:** [v0.18.0](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.18.0)

**Compatibility-relevant changes**

- adds `--fp16-intermediates` and `--enable-dynamic-vram` for more explicit memory-mode control
- aligns parts of the local API with the cloud spec and adds CacheProvider support
- bumps the frontend package to `1.41.21` and moves Manager through the `4.1b4` to `4.1b6` range
- expands Essentials, blueprint metadata, Quiver SVG nodes, and intermediate dtype/device handling

**What to re-check**

- dtype, VRAM, and offload assumptions in custom nodes and runtime-facing docs
- API tooling that assumes older local-versus-cloud response or asset behavior
- frontend integrations that cache chunks aggressively or depend on older package state
- blueprint, Essentials-tab, and advanced-input metadata assumptions

### v0.17.x

**Exact release anchor:** [v0.17.0](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.17.0)

**Compatibility-relevant changes**

- introduces a modular asset architecture with an async scanner and background seeder
- bumps the frontend package through `1.41.18` and moves Manager to `4.1b2`
- adds FluxKVCache support plus pre-attention, post-input, and cleanup-oriented model patching changes
- turns on Python fault-handler support and broadens accelerator-error handling

**What to re-check**

- extensions or tooling that assume older asset indexing or seeding behavior
- frontend integrations that depend on older asset-loading or package-state timing
- Manager install guidance, especially when docs assume the package is already present
- model-patching assumptions, especially if custom code hooks into wrapped-model behavior

### v0.16.x

**Exact release anchor:** [v0.16.0](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.16.0)

**Compatibility-relevant changes**

- adds `CURVE` type support and the ResolutionSelector node
- makes DynamicVram the default memory mode and expands related offload heuristics
- adds jobs-API text preview support and more intermediate-device or intermediate-dtype handling
- includes node-label and API-surface changes such as Similarity-Adaptive Guidance and `IMAGE+TEXT` support in NanoBanana2

**What to re-check**

- V1-era node definitions or docs that do not account for newer typed input surfaces
- tooling that consumes jobs output or assumes older preview capabilities
- memory-mode defaults, especially if custom nodes expect static VRAM behavior
- docs or examples that rely on older display names or dtype-flow expectations

### v0.8.x

**Exact release anchor:** [v0.8.0](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.8.0)

**Compatibility-relevant changes**

- exposes DynamicCombo and Autogrow in the public V3 API surface
- adds Sage Attention 3 CLI support, LTXV 2 support, and NVFP4 checkpoint support
- adds OOM memory summaries and more low-VRAM or CPU-offload fixes
- continues template churn and API-node expansion around video and 3D flows

**What to re-check**

- custom nodes and docs that assume older public V3 API capabilities
- CLI wrappers or launch scripts that need to account for newer runtime flags
- low-VRAM execution assumptions, especially around model movement and debugging output
- version-aware examples that should mention DynamicCombo or Autogrow instead of older workarounds

### v0.4.x

**Exact release anchor:** [v0.4.0](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.4.0)

**Compatibility-relevant changes**

- adds MatchType, DynamicCombo, and Autogrow support to the V3 schema
- converts more built-in node categories such as 3D, audio, freelunch, and mask nodes to V3
- bumps the frontend into the `1.33.x` line and adds ComfyUI-Manager pip-install support
- adds PATCH to CORS headers and ships major VRAM and temporal/context-window changes

**What to re-check**

- older V1 examples and custom nodes that still assume pre-V3 built-in node patterns
- API clients that depend on older CORS-method assumptions
- Manager setup docs, especially for pip-based installations
- runtime assumptions around temporal workflows, context windows, and VRAM accounting

If you are jumping from `v0.3.76` or older, also review the
[v0.3.76...v0.4.0 full changelog](https://github.com/Comfy-Org/ComfyUI/compare/v0.3.76...v0.4.0)
before assuming older Nodes 2.0, subgraph, or asset-sidebar UI expectations
still match current behavior.

## Compatibility Review Checklist

Before upgrading a custom node pack, frontend extension, tool integration, or
version-aware doc page, re-check these categories against the exact tag you are
targeting:

- **V1 versus V3 assumptions:** built-in node migrations, typed input/output changes, and older V1 helper usage
- **Frontend and package drift:** frontend package bumps, UI metadata changes, widget behavior, and missing-node or blueprint UI changes
- **Manager and registry workflow drift:** Manager version movement, install guidance changes, and pip-versus-registry assumptions
- **Datatype and widget drift:** `CURVE`, MatchType, DynamicCombo, Autogrow, range types, and interactive-output flags
- **API and route drift:** OpenAPI changes, jobs/history output changes, CORS-method changes, and local/cloud alignment notes
- **Runtime and execution drift:** dynamic VRAM defaults, fp16-intermediate behavior, memory accounting, anti-cycle validation, and asset execution side effects

Narrow downstream implications:

- **Tool builders:** prefer the exact release page plus the current pinned artifacts when you need version-specific route, schema, or datatype expectations
- **Doc authors:** update screenshots, widget names, Manager/version notes, and compatibility cautions only when the cited release line explicitly supports the change

The repository's machine-readable artifacts are extracted from a pinned baseline
and published with versioned copies. When you need exact API or schema behavior
for a specific ComfyUI version, prefer the pinned artifacts over broad release
notes. See [Machine-Readable Artifacts](machine-readable-artifacts.md) for the
manifest and stable URLs.

## Read Next

- [Version Pin Status](version-pin-status.md)
- [Machine-Readable Artifacts](machine-readable-artifacts.md)
- [Source Evidence Policy](source-evidence-policy.md)
