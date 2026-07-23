# Snapshot Inputs

This directory stores pinned upstream source inputs used by the repo's
extractors. These files are source inputs, not generated outputs.

## Directory layout

- each dated directory records the snapshot set captured for a refresh or pinned
  baseline change
- directory names use `YYYY-MM-DD`
- the current baseline is tracked in
  [`src/content/docs/reference/version-pin-status.md`](../../src/content/docs/reference/version-pin-status.md)

Current layout at the time of this update:

| Snapshot date | Core version | Frontend version | Role | Completeness class | Extraction suitability |
|---|---|---|---|---|---|
| `2026-04-19/` | `v0.19.3` | missing | Historical baseline retained for provenance and comparison. | `historical-partial` | Not suitable for extraction without backfill. |
| `2026-04-30/` | missing | missing | Known empty capture from an abandoned v0.20.1 / v1.44.13 refresh; the empty versioned artifact placeholder was removed after confirming no active publication references required it. | `historical-partial` | Not suitable for extraction without backfill. |
| `2026-05-18/` | `v0.21.1` | missing | Historical baseline retained for comparison and refresh-path proof. | `historical-partial` | Not suitable for extraction without backfill. |
| `2026-05-21/` | `v0.22.0` | missing | Historical baseline retained for comparison and refresh-path proof. | `historical-partial` | Not suitable for extraction without backfill. |
| `2026-06-01/` | `v0.23.0` | missing | Prior active baseline superseded by `2026-06-03/`; retained for refresh-path proof. | `historical-partial` | Not suitable for extraction without backfill. |
| `2026-06-03/` | `v0.23.0` | `v1.46.6` | Retained complete baseline superseded by `2026-06-13/`, `2026-06-26/`, and `2026-07-23/`. | `retained-complete` | Suitable for historical extraction and comparison. |
| `2026-06-13/` | `v0.24.0` | `v1.46.14` | Retained complete baseline superseded by `2026-06-26/` and `2026-07-23/`. | `retained-complete` | Suitable for historical extraction and comparison. |
| `2026-06-26/` | `v0.26.0` | `v1.47.5` | Retained complete baseline superseded by `2026-07-23/`. | `retained-complete` | Suitable for historical extraction and comparison. |
| `2026-07-23/` | `v0.28.0` | `v1.48.4` | Current active pinned baseline used by `references/raw/` and `public/artifacts/versions/core-v0.28.0_frontend-v1.48.4_2026-07-23/`. | `current-required-complete` | Suitable for current extraction. |

Maintainer classification procedure: run
`python scripts/verify/snapshot_surface_coverage.py`, inspect the dated
directories under `references/snapshots/`, sort rows by snapshot date, and update
this hand-authored table byte-stably for the same on-disk state. Historical
partial rows are retained provenance, not blocking current-baseline failures.

## Maintainer rules

- do not hand-edit files under these dated directories
- this parent README is the canonical inventory for retained snapshot baselines;
  individual dated directories do not need their own README when this inventory
  records their retention purpose clearly
- use `scripts/refresh_snapshots.py` and the maintainer workflow in
  [`CONTRIBUTING.md`](../../CONTRIBUTING.md) when refreshing the pinned baseline
- use
  [`src/content/docs/reference/version-pin-status.md`](../../src/content/docs/reference/version-pin-status.md)
  to confirm which dated directory is current before reviewing or citing
  snapshot paths

Temporary refresh backup working state belongs under `references/_refresh_backups/`.
That location is distinct from this committed snapshot history.
