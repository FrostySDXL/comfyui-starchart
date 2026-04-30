# ComfyUI Knowledge Base

**Last Updated:** 2026-04-29
**ComfyUI Version Pin:** Core `v0.19.3` (`3086026401180c9216bcb6ace442a4e3587d2c66`) with official frontend `v1.42.11` (`3dc4061d484d61cb89366de25bf5e2f8a65da4d0`) for pinned snapshots and extracted reference data

**Evidence:** Scaffold

## What This Repository Is

This repository is a version-pinned, source-extracted companion reference for
ComfyUI developers. It is not the official ComfyUI documentation; authoritative
human reference remains at [docs.comfy.org](https://docs.comfy.org/).

The repo publishes extracted JSON artifacts alongside a self-hostable MkDocs
site. It is designed for extension developers, tooling authors, and integrators
who need a stable, cited baseline for selected ComfyUI API surfaces, hooks, and
node schema behavior. Because everything is pinned to exact upstream commits,
the reference baseline is reproducible and forkable.

This repository covers:
- server API endpoints and WebSocket behavior
- JavaScript and server-side extension hooks
- custom node development patterns and datatypes
- extension architecture patterns
- tutorials, how-to guides, and machine-readable reference data

## Evidence Discipline

Apply this trust order when reading any page:

1. official ComfyUI documentation on `docs.comfy.org`
2. upstream ComfyUI source and release notes
3. this repository's summaries, examples, and extracted references
4. clearly labeled community pattern examples

This repository does not claim official or native ComfyUI behavior unless backed
by an official docs page or a pinned upstream source citation.

For editorial standards and evidence rules, use these files together:

- `docs/reference/source-evidence-policy.md`
- `docs/reference/writing-style-guide.md`
- `docs/reference/doc-quality-checklist.md`

## Documentation Layers

### Human-readable docs

- Source lives in `docs/`
- Preview locally with `mkdocs serve`
- New pages should start from `templates/docs/` or use `scripts/new_doc.py`

### Where to Start

- Building custom nodes: [`docs/start-here/author.md`](docs/start-here/author.md)
- Extending ComfyUI: [`docs/start-here/extension-developer.md`](docs/start-here/extension-developer.md)
- Integrating ComfyUI into a service: [`docs/start-here/service-integration.md`](docs/start-here/service-integration.md)
- Contributing documentation: [`docs/start-here/docs-contributor.md`](docs/start-here/docs-contributor.md)
- Building tools or agents: [`docs/start-here/tooling-builder.md`](docs/start-here/tooling-builder.md)

### Machine-readable references

- JSON reference data lives in `references/raw/`
- Community metadata lives in `references/community/`
- Snapshots live in `references/snapshots/`
- Helper scripts live in `scripts/extract/` and `scripts/generate/`
- Published artifact copies and manifest live in `docs/artifacts/`
- See [Machine-Readable Artifacts](docs/reference/machine-readable-artifacts.md) for
  the canonical published artifact set, bounded guarantees, and conceptual
  examples for tooling authors

## Quick Start

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m mkdocs build
```

Serve locally: `python -m mkdocs serve`

### Self-hosting

The documentation site and published artifacts can be self-hosted or forked.
Build the site with `python -m mkdocs build`, then serve the `site/` directory
with any static file server. The artifact files under `docs/artifacts/` are
included in the built output.

### Extracting references

```bash
python scripts/extract/parse_server.py path/to/server.py --version v0.19.3 --commit 3086026401180c9216bcb6ace442a4e3587d2c66
python scripts/extract/parse_hooks.py path/to/app.ts path/to/comfy.ts path/to/litegraphService.ts --version v1.42.11 --commit 3dc4061d484d61cb89366de25bf5e2f8a65da4d0
python scripts/extract/parse_node_api_schema.py path/to/server.py path/to/_io.py path/to/basic_types.py --version v0.19.3 --commit 3086026401180c9216bcb6ace442a4e3587d2c66
python scripts/generate/md_from_json.py
```

### Generating community pages

```bash
python scripts/generate/generate_community_pages.py
```

### Refreshing upstream versions

Replace the example versions below with the actual target versions for the
refresh you are performing.

```bash
python scripts/refresh_snapshots.py --core-version <new-core-version>
python scripts/refresh_snapshots.py --frontend-version <new-frontend-version>
python scripts/refresh_snapshots.py --core-version <new-core-version> --frontend-version <new-frontend-version>
```

## Verification

```bash
# One-command wrapper (runs the current CI-blocking local checks)
python scripts/verify/run_all.py

# CI-blocking local checks
python -m unittest discover -s tests -v
python scripts/verify/cross_references.py
python scripts/verify/validate_schema.py
python scripts/verify/community_generated_freshness.py
python scripts/verify/community_page_coverage.py
python -m mkdocs build

# Additional checks (non-blocking in CI)
python scripts/verify/stale_content.py
python scripts/verify/extraction_idempotency.py
python scripts/verify/upstream_pins.py

# Community metadata checks (non-blocking in CI)
python scripts/verify/community_metadata.py
python scripts/verify/community_staleness.py
```

## CI

### CPU-safe workflows (blocking and non-blocking)

- **`.github/workflows/ci.yml`** -- runs on push/PR to main: tests, MkDocs build, cross-references (blocking), schema validation (blocking), generated community freshness (blocking), community page coverage (blocking), stale content (non-blocking), idempotency (non-blocking), upstream pins (non-blocking), community metadata (non-blocking), and community staleness (non-blocking). Also supports `workflow_dispatch` with `core_version` and `frontend_version` inputs to trigger `refresh_snapshots.py`.
- **`.github/workflows/weekly-pin-check.yml`** -- runs every Monday at 09:00 UTC and on manual dispatch: checks that pinned commits and tags still resolve in upstream repos.
- **`.github/workflows/upstream-watch.yml`** -- runs every Monday at 10:00 UTC: detects newer upstream versions and creates or updates tracking issues.

### Site deployment

- **`.github/workflows/deploy-pages.yml`** -- builds and deploys the MkDocs site
  (including packaged artifacts under `docs/artifacts/`) to GitHub Pages.
  Triggers on push to `main`/`master` and on `workflow_dispatch`.
  Requires the repository Pages source to be set to **GitHub Actions** in
  repository settings.

### Opt-in runtime workflows

- **`.github/workflows/runtime-smoke.yml`** -- `workflow_dispatch` only: runs lightweight smoke checks against a live ComfyUI instance. Requires a ComfyUI base URL input.

## Runtime Extraction

The repo supports optional runtime capture from a live ComfyUI instance:

```bash
# Capture runtime object_info
python scripts/extract/parse_from_api.py --url http://127.0.0.1:8188 --version v0.19.3 --commit <sha> --output references/raw/object_info_runtime.json

# Hybrid refresh (source + runtime)
python scripts/refresh_snapshots.py --core-version v0.19.4 --runtime-object-info-url http://127.0.0.1:8188

# Runtime smoke checks
python scripts/verify/runtime_smoke.py --url http://127.0.0.1:8188
```

Runtime extraction is opt-in and separate from standard CPU-safe verification.
Runtime-only `object_info` capture is not part of the canonical published
artifact surface. See `docs/reference/runtime-ci-operations.md` for the full
operating model.

## Scope Boundaries

- [docs.comfy.org](https://docs.comfy.org/) is the official human reference for ComfyUI.
- This repository is a pinned companion reference with bounded machine-readable
  guarantees. It does not aim to replace official docs or cover end-user
  tutorials.
- Workflow and tutorial-oriented readers may prefer community resources such as
  [comfyui-wiki.com](https://comfyui-wiki.com/) for non-developer guides.

## External Sources

- https://docs.comfy.org/
- https://github.com/Comfy-Org/ComfyUI
- https://registry.comfy.org/
