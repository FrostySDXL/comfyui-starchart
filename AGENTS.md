# AGENTS.md

## Startup Sequence

1. Read `README.md`, this file, and relevant files in `docs/`, `references/`, `scripts/`, or `tests/`.
2. Confirm whether the task is scaffold work, documentation population, or script maintenance.
3. Run the smallest verification command that can prove the change.

## Repo Map

- `docs/` - MkDocs content, mostly scaffold pages in Phase 1
- `references/raw/` - machine-readable JSON reference data
- `references/snapshots/` - source snapshot templates and pinned source copies
- `scripts/extract/` - ad-hoc extractors for ComfyUI source
- `scripts/generate/` - Markdown generation from JSON references
- `tests/` - unit tests for helper scripts
- `examples/` - planned example content with placeholder READMEs

## Task Area Map

- API and hooks docs: `docs/api/`, `docs/hooks/`, `references/raw/`
- Custom node docs: `docs/custom-nodes/`
- Extension docs: `docs/extensions/`
- Generated reference pages: `docs/reference/`, `scripts/generate/`
- Extraction logic: `scripts/extract/`, `tests/unit/`

## Verification Expectations

- Script changes: `python -m unittest discover -s tests`
- MkDocs/nav/content changes: `mkdocs build`
- Before claiming completion, report exact commands run and their outcomes.

## Completion Standard

Do not say work is complete unless you can state:
- what changed
- which files changed
- which commands were run
- what those commands returned
- any remaining gaps or follow-up work
