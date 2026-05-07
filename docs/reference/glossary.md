# Glossary

**Evidence:** Operational guidance
**Last Updated:** 2026-05-03

## Scope

This glossary defines repeated repository and artifact terms that appear across
the docs. It is an orientation aid, not a tutorial or a second reference set.

## Terms

### Pinned snapshot

A checked-in copy of upstream ComfyUI source stored under
`references/snapshots/`. The repo uses pinned snapshots to make extracted docs
and artifacts reproducible.

### Source-backed

A label used when a behavior claim is derived from official ComfyUI docs or a
pinned upstream source citation. See the
[Source Evidence Policy](source-evidence-policy.md).

### Operational guidance

A label used for repo-local process, maintenance, and workflow pages. It does
not raise the trust level of a ComfyUI behavior claim.

### Canonical raw artifact

A repo-local JSON output under `references/raw/` that acts as the canonical
extractor result before publication to `docs/artifacts/`.

### Extracted artifact

A JSON file produced by an extractor script from pinned source snapshots.
Examples include `server_endpoints.json`, `js_hooks.json`, and
`node_api_schema.json`.

### Published artifact

A checked-in JSON file served from `docs/artifacts/` as part of the built site.
Published artifacts mirror the bounded web-consumption surface.

### Artifact schema version

The version of this repo's bounded published artifact contract. It is separate
from the upstream ComfyUI version pin.

### Version key

The deterministic identifier used for versioned published artifact copies under
`docs/artifacts/versions/<key>/`.

## Read Next

- [Machine-Readable Artifacts](machine-readable-artifacts.md)
- [Source Evidence Policy](source-evidence-policy.md)
- [What's New](../whats-new/index.md)
