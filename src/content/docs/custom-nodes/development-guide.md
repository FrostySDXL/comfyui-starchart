---
title: "Custom Node Development Guide"
---

# Custom Node Development Guide

**Evidence:** Official docs-backed from docs.comfy.org
**Last Updated:** 2026-05-07
**Primary Source:** https://docs.comfy.org/custom-nodes/overview

## Primary Sources

- https://docs.comfy.org/custom-nodes/overview
- https://docs.comfy.org/custom-nodes/backend/server_overview
- https://docs.comfy.org/custom-nodes/backend/more_on_inputs
- https://docs.comfy.org/custom-nodes/walkthrough

## Scope

ComfyUI custom nodes extend the platform's client-server model. The
server side is Python and performs real work such as model execution,
data processing, and file handling. The client side is JavaScript and
renders the editor, widgets, and graph interactions.

The official overview groups custom nodes into four broad patterns:

- server side only
- client side only
- independent client and server pieces
- tightly connected client and server behavior

Most custom nodes are server-side Python nodes. Those define inputs,
outputs, and an execution function so the graph can pass data through
them like any built-in Comfy node.

This page was re-reviewed against the current pinned repository baseline on
2026-05-07. The guidance here still matches the repo's current core `v0.20.1`
and frontend `v1.44.13` orientation at the level this page intends to cover.

For current development, V3 is the recommended mental model: declare a
schema with `io.Schema`, implement execution with `execute`, and expose
nodes through a `ComfyExtension` entrypoint (observed from the frontend
extension API in pinned TypeScript source; the Python-side entrypoint
convention is documented in community examples). V1 still matters for older
repos and for understanding the large installed base of existing nodes.

## Development Environment

At minimum, a custom node workflow usually needs:

- a local ComfyUI checkout or install for iterative testing
- a Python package or custom node folder that ComfyUI can import
- a small test workflow that exercises the new node
- source inspection of built-in nodes and current docs when behavior is
  unclear

Practical iteration loop:

1. define the node's inputs and outputs
2. implement the execution method
3. restart or reload ComfyUI as needed
4. add the node to a minimal workflow
5. verify execution, caching behavior, and UI presentation

If the node also needs custom UI behavior, pair the Python node with a
frontend extension rather than trying to force server code to solve UI
concerns by itself.

## Core server-side concepts

The official backend docs still explain the classic server-side model
well:

- `INPUT_TYPES` defines required, optional, and hidden inputs in V1
- `RETURN_TYPES` defines output datatypes
- `RETURN_NAMES` optionally labels outputs
- `CATEGORY` controls Add Node menu placement
- `FUNCTION` names the method called at execution time

The same underlying ideas still matter in V3, but they move into
`io.Schema` and a fixed `execute` contract instead of class attributes
and mapping dictionaries.

The backend docs also call out execution-control features that remain
important conceptually:

- output nodes drive backward execution planning
- cache behavior depends on whether inputs changed
- validation can happen before execution
- hidden inputs can inject prompt, metadata, and node identity

## V1 vs V3

### V1

Legacy V1 nodes are plain Python classes that typically define:

- `INPUT_TYPES()`
- `RETURN_TYPES`
- `RETURN_NAMES`
- `CATEGORY`
- `FUNCTION`

They return plain tuples and are registered through
`NODE_CLASS_MAPPINGS` and related dictionaries.

### V3

V3 nodes inherit from `io.ComfyNode` and typically provide:

- `define_schema()` returning `io.Schema`
- `execute()` returning `io.NodeOutput(...)`
- registration through `ComfyExtension` and `comfy_entrypoint()` (observed from
  pinned frontend TypeScript source and community examples; see caveats in
  [Registration](registration.md))

This model is more explicit, more structured, and better aligned with
newer ComfyUI extension guidance.

### Migration mindset

When reading older repos, assume V1 until proven otherwise. When writing
new docs or new extensions, treat V3 as the preferred target unless you
have a compatibility reason to stay with V1.

## Important constraints

- nodes that depend on direct client-server coordination are not suitable
  for pure API-mode use
- backend validation and type handling can differ from what the frontend
  appears to allow, especially with flexible or wildcard inputs
- custom nodes should expose the narrowest, clearest interface possible
  so caching and graph reasoning stay predictable

## Read Next

- [Node Structure](node-structure.md)
- [Registration](registration.md)
