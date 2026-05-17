---
title: "Integrate with Manager"
---

# Integrate with Manager

**Evidence:** Official docs-backed from docs.comfy.org; Community pattern study based on pinned external version
**Last Updated:** 2026-05-13
**Primary Source:** https://docs.comfy.org/manager/pack-management

## Primary Sources

- https://docs.comfy.org/manager/pack-management
- https://docs.comfy.org/registry/publishing
- https://docs.comfy.org/registry/specifications
- `https://github.com/ltdrdata/ComfyUI-Manager/tree/491f847bbc286588175695ea43fa4e13cd14a437` (community repo state verified 2026-04-22)

## Scope

Use this page when you are deciding how a custom node should fit the current
Manager and registry ecosystem.

This page is author-facing. It explains the boundary between Manager-compatible
distribution and registry-backed publication. It does not reteach end-user
installation, and it does not replace the step-by-step registry publishing
workflow.

## 1. Decide which outcome you are targeting

1. If you want users to install, update, and uninstall your pack through the
   **new Manager UI**, plan for the **registry-backed flow**.
2. If you only want to document a repository that advanced users can clone by
   hand, keep that as a **manual install path** and document it separately.
3. Do not imply those two outcomes are interchangeable. The official docs say
   the new Manager UI does not install arbitrary git URLs.

## 2. Prepare the repository for Manager-adjacent distribution

The official docs describe these integration points:

- keep the custom node in a git repository
- add `requirements.txt` when Python dependencies need installation
- add `install.py` or `uninstall.py` only when lifecycle automation is useful
- add `disable.py` or `enable.py` only when you need explicit disable/re-enable
  behavior
- add `node_list.json` only when your node package does not follow the standard
  discovery pattern

Keep `requirements.txt` as loose as possible. The official guidance calls this
out to reduce dependency conflicts.

## 3. Match your claims to the Manager UI boundary

1. Treat **registry-backed installation** as the supported new-UI path.
2. Treat **manual git install** as a separate fallback for packs that are not in
   the registry-backed flow.
3. If your pack is not yet in the registry-backed flow, say that clearly in your
   README or docs instead of implying the new UI can install it directly.

For end users, the official pack-management page says the new UI supports:

- search by node pack or individual node
- selected-version install
- updates for installed packs
- missing-node pack discovery from workflows
- uninstall for installed packs

## 4. Use registry publication when you want new-UI discoverability

1. Add the required `pyproject.toml` and compatibility metadata.
2. Create a publisher and publishing API key.
3. Publish through the registry flow documented by ComfyUI.
4. Test the package in the supported Manager-facing path after publication.

The detailed step sequence lives on [Publish a Custom Node to the Registry](publish-a-custom-node-to-registry.md).

## 5. Keep community-pattern observations secondary

The pinned community repo verification is used more narrowly here: it confirms
that the current public Manager repository still exposes the legacy discovery
list (`custom-node-list.json`) and the expected split between frontend and
backend code (`js/comfyui-manager.js`, `glob/manager_server.py`,
`glob/manager_core.py`).

Use that community repo state as a secondary implementation observation. Do not
use it to overstate what the new official UI promises.

## Validation Steps

Use this checklist before claiming Manager-compatible distribution:

- confirm the repo can be cloned cleanly into `ComfyUI/custom_nodes`
- confirm `requirements.txt` installs successfully and does not pin more than
  necessary
- confirm optional `install.py` and `enable.py` are safe to run from the
  package root
- confirm the package still loads if lifecycle scripts are skipped
- add `node_list.json` only if your node mappings are non-standard
- publish through the supported Manager/registry path instead of assuming a raw
  git URL is enough for the new UI
- test a fresh install, update, disable/re-enable, and uninstall path on a
  clean ComfyUI instance if possible

If your pack is not yet available in the registry-backed Manager flow, document
manual installation separately instead of implying the new Manager UI can
install it directly.

## Read Next

- [Publish a Custom Node to the Registry](publish-a-custom-node-to-registry.md)
- [Install Custom Nodes Safely](install-custom-nodes-safely.md)
- [ComfyUI Manager Deep Dive](../deep-dives/comfyui-manager.md)
- [Ecosystem Map](../ecosystem/map.md)
- Worked example: `examples/custom-nodes/example-5-full-extension-package/` --
  a complete Manager-ready package with lifecycle scripts, multiple nodes,
  and frontend extension
