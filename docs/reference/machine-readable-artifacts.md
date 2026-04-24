# Machine-Readable Artifacts

**Evidence:** Operational guidance
**Last Updated:** 2026-04-24

## Scope

This page documents the machine-readable JSON artifacts this repository publishes.
It covers what artifacts exist, what they contain, and how tooling authors can
consume them from the static site or from the repo directly.

## Who This Page Is For

- Tooling authors building ComfyUI integrations, SDKs, or analysis tools
- Extension developers who want to validate assumptions against a pinned API surface
- CI or automation pipelines that need a stable, cited baseline for ComfyUI behavior

## What Artifacts Exist

The repository publishes three canonical artifacts extracted from pinned upstream
snapshots. All paths below are site-relative to the built documentation.

| Artifact | Source | Stable URL |
|----------|--------|------------|
| `server_endpoints.json` | Pinned `server.py` | `artifacts/current/server_endpoints.json` |
| `js_hooks.json` | Pinned frontend TypeScript | `artifacts/current/js_hooks.json` |
| `node_api_schema.json` | Pinned `server.py`, `_io.py`, `basic_types.py` | `artifacts/current/node_api_schema.json` |

Each artifact also has a versioned copy under `artifacts/versions/<key>/`, where
the key includes the pinned core version, frontend version, and extraction date.

### server_endpoints.json

Contains HTTP routes, methods, parameters, and inferred return shapes from the
pinned ComfyUI server source. Useful for:

- generating typed API client stubs
- building route documentation or OpenAPI-like descriptions
- verifying that a ComfyUI instance exposes the expected surface

### js_hooks.json

Contains JavaScript and frontend extension hooks, their signatures, and where
they are defined and invoked in the pinned frontend source. Useful for:

- building a hook explorer or IDE autocomplete data
- validating that a custom extension registers against hooks that exist in the
  pinned version
- tracking frontend integration point changes across versions

### node_api_schema.json

Contains object info fields, I/O types, and basic input shapes from the pinned
core source. Useful for:

- validating node surface assumptions before running a workflow
- building datatype-aware tooling or linting
- comparing schema behavior across ComfyUI versions

## Repo Sources vs Published Copies

The canonical extraction outputs live in `references/raw/` in the repository.
The published copies live under `docs/artifacts/` and are included in the built
site.

| Location | Purpose |
|----------|---------|
| `references/raw/` | Canonical extractor output; versioned in git |
| `docs/artifacts/current/` | Stable current-copy URL for web consumption |
| `docs/artifacts/versions/<key>/` | Immutable snapshot for reproducible builds |
| `docs/artifacts/manifest.json` | Discovery metadata with URLs, versions, and commits |

If you need the exact commit and extraction date for an artifact, read its
`metadata` object or consult `manifest.json`.

## Manifest

`docs/artifacts/manifest.json` (served at `artifacts/manifest.json`) contains:

- `version_key` -- the deterministic key for the current versioned copy
- `artifacts` -- per-artifact entries with:
  - `current_url` and `versioned_url` (relative to the site root, with no leading
    slash, so they resolve correctly on GitHub Pages project sites)
  - `version`, `commit`, `extracted_date`
  - `sources` -- the pinned snapshot file(s) the artifact was extracted from

## Versioning

Artifacts are versioned by the upstream commit and tag they were extracted from,
not by an independent schema version. The version key format is:

```
core-<core-version>_frontend-<frontend-version>_<oldest-extracted-date>
```

When upstream snapshots are refreshed, running the packaging script generates a
new version key and new versioned copies. The `current/` copies are overwritten,
but the versioned copies are preserved until explicitly removed.

## Usage Examples

These examples show how tooling authors can consume the published artifacts.
They are conceptual and lightweight, not a full SDK.

### Generating a typed API client from endpoint metadata

Read `server_endpoints.json` and map each entry to a typed function signature.
The `route`, `method`, `parameters`, and `returns` fields provide enough structure
for OpenAPI-like generation or strongly-typed client stubs.

```python
import json, urllib.request

base = "https://<your-site>"
manifest = json.load(urllib.request.urlopen(f"{base}/artifacts/manifest.json"))
url = manifest["artifacts"]["server_endpoints.json"]["current_url"]
endpoints = json.load(urllib.request.urlopen(f"{base}/{url}"))

for ep in endpoints["endpoints"]:
    print(f"{ep['method']} {ep['route']} -> {ep['returns']['kind']}")
```

### Building a hook explorer from js_hooks.json

Use `js_hooks.json` to populate an autocomplete list or documentation panel for
frontend extension authors. Each hook entry includes `name`, `type`, `description`,
and source locations.

```python
hooks = json.load(urllib.request.urlopen(
    "https://<your-site>/artifacts/current/js_hooks.json"
))

for hook in hooks["hooks"]:
    print(f"{hook['name']} ({hook['type']}): {hook['description']}")
```

### Validating node-surface assumptions from node_api_schema.json

Before submitting a workflow to a ComfyUI instance, compare the node types and
inputs your workflow uses against the pinned schema. This catches mismatches
when the instance version differs from the pinned baseline.

```python
schema = json.load(urllib.request.urlopen(
    "https://<your-site>/artifacts/current/node_api_schema.json"
))

# Example: verify a node type exists in the pinned schema
node_type = "CheckpointLoaderSimple"
assert node_type in schema.get("object_info", {}), f"{node_type} not in schema"
```

## Runtime Artifacts

The repository can also produce `object_info_runtime.json` via live ComfyUI
capture. This file is explicitly excluded from the published artifact surface.
It reflects the specific runtime configuration of the instance it was captured
from and is not a reproducible baseline.

## Caveats

- These artifacts are extracted from pinned source, not from live API responses.
  They describe what the source declares, not what every runtime instance will
  expose.
- Return shape inference is best-effort static analysis. Some endpoints return
  variable structures that cannot be captured precisely without runtime data.
- The `node_api_schema.json` artifact covers built-in types and common patterns.
  Custom node packs may introduce types that do not appear in the pinned snapshot.
- For authoritative human reference, use [docs.comfy.org](https://docs.comfy.org/).
- This repo does not cover end-user workflow tutorials. For those, see community
  resources such as [comfyui-wiki.com](https://comfyui-wiki.com/).

## Read Next

- [Version Pin Status](version-pin-status.md)
- [Source Evidence Policy](source-evidence-policy.md)
- [API Reference: Endpoints](../api/endpoints.md)
- [Hooks: JavaScript Hooks](../hooks/javascript-hooks.md)
