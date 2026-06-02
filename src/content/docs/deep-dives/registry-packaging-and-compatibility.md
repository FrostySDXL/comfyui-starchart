---
title: "Deep Dive: Registry Packaging and Compatibility"
---

**Evidence:** Official docs-backed from docs.comfy.org
**Last Updated:** 2026-05-13
**Primary Sources:** https://docs.comfy.org/registry/specifications; https://docs.comfy.org/registry/publishing; https://docs.comfy.org/registry/cicd
**Baseline verification status:** This page has not been re-reviewed against the current baseline.

## Scope

This page explains the official registry packaging model for ComfyUI custom
nodes. It focuses on metadata, compatibility fields, and the distribution model
those fields support. It is not a repackaged step-by-step publishing guide.

## Why the packaging model matters

The registry flow is not just a delivery channel. It defines what a custom node
package must say about itself so the registry, ComfyUI-Manager, and surrounding
automation can reason about installation and compatibility.

At the center of that model is `pyproject.toml`, with two major surfaces:

- `[project]` for package identity and Python packaging metadata
- `[tool.comfy]` for Comfy-specific publisher and compatibility metadata

That split matters because it keeps registry packaging tied to standard Python
package conventions while still exposing Comfy-specific distribution rules.

## Package identity is part of the public contract

The official specifications page treats package identity as more than a display
choice.

### `name` is registry identity

The `[project].name` field uniquely identifies the node and is used in registry
URLs and install commands. That makes it part of the package's durable public
surface, not just a label.

### `version` is the release track

The registry model expects semantic versioning in `X.Y.Z` form. That gives the
registry, automation, and users a shared compatibility language for breaking
changes, backward-compatible features, and patches.

### Publisher identity is separate

`[tool.comfy].PublisherId` identifies who publishes the node. This is distinct
from the node package name. In practice, the model separates:

- package identity
- publisher identity
- user-facing display metadata

That separation is one of the main differences between the official registry
flow and older community-discovery patterns.

## Compatibility is declared in layers

The official docs spread compatibility across several fields rather than one
single switch.

### Python compatibility

`requires-python` declares which Python versions the package supports. This is a
standard packaging constraint and belongs to the Python layer.

### Frontend compatibility

The specifications page describes frontend version compatibility through the
`comfyui-frontend-package` dependency. That is a notable design choice: frontend
compatibility is modeled as a package dependency constraint rather than as an
entirely separate bespoke field.

For extension authors, this means frontend breakage or API expectations should
be expressed in dependency ranges when the official packaging model supports it.

### Core ComfyUI compatibility

`[tool.comfy].requires-comfyui` declares which ComfyUI versions a node supports.
This is the Comfy-specific compatibility field that helps users and tooling
understand whether a package matches a given ComfyUI installation.

Together, these fields form a layered compatibility story:

- Python interpreter support
- frontend package compatibility when relevant
- ComfyUI version compatibility

That is more precise than treating compatibility as a single freeform note.

## Metadata also shapes discoverability

The packaging model includes fields that affect how a package is presented and
filtered.

- `description` summarizes purpose
- `classifiers` declare OS and accelerator compatibility
- `DisplayName`, `Icon`, and `Banner` shape registry and Manager presentation
- `project.urls` exposes repository and related links

These fields do not change runtime execution, but they do change how packages
are understood, discovered, and trusted. In the official model, packaging is
part technical contract and part distribution metadata.

## Publishing is downstream of metadata quality

The publishing flow assumes the package metadata already exists.

- `comfy node init` scaffolds the expected metadata structure
- `comfy node publish` submits a versioned package to the registry
- GitHub Actions can automate publication once credentials and metadata are in
  place

That means publication is not the conceptual starting point. The deeper model is
that a node becomes registrable only after it has a coherent package identity,
publisher identity, and compatibility declaration.

This reduced surface keeps the packaging model and compatibility framing, not a
step-by-step publication walkthrough.

## CI/CD is part of the official packaging story

The CI/CD page is short, but it matters. The official flow expects maintainers
to validate workflow behavior in automation rather than treating publication as a
pure metadata event.

The docs point to `comfy-action` for running workflow JSON on GitHub Actions
across Linux, macOS, and Windows, with support for models and custom nodes.
That turns compatibility from a static declaration into something a package can
test before release.

The important distinction is:

- metadata declares intended compatibility
- CI/CD provides evidence that a release still behaves under automation

## Registry-backed distribution boundaries

The newer Manager UI and the registry model introduce a clearer official
boundary around supported distribution.

- registry-backed packages participate in the official metadata and install flow
- the new Manager UI only supports installing nodes from the registry
- manual installation remains a separate path for nodes outside that flow

This does not mean every community package is invalid if it is not in the
registry. It means the official distribution surface now has explicit boundaries.
Tooling and docs should not blur registry-backed installation with legacy or
manual discovery methods.

## What this page does not claim

- It does not claim registry packaging is the only way a community node can
  exist.
- It does not turn the publishing guide into a compatibility guarantee.
- It does not treat ComfyUI-Manager's community repo layout as the authority for
  official package metadata.

The official packaging model is defined by the registry docs, not by a community
repository structure.

## Read Next

- [Registration](../custom-nodes/registration.md)
- [Tooling Builder](../start-here/tooling-builder.md)
- [Topic Scope](../reference/topic-scope.md)
