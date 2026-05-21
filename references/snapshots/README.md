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

- `2026-05-21/` - current active pinned baseline used by `references/raw/`
- `2026-05-18/` - historical baseline retained for comparison and refresh-path
  proof
- `2026-04-30/` - earlier historical baseline retained for comparison and
  refresh-path proof
- `2026-04-19/` - earlier historical baseline retained for provenance and
  comparison

## Maintainer rules

- do not hand-edit files under these dated directories
- use `scripts/refresh_snapshots.py` and the maintainer workflow in
  [`CONTRIBUTING.md`](../../CONTRIBUTING.md) when refreshing the pinned baseline
- use
  [`src/content/docs/reference/version-pin-status.md`](../../src/content/docs/reference/version-pin-status.md)
  to confirm which dated directory is current before reviewing or citing
  snapshot paths

Temporary refresh backup working state belongs under `references/_refresh_backups/`.
That location is distinct from this committed snapshot history.
