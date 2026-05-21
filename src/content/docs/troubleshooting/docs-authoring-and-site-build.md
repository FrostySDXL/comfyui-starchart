---
title: "Docs Authoring and Site Build Troubleshooting"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-05-20
**Baseline verification status:** Verified against the current pinned baseline: core `v0.21.1`, frontend `v1.45.9`, snapshots `2026-05-18`.

## Scope

This page covers repo-local doc authoring confusion: what kind of file you are
editing, when to start from a template or helper, and which minimum checks must
pass before you call a doc change done.

## Problem: I am not sure whether this file is hand-authored, generated, extracted, or published

- Hand-authored pages live under `src/content/docs/` and most `examples/` paths.
- Generated markdown is produced from a source file and should be regenerated,
  not hand-edited.
- Extracted JSON lives under `references/raw/` and comes from extractor scripts.
- Published artifacts live under `public/artifacts/` and are copied there as part
  of the publication pipeline.

Read next:

- [Start Here: Docs Contributor](../start-here/docs-contributor.md)
- [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md)

## Problem: I am creating a new page and do not know where to start

For new docs pages, prefer `templates/docs/` or `scripts/new_doc.py` so the new
page starts with the repo's expected structure and labeling.

Read next:

- [Start Here: Docs Contributor](../start-here/docs-contributor.md)
- [Writing Style Guide](../reference/writing-style-guide.md)

## Problem: I changed docs and do not know the minimum verification bar

For doc-only changes, the minimum expected checks are:

 ```bash
 python scripts/verify/cross_references.py
 npm run build
 ```

Read next:

- [Doc Quality Checklist](../reference/doc-quality-checklist.md)
- [Start Here: Docs Contributor](../start-here/docs-contributor.md)
