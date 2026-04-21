# JavaScript Hooks

**Evidence:** Official docs-backed from docs.comfy.org
**Last Updated:** 2026-04-21
**Primary Source:** https://docs.comfy.org/custom-nodes/js/javascript_hooks

## Primary Sources

- https://docs.comfy.org/custom-nodes/js/javascript_hooks
- https://docs.comfy.org/custom-nodes/js/javascript_objects_and_hijacking
- `references/snapshots/2026-04-19/comfyui-frontend-v1.42.11/src/scripts/app.ts` (v1.42.11, commit 3dc4061)

## Scope

ComfyUI's JavaScript extension system calls named hooks on every
registered frontend extension by routing through
`invokeExtensions()` or `invokeExtensionsAsync()`. These hooks are the
main supported way to modify client-side behavior without directly
rewriting core UI code.

The official docs explicitly recommend starting with
`beforeRegisterNodeDef`, because it is the most common and usually the
most useful extension point for node-focused UI customization.

## Hook Inventory

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

### `nodeCreated(node)`

Called when an individual node instance is created. Use it for
instance-specific changes rather than class-wide prototype behavior.

### `init()`

Called when the Comfy page is loaded after the graph object exists, but
before nodes are registered or created. This is the earliest lifecycle
hook and is the place most likely to be used for app- or graph-level
setup.

### `setup()`

Called at the end of startup. The official docs recommend this for
adding event listeners or global UI integrations.

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

## Practical guidance

- prefer `beforeRegisterNodeDef` for node-wide behavior
- prefer `nodeCreated` for per-instance adjustments
- use `setup`, not `init`, for logic that assumes startup is complete
- use `afterConfigureGraph` rather than `setup` for workflow-load logic

## Deprecation and caution notes

The official docs now warn that direct hijacking or monkey-patching of
core app methods and prototypes is deprecated and fragile. That pattern
still appears in older examples, but hook-first approaches are the safer
default for future compatibility.

## Read Next

- [Server Hooks](server-hooks.md)
- [Extension Points](extension-points.md)
