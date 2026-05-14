# Troubleshoot Custom Node Breakage

**Evidence:** Official docs-backed from docs.comfy.org
**Last Updated:** 2026-05-13
**Primary Source:** https://docs.comfy.org/troubleshooting/custom-node-issues

## Primary Sources

- https://docs.comfy.org/troubleshooting/custom-node-issues
- https://docs.comfy.org/manager/troubleshooting

## Scope

Use this page when ComfyUI breaks after adding or updating custom nodes and you
need an official-docs-backed way to identify, isolate, confirm, and recover.

This page stays narrow. It covers custom-node breakage only. If disabling custom
nodes does not change the problem, move to broader ComfyUI troubleshooting
instead of stretching this page beyond its evidence.

## 1. Confirm whether custom nodes are actually the cause

1. Start ComfyUI with custom nodes disabled.
2. Use the install mode that matches your setup:
   - Manual install:

     ```bash
     python main.py --disable-all-custom-nodes
     ```

   - Portable:

     ```bash
     .\python_embeded\python.exe -s ComfyUI\main.py --disable-all-custom-nodes
     ```

3. Test the same failure again.
4. If the issue disappears, continue with this page.
5. If the issue persists, stop treating it as a custom-node problem and route to
   broader troubleshooting.

## 2. Check frontend extensions first when the UI is broken

1. If ComfyUI still opens, disable third-party frontend extensions from the
   Extensions settings area.
2. Restart ComfyUI after the first full disable so the change is actually in
   effect.
3. Test the issue again.
4. If the issue disappears, treat it as a frontend-extension problem and narrow
   the search to those nodes first.
5. If you cannot get into the frontend at all, skip straight to the general
   binary-search flow below.

The official docs call out frontend-extension conflicts as a common update-time
failure mode, so this is the fastest supported branch when the UI itself is the
problem.

## 3. Isolate the offending node with a binary-search workflow

1. Split the current custom nodes into two halves.
2. Re-enable or move back only one half.
3. Restart ComfyUI and test again.
4. If the issue returns, keep searching inside the enabled half.
5. If the issue stays gone, keep searching inside the disabled half.
6. Repeat until one node or one small pack is left.

If you use `comfy-cli`, the official docs also describe its node bisect flow as
an automated way to drive the same isolation process.

## 4. Check the likely failure class before you change more things

1. If the breakage is mostly in the UI, keep suspecting frontend extensions
   first.
2. If startup logs show import or dependency problems, inspect the node's Python
   dependencies and version requirements.
3. If the problem started immediately after a ComfyUI update, distinguish
   **ComfyUI core changes** from **custom-node compatibility lag** instead of
   assuming the core update alone is wrong.
4. If Manager itself is the failing surface, use the official Manager
   troubleshooting page for Manager-specific config, path, SSL, or security-level
   issues.

## 5. Recover with the smallest supported change

1. Update the node if a compatible update is available.
2. If no update exists, remove or disable the node temporarily.
3. Report the issue to the node author with your ComfyUI version, logs, OS, and
   reproduction steps.
4. If you need the feature immediately, look for a replacement node instead of
   repeatedly reinstalling the broken one without new evidence.

## What to expect when it works

- you know whether the failure is really caused by custom nodes
- the suspect node or pack is isolated instead of guessed at
- frontend-extension failures and dependency failures are separated cleanly
- recovery is based on update, removal, replacement, or author escalation rather
  than random reinstall loops

## Read Next

- [Update ComfyUI with Version Awareness](update-comfyui-with-version-awareness.md)
- [Install Custom Nodes Safely](install-custom-nodes-safely.md)
- [Enable and Use Manager on Manual or Portable Installs](enable-and-use-manager-on-manual-or-portable-installs.md)
