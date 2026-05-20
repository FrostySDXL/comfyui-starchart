---
title: "What's New"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-05-20

## Scope

This page highlights meaningful repo-visible changes that affect how readers
use the docs or published artifacts. It is intentionally selective and does not
backfill the full project history. For exhaustive chronological repo history,
use `CHANGELOG.md` in the repository root.

## Current Wave

### Tooling routing now has a richer support artifact

The published support surface now includes `artifacts/tooling-index.json` for
higher-level tooling-task routing, route relations, and next-read hints. The
tooling-builder entry path and starter-example routing were also tightened so
tooling consumers can move from discovery to prompt-submit monitoring faster
without blurring the canonical artifact boundary.

### Site framework migrated to Astro Starlight

The documentation site now builds with Astro Starlight instead of MkDocs.
Build output moves from `site/` to `dist/`. The sidebar, remark plugins,
and page routing are all Starlight-native. Use `npm run dev` and
`npm run build` as before; the underlying framework is different but the
reader-visible surface is preserved.

### Verification surface expanded

The blocking verification path now catches Python style drift via Ruff
(`python_style.py`), sidebar navigation coverage drift
(`sidebar_navigation_coverage.py`), and built-site internal navigation failures
(`rendered_links.py`). Example surface integrity
(`example_surface_integrity.py`) remains advisory in normal push/PR CI and is
replayed as blocking only in the scheduled/manual advisory workflow.

### Community page coverage is now verified

A new verifier ensures every page in the community-generated surface is
accounted for, and stale generated pages are flagged before they reach
readers.

### Architecture and limitations navigation are deeper

The docs now include dedicated architecture pages for the execution pipeline
and server-side composition. Known Limitations is split into categorized
sub-pages so readers can navigate API/execution boundaries, service-surface
boundaries, and extension-package constraints without scanning one long page.

### Integration coverage is less smoke-level

The test surface now includes fixture-backed extractor integration tests and
real remark/unified pipeline tests for the markdown plugins used by the site.

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
- Use `CHANGELOG.md` when you need exhaustive chronological repo history.

## Read Next

- [Docs Home](../index.md)
- [Glossary](../reference/glossary.md)
- [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md)
