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
npm ci
py -3.11 -m unittest discover -s tests -v
npm run build
```

```
python -m pip install -r requirements.lock
npm ci
python -m unittest discover -s tests -v
npm run build
```

Serve locally: `npm run dev`

Always Use Supported Node.js for site/framework work: `22.12+` (tested through Node 24 LTS)

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
| Add/fix docs content | `src/content/docs/<topic>/` page + `src/content/docs/reference/source-evidence-policy.md` + `src/content/docs/reference/writing-style-guide.md` | The page + adjacent linked pages + `references/raw/` if citing data; copy from `templates/docs/` or use `scripts/new_doc.py` for new pages | `python scripts/verify/cross_references.py` + `npm run build` |
| Update extracted references | `references/raw/<file>.json` | Run the matching extractor script | `python scripts/verify/extraction_idempotency.py` |
| Update community catalog | `references/community/ecosystem_packages.json` + `src/content/docs/reference/community-maintenance-policy.md` | Edit JSON source; regenerate page | `python scripts/verify/validate_schema.py` + `python scripts/verify/community_metadata.py` + `python scripts/verify/community_staleness.py` + `python scripts/generate/generate_community_pages.py` + `python scripts/verify/community_generated_freshness.py` + `python scripts/verify/community_page_coverage.py` + `python scripts/verify/cross_references.py` + `npm run build` |
| Add a new extractor | Existing extractor in `scripts/extract/` | New script + test in `tests/unit/` | `python -m unittest discover -s tests` |
| Add a verification script | Existing script in `scripts/verify/` | New script + test in `tests/unit/` + intentional `run_all.py` / CI placement | `python -m unittest discover -s tests` |
| Refresh upstream version | `scripts/refresh_snapshots.py` | Run refresh with `--core-version` / `--frontend-version`, note the auto-created `references/raw_backup_TIMESTAMP` path and `public/artifacts/refresh-provenance.json`, then republish artifacts and regenerate delta summary | `python scripts/generate/publish_reference_artifacts.py` + `python scripts/generate/generate_snapshot_delta_summary.py --old <backup-dir> --new references/raw --output public/artifacts/delta-summary.json` + `python scripts/verify/run_all.py` |
| Runtime extraction | `scripts/extract/parse_from_api.py` | Run with `--url` and `--output` | `validate_schema.py` passes on output |
| Change CI workflow | relevant file in `.github/workflows/` + adjacent operational docs | Edit YAML + linked docs when operator behavior changes | Inspect YAML carefully, run `python -m unittest discover -s tests -v -p "test_run_all.py"` and `python scripts/verify/run_all.py`, then check Ubuntu/Windows Actions runs and any advisory replay workflow after push |

## 0.6. Consumer Agent Orientation

If you are helping a user **build with ComfyUI** (not contribute to this repo), start at `src/content/docs/index.md` and follow the role table to prevent getting lost or introducing context bloat:

| Goal | File |
|------|------|
| Custom nodes | `src/content/docs/start-here/author.md` |
| Extend frontend/server | `src/content/docs/start-here/extension-developer.md` |
| Service integration | `src/content/docs/start-here/service-integration.md` |
| Tools/agents | `src/content/docs/start-here/tooling-builder.md` |

Read only the pages listed in that file's reading order. Stop when the question is answered. Do not explore `scripts/`, `references/`, `tests/`, `.github/workflows/`, `src/content/docs/reference/`, or `CONTRIBUTING.md`.

## 1. Mission

Source-backed, repo-local reference documentation for ComfyUI development.
Covers server API endpoints, JS/server hooks, custom node patterns, and
extension architecture. Content is extracted from pinned upstream source
snapshots, not written from memory.

The repo also publishes machine-readable JSON artifacts, a manifest for
tooling authors and integrators, and a bounded docs-index support artifact.
These files are packaged into the built site from `public/artifacts/`.

Consumer-facing docs describe the published artifact surface, while repo-local
maintainer workflows intentionally remain in `AGENTS.md` and `CONTRIBUTING.md`.

Use `AGENTS.md` as the startup-critical quick-reference for session setup,
constraints, repo map, and key commands. Use `CONTRIBUTING.md` as the
authoritative home for deeper maintainer playbooks and longer operating
procedures.

Non-goals: official docs replacement, community wiki, package registry.

## 2. Hard Rules

- Do not claim official behavior without a source citation from `references/snapshots/` or `docs.comfy.org`
- Do not add emojis or emoticons to any file
- All paths in JSON metadata must use forward slashes (never backslashes)
- Extractors write JSON; generators write markdown; never hand-edit generated markdown
- For prose doc edits, follow `src/content/docs/reference/source-evidence-policy.md`, `src/content/docs/reference/writing-style-guide.md`, and `src/content/docs/reference/doc-quality-checklist.md`
- Run verification before claiming completion

## 3. Repo Map

- `src/content/docs/` -- Canonical published documentation pages
- `public/artifacts/` -- Published JSON artifacts, manifest, docs index support artifact, delta summary, refresh provenance, and checked-in schemas
- `references/raw/` -- JSON reference data extracted from pinned upstream snapshots
  - `server_endpoints.json` -- API routes from `parse_server.py`
  - `js_hooks.json` -- Frontend hooks from `parse_hooks.py`
  - `node_api_schema.json` -- Node API schema from `parse_node_api_schema.py`
- `references/community/` -- JSON metadata for community-facing content (editable)
  - `ecosystem_packages.json` -- Package catalog that drives `src/content/docs/ecosystem/map.md`
  - `community_pages.json` -- Review metadata for community pages
- `references/snapshots/` -- Pinned upstream source files organized by date
- `scripts/common/` -- Shared utility modules used by multiple scripts (for example path normalization and HTTP helpers)
- `scripts/extract/` -- Extractors that parse source into JSON
- `scripts/generate/` -- Generators that render markdown from JSON or package artifacts
  - `md_from_json.py` -- Renders reference docs from `references/raw/`
  - `generate_community_pages.py` -- Renders `src/content/docs/ecosystem/map.md` from community metadata
  - `generate_docs_index.py` -- Produces `public/artifacts/docs-index.json` from the published docs surface
  - `publish_reference_artifacts.py` -- Copies canonical JSON artifacts to `public/artifacts/` and writes `manifest.json`
  - `generate_snapshot_delta_summary.py` -- Produces deterministic baseline-to-baseline comparison under `public/artifacts/delta-summary.json`
- `scripts/verify/` -- Verification scripts
  - Core blocking checks: `cross_references.py` (bounded `references/...` path verification plus raw JSON source-path checks), `docs_index_freshness.py`, `validate_schema.py`, `verify_artifact_integrity.py`, `markdown_top_level_spacing.py`, `sidebar_navigation_coverage.py`, `community_generated_freshness.py`, `community_page_coverage.py`
  - Supplemental checks: `pipeline_smoke.py`, `shell_examples_syntax.py`
  - Non-blocking: `stale_content.py`, `extraction_idempotency.py`, `upstream_pins.py`
  - Community: `community_metadata.py`, `community_staleness.py`
- `scripts/refresh_snapshots.py` -- Fetch new upstream versions and re-run pipeline
- `tests/unit/` -- Unit tests for all scripts
- `examples/` -- Hand-authored pattern examples, API calls, and workflows
- `.github/workflows/` -- CI (`ci.yml`), advisory replay (`advisory-checks.yml`),
  weekly pin check (`weekly-pin-check.yml`), upstream version watch (`upstream-watch.yml`, scheduled every Monday at 10:00 UTC with manual dispatch also available), and docs deployment (`deploy-pages.yml`)
  - includes opt-in runtime workflows such as `runtime-smoke.yml` and `headless-runtime-metadata.yml`

## 4. Key Commands

```bash
# One-command wrapper for the blocking local gate mirrored by CI
python scripts/verify/run_all.py

