---
title: "Registration"
---

**Evidence:** Official docs-backed from docs.comfy.org; Source-backed from pinned snapshots; Community pattern study based on pinned external version
**Last Updated:** 2026-06-26
**Primary Sources:**

- https://docs.comfy.org/custom-nodes/overview
- https://docs.comfy.org/custom-nodes/backend/server_overview
- `references/snapshots/2026-06-26/comfyui-core-v0.26.0/nodes.py` (V1 and V3 custom-node discovery)
- `references/snapshots/2026-06-26/comfyui-core-v0.26.0/comfy_api/latest/__init__.py` (Python `ComfyExtension`)
- `references/snapshots/2026-06-26/comfyui-frontend-v1.47.5/src/types/comfy.ts` (ComfyExtension interface)
- `references/snapshots/2026-06-26/comfyui-core-v0.26.0/comfy_api/latest/_io.py` (io.Schema, io.ComfyNode, NodeOutput)
**Baseline verification status:** Verified against the current pinned baseline: core v0.26.0, frontend v1.47.5, snapshots 2026-06-26.

## Scope

Registration is the step that makes ComfyUI discover your node classes.
The exact mechanism depends on whether the package is using legacy V1 or
modern V3 conventions.

## V3 Registration

In V3, nodes are exposed through a `ComfyExtension` plus a module-level
`comfy_entrypoint()` function.

The current pinned Python source directly handles this path. During custom-node
discovery, `nodes.py` accepts modules that export a callable
`comfy_entrypoint()`, requires it to return a Python `ComfyExtension`, awaits
`get_node_list()`, and registers each returned node class by its schema
`node_id`. The `io.Schema`, `io.ComfyNode`, and `io.NodeOutput` classes used in
V3 nodes are pinned from `comfy_api/latest/_io.py`.

Typical pattern:

```python
from typing_extensions import override
from comfy_api.latest import ComfyExtension, io

class MyNode(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MyNode",
            display_name="My Node",
            category="examples",
            inputs=[io.String.Input("text")],
            outputs=[io.String.Output()],
        )

    @classmethod
    def execute(cls, text):
        return io.NodeOutput(text.upper())


class MyExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [MyNode]


async def comfy_entrypoint() -> MyExtension:
    return MyExtension()
```

Important details:

- `comfy_entrypoint()` must exist at module level
- `get_node_list()` returns the node classes exposed by the extension
- the imported entry module is the package contract ComfyUI discovers

This model keeps registration explicit and package-oriented, instead of
depending on global mapping variables scattered across files.

## Legacy Compatibility

Legacy V1 nodes are usually registered with mapping dictionaries such as:

- `NODE_CLASS_MAPPINGS`
- `NODE_DISPLAY_NAME_MAPPINGS`

Typical pattern:

```python
NODE_CLASS_MAPPINGS = {"MyNodeV1": MyNodeV1}
NODE_DISPLAY_NAME_MAPPINGS = {"MyNodeV1": "My Node V1"}
```

This still matters because a large amount of existing community code uses
it, and much upstream discussion still references these names.

For consumer authoring, place the V1 module or package under
`ComfyUI/custom_nodes/` and restart ComfyUI so startup discovery imports it
again. If the node still does not appear, verify the module exports
`NODE_CLASS_MAPPINGS` and that the mapping points at the class you expect.

## Choosing between V1 and V3

Use V3 when:

- starting a new node package
- documenting modern patterns
- building around `comfy_api.latest`

Stay aware of V1 when:

- reading older repos
- debugging compatibility issues
- migrating established community nodes

## Practical guidance

- keep `node_id` stable once published
- expose only the nodes you intend to support publicly
- treat registration as part of the package's public contract, not just
  implementation detail
- when documenting community code, identify whether it is V1 or V3 first
  before describing how it registers nodes

## Read Next

- [Node Structure](node-structure.md)
- [Development Guide](development-guide.md)
- [Datatypes](datatypes.md)
