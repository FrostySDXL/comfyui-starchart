# AGENTS.md

## 0. Quickstart

Always Use Supported Python: `3.11+`

Windows interpreter rule:

- Do not assume `python` points to 3.11.
- Before running repo commands on Windows, verify `python --version` is `3.11.x`.
- If the default `python` is not 3.11, use `py -3.11` for every repo command instead of `python`.
- Prefer these Windows-safe forms when there is any doubt:

```bash
py -3.11 -m pip install -r requirements.lock
py -3.11 -m unittest discover -s tests -v
py -3.11 -m mkdocs build
```

```
python -m pip install -r requirements.lock
python -m unittest discover -s tests -v
python -m mkdocs build
```

Serve locally: `python -m mkdocs serve`

On Windows when `python` is not 3.11, use: `py -3.11 -m mkdocs serve`

Maintainer dependency contract:

- Install from `requirements.lock`
- Edit direct dependencies in `requirements.in`
- Do not hand-edit `requirements.lock`; regenerate it after dependency changes
- `requirements.txt` is a compatibility shim to `requirements.lock`

Lockfile regeneration (Python 3.11+ environment, `pip-tools` installed):

```bash
python -m pip install pip-tools
python -m piptools compile --strip-extras requirements.in --output-file requirements.lock
```

On Windows when `python` is not 3.11, run the same commands with `py -3.11 -m ...`.

Default maintainer pre-push wrapper:

```bash
python scripts/verify/run_all.py
```

On Windows when `python` is not 3.11, use: `py -3.11 scripts/verify/run_all.py`

## 0.5. Decision Tree

| Task | Read first | Edit | Verify |
|------|-----------|------|--------|
| Add/fix docs content | `docs/<topic>/` page + `docs/reference/source-evidence-policy.md` + `docs/reference/writing-style-guide.md` | The page + adjacent linked pages + `references/raw/` if citing data; copy from `templates/docs/` or use `scripts/new_doc.py` for new pages | `python scripts/verify/cross_references.py` + `python -m mkdocs build` |
| Update extracted references | `references/raw/<file>.json` | Run the matching extractor script | `python scripts/verify/extraction_idempotency.py` |
| Update community catalog | `references/community/ecosystem_packages.json` + `docs/reference/community-maintenance-policy.md` | Edit JSON source; regenerate page | `python scripts/verify/validate_schema.py` + `python scripts/verify/community_metadata.py` + `python scripts/verify/community_staleness.py` + `python scripts/generate/generate_community_pages.py` + `python scripts/verify/community_generated_freshness.py` + `python scripts/verify/community_page_coverage.py` + `python scripts/verify/cross_references.py` + `python -m mkdocs build` |
| Add a new extractor | Existing extractor in `scripts/extract/` | New script + test in `tests/unit/` | `python -m unittest discover -s tests` |
| Add a verification script | Existing script in `scripts/verify/` | New script + test in `tests/unit/` + intentional `run_all.py` / CI placement | `python -m unittest discover -s tests` |
| Refresh upstream version | `scripts/refresh_snapshots.py` | Run refresh with `--core-version` / `--frontend-version`, note the auto-created `references/raw_backup_TIMESTAMP` path and `docs/artifacts/refresh-provenance.json`, then republish artifacts and regenerate delta summary | `python scripts/generate/publish_reference_artifacts.py` + `python scripts/generate/generate_snapshot_delta_summary.py --old <backup-dir> --new references/raw --output docs/artifacts/delta-summary.json` + `python scripts/verify/run_all.py` |
| Runtime extraction | `scripts/extract/parse_from_api.py` | Run with `--url` and `--output` | `validate_schema.py` passes on output |
| Change CI workflow | relevant file in `.github/workflows/` + adjacent operational docs | Edit YAML + linked docs when operator behavior changes | Inspect YAML carefully, run `python -m unittest discover -s tests -v -p "test_run_all.py"` and `python scripts/verify/run_all.py`, then check Ubuntu/Windows Actions runs and any advisory replay workflow after push |

