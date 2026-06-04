---
title: "Machine-Readable Artifacts"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-06-03
**Baseline verification status:** Re-reviewed for core v0.23.0 / frontend v1.46.6 transition.

## Scope

This page documents the machine-readable JSON artifacts this repository publishes.
It defines the durable artifact taxonomy, discovery rules, support-artifact
boundaries, schema expectations, and version/retention policy.

The published contract is intentionally bounded. These artifacts are a pinned
companion reference for tooling and analysis, not a full OpenAPI-grade or fully
typed description of every ComfyUI behavior.

If you only need the first-use consumer flow, start with
[Start Here: Artifact Consumer](../start-here/artifact-consumer.md) and return
here for the durable contract.

## Who This Page Is For

- Tooling authors building ComfyUI integrations, SDKs, or analysis tools
- Extension developers who want to validate assumptions against a pinned API surface
- CI or automation pipelines that need a stable, cited baseline for ComfyUI behavior

## What Artifacts Exist

The repository publishes four canonical artifacts extracted from pinned upstream
snapshots. All paths below are site-relative to the built documentation.

| Artifact | Source | Stable URL |
|----------|--------|------------|
| `server_endpoints.json` | Pinned `server.py` and `execution.py` | `artifacts/current/server_endpoints.json` |
| `js_hooks.json` | Pinned frontend TypeScript | `artifacts/current/js_hooks.json` |
| `node_api_schema.json` | Pinned `server.py`, `_io.py`, `basic_types.py` | `artifacts/current/node_api_schema.json` |
| `websocket_events.json` | Pinned `server.py`, `main.py`, `execution.py`, `protocol.py`, `comfy_execution/progress.py`, frontend `app.ts` | `artifacts/current/websocket_events.json` |

Each artifact also has a versioned copy under `artifacts/versions/<key>/`, where
the key includes the pinned core version, frontend version, and extraction date.

The repo also publishes non-canonical support artifacts:

| Artifact | Purpose | Stable URL |
|----------|---------|------------|
| `docs-index.json` | Bounded page-level index for routing tools and agents to the right published docs page without full-site scraping, including optional nested tooling-task hints on retained pages | `artifacts/docs-index.json` |
| `delta-summary.json` | Deterministic comparison summary between two artifact baselines | `artifacts/delta-summary.json` |
| `refresh-provenance.json` | Durable evidence about the most recent refresh run, including requested versions, resolved commits, backup path, and runtime-enrichment intent | `artifacts/refresh-provenance.json` |

The repo also publishes bounded JSON Schema files for the four canonical
artifacts:

| Schema file | Covers | Stable URL |
|-------------|--------|------------|
| `server_endpoints.schema.json` | `server_endpoints.json` guaranteed structure | `artifacts/schemas/server_endpoints.schema.json` |
| `js_hooks.schema.json` | `js_hooks.json` guaranteed structure | `artifacts/schemas/js_hooks.schema.json` |
| `node_api_schema.schema.json` | `node_api_schema.json` guaranteed structure | `artifacts/schemas/node_api_schema.schema.json` |
| `websocket_events.schema.json` | `websocket_events.json` guaranteed structure | `artifacts/schemas/websocket_events.schema.json` |

## Contract Tiers

Read each artifact through these tiers:

- **Guaranteed structure**: fields explicitly listed in each artifact's
  `coverage.guaranteed_fields` block.
- **Best-effort fields**: inferred or descriptive fields listed in
  `coverage.best_effort_fields`.
- **Deferred areas**: fidelity gaps listed in `coverage.deferred` that are not
  promised by the current contract.

Tooling can depend on guaranteed structure. Treat best-effort fields as useful
helpers, not strict contracts.

**node_api_schema.json contract:**

