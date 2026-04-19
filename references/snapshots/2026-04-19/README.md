# Snapshot: 2026-04-19

Pinned upstream source files used for the current extracted reference baseline.

## Pinned Versions

- ComfyUI core tag: `v0.19.3`
- ComfyUI core commit: `3086026401180c9216bcb6ace442a4e3587d2c66`
- Official frontend tag: `v1.42.11`
- Official frontend commit: `3dc4061d484d61cb89366de25bf5e2f8a65da4d0`

## Snapshot Layout

- `comfyui-core-v0.19.3/`
  - `server.py`
  - `execution.py`
  - `pyproject.toml`
  - `requirements.txt`
  - `app/frontend_management.py`
  - `comfy_api/latest/_io.py`
  - `comfy_api/latest/_input/basic_types.py`
- `comfyui-frontend-v1.42.11/`
  - `package.json`
  - `src/scripts/app.ts`
  - `src/types/comfy.ts`
  - `src/services/litegraphService.ts`

## Extraction Inputs

- `references/raw/server_endpoints.json` <- core `server.py`
- `references/raw/js_hooks.json` <- frontend `app.ts`, `comfy.ts`, `litegraphService.ts`
- `references/raw/node_api_schema.json` <- core `server.py`, `_io.py`, `basic_types.py`
