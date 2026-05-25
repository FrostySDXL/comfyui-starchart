---
title: "Start Here: Artifact Consumer"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-05-24

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

## Use the Routing Support Surface Sparingly

The repo also publishes a bounded support index for docs and tooling routing.
Treat that surface as optional guidance layered on top of manifest-first
artifact discovery.

- Use it when you need a first-pass page match.
- Do not treat it as a replacement for `manifest.json`.
- Do not treat it as full-text search or as a new canonical artifact contract.

## Starter Example Boundary

The consumer examples under `examples/consumers/` are starter patterns only.

- They show small manifest, route, and runtime-consumer flows.
- They are intentionally bounded.
- They do not create a supported SDK, client library, or broader productized
  integration contract.

Runtime-dependent examples remain optional. The manifest-first and artifact-only
parts are the stable starting point.

## Read Next

- [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md)
- [Start Here: Tooling Builder](tooling-builder.md)
- [Start Here: Service Integration](service-integration.md)
- [Reference: Topic Scope](../reference/topic-scope.md)