| Tier | Fields |
|---|---|
| Guaranteed | `metadata`, `object_info_fields`, `io_types`, `basic_input_shapes`, `coverage` |
| Best-effort | `typed_input_shapes`, `prompt_conditioning_surface.text_input_io_types`, `prompt_conditioning_surface.conditioning_io_types`, `prompt_conditioning_surface.runtime_node_output_summary` |
| Deferred | runtime `/object_info` response, custom node definitions, per-node `INPUT_TYPES` schemas |

The published JSON Schema files intentionally encode only the guaranteed
structure. They do not hard-contract every descriptive or inferred field that
may appear in the current artifacts.

## Minimum Consumer Contract

If you are building strict tooling against the published artifact surface, keep
to these minimum rules:

- start from `artifacts/manifest.json` and the canonical published artifacts it
  points to instead of hardcoding versioned artifact paths
- verify the manifest metadata before trusting a download; at minimum, compare
  the artifact bytes against the manifest `sha256` for canonical current-copy
  URLs
- build strict logic only against guaranteed fields and the published schema
  files; treat best-effort summaries, traceability, and other descriptive fields
  as optional helpers
- do not expect the artifacts to encode HTTP transport setup such as the ComfyUI
  base URL, port, or request headers; for direct local use, the practical
  default is `http://127.0.0.1:8188`, and JSON `POST` calls such as `/prompt`
  should send `Content-Type: application/json`
- treat `docs-index.json`, `delta-summary.json`, and
  `refresh-provenance.json` as support artifacts with narrower guarantees than
  the four canonical extracted artifacts
- treat runtime-only captures such as `object_info_runtime.json` as optional,
  instance-specific inputs rather than part of the canonical published contract

This contract is intentionally lightweight. It defines safe consumption
behavior for this repo's published artifacts. It does not promise an SDK,
OpenAPI-grade semantics, or a full runtime truth layer.

## Interpreting delta-summary.json

Use `delta-summary.json` as a bounded comparison aid between two checked-in
artifact baselines.

- `added` lists keys or entries that appear only in the newer baseline
- `removed` lists keys or entries that disappeared from the newer baseline
- `changed` lists stable keys that still exist but differ structurally between the compared baselines

These changes help answer questions such as whether a route, hook, object-info
field, I/O type, or typed input shape moved between two pinned baselines. They
do not, by themselves, prove semantic compatibility or runtime impact.

Typical interpretation rules:

- `added` often means a tooling consumer may choose to support a new surface, but existing baseline-targeted code may still work unchanged
- `removed` is the clearest signal that baseline-targeted tooling may need an update or fallback path
- `changed` means you should inspect the canonical artifact directly before assuming the difference is breaking, harmless, or runtime-visible

Treat the file as a maintainer and developer comparison shortcut, not as a
complete compatibility guarantee. When the result matters for parser logic,
request shaping, or runtime assumptions, re-check the canonical current or
versioned artifacts directly instead of relying on delta output alone.

### server_endpoints.json

Contains HTTP routes, methods, return kinds, limited inferred response details,
and bounded prompt/queue/history runtime contracts from the pinned ComfyUI server
source. Useful for:

- building route inventories, request scaffolding, or bounded client helpers
- checking that route and response-kind coverage matches the pinned baseline
- inspecting the source-backed `POST /prompt` request/response field inventory
- enumerating prompt validation error `type` strings extracted from server-side
  error dictionaries
- locating the bounded queue/history sections exposed by the pinned server and
  prompt queue implementation
- verifying that a ComfyUI instance exposes the expected surface

Guaranteed fields follow the artifact's `coverage.guaranteed_fields` block.
Return summaries, parameter details, response field details,
`prompt_submission_contract`, `prompt_validation_errors`,
`queue_history_contract`, and traceability markers remain best-effort static
analysis rather than full semantic contracts.

When present, `parameters[]` entries may include:

- `location` such as `path`, `query`, `form`, or `json`
- `required` and `default` when the access pattern makes them obvious
- `allowed_values` when a small literal constraint is directly visible nearby
- `traceability` showing whether the detail came from a route token, request
  access pattern, or another bounded static rule

