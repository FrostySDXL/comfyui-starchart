# ComfyUI Knowledge Base

**Last Updated:** 2026-04-19
**Status:** Source-backed documentation pass in progress
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
mkdocs serve
python scripts/extract/parse_server.py path/to/server.py --version v0.19.3 --commit 3086026401180c9216bcb6ace442a4e3587d2c66
python scripts/extract/parse_hooks.py path/to/app.ts path/to/comfy.ts path/to/litegraphService.ts --version v1.42.11 --commit 3dc4061d484d61cb89366de25bf5e2f8a65da4d0
python scripts/extract/parse_node_api_schema.py path/to/server.py path/to/_io.py path/to/basic_types.py --version v0.19.3 --commit 3086026401180c9216bcb6ace442a4e3587d2c66
python scripts/generate/md_from_json.py
```

## Current Scope

This repository now includes source-backed coverage for:

- server API endpoints and WebSocket behavior
- hooks and extension points
- custom node development, registration, datatypes, and best practices
- extension architecture patterns and ProfilerX-style monitoring analysis
- practical tutorials and how-to pages for common extension tasks

It also still includes supporting infrastructure for future expansion:

- MkDocs site structure
- machine-readable reference files
- extraction and generation scripts
- snapshot/reference scaffolding for additional source capture

Some areas remain summary-level and should continue to be refined against exact
upstream source snapshots.

## Current Gaps

- extracted endpoint descriptions are present but some routes could benefit from more detailed parameter and response documentation
- extracted references pin core plus official frontend, not every possible upstream package involved in the full product surface
- community repositories remain supplementary examples only
- no automated CI pipeline yet (workflows are planned but not implemented)

## Verification

```bash
python -m unittest discover -s tests
python -m pip install -r requirements.txt
mkdocs build
```

## External Sources

- https://docs.comfy.org/
- https://github.com/Comfy-Org/ComfyUI
- https://registry.comfy.org/
- https://github.com/ryanontheinside/ComfyUI_ProfilerX
