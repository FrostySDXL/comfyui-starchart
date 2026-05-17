---
title: "Community Maintenance Policy"
---

# Community Maintenance Policy

**Evidence:** Operational guidance
**Last Updated:** 2026-05-06
**Related:** `references/community/community_pages.json`, `references/community/ecosystem_packages.json`

## Purpose

This repository contains two kinds of content:

1. **Source-backed reference** extracted from pinned ComfyUI upstream snapshots
2. **Community-facing material** about ecosystem packages, patterns, and limitations

This policy defines maintenance tiers for the second category. Tiers help
prioritize review effort without overstating certainty.

## Maintenance Tiers

### Tier 1 -- Source-backed core reference

Pages derived from current ComfyUI source code or official docs.

- **Examples:** API endpoint reference, hook catalogs, datatype definitions,
  `src/content/docs/known-limitations/index.md`
- **Review cadence:** When the upstream version pin changes
- **Evidence label:** `Source-backed from pinned snapshots` or
  `Official docs-backed from docs.comfy.org`
- **Trust framing:** Highest confidence; cite exact snapshot paths or docs URLs

### Tier 2 -- Curated community pages with active maintenance value

Pages that track high-churn ecosystem information and are regenerated or
reviewed frequently.

- **Examples:** `src/content/docs/ecosystem/map.md` (generated from
  `references/community/ecosystem_packages.json`)
- **Review cadence:** Every 3 months
- **Evidence label:** `Community pattern study` or `Community pattern study based on pinned external version`
- **Trust framing:** Time-bound assessments; verify before building dependencies

### Tier 3 -- Pinned community deep dives

Hand-authored studies of external repositories at a pinned commit. These are
slower-moving but still drift when the upstream repo changes.

- **Examples:** `src/content/docs/deep-dives/comfyui-manager.md`,
  `src/content/docs/deep-dives/comfyui-impact-pack.md`
- **Review cadence:** Every 6 months, or when the pinned external repo has a
  significant release
- **Evidence label:** `Community pattern study based on pinned external version`
- **Trust framing:** Conservative scope; do not claim full audit coverage

### Tier 4 -- Low-priority or archival community references

Pages or packages with insufficient signal to assess, or content kept for
historical context.

- **Examples:** Packages marked `Unknown` in the ecosystem map, abandoned
  scaffold pages
- **Review cadence:** As needed; annual at most
- **Evidence label:** `Community pattern study` or `Scaffold`
- **Trust framing:** Explicitly weak; do not build production dependencies on
  Tier 4 material

## Low-Confidence and Unknown Entries

Treat low-confidence entries as exceptions, not as the default shape of the
catalog.

- Prefer omission over weak inclusion. If a candidate does not have enough
  public signal to support a clear maintenance assessment, leave it out of
  `references/community/ecosystem_packages.json` until stronger evidence exists.
- Use `Unknown` status and `tier_4` only when the package is important enough to
  mention despite weak or mixed signals.
- When an `Unknown` or `tier_4` entry is intentionally retained, add an explicit
  `caveats` note that tells readers why confidence is limited and why the entry
  still appears in the catalog.
- Do not add placeholder-like entries just to fill a gap category. Gap coverage
  matters less than confidence clarity.
- First-wave catalog additions should favor candidates with strong public signal
  and a clear maintenance story before lower-confidence ecosystem breadth.

## How Tiers Are Enforced

- `references/community/community_pages.json` records the tier and
  `needs_review_after` date for every community-facing page
- `references/community/ecosystem_packages.json` records the tier and review
  date for every cataloged package
- `scripts/verify/community_staleness.py` flags entries whose review date has
  passed
- `scripts/verify/community_metadata.py` validates that tier values are allowed
  and that dates are consistent
- `scripts/verify/validate_schema.py` validates JSON structure and enforces
  forward-slash path formatting for community metadata
- `scripts/verify/community_page_coverage.py` checks that community-evidence
  pages are tracked and that tracked pages still exist with matching evidence
  labels
- `scripts/verify/community_generated_freshness.py` checks that generated
  community pages were regenerated after source metadata changes

## Generated vs Hand-Authored Boundaries

| Kind | Edit surface | Do not edit |
|------|--------------|-------------|
| Generated catalog | `references/community/ecosystem_packages.json` | `src/content/docs/ecosystem/map.md` |
| Hand-authored deep dive | The markdown file itself | n/a |
| Generated-surface explainer | `src/content/docs/reference/community-generated-surfaces.md` | n/a |
| Policy page | The markdown file itself | n/a |

If you update community metadata or regenerate a catalog, run the community
verification sequence afterwards:

```bash
python scripts/verify/validate_schema.py
python scripts/verify/community_metadata.py
python scripts/verify/community_staleness.py
python scripts/generate/generate_community_pages.py
python scripts/verify/community_generated_freshness.py
python scripts/verify/community_page_coverage.py
python scripts/verify/cross_references.py
npm run build
```

If you only change a hand-authored community page or policy page, you can skip
the generator step, but still run:

```bash
python scripts/verify/validate_schema.py
python scripts/verify/community_metadata.py
python scripts/verify/community_staleness.py
python scripts/verify/community_page_coverage.py
python scripts/verify/cross_references.py
npm run build
```

## Trust Boundaries

- Community content is never authoritative for native ComfyUI behavior.
- Generated pages carry a `GENERATED FILE` banner.
- Hand-authored studies carry an explicit pinned commit and verification date.
- When in doubt, prefer Tier 1 sources over community observations.

## Read Next

- `src/content/docs/reference/source-evidence-policy.md` for evidence labeling rules
- `src/content/docs/reference/community-generated-surfaces.md` for the public generated-community product surface
- `src/content/docs/ecosystem/map.md` for the current ecosystem catalog
- `references/community/README.md` for the community metadata update workflow
