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
| Add/fix docs content | `docs/<topic>/` page | The page + `references/raw/` if citing data | `mkdocs build` |
| Update extracted references | `references/raw/<file>.json` | Run the matching extractor script | `python scripts/verify/extraction_idempotency.py` |
| Add a new extractor | Existing extractor in `scripts/extract/` | New script + test in `tests/unit/` | `python -m unittest discover -s tests` |
| Add a verification script | Existing script in `scripts/verify/` | New script + test in `tests/unit/` | `python -m unittest discover -s tests` |
| Refresh upstream version | `scripts/refresh_snapshots.py` | Run with `--core-version` / `--frontend-version` | All verify scripts pass |
| Change CI workflow | `.github/workflows/ci.yml` | Edit YAML | Push and check Actions tab |

## 1. Mission

Source-backed, repo-local reference documentation for ComfyUI development.
Covers server API endpoints, JS/server hooks, custom node patterns, and
extension architecture. Content is extracted from pinned upstream source
snapshots, not written from memory.

Non-goals: official docs replacement, community wiki, package registry.

## 2. Hard Rules

- Do not claim official behavior without a source citation from `references/snapshots/` or `docs.comfy.org`
- Do not add emojis or emoticons to any file
- All paths in JSON metadata must use forward slashes (never backslashes)
- Extractors write JSON; generators write markdown; never hand-edit generated markdown
- Run verification before claiming completion
- Never commit `.cache/` or `site/`

## 3. Repo Map

- `docs/` -- MkDocs source-backed documentation pages
- `references/raw/` -- JSON reference data (machine-readable)
  - `server_endpoints.json` -- API routes from `parse_server.py`
  - `js_hooks.json` -- Frontend hooks from `parse_hooks.py`
  - `node_api_schema.json` -- Node API schema from `parse_node_api_schema.py`
- `references/snapshots/` -- Pinned upstream source files organized by date
- `scripts/extract/` -- Extractors that parse source into JSON
- `scripts/generate/` -- `md_from_json.py` generates markdown from JSON
- `scripts/verify/` -- Verification scripts (cross_references, stale_content, extraction_idempotency, upstream_pins, validate_schema)
- `scripts/refresh_snapshots.py` -- Fetch new upstream versions and re-run pipeline
- `tests/unit/` -- Unit tests for all scripts
- `examples/` -- Source-backed example nodes, API calls, and workflows
- `.github/workflows/` -- CI (`ci.yml`) and weekly pin check (`weekly-pin-check.yml`)

## 4. Key Commands

```bash
# Tests
python -m unittest discover -s tests -v

# Build docs
python -m mkdocs build

# Verification scripts (all should exit 0 on clean repo)
python scripts/verify/cross_references.py
python scripts/verify/stale_content.py
python scripts/verify/extraction_idempotency.py
python scripts/verify/upstream_pins.py
python scripts/verify/validate_schema.py

# Extractors (run against snapshot files)
python scripts/extract/parse_server.py <path> --version <v> --commit <sha>
python scripts/extract/parse_hooks.py <paths...> --version <v> --commit <sha>
python scripts/extract/parse_node_api_schema.py <server> <io> <types> --version <v> --commit <sha>

# Generator (run after any extractor)
python scripts/generate/md_from_json.py

# Refresh upstream (clone, extract, generate)
python scripts/refresh_snapshots.py --core-version v0.19.4
```

## 5. Task Playbooks

### Updating extracted references

1. Edit source in `references/snapshots/` or run `refresh_snapshots.py`
2. Run the matching extractor with `--version` and `--commit` flags
3. Run `md_from_json.py` to regenerate markdown
4. Run `cross_references.py` and `validate_schema.py` to verify

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
- **Stale TODO markers**: The `returns` field in `server_endpoints.json` is `"TODO"` for all endpoints. This is a known gap, not a bug.
- **CI non-blocking steps**: `stale_content`, `extraction_idempotency`, and `upstream_pins` use `continue-on-error: true` in CI. Only `cross_references` and `validate_schema` block the pipeline.

## 7. Completion Standard

Do not say work is complete unless you can state:
- what changed
- which files changed
- which commands were run
- what those commands returned
- any remaining gaps or follow-up work