The runtime contract sections are extracted from the pinned
`references/snapshots/2026-06-03/comfyui-core-v0.23.0/server.py` and
`references/snapshots/2026-06-03/comfyui-core-v0.23.0/execution.py` snapshots.
They add source-backed structure without turning the artifact into an OpenAPI
document:

- `prompt_submission_contract` lists direct JSON request fields observed in
  `post_prompt` plus success/error response keys returned through
  `web.json_response`.
- `prompt_validation_errors` lists source-backed prompt validation error `type`
  strings and their source functions. Runtime custom-node `VALIDATE_INPUTS`
  behavior remains deferred.
- `queue_history_contract` names bounded queue/history areas such as
  `queue_running`, `queue_pending`, `history`, `status`, `task_done`, and
  `flags`. Exact runtime queue tuple contents and node-produced history outputs
  remain deferred.

For mutation endpoints, treat `parameters[].required` and
`prompt_submission_contract.request_fields[].required` as bounded source-access
requiredness hints, not full API-level requiredness contracts. The current
extractor can reliably see route tokens, direct subscripting, `.get(...)` calls,
defaults, and small literal checks, but it does not prove every
branch-conditioned request rule. `POST /prompt` is the clearest example:
the pinned handler only hard-fails when `prompt` is missing, while fields such
as `number`, `front`, `extra_data`, `client_id`, and
`partial_execution_targets` are conditionally consumed. Use the artifact for
route scaffolding and then read the matching prose API page when you need
precise mutation-request semantics.

### js_hooks.json

Contains JavaScript and frontend extension hooks, their signatures, declared
frontend extension fields from `ComfyExtension`, and where those surfaces are
defined and invoked in the pinned frontend source. Useful for:

- building a hook explorer or IDE autocomplete data
- validating that a custom extension registers against hooks that exist in the
  pinned version
- answering which properties a ComfyUI frontend extension can export
- distinguishing lifecycle hooks from declarative UI contribution points such as
  commands, keybindings, menu commands, settings, badges, bottom-panel tabs, and
  action-bar buttons
- tracking frontend integration point changes across versions

This artifact is more structured than the endpoint artifact, but descriptive and
provenance-style fields such as `description`, `defined_in`, `signature`,
`arguments`, `invocation_style`, and `extension_fields[].traceability` should
still be treated according to the artifact's `coverage` block.

The `extension_fields` section preserves raw TypeScript annotations from
`src/types/comfy.ts` as `type_hint` values. It does not expand imported type
definitions such as `ComfyCommand`, `SettingParams`, or `BottomPanelExtension`.
Use `extension_fields[].is_hook` to separate fields that are also lifecycle hook
methods from non-hook declarative contribution points. Invocation evidence and
call style remain in the `hooks` section.

### node_api_schema.json

Contains object info fields, I/O types, and basic input shapes from the pinned
core source. Useful for:

- validating node surface assumptions before running a workflow
- building datatype-aware tooling or linting
- comparing schema behavior across ComfyUI versions
- identifying source-backed text-input and conditioning I/O surfaces before
  falling back to live object-info inspection

This is the strongest pinned-source-derived schema contract in the published
artifact set. It still does not make runtime-only custom-node state canonical by
default.

This surface is extended with richer typed detail where pinned source proves
it, including:

- `io_types[].input_parameter_details` / `output_parameter_details`
- `typed_input_shapes[*].defined_in`
- field-level `traceability` markers for extracted `TypedDict` fields
- `prompt_conditioning_surface`, a best-effort helper that summarizes pinned
  `STRING` widget input parameters and `CONDITIONING` type metadata from `_io.py`
  while keeping per-node output summaries runtime-bounded when optional
  `runtime_object_info` is present

These additions remain source-backed only. They do not imply full runtime node
coverage.

Source-backed from pinned snapshots: the current `_io.py` snapshot defines
`STRING` as an I/O type with a `WidgetInput` carrying parameters such as
`multiline`, `placeholder`, `default`, and `dynamic_prompts`; it also defines
`CONDITIONING` as an I/O type whose `Type` is `CondList`. See
`references/snapshots/2026-06-03/comfyui-core-v0.23.0/comfy_api/latest/_io.py`.

