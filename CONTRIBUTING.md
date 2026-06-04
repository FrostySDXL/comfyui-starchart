# Contributing

**Last Updated:** 2026-06-02

This file is the canonical maintainer workflow guide for ComfyUI StarChart.
Use `AGENTS.md` for startup-critical orientation. Use this file for deeper
maintainer playbooks, policy, verification placement, refresh flow, and CI
surface ownership.

## Quickstart

Use Python `3.11+` and Node.js `24.x` for repo/site work.

```bash
# Windows:
py -3.11 -m venv .venv
.venv\Scripts\activate

# Linux / macOS:
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip install -e .
npm ci
python -m unittest discover -s tests -v
npm run build
```

Windows bootstrap rule:

- create the venv once with `py -3.11 -m venv .venv`
- after activation, `python` resolves to the venv interpreter and version is always `3.11.x`
- prefer `python scripts/verify/run_all.py` as the default maintainer gate on Windows

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

## Final Retained Published Surface (29 pages)

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
11. `src/content/docs/reference/version-pin-status.md`
12. `src/content/docs/reference/artifact-schema-version-migration.md`
13. `src/content/docs/reference/topic-scope.md`
14. `src/content/docs/architecture/overview.md`
15. `src/content/docs/architecture/execution-pipeline.md`
16. `src/content/docs/api/endpoints.md`
17. `src/content/docs/api/websocket.md`
18. `src/content/docs/api/prompt-submission.md`
19. `src/content/docs/api/history-queue.md`
20. `src/content/docs/hooks/javascript-hooks.md`
21. `src/content/docs/hooks/server-hooks.md`
22. `src/content/docs/hooks/extension-points.md`
23. `src/content/docs/custom-nodes/development-guide.md`
24. `src/content/docs/custom-nodes/node-structure.md`
25. `src/content/docs/custom-nodes/datatypes.md`
26. `src/content/docs/custom-nodes/registration.md`
27. `src/content/docs/deep-dives/execution-model-inversion.md`
28. `src/content/docs/deep-dives/workflow-json-schema.md`
29. `src/content/docs/deep-dives/registry-packaging-and-compatibility.md`

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

Admission case: `websocket_events.json`

- Need: real-time clients, extension authors, and maintainers need source-backed
  event names, direction, and payload hints for execution monitoring that HTTP
  route artifacts cannot describe.
- Owner: maintainers of the canonical extraction and publication pipeline under
  `scripts/extract/`, `references/raw/`, and `public/artifacts/`.
- Verification: unit coverage for `scripts/extract/parse_websocket_events.py`,
  `scripts/verify/validate_schema.py`, artifact integrity checks, and the
  default `scripts/verify/run_all.py` gate when touching the artifact contract.
- Bounded contract and removal criteria: include only pinned-source-observed
  events, binary event constants, listener direction, and payload hints when
  source-backed. Remove or deprecate fields when upstream removes the source
  surface or the extractor can no longer prove the contract from retained
  snapshots.
- Why not extend an existing surface: websocket events are not HTTP routes, JS
  extension hooks, or node API schema fields; merging them into those artifacts
  would blur ownership and make real-time execution contracts harder to query.

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

## Published Artifact Version Retention

Treat `public/artifacts/versions/` as durable but bounded history.

- keep the current baseline
- keep the last 2 prior baselines
- keep any older baseline still referenced by active docs, delta artifacts,
  refresh-provenance records, or migration guidance

`references/_refresh_backups/` is temporary local working state for refresh
rollback/comparison. It is outside the durable published-history policy.

### Versioned Artifact Regeneration

Versioned artifacts under `public/artifacts/versions/` are keyed to a frozen
upstream source baseline (tag + commit + snapshot date). When extractors or
schemas change, a regeneration pass may update versioned artifacts to reflect
the current extraction logic applied to the same frozen source. This means:

- **Structural content** (sections, fields, shape) reflects the extractor
  version, not the historical extraction date. If the extractor learns a new
  section (e.g., `prompt_conditioning_surface`), that section will appear in
  regenerated versioned artifacts for earlier baselines.
- **The extracted source is frozen.** The pinned snapshot files under
  `references/snapshots/` that feed the extractor do not change for a given
  version key.
- **`extracted_date`** in the artifact metadata records when the extraction
  was run (operator local date), not the upstream release date.

This is a deliberate tradeoff: the artifacts are "what the current tooling
produces for this baseline" rather than a strict historical timestamp. If a
strict historical record is needed, compare against the pinned snapshot
source files directly.

## Editing Published Docs

1. Read the target page and nearby linked pages.
2. Read:
   - `src/content/docs/reference/source-evidence-policy.md`
   - `src/content/docs/reference/writing-style-guide.md`
   - the `Editorial Checklist` section in this file
3. Keep claims tied to `references/snapshots/` or `docs.comfy.org`.
4. Verify:

