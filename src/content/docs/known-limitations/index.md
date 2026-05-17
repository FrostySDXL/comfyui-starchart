---
title: "Known Limitations"
---

**Evidence:** Official docs-backed from docs.comfy.org; Source-backed from pinned snapshots; Operational guidance for repo-local publication boundaries
**Last Updated:** 2026-05-13

## Scope

This page is intentionally small. It only keeps limitations that can be
verified against the repo's pinned ComfyUI snapshots or official docs.

**Tier note:** This page uses two evidence tiers. Tier 1 covers limitations
verified directly against official docs or this repo's pinned snapshots. Tier 2
covers curated community-reported limitations only when the report is specific,
reproducible, and clearly labeled as external evidence. In the current
revision, every listed entry is Tier 1 because no additional Tier 2 item met
the page's evidence threshold.

## Curation Policy

Before adding an entry:

1. Verify the limitation against the current pinned ComfyUI baseline.
2. Cite the exact docs.comfy.org page or pinned snapshot file.
3. State the verified version scope directly.
4. Prefer omission over a broad or weakly sourced claim.

---

## API / Client-Server Boundaries

### Custom nodes with frontend-only features do not work in API mode

**Source:** https://docs.comfy.org/custom-nodes/js/javascript_hooks ; https://docs.comfy.org/development/comfyui-server/comms_routes

**Verified in:** docs.comfy.org pages cited above and this repo's pinned core v0.20.1 / frontend v1.44.13 baseline

**Status:** Behavioral constraint

**Description:** Nodes that rely on the ComfyUI frontend extension system
(frontend JavaScript hooks, custom UI widgets, WebSocket-based progress
reporting) cannot provide their UI features in API mode. The ComfyUI
HTTP API does not serve the frontend, so extension registration does not
occur.

**Workaround:** Use the ComfyUI editor rather than API mode for workflows
that depend on custom frontend extensions. For progress reporting in API
mode, use the official `progress` WebSocket event and poll `GET /queue` while
the prompt is running. After completion, use `GET /history/{prompt_id}` to
fetch stored outputs and metadata.

**Last verified:** 2026-04-30

---

### Tightly connected client-server node behavior is not a safe pure API-mode assumption

**Source:** https://docs.comfy.org/custom-nodes/overview

**Verified in:** docs.comfy.org custom-node overview, with wording kept aligned to this repo's pinned core `v0.20.1` / frontend `v1.44.13` API-mode guidance

**Status:** Behavioral constraint

**Description:** The official custom-node overview describes a client-server model
that includes tightly connected client and server behavior as one node pattern.
That is not the same thing as a pure API-mode integration. If a node or package
depends on direct client-server coordination, connected UI behavior, or
frontend-side execution context, it is not safe to assume that a remote API-only
tool can reproduce it.

**Workaround:** Treat pure API mode as a narrower execution surface. If the
workflow depends on connected frontend behavior, use the ComfyUI editor or split
the design into a server-side automation path plus a separate frontend extension
path.

**Last verified:** 2026-05-07

---

### Runtime `/object_info` is not the canonical published artifact surface

**Source:** `src/content/docs/reference/machine-readable-artifacts.md`; `src/content/docs/reference/runtime-ci-operations.md`

**Verified in:** current repo-published artifact contract and runtime-capture guidance for the pinned core v0.20.1 / frontend v1.44.13 baseline

**Status:** Repo-local publication boundary

**Description:** The repo's canonical published artifact set is intentionally
bounded to the three extracted JSON artifacts documented under
`public/artifacts/`. Runtime-only `object_info` capture reflects the installed
state of a live ComfyUI instance, including custom nodes, so it is useful for
live analysis but is not promoted to the canonical published artifact contract.

**Workaround:** Build against the canonical published artifacts first. Add
runtime `object_info` capture only when your tool depends on live installed-node
state, and treat that runtime file as instance-specific enrichment rather than a
stable published baseline. For routing help, see
[API Integration Troubleshooting](../troubleshooting/api-integration.md) and
[Start Here: Tooling Builder](../start-here/tooling-builder.md).

**Last verified:** 2026-05-03

---

## Cloud / Experimental Surface Limits

### Cloud API is experimental and subject to change

**Source:** https://docs.comfy.org/api-reference/cloud/overview ; https://docs.comfy.org/development/cloud/api-reference

**Verified in:** official ComfyUI Cloud API overview and reference docs

**Status:** Behavioral constraint

**Description:** The official Cloud API docs explicitly describe the API as
experimental and subject to change. They also warn that endpoints,
request/response formats, and behavior may change without notice.

**Workaround:** Treat Cloud API integrations as a separate surface from local
ComfyUI automation. Re-check the current official cloud docs before depending on
request, response, or compatibility details as stable contracts.

**Last verified:** 2026-05-13

---

### Some cloud compatibility fields are accepted but ignored

**Source:** https://docs.comfy.org/api-reference/cloud/workflow/submit-a-workflow-for-execution ; https://docs.comfy.org/development/cloud/api-reference

**Verified in:** official Cloud workflow submission and reference docs

**Status:** Behavioral constraint

**Description:** The official cloud docs call out several fields that are
accepted for API compatibility but ignored in cloud behavior. Current documented
examples include `number` and `front` on workflow submission and `subfolder` for
mask upload handling.

**Workaround:** Do not assume local queue-ordering or storage-shape semantics
carry over to cloud. Treat compatibility-only fields as tolerated inputs rather
than behavior guarantees.

