# ComfyUI Knowledge Base

**Last Updated:** 2026-04-19
**Status:** Phase 1 scaffold
**ComfyUI Version Pin:** TODO: add commit hash or release tag after first snapshot

## Overview

Authoritative, repo-local documentation infrastructure for ComfyUI development topics:
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

## Phase 1 Scope

Phase 1 intentionally provides scaffold and infrastructure only:
- MkDocs site structure
- placeholder documentation pages
- sample JSON reference files
- ad-hoc extraction and generation scripts
- snapshot and workflow placeholders

Actual research-heavy documentation content is future work.

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
- https://github.com/refrance/ProfilerX
