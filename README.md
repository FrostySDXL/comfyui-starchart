# ComfyUI Knowledge Base

**Last Updated:** 2026-04-19
**Status:** Source-backed documentation pass in progress
**ComfyUI Version Pin:** Track against cited upstream docs pages and release notes until a repo snapshot pin is added

## Overview

Authoritative, repo-local documentation for ComfyUI development topics:
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

## Quick Start

```bash
python -m pip install -r requirements.txt
mkdocs serve
python scripts/extract/parse_server.py path/to/ComfyUI/server.py
python scripts/extract/parse_hooks.py path/to/ComfyUI/web/app.js
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