Treat `prompt_conditioning_surface` as routing metadata, not prompt recovery
proof. It can tell tooling which pinned I/O datatypes look text-like or
conditioning-related, and runtime-enriched copies can summarize node output
types from live `object_info`; it cannot prove that every text-bearing node,
custom node, or composed conditioning path has recoverable literal prompt text.

### websocket_events.json

Contains WebSocket JSON lifecycle events and binary preview event contracts
extracted from the pinned core and frontend source. Useful for:

- building execution-monitoring dashboards or progress trackers
- validating that a ComfyUI instance emits the expected event set
- enumerating binary preview event types and their protocol enum values
- understanding the bidirectional `feature_flags` negotiation flow

Guaranteed fields follow the artifact's `coverage.guaranteed_fields` block.
Payload field lists, dynamic dispatch notes, and traceability markers remain
best-effort static analysis rather than full semantic contracts.

The artifact covers both JSON events (such as `status`, `progress`,
`progress_state`, `executing`, `executed`, `execution_start`,
`execution_error`, `execution_interrupted`, `execution_cached`,
`execution_success`, and `feature_flags`) and binary events (such as
`PREVIEW_IMAGE`, `UNENCODED_PREVIEW_IMAGE`, `TEXT`, and
`PREVIEW_IMAGE_WITH_METADATA`).

Source-backed from pinned snapshots:
`references/snapshots/2026-06-03/comfyui-core-v0.23.0/server.py`,
`references/snapshots/2026-06-03/comfyui-core-v0.23.0/main.py`,
`references/snapshots/2026-06-03/comfyui-core-v0.23.0/execution.py`,
`references/snapshots/2026-06-03/comfyui-core-v0.23.0/protocol.py`,
`references/snapshots/2026-06-03/comfyui-core-v0.23.0/comfy_execution/progress.py`,
and `references/snapshots/2026-06-03/comfyui-frontend-v1.46.6/src/scripts/app.ts`.

### delta-summary.json

`delta-summary.json` is a deterministic structural comparison artifact. Its
first version is intentionally narrow: keyed adds/removes/changes and count
summaries for the canonical baseline artifacts.

Use it to answer questions like:

- which endpoint keys were added or removed between two baselines
- which hook names changed
- whether object-info fields, I/O types, or typed input shapes drifted

Do not use it as runtime truth. It compares checked-in artifact baselines only.
When generating this file after a refresh, preserve a copy of the pre-refresh
`references/raw/` directory first and use that preserved copy as `--old`. The
refresh script overwrites `references/raw/` in place. The current refresh helper
creates that ephemeral working copy under the `_refresh_backups/raw_<timestamp>/`
directory inside `references/`.

`delta-summary.json` also remains outside the canonical published contract. It
is not discovered from `manifest.json`, and `verify_artifact_integrity.py` does
not treat it as part of the canonical byte-identity guarantee.

### refresh-provenance.json

`refresh-provenance.json` records operator-facing evidence about the latest
refresh run. It is published under `public/artifacts/` for auditability, but it
is not part of the canonical manifest discovery surface.

The current payload records at least:

- `refresh_date`
- requested core and frontend versions
- resolved core and frontend commits
- the repo-local backup path created before `references/raw/` was overwritten
- whether runtime object-info enrichment was requested and merged
- the next `generate_snapshot_delta_summary.py` command to run when a backup is available
- an ordered `next_steps.recommended_follow_up_commands` sequence assembled from the
  recorded provenance state

The recorded `published` flags are intentionally conservative. Immediately after
`scripts/refresh_snapshots.py` finishes, they should still say the canonical
published artifacts and `delta-summary.json` have not yet been refreshed. Those
truth values only change after the follow-up publication and comparison steps
are run separately.

