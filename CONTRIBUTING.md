# Contributing

**Last Updated:** 2026-05-25

This file is the canonical maintainer workflow guide for ComfyUI StarChart.
Use `AGENTS.md` for startup-critical orientation. Use this file for deeper
maintainer playbooks, policy, verification placement, refresh flow, and CI
surface ownership.

## Quickstart

```bash
python -m pip install -r requirements.lock
python -m pip install -e .
npm ci
python -m unittest discover -s tests -v
npm run build
```

Windows rule:

- if `python --version` is not `3.11.x`, use `py -3.11` for repo Python commands
- prefer `py -3.11 scripts/verify/run_all.py` as the default maintainer gate on Windows

Default maintainer gate:

```bash
python scripts/verify/run_all.py
```

Advisory typing check:

```bash
python -m mypy
```

## What This Repository Is

This repo is a source-backed, version-pinned ComfyUI development reference.
It publishes:

- retained human docs under `src/content/docs/`
- extracted JSON artifacts under `references/raw/`
- published current/versioned artifacts under `public/artifacts/`
- one merged support index: `public/artifacts/docs-index.json`

Non-goals:

- official docs replacement
- community wiki
- package registry
- unbounded maintainer-handbook content inside the published docs tree

## Repository Map

| Path | Purpose | Hand-edit? |
|---|---|---|
| `src/content/docs/` | retained published docs surface | yes |
| `references/raw/` | canonical extracted JSON from pinned upstream snapshots | no |
| `references/docs-index-metadata.json` | curated tooling metadata merged into `docs-index.json` | yes |
| `references/snapshots/` | pinned upstream source files | no |
| `public/artifacts/current/` | published current canonical artifact copies | no |
| `public/artifacts/versions/` | bounded versioned artifact history | no |
| `public/artifacts/docs-index.json` | generated merged support index | no |
| `public/artifacts/schemas/` | checked-in published schemas | yes |
| `scripts/common/` | shared helper modules (refresh pipeline, git ops, subprocess, JSON, HTTP, surface constants) | yes |
| `scripts/extract/` | extractors | yes |
| `scripts/generate/` | generators and publication scripts | yes |
| `scripts/verify/` | blocking, supplemental, and advisory verifiers | yes |
| `tests/unit/` | unit tests for scripts | yes |
| `.github/workflows/` | CI, advisory replay, deployment, refresh/watch automation | yes |

## Final Retained Published Surface (30 pages)

This is the active published docs contract under `src/content/docs/`:

1. `src/content/docs/index.md`
2. `src/content/docs/start-here/author.md`
3. `src/content/docs/start-here/extension-developer.md`
4. `src/content/docs/start-here/service-integration.md`
5. `src/content/docs/start-here/tooling-builder.md`
6. `src/content/docs/start-here/artifact-consumer.md`
7. `src/content/docs/reference/machine-readable-artifacts.md`
8. `src/content/docs/reference/object-info.md`
9. `src/content/docs/reference/source-evidence-policy.md`
10. `src/content/docs/reference/writing-style-guide.md`
11. `src/content/docs/reference/doc-quality-checklist.md`
12. `src/content/docs/reference/version-pin-status.md`
13. `src/content/docs/reference/artifact-schema-version-migration.md`
14. `src/content/docs/reference/topic-scope.md`
15. `src/content/docs/architecture/overview.md`
16. `src/content/docs/architecture/execution-pipeline.md`
17. `src/content/docs/api/endpoints.md`
18. `src/content/docs/api/websocket.md`
19. `src/content/docs/api/prompt-submission.md`
20. `src/content/docs/api/history-queue.md`
21. `src/content/docs/hooks/javascript-hooks.md`
22. `src/content/docs/hooks/server-hooks.md`
23. `src/content/docs/hooks/extension-points.md`
24. `src/content/docs/custom-nodes/development-guide.md`
25. `src/content/docs/custom-nodes/node-structure.md`
26. `src/content/docs/custom-nodes/datatypes.md`
27. `src/content/docs/custom-nodes/registration.md`
28. `src/content/docs/deep-dives/execution-model-inversion.md`
29. `src/content/docs/deep-dives/workflow-json-schema.md`
30. `src/content/docs/deep-dives/registry-packaging-and-compatibility.md`

Do not add a new published page or section without meeting the new-surface
admission policy below.

## Decision Tree

