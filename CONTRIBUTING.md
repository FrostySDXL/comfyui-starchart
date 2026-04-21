# Contributing

## Setup

```bash
python -m pip install -r requirements.txt
```

## Repo Conventions

- Keep Phase 1 pages as scaffolds unless you are intentionally replacing placeholders with researched content.
- Update both human docs and machine-readable references when behavior changes.
- Prefer small, verifiable changes.
- Do not add emojis or emoticons to docs.

## Verification Commands

Run the narrowest relevant checks first, then broader checks before completion:

```bash
python -m unittest discover -s tests
mkdocs build
```

If you change extraction or generation scripts, include the exact command and output in your handoff or PR notes.

## Documentation Rules

- Every content page should keep explicit primary sources.
- Replace placeholder text only when backed by source material.
- Keep generated artifacts aligned with their source JSON.

## Editorial Standards

Before submitting a documentation change, review it against:

1. **`docs/reference/source-evidence-policy.md`** -- confirms the page carries the
   correct evidence label and that claims are appropriately sourced.
2. **`docs/reference/writing-style-guide.md`** -- confirms the page mode, tone,
   section naming, and cross-linking follow repo conventions.

Use the checklist at `docs/reference/doc-quality-checklist.md` as a pre-commit
review step for doc-only changes.

## Doc Review Checklist

Before opening a PR that touches documentation, confirm:

1. **Page mode is correct** -- the page reads as one of: Reference, Tutorial,
   Decision Guide, Community Pattern Study, or Scaffold (see
   `docs/reference/writing-style-guide.md`)
2. **Evidence label is present and correct** -- the `**Evidence:**` line at the
   top of the page matches the actual source quality (see
   `docs/reference/source-evidence-policy.md`)
3. **Cross-links are intentional** -- links go to existing pages; "Read Next"
   blocks contain a small number of deliberate next-step links
4. **Docs build passes** -- `python -m mkdocs build` completes without errors