Use this file as refresh evidence and as a maintainer handoff aid. Do not treat
it as a canonical artifact contract alongside the three primary published JSON
artifacts.

The backup path recorded here is temporary local rollback state, not durable
history. Durable history lives in `references/snapshots/`,
`public/artifacts/versions/`, and the published `refresh-provenance.json`
record itself.

### docs-index.json

`docs-index.json` is a bounded support artifact for tooling and agent consumers
that need lightweight page discovery without scraping the full built site.

It is intentionally narrower than the canonical extracted artifacts. The index
may include only conservative, machine-derivable page metadata such as:

- page title
- repo-relative docs path
- nav family or section
- audience when the page path or repo-local start-here routing makes it obvious
- evidence label
- short scope line when it can be extracted deterministically from the page;
  currently this is limited to the first non-empty paragraph under `## Scope`

The source surface is intentionally limited to hand-authored published docs
pages under `src/content/docs/`. It excludes generated markdown pages, the built
`dist/` output, root-level repo workflow markdown, and any attempt at full-text
page capture.

Use this file to answer questions like:

- which published docs page best fits a tooling or agent task
- which page families exist in the current nav structure
- which pages are reference, troubleshooting, start-here, or tutorial-style
  entry points

Do not treat it as:

- full-text search
- a guarantee that every prose nuance is machine-readable
- a replacement for reading the pages themselves
- a new canonical artifact contract alongside `server_endpoints.json`,
  `js_hooks.json`, `node_api_schema.json`, and `websocket_events.json`

The maintained generation path is:

```bash
python scripts/generate/generate_docs_index.py
```

`docs-index.json` is intentionally excluded from `manifest.json`. It is a
published support artifact for routing and discovery, not part of the canonical
schema-discovery contract. It remains outside the canonical-artifact
byte-identity guarantee enforced for the four extracted JSON artifacts.

## Repo Sources vs Published Copies

The canonical extraction outputs live in `references/raw/` in the repository.
The published copies live under `public/artifacts/` and are included in the
built site.

| Location | Purpose |
|----------|---------|
| `references/raw/` | Canonical extractor output; versioned in git |
| `public/artifacts/current/` | Stable current-copy URL for web consumption |
| `public/artifacts/versions/<key>/` | Immutable snapshot for reproducible builds |
| `public/artifacts/manifest.json` | Discovery metadata with URLs, versions, commits, and SHA-256 checksums for canonical published artifacts |
| `public/artifacts/docs-index.json` | Published support artifact for bounded docs-page discovery |
| `public/artifacts/schemas/` | Checked-in bounded JSON Schema files for the canonical published artifacts |
| `public/artifacts/delta-summary.json` | Deterministic baseline-to-baseline comparison output |
| `public/artifacts/refresh-provenance.json` | Durable published record of the latest refresh run; intentionally outside manifest discovery |

For the four canonical published artifacts, `references/raw/` remains the
canonical repo-local source. `public/artifacts/current/` must stay byte-identical
to those canonical files, and the manifest checksum must match the published
current-copy bytes.

If you need the exact commit, extraction date, or published checksum for an
artifact, read its `metadata` object or consult `manifest.json`.

## Manifest

`public/artifacts/manifest.json` (served at `artifacts/manifest.json`) contains:

- `artifact_schema_version` -- the version of this repo's published artifact
  contract, independent from upstream ComfyUI version pins
- `version_key` -- the deterministic key for the current versioned copy
- `schemas` -- per-artifact schema discovery entries with `schema_url`
- `artifacts` -- per-artifact entries with:
  - `current_url` and `versioned_url` (relative to the site root, with no leading
    slash, so they resolve correctly on GitHub Pages project sites)
  - `sha256` for the bytes served from `current_url`
  - `version`, `commit`, `extracted_date`
  - `sources` -- the pinned snapshot file(s) the artifact was extracted from

Maintainership note: `python scripts/verify/verify_artifact_integrity.py` is a
blocking verifier. It proves the canonical `references/raw/` files, published
`public/artifacts/current/` copies, and manifest `sha256` values remain aligned
for the four canonical artifacts.

