---
title: "Version Pin Status"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-06-01

> **Operational Note:** This is an operational tracking page that records the
> repository's current pinned extraction baseline. It is maintained manually.
> It does not define native ComfyUI behavior; it records what this
> repository has pinned for its own reference purposes.

**Primary Sources:** https://github.com/Comfy-Org/ComfyUI, https://github.com/Comfy-Org/ComfyUI/releases, https://docs.comfy.org/changelog

## Current State

This repository now has a pinned extraction baseline for its machine-readable
reference data.

Pinned source set:

- ComfyUI core tag `v0.23.0`
- core commit `a88e02b18576283b1ff25a4b564548c5dc42cbf6`
- official frontend package version `1.46.6`
- official frontend tag `v1.46.6`
- frontend commit `9e32b7db5173bc2879d4c19c1d058d733b3074b8`

The active pinned files now live under `references/snapshots/2026-06-01/` and
the extracted JSON in `references/raw/` points at those snapshot files.

Prose docs may lag this canonical artifact baseline. When they do, they should
declare that explicitly with a `**Baseline verification status:**` block rather
than implying current-baseline review that did not happen.

Earlier pinned baselines under `references/snapshots/2026-05-21/`,
`references/snapshots/2026-05-18/`, `references/snapshots/2026-04-30/`, and
`references/snapshots/2026-04-19/`
remain preserved for historical comparison and refresh-path proof.

Published artifact history is intentionally bounded: keep the current baseline,
the last 2 prior baselines, and any older baseline still referenced by active
docs, delta artifacts, refresh-provenance records, or migration guidance.
`references/_refresh_backups/` remains temporary local working state rather than
durable published history.

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

These artifacts are also published as static files under `public/artifacts/`,
with current copies and versioned copies keyed to the pinned baseline. See
[Machine-Readable Artifacts](machine-readable-artifacts.md) for the manifest
and consumption details.

The current published versioned artifact directory is
`public/artifacts/versions/core-v0.23.0_frontend-v1.46.6_2026-06-01/`.

## Automation

- `.github/workflows/advisory-checks.yml` runs `scripts/verify/upstream_pins.py`
  on a weekly schedule and on manual dispatch as the advisory replay path for
  pin-validity checks
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
then reconcile against official docs and release notes. For artifact-surface
consumption details, see [Machine-Readable Artifacts](machine-readable-artifacts.md).

## Known Baseline Deltas (v0.22.0 -> v0.23.0)

- **`GET /system_stats` field flattening:** The extracted `server_endpoints.json`
  artifact corrected how per-device GPU fields are represented (no longer listed
  as flat top-level fields; the `devices` array remains present in the actual
  API response). The 3D file type additions (SPLAT, FILE_3D_PLY, etc.) are
  recorded in `delta-summary.json`.

## Read Next

- [Machine-Readable Artifacts](machine-readable-artifacts.md)
- [Artifact Schema Version Migration](artifact-schema-version-migration.md)
- [Source Evidence Policy](source-evidence-policy.md)
