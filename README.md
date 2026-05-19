# ComfyUI Knowledge Base

**Last Updated:** 2026-05-13
**ComfyUI Version Pin:** Core `v0.21.1` (`26515acd23fa291a8f5ab53c5997258598de0701`) with official frontend `v1.45.9` (`8562816ffa0d996bd400e517292fee074a6acefa`) for the current pinned snapshots and extracted reference data

**Evidence:** Operational guidance

## What This Repository Is

This repository is a version-pinned, source-extracted companion reference for
ComfyUI developers. It is not the official ComfyUI documentation; authoritative
human reference remains at [docs.comfy.org](https://docs.comfy.org/).

The repo publishes extracted JSON artifacts alongside a self-hostable Astro
Starlight site. It is designed for extension developers, tooling authors, and integrators
who need a stable, cited baseline for selected ComfyUI API surfaces, hooks, and
node schema behavior. Because everything is pinned to exact upstream commits,
the reference baseline is reproducible and forkable.

This repo serves three bounded audiences:

- **Consumers** using the published docs and artifacts to build custom nodes,
  extensions, integrations, or tools against ComfyUI
- **Contributors** editing docs, examples, or other hand-authored repo content
- **Maintainers** running snapshot refreshes, generators, verifiers, CI-facing
  workflow changes, or published artifact updates

## Repository Health Files

- [SECURITY.md](SECURITY.md) -- private vulnerability reporting guidance
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) -- participation expectations for public collaboration

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

- `src/content/docs/reference/source-evidence-policy.md`
- `src/content/docs/reference/writing-style-guide.md`
- `src/content/docs/reference/doc-quality-checklist.md`

## Documentation Layers

### Human-readable docs

- Source lives in `src/content/docs/`
- Preview locally with `npm run dev`
- New pages should start from `templates/docs/` or use `scripts/new_doc.py --output src/content/docs/...`

### Where to Start

- **Consumers**
  - Building custom nodes: [`src/content/docs/start-here/author.md`](src/content/docs/start-here/author.md)
  - Extending ComfyUI: [`src/content/docs/start-here/extension-developer.md`](src/content/docs/start-here/extension-developer.md)
  - Integrating ComfyUI into a service: [`src/content/docs/start-here/service-integration.md`](src/content/docs/start-here/service-integration.md)
  - Building tools or agents: [`src/content/docs/start-here/tooling-builder.md`](src/content/docs/start-here/tooling-builder.md)
- **Contributors**
  - Start with [`src/content/docs/start-here/docs-contributor.md`](src/content/docs/start-here/docs-contributor.md) for the lighter editorial path
- **Maintainers**
  - Use [`CONTRIBUTING.md`](CONTRIBUTING.md) as the canonical repo-local maintainer workflow source for verification, refresh, artifact publication, CI-adjacent, and release-style tasks

### Machine-readable references

- JSON reference data lives in `references/raw/`
- Community metadata lives in `references/community/`
- Snapshots live in `references/snapshots/`
- Helper scripts live in `scripts/extract/` and `scripts/generate/`
- Published artifact copies, manifest, delta summary, and refresh provenance live in `public/artifacts/`
- `public/artifacts/docs-index.json` is a bounded support artifact for tooling and agent page discovery; it does not widen the canonical JSON artifact contract
- See [Machine-Readable Artifacts](src/content/docs/reference/machine-readable-artifacts.md) for
  the canonical published artifact set, published JSON Schemas, bounded
  guarantees, the minimum consumer contract, and conceptual examples for tooling
  authors
- Consumer starter examples for manifest-first artifact loading and docs-discovery
  patterns live under `examples/consumers/`; see
  [Consumer Starter Examples](src/content/docs/how-to/consumer-starter-examples.md)

### Orientation aids