```bash
python scripts/verify/cross_references.py
npm run build
```

## Editorial Checklist

Use this checklist before marking any documentation page complete. Items marked
Required must pass before a page is merged. Recommended items should be
addressed unless there is a documented reason to defer them. Optional items are
best-effort polish checks.

### Page shape and mode

- [ ] Required: page mode is explicit and matches the content
- [ ] Required: the evidence label appears near the top of the page and is correct
- [ ] Required: the opening paragraph or two includes an honest scope statement

### Prose quality

- [ ] Recommended: sentences stay short and direct, with active voice where it helps
- [ ] Recommended: filler phrases are removed (`in order to`, `it is important to note that`, similar padding)
- [ ] Optional: wording is concrete rather than vague or inflated
- [ ] Optional: the opening avoids filler or repetition from adjacent docs

### Structure and navigation

- [ ] Optional: section order is intentional and fits the page mode
- [ ] Recommended: `Who This Page Is For` appears when the audience is not obvious
- [ ] Optional: decision guides include key takeaways or a short decision summary
- [ ] Recommended: the page ends with intentional `Read Next` or `Related Pages` links
- [ ] Optional: cross-links are navigational, not scattered incidental references
- [ ] Optional: no `see also` filler that adds little value

### Evidence and claims

- [ ] Required: no claim of official ComfyUI behavior appears without a citation from `docs.comfy.org` or a pinned upstream source
- [ ] Recommended: official versus community claims are clearly separated
- [ ] Recommended: repo-local policy/process pages use `Operational guidance` without implying source-backed ComfyUI behavior claims
- [ ] Required: after a snapshot refresh, baseline verification wording was reviewed; if the page is not fully current, the opening block says so explicitly
- [ ] Optional: source citations point to pinned snapshots or official docs where applicable
- [ ] Optional: `TODO` or `incomplete` markers are honest; incomplete pages use the Scaffold label
- [ ] Optional: words like `authoritative` or `source of truth` appear only when exact backing exists

### Build and links

- [ ] Required: `npm run build` passes without new errors
- [ ] Required: `references/` path mentions and navigational links resolve to valid targets
- [ ] Recommended: no broken or dangling links remain

### When to use this checklist

- before opening a PR that touches documentation
- before marking a doc page complete during a review session
- during the weekly doc review pass described in this file

This checklist is not a gate for draft or scaffold pages. Use it when you are
ready to declare that a page meets the repo's editorial standard.

## Updating Docs-Index Metadata

The repo now has one active support index only: `docs-index.json`.

Metadata source of truth:

- `references/docs-index-metadata.json`

Rules:

- target retained published pages only
- every retained published page must either carry `tooling_metadata` or be
  intentionally bare under the current policy
- the intentionally bare class is limited to governance, writing-policy,
  status, and scope-boundary pages; the current retained bare pages are
  `reference/source-evidence-policy.md`, `reference/writing-style-guide.md`,
  `reference/version-pin-status.md`, and `reference/topic-scope.md`
