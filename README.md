# ComfyUI Knowledge Base

**Last Updated:** 2026-05-02
**ComfyUI Version Pin:** Core `v0.20.1` (`64b8457f55cd7fb54ca7a956d9c73b505e903e0c`) with official frontend `v1.44.13` (`389ff8ba49468cc3afa11aec5778224689a8f9b9`) for the current pinned snapshots and extracted reference data

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

This repo serves three bounded audiences:

- **Consumers** using the published docs and artifacts to build custom nodes,
  extensions, integrations, or tools against ComfyUI
- **Contributors** editing docs, examples, or other hand-authored repo content
- **Maintainers** running snapshot refreshes, generators, verifiers, CI-facing
  workflow changes, or published artifact updates

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

- **Consumers**
  - Building custom nodes: [`docs/start-here/author.md`](docs/start-here/author.md)
  - Extending ComfyUI: [`docs/start-here/extension-developer.md`](docs/start-here/extension-developer.md)
  - Integrating ComfyUI into a service: [`docs/start-here/service-integration.md`](docs/start-here/service-integration.md)
  - Building tools or agents: [`docs/start-here/tooling-builder.md`](docs/start-here/tooling-builder.md)
- **Contributors**
  - Start with [`docs/start-here/docs-contributor.md`](docs/start-here/docs-contributor.md) for the lighter editorial path
- **Maintainers**
  - Use [`CONTRIBUTING.md`](CONTRIBUTING.md) for repo-local operational workflows, verification, refresh, and release-style tasks

### Machine-readable references

- JSON reference data lives in `references/raw/`
- Community metadata lives in `references/community/`
- Snapshots live in `references/snapshots/`
- Helper scripts live in `scripts/extract/` and `scripts/generate/`
- Published artifact copies, manifest, delta summary, and refresh provenance live in `docs/artifacts/`
- See [Machine-Readable Artifacts](docs/reference/machine-readable-artifacts.md) for
  the canonical published artifact set, published JSON Schemas, bounded
  guarantees, and conceptual examples for tooling authors

## Quick Start

Supported Python: `3.11+`

```bash
python -m pip install -r requirements.lock
python -m unittest discover -s tests -v
python -m mkdocs build
```

Serve locally: `python -m mkdocs serve`

### Dependency reproducibility

- Install the repo's maintainer environment from `requirements.lock`.
- Edit direct Python dependencies in `requirements.in`.
- Do not hand-edit `requirements.lock`; regenerate it after dependency changes.
- `requirements.txt` is a compatibility shim that points to `requirements.lock`.

Refresh the lockfile from a Python 3.11+ environment with `pip-tools` installed:

```bash
python -m pip install pip-tools
python -m piptools compile --strip-extras requirements.in --output-file requirements.lock
```

Before pushing maintainer-grade workflow, script, or verifier changes, run:

```bash
python scripts/verify/run_all.py
```

### Self-hosting

The documentation site and published artifacts can be self-hosted or forked.
Build the site with `python -m mkdocs build`, then serve the `site/` directory
with any static file server. The artifact files under `docs/artifacts/` are
included in the built output.

### Extracting references

```bash
python scripts/extract/parse_server.py path/to/server.py --version v0.20.1 --commit 64b8457f55cd7fb54ca7a956d9c73b505e903e0c
python scripts/extract/parse_hooks.py path/to/app.ts path/to/comfy.ts path/to/litegraphService.ts --version v1.44.13 --commit 389ff8ba49468cc3afa11aec5778224689a8f9b9
python scripts/extract/parse_node_api_schema.py path/to/server.py path/to/_io.py path/to/basic_types.py --version v0.20.1 --commit 64b8457f55cd7fb54ca7a956d9c73b505e903e0c
python scripts/generate/md_from_json.py
python scripts/generate/publish_reference_artifacts.py
```

### Generating community pages

```bash
python scripts/generate/generate_community_pages.py
```

### Comparing artifact baselines

When comparing two pinned baselines after a refresh, use the auto-created
`references/raw_backup_TIMESTAMP/` directory that `refresh_snapshots.py`
prints before it overwrites the canonical raw artifacts in place. The same
refresh run also writes `docs/artifacts/refresh-provenance.json` with the
requested versions, resolved commits, backup path, and runtime-enrichment
intent.

```bash
python scripts/generate/generate_snapshot_delta_summary.py --old references/raw_backup_TIMESTAMP --new references/raw --output docs/artifacts/delta-summary.json
```

### Refreshing upstream versions

Replace the example versions below with the actual target versions for the
refresh you are performing.

```bash
python scripts/refresh_snapshots.py --core-version <new-core-version>
python scripts/refresh_snapshots.py --frontend-version <new-frontend-version>
python scripts/refresh_snapshots.py --core-version <new-core-version> --frontend-version <new-frontend-version>
python scripts/generate/publish_reference_artifacts.py
```

The refresh script now creates a repo-local backup automatically when
`references/raw/` already exists, prints the exact backup path to reuse for
delta generation, and writes `docs/artifacts/refresh-provenance.json`. It does
not auto-generate `delta-summary.json`, auto-clean backups, or auto-commit.

## Verification

```bash
# One-command wrapper (runs the current CI-blocking local checks)
python scripts/verify/run_all.py

# CI-blocking local checks
python -m unittest discover -s tests -v
python scripts/verify/cross_references.py
python scripts/verify/validate_schema.py
python scripts/verify/verify_artifact_integrity.py
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

Use targeted commands while iterating on a narrow surface. Run
`python scripts/verify/run_all.py` before opening a PR when you need the same
blocking verification path that CI runs on both Ubuntu and Windows. Advisory
checks remain separate from this local wrapper and from PR-blocking status.

For issue intake, use the repository's bug-report template for behavior or
artifact problems, the docs-request template for documentation gaps or
discoverability requests, and the upstream-refresh template for maintainer-run
version watch follow-up.

## CI

### CPU-safe workflows (blocking and non-blocking)

- **`.github/workflows/ci.yml`** -- runs on push/PR to main: the blocking verification path runs on both `ubuntu-latest` and `windows-latest` (tests, cross-references, schema validation, artifact integrity verification for canonical published artifacts, generated community freshness, community page coverage, and MkDocs build). Advisory checks (`stale_content.py`, `extraction_idempotency.py`, `upstream_pins.py`, `community_metadata.py`, and `community_staleness.py`) still run in CI but remain non-blocking there. Also supports `workflow_dispatch` with `core_version` and `frontend_version` inputs to trigger `refresh_snapshots.py`.
- **`.github/workflows/advisory-checks.yml`** -- scheduled weekly and available via `workflow_dispatch`: reruns the current advisory scripts as blocking so advisory failures remain visible without turning normal PR CI into a noisy blocker.
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
python scripts/extract/parse_from_api.py --url http://127.0.0.1:8188 --version v0.20.1 --commit <sha> --output references/raw/object_info_runtime.json

# Hybrid refresh (source + runtime)
python scripts/refresh_snapshots.py --core-version v0.20.1 --runtime-object-info-url http://127.0.0.1:8188

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