`python scripts/verify/validate_schema.py` is the matching blocking verifier for
the schema contract. It validates canonical artifacts against the checked-in
published schema files under `public/artifacts/schemas/`.

`refresh-provenance.json` is intentionally excluded from `manifest.json`. It is
useful published operator evidence, but it is not a canonical extracted artifact
and does not participate in the bounded schema-discovery contract.

`docs-index.json` is also intentionally excluded from `manifest.json`. It is a
published docs-routing aid rather than a canonical extracted artifact.

### docs-index.json tooling metadata

`docs-index.json` now carries the former tooling-routing hints directly on the
retained page entries under an optional nested `tooling_metadata` object.

Every retained published docs page must either carry that `tooling_metadata`
key or remain intentionally bare under the current bounded policy. The allowed
bare class is limited to governance, writing-policy, status, and scope-boundary
pages. In the current retained surface, that means
`reference/source-evidence-policy.md`, `reference/writing-style-guide.md`,
`reference/version-pin-status.md`, and `reference/topic-scope.md` may remain
bare while other retained pages must be enriched.

Each page entry always includes the base page facts:

- `title`
- `path`
- `nav_section`
- `audience`
- `evidence`
- `summary`

When a retained page has curated routing enrichment, `tooling_metadata` can
include:

- `task_intents`
- `related_artifacts`
- `related_routes`
- `related_events`
- `runtime_required`
- `stability_tier`
- `recommended_next_reads`

**`task_intents` controlled vocabulary:**

The following strings are the canonical set of `task_intents` values used in
`docs-index.json`. When adding new pages with curated routing enrichment, use
an existing intent where it fits or add a new value to this list.

| Intent | Meaning |
|---|---|
| `route-docs-task` | Match the page best suited for a given task from a tooling query |
| `discover-routes` | Enumerate or explore API endpoints |
| `discover-artifacts` | Locate canonical published JSON artifacts |
| `discover-hooks` | Enumerate frontend or server-side extension hooks |
| `submit-prompt` | Submit a workflow for execution via the REST API |
| `extract-prompt-text` | Extract the user-facing prompt text from a workflow JSON payload |
| `inspect-prompt-payload` | Inspect the structure and fields of a prompt API request |
| `inspect-object-info` | Read or interpret a node's `object_info` metadata |
| `inspect-conditioning-graph` | Trace how conditioning flows through a prompt graph |
| `understand-architecture` | Understand the high-level execution and pipeline architecture |
| `understand-prompt-topology` | Understand the node graph and prompt submission lifecycle |
| `monitor-execution` | Monitor node execution progress or status |
| `lookup-history` | Retrieve or query prompt execution history |
| `observe-server-lifecycle` | Observe server-side lifecycle events and hooks |
| `build-custom-node` | Build or develop a ComfyUI custom node |
| `debug-api-integration` | Debug integration issues with the ComfyUI REST or WebSocket API |

> **Stability note:** New intents may be added without a schema version bump.
> Tooling consumers should treat unknown intents as a soft signal and fall back
> to other routing signals rather than failing.

Use this merged artifact when a tool needs to answer questions like:

- which docs page best matches a task such as route discovery, prompt
  submission, or execution monitoring
- which canonical artifacts or routes are most related to that page
- whether a task depends on a live runtime rather than only pinned artifacts
- which next pages a tooling consumer should read after the first match

Do not treat it as:

- full-text search
- a replacement for `manifest.json`
- a new canonical extracted artifact contract
- a guarantee that every tooling nuance is fully classified

The maintained generation path is:

```bash
python scripts/generate/generate_docs_index.py
```

The checked-in companion schema remains `artifacts/schemas/docs-index.schema.json`.
Like the artifact itself, it stays outside manifest schema discovery and the
canonical byte-identity guarantee enforced for the four extracted JSON artifacts.

## Versioning

The published surface now exposes two separate version concepts:

- `artifact_schema_version` tracks this repo's bounded artifact contract.
- `version_key` and each artifact entry's `version` / `commit` track the pinned
  upstream ComfyUI baseline used to extract the current files.

Do not treat them as interchangeable. A new upstream pin can reuse the same
`artifact_schema_version` if the guaranteed artifact structure is unchanged. A
schema-version bump can happen without changing the upstream pin if the repo's
guaranteed artifact contract changes.

The `artifact_schema_version` follows semantic versioning for the bounded
published contract:

- increment **MAJOR** for breaking changes to guaranteed fields, required
  structure, or schema-discovery semantics that a consumer must handle
- increment **MINOR** for backward-compatible additions to guaranteed structure
  or manifest-level schema discovery
- increment **PATCH** for non-breaking corrections, clarifications, or schema
  tightening that does not invalidate previously valid guaranteed-shape content

Artifact content is still versioned by the upstream commit and tag they were
extracted from. The version key format is:

```
core-<core-version>_frontend-<frontend-version>_<oldest-extracted-date>
```

When upstream snapshots are refreshed, running the packaging script generates a
new version key and new versioned copies. The `current/` copies are overwritten,
but the versioned copies are preserved until explicitly removed.

Versioned copies under `public/artifacts/versions/` are durable published
history, but that history is intentionally bounded. Keep:

- the current baseline
- the last 2 prior baselines
- any older baseline still referenced by active docs, delta artifacts,
  refresh-provenance records, or migration guidance

This versioned-history policy is distinct from the temporary repo-local refresh
backup directories created during a refresh in the repo's ignored refresh-backup
area. Those backup directories are local rollback and comparison working state,
not published historical artifacts.

## Schema Publication Approach

The schema files under `public/artifacts/schemas/` are checked into the repo as
deterministic source files rather than being generated from Python definitions.
This keeps the published contract explicit, reviewable in diffs, and easy to
inspect without adding a second schema-generation pipeline.

This choice does not widen the contract. The checked-in schemas remain bounded
to guaranteed structure only, while best-effort fields continue to evolve under
the artifact `coverage` blocks and prose guidance.

For baseline-to-baseline comparisons, the proven maintainer sequence is:

1. run `scripts/refresh_snapshots.py` and note the printed repo-local backup directory plus `refresh-provenance.json` output
2. follow the printed `Recommended follow-up commands:` block, which is derived from `refresh-provenance.json`
3. run `scripts/generate/publish_reference_artifacts.py`
4. run `scripts/generate/generate_snapshot_delta_summary.py --old <backup-dir> --new references/raw --output public/artifacts/delta-summary.json`

The `<backup-dir>` value should normally be the auto-created
`_refresh_backups/raw_<timestamp>/` directory inside `references/`. If older
`raw_backup_*` directories directly under `references/` remain on disk from earlier refreshes,
leave them as legacy local working copies unless you intentionally delete or
migrate them after confirming the new path covers your rollback and comparison
needs.

## Bounded Usage Examples

These examples show how tooling authors can consume the published artifacts.
They are conceptual and lightweight. They demonstrate bounded consumption
patterns, not full SDK or OpenAPI generation guarantees.

If you want runnable starter patterns instead of inline conceptual snippets, use
the self-contained consumer examples under `examples/consumers/`:

- Python manifest reader - manifest-first canonical artifact loading with checksum validation
- JavaScript docs-index routing example - optional `docs-index.json` routing plus separate manifest-based artifact discovery
- Shell + jq artifact consumer - manifest-first endpoint discovery with optional live zero-parameter `GET` probing
- Artifacts plus live API example - artifact discovery plus optional live `GET /queue` interaction

Treat those directories as starter patterns, not a formal supported library
surface.

### Building a route inventory from endpoint metadata

Read `server_endpoints.json` and map each entry to a lightweight request helper
or audit report. The guaranteed route, method, and return-kind fields are stable
enough for bounded tooling even when deeper parameter or response semantics are
best-effort.

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
frontend extension authors. Each hook entry includes `name`, `type`,
`description`, and source locations. The `extension_fields` section answers which
fields an extension can export beyond lifecycle hooks.

