---
title: "Community Generated Surfaces"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-05-06
**Related:** `references/community/ecosystem_packages.json`, `references/community/community_pages.json`, `src/content/docs/ecosystem/map.md`, `src/content/docs/reference/community-maintenance-policy.md`

This page explains the repo's public community-product surface. It covers the
structured metadata files, the generated ecosystem catalog, and the confidence
signals readers should use when deciding how much weight to place on community
content.

## What This Surface Includes

The community surface has two main metadata inputs:

1. `references/community/ecosystem_packages.json` -- the editable package catalog
   source for community ecosystem entries
2. `references/community/community_pages.json` -- the review-tracking source for
   generated and hand-authored community-facing pages

Those inputs currently feed these reader-visible surfaces:

- `src/content/docs/ecosystem/map.md` -- generated ecosystem catalog
- community deep dives, guides, and policy pages tracked in
  `references/community/community_pages.json`

## What Is Generated

`src/content/docs/ecosystem/map.md` is generated from
`references/community/ecosystem_packages.json` by
`scripts/generate/generate_community_pages.py`.

That means:

- edit the JSON source when package entries change
- regenerate the page after metadata edits
- do not hand-edit the generated Markdown

`references/community/community_pages.json` is not a generator input for page
body text. It tracks review cadence, evidence labels, and page coverage for the
community-facing docs surface.

## How to Interpret Confidence Signals

The community catalog does not use the same trust model as pinned upstream
reference pages. Its confidence signals are operational and time-bound.

Use these signals together:

- **Status** -- reader-facing maintenance assessment such as `Actively Maintained`,
  `Community Supported`, `Likely Unmaintained`, or `Unknown`
- **Maintenance tier** -- repo-local review priority and confidence framing from
  `src/content/docs/reference/community-maintenance-policy.md`
- **Last Verified / Needs Review After** -- freshness window for the current
  assessment
- **Caveats** -- explicit warnings for weak-signal, unusual, or maintenance-only
  entries

In practice:

- `tier_2` entries are curated community references worth checking regularly,
  but they still need direct upstream re-verification before hard dependency use
- `tier_3` entries are useful pinned studies or community examples with narrower
  trust framing
- `tier_4` entries are intentionally weak-signal or archival and should be rare

## What the Catalog Does and Does Not Claim

The ecosystem catalog does:

- highlight notable community packages with clear maintenance framing
- point readers at instructive community patterns
- preserve a bounded, reviewable slice of the ComfyUI ecosystem

The ecosystem catalog does not:

- claim official ComfyUI behavior
- guarantee that a package is safe, current, or production-ready
- attempt to list every custom node repository
- replace direct verification of a dependency before adoption

## Reader Workflow

When you use the ecosystem catalog:

1. scan the package status and caveats
2. check the verification date
3. open the linked upstream repository or registry page
4. confirm the package still matches your ComfyUI version and use case

## Read Next

- [Community Maintenance Policy](community-maintenance-policy.md)
- [Ecosystem Map](../ecosystem/map.md)
- `references/community/README.md` for the repo-local metadata update workflow
