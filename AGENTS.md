# AGENTS.md

## Mission

Source-backed, repo-local reference documentation for ComfyUI development.

This repo publishes:

- retained human docs under `src/content/docs/`
- canonical extracted JSON under `references/raw/`
- published current/versioned artifacts under `public/artifacts/`
- one merged support index: `public/artifacts/docs-index.json`

Use `AGENTS.md` for startup-critical repo guidance. Use `CONTRIBUTING.md` for the
deep maintainer playbooks.

## Hard Rules

- Use Python `3.11+`
- On Windows, bootstrap the venv with `py -3.11 -m venv .venv` once; all subsequent commands run from the activated venv
- Use Node.js `24.x` for site/framework work
- Do not claim official behavior without a source citation from `references/snapshots/` or `docs.comfy.org`
- Do not add emojis or emoticons
- Normalize JSON paths to forward slashes
- Extractors write JSON; generators write derived artifacts; do not hand-edit generated outputs
- Run current verification before claiming completion
- New verifiers, generators, support artifacts, or published docs sections require an explicit maintenance case and lifecycle decision in `CONTRIBUTING.md`

## Windows Quickstart

```bash
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --require-hashes -r requirements.lock
python -m pip install -e .
npm ci
python -m unittest discover -s tests -v
npm run build
```

Default maintainer gate:

```bash
python scripts/verify/run_all.py
```

## Repo Map

- `src/content/docs/` — retained published docs surface
- `references/raw/` — canonical extracted JSON artifacts
- `references/docs-index-metadata.json` — curated nested tooling metadata merged into `docs-index.json`
- `references/snapshots/` — pinned upstream source snapshots
- `public/artifacts/` — published current/versioned artifacts, schemas, docs index, delta summary, refresh provenance
- `scripts/common/` — shared helpers
- `scripts/extract/` — extractors
- `scripts/generate/` — generators and artifact publication scripts
- `scripts/verify/` — blocking, supplemental, and advisory verifiers
- `tests/unit/` — unit tests for scripts
- `.github/workflows/` — CI, advisory replay, deployment, upstream watch, and optional runtime workflows

## Routing Cues

Use this quick router before exploring the repo:

| Task | Read first | Verify |
|---|---|---|
| Edit published docs prose | target page + `src/content/docs/reference/source-evidence-policy.md` + `src/content/docs/reference/writing-style-guide.md` | `python scripts/verify/cross_references.py` + `npm run build` |
| Update docs-index routing metadata | `references/docs-index-metadata.json` + `src/content/docs/reference/machine-readable-artifacts.md` | `python scripts/generate/generate_docs_index.py` + `python scripts/verify/docs_index_freshness.py` + `python scripts/verify/validate_schema.py` |
| Update extracted references | matching file in `references/raw/` + extractor in `scripts/extract/` | `python scripts/verify/validate_schema.py` + relevant narrow checks |
| Change maintainer Python tooling | `pyproject.toml` + affected `scripts/` modules | `python -m pip install -e .` + `python -m mypy` + `python -m unittest discover -s tests -v` + `python scripts/verify/run_all.py` |
| Add or change a verifier | existing verifier + matching unit test | `python -m unittest discover -s tests -v` and place it in blocking/advisory CI intentionally |
| Change examples | target example README + `references/example-validation-matrix.json` | `python scripts/verify/example_surface_integrity.py` + `python scripts/verify/example_validation_matrix.py` + relevant example tests |
| Runtime-check examples | target example README + `CONTRIBUTING.md` runtime-specific verifier inventory | `python scripts/verify/example_runtime_smoke.py --url <live-url> --comfyui-root <runtime-root> --model-name <checkpoint>` |
| Change CI workflow | relevant `.github/workflows/*.yml` + `CONTRIBUTING.md` workflow guidance | `python -m unittest discover -s tests -v -p "test_run_all.py"` + `python scripts/verify/run_all.py` |
| Refresh upstream baselines | `scripts/refresh_snapshots.py` + `CONTRIBUTING.md` refresh section | follow the printed post-refresh command sequence, then `python scripts/verify/run_all.py` |
| Need the full verifier inventory | `CONTRIBUTING.md` verifier inventory + `references/verifier-lifecycle.json` | run the relevant listed verifier directly |

## Key Commands

```bash
python scripts/verify/run_all.py
python -m unittest discover -s tests -v
npm run check
npm run build
```

See `CONTRIBUTING.md` for the canonical blocking, supplemental, and advisory
verifier inventory. Supplemental/advisory surfaces remain outside `run_all.py`
unless promoted intentionally.

## Current Blocking vs Advisory Shape

`CONTRIBUTING.md` is canonical for the full verifier inventory, lifecycle
records, and promotion rules. Keep `AGENTS.md` startup-oriented: use the key
commands above, then read `CONTRIBUTING.md` before changing verifier placement or
workflow wiring.

Current supplemental/advisory examples to remember during startup:

- `stale_content.py`
- `extraction_idempotency.py`
- `upstream_pins.py`
- `example_surface_integrity.py`
- `example_validation_matrix.py`
- `evidence_metadata_freshness.py`
- `governance_lifecycle.py`
- `python -m mypy`

## Common Pitfalls

- `docs-index.json` is the only active support index; do not recreate `tooling-index.json`
- `public/artifacts/docs-index.json` is generated; regenerate it after navigation or metadata changes
- all repo Python commands must be run from an activated venv; running them outside the venv uses a different interpreter and may fail mypy or unit tests
- `references/docs-index-metadata.json` must only target retained published pages
- `refresh-provenance.json` is published operator evidence, not a manifest-discovered canonical artifact
- after `scripts/refresh_snapshots.py`, use the printed `Recommended follow-up commands:` block instead of reconstructing the republish/delta-summary/verification order by hand
- examples are validated by matrix/tier evidence; do not claim an example is runtime-validated unless `example_runtime_smoke.py` was run against a live ComfyUI instance and the exact command is recorded
- `npm run build` may print the benign Starlight `Entry docs -> 404 was not found.` warning

## Completion Standard

Do not say the work is complete unless you can state:

- what changed
- which files changed
- which commands were run
- what those commands returned
- any remaining gaps or follow-up work