## 0.6. Consumer Agent Orientation

If you are helping a user **build with ComfyUI** (not contribute to this repo), start at `docs/index.md` and follow the role table to prevent getting lost or introducing context bloat:

| Goal | File |
|------|------|
| Custom nodes | `docs/start-here/author.md` |
| Extend frontend/server | `docs/start-here/extension-developer.md` |
| Service integration | `docs/start-here/service-integration.md` |
| Tools/agents | `docs/start-here/tooling-builder.md` |

Read only the pages listed in that file's reading order. Stop when the question is answered. Do not explore `scripts/`, `references/`, `tests/`, `.github/workflows/`, `docs/reference/`, or `CONTRIBUTING.md`.

## 1. Mission

Source-backed, repo-local reference documentation for ComfyUI development.
Covers server API endpoints, JS/server hooks, custom node patterns, and
extension architecture. Content is extracted from pinned upstream source
snapshots, not written from memory.

The repo also publishes machine-readable JSON artifacts, a manifest for
tooling authors and integrators, and a bounded docs-index support artifact.
These files are packaged into the built site under `docs/artifacts/`.

Consumer-facing docs describe the published artifact surface, while repo-local
maintainer workflows intentionally remain in `AGENTS.md` and `CONTRIBUTING.md`.

Non-goals: official docs replacement, community wiki, package registry.

## 2. Hard Rules

- Do not claim official behavior without a source citation from `references/snapshots/` or `docs.comfy.org`
- Do not add emojis or emoticons to any file
- All paths in JSON metadata must use forward slashes (never backslashes)
- Extractors write JSON; generators write markdown; never hand-edit generated markdown
- For prose doc edits, follow `docs/reference/source-evidence-policy.md`, `docs/reference/writing-style-guide.md`, and `docs/reference/doc-quality-checklist.md`
- Run verification before claiming completion

## 3. Repo Map

- `docs/` -- MkDocs source-backed documentation pages
  - `docs/artifacts/` -- Published JSON artifacts, manifest, docs index support artifact, delta summary, refresh provenance, and checked-in schemas
- `references/raw/` -- JSON reference data extracted from pinned upstream snapshots
  - `server_endpoints.json` -- API routes from `parse_server.py`
  - `js_hooks.json` -- Frontend hooks from `parse_hooks.py`
  - `node_api_schema.json` -- Node API schema from `parse_node_api_schema.py`
- `references/community/` -- JSON metadata for community-facing content (editable)
  - `ecosystem_packages.json` -- Package catalog that drives `docs/ecosystem/map.md`
  - `community_pages.json` -- Review metadata for community pages
- `references/snapshots/` -- Pinned upstream source files organized by date
- `scripts/common/` -- Shared utility modules used by multiple scripts (for example path normalization and HTTP helpers)
- `scripts/extract/` -- Extractors that parse source into JSON
- `scripts/generate/` -- Generators that render markdown from JSON or package artifacts
  - `md_from_json.py` -- Renders reference docs from `references/raw/`
  - `generate_community_pages.py` -- Renders `docs/ecosystem/map.md` from community metadata
  - `generate_docs_index.py` -- Produces `docs/artifacts/docs-index.json` from the published docs surface
  - `publish_reference_artifacts.py` -- Copies canonical JSON artifacts to `docs/artifacts/` and writes `manifest.json`
  - `generate_snapshot_delta_summary.py` -- Produces deterministic baseline-to-baseline comparison under `docs/artifacts/delta-summary.json`
- `scripts/verify/` -- Verification scripts
  - Core blocking checks: `cross_references.py`, `docs_index_freshness.py`, `validate_schema.py`, `verify_artifact_integrity.py`, `community_generated_freshness.py`, `community_page_coverage.py`
  - Supplemental checks: `pipeline_smoke.py`, `shell_examples_syntax.py`
  - Non-blocking: `stale_content.py`, `extraction_idempotency.py`, `upstream_pins.py`
  - Community: `community_metadata.py`, `community_staleness.py`