- [Docs home](src/content/docs/index.md) for audience-based entry paths
- [Glossary](src/content/docs/reference/glossary.md) for repeated artifact and repo terms
- [What's New](src/content/docs/whats-new/index.md) for recent reader-visible changes

## Quick Start

Supported Python: `3.11+`

Supported Node.js for site-work and Starlight surfaces: `24+`

```bash
python -m pip install -r requirements.lock
npm ci
python -m unittest discover -s tests -v
npm run build
```

Serve locally: `npm run dev`

If you are touching site-framework or frontend-build surfaces, use Node.js
`24+` via `.nvmrc` or equivalent environment-specific tooling.

### Dependency reproducibility

Maintainers should install from `requirements.lock`. For direct dependency edits,
lockfile regeneration, and the full maintainer setup workflow, use
[`CONTRIBUTING.md`](CONTRIBUTING.md).

Before pushing maintainer-grade workflow, script, or verifier changes, run:

```bash
python scripts/verify/run_all.py
```

Use `run_all.py` as the default maintainer-grade before-push check. It mirrors
the CI job's blocking path. For lockfile regeneration, extractor/generator
workflows, snapshot refreshes, runtime capture, community metadata pipelines,
and the full maintainer verification matrix, use
[`CONTRIBUTING.md`](CONTRIBUTING.md).

### Self-hosting

The documentation site and published artifacts can be self-hosted or forked.
Build the site with `npm run build`, then serve the `dist/` directory
with any static file server. The artifact files under `public/artifacts/` are
included in the built output.

## Maintainer Workflow Entry Points

- `python scripts/verify/run_all.py` is the default maintainer-grade local gate
  and mirrors the blocking CI path.
- Use targeted commands while iterating on a narrow surface, then use
  [`CONTRIBUTING.md`](CONTRIBUTING.md) for the canonical maintainer workflows,
  verification matrix, extractor/generator procedures, snapshot refresh steps,
  community metadata pipeline, and CI-adjacent guidance.
- For runtime-only capture and validation against a live ComfyUI instance, use
  [`CONTRIBUTING.md`](CONTRIBUTING.md) and
  [`src/content/docs/reference/runtime-ci-operations.md`](src/content/docs/reference/runtime-ci-operations.md).

For issue intake, use the repository's bug-report template for behavior or
artifact problems, the docs-request template for documentation gaps or
discoverability requests, the feature-request template for proposed repo
enhancements, and the upstream-refresh template for maintainer-run version watch
follow-up.

## CI

### CPU-safe workflows (blocking, supplemental, and non-blocking)

- **`.github/workflows/ci.yml`** -- runs on push/PR to main: the blocking verification path runs on both `ubuntu-latest` and `windows-latest` (Python unit tests, Node-side tests, Python style, references-path verification, docs-index freshness, schema validation, artifact integrity verification for canonical published artifacts, top-level markdown spacing verification for hand-authored docs, generated community freshness, community page coverage, sidebar navigation coverage, `npm run check`, and `npm run build`). A supplemental Ubuntu job then runs `python scripts/verify/pipeline_smoke.py` to exercise the `run_all.py` wrapper end-to-end without rerunning unit tests, plus `python scripts/verify/shell_examples_syntax.py` to validate hand-authored shell examples with `bash -n`. Advisory checks (`stale_content.py`, `extraction_idempotency.py`, `upstream_pins.py`, `community_metadata.py`, and `community_staleness.py`) still run in CI but remain non-blocking there. Also supports `workflow_dispatch` with `core_version` and `frontend_version` inputs to trigger `refresh_snapshots.py`.
- **`.github/workflows/advisory-checks.yml`** -- scheduled weekly and available via `workflow_dispatch`: reruns the current advisory scripts as blocking so advisory failures remain visible without turning normal PR CI into a noisy blocker.
- **`.github/workflows/weekly-pin-check.yml`** -- runs every Monday at 09:00 UTC and on manual dispatch: checks that pinned commits and tags still resolve in upstream repos.
- **`.github/workflows/upstream-watch.yml`** -- runs every Monday at 10:00 UTC and on manual dispatch: scheduled runs detect newer upstream versions and create or update tracking issues; manual runs generate the watch artifacts without mutating issue state.

### Site deployment

- **`.github/workflows/deploy-pages.yml`** -- republishes canonical artifacts,
  reruns the blocking local verification wrapper (without the final duplicate
  Starlight checks already covered by the wrapper), then deploys the Starlight site (including packaged
  artifacts from `public/artifacts/`) to GitHub Pages. Triggers on push to
  `main`/`master` and on `workflow_dispatch`. Requires the repository Pages
  source to be set to **GitHub Actions** in repository settings.

### Opt-in runtime workflows

- **`.github/workflows/runtime-smoke.yml`** -- `workflow_dispatch` only: runs lightweight smoke checks against a live ComfyUI instance. Requires a ComfyUI base URL input.

## Runtime Extraction

Optional runtime capture from a live ComfyUI instance stays outside the default
CPU-safe verification path. Runtime-only `object_info` capture is not part of
the canonical published artifact surface. Use
[`CONTRIBUTING.md`](CONTRIBUTING.md) and
[`src/content/docs/reference/runtime-ci-operations.md`](src/content/docs/reference/runtime-ci-operations.md)
for the full operating model and commands.

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