- keep `recommended_next_reads` inside the retained 29-page surface
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
python scripts/extract/parse_websocket_events.py <server> <main> <execution> <protocol> <progress> <app.ts> --version <v> --commit <sha>
```

3. Verify:

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
- `npm audit` is intentionally excluded from the blocking CI path and from
  `scripts/verify/run_all.py`. This repo has a small dependency surface and no
  current automation for dependency vulnerability scanning (Dependabot, Renovate,
  or advisory replay). This is an accepted gap for now; if dependency risk
  warrants it, add a non-blocking advisory signal rather than restoring
  `npm audit` to the blocking path.

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
python scripts/verify/snapshot_surface_coverage.py
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
python scripts/verify/run_all.py --skip-tests
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

## Verifier Inventory

This inventory covers the current direct verifier surfaces and the workflows that
run or replay them. Helper modules such as `schema_common.py`,
`schema_server.py`, `schema_hooks.py`, `schema_node_api.py`,
`schema_websocket_events.py`, and `published_schema_validation.py` support
these checks but are not standalone inventory rows.

### Blocking wrapper and blocking checks

| Verifier / workflow | Purpose | Scope | Blocking/advisory/manual | Unique signal | When to run directly |
|---|---|---|---|---|---|
| `scripts/verify/run_all.py` | Run the default maintainer gate in CI-aligned order | Whole repo blocking path | Blocking wrapper | Step-for-step local mirror of the main CI blocking job | Before handoff, before push, and after multi-surface changes |
| `python -m unittest discover -s tests -v` | Run Python unit coverage for scripts and generators | `tests/` and exercised Python modules | Blocking | Catches logic regressions before narrower verifiers run | Any Python tooling or docs-index generator change |
| `npm test` | Run Node-side tests | frontend/site test surface | Blocking | Only blocking signal for repo Node-side tests | Site or frontend utility changes |
| `scripts/verify/python_style.py` | Enforce Ruff lint and format checks | `scripts/`, `tests/` | Blocking | Bundles lint plus format drift into one Python gate | Any Python edit before broader verification |
| `scripts/verify/cross_references.py` | Validate repo-local `references/` mentions and JSON source paths | published docs plus `references/raw/*.json` metadata | Blocking | Checks repo-path truth without depending on site build output | Any docs edit that touches cited repo paths or extracted metadata |
| `scripts/verify/docs_index_freshness.py` | Detect stale checked-in `docs-index.json` | docs-index source pages, metadata, generated output | Blocking | In-memory regenerate-and-compare against committed artifact | After docs-index source or metadata changes |
| `scripts/verify/snapshot_surface_coverage.py` | Prevent incomplete snapshot source surfaces before extractors rely on them | current pinned core/frontend snapshots | Blocking once wired into `run_all.py`; lifecycle stays blocking while limited to required-file and import checks | Catches missing required source files such as `protocol.py` and `comfy_execution/progress.py` before artifacts lose source evidence | After snapshot refreshes or extractor source-surface changes |
| `scripts/verify/validate_schema.py` | Validate canonical and selected published/support JSON artifacts against schemas | `references/raw/*.json`, `public/artifacts/docs-index.json`, selected support artifacts | Blocking | Only schema gate spanning canonical raw artifacts plus checked-in published/support JSON | Any extractor, schema, or published JSON contract change |
| `scripts/verify/verify_artifact_integrity.py` | Confirm canonical raw artifacts match published current copies and manifest hashes | canonical artifact publication chain | Blocking | Hash-level canonical vs published integrity check | After republishing canonical artifacts or manifest-affecting changes |
| `scripts/verify/markdown_top_level_spacing.py` | Catch leading-space markdown that renders incorrectly | hand-authored docs markdown | Blocking | Prevents raw-markdown leakage caused by indentation drift | After docs prose or formatting edits |
| `scripts/verify/sidebar_navigation_coverage.py` | Ensure sidebar data matches the retained published docs tree | `src/site/sidebar-data.json` and `src/content/docs/` | Blocking | Detects missing nav entries, dead nav paths, and duplicates | After page additions, removals, or sidebar edits |
| `npm run check` | Run Astro type/content checks | site build configuration and content graph | Blocking | Framework-aware diagnostics beyond markdown-only checks | After content, config, or site-code changes |
| `npm run build` | Build the published Starlight site | full rendered docs site | Blocking | Produces the rendered output that downstream link verification depends on | After docs or site changes; always before rendered-links |
| `scripts/verify/rendered_links.py` | Verify internal links in built HTML resolve | `dist/` output | Blocking | Catches link rewrite and route-resolution bugs that source checks miss | After a successful build |

Lifecycle detail for `scripts/verify/snapshot_surface_coverage.py`: purpose is
to prevent snapshot refreshes from dropping source files that current extractors
depend on; owner is the maintainer of snapshot refresh and extractor pipelines;
target surface is the current pinned core/frontend snapshots and required import
paths; false-positive tolerance is low because missing required files can
silently degrade generated artifacts; placement is blocking while checks remain
limited to required files and import reachability; promotion is already satisfied
by stable required-file coverage in `run_all.py`; demote to advisory if the
check expands into heuristic source-quality scoring; remove only when extractor
source requirements are represented by a stricter manifest or replacement
verifier with equivalent coverage.

### Supplemental verifiers

| Verifier / workflow | Purpose | Scope | Blocking/advisory/manual | Unique signal | When to run directly |
|---|---|---|---|---|---|
| `python -m mypy` | Advisory typing pass for Python tooling | typed Python surfaces | Supplemental / advisory | Static type signal without blocking the default maintainer gate | Python refactors, interface changes, or before promoting stricter typing |
| `python scripts/verify/run_all.py --skip-tests` | Smoke the blocking wrapper without rerunning Python or Node tests | blocking pipeline minus Python/Node tests | Supplemental | Fastest way to exercise the Starlight-era blocking path end-to-end without a wrapper script | Iterating on blocking verifiers or site build behavior |
| `scripts/verify/shell_examples_syntax.py` | Parse-check repo shell examples with `bash -n` | `examples/**/*.sh` | Supplemental | Only direct syntax check for shell example scripts | After adding or editing shell examples |

### Advisory verifiers and replay workflows

| Verifier / workflow | Purpose | Scope | Blocking/advisory/manual | Unique signal | When to run directly |
|---|---|---|---|---|---|
| `scripts/verify/stale_content.py` | Scan for stale markers and aging content | docs plus extracted JSON | Advisory | Finds `TODO`/`TBD`-style drift and old `Last Updated` markers | Cleanup sweeps, doc review passes, or before promoting pages |
| `scripts/verify/extraction_idempotency.py` | Re-run extractors against pinned inputs and compare outputs | extractor determinism for `references/raw/*.json` | Advisory | Only direct determinism check for extraction reproducibility | Extractor changes or refresh-pipeline review |
| `scripts/verify/upstream_pins.py` | Confirm pinned tags and commits still resolve upstream | upstream pin validity for canonical JSON metadata | Advisory | External trust check with cached GitHub API resolution | Scheduled pin health review or after suspicious upstream changes |
| `scripts/verify/example_surface_integrity.py` | Validate example family structure and routed example references | `examples/` plus routed start-here docs | Advisory | Checks example directory completeness and routed example paths together | Example-surface edits or start-here routing updates |
| `scripts/verify/evidence_metadata_freshness.py` | Enforce opening evidence metadata discipline on retained pages | selected published docs pages | Advisory | Only verifier that checks allowed baseline-status wording patterns directly | Docs policy changes or refreshes affecting evidence blocks |
| `.github/workflows/advisory-checks.yml` | Replay advisory scripts as blocking on schedule/manual dispatch | weekly/manual advisory escalation path | Advisory workflow | Converts the non-blocking advisory script set into a durable scheduled gate | Use the workflow when maintainers want a blocking replay outside push/PR CI |

### Runtime-specific verifiers and workflows

| Verifier / workflow | Purpose | Scope | Blocking/advisory/manual | Unique signal | When to run directly |
|---|---|---|---|---|---|
| `scripts/verify/runtime_smoke.py` | Probe a live ComfyUI instance for basic API readiness and prompt submission | live runtime endpoints | Manual runtime-specific | Only repo-local verifier that exercises real HTTP runtime behavior directly | When validating a running ComfyUI instance or runtime-facing examples |
| `scripts/verify/wait_for_runtime.py` | Poll a live endpoint until JSON readiness | live runtime startup/readiness | Manual runtime-specific | Purpose-built readiness gate for headless runtime workflows | Before runtime capture steps that require a live ComfyUI server |
| `.github/workflows/runtime-smoke.yml` | Run `runtime_smoke.py` against a user-supplied ComfyUI URL | manual live-runtime smoke workflow | Manual runtime-specific workflow | Reproducible GitHub Actions wrapper for runtime smoke without local setup | When maintainers need remote/manual runtime verification evidence |
| `.github/workflows/headless-runtime-metadata.yml` | Launch pinned ComfyUI headlessly, wait for readiness, capture runtime metadata, and optionally build a hybrid schema artifact | pinned runtime metadata capture | Manual runtime-specific workflow | Only workflow that clones the pinned runtime and captures fresh `object_info` evidence | When runtime metadata or hybrid-schema evidence is needed |

### Workflow orchestration surfaces

| Verifier / workflow | Purpose | Scope | Blocking/advisory/manual | Unique signal | When to run directly |
|---|---|---|---|---|---|
| `.github/workflows/ci.yml` | Main CI entrypoint for blocking, supplemental, advisory-in-CI, and optional refresh jobs | push/PR/manual repo verification | Workflow orchestration | Shows how blocking, supplemental, and non-blocking advisory checks are staged in CI | Inspect when changing verifier placement or CI parity with `run_all.py` |
| `.github/workflows/deploy-pages.yml` | Publish artifacts, rerun the blocking wrapper, and deploy the built site | deploy pipeline | Workflow orchestration | Couples publication and full blocking verification before Pages deploy | Inspect when changing deployment or publication flow |
| `.github/workflows/upstream-watch.yml` | Check upstream versions and open/update a tracking issue | upstream monitoring automation | Workflow orchestration | Tracks refresh opportunities rather than repo correctness | Inspect when changing upstream-watch automation or issue workflow |

## Maintainer Failure-Path Quick Guide

- blocking CI failure: reproduce locally with `python scripts/verify/run_all.py`
- advisory replay failure: rerun the named advisory script locally
- schema failure: fix the source JSON or schema, not generated outputs by hand
- docs-index freshness failure: regenerate with `python scripts/generate/generate_docs_index.py`
- artifact-integrity failure: republish canonical artifacts and recheck the manifest/current copies
- rendered-links failure: rebuild and fix the source markdown or route mismatch

## Common Pitfalls

- all repo Python commands must be run from an activated venv; running them outside the venv will use a different Python version and may fail mypy or unit tests
- `docs-index.json` is the only active support index; do not recreate `tooling-index.json`
- `references/docs-index-metadata.json` must only point at retained published pages
- do not hand-edit `public/artifacts/docs-index.json`
- keep JSON paths on forward slashes only
- `refresh-provenance.json` is published operator evidence, not a manifest-discovered canonical artifact
- `npm run build` may print the benign Starlight `Entry docs -> 404 was not found.` warning
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