- `scripts/refresh_snapshots.py` -- Fetch new upstream versions and re-run pipeline
- `tests/unit/` -- Unit tests for all scripts
- `examples/` -- Hand-authored pattern examples, API calls, and workflows
- `.github/workflows/` -- CI (`ci.yml`), advisory replay (`advisory-checks.yml`),
  weekly pin check (`weekly-pin-check.yml`), upstream version watch (`upstream-watch.yml`), and docs deployment (`deploy-pages.yml`)
  - includes opt-in runtime workflows such as `runtime-smoke.yml` and `headless-runtime-metadata.yml`

## 4. Key Commands

```bash
# One-command wrapper for the blocking local gate mirrored by CI
python scripts/verify/run_all.py

# Tests
python -m unittest discover -s tests -v

# Build docs
python -m mkdocs build

# Verification scripts (all should exit 0 on clean repo)
python scripts/verify/cross_references.py
python scripts/verify/docs_index_freshness.py
python scripts/verify/community_generated_freshness.py
python scripts/verify/community_page_coverage.py
python scripts/verify/stale_content.py
python scripts/verify/extraction_idempotency.py
python scripts/verify/upstream_pins.py
python scripts/verify/validate_schema.py
python scripts/verify/verify_artifact_integrity.py
python scripts/verify/pipeline_smoke.py
python scripts/verify/shell_examples_syntax.py

# Community verifiers (non-blocking in CI)
python scripts/verify/community_metadata.py
python scripts/verify/community_staleness.py

# Extractors (run against snapshot files)
python scripts/extract/parse_server.py <path> --version <v> --commit <sha>
python scripts/extract/parse_hooks.py <paths...> --version <v> --commit <sha>
python scripts/extract/parse_node_api_schema.py <server> <io> <types> --version <v> --commit <sha>

# Runtime extractor (opt-in; requires live ComfyUI instance)
python scripts/extract/parse_from_api.py --url <url> --version <v> --commit <sha> --output references/raw/object_info_runtime.json

# Generators
python scripts/generate/md_from_json.py
python scripts/generate/generate_community_pages.py
python scripts/generate/generate_docs_index.py
python scripts/generate/publish_reference_artifacts.py
python scripts/generate/generate_snapshot_delta_summary.py --old <dir> --new <dir> --output docs/artifacts/delta-summary.json

# Refresh upstream (clone, extract, generate)
python scripts/refresh_snapshots.py --core-version v0.20.1

# Runtime smoke checks (opt-in; requires live ComfyUI instance)
python scripts/verify/runtime_smoke.py --url <url>

# Runtime readiness helper (useful for CI-hosted local instances)
python scripts/verify/wait_for_runtime.py --url <endpoint>
```

Use narrow checks while iterating. Use `python scripts/verify/run_all.py`
before calling maintainer workflow changes complete. That wrapper mirrors the
blocking CI path that now runs on both Ubuntu and Windows; advisory checks stay
separate and escalate through the dedicated advisory replay workflow.

## 5. Task Playbooks

### Updating extracted references

1. Edit source in `references/snapshots/` or run `refresh_snapshots.py`
2. Run the matching extractor with `--version` and `--commit` flags
3. Optionally run `parse_from_api.py` with `--url` for runtime enrichment
4. Run `md_from_json.py` to regenerate markdown
5. If published JSON artifacts or `docs/artifacts/manifest.json` changed, rerun `python scripts/generate/publish_reference_artifacts.py` before verification so manifest hashes stay in sync
6. Run `cross_references.py` and `validate_schema.py` to verify

### Refreshing upstream baselines

1. Run `python scripts/refresh_snapshots.py --core-version <v> --frontend-version <v>` and note the printed `references/raw_backup_TIMESTAMP` path plus `docs/artifacts/refresh-provenance.json`
2. Run `python scripts/generate/publish_reference_artifacts.py`
3. Run `python scripts/verify/verify_artifact_integrity.py`
4. If comparing two baselines, run `python scripts/generate/generate_snapshot_delta_summary.py --old <backup-dir> --new references/raw --output docs/artifacts/delta-summary.json`
5. Remove the temporary backup after confirming the delta output if you no longer need it
6. Run `python scripts/verify/run_all.py`

