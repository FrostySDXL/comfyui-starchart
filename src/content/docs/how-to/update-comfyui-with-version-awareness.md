---
title: "Update ComfyUI with Version Awareness"
---

**Evidence:** Official docs-backed from docs.comfy.org
**Last Updated:** 2026-05-13
**Primary Source:** https://docs.comfy.org/installation/update_comfyui

## Primary Sources

- https://docs.comfy.org/installation/update_comfyui
- https://docs.comfy.org/changelog/index

## Scope

Use this page when you want to update ComfyUI without mixing together install
mode, release line, code updates, and dependency updates.

This page covers official update flows by install mode. It does not replace the
troubleshooting workflow for custom node failures after an update.

## 1. Check which install mode and release line you are on

1. Identify whether you run **Desktop**, **Windows portable**, or a **manual
   git install**.
2. Decide whether you want the **development/nightly** line or a **stable
   release** line.
3. Review the repo's [Version History](../reference/version-history.md) when you
   need release-line context before switching versions or expecting a feature.

The official docs distinguish these release expectations clearly: Desktop tracks
stable releases, while portable and manual installs are the paths that expose
the latest development updates more directly.

## 2. Update Desktop the Desktop way

1. Confirm automatic updates are enabled in Desktop settings.
2. If needed, use **Menu → Help → Check for Updates**.
3. Let Desktop handle the update flow for code and dependencies.
4. If you need features that exist only on newer development builds, do not
   assume Desktop has them yet. Check the release line first.

## 3. Update Windows portable with the correct script

1. Go to the `update` folder in your portable install.
2. Use `update_comfyui.bat` for the latest development version.
3. Use `update_comfyui_stable.bat` when you want the latest stable release.
4. Use `update_comfyui_and_python_dependencies.bat` only when you explicitly
   need the broader dependency refresh.

The official docs warn that the full dependency script is riskier because it can
reinstall dependencies, overwrite manual package choices, and break custom nodes
that rely on specific versions.

## 4. Update a manual git install in two layers

1. Activate the same virtual environment or Conda environment that runs
   ComfyUI.
2. Pull the latest code:

   ```bash
   git pull
   ```

3. Update dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Restart ComfyUI.
5. If you need a specific version instead of the latest code, inspect git
   history and switch deliberately instead of mixing release lines by accident.

## 5. Treat dependencies as part of the update, not an optional extra

1. Update the **core code**.
2. Update the **core dependencies** from `requirements.txt`.
3. If a feature seems missing after `git pull`, verify that dependency updates
   also succeeded.
4. If you are on Desktop, remember dependency handling is normally automatic.

The official docs call out several dependency-backed surfaces that can look
broken when only the code updated, including frontend functionality, workflow
templates, and embedded docs.

## 6. Confirm the result before moving on

1. Restart ComfyUI.
2. Confirm the feature or fix you expected is present on the release line you
   chose.
3. If you updated manually, confirm dependency installation completed in the
   correct environment.
4. If problems start after the update, move to the custom-node troubleshooting
   workflow instead of turning this page into a rollback guide.

## What to expect when it works

- ComfyUI starts on the release line you intended
- the code and dependency layers match the update path you used
- Desktop users stay on the stable-desktop flow instead of expecting nightly
  behavior automatically
- manual and portable users know whether they chose stable or nightly and can
  route to troubleshooting only if the update result is bad

## Read Next

- [Troubleshoot Custom Node Breakage](troubleshoot-custom-node-breakage.md)
- [Install Custom Nodes Safely](install-custom-nodes-safely.md)
- [Version History](../reference/version-history.md)
