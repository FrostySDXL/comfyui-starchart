---
title: "Runtime and CI Operations"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-05-06

## Overview

This repository has two automation modes with different hardware and trust
requirements:

1. **CPU-safe repo CI** -- runs on ordinary GitHub-hosted runners
2. **Opt-in runtime extraction/verification** -- requires a live ComfyUI instance

This page explains when to use each mode, what they prove, and what they do
not prove.

## CPU-Safe CI

These jobs run on every push and pull request. They do not require a GPU or a
running ComfyUI process.

### What runs

- Unit tests for all extractors, verifiers, and generators
- Node-side tests
- Cross-reference verification
- JSON schema validation
- Sidebar navigation coverage
- Astro check and site build
- Stale content checks (non-blocking)
- Extraction idempotency checks (non-blocking)
- Upstream pin resolution checks (non-blocking)

### Workflows

- `.github/workflows/ci.yml` -- blocking checks on push/PR
- `.github/workflows/advisory-checks.yml` -- scheduled/manual blocking replay of
  the advisory scripts
- `.github/workflows/weekly-pin-check.yml` -- verifies pinned commits still
  resolve upstream
- `.github/workflows/upstream-watch.yml` -- scheduled every Monday at 10:00 UTC
  and available on manual dispatch; scheduled runs detect newer upstream
  versions and create or update tracking issues, while manual runs produce the
  watch artifacts without mutating issue state

### When to rely on it

Use CPU-safe CI for:
- validating extractor output shape and schema compliance
- confirming docs build without broken links
- validating the checked-in sidebar and Starlight build path
- checking that pinned upstream refs still exist
- catching structural drift in generated references

### Limits

CPU-safe CI does **not** verify that:
- extracted data matches a live ComfyUI instance
- example payloads work against a real server
- custom nodes registered at runtime match static parsers

### Blocking vs advisory interpretation

- `blocking-verification` in `.github/workflows/ci.yml` is the merge-gating path.
  It should line up with the local `python scripts/verify/run_all.py` wrapper.
- `advisory-checks` in `.github/workflows/ci.yml` keeps noisy or still-maturing
  checks visible without blocking push/PR CI.
- `.github/workflows/advisory-checks.yml` reruns those same advisory scripts as
  blocking on a scheduled or manual basis so maintainers still get a durable
  escalation path.
- `scripts/verify/example_surface_integrity.py` currently stays advisory in
  normal push/PR CI because the example surface and its routing references are
  still evolving. Promote it only after maintainers judge the signal stable
  enough that false positives are uncommon.

## Opt-In Runtime Verification

These jobs require a running ComfyUI instance and are kept separate from
ordinary CI so that PRs do not depend on GPU availability.

### What runs

- `scripts/extract/parse_from_api.py` -- captures `GET /object_info` from a live
  instance and writes a pinned runtime snapshot
- `scripts/verify/runtime_smoke.py` -- lightweight smoke checks against
  `/features`, `/system_stats`, `/object_info`, and optionally `POST /prompt`

### Workflows

- `.github/workflows/runtime-smoke.yml` -- `workflow_dispatch` only; accepts a
  ComfyUI base URL and runs the smoke script
- `.github/workflows/headless-runtime-metadata.yml` -- `workflow_dispatch` only;
  clones the pinned ComfyUI commit into the runner, starts a localhost-only
  instance, skips `POST /prompt` to avoid a model requirement, captures
  temporary runtime metadata, and uploads artifacts from the runner temp
  directory

### When to use it

Use runtime verification for:
- refreshing references after a major upstream release when you have a known
  good ComfyUI instance available
- validating that example payloads still work against the current ComfyUI
  surface
- capturing a runtime snapshot for hybrid schema generation

Do not treat runtime capture as the default onboarding path for tooling authors.
Start with the canonical published artifacts first, and use runtime capture only
when the tool genuinely depends on live installed-node state.

Use `runtime-smoke.yml` when you need to test a specific existing instance,
including custom nodes or non-default runtime configuration. Use
`headless-runtime-metadata.yml` when you want CI-hosted proof that the runtime
metadata path works against a disposable, pinned upstream baseline without
exposing a local machine.

### Limits

Runtime verification does **not** verify that:
- all custom node types are documented
- prose docs are free of stale markers
- generated markdown is up to date with JSON references

## Hybrid Schema Generation

The node API schema pipeline supports a hybrid mode that merges source-derived
metadata with runtime-captured object info.

### Source-only mode

Default when running `parse_node_api_schema.py` without a runtime snapshot.
Produces:

- `object_info_fields` from static `server.py` analysis
- `io_types` from `_io.py` class parsing
- `basic_input_shapes` and `typed_input_shapes` from `basic_types.py`

### Hybrid mode

Enabled by passing `--object-info-runtime-path` to `parse_node_api_schema.py`.
Adds:

- `runtime_object_info` -- raw runtime node definitions
- `provenance` metadata recording which sections came from source files versus
  runtime capture
- updated `coverage` noting runtime enrichment

### Refresh orchestration

`scripts/refresh_snapshots.py` can orchestrate the full hybrid pipeline:

```bash
# Source-only refresh
python scripts/refresh_snapshots.py --core-version v0.20.1

# Hybrid refresh with runtime capture
python scripts/refresh_snapshots.py --core-version v0.20.1 \
  --runtime-object-info-url http://127.0.0.1:8188 \
  --runtime-object-info-version v0.20.1
```

