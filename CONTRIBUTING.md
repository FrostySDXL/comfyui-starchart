# Contributing

**Last Updated:** 2026-07-23

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
python -m pip install --require-hashes -r requirements.lock
python -m pip install -e .
npm ci
python -m unittest discover -s tests -v
npm run build
```

Windows bootstrap rule:

- create the venv once with `py -3.11 -m venv .venv`
- after activation, `python` resolves to the venv interpreter and version is always `3.11.x`
- install Python dependencies from the hash-pinned `requirements.lock` with
  `python -m pip install --require-hashes -r requirements.lock`
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

### Non-Goal Addendum

`CONTRIBUTING.md` is canonical for maintainer scope decisions. The root
`README.md` mirrors these four public non-goals exactly so public orientation and
maintainer policy stay aligned.

| Rejected feature class | Rationale |
|---|---|
| official docs replacement | This repo is a pinned companion reference; authoritative official guidance remains at `docs.comfy.org`. |
| community wiki | The published docs surface is retained, curated, and source-backed rather than open-ended community aggregation. |
| package registry | Artifact discovery and examples stay bounded; this repo does not index, rank, or distribute ComfyUI packages. |
| unbounded maintainer-handbook content inside the published docs tree | Workflow-heavy maintainer procedures belong in repo-local guidance, especially `CONTRIBUTING.md` and `AGENTS.md`. |

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
| Add or change examples | target example README + `references/example-validation-matrix.json` + relevant verifier/test files | `python scripts/verify/example_surface_integrity.py` + `python scripts/verify/example_validation_matrix.py` + targeted tests |
| Change CI workflow | target workflow + composite action + this file | `python -m unittest discover -s tests -v -p "test_run_all.py"` + `python scripts/verify/run_all.py` |
| Refresh upstream baselines | `scripts/refresh_snapshots.py` + refresh sections below | republish + delta summary + `python scripts/verify/delta_summary_integrity.py` + `python scripts/verify/run_all.py` |

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

Admission case: `manifest.json`

- Need: tooling consumers need one discovery entrypoint for canonical artifact
  URLs, versions, commits, schemas, and checksums instead of hardcoding paths.
- Owner: maintainers of artifact publication under
  `scripts/generate/publish_reference_artifacts.py` and canonical artifacts under
  `references/raw/` and `public/artifacts/current/`.
- Verification: `python scripts/verify/validate_schema.py`,
  `python scripts/verify/published_schema_validation.py`, and
  `python scripts/verify/verify_artifact_integrity.py` must prove the schema and
  manifest checksums match the published files.
- Bounded contract and removal criteria: the manifest is a discovery index, not a
  package registry. If richer discovery metadata is needed, extend the manifest
  under a new `artifact_schema_version` rather than redefining fields in place.
  Removal requires dropping `manifest.json` from publication and schema
  validation wiring in the same change.
- Why not extend an existing surface: `docs-index.json`, `delta-summary.json`,
  and `refresh-provenance.json` each describe routing, comparison, or operator
  evidence; the manifest is the only artifact that enumerates the canonical set
  with checksums for external tooling.

Admission case: `docs-index.json`

- Need: tooling and agent consumers need a bounded page-level routing aid without
  scraping the built site or treating published prose as full-text search.
- Owner: maintainers of `references/docs-index-metadata.json`,
  `scripts/generate/generate_docs_index.py`, and the retained docs surface.
- Verification: `python scripts/generate/generate_docs_index.py`,
  `python scripts/verify/docs_index_freshness.py`, and
  `python scripts/verify/validate_schema.py` must pass after source or metadata
  changes.
- Bounded contract and removal criteria: include only conservative page facts and
  curated tooling metadata for retained published pages. Remove only if routing
  metadata is retired or replaced by an equivalent documented support artifact.
- Why not extend an existing surface: canonical extracted artifacts describe
  ComfyUI source surfaces, not repo-local page routing; embedding page routing in
  them would blur artifact ownership.

Admission case: `delta-summary.json`

- Need: maintainers and artifact consumers need deterministic baseline-to-baseline
  comparison evidence after refreshes without manually diffing every canonical
  artifact.
- Owner: maintainers of `scripts/generate/generate_snapshot_delta_summary.py` and
  refresh artifact review.
- Verification: `python scripts/generate/generate_snapshot_delta_summary.py` with
  the recorded old/new paths, `python scripts/verify/delta_summary_integrity.py`,
  and `python scripts/verify/validate_schema.py` must pass.
- Bounded contract and removal criteria: the summary reports structural
  add/remove/change evidence for canonical artifacts only. Remove only if refresh
  comparison evidence is no longer published or is replaced by an equivalent
  generated artifact.
- Why not extend an existing surface: `manifest.json` discovers current
  artifacts, and `refresh-provenance.json` records operator inputs; neither is a
  deterministic structural comparison output.

Admission case: `refresh-provenance.json`

- Need: maintainers need durable operator evidence for the latest refresh run,
  including requested versions, resolved commits, backup path, and recommended
  follow-up commands.
- Owner: maintainers of `scripts/refresh_snapshots.py` and refresh procedure
  documentation.
- Verification: rerun the refresh command when updating provenance, then run the
  printed follow-up sequence and `python scripts/verify/validate_schema.py`.
- Bounded contract and removal criteria: this is operator evidence for the latest
  refresh, not a canonical artifact manifest. Remove only if refreshes no longer
  publish operator evidence or a replacement provenance artifact is admitted.
- Why not extend an existing surface: canonical artifacts describe extracted
  ComfyUI surfaces, while the manifest describes published files; refresh
  provenance captures operator process state that belongs in a separate record.

Admission case: `example-validation-matrix.json`

- Need: maintainers need a compact, examples-only evidence map so example READMEs
  cannot self-certify accuracy without static checks, offline tests,
  pinned-source evidence, caveats, or opt-in runtime smoke commands.
- Owner: maintainers of `examples/`, `scripts/verify/example_surface_integrity.py`,
  `scripts/verify/example_validation_matrix.py`, and runtime-facing example docs.
- Verification: `python scripts/verify/example_validation_matrix.py`,
  `python scripts/verify/example_surface_integrity.py`, and targeted example unit
  tests must pass after example or matrix changes.
- Bounded contract and removal criteria: the matrix records validation evidence
  tiers for repo-local example families only. It is not a package registry,
  quality ranking, or live runtime result log. Remove only if examples are
  retired or a stricter examples-only validation artifact replaces it.
- Why not extend an existing surface: docs-index routing metadata describes
  published pages, while canonical artifacts describe extracted ComfyUI source
  surfaces. Example validation status belongs beside maintainer evidence, not in
  generated published artifacts.

## Verifier Lifecycle Policy

Every verifier must have an explicit lifecycle decision.

The machine-readable source for complete verifier lifecycle records is
`references/verifier-lifecycle.json`. `CONTRIBUTING.md` remains the human policy
surface and inventory; do not hand-maintain long lifecycle paragraphs when the
manifest can carry the durable record.

Document for each verifier or workflow record:

- purpose
- owner
- target surface
- false-positive tolerance
- placement: blocking, supplemental, advisory, manual, or workflow
- promotion criteria
- demotion criteria
- removal criteria
- `last_reviewed` as an ISO-8601 `YYYY-MM-DD` date, updated whenever maintainers
  re-review lifecycle fit

`false_positive_tolerance` is a closed object, not a free-form label:

- `level`: one of `none`, `low`, `medium`, or `high`
- `justification`: one or two sentences explaining why that level is acceptable

Use this scale consistently:

| Level | Meaning |
|---|---|
| `none` | A single false positive fails the lifecycle standard; deterministic contract checks belong here. |
| `low` | Up to roughly 1 false positive per 100 reports is acceptable during normal maintenance. |
| `medium` | Up to roughly 5 false positives per 100 reports is acceptable for policy-heavy or transition-sensitive advisory signals. |
| `high` | Up to roughly 10 false positives per 100 reports is acceptable for live-runtime, external-upstream, or operator-triaged signals. |

Default rollout:

1. add the verifier with unit tests
2. wire it into advisory replay first if the signal is new or still being tuned
3. observe false positives and clarify docs/contracts
4. promote to blocking only when the signal is stable and maintainers can act on failures routinely

Current example:

- `scripts/verify/evidence_metadata_freshness.py` is advisory-first and must stay out of `run_all.py` until the retained page set proves stable under the rule

Current governance verifier decision:

- `scripts/verify/governance_lifecycle.py` is advisory-first and replayed by
  `.github/workflows/advisory-checks.yml`. Do not wire it into `run_all.py`
  until the promotion thresholds in this file are satisfied and recorded in the
  lifecycle manifest.

### Evidence metadata verifier contract

Current advisory failure criteria for `scripts/verify/evidence_metadata_freshness.py`:

- covered pages must include opening `**Evidence:**` and `**Last Updated:**` labels
- retained API, hooks, custom-node, architecture, object-info, and machine-readable-artifact pages must include an opening `**Baseline verification status:**` line
- retained deep-dive pages that currently make current-baseline claims must also include that opening baseline-status line
- non-current baseline exceptions must use one of the approved phrasings from `src/content/docs/reference/source-evidence-policy.md`

Do not expand this verifier's heuristic surface casually. Keep failures deterministic,
documented, and directly actionable.

### Baseline-review status for routed pages

Routed pages are retained when their opening evidence block and baseline status
accurately describe the review state. Do not maintain a separate stale-page
backlog unless a current page explicitly declares partial or non-current review.

When re-reviewing a routed page against a new pinned baseline, update these
surfaces together:

- the page `**Last Updated:**` line
- the page `**Baseline verification status:**` line
- any source paths or commit references in the page body
- `references/docs-index-metadata.json` when routing metadata changes
- `public/artifacts/docs-index.json` by running
  `python scripts/generate/generate_docs_index.py`

Generated docs-index tooling metadata emits `metadata_reviewed_at` and
`metadata_baseline` from the current pinned artifact baseline when a page entry
does not override those fields explicitly.

## Generated vs Hand-Authored Boundaries

- hand-authored: `src/content/docs/`, `examples/`, top-level maintainer docs, checked-in schemas
- extracted: `references/raw/*.json` from `scripts/extract/`
- generated support artifact: `public/artifacts/docs-index.json` from `scripts/generate/generate_docs_index.py`
- published current/versioned canonical artifacts: `public/artifacts/current/` and `public/artifacts/versions/` from `scripts/generate/publish_reference_artifacts.py`
- published refresh evidence: `public/artifacts/refresh-provenance.json` from `scripts/refresh_snapshots.py`

Do not hand-edit generated or extracted outputs. Edit their sources and rerun the
owning script.

### Schema closure exceptions

Default schema policy is permissive for extracted source-backed objects: use
`additionalProperties: true` unless there is a documented maintenance reason to
close a narrow record shape. Intentional closed-record exceptions currently are:

| Schema | Closed record reason |
|---|---|
| `public/artifacts/schemas/websocket_events.schema.json` | Closes `metadata.commits` so the two-component core/frontend commit record cannot silently grow ambiguous repository keys. |
| `public/artifacts/schemas/node_api_schema.schema.json` | Closes each `node_flags` item so flag metadata remains a stable finite record. |
| `public/artifacts/schemas/manifest.schema.json` | Closes the discovery object, schema map, artifact map, source records, and checksum-bearing artifact records so canonical discovery cannot silently grow registry-like fields. |
| `public/artifacts/schemas/docs-index.schema.json` | Closes page and tooling-metadata records so the routing support index stays bounded to documented page facts and curated task hints. |
| `public/artifacts/schemas/delta-summary.schema.json` | Closes comparison, section, and entry summary records so generated delta evidence cannot grow ambiguous ad hoc fields. |

Do not add another `additionalProperties: false` schema object without recording
the closed-record reason here or in a more specific published schema policy.

## Published Artifact Version Retention

Treat `public/artifacts/versions/` as durable but bounded history.

- keep the current baseline
- keep the last 2 prior baselines
- keep any older baseline still referenced by active docs, delta artifacts,
  refresh-provenance records, or migration guidance

`references/_refresh_backups/` is temporary local working state for refresh
rollback/comparison. It is outside the durable published-history policy.

### Refresh backup retention

Keep the latest `_refresh_backups/raw_<timestamp>/` backup for the active refresh
until `public/artifacts/delta-summary.json` has been regenerated and reviewed.
Older backups may be deleted manually after confirming they are not referenced by
`public/artifacts/refresh-provenance.json`, `public/artifacts/delta-summary.json`,
or an open execution log entry.

Do not add automatic deletion in the first pass. If cleanup automation is added
later, make it opt-in and dry-run first, and require the command to print the
referencing provenance/delta-summary check before deleting anything.

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

### Versioned artifact completeness decisions

`scripts/verify/versioned_artifact_completeness.py` is advisory-first and
classifies every directory under `public/artifacts/versions/` in sorted
`version_key` order.

Current decision table:

| Version key | Classification | Decision |
|---|---|---|
| `core-v0.21.1_frontend-v1.45.9_2026-05-18` | `legacy-pre-websocket-events` | Retain as a documented legacy exception unless source-backed regeneration is needed. |
| `core-v0.22.0_frontend-v1.45.12_2026-05-21` | `legacy-pre-websocket-events` | Retain as a documented legacy exception unless source-backed regeneration is needed. |
| `core-v0.23.0_frontend-v1.46.6_2026-06-01` | `legacy-pre-websocket-events` | Retain as a documented legacy exception unless source-backed regeneration is needed. |
| `core-v0.23.0_frontend-v1.46.6_2026-06-03` | `retained-complete` | Retain as a complete historical baseline. |
| `core-v0.24.0_frontend-v1.46.14_2026-06-13` | `retained-complete` | Retain as a complete historical baseline. |
| `core-v0.26.0_frontend-v1.47.5_2026-06-26` | `retained-complete` | Retain as a complete historical baseline. |
| `core-v0.28.0_frontend-v1.48.4_2026-07-23` | `current-required-complete` | Keep as the current canonical versioned artifact set. |

The 2026-04 empty legacy placeholders were removed after confirming they had no
tracked artifact files and no active manifest, docs, or provenance references.
Do not backfill legacy versioned directories without a later explicit
policy/action change. Current and retained-complete version directories must
contain `server_endpoints.json`, `js_hooks.json`, `node_api_schema.json`, and
`websocket_events.json`; the advisory verifier parses, schema-validates, and
hash-verifies those current/retained-complete JSON files. Current versioned
artifact hashes must match the corresponding `sha256` values in
`public/artifacts/manifest.json`. Retained-complete historical artifact hashes
must match the deterministic expected-hash table in
`scripts/verify/versioned_artifact_completeness.py`.

Retained-complete historical artifacts are validated against the current
checked-in schemas under `public/artifacts/schemas/`. If a schema hardening makes
an intentionally retained baseline fail, do not weaken the verifier casually;
record the maintenance decision, either regenerate the baseline from pinned
sources or add an explicit lifecycle exception with the reason.

When adding or intentionally republishing a retained-complete baseline, update
`EXPECTED_RETAINED_COMPLETE_HASHES` in the same change:

1. Regenerate or copy the complete versioned artifact directory.
2. For each required JSON artifact in that directory, compute the normalized
   hash with `compute_textual_json_sha256` from `scripts/common/json_utils.py`.
3. Add the new `version_key` entry and artifact hashes to
   `scripts/verify/versioned_artifact_completeness.py`.
4. Run `python scripts/verify/versioned_artifact_completeness.py` and the
   matching unit test file before publishing the baseline.

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
  `scripts/verify/run_all.py`. Dependency risk is handled by Dependabot for pip,
  npm, and GitHub Actions plus the scheduled/manual
  `.github/workflows/dependency-advisory.yml` workflow, which runs npm and Python
  advisory audits outside push/PR blocking CI.
- Pin external GitHub Actions to full commit SHAs rather than moving major tags.
  Dependabot's `github-actions` ecosystem entry is the maintained update path
  for those pinned workflow dependencies.

Verify:

```bash
python -m unittest discover -s tests -v -p "test_run_all.py"
python scripts/verify/run_all.py
```

## CHANGELOG Maintenance Policy

Owner: maintainers of repo history and release notes.

Add a `CHANGELOG.md` entry for meaningful changes to any of these surfaces:

- published docs surface
- artifact contracts
- verifiers
- workflows
- refresh baselines
- examples
- package metadata
- repo identity

Selectivity threshold: exclude routine typo-only edits and generated-only churn
unless the change alters a documented contract, published surface, verification
expectation, or release-facing behavior.

Version bump trigger: bump `package.json` or `pyproject.toml` only when the repo
or tooling surface maturity changes. Otherwise, dated changelog entries are
enough.

Cadence: update the changelog during release, baseline, policy, or surface-change
batches. Do not require a changelog entry for every commit. Git history remains
the exhaustive record; `CHANGELOG.md` is the curated maintainer-facing summary.

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

Deployment does not regenerate canonical artifacts. The Pages workflow verifies
and publishes the generated artifact tree already committed under
`public/artifacts/`; run `publish_reference_artifacts.py` locally as a maintainer
step before commit when the canonical raw artifacts or pinned baseline change.

Commands:

```bash
python scripts/refresh_snapshots.py --core-version <version> --frontend-version <version>
python scripts/generate/publish_reference_artifacts.py
python scripts/verify/verify_artifact_integrity.py
python scripts/generate/generate_snapshot_delta_summary.py --old <backup-dir> --new references/raw --output public/artifacts/delta-summary.json
python scripts/verify/delta_summary_integrity.py
python scripts/verify/run_all.py
```

Version-pin follow-up docs to review after a refresh:

- `README.md`
- `src/content/docs/index.md`
- `src/content/docs/reference/version-pin-status.md`
- any retained docs page that cites the prior snapshot directory or version

## Verification Reference

Run narrow checks while iterating, then use the wrapper before handoff.

### Frontend test boundaries

Current site-navigation coverage is intentionally utility and rendered-output
based: Node-side markdown/sidebar tests, `npm run check`, `npm run build`, and
`python scripts/verify/rendered_links.py`. Browser-level navigation tests
(Playwright or equivalent) are deferred until a concrete visual regression or
interactive navigation requirement exists.

`tsconfig.json` intentionally excludes `tests/` because current Node tests are
`.mjs` runtime tests executed by `npm test`, not TypeScript source checked by
Astro. Revisit this boundary if tests migrate to TypeScript or if a JavaScript
lint/type verifier is admitted under the new-surface policy.

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
python scripts/verify/delta_summary_integrity.py
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
python scripts/verify/example_validation_matrix.py
```

### Advisory

```bash
python scripts/verify/stale_content.py
python scripts/verify/extraction_idempotency.py
python scripts/verify/upstream_pins.py
python scripts/verify/example_surface_integrity.py
python scripts/verify/evidence_metadata_freshness.py
python scripts/verify/docs_index_unknown_routes.py
python scripts/verify/provenance_chain_integrity.py
python scripts/verify/versioned_artifact_completeness.py
python scripts/verify/site_base_consistency.py
python scripts/verify/governance_lifecycle.py
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
| `scripts/verify/delta_summary_integrity.py` | Confirm `delta-summary.json` covers every canonical artifact section and no stale sections | `public/artifacts/delta-summary.json` against `CANONICAL_ARTIFACTS` | Blocking | Catches artifact-set drift when a canonical artifact is added, removed, or omitted from the delta summary | After regenerating delta summaries or changing canonical artifact membership |
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

Lifecycle detail for `scripts/verify/delta_summary_integrity.py`: purpose is to
prevent canonical artifact membership from drifting away from the published delta
summary; owner is the maintainer of artifact generation and publication tooling;
target surface is `public/artifacts/delta-summary.json` compared with
`scripts.generate.generate_snapshot_delta_summary.CANONICAL_ARTIFACTS`;
false-positive tolerance is low because missing sections make refresh evidence
misleading; placement is blocking because the check is deterministic and cheap;
promotion is already satisfied by unit coverage and `run_all.py` wiring; demote
only if delta summaries stop being a required published support artifact; remove
only with a replacement verifier that proves equivalent canonical-artifact delta
coverage.

### Supplemental verifiers

| Verifier / workflow | Purpose | Scope | Blocking/advisory/manual | Unique signal | When to run directly |
|---|---|---|---|---|---|
| `python -m mypy` | Advisory typing pass for Python tooling | typed Python surfaces | Supplemental / advisory | Static type signal without blocking the default maintainer gate | Python refactors, interface changes, or before promoting stricter typing |
| `python scripts/verify/run_all.py --skip-tests` | Smoke the blocking wrapper without rerunning Python or Node tests | blocking pipeline minus Python/Node tests | Supplemental | Fastest way to exercise the Starlight-era blocking path end-to-end without a wrapper script | Iterating on blocking verifiers or site build behavior |
| `scripts/verify/example_validation_matrix.py` | Validate explicit examples-only evidence tiers and runtime-smoke commands | `references/example-validation-matrix.json` plus `examples/` paths | Supplemental | Prevents examples from claiming validation without a recorded evidence tier or command | After adding, removing, or changing examples |
| `scripts/verify/shell_examples_syntax.py` | Parse-check repo shell examples with `bash -n` | `examples/**/*.sh` | Supplemental | Only direct syntax check for shell example scripts | After adding or editing shell examples |

### Advisory verifiers and replay workflows

| Verifier / workflow | Purpose | Scope | Blocking/advisory/manual | Unique signal | When to run directly |
|---|---|---|---|---|---|
| `scripts/verify/stale_content.py` | Scan for stale markers and aging content | docs plus extracted JSON | Advisory | Finds `TODO`/`TBD`-style drift and old `Last Updated` markers | Cleanup sweeps, doc review passes, or before promoting pages |
| `scripts/verify/extraction_idempotency.py` | Re-run extractors against pinned inputs and compare outputs | extractor determinism for `references/raw/*.json` | Advisory | Only direct determinism check for extraction reproducibility | Extractor changes or refresh-pipeline review |
| `scripts/verify/upstream_pins.py` | Confirm pinned tags and commits still resolve upstream | upstream pin validity for canonical JSON metadata | Advisory | External trust check with cached GitHub API resolution | Scheduled pin health review or after suspicious upstream changes |
| `scripts/verify/example_surface_integrity.py` | Validate example family structure and routed example references | `examples/` plus routed start-here docs | Advisory | Checks example directory completeness and routed example paths together | Example-surface edits or start-here routing updates |
| `scripts/verify/evidence_metadata_freshness.py` | Enforce opening evidence metadata discipline on retained pages | selected published docs pages | Advisory | Only verifier that checks allowed baseline-status wording patterns directly | Docs policy changes or refreshes affecting evidence blocks |
| `scripts/verify/docs_index_unknown_routes.py` | Surface unclassified docs-index route entries for maintainer triage | `public/artifacts/docs-index.json` route metadata | Advisory | Only verifier that summarizes unknown docs-index route classifications and reason counts | Docs-index route metadata changes or route-classification audits |
| `scripts/verify/governance_lifecycle.py` | Validate lifecycle records and advisory-first governance policy coverage | verifier lifecycle manifest, policy text, schemas, and support artifact records | Advisory | Only verifier that checks lifecycle manifest shape, schema-closure documentation, support-artifact admission records, and placement wiring drift | Governance policy changes or new durable verifier/support surfaces |
| `scripts/verify/provenance_chain_integrity.py` | Validate refresh provenance follow-up ordering and flag consistency | `public/artifacts/refresh-provenance.json` plus delta/manifest/current artifact state | Advisory | Only verifier that checks stale backup references and reverse-direction published flag drift | After refreshes, publication follow-up commands, or provenance cleanup |
| `scripts/verify/versioned_artifact_completeness.py` | Classify versioned artifact directories and current-version completeness | `public/artifacts/versions/` plus manifest `version_key` | Advisory | Only verifier that distinguishes current complete, retained complete, empty directory drift, and pre-websocket historical exceptions | After publishing artifacts, changing version retention policy, or reviewing empty/partial version directories |
| `scripts/verify/site_base_consistency.py` | Detect shared site/base configuration drift | `src/site/site-config.json`, Astro config, markdown rewriting, and rendered-link verification | Advisory | Only verifier that checks site/base URL settings across config and verifier consumers | Site base, route rewriting, or rendered-link verifier changes |
| `.github/workflows/dependency-advisory.yml` | Run scheduled/manual dependency vulnerability audits | npm and Python dependency surfaces | Advisory workflow | Durable dependency-risk signal outside push/PR blocking CI | Use the workflow for weekly or manual dependency advisory review |
| `.github/workflows/advisory-checks.yml` | Replay advisory scripts as blocking on schedule/manual dispatch | weekly/manual advisory escalation path | Advisory workflow | Converts the non-blocking advisory script set into a durable scheduled gate | Use the workflow when maintainers want a blocking replay outside push/PR CI |

### Runtime-specific verifiers and workflows

| Verifier / workflow | Purpose | Scope | Blocking/advisory/manual | Unique signal | When to run directly |
|---|---|---|---|---|---|
| `scripts/verify/runtime_smoke.py` | Probe a live ComfyUI instance for basic API readiness and prompt submission | live runtime endpoints | Manual runtime-specific | Only repo-local verifier that exercises real HTTP runtime behavior directly | When validating a running ComfyUI instance or runtime-facing examples |
| `scripts/verify/example_runtime_smoke.py` | Exercise repo-local examples against a live ComfyUI runtime | `examples/` API prompt, WebSocket, optional installed example nodes/routes | Manual runtime-specific | Only examples-only live validation path; checks object_info classes, prompt submission, WebSocket status, and optional example route/node expectations | Before claiming an example is runtime-validated against a live ComfyUI instance |
| `scripts/verify/wait_for_runtime.py` | Poll a live endpoint until JSON readiness | live runtime startup/readiness | Manual runtime-specific | Purpose-built readiness gate for headless runtime workflows | Before runtime capture steps that require a live ComfyUI server |
| `.github/workflows/runtime-smoke.yml` | Run `runtime_smoke.py` against a user-supplied ComfyUI URL | manual live-runtime smoke workflow | Manual runtime-specific workflow | Reproducible GitHub Actions wrapper for runtime smoke without local setup | When maintainers need remote/manual runtime verification evidence |
| `.github/workflows/headless-runtime-metadata.yml` | Launch pinned ComfyUI headlessly, wait for readiness, capture runtime metadata, and optionally build a hybrid schema artifact | pinned runtime metadata capture | Manual runtime-specific workflow | Only workflow that clones the pinned runtime and captures fresh `object_info` evidence | When runtime metadata or hybrid-schema evidence is needed |

### Workflow orchestration surfaces

| Verifier / workflow | Purpose | Scope | Blocking/advisory/manual | Unique signal | When to run directly |
|---|---|---|---|---|---|
| `.github/workflows/ci.yml` | Main CI entrypoint for blocking, supplemental, advisory-in-CI, and optional refresh jobs | push/PR/manual repo verification | Workflow orchestration | Shows how blocking, supplemental, and non-blocking advisory checks are staged in CI | Inspect when changing verifier placement or CI parity with `run_all.py` |
| `.github/workflows/deploy-pages.yml` | Verify committed artifacts and deploy the built site | deploy pipeline | Workflow orchestration | Publishes the committed generated artifact tree only after the blocking wrapper passes | Inspect when changing deployment or publication flow |
| `.github/workflows/upstream-watch.yml` | Check upstream versions and open/update a tracking issue | upstream monitoring automation | Workflow orchestration | Tracks refresh opportunities rather than repo correctness | Inspect when changing upstream-watch automation or issue workflow |

## Maintainer Failure-Path Quick Guide

- blocking CI failure: reproduce locally with `python scripts/verify/run_all.py`
- advisory replay failure: rerun the named advisory script locally
- schema failure: fix the source JSON or schema, not generated outputs by hand
- docs-index freshness failure: regenerate with `python scripts/generate/generate_docs_index.py`
- artifact-integrity failure: republish canonical artifacts and recheck the manifest/current copies
- delta-summary integrity failure: regenerate `public/artifacts/delta-summary.json` from the recorded refresh backup and rerun `python scripts/verify/delta_summary_integrity.py`
- rendered-links failure: rebuild and fix the source markdown or route mismatch
- example validation failure: fix the example, its README, or `references/example-validation-matrix.json`; do not relabel examples as runtime-validated without a live `example_runtime_smoke.py` result

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
