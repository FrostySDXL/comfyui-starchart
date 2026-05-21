---
title: "Custom Node and Extension Boundaries"
---

**Evidence:** Official docs-backed from docs.comfy.org; Source-backed from pinned snapshots
**Last Updated:** 2026-05-20
**Baseline verification status:** Verified against the current pinned baseline: core `v0.21.1`, frontend `v1.45.9`, snapshots `2026-05-18`.

## Scope

This page routes readers who are mixing together server-side nodes, frontend
extensions, and distribution assumptions. It stays at the boundary level and
points onward to the deeper authoring pages.

## Problem: I am not sure whether this belongs in a custom node or a frontend extension

Put execution logic, inputs, outputs, and data processing in the Python node.
Put editor UI changes, custom widgets, sidebar behavior, and graph interactions
in a frontend extension. Some packages need both, but they are still different
layers with different hooks and runtime constraints.

Read next:

- [Start Here: Custom Node Author](../start-here/author.md)
- [Start Here: Extension Developer](../start-here/extension-developer.md)
- [Custom Node Development Guide](../custom-nodes/development-guide.md)

## Problem: I am reading V1 examples but planning a new package

Older repositories and tutorials still use V1 class mappings. New work should
usually read those examples as mental-model material, then map the design to
the repo's current V3-oriented guidance.

If you need the legacy V1 contract itself, start with the repo's single
landing page for that surface. If your package is hybrid and also registers a
custom route, keep the node contract and the route surface separate in your
mental model.

Read next:

- [V1 Custom Node Reference](../custom-nodes/v1-reference.md)
- [Node Structure](../custom-nodes/node-structure.md)
- [Registration](../custom-nodes/registration.md)
- [V1 to V3 Migration](../custom-nodes/v1-to-v3-migration.md)

## Problem: I assumed Manager distribution rules are the same as local development

Local development only needs a working ComfyUI installation and a loadable node
or extension package. Manager or registry distribution adds packaging and
publication expectations that do not apply to a private local prototype.

Read next:

- [Integrate with Manager](../how-to/integrate-with-manager.md)
- [Start Here: Custom Node Author](../start-here/author.md)
- [Start Here: Extension Developer](../start-here/extension-developer.md)
