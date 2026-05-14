# Enable and Use Manager on Manual or Portable Installs

**Evidence:** Official docs-backed from docs.comfy.org
**Last Updated:** 2026-05-13
**Primary Source:** https://docs.comfy.org/manager/install

## Primary Sources

- https://docs.comfy.org/manager/install
- https://docs.comfy.org/manager/pack-management

## Scope

Use this page when Manager is missing or disabled on a manual or portable
ComfyUI install.

This page covers enabling and using Manager on those installs. It does not
repeat the full custom-node install decision tree, and it does not cover author
publication to the registry.

## 1. Identify whether you actually need to enable Manager

1. If you use **ComfyUI Desktop**, stop here. The official install page says
   Manager is already included and enabled by default.
2. If you use **Windows portable** or a **manual install**, continue. The new
   Manager is built into ComfyUI core for those setups, but it still needs to be
   enabled.

## 2. Install Manager dependencies for your install mode

1. For **Windows portable**, install the Manager dependencies with the embedded
   Python:

   ```bash
   .\python_embeded\python.exe -m pip install -r ComfyUI\manager_requirements.txt
   ```

2. For a **manual install**, activate the same environment you use for ComfyUI,
   then install the Manager requirements:

   ```bash
   pip install -r manager_requirements.txt
   ```

3. Do not install these requirements into an unrelated system Python.

## 3. Launch ComfyUI with Manager enabled

1. For **Windows portable**, start ComfyUI with the Manager flag:

   ```bash
   .\python_embeded\python.exe -s ComfyUI\main.py --windows-standalone-build --enable-manager
   ```

2. For a **manual install**, launch ComfyUI with:

   ```bash
   python main.py --enable-manager
   ```

3. If you need the legacy interface instead of the new UI, add:

   ```bash
   --enable-manager-legacy-ui
   ```

4. If you need background Manager features without the UI and endpoints, the
   docs list:

   ```bash
   --disable-manager-ui
   ```

## 4. Use Manager for the workflows the new UI actually supports

1. Search by **node pack** or **individual node**.
2. Install a node pack from the registry-backed catalog.
3. Select a specific version before installing or updating when needed.
4. Use the missing-node prompt to install missing packs from a workflow.
5. Uninstall packs through the Manager UI when you no longer need them.

The official docs are explicit about one boundary: the new UI installs nodes
from the registry-backed flow. It does not provide arbitrary git-URL install in
that UI.

## 5. Verify Manager is working before you rely on it

1. Confirm the Manager interface appears after launch.
2. Confirm you can search for node packs or nodes.
3. Confirm you can inspect versions, install, update, or uninstall supported
   packs.
4. If a pack you need is not available in the registry-backed UI, switch to the
   manual install workflow instead of forcing the new UI to do a git install.

## What to expect when it works

- Manager is visible on your manual or portable install
- registry-backed pack search and version selection are available
- missing-node prompts can route you into supported installs
- you know when to leave Manager and use the manual install flow instead

## Read Next

- [Install Custom Nodes Safely](install-custom-nodes-safely.md)
- [Integrate with Manager](integrate-with-manager.md)
- [Troubleshoot Custom Node Breakage](troubleshoot-custom-node-breakage.md)
