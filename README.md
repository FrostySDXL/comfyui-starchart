# ComfyUI Knowledge Base

**Last Updated:** 2026-04-19
**ComfyUI Version Pin:** Core `v0.19.3` (`3086026401180c9216bcb6ace442a4e3587d2c66`) with official frontend `v1.42.11` (`3dc4061d484d61cb89366de25bf5e2f8a65da4d0`) for pinned snapshots and extracted reference data

## Overview

Source-backed, repo-local reference documentation for ComfyUI development topics:
- server API endpoints and WebSocket behavior
- JavaScript and server-side extension hooks
- custom node development patterns and datatypes
- extension architecture patterns and ProfilerX-style metrics
- tutorials, how-to guides, and machine-readable reference data

## Documentation Layers

### Human-readable docs

- Source lives in `docs/`
- Preview locally with `mkdocs serve`

### Machine-readable references

- JSON reference data lives in `references/raw/`
- Snapshots live in `references/snapshots/`
- Helper scripts live in `scripts/extract/` and `scripts/generate/`

## Evidence Model

Use content in this repository with this trust order:

1. official ComfyUI documentation
2. upstream ComfyUI source and release notes
3. this repository's summaries, examples, and extracted references
4. clearly labeled community pattern examples

This repository is intended to be a reviewable working reference for future OSS
ComfyUI projects. It should not claim native or official behavior unless that
behavior is backed by an official docs page or upstream source citation.

## Quick Start

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m mkdocs build
```

Serve locally: `python -m mkdocs serve`

### Extracting references

```bash
python scripts/extract/parse_server.py path/to/server.py --version v0.19.3 --commit 3086026401180c9216bcb6ace442a4e3587d2c66
python scripts/extract/parse_hooks.py path/to/app.ts path/to/comfy.ts path/to/litegraphService.ts --version v1.42.11 --commit 3dc4061d484d61cb89366de25bf5e2f8a65da4d0
python scripts/extract/parse_node_api_schema.py path/to/server.py path/to/_io.py path/to/basic_types.py --version v0.19.3 --commit 3086026401180c9216bcb6ace442a4e3587d2c66
python scripts/generate/md_from_json.py
```

### Refreshing upstream versions

```bash
python scripts/refresh_snapshots.py --core-version v0.19.4
python scripts/refresh_snapshots.py --frontend-version v1.42.12
python scripts/refresh_snapshots.py --core-version v0.19.4 --frontend-version v1.42.12
```

## Current Scope

This repository includes source-backed coverage for:

- server API endpoints and WebSocket behavior
- hooks and extension points
- custom node development, registration, datatypes, and best practices
- extension architecture patterns and ProfilerX-style monitoring analysis
- practical tutorials and how-to pages for common extension tasks

Supporting infrastructure:

- MkDocs site structure with CI build verification
- machine-readable reference files with schema validation
- extraction, generation, and verification scripts
- snapshot/reference scaffolding for additional source capture
- automated upstream pin checking (weekly cron)

## Verification

```bash
# Unit tests
python -m unittest discover -s tests -v

# Build docs
python -m mkdocs build

# Verification scripts (all should exit 0 on clean repo)
python scripts/verify/cross_references.py
python scripts/verify/stale_content.py
python scripts/verify/extraction_idempotency.py
python scripts/verify/upstream_pins.py
python scripts/verify/validate_schema.py
```

## CI

- **`.github/workflows/ci.yml`** -- runs on push/PR to main: tests, MkDocs build, cross-references (blocking), schema validation (blocking), stale content (non-blocking), idempotency (non-blocking), upstream pins (non-blocking). Also supports `workflow_dispatch` with `core_version` and `frontend_version` inputs to trigger `refresh_snapshots.py`.
- **`.github/workflows/weekly-pin-check.yml`** -- runs every Monday at 09:00 UTC and on manual dispatch: checks that pinned commits and tags still resolve in upstream repos.

## Current Gaps

- extracted endpoint descriptions are present but some routes could benefit from more detailed parameter and response documentation
- extracted references pin core plus official frontend, not every possible upstream package involved in the full product surface
- community repositories remain supplementary examples only

## External Sources

- https://docs.comfy.org/
- https://github.com/Comfy-Org/ComfyUI
- https://registry.comfy.org/