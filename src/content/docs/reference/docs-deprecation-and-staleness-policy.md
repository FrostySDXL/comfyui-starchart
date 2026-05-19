---
title: "Docs Deprecation and Staleness Policy"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-05-18
**Related:** `scripts/verify/stale_content.py`, `references/community/community_pages.json`, `src/content/docs/reference/community-maintenance-policy.md`

## Scope

This page defines how maintainers should handle documentation that becomes stale,
version-misaligned, or superseded.

It covers repo-local process for published docs pages. It does not redefine how
ComfyUI itself marks deprecated runtime features.

## Two Different Problems

| Condition | Meaning | Typical action |
|---|---|---|
| stale content | the page no longer matches the current pinned baseline, repo workflow, or reviewed community state | update, narrow, or temporarily downgrade the page honestly |
| deprecated subject | the page describes a feature or path that upstream or the repo still needs to mention, but no longer recommends | keep the page only with explicit replacement guidance and source-backed framing |

## Triggers for Review

Re-review a page when any of these happen:

- the pinned upstream baseline changes
- repo workflow or verification commands change
- community review windows expire
- a page starts contradicting generated artifacts or policy pages
- a verifier or build failure points to outdated guidance

## Required Maintainer Actions

When you confirm drift, do one of these immediately:

1. update the page to the current truthful state
2. narrow the claims so the page is still correct for a bounded scope
3. convert the page to a Scaffold if major sections are knowingly incomplete
4. remove or reroute the page if keeping it would mislead readers

Do not leave known drift in place without an honest scope reduction.

## Handling Deprecated Subjects

If a page must continue to document a deprecated upstream or repo path:

- cite the source that establishes the deprecation or replacement
- state what readers should use instead
- keep the deprecated path separate from the recommended path
- avoid wording that makes the older path sound current or preferred

## Automation Boundaries

Automation helps, but it does not replace editorial judgment:

- `scripts/verify/stale_content.py` flags broad stale-marker tokens and can also
  flag old dates or older version references when run with optional checks
- community review metadata and staleness checks cover the community-facing
  surface on their own cadence
- normal doc verification still depends on `cross_references.py` and site build
  success, not only stale-marker scanning

## Read Next

- [Doc Quality Checklist](doc-quality-checklist.md)
- [Source Evidence Policy](source-evidence-policy.md)
- [Community Maintenance Policy](community-maintenance-policy.md)
- [Version Pin Status](version-pin-status.md)
