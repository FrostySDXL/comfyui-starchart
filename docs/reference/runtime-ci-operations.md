# Runtime and CI Operations

**Evidence:** Operational guide
**Last Updated:** 2026-04-23

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
- MkDocs site build
- Cross-reference verification
- JSON schema validation
- Stale content checks (non-blocking)
- Extraction idempotency checks (non-blocking)
- Upstream pin resolution checks (non-blocking)

### Workflows

- `.github/workflows/ci.yml` -- blocking checks on push/PR
- `.github/workflows/weekly-pin-check.yml` -- verifies pinned commits still
  resolve upstream
- `.github/workflows/upstream-watch.yml` -- detects newer upstream versions and
  creates tracking issues

### When to rely on it

Use CPU-safe CI for:
- validating extractor output shape and schema compliance
- confirming docs build without broken links
- checking that pinned upstream refs still exist
- catching structural drift in generated references

### Limits

CPU-safe CI does **not** verify that:
- extracted data matches a live ComfyUI instance
- example payloads work against a real server
- custom nodes registered at runtime match static parsers

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

### When to use it

Use runtime verification for:
- refreshing references after a major upstream release when you have a known
  good ComfyUI instance available
- validating that example payloads still work against the current ComfyUI
  surface
- capturing a runtime snapshot for hybrid schema generation

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
python scripts/refresh_snapshots.py --core-version v0.19.4

# Hybrid refresh with runtime capture
python scripts/refresh_snapshots.py --core-version v0.19.4 \
  --runtime-object-info-url http://127.0.0.1:8188 \
  --runtime-object-info-version v0.19.4
```

## Artifact Boundaries

| Artifact | Source | Canonical | Packaged |
|---|---|---|---|
| `references/raw/server_endpoints.json` | source | yes | yes |
| `references/raw/js_hooks.json` | source | yes | yes |
| `references/raw/node_api_schema.json` | source + optional runtime | yes | yes |
| `references/raw/object_info_runtime.json` | runtime only | no | no |

`object_info_runtime.json` is a runtime-only capture artifact. It is excluded
from the public artifact packaging pipeline because its contents depend on the
specific ComfyUI instance configuration at capture time.

## One-Command Verification

`scripts/verify/run_all.py` wraps the standard CPU-safe verification sequence:

```bash
python scripts/verify/run_all.py
```

This runs unit tests, cross-references, schema validation, and MkDocs build in
order. It exits non-zero on the first blocking failure.

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