### Editing prose documentation

1. Read the target page and the closest adjacent pages first
2. Read `docs/reference/source-evidence-policy.md` before changing evidence labels or trust framing
3. Read `docs/reference/writing-style-guide.md` before rewriting structure or tone
4. Use `docs/reference/doc-quality-checklist.md` before calling the edit complete
5. For new pages, copy from `templates/docs/` or use `scripts/new_doc.py`
6. Run `python scripts/verify/cross_references.py`
7. Run `python -m mkdocs build`

### Updating community metadata

1. Edit `references/community/ecosystem_packages.json` for catalog changes
2. Edit `references/community/community_pages.json` for page review metadata
3. Run `python scripts/verify/validate_schema.py`
4. Run `python scripts/verify/community_metadata.py`
5. Run `python scripts/verify/community_staleness.py`
6. Run `python scripts/generate/generate_community_pages.py`
7. Run `python scripts/verify/community_generated_freshness.py`
8. Run `python scripts/verify/community_page_coverage.py`
9. Run `python scripts/verify/cross_references.py`
10. Run `python -m mkdocs build`

### Adding a new verification script

1. Create `scripts/verify/<name>.py` -- exit 0 on pass, exit 1 on fail
2. Add test in `tests/unit/test_<name>.py` -- import check, smoke test, edge cases
3. Add it to `scripts/verify/run_all.py` if it should be part of the default local blocking gate
4. Add step to `.github/workflows/ci.yml` with an explicit blocking vs advisory choice

### Adding a new extractor

1. Create `scripts/extract/<name>.py` -- reads source, writes JSON to `references/raw/`
2. Include `--version` and `--commit` flags in metadata
3. Normalize all file paths to forward slashes in output JSON
4. Add test in `tests/unit/`
5. Add generator step in `scripts/generate/` if markdown output is needed

## 6. Common Pitfalls

- **Windows backslashes in JSON**: Extractors run on Windows produce `\` in paths. Always use `.replace("\\", "/")` when writing `str(path)` to JSON metadata.
- **Cross-platform artifact hashes**: The three published artifact checksums are for textual JSON files and must be stable across Windows and Linux checkouts. Hash them after normalizing `CRLF` to `LF`; do not use this normalization rule for future binary artifacts.
- **Idempotency drift**: Extractors write timestamps (`extracted_date`). The idempotency checker reports byte-level differences as expected; structural differences are the real concern.
- **Structured returns and traceability are partially inferred**: `server_endpoints.json` now uses structured `returns` objects instead of `"TODO"`, and Plan K semantic enrichment adds `traceability` markers to endpoints, hooks, and node schema fields. The `kind` field is reliable; `fields`, `summary`, and `traceability` details are best-effort from static analysis.
- **CI non-blocking steps**: `stale_content`, `extraction_idempotency`, `upstream_pins`, `community_metadata`, and `community_staleness` use `continue-on-error: true` in normal push/PR CI. `cross_references`, `validate_schema`, `verify_artifact_integrity`, `community_generated_freshness`, and `community_page_coverage` block the pipeline, and the advisory scripts also replay in `advisory-checks.yml` as a scheduled/manual blocking escalation path.
- **Supplemental CI checks are intentionally outside `run_all.py`**: `pipeline_smoke.py` reruns the blocking wrapper end-to-end without recursive unit tests, and `shell_examples_syntax.py` depends on a `bash` executable for `examples/**/*.sh` validation.
- **Generated community pages must not be hand-edited**: `docs/ecosystem/map.md` is generated from `references/community/ecosystem_packages.json`. Edit the JSON and rerun the generator.
- **Examples are not all source-backed**: Treat files under `examples/` as pattern examples unless the page explicitly states they were generated or extracted from pinned upstream sources.

## 7. Completion Standard

Do not say work is complete unless you can state:
- what changed
- which files changed
- which commands were run
- what those commands returned
- any remaining gaps or follow-up work
