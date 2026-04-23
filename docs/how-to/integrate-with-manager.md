# Integrate with Manager

**Evidence:** Official docs-backed from docs.comfy.org; Community pattern study based on pinned external version
**Last Updated:** 2026-04-22
**Primary Source:** https://docs.comfy.org/custom-nodes/backend/manager

## Primary Sources

- https://docs.comfy.org/custom-nodes/backend/manager
- https://docs.comfy.org/manager/pack-management
- `https://github.com/ltdrdata/ComfyUI-Manager/tree/491f847bbc286588175695ea43fa4e13cd14a437` (community repo state verified 2026-04-22)

## Scope

ComfyUI Manager is the main distribution path most users expect for custom
node packs. Publishing through the Manager makes installation, upgrades,
disable/enable operations, and dependency setup easier than asking users to
clone a repository by hand.

Two distinct paths matter:

- author-facing publication: make your pack discoverable through Manager
- user-facing management: install, update, and inspect packs from the Manager UI

The official author docs say a pack must live in a git repository and be added
to the Manager list so users can discover it. The newer Manager UI docs also
make an important compatibility point: the new UI installs packs from the
registry-backed Manager flow, not arbitrary git URLs.

The pinned community repo verification is used more narrowly here: it confirms
that the current public Manager repository still exposes the legacy discovery
list (`custom-node-list.json`) and the expected split between frontend and
backend code (`js/comfyui-manager.js`, `glob/manager_server.py`,
`glob/manager_core.py`).

## Required Metadata

The official Manager publication page describes these integration points:

- repository: your custom node should be in a git repository, typically GitHub
- Manager registration: submit a pull request to the ComfyUI-Manager repository
  that adds your pack to `custom-node-list.json`
- `requirements.txt`: optional, but used by Manager for Python dependency
  installation
- `install.py` / `uninstall.py`: optional lifecycle scripts for install and
  uninstall
- `disable.py` / `enable.py`: optional lifecycle scripts for disable and
  re-enable operations
- `node_list.json`: only needed when your node package does not follow the
  conventional node discovery pattern

Update expectations from the docs:

- keep `requirements.txt` as loose as possible to reduce dependency conflicts
- treat lifecycle scripts as optional helpers, not the only cleanup path,
  because users can still delete the directory directly
- if you depend on disable/enable behavior, remember disabled pack folders get
  `.disabled` appended and Comfy ignores them
- if you want the new Manager UI to surface your pack cleanly, make sure the
  package is registered through the supported Manager/registry flow

For end users, the new UI supports:

- searching by node pack or individual node
- installing a selected version
- updating packs with available updates
- finding missing node packs from workflows
- uninstalling installed packs

The same page also notes two limits that affect authors:

- the new UI only supports nodes available through the registry-backed flow
- installing via arbitrary git URL is not offered in the new UI for security
  and stability reasons

## Validation Steps

Use this checklist before claiming Manager support:

- confirm the repo can be cloned cleanly into `ComfyUI/custom_nodes`
- confirm `requirements.txt` installs successfully and does not pin more than
  necessary
- confirm optional `install.py` and `enable.py` are safe to run from the
  package root
- confirm the package still loads if lifecycle scripts are skipped
- add `node_list.json` only if your node mappings are non-standard
- register the pack through the Manager submission path instead of assuming a
  raw git URL is enough
- test a fresh install, update, disable/re-enable, and uninstall path on a
  clean ComfyUI instance if possible

If your pack is not yet available in the registry-backed Manager flow, document
manual installation separately instead of implying the new Manager UI can
install it directly.

## Read Next

- [ComfyUI Manager Deep Dive](../deep-dives/comfyui-manager.md)
- [Ecosystem Map](../ecosystem/map.md)
- Worked example: `examples/custom-nodes/example-5-full-extension-package/` --
  a complete Manager-ready package with lifecycle scripts, multiple nodes,
  and frontend extension