| Task | Read first | Verify |
|---|---|---|
| Edit published docs prose | target page + `source-evidence-policy.md` + `writing-style-guide.md` | `python scripts/verify/cross_references.py` + `npm run build` |
| Update docs-index routing metadata | `references/docs-index-metadata.json` + `machine-readable-artifacts.md` | `python scripts/generate/generate_docs_index.py` + `python scripts/verify/docs_index_freshness.py` + `python scripts/verify/validate_schema.py` |
| Update extracted references | matching file in `references/raw/` + matching extractor | `python scripts/verify/validate_schema.py` + relevant narrow checks |
| Change maintainer Python tooling | `pyproject.toml` + affected `scripts/` modules | `python -m pip install -e .` + `python -m mypy` + `python -m unittest discover -s tests -v` + `python scripts/verify/run_all.py` |
| Add or change a verifier | existing verifier + matching tests + policy sections below | `python -m unittest discover -s tests -v` |
| Change CI workflow | target workflow + composite action + this file | `python -m unittest discover -s tests -v -p "test_run_all.py"` + `python scripts/verify/run_all.py` |
| Refresh upstream baselines | `scripts/refresh_snapshots.py` + refresh sections below | republish + delta summary + `python scripts/verify/run_all.py` |

## New Surface Admission Policy

Before adding any new published docs section, support artifact, generator, or
verifier, document and satisfy all of these:

1. clear user/maintainer need that existing surfaces cannot already cover
2. named owner for ongoing maintenance
3. explicit verification path
4. bounded contract and removal criteria
5. reason the new surface is better than extending an existing one

Stop rule:

- do not add a new published docs section just because content exists
- do not add a new support artifact when an existing artifact can absorb the data
- do not add a verifier without an intended blocking/advisory lifecycle

## Verifier Lifecycle Policy

Every verifier must have an explicit lifecycle decision.

Document for each verifier:

- purpose
- owner
- target surface
- false-positive tolerance
- placement: blocking, supplemental, or advisory
- promotion criteria
- demotion criteria
- removal criteria

Default rollout:

1. add the verifier with unit tests
2. wire it into advisory replay first if the signal is new or still being tuned
3. observe false positives and clarify docs/contracts
4. promote to blocking only when the signal is stable and maintainers can act on failures routinely

Current example:

- `scripts/verify/evidence_metadata_freshness.py` is advisory-first and must stay out of `run_all.py` until the retained page set proves stable under the rule

### Evidence metadata verifier contract

Current advisory failure criteria for `scripts/verify/evidence_metadata_freshness.py`:

- covered pages must include opening `**Evidence:**` and `**Last Updated:**` labels
- retained API, hooks, custom-node, architecture, object-info, and machine-readable-artifact pages must include an opening `**Baseline verification status:**` line
- retained deep-dive pages that currently make current-baseline claims must also include that opening baseline-status line
- non-current baseline exceptions must use one of the approved phrasings from `src/content/docs/reference/source-evidence-policy.md`

Do not expand this verifier's heuristic surface casually. Keep failures deterministic,
documented, and directly actionable.

## Generated vs Hand-Authored Boundaries

- hand-authored: `src/content/docs/`, `examples/`, top-level maintainer docs, checked-in schemas
- extracted: `references/raw/*.json` from `scripts/extract/`
- generated support artifact: `public/artifacts/docs-index.json` from `scripts/generate/generate_docs_index.py`
- published current/versioned canonical artifacts: `public/artifacts/current/` and `public/artifacts/versions/` from `scripts/generate/publish_reference_artifacts.py`
- published refresh evidence: `public/artifacts/refresh-provenance.json` from `scripts/refresh_snapshots.py`

Do not hand-edit generated or extracted outputs. Edit their sources and rerun the
owning script.

## Editing Published Docs

1. Read the target page and nearby linked pages.
2. Read:
   - `src/content/docs/reference/source-evidence-policy.md`
   - `src/content/docs/reference/writing-style-guide.md`
   - `src/content/docs/reference/doc-quality-checklist.md`
3. Keep claims tied to `references/snapshots/` or `docs.comfy.org`.
4. Verify:

```bash
python scripts/verify/cross_references.py
npm run build
```

## Updating Docs-Index Metadata

The repo now has one active support index only: `docs-index.json`.

Metadata source of truth:

- `references/docs-index-metadata.json`

Rules:

- target retained published pages only
- keep `recommended_next_reads` inside the retained 30-page surface
- keep `related_artifacts` limited to real published artifacts
- preserve nested shape under `tooling_metadata` in generated output; do not flatten those fields into top-level page keys

Regenerate and verify:

```bash
python scripts/generate/generate_docs_index.py
python scripts/verify/docs_index_freshness.py
python scripts/verify/validate_schema.py
```

## Updating Extracted References

1. Update pinned snapshot inputs under `references/snapshots/<date>/`, or run the refresh flow.
2. Run the matching extractor:

```bash
python scripts/extract/parse_server.py <path> --version <v> --commit <sha>
python scripts/extract/parse_hooks.py <paths...> --version <v> --commit <sha>
python scripts/extract/parse_node_api_schema.py <server> <io> <types> --version <v> --commit <sha>
```

3. Regenerate retained markdown if needed:

```bash
python scripts/generate/md_from_json.py
```

4. Verify:

```bash
python scripts/verify/validate_schema.py
python scripts/verify/cross_references.py
python scripts/verify/extraction_idempotency.py
```

## Adding or Changing a Verifier

