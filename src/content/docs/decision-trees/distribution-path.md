---
title: "Decision Tree: Choosing a Distribution Path"
---

**Evidence:** Official docs-backed from docs.comfy.org
**Last Updated:** 2026-05-18
**Primary Sources:** https://docs.comfy.org/manager/pack-management, https://docs.comfy.org/registry/publishing, https://docs.comfy.org/registry/specifications

## Overview

This page helps custom node and extension authors decide whether they need a
local-only package, a manual public repository, or the registry-backed Manager
distribution path.

Work through the questions in order. Each branch ends with the docs surface that
matches the distribution outcome.

## Question 1: Is This Only for You or a Private Team?

### Yes -- I only need a local or private install path

Keep the package on a manual install path.

- document the clone or copy steps clearly
- keep the package loadable in `custom_nodes`
- test installation on a clean ComfyUI instance before sharing internally

Read next:

- [Install Custom Nodes Safely](../how-to/install-custom-nodes-safely.md)
- [Troubleshoot Custom Node Breakage](../how-to/troubleshoot-custom-node-breakage.md)

### No -- I want other users to discover or install it more broadly

Go to Question 2.

---

## Question 2: Do You Want the New Manager UI to Install It Directly?

### Yes -- discoverability in the supported Manager flow matters

Use the registry-backed publication path.

- prepare the repository metadata the registry expects
- create the publisher identity and API key
- publish through the registry workflow instead of assuming a raw git URL is enough

Read next:

- [Integrate with Manager](../how-to/integrate-with-manager.md)
- [Publish a Custom Node to the Registry](../how-to/publish-a-custom-node-to-registry.md)

### No -- a public repository with manual install instructions is enough

Go to Question 3.

---

## Question 3: Do You Still Want to Be Manager-Adjacent Later?

### Yes -- I want the repo structured so a later registry move is easier

Prepare the repo with the usual distribution hygiene now:

- keep dependencies in `requirements.txt` only when needed
- add lifecycle scripts only when they provide real value
- keep install instructions honest about the current manual path

Then read:

- [Integrate with Manager](../how-to/integrate-with-manager.md)

### No -- I only need a documented public manual install path

Keep the scope narrow:

- document the supported ComfyUI version clearly
- describe installation, update, and removal by hand
- do not claim Manager new-UI support if the package is not registry-published

Then read:

- [Install Custom Nodes Safely](../how-to/install-custom-nodes-safely.md)

---

## Decision Summary

| Situation | Path |
|---|---|
| local experiment or private team package | manual local install |
| public package, no new-UI install requirement | documented manual install repo |
| package that should appear in the supported Manager flow | registry-backed publication |
| package that is manual now but may move later | manual now, Manager-aligned structure |

## Read Next

- [Integrate with Manager](../how-to/integrate-with-manager.md)
- [Publish a Custom Node to the Registry](../how-to/publish-a-custom-node-to-registry.md)
- [Start Here: Custom Node Author](../start-here/author.md)
