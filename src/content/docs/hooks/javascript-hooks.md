---
title: "JavaScript Hooks and Registration"
---

**Evidence:** Official docs-backed from docs.comfy.org
**Last Updated:** 2026-05-19
**Primary Source:** https://docs.comfy.org/custom-nodes/js/javascript_hooks
**Baseline verification status:** Verified against the current pinned baseline: core `v0.21.1`, frontend `v1.45.9`, snapshots `2026-05-18`.

## Primary Sources

- https://docs.comfy.org/custom-nodes/js/javascript_hooks
- https://docs.comfy.org/custom-nodes/js/javascript_overview
- https://docs.comfy.org/custom-nodes/js/javascript_objects_and_hijacking
- `references/snapshots/2026-05-18/comfyui-frontend-v1.45.9/src/scripts/app.ts` (v1.45.9, commit 8562816ffa0d996bd400e517292fee074a6acefa)

## Scope

ComfyUI's JavaScript extension system calls named hooks on every
registered frontend extension by routing through
`invokeExtensions()` or `invokeExtensionsAsync()`. These hooks are the
main supported way to modify client-side behavior without directly
rewriting core UI code.

The official docs explicitly recommend starting with
`beforeRegisterNodeDef`, because it is the most common and usually the
most useful extension point for node-focused UI customization.

## Registration prerequisites

JavaScript hooks run only after the frontend extension is loaded into the
browser-side ComfyUI app.

This page is also the main hook registration reference for the supported
frontend hook surface.

The documented frontend pattern is to register an extension through
`app.registerExtension(...)`. In custom-node packages, official docs and repo
examples also frame `WEB_DIRECTORY` as the server-side export that tells ComfyUI
where the package's frontend JavaScript lives.

Use this page after that loading path already exists. The sections below focus
on which supported hook to choose once the extension is being registered.

## Choose this hook when ...

| Hook | Choose it when | Main scope |
|------|----------------|------------|
| `init` | you need early app or graph setup before node registration starts | app-level startup |
| `beforeRegisterNodeDef` | you need class-wide node behavior or prototype changes | node-type registration |
| `nodeCreated` | you need per-instance node setup | node instance creation |
| `beforeConfigureGraph` | you need to prepare for workflow loading before nodes are configured | workflow load pre-pass |
| `afterConfigureGraph` | you need logic that depends on the loaded workflow being configured | workflow load post-pass |
| `setup` | you need final startup wiring after the rest of startup finishes | late startup and global listeners |

## Hook Inventory

### `init()`

Called when the Comfy page is loaded after the graph object exists, but before
nodes are registered or created. This is the earliest lifecycle hook and is the
right place for app-level setup that must happen before node definitions are
processed.

Choose `init` when the extension needs early access to the app or graph shell.
Do not use it for logic that assumes full startup has already completed.

### `beforeRegisterNodeDef(nodeType, nodeData, app)`

Called once for each node type as Comfy registers available nodes. This
is where most extensions patch or extend node behavior.

Key facts from the official docs:

- `nodeType` acts like the template for all future instances of that node
- `nodeData` exposes Python-defined metadata such as category, inputs,
  and outputs
- `app` is the main frontend application object
- the hook runs for every registered extension and every node type, not
  just the extension's own custom nodes

This is the usual place to add prototype-level behavior that should
apply to all instances of a node class.

Choose this hook when the job is node-type customization rather than one-off
instance setup. The official docs call it the most common and usually the most
useful hook for node-focused UI work.

### `nodeCreated(node)`

Called when an individual node instance is created. Use it for
instance-specific changes rather than class-wide prototype behavior.

Choose this hook when the behavior belongs to a concrete node instance, such as
instance state, per-node widgets, or one-off event wiring.

### `beforeConfigureGraph()`

Called before a workflow is configured into the graph. Use it when workflow-load
logic must run before node configuration finishes.

This is the better fit for pre-load workflow handling than `setup`, because it
belongs to the workflow-loading path instead of general application startup.

### `afterConfigureGraph()`

Called after workflow configuration completes. Use it for workflow-load behavior
that depends on configured nodes already existing.

Choose this hook for post-load reconciliation, graph-aware UI refreshes, or
other logic that should happen after the workflow has been applied.

### `setup()`

Called at the end of startup. The official docs recommend this for
adding event listeners or global UI integrations.

Choose `setup` when the extension needs late startup wiring and expects the rest
of the application bootstrap to be complete.

## Call Order

The official docs include measured hook sequences.

### Initial page load

```text
invokeExtensionsAsync init
invokeExtensionsAsync addCustomNodeDefs
invokeExtensionsAsync getCustomWidgets
invokeExtensionsAsync beforeRegisterNodeDef    [repeated multiple times]
invokeExtensionsAsync registerCustomNodes
invokeExtensionsAsync beforeConfigureGraph
invokeExtensionsAsync nodeCreated
invokeExtensions loadedGraphNode
invokeExtensionsAsync afterConfigureGraph
invokeExtensionsAsync setup
```

### Loading a workflow

```text
invokeExtensionsAsync beforeConfigureGraph
invokeExtensionsAsync beforeRegisterNodeDef   [zero, one, or multiple times]
invokeExtensionsAsync nodeCreated             [repeated multiple times]
invokeExtensions loadedGraphNode             [repeated multiple times]
invokeExtensionsAsync afterConfigureGraph
```

### Adding a new node

```text
invokeExtensionsAsync nodeCreated
```

## Lifecycle guidance

The documented call order supports a simple rule set:

- use `init` for early app-level setup
- use `beforeRegisterNodeDef` for node-type customization
- use `nodeCreated` for per-instance behavior
- use `beforeConfigureGraph` and `afterConfigureGraph` for workflow-load logic
- use `setup` for late startup wiring and global listeners

## Practical guidance

- prefer `beforeRegisterNodeDef` for node-wide behavior
- prefer `nodeCreated` for per-instance adjustments
- use `setup`, not `init`, for logic that assumes startup is complete
- use `afterConfigureGraph` rather than `setup` for workflow-load logic

## Supported-style guidance

The official docs now warn that direct hijacking or monkey-patching of
core app methods and prototypes is deprecated and fragile. That pattern
still appears in older examples, but hook-first approaches are the safer
default for future compatibility.

Prefer the named extension hooks first. Reach for deeper hijacking only when a
supported hook does not cover the case, and treat that fallback as higher-risk
maintenance work rather than a normal extension pattern.

## Subgraph-specific cases

If the hook choice depends on active graph context, subgraph traversal, node
identifier boundaries, or widget-promotion behavior, continue to
[Subgraph Extension Behavior](subgraph-extension-behavior.md). Keep this page
focused on hook selection and lifecycle rather than overloading it with the full
subgraph surface.

## Read Next

- [Server Hooks](server-hooks.md)
- [Extension Points](extension-points.md)
- [Subgraph Extension Behavior](subgraph-extension-behavior.md)
