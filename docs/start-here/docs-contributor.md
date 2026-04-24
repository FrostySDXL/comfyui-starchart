# Start Here: Docs Contributor

**Evidence:** Operational guidance
**Last Updated:** 2026-04-24

## Who This Path Is For

You want to improve, correct, or expand the documentation in this repository.
This includes:

- fixing errors in existing pages
- adding new reference or tutorial pages
- updating extracted references after a snapshot refresh
- contributing examples or decision guides

**Prerequisites:** you have read `AGENTS.md` and can run the verification scripts.

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

## When to Read the Editorial References

Read these files in this order before writing or editing prose documentation:

1. [`source-evidence-policy.md`](../reference/source-evidence-policy.md) -- evidence levels and labeling rules
2. [`writing-style-guide.md`](../reference/writing-style-guide.md) -- page modes, sentence style, section naming
3. [`doc-quality-checklist.md`](../reference/doc-quality-checklist.md) -- required, recommended, and optional checks

Return to the checklist before marking any page complete.

## What Verification to Run for Doc-Only Changes

Run these commands after editing documentation:

```bash
python scripts/verify/cross_references.py
python -m mkdocs build
```

If you added or changed a verification script or extractor, also run:

```bash
python -m unittest discover -s tests -v
```

## Where Generated vs Hand-Authored Boundaries Matter

- **Hand-authored:** pages under `docs/`, `examples/`, and editorial reference files.
- **Generated:** `docs/ecosystem/map.md` (driven by `references/community/ecosystem_packages.json`).
- **Extracted:** JSON files under `references/raw/` (driven by `scripts/extract/`).

Edit generated or extracted output only by changing its source and rerunning the
generator or extractor. Never hand-edit `docs/ecosystem/map.md` directly.

## First Practical Step

Open `docs/reference/writing-style-guide.md`, read the Page-Type Decision
Matrix, and identify the mode of the page you plan to edit or create. Write
the mode and evidence label in a draft before adding body content.

## Read Next

- [Writing Style Guide](../reference/writing-style-guide.md)
- [Source Evidence Policy](../reference/source-evidence-policy.md)
- [Doc Quality Checklist](../reference/doc-quality-checklist.md)
