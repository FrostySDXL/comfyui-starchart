---
title: "Version Pin Status"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-05-18

> **Operational Note:** This is an operational tracking page that records the
> repository's current pinned extraction baseline. It is maintained manually.
> It does not define native ComfyUI behavior; it records what this
> repository has pinned for its own reference purposes.

**Primary Sources:** https://github.com/Comfy-Org/ComfyUI, https://github.com/Comfy-Org/ComfyUI/releases, https://docs.comfy.org/changelog

## Current State

This repository now has a pinned extraction baseline for its machine-readable
reference data.

Pinned source set:

- ComfyUI core tag `v0.21.1`
- core commit `26515acd23fa291a8f5ab53c5997258598de0701`
- official frontend package version `1.45.9`
- official frontend tag `v1.45.9`
- frontend commit `8562816ffa0d996bd400e517292fee074a6acefa`

The active pinned files now live under `references/snapshots/2026-05-18/` and
the extracted JSON in `references/raw/` points at those snapshot files.

The earlier pinned baseline under `references/snapshots/2026-04-19/` is still
preserved for historical comparison and refresh-path proof.

## Included Pinned Snapshot Material

- core: `server.py`, `execution.py`, `pyproject.toml`, `requirements.txt`,
  `app/frontend_management.py`, `comfy_api/latest/_io.py`,
  `comfy_api/latest/_input/basic_types.py`
- frontend: `package.json`, `src/scripts/app.ts`, `src/types/comfy.ts`,
  `src/services/litegraphService.ts`

## What This Pin Covers

- `references/raw/server_endpoints.json` is extracted from the pinned core
  `server.py`
- `references/raw/js_hooks.json` is extracted from the pinned official frontend
  TypeScript files
- `references/raw/node_api_schema.json` is extracted from the pinned core
  `server.py`, `comfy_api/latest/_io.py`, and `basic_types.py`
- `references/raw/object_info_runtime.json` is an optional runtime-only capture
  artifact and is not part of the canonical public artifact set
- `references/community/ecosystem_packages.json` and `community_pages.json`
  track external community metadata with their own `last_verified` and
  `needs_review_after` fields, independent of the ComfyUI core/frontend baseline

These artifacts are also published as static files under `public/artifacts/`,
with current copies and versioned copies keyed to the pinned baseline. See
[Machine-Readable Artifacts](machine-readable-artifacts.md) for the manifest
and consumption details.

The current published versioned artifact directory is
`public/artifacts/versions/core-v0.21.1_frontend-v1.45.9_2026-05-18/`.

## Automation

- `.github/workflows/weekly-pin-check.yml` verifies pinned commits still resolve
- `.github/workflows/upstream-watch.yml` runs every Monday at 10:00 UTC and on
  manual dispatch; scheduled runs detect newer upstream versions and create or
  update tracking issues, while manual runs do not mutate issue state

## Remaining Limits

- some prose docs still cite official docs pages or broader upstream URLs
  instead of exact pinned snapshot paths
- this pinned baseline directly governs the extracted data and published
  artifact set; prose citation depth still varies by page
- runtime-only artifacts reflect the specific ComfyUI instance configuration at
  capture time and should not be treated as canonical baselines

When exact version behavior matters, prefer the pinned snapshot files first,
then reconcile against official docs and release notes. For release-line
upgrade context, see [Version History](version-history.md).
