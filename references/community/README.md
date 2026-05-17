# Community Metadata

This directory contains structured JSON metadata for community-facing content.
It is separate from `references/raw/` because it tracks ecosystem packages and
community pages rather than extracted upstream ComfyUI source artifacts.

## Scope

This directory tracks pages and packages that carry a community evidence
component or that define operational policy for community content. That
includes:

- generated catalogs (`src/content/docs/ecosystem/map.md`)
- pinned external repo studies (`src/content/docs/deep-dives/*.md`, case studies)
- community extension case studies (`src/content/docs/extensions/profilerx-analysis.md`)
- hybrid pages that mix official docs with community examples
- operational policy pages that govern community content review and tiering
  (`src/content/docs/reference/community-maintenance-policy.md`)

It does **not** track purely official-docs-backed reference pages such as
endpoint catalogs or hook lists. Those are source-backed and managed under
`references/raw/` and `references/snapshots/`.

## Files

| File | Purpose | Editable? |
|------|---------|-----------|
| `ecosystem_packages.json` | Catalog of ecosystem packages and their maintenance status | Yes -- edit this file to update the ecosystem map |
| `community_pages.json` | Review metadata for community-facing documentation pages | Yes -- edit this file to adjust review cadence or page status |

## Why JSON?

The repository already uses JSON for all machine-readable reference data.
Using JSON here keeps the community metadata layer consistent with the rest of
`references/` and avoids adding a YAML parser dependency.

## Generated consumers

- `src/content/docs/ecosystem/map.md` is generated from `ecosystem_packages.json` by
  `scripts/generate/generate_community_pages.py`. Do not edit the markdown file
  directly; edit the JSON source and rerun the generator.

## Freshness metadata

Every package entry and page entry carries:

- `last_verified` -- when the entry was last checked against public sources
- `needs_review_after` -- when the entry should be reviewed again
- `maintenance_tier` -- operational priority for review effort

These fields are checked by `scripts/verify/community_staleness.py`.

## Trust boundaries

Content in this directory is community-maintained, not source-backed from pinned
ComfyUI upstream snapshots. Generated pages carry explicit non-authoritative
language. Hand-authored deep dives remain hand-authored and are tracked here for
review scheduling only.

## Update workflow

1. Edit `ecosystem_packages.json` or `community_pages.json`
2. Run `python scripts/verify/validate_schema.py`
3. Run `python scripts/verify/community_metadata.py`
4. Run `python scripts/verify/community_staleness.py`
5. If you changed `ecosystem_packages.json`, run `python scripts/generate/generate_community_pages.py`
6. If you ran the generator, run `python scripts/verify/community_generated_freshness.py`
7. Run `python scripts/verify/community_page_coverage.py`
8. Run `python scripts/verify/cross_references.py`
9. Run `python -m mkdocs build`

## Path formatting

- Use forward slashes in JSON paths, even on Windows.
- `community_pages.json` path fields such as `page_path` and `generated_from`
  must use `/`, not `\\`.
