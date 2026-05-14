# Install Custom Nodes Safely

**Evidence:** Official docs-backed from docs.comfy.org
**Last Updated:** 2026-05-13
**Primary Source:** https://docs.comfy.org/installation/install_custom_node

## Primary Sources

- https://docs.comfy.org/installation/install_custom_node
- https://docs.comfy.org/manager/install
- https://docs.comfy.org/manager/pack-management

## Scope

Use this page when you want to install a custom node and choose the safest
supported path for your ComfyUI setup.

This page covers end-user installation. It does not explain how to enable
Manager on setups where it is absent, and it does not explain how authors
publish nodes to the registry.

## 1. Choose the install path before you download anything

1. Start with **ComfyUI Manager** when it is already available in your setup.
   The official install guide treats Manager as the recommended path because it
   gives you a UI, version selection, and dependency handling.
2. Use **git clone** when the node is not available through the registry-backed
   Manager flow or when you need a specific repository revision.
3. Use a **ZIP download** only when you cannot use Git. The official guide warns
   that ZIP installs lose version-control benefits and keep dependency handling
   manual.
4. Before using any path, review the node's README and install only from trusted
   authors. The official docs explicitly warn that custom nodes can be malicious.

## 2. Install with Manager when Manager is available

1. Open Manager and search for the node pack or node.
2. Select the node pack you want.
3. Click **Install**, or choose a specific version first if you need one.
4. Restart ComfyUI and refresh the browser if the node pack requires a restart.

Use this path only for nodes available through the registry-backed Manager UI.
If the node you need is missing from the new UI, switch to the manual install
path instead of assuming the UI can install an arbitrary git URL.

## 3. Install manually with Git when Manager is not the right path

1. Copy the repository HTTPS URL from the node's source repository.
2. Go to `ComfyUI/custom_nodes`.
3. Clone the repository.

   ```bash
   git clone <repository-url>
   ```

4. Install the node's Python dependencies in the same Python environment that
   runs ComfyUI.
   - Windows portable:

     ```bash
     python_embeded\python.exe -m pip install -r ComfyUI\custom_nodes\<node-directory>\requirements.txt
     ```

   - Manual install:

     ```bash
     pip install -r requirements.txt
     ```

5. Restart ComfyUI and refresh the browser.
6. Check the startup log for `import failed` errors.

## 4. Use ZIP only as a last-resort manual path

1. Download the repository ZIP from the node's source repository.
2. Extract it.
3. Copy the extracted folder into `ComfyUI/custom_nodes/`.
4. Install dependencies manually in the correct ComfyUI Python environment.
5. Restart ComfyUI and refresh the browser.
6. Verify the node loads without `import failed` errors.

The official docs do not recommend ZIP as the default path because it removes
normal version-control workflows.

## 5. Verify the install before you keep building on it

1. Confirm the node appears in Manager when that interface is available.
2. Confirm ComfyUI starts without `import failed` errors for the node.
3. Confirm any required dependencies finished installing in the correct Python
   environment.
4. If the node ships extra models, templates, or docs, read the node README for
   those follow-up steps.

## What to expect when it works

- the custom node loads after restart
- startup logs do not show `import failed` for that node
- Manager can see the installed node when the registry-backed UI supports it
- you can move on to workflow use or targeted troubleshooting instead of guessing
  whether the install actually finished

## Read Next

- [Enable and Use Manager on Manual or Portable Installs](enable-and-use-manager-on-manual-or-portable-installs.md)
- [Integrate with Manager](integrate-with-manager.md)
- [Troubleshoot Custom Node Breakage](troubleshoot-custom-node-breakage.md)