# Tests
python -m unittest discover -s tests -v

# Build docs
npm run build

# Verification scripts (all should exit 0 on clean repo)
python scripts/verify/python_style.py
python scripts/verify/cross_references.py
python scripts/verify/docs_index_freshness.py
python scripts/verify/community_generated_freshness.py
python scripts/verify/community_page_coverage.py
python scripts/verify/stale_content.py
python scripts/verify/extraction_idempotency.py
python scripts/verify/upstream_pins.py
python scripts/verify/validate_schema.py
python scripts/verify/verify_artifact_integrity.py
python scripts/verify/markdown_top_level_spacing.py
python scripts/verify/sidebar_navigation_coverage.py
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
python scripts/generate/generate_snapshot_delta_summary.py --old <dir> --new <dir> --output public/artifacts/delta-summary.json

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

For `python scripts/verify/shell_examples_syntax.py`, resolve `bash` from the
CLI flag `--bash-executable`, then `COMFYUI_KB_BASH`, then `PATH`. Do not rely
on hardcoded Windows install paths.

## 4.5. Local Node.js Baseline

- Use Node.js `22.12+` (tested through Node 24 LTS) when touching site-framework or frontend-build surfaces.
- The repo enforces this with the root `.nvmrc` file (content: `22.12`).
- CI selects the version via `actions/setup-node@v4` with `node-version-file: ".nvmrc"`.

