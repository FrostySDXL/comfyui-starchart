---
title: "Artifact Schema Version Migration"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-05-18
**Related:** `public/artifacts/manifest.json`, `public/artifacts/schemas/`, `references/raw/`

## Scope

This page explains how tooling consumers should interpret and respond to changes
in the published `artifact_schema_version` field.

It covers the repo's artifact contract, not upstream ComfyUI release migration
in general.

## Two Version Concepts

Keep these version concepts separate:

| Field | What it tracks | Use it for |
|---|---|---|
| `artifact_schema_version` | the repo's bounded artifact contract | parser and schema migration decisions |
| `version_key` plus per-artifact `version` / `commit` | the pinned upstream ComfyUI baseline | baseline selection and reproducibility |

A new upstream pin can keep the same schema version. A schema version bump can
happen even when the upstream pin is unchanged.

## How to Interpret a Schema-Version Bump

The repo documents semantic-version meanings for the published contract:

- **major**: breaking changes to guaranteed fields, required structure, or
  schema-discovery semantics
- **minor**: backward-compatible additions to guaranteed structure or manifest
  schema discovery
- **patch**: non-breaking corrections or tightening that should not invalidate a
  previously valid guaranteed-shape consumer

## Consumer Migration Workflow

When `artifact_schema_version` changes:

1. fetch the new `artifacts/manifest.json`
2. compare the old and new `artifact_schema_version`
3. read the matching checked-in schema file under `artifacts/schemas/` for the
   canonical artifact you consume
4. update strict parsing only for guaranteed fields and required structure
5. retest against the new versioned artifact URL, not only the `current/` copy

If your tooling consumes best-effort fields, treat every schema-version bump as
an extra review trigger even when the guaranteed structure remains compatible.

## What Does Not Automatically Require a Parser Migration

These changes are still important, but they are not the same as a contract bump:

- `version_key` changes with the same `artifact_schema_version`
- new pinned upstream commits with unchanged guaranteed structure
- support-artifact changes in `docs-index.json`, `delta-summary.json`, or
  `refresh-provenance.json`

Those cases usually mean baseline review, not guaranteed-structure migration.

## Safe Consumer Rules

- start from `manifest.json` instead of hardcoding versioned paths
- validate downloads against manifest `sha256` when integrity matters
- build strict logic only against guaranteed fields and schema files
- treat support artifacts as optional helpers with narrower guarantees
- keep runtime-only captures out of the canonical parser path unless your tool
  explicitly supports live-instance enrichment

## Read Next

- [Machine-Readable Artifacts](machine-readable-artifacts.md)
- [Runtime and CI Operations](runtime-ci-operations.md)
- [Version History](version-history.md)
