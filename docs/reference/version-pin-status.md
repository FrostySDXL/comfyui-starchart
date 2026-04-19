# Version Pin Status

**Last Updated:** 2026-04-19
**Primary Sources:** https://github.com/Comfy-Org/ComfyUI, https://github.com/Comfy-Org/ComfyUI/releases, https://docs.comfy.org/changelog

## Current State

This repository now has a pinned extraction baseline for its machine-readable
reference data.

Pinned source set:

- ComfyUI core tag `v0.19.3`
- core commit `3086026401180c9216bcb6ace442a4e3587d2c66`
- official frontend package version `1.42.11`
- official frontend tag `v1.42.11`
- frontend commit `3dc4061d484d61cb89366de25bf5e2f8a65da4d0`

Pinned files now live under `references/snapshots/2026-04-19/` and the extracted
JSON in `references/raw/` points at those snapshot files.

## Included Pinned Snapshot Material

- core: `server.py`, `execution.py`, `pyproject.toml`, `requirements.txt`,
  `app/frontend_management.py`, `comfy_api/latest/_io.py`,
  `comfy_api/latest/_input/basic_types.py`
- frontend: `package.json`, `src/scripts/app.ts`, `src/types/comfy.ts`,
  `src/services/litegraphService.ts`

## What This Pin Covers

- `references/raw/server_endpoints.json` is extracted from the pinned core
  `server.py`
- `references/raw/js_hooks.json` is extracted from the pinned official frontend
  TypeScript files
- `references/raw/node_api_schema.json` is extracted from the pinned core
  `server.py`, `comfy_api/latest/_io.py`, and `basic_types.py`

## Remaining Limits

- many prose docs still cite official docs pages or broad upstream URLs rather
  than exact pinned snapshot paths
- this is a pinned reference baseline for the extracted data, not a claim that
  every documentation page in the repo has been fully rewritten to exact pinned
  citations yet

When exact version behavior matters, prefer the pinned snapshot files first,
then reconcile against official docs and release notes.
