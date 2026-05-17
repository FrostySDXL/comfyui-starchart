---
title: "Start Here: Docs Contributor"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-04-30

## Who This Path Is For

You want to improve, correct, or expand the documentation in this repository.
This includes:

- fixing errors in existing pages
- adding new reference or tutorial pages
- updating extracted references after a snapshot refresh
- contributing examples or decision guides

**Prerequisites:** you are ready to follow the editorial references first and
run the minimum verification that matches your change.

## Start With the Editorial Reference Stack

Read these files in this order before writing or editing prose documentation:

1. [`source-evidence-policy.md`](../reference/source-evidence-policy.md) -- evidence levels and labeling rules
2. [`writing-style-guide.md`](../reference/writing-style-guide.md) -- page modes, sentence style, section naming
3. [`doc-quality-checklist.md`](../reference/doc-quality-checklist.md) -- required, recommended, and optional checks

Use `CONTRIBUTING.md` only when your change crosses into maintainer-owned
surfaces such as scripts, CI, extracted data, published artifacts, or other
repo-local workflow material.

## How to Pick the Right Page Mode

Every page must have one primary mode. Use the decision matrix in
[`writing-style-guide.md`](../reference/writing-style-guide.md) to choose:

| If you are writing... | Use mode |
|-----------------------|----------|
| API routes, hooks, or schemas | Reference |
| Step-by-step instructions | Tutorial |
| Option comparisons | Decision Guide |
| External project patterns | Community Pattern |
| A placeholder for future work | Scaffold |

Do not mix modes on the same page.

Return to the checklist before marking any page complete.

## What Verification to Run for Doc-Only Changes

Run these commands after editing documentation:

```bash
python scripts/verify/cross_references.py
npm run build
```

If you added or changed a verification script or extractor, also run:

```bash
python -m unittest discover -s tests -v
```

If your work crosses into maintainer workflow surfaces such as
`scripts/verify/`, `.github/workflows/`, or repo-local operational guidance,
use targeted checks while iterating and then follow the authoritative
maintainer verification path in `CONTRIBUTING.md`, including
`python scripts/verify/run_all.py` before handoff.

## Preferred New-Page Workflow

When you are creating a new page, start with the scaffold tool instead of pasting an old page by hand:

```bash
python scripts/new_doc.py --output src/content/docs/tutorials/my-topic.md --mode tutorial --title "My Topic" --primary-source "docs.comfy.org/<page-or-section>"
```

Keep the output under `src/content/docs/`, and use the mode that matches the folder when practical. For example, tutorials usually belong under `src/content/docs/tutorials/` or `src/content/docs/how-to/`, community pattern studies usually belong under `src/content/docs/extensions/` or `src/content/docs/ecosystem/`, and reference pages usually belong under `src/content/docs/reference/`, `src/content/docs/api/`, `src/content/docs/hooks/`, or `src/content/docs/custom-nodes/`.

If the script rejects a mode/path combination that you still want intentionally, fix the path first or use `--allow-path-mismatch` with a short note in your PR or handoff.

## Where Generated vs Hand-Authored Boundaries Matter

- **Hand-authored:** pages under `src/content/docs/`, `examples/`, and editorial reference files.
- **Generated:** `src/content/docs/ecosystem/map.md` (driven by `references/community/ecosystem_packages.json`).
- **Extracted:** JSON files under `references/raw/` (driven by `scripts/extract/`).
- **Published:** files under `public/artifacts/` (produced by `scripts/generate/publish_reference_artifacts.py`). This includes the manifest, current and versioned artifact copies, and the published `delta-summary.json` support artifact.

Edit generated or extracted output only by changing its source and rerunning the
generator or extractor. Never hand-edit `src/content/docs/ecosystem/map.md` directly.

## First Practical Step

Open `src/content/docs/reference/writing-style-guide.md`, read the Page-Type Decision
Matrix, and identify the mode of the page you plan to edit or create. Write
the mode and evidence label in a draft before adding body content.

## Read Next

- [Writing Style Guide](../reference/writing-style-guide.md)
- [Source Evidence Policy](../reference/source-evidence-policy.md)
- [Doc Quality Checklist](../reference/doc-quality-checklist.md)
- `CONTRIBUTING.md` in the repo root when your change crosses into maintainer-owned surfaces

If you are blocked on generated versus hand-authored boundaries or the minimum
doc verification bar, see
[Docs Authoring and Site Build Troubleshooting](../troubleshooting/docs-authoring-and-site-build.md).
