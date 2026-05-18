---
title: "Known Limitations: Service Surface Boundaries"
---

**Evidence:** Official docs-backed from docs.comfy.org
**Last Updated:** 2026-05-18

## Scope

This page groups limitations that belong to official non-local service surfaces,
especially ComfyUI Cloud and the official MCP server. These are official
surfaces, but they are not interchangeable with the local API.

## Cloud API is experimental and subject to change

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

## Some cloud compatibility fields are accepted but ignored

**Source:** https://docs.comfy.org/api-reference/cloud/workflow/submit-a-workflow-for-execution ; https://docs.comfy.org/development/cloud/api-reference

**Verified in:** official Cloud workflow submission and reference docs

**Status:** Behavioral constraint

**Description:** The official cloud docs call out several fields that are
accepted for API compatibility but ignored in cloud behavior. Current
documented examples include `number` and `front` on workflow submission and
`subfolder` for mask upload handling.

**Workaround:** Do not assume local queue-ordering or storage-shape semantics
carry over to cloud. Treat compatibility-only fields as tolerated inputs rather
than behavior guarantees.

**Last verified:** 2026-05-13

---

## Cloud WebSocket `clientId` is currently ignored

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

## Some cloud job/history endpoints are deprecated

**Source:** https://docs.comfy.org/api-reference/cloud/overview

**Verified in:** official Cloud API overview endpoint catalog

**Status:** Behavioral constraint

**Description:** The official cloud API overview currently marks `Get execution
history (v2)` and `Get history for specific prompt` as deprecated.

**Workaround:** Prefer the non-deprecated cloud job endpoints documented in the
current API reference when building new integrations.

**Last verified:** 2026-05-13

---

## MCP saved workflows cannot be executed by ID

**Source:** https://docs.comfy.org/development/cloud/mcp-server

**Verified in:** official ComfyUI MCP Server known limitations

**Status:** Behavioral constraint

**Description:** The official MCP docs state that saved workflows can be browsed
and inspected but cannot be executed directly by ID. The docs attribute this to
saved workflows using ComfyUI graph format rather than ready-to-submit API
format.

**Workaround:** Use saved workflows for inspection or reconstruction, then
submit an API-format workflow rather than expecting direct saved-workflow
execution.

**Last verified:** 2026-05-13

---

## MCP-generated assets do not include workflow JSON metadata

**Source:** https://docs.comfy.org/development/cloud/mcp-server

**Verified in:** official ComfyUI MCP Server known limitations

**Status:** Behavioral constraint

**Description:** The official MCP docs state that images created via the MCP
server do not include workflow JSON in their metadata, so opening them in
ComfyUI does not recover the workflow.

**Workaround:** Preserve the workflow separately if downstream reuse, audit, or
round-trip loading matters.

**Last verified:** 2026-05-13

## Read Next

- [Known Limitations](index.md)
- [Start Here: Tooling Builder](../start-here/tooling-builder.md)
- [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md)
