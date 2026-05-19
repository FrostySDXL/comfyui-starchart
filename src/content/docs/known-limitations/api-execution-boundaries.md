---
title: "Known Limitations: API and Execution Boundaries"
---

**Evidence:** Official docs-backed from docs.comfy.org; Source-backed from pinned snapshots
**Last Updated:** 2026-05-19
**Baseline verification status:** This page contains mixed entry-level verification. Source-backed limitations tied to the current pinned snapshots were re-reviewed against core `v0.21.1`, frontend `v1.45.9`, snapshots `2026-05-18`; docs.comfy.org-backed API-mode guidance still carries the prior-baseline notes shown inline.

## Scope

This page groups limitations that come from the boundary between ComfyUI's HTTP
API, WebSocket execution stream, queue/history storage, and API-only operation.
It keeps only limitations that are source-backed or official-docs-backed.

## Custom nodes with frontend-only features do not work in API mode

**Source:** https://docs.comfy.org/custom-nodes/js/javascript_hooks ; https://docs.comfy.org/development/comfyui-server/comms_routes

**Verified in:** docs.comfy.org pages cited above and this repo's prior pinned core `v0.20.1` / frontend `v1.44.13` baseline. Current-baseline re-review is still pending.

**Status:** Behavioral constraint

**Description:** Nodes that rely on the ComfyUI frontend extension system
(frontend JavaScript hooks, custom UI widgets, WebSocket-based progress
reporting) cannot provide their UI features in API mode. The ComfyUI HTTP API
does not serve the frontend, so extension registration does not occur.

**Workaround:** Use the ComfyUI editor rather than API mode for workflows that
depend on custom frontend extensions. For progress reporting in API mode, use
the official `progress` WebSocket event and poll `GET /queue` while the prompt
is running. After completion, use `GET /history/{prompt_id}` to fetch stored
outputs and metadata.

**Last verified:** 2026-04-30

---

## Tightly connected client-server node behavior is not a safe pure API-mode assumption

**Source:** https://docs.comfy.org/custom-nodes/overview

**Verified in:** docs.comfy.org custom-node overview, with wording kept aligned to this repo's prior pinned core `v0.20.1` / frontend `v1.44.13` API-mode guidance. Current-baseline re-review is still pending.

**Status:** Behavioral constraint

**Description:** The official custom-node overview describes a client-server
model that includes tightly connected client and server behavior as one node
pattern. That is not the same thing as a pure API-mode integration. If a node
or package depends on direct client-server coordination, connected UI behavior,
or frontend-side execution context, it is not safe to assume that a remote
API-only tool can reproduce it.

**Workaround:** Treat pure API mode as a narrower execution surface. If the
workflow depends on connected frontend behavior, use the ComfyUI editor or split
the design into a server-side automation path plus a separate frontend
extension path.

**Last verified:** 2026-05-07

---

## Runtime `/object_info` is not the canonical published artifact surface

**Source:** `src/content/docs/reference/machine-readable-artifacts.md`; `src/content/docs/reference/runtime-ci-operations.md`

**Verified in:** current repo-published artifact contract and runtime-capture guidance for the pinned core `v0.21.1` / frontend `v1.45.9` baseline

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

**Last verified:** 2026-05-19

---

## Initial WebSocket `status` only exposes queue count, not full queue lists

**Source:** `references/snapshots/2026-05-18/comfyui-core-v0.21.1/server.py`

**Verified in:** ComfyUI core `v0.21.1` pinned snapshot

**Status:** Behavioral constraint

**Description:** The initial `status` payload sent on `GET /ws` comes from
`get_queue_info()`. In the pinned server snapshot that structure only carries
`status.exec_info.queue_remaining` plus the resolved `sid`. It does not include
the full `queue_running` and `queue_pending` lists.

**Workaround:** Use `GET /queue` when you need the running or pending queue
entries themselves. Treat the WebSocket `status` snapshot as a lightweight
queue-count signal.

**Last verified:** 2026-05-19

---

## `executed` is not emitted for every completed node

**Source:** `references/snapshots/2026-05-18/comfyui-core-v0.21.1/execution.py`

**Verified in:** ComfyUI core `v0.21.1` pinned snapshot

**Status:** Behavioral constraint

**Description:** In the pinned execution path, ComfyUI only sends an `executed`
event when a node produced UI output. Nodes that run successfully without UI
output still execute, but they do not emit this message.

**Workaround:** Use `executing`, `execution_cached`, `execution_success`, and
history lookup together when you need complete execution tracking. Do not use
`executed` as a proxy for "every node finished."

**Last verified:** 2026-05-19

## Read Next

- [Known Limitations](index.md)
- [WebSocket](../api/websocket.md)
- [History and Queue](../api/history-queue.md)
- [API Integration Troubleshooting](../troubleshooting/api-integration.md)