1. Add `scripts/verify/<name>.py`
2. Add `tests/unit/test_<name>.py`
3. Decide blocking vs advisory vs supplemental before wiring it anywhere
4. Update this file's lifecycle section if the verifier is durable
5. Verify:

```bash
python -m unittest discover -s tests -v
```

Only place a verifier in `scripts/verify/run_all.py` and the blocking CI job in
the same change.

## Changing CI or Workflow Automation

- Keep `.github/workflows/ci.yml` and `scripts/verify/run_all.py` aligned step-for-step for the blocking path
- Prefer the shared composite setup action where it reduces real duplication
- Keep workflow-specific logic out of the composite action

Verify:

```bash
python -m unittest discover -s tests -v -p "test_run_all.py"
python scripts/verify/run_all.py
```

## Refreshing Upstream Baselines

Use `scripts/refresh_snapshots.py` when proving or updating the pinned baseline.

Expected flow:

1. run refresh with the requested core/frontend versions
2. note the backup path under `references/_refresh_backups/`
3. confirm `public/artifacts/refresh-provenance.json` truthfully records:
   - requested versions
   - resolved commits
   - backup location
   - runtime-object-info intent
   - next follow-up commands
   - the ordered `next_steps.recommended_follow_up_commands` list derived from the recorded provenance state
   - `published.canonical_artifacts_updated_by_refresh: false` and `published.delta_summary_updated_by_refresh: false` until those post-refresh steps are actually performed
4. follow the `Recommended follow-up commands:` block printed by `scripts/refresh_snapshots.py`
5. republish canonical artifacts
6. regenerate delta summary when comparing against the pre-refresh backup
7. rerun blocking verification

Commands:

```bash
python scripts/refresh_snapshots.py --core-version <version> --frontend-version <version>
python scripts/generate/publish_reference_artifacts.py
python scripts/verify/verify_artifact_integrity.py
python scripts/generate/generate_snapshot_delta_summary.py --old <backup-dir> --new references/raw --output public/artifacts/delta-summary.json
python scripts/verify/run_all.py
```

Version-pin follow-up docs to review after a refresh:

- `README.md`
- `src/content/docs/index.md`
- `src/content/docs/reference/version-pin-status.md`
- any retained docs page that cites the prior snapshot directory or version

## Verification Reference

Run narrow checks while iterating, then use the wrapper before handoff.

### Blocking path (`run_all.py` and main CI)

```bash
python -m unittest discover -s tests -v
npm test
python scripts/verify/python_style.py
python scripts/verify/cross_references.py
python scripts/verify/docs_index_freshness.py
python scripts/verify/validate_schema.py
python scripts/verify/verify_artifact_integrity.py
python scripts/verify/markdown_top_level_spacing.py
python scripts/verify/sidebar_navigation_coverage.py
npm run check
npm run build
python scripts/verify/rendered_links.py
```

### Supplemental

```bash
python scripts/verify/pipeline_smoke.py
python scripts/verify/shell_examples_syntax.py
```

### Advisory

```bash
python scripts/verify/stale_content.py
python scripts/verify/extraction_idempotency.py
python scripts/verify/upstream_pins.py
python scripts/verify/example_surface_integrity.py
python scripts/verify/evidence_metadata_freshness.py
python -m mypy
```

## Maintainer Failure-Path Quick Guide

- blocking CI failure: reproduce locally with `python scripts/verify/run_all.py`
- advisory replay failure: rerun the named advisory script locally
- schema failure: fix the source JSON or schema, not generated outputs by hand
- docs-index freshness failure: regenerate with `python scripts/generate/generate_docs_index.py`
- artifact-integrity failure: republish canonical artifacts and recheck the manifest/current copies
- rendered-links failure: rebuild and fix the source markdown or route mismatch

## Common Pitfalls

- `docs-index.json` is the only active support index; do not recreate `tooling-index.json`
- `references/docs-index-metadata.json` must only point at retained published pages
- do not hand-edit `public/artifacts/docs-index.json`
- keep JSON paths on forward slashes only
- `refresh-provenance.json` is published operator evidence, not a manifest-discovered canonical artifact
- `npm run build` may print the benign Starlight `Entry docs → 404 was not found.` warning
- do not let `AGENTS.md` and `CONTRIBUTING.md` drift into duplicate command inventories or conflicting CI descriptions

## Rollback Expectations

- doc-only change: restore the markdown files, then rerun `cross_references.py` and `npm run build`
- support-index change: restore `references/docs-index-metadata.json`, `generate_docs_index.py`, schema/docs text, then regenerate `public/artifacts/docs-index.json`
- canonical artifact publication change: restore the real source, rerun `publish_reference_artifacts.py`, then rerun integrity verification
- refresh failure: use the repo-local backup under `references/_refresh_backups/`, then republish and reverify

## Completion Standard

Do not say work is complete unless you can state:

- what changed
- which files changed
- which commands were run
- what those commands returned
- any remaining gaps or follow-up work