```python
hooks = json.load(urllib.request.urlopen(
    "https://<your-site>/artifacts/current/js_hooks.json"
))

for hook in hooks["hooks"]:
    print(f"{hook['name']} ({hook['type']}): {hook['description']}")

for field in hooks["extension_fields"]:
    kind = "hook" if field["is_hook"] else "declarative field"
    print(f"{field['name']}: {field['type_hint']} [{kind}]")
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

### Verifying a published artifact checksum from manifest.json

Use the manifest checksum when you need to confirm a downloaded current artifact
matches the bytes the site publishes.

```python
import hashlib, json, urllib.request

base = "https://<your-site>"
manifest = json.load(urllib.request.urlopen(f"{base}/artifacts/manifest.json"))
entry = manifest["artifacts"]["server_endpoints.json"]
artifact_bytes = urllib.request.urlopen(f"{base}/{entry['current_url']}").read()

assert hashlib.sha256(artifact_bytes).hexdigest() == entry["sha256"]
```

### Routing a tooling task with docs-index.json

Use `docs-index.json` when your consumer wants a bounded first-pass routing
hint before reading the matched docs page in full.

```python
import json, urllib.request

base = "https://<your-site>"
docs_index = json.load(
    urllib.request.urlopen(f"{base}/artifacts/docs-index.json")
)

matches = [
    page
    for page in docs_index["pages"]
    if "monitor-execution" in page.get("tooling_metadata", {}).get("task_intents", [])
]

for page in matches:
    metadata = page.get("tooling_metadata", {})
    print(page["path"], metadata.get("related_routes"), metadata.get("recommended_next_reads"))
```

## Runtime Artifacts

The repository can also produce `object_info_runtime.json` via live ComfyUI
capture. This file is explicitly excluded from the published artifact surface.
It reflects the specific runtime configuration of the instance it was captured
from and is not a reproducible baseline. Use it only when your workflow depends
on live installed-node state or hybrid enrichment. See [Object Info](object-info.md).

This runtime-only surface remains optional by design. The canonical artifact
publish step excludes it, `manifest.json` does not discover it, and its
presence depends on whether someone ran the live runtime capture path at all.

## Caveats

- These artifacts are extracted from pinned source, not from live API responses.
  They describe what the source declares, not what every runtime instance will
  expose.
- Manifest `sha256` fields prove byte integrity for the published canonical
  current copies only. They do not provide signatures, provenance attestations,
  or schema-compatibility guarantees by themselves.
- Return shape inference is best-effort static analysis. Some endpoints return
  variable structures that cannot be captured precisely without runtime data.
- Traceability fields indicate where an extracted fact came from, not that the
  repo now guarantees full request validation or runtime response behavior.
- `server_endpoints.json` is suitable for route/method scaffolding and response
  kind checks, not as a complete OpenAPI replacement.
- `js_hooks.json` includes useful descriptive metadata, but some hook and
  extension-field descriptions and provenance details remain best-effort.
- The `node_api_schema.json` artifact covers built-in types and common patterns.
  Custom node packs may introduce types that do not appear in the pinned snapshot.
- For authoritative human reference, use [docs.comfy.org](https://docs.comfy.org/).
- This repo does not cover end-user workflow tutorials. For those, see community
  resources such as [comfyui-wiki.com](https://comfyui-wiki.com/).

## Read Next

- [Start Here: Artifact Consumer](../start-here/artifact-consumer.md)
- [Start Here: Tooling Builder](../start-here/tooling-builder.md)
- [Version Pin Status](version-pin-status.md)
- [Source Evidence Policy](source-evidence-policy.md)
- [Topic Scope](topic-scope.md)
- [API Reference: Endpoints](../api/endpoints.md)
- [Hooks: JavaScript Hooks](../hooks/javascript-hooks.md)