Refresh is not complete at the first command. The maintainer closure sequence is:

1. run `scripts/refresh_snapshots.py` and note the printed repo-local backup
   directory path
2. confirm `public/artifacts/refresh-provenance.json` was written and still matches
   what you intended to refresh
3. run `python scripts/generate/publish_reference_artifacts.py`
4. run `python scripts/verify/verify_artifact_integrity.py`
5. if you are comparing baselines, run
   `python scripts/generate/generate_snapshot_delta_summary.py --old <backup-dir> --new references/raw --output public/artifacts/delta-summary.json`
6. review `public/artifacts/delta-summary.json` and `public/artifacts/refresh-provenance.json`
   together before calling the refresh closed
7. run the broader verification path required by the change, typically
   `python scripts/verify/run_all.py`
8. remove the temporary backup only after you no longer need it for restore or
   delta review

## Broken pushes and ambiguous CI failures

Use this section when a maintainer push or PR does not fail as one obvious repo
script error.

### Broken pushes

1. Identify whether the failure came from the blocking path, the advisory path,
   a runtime-only workflow, or a manual refresh workflow.
2. Reproduce locally with the closest repo command you can actually run:
   - `python scripts/verify/run_all.py` for the blocking path
   - the specific advisory script for advisory failures
   - the matching runtime script only when you intentionally have a live
     ComfyUI instance available
3. If the failure reproduces locally, fix the repo state first and rerun the
   failing command before pushing again.
4. If the failure does not reproduce locally, inspect workflow-specific inputs:
   matrix OS, scheduled/manual trigger context, or runtime availability.

### Ambiguous CI failures

Treat ambiguous CI failures as classification work first:

- **Blocking failure:** starts in `blocking-verification` and should be explainable
  from the ordered local gate mirrored by `run_all.py`.
- **Advisory failure:** starts in the advisory job or advisory replay; fix it when
  the signal is real, but do not misreport it as a canonical artifact or docs
  build failure.
- **Runtime-only failure:** can be normal when the workflow requires a live or
  disposable ComfyUI instance and the problem is specific to that operating mode.

Inspect `.github/workflows/ci.yml` when the failure might depend on the Ubuntu or
Windows matrix, and inspect `.github/workflows/advisory-checks.yml` when the
same script passed in normal PR CI but failed in the scheduled/manual blocking
replay.

## Rollback and restore expectations

Use the smallest truthful rollback that returns the repo to a verified state.

### Doc-only changes

- Revert or restore the affected docs files.
- Rerun `python scripts/verify/cross_references.py`.
- Rerun `npm run build`.

### Canonical artifact publication changes

- Restore the intended source of truth first: checked-in schema files or the
  canonical `references/raw/` outputs.
- Rerun `python scripts/generate/publish_reference_artifacts.py`.
- Rerun `python scripts/verify/verify_artifact_integrity.py`.
- If the change also affected docs links or published guidance, rerun
  `python scripts/verify/cross_references.py` and `npm run build`.

### Snapshot refresh changes

- Use the printed repo-local backup directory when you need to restore the prior
  canonical raw baseline.
- After restore, republish artifacts and rerun integrity verification.
- Regenerate `public/artifacts/delta-summary.json` if you want the published
  comparison view to match the restored baseline.
- Keep `public/artifacts/refresh-provenance.json` honest about the last attempted
  refresh or explicitly update the surrounding maintainer note if the published
  provenance record is intentionally being replaced.

## Artifact Boundaries

| Artifact | Source | Canonical | Packaged |
|---|---|---|---|
| `references/raw/server_endpoints.json` | source | yes | yes |
| `references/raw/js_hooks.json` | source | yes | yes |
| `references/raw/node_api_schema.json` | source + optional runtime | yes | yes |
| `references/raw/object_info_runtime.json` | runtime only | no | no |
| workflow artifact `runtime-metadata-<run_id>` | disposable CI runtime | no | no |

`object_info_runtime.json` is a runtime-only capture artifact. It is excluded
from the public artifact packaging pipeline because its contents depend on the
specific ComfyUI instance configuration at capture time.

Treat that runtime-only file as optional in normal local verification, normal
push/PR CI, and standard consumer artifact loading. Its absence is expected
unless someone intentionally ran `scripts/extract/parse_from_api.py`, used the
runtime-enriched refresh path, or triggered a runtime-focused workflow.

The canonical published artifact surface is documented in
[Machine-Readable Artifacts](machine-readable-artifacts.md).

The headless CI workflow follows the same boundary. It writes runtime captures
and optional hybrid schema output under the runner temp directory and uploads
them only as workflow artifacts.

## One-Command Verification

`scripts/verify/run_all.py` wraps the standard CPU-safe verification sequence:

```bash
python scripts/verify/run_all.py
```

This runs unit tests, Node-side tests, Python/style verifiers, artifact/docs
verifiers, sidebar coverage, and the Starlight check/build sequence in order.
It exits non-zero on the first blocking failure.

## Known Limitations

- Runtime smoke checks use a minimal endpoint subset. They do not exercise image
  generation or custom node execution.
- The upstream-watch workflow detects tag differences but does not evaluate
  changelog risk.
- Hybrid schema generation preserves source-derived sections that runtime
  capture does not expose (e.g., type hints from `_io.py`).

## Read Next

- [Version Pin Status](version-pin-status.md)
- [Object Info](object-info.md)
- [Machine-Readable Artifacts](machine-readable-artifacts.md)
