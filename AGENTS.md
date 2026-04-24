# AGENTS.md

## 0. Quickstart

```
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m mkdocs build
```

Serve locally: `python -m mkdocs serve`

## 0.5. Decision Tree

| Task | Read first | Edit | Verify |
|------|-----------|------|--------|
| Add/fix docs content | `docs/<topic>/` page + `docs/reference/source-evidence-policy.md` + `docs/reference/writing-style-guide.md` | The page + adjacent linked pages + `references/raw/` if citing data; copy from `templates/docs/` or use `scripts/new_doc.py` for new pages | `python scripts/verify/cross_references.py` + `python -m mkdocs build` |
| Update extracted references | `references/raw/<file>.json` | Run the matching extractor script | `python scripts/verify/extraction_idempotency.py` |
| Update community catalog | `references/community/ecosystem_packages.json` + `docs/reference/community-maintenance-policy.md` | Edit JSON source; regenerate page | `python scripts/verify/validate_schema.py` + `python scripts/verify/community_metadata.py` + `python scripts/verify/community_staleness.py` + `python scripts/generate/generate_community_pages.py` + `python scripts/verify/community_generated_freshness.py` + `python scripts/verify/community_page_coverage.py` + `python scripts/verify/cross_references.py` + `python -m mkdocs build` |
| Add a new extractor | Existing extractor in `scripts/extract/` | New script + test in `tests/unit/` | `python -m unittest discover -s tests` |
| Add a verification script | Existing script in `scripts/verify/` | New script + test in `tests/unit/` | `python -m unittest discover -s tests` |
| Refresh upstream version | `scripts/refresh_snapshots.py` | Run with `--core-version` / `--frontend-version` | All verify scripts pass |
| Runtime extraction | `scripts/extract/parse_from_api.py` | Run with `--url` and `--output` | `validate_schema.py` passes on output |
| Change CI workflow | relevant file in `.github/workflows/` + adjacent operational docs | Edit YAML + linked docs when operator behavior changes | Inspect YAML carefully, run affected local verification, then check Actions tab after push |

## 1. Mission

Source-backed, repo-local reference documentation for ComfyUI development.
Covers server API endpoints, JS/server hooks, custom node patterns, and
extension architecture. Content is extracted from pinned upstream source
snapshots, not written from memory.

The repo also publishes machine-readable JSON artifacts and a manifest for
tooling authors and integrators. These artifacts are packaged into the built
site under `docs/artifacts/`.

Non-goals: official docs replacement, community wiki, package registry.

## 2. Hard Rules

- Do not claim official behavior without a source citation from `references/snapshots/` or `docs.comfy.org`
- Do not add emojis or emoticons to any file
- All paths in JSON metadata must use forward slashes (never backslashes)
- Extractors write JSON; generators write markdown; never hand-edit generated markdown
- For prose doc edits, follow `docs/reference/source-evidence-policy.md`, `docs/reference/writing-style-guide.md`, and `docs/reference/doc-quality-checklist.md`
- Run verification before claiming completion
- Never commit `.cache/` or `site/`

## 3. Repo Map

- `docs/` -- MkDocs source-backed documentation pages
- `references/raw/` -- JSON reference data extracted from pinned upstream snapshots
  - `server_endpoints.json` -- API routes from `parse_server.py`
  - `js_hooks.json` -- Frontend hooks from `parse_hooks.py`
  - `node_api_schema.json` -- Node API schema from `parse_node_api_schema.py`
- `references/community/` -- JSON metadata for community-facing content (editable)
  - `ecosystem_packages.json` -- Package catalog that drives `docs/ecosystem/map.md`
  - `community_pages.json` -- Review metadata for community pages
- `references/snapshots/` -- Pinned upstream source files organized by date
- `scripts/extract/` -- Extractors that parse source into JSON
- `scripts/generate/` -- Generators that render markdown from JSON or package artifacts
  - `md_from_json.py` -- Renders reference docs from `references/raw/`
  - `generate_community_pages.py` -- Renders `docs/ecosystem/map.md` from community metadata
  - `publish_reference_artifacts.py` -- Copies canonical JSON artifacts to `docs/artifacts/` and writes `manifest.json`
