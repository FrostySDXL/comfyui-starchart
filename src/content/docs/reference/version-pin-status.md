---
title: "Version Pin Status"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-06-13

> **Operational Note:** This is an operational tracking page that records the
> repository's current pinned extraction baseline. It is maintained manually.
> It does not define native ComfyUI behavior; it records what this
> repository has pinned for its own reference purposes.

**Primary Sources:** https://github.com/Comfy-Org/ComfyUI, https://github.com/Comfy-Org/ComfyUI/releases, https://docs.comfy.org/changelog

## Current State

This repository now has a pinned extraction baseline for its machine-readable
reference data.

Pinned source set:

- ComfyUI core tag `v0.24.0`
- core commit `f49bdb655707b97952dcef40e12e5af1f08d2007`
- official frontend package version `1.46.14`
- official frontend tag `v1.46.14`
- frontend commit `f212c7d40955a5ed54951a94a51ca40d1f4d4cbf`

The active pinned files now live under `references/snapshots/2026-06-13/` and
the extracted JSON in `references/raw/` points at those snapshot files.

Prose docs may lag this canonical artifact baseline. When they do, they should
declare that explicitly with a `**Baseline verification status:**` block rather
than implying current-baseline review that did not happen.

Earlier pinned baselines under `references/snapshots/2026-06-01/`,
`references/snapshots/2026-05-21/`, `references/snapshots/2026-05-18/`,
`references/snapshots/2026-04-30/`, and `references/snapshots/2026-04-19/`
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
- `references/raw/websocket_events.json` is extracted from pinned core
  WebSocket/event sources plus pinned frontend listener sources
- `references/raw/object_info_runtime.json` is an optional runtime-only capture
  artifact and is not part of the canonical public artifact set

These artifacts are also published as static files under `public/artifacts/`,
with current copies and versioned copies keyed to the pinned baseline. See
[Machine-Readable Artifacts](machine-readable-artifacts.md) for the manifest
and consumption details.

The current published versioned artifact directory is
`public/artifacts/versions/core-v0.24.0_frontend-v1.46.14_2026-06-13/`.

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

## Known Baseline Deltas

The current checked-in machine-readable delta is published in
`public/artifacts/delta-summary.json`. Its `comparison` block is the authority
for what was compared. At the time of this page update, it compares the recorded
pre-refresh raw backup `references/_refresh_backups/raw_20260613T202328Z` to the
current `references/raw/` artifacts.

The extraction surface is structurally stable between v0.23.0 and v0.24.0:
no endpoints, hooks, IO types, WebSocket events, or other canonical artifact
sections were added, removed, or changed at the extraction level. All counts
are identical between the two baselines (25 endpoints, 19 hooks, 76 IO types,
11 WebSocket events).

For item-level proof and field-level diff coverage, read
`public/artifacts/delta-summary.json` directly.

## Read Next

- [Machine-Readable Artifacts](machine-readable-artifacts.md)
- [Artifact Schema Version Migration](artifact-schema-version-migration.md)
- [Source Evidence Policy](source-evidence-policy.md)
