---
title: "Start Here: Artifact Consumer"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-05-27

## Scope

This page is the shortest start-here route for readers who consume this repo's
published JSON artifacts. It covers the manifest-first loading path, the bounded
routing-support surface, and the example boundary. It does not restate every
artifact field or every API page.

## Who This Path Is For

Use this path when you need to:

- load the pinned JSON artifacts safely
- route a tool to the right retained docs page without scraping the whole site
- inspect the starter consumer examples without treating them as an SDK

## Start with the Manifest

Use `artifacts/manifest.json` first.

- It is the canonical discovery surface for the three published extracted
  artifacts.
- It gives you stable current URLs, versioned URLs, source metadata, and SHA-256
  checksums.
- Strict tooling should trust guaranteed fields and published schema files, not
  descriptive best-effort prose fields.

Read [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md)
for the exact contract.

## Inline Consumer Contract

Keep the durable contract short and explicit:

- use manifest-first discovery from `artifacts/manifest.json`
- load the canonical current copy from `artifacts/current/<name>.json`
- build strict tooling only against guaranteed fields and published schemas
- verify current-copy downloads against the manifest `sha256`
- treat `docs-index.json` as optional routing help layered on top of the canonical artifacts

## Use the Routing Support Surface Sparingly

The repo also publishes a bounded support index for docs and tooling routing.
Treat that surface as optional guidance layered on top of manifest-first
artifact discovery.

- Use it when you need a first-pass page match.
- Do not treat it as a replacement for `manifest.json`.
- Do not treat it as full-text search or as a new canonical artifact contract.

## If you are an agent or tool

Use `docs-index.json` when you need a bounded first pass to choose which docs
page to read next. Ignore it and go straight to the canonical artifacts when you
already know the route, schema, or artifact surface you need. Do not over-trust
best-effort routing fields when a manifest entry or canonical artifact answers
the question directly.

## Starter Example Boundary

The consumer examples under `examples/consumers/` are starter patterns only.

- They show small manifest, route, and runtime-consumer flows.
- They are intentionally bounded.
- They do not create a supported SDK, client library, or broader productized
  integration contract.

Runtime-dependent examples remain optional. The manifest-first and artifact-only
parts are the stable starting point.

## When to Switch to Repo-Local Workflow Docs

Stay in the published docs path unless you are contributing to this repository.
If you start editing docs, scripts, or generated artifacts, switch to the
repo-local maintainer workflow in `CONTRIBUTING.md`.

## Read Next

- [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md)
- [Start Here: Tooling Builder](tooling-builder.md)
- [Start Here: Service Integration](service-integration.md)
- [Reference: Topic Scope](../reference/topic-scope.md)
