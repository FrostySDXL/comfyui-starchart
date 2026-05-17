---
title: "What's New"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-05-17

## Scope

This page highlights meaningful repo-visible changes that affect how readers
use the docs or published artifacts. It is intentionally selective and does not
backfill the full project history.

## Current Wave

### Site framework migrated to Astro Starlight

The documentation site now builds with Astro Starlight instead of MkDocs.
Build output moves from `site/` to `dist/`. The sidebar, remark plugins,
and page routing are all Starlight-native. Use `npm run dev` and
`npm run build` as before; the underlying framework is different but the
reader-visible surface is preserved.

### Verification surface expanded

New blocking verifiers catch sidebar navigation coverage drift
(`sidebar_navigation_coverage.py`), example surface integrity
(`example_surface_integrity.py`), and Python style violations via Ruff
(`python_style.py`). The advisory escalation workflow (`advisory-checks.yml`)
replays non-blocking checks as blocking on a weekly schedule.

### Community page coverage is now verified

A new verifier ensures every page in the community-generated surface is
accounted for, and stale generated pages are flagged before they reach
readers.

## Previous Waves

### Reader entry paths are now audience-specific

The docs route readers through focused start-here pages for custom node
authors, extension developers, service integrators, tooling builders, and docs
contributors.

### Published artifact guidance is more explicit

The machine-readable artifact docs distinguish canonical published artifacts,
support artifacts, schema discovery, and versioning boundaries more clearly
for tooling consumers.

### Discoverability surfaces are expanding

The repo adds bounded orientation pages such as this update log, the glossary,
troubleshooting routes, and short section hubs so readers can find the right
page without scanning the entire sidebar first.

## How to Use This Page

- Read this page when the repo structure or reader workflow changes.
- Use section hubs and start-here pages for routing, not this page.
- Use the reference pages when you need exact artifact or API details.

## Read Next

- [Docs Home](../index.md)
- [Glossary](../reference/glossary.md)
- [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md)
