# Example 7: V3 Caveated Node Pattern

## Caveats

- `io.Schema`, `io.ComfyNode`, and `io.NodeOutput` are pinned to source definitions in the upstream `_io.py` snapshot. Behavior matches the pinned snapshot within the supported pin window; new V3 additions beyond the pin are not yet reflected.
- `ComfyExtension` and `comfy_entrypoint()` are pinned through the current registration page's Python sources, but this example still needs live runtime validation before you treat package discovery as proven in an installed ComfyUI environment.

These caveats mirror the canonical wording in
[`src/content/docs/custom-nodes/registration.md`](../../../src/content/docs/custom-nodes/registration.md).

**Status:** Caveated pattern example
**Level:** Modern V3 shape, runtime validation still required
**Validation tiers:** static, pinned-source, pattern-only caveated; opt-in runtime smoke only after installing the example into a live ComfyUI runtime

## What This Example Is

This directory contains a deliberately small V3-style `io.ComfyNode` pattern
aligned with the retained V3 node-structure and registration pages. It
demonstrates schema-first node shape and `io.NodeOutput` return shape while
leaving installed-runtime discovery proof to opt-in runtime validation.

## Files

- `v3_caveated_node.py` -- minimal `io.ComfyNode` example with schema and execute methods

## What This Example Does Not Prove

- It does not prove installed-runtime discovery through `ComfyExtension` or
  `comfy_entrypoint()` in your local ComfyUI environment.
- It does not replace live validation against your installed ComfyUI version.
- It does not document new V3 APIs beyond the pinned `_io.py` source window.

## Read Next

- [`src/content/docs/custom-nodes/node-structure.md`](../../../src/content/docs/custom-nodes/node-structure.md)
- [`src/content/docs/custom-nodes/registration.md`](../../../src/content/docs/custom-nodes/registration.md)