## 5. Task Playbooks

Use this section as a routing aid, not a second full maintainer handbook.
`CONTRIBUTING.md` owns the deeper step-by-step playbooks and longer operating
procedures.

- **Editing prose documentation:** read the target page plus the editorial
  policy stack, then run `python scripts/verify/cross_references.py` and
  `npm run build`.
- **Updating extracted references:** use the matching extractor/generator flow
  from `CONTRIBUTING.md`, then verify with the required schema and cross-link
  checks.
- **Refreshing upstream baselines:** use `scripts/refresh_snapshots.py`, note
  the printed backup path and `public/artifacts/refresh-provenance.json`, confirm
  that the file's `backup_location`, `published`, and `next_steps` fields tell the
  truth about the attempted path, then use the republish and verification
  sequence in `CONTRIBUTING.md`. Provenance-structure hardening is not a
  substitute for a future real refresh rehearsal.
- **Updating community metadata:** edit the JSON source, regenerate downstream
  output, and use the community verification pipeline from `CONTRIBUTING.md`.
- **Adding extractors or verifiers:** keep them test-backed, wire them into
  `run_all.py` or CI intentionally, and use `CONTRIBUTING.md` for exact
  placement rules.

## 6. Common Pitfalls

- **Windows backslashes in JSON**: Extractors run on Windows produce `\` in paths. Always use `.replace("\\", "/")` when writing `str(path)` to JSON metadata.
- **Cross-platform artifact hashes**: The three published artifact checksums are for textual JSON files and must be stable across Windows and Linux checkouts. Hash them after normalizing `CRLF` to `LF`; do not use this normalization rule for future binary artifacts.
- **Idempotency drift**: Extractors write timestamps (`extracted_date`). The idempotency checker reports byte-level differences as expected; structural differences are the real concern.
- **Structured returns and traceability are partially inferred**: `server_endpoints.json` now uses structured `returns` objects instead of `"TODO"`. The `kind` field is reliable; `fields`, `summary`, and `traceability` details are best-effort from static analysis.
- **CI non-blocking steps**: `stale_content`, `extraction_idempotency`, `upstream_pins`, `community_metadata`, `community_staleness`, and `example_surface_integrity` use `continue-on-error: true` in normal push/PR CI. `python_style`, `cross_references`, `validate_schema`, `verify_artifact_integrity`, `markdown_top_level_spacing`, `community_generated_freshness`, and `community_page_coverage` block the pipeline, and the advisory scripts also replay in `advisory-checks.yml` as a scheduled/manual blocking escalation path. Keep `example_surface_integrity` advisory until maintainers judge the example surface stable enough that false positives are uncommon.
- **Site-render-sensitive markdown spacing**: leading spaces before top-level markdown headings or metadata labels in hand-authored docs can render raw markdown in the browser output. `scripts/verify/markdown_top_level_spacing.py` blocks that drift.
- **Supplemental CI checks are intentionally outside `run_all.py`**: `pipeline_smoke.py` reruns the blocking wrapper end-to-end without recursive unit tests, and `shell_examples_syntax.py` depends on a `bash` executable for `examples/**/*.sh` validation resolved from `--bash-executable`, `COMFYUI_KB_BASH`, or `PATH`.
- **Generated community pages must not be hand-edited**: `src/content/docs/ecosystem/map.md` is generated from `references/community/ecosystem_packages.json`. Edit the JSON and rerun the generator.
- **Examples are not all source-backed**: Treat files under `examples/` as pattern examples unless the page explicitly states they were generated or extracted from pinned upstream sources.

## 7. Completion Standard

Do not say work is complete unless you can state:
- what changed
- which files changed
- which commands were run
- what those commands returned
- any remaining gaps or follow-up work