- `scripts/verify/` -- Verification scripts
  - Core blocking checks: `cross_references.py`, `validate_schema.py`, `community_generated_freshness.py`, `community_page_coverage.py`
  - Non-blocking: `stale_content.py`, `extraction_idempotency.py`, `upstream_pins.py`
  - Community: `community_metadata.py`, `community_staleness.py`
- `scripts/refresh_snapshots.py` -- Fetch new upstream versions and re-run pipeline
- `tests/unit/` -- Unit tests for all scripts
- `examples/` -- Hand-authored pattern examples, API calls, and workflows
- `.github/workflows/` -- CI (`ci.yml`), weekly pin check (`weekly-pin-check.yml`),
  upstream version watch (`upstream-watch.yml`), and docs deployment (`deploy-pages.yml`)
  - includes opt-in runtime workflows such as `runtime-smoke.yml` and `headless-runtime-metadata.yml`

## 4. Key Commands

```bash
# One-command wrapper
python scripts/verify/run_all.py

# Tests
python -m unittest discover -s tests -v

# Build docs
python -m mkdocs build

# Verification scripts (all should exit 0 on clean repo)
python scripts/verify/cross_references.py
python scripts/verify/community_generated_freshness.py
python scripts/verify/community_page_coverage.py
python scripts/verify/stale_content.py
python scripts/verify/extraction_idempotency.py
python scripts/verify/upstream_pins.py
python scripts/verify/validate_schema.py

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
python scripts/generate/publish_reference_artifacts.py

# Refresh upstream (clone, extract, generate)
python scripts/refresh_snapshots.py --core-version v0.19.4

# Runtime smoke checks (opt-in; requires live ComfyUI instance)
python scripts/verify/runtime_smoke.py --url <url>

# Runtime readiness helper (useful for CI-hosted local instances)
python scripts/verify/wait_for_runtime.py --url <endpoint>
```

## 5. Task Playbooks

### Updating extracted references

1. Edit source in `references/snapshots/` or run `refresh_snapshots.py`
2. Run the matching extractor with `--version` and `--commit` flags
3. Optionally run `parse_from_api.py` with `--url` for runtime enrichment
4. Run `md_from_json.py` to regenerate markdown
5. Run `cross_references.py` and `validate_schema.py` to verify

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
3. Add step to `.github/workflows/ci.yml` if it should run in CI

### Adding a new extractor

1. Create `scripts/extract/<name>.py` -- reads source, writes JSON to `references/raw/`
2. Include `--version` and `--commit` flags in metadata
3. Normalize all file paths to forward slashes in output JSON
4. Add test in `tests/unit/`
5. Add generator step in `scripts/generate/` if markdown output is needed

## 6. Common Pitfalls

- **Windows backslashes in JSON**: Extractors run on Windows produce `\` in paths. Always use `.replace("\\", "/")` when writing `str(path)` to JSON metadata.
- **Idempotency drift**: Extractors write timestamps (`extracted_date`). The idempotency checker reports byte-level differences as expected; structural differences are the real concern.
- **Structured returns are partially inferred**: `server_endpoints.json` now uses structured `returns` objects instead of `"TODO"`, but some endpoints still show generic summaries when the handler returns a variable rather than a literal dict. The `kind` field is reliable; `fields` and `summary` are best-effort from static analysis.
- **CI non-blocking steps**: `stale_content`, `extraction_idempotency`, `upstream_pins`, `community_metadata`, and `community_staleness` use `continue-on-error: true` in CI. `cross_references`, `validate_schema`, `community_generated_freshness`, and `community_page_coverage` block the pipeline.
- **Generated community pages must not be hand-edited**: `docs/ecosystem/map.md` is generated from `references/community/ecosystem_packages.json`. Edit the JSON and rerun the generator.
- **Examples are not all source-backed**: Treat files under `examples/` as pattern examples unless the page explicitly states they were generated or extracted from pinned upstream sources.

## 7. Completion Standard

Do not say work is complete unless you can state:
- what changed
- which files changed
- which commands were run
- what those commands returned
- any remaining gaps or follow-up work