**Last verified:** 2026-05-13

---

### Cloud WebSocket `clientId` is currently ignored

**Source:** https://docs.comfy.org/development/cloud/api-reference

**Verified in:** official Cloud API reference WebSocket section

**Status:** Behavioral constraint

**Description:** The official cloud WebSocket docs state that the `clientId`
parameter is currently ignored and that all connections for a user receive the
same messages.

**Workaround:** Filter progress and lifecycle handling by prompt or job identity
instead of relying on `clientId`-scoped message isolation. Pass a unique
`clientId` only for forward compatibility.

**Last verified:** 2026-05-13

---

### Some cloud job/history endpoints are deprecated

**Source:** https://docs.comfy.org/api-reference/cloud/overview

**Verified in:** official Cloud API overview endpoint catalog

**Status:** Behavioral constraint

**Description:** The official cloud API overview currently marks `Get execution
history (v2)` and `Get history for specific prompt` as deprecated.

**Workaround:** Prefer the non-deprecated cloud job endpoints documented in the
current API reference when building new integrations.

**Last verified:** 2026-05-13

---

## MCP Limits

### MCP saved workflows cannot be executed by ID

**Source:** https://docs.comfy.org/development/cloud/mcp-server

**Verified in:** official ComfyUI MCP Server known limitations

**Status:** Behavioral constraint

**Description:** The official MCP docs state that saved workflows can be browsed
and inspected but cannot be executed directly by ID. The docs attribute this to
saved workflows using ComfyUI graph format rather than ready-to-submit API
format.

**Workaround:** Use saved workflows for inspection or reconstruction, then submit
an API-format workflow rather than expecting direct saved-workflow execution.

**Last verified:** 2026-05-13

---

### MCP-generated assets do not include workflow JSON metadata

**Source:** https://docs.comfy.org/development/cloud/mcp-server

**Verified in:** official ComfyUI MCP Server known limitations

**Status:** Behavioral constraint

**Description:** The official MCP docs state that images created via the MCP
server do not include workflow JSON in their metadata, so opening them in
ComfyUI does not recover the workflow.

**Workaround:** Preserve the workflow separately if downstream reuse, audit, or
round-trip loading matters.

**Last verified:** 2026-05-13

---

## Manager / Registry Boundaries

### New Manager UI does not support arbitrary git URL installs

**Source:** https://docs.comfy.org/manager/pack-management

**Verified in:** docs.comfy.org Manager new UI documentation

**Status:** Behavioral constraint

**Description:** The official Manager new UI only supports installing node
packs that are available through the registry-backed flow. The same docs state
that the new UI does not offer git-based installation.

**Workaround:** Register the package through the supported Manager and registry
flow if you want it to appear in the new UI. Otherwise document manual install
steps separately instead of implying users can paste an arbitrary git URL into
the new Manager interface.

**Last verified:** 2026-04-22

---

### `uninstall.py` is not a guaranteed cleanup path

**Source:** https://docs.comfy.org/custom-nodes/backend/manager

**Verified in:** docs.comfy.org Manager publication documentation

**Status:** Behavioral constraint

**Description:** The official Manager publication docs list `uninstall.py` as
an optional lifecycle script and explicitly warn that users can delete the
directory directly. That means authors cannot rely on `uninstall.py` as the
only cleanup path for critical state.

**Workaround:** Treat `uninstall.py` as best-effort cleanup only. Keep critical
state inside the package directory when possible, or make cleanup idempotent
and recoverable if the directory is removed without running the script.

**Last verified:** 2026-04-22

---

## UI / Execution Event Notes

### Initial WebSocket `status` only exposes queue count, not full queue lists

**Source:** `references/snapshots/2026-04-30/comfyui-core-v0.20.1/server.py`

**Verified in:** ComfyUI core v0.20.1 pinned snapshot

**Status:** Behavioral constraint

**Description:** The initial `status` payload sent on `GET /ws` comes from
`get_queue_info()`. In the pinned server snapshot that structure only carries
`status.exec_info.queue_remaining` plus the resolved `sid`. It does not include
the full `queue_running` and `queue_pending` lists.

**Workaround:** Use `GET /queue` when you need the running or pending queue
entries themselves. Treat the WebSocket `status` snapshot as a lightweight
queue-count signal.

**Last verified:** 2026-04-30

---

### `executed` is not emitted for every completed node

**Source:** `references/snapshots/2026-04-30/comfyui-core-v0.20.1/execution.py`

**Verified in:** ComfyUI core v0.20.1 pinned snapshot

**Status:** Behavioral constraint

**Description:** In the pinned execution path, ComfyUI only sends an
`executed` event when a node produced UI output. Nodes that run successfully
without UI output still execute, but they do not emit this message.

**Workaround:** Use `executing`, `execution_cached`, `execution_success`, and
history lookup together when you need complete execution tracking. Do not use
`executed` as a proxy for "every node finished."

**Last verified:** 2026-04-30

---

## Adding an Entry

When adding an entry, use this template:

```markdown
### Limitation Title

**Source:** [exact docs.comfy.org page or pinned snapshot path]

**Verified in:** [pinned version or exact doc scope]

**Status:** [open, fixed, or behavioral constraint]

**Description:** [clear description of the limitation]

**Workaround:** [if one exists, with caveats]

**Last verified:** [date]
```

---

## Maintenance

Review this page when the repo's ComfyUI version pin changes. Remove entries
that no longer reproduce or that depend on community-only evidence.
