# Registration

**Evidence:** Official docs-backed from docs.comfy.org
**Last Updated:** 2026-04-21
**Primary Source:** https://docs.comfy.org/custom-nodes/overview

## Primary Sources

- https://docs.comfy.org/custom-nodes/overview
- https://docs.comfy.org/custom-nodes/backend/server_overview
- https://docs.comfy.org/custom-nodes/walkthrough

## Scope

Registration is the step that makes ComfyUI discover your node classes.
The exact mechanism depends on whether the package is using legacy V1 or
modern V3 conventions.

## V3 Registration

In V3, nodes are exposed through a `ComfyExtension` plus a module-level
`comfy_entrypoint()` function.

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
- [V1 to V3 Migration](v1-to-v3-migration.md)
