# Known Limitations

**Evidence:** Official docs-backed from docs.comfy.org, source-backed from pinned snapshots, and operational guidance for repo-local publication boundaries
**Last Updated:** 2026-04-30

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

## API and Execution Limitations

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

### Runtime `/object_info` is not the canonical published artifact surface

**Source:** `docs/reference/machine-readable-artifacts.md`; `docs/reference/runtime-ci-operations.md`

**Verified in:** current repo-published artifact contract and runtime-capture guidance for the pinned core v0.20.1 / frontend v1.44.13 baseline

**Status:** Publication boundary

**Description:** The repo's canonical published artifact set is intentionally
bounded to the three extracted JSON artifacts documented under
`docs/artifacts/`. Runtime-only `object_info` capture reflects the installed
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
