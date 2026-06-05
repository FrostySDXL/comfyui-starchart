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

- `2026-06-03/` - current active pinned baseline used by `references/raw/`
  and the published versioned artifacts under
  `public/artifacts/versions/core-v0.23.0_frontend-v1.46.6_2026-06-03/`
- `2026-06-01/` - prior active baseline superseded by `2026-06-03/`; retained
  for refresh-path proof
- `2026-05-21/` - historical baseline retained for comparison and refresh-path
  proof
- `2026-05-18/` - historical baseline retained for comparison and refresh-path
  proof
- `2026-04-19/` - earlier historical baseline retained for provenance and
  comparison
- `2026-04-30/` - known partial capture from an abandoned v0.20.1 / v1.44.13
  refresh; the snapshot directory itself is empty, but the corresponding
  versioned artifact set under
  `public/artifacts/versions/core-v0.20.1_frontend-v1.44.13_2026-04-30/` is
  retained for published-history completeness

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
