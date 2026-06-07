# Example 7: V3 Caveated Node Pattern

## Caveats

- `io.Schema`, `io.ComfyNode`, and `io.NodeOutput` are pinned to source definitions in the upstream `_io.py` snapshot. Behavior matches the pinned snapshot within the supported pin window; new V3 additions beyond the pin are not yet reflected.
- `ComfyExtension` and `comfy_entrypoint()` are not yet backed by a pinned Python source; treat this example as illustrative for the shape of the API only and verify against a live ComfyUI runtime before relying on it.

These caveats mirror the canonical wording in
[`src/content/docs/custom-nodes/registration.md`](../../../src/content/docs/custom-nodes/registration.md).

**Status:** Caveated pattern example
**Level:** Modern V3 shape, runtime validation still required
**Validation tiers:** static, pinned-source, pattern-only caveated; opt-in runtime smoke only after installing the example into a live ComfyUI runtime

## What This Example Is

This directory contains a deliberately small V3-style `io.ComfyNode` pattern
aligned with the retained V3 node-structure page. It demonstrates schema-first
node shape and `io.NodeOutput` return shape without claiming that this repository
has pinned every Python-side package discovery behavior for V3.

## Files

- `v3_caveated_node.py` -- minimal `io.ComfyNode` example with schema and execute methods

## What This Example Does Not Prove

- It does not prove full runtime discovery through `ComfyExtension` or
  `comfy_entrypoint()`.
- It does not replace live validation against your installed ComfyUI version.
- It does not document new V3 APIs beyond the pinned `_io.py` source window.

## Read Next

- [`src/content/docs/custom-nodes/node-structure.md`](../../../src/content/docs/custom-nodes/node-structure.md)
- [`src/content/docs/custom-nodes/registration.md`](../../../src/content/docs/custom-nodes/registration.md)
