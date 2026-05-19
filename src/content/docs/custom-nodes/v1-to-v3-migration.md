---
title: "V1 to V3 Migration Guide"
---

**Evidence:** Official docs-backed (migration steps); Community pattern studies (case studies)
**Last Updated:** 2026-05-19
**Primary Source:** https://docs.comfy.org/custom-nodes/backend/migration
**Baseline verification status:** Verified against the current pinned baseline: core `v0.21.1`, frontend `v1.45.9`, snapshots `2026-05-18`.

## Primary Sources

- https://docs.comfy.org/custom-nodes/overview
- https://docs.comfy.org/custom-nodes/backend/migration
- `references/snapshots/2026-05-18/comfyui-core-v0.21.1/comfy_api/latest/_io.py`

## Scope

V1 and V3 refer to two custom node authoring models in ComfyUI. V1 is the
legacy class-attribute model. V3 is the structured schema-and-execute model
introduced in newer ComfyUI versions.

This guide shows how to migrate a V1 node to V3. The two models produce
equivalent behavior -- V3 is not a new execution engine, but a more explicit
and structured registration API.

## When to Migrate

Target V3 for new nodes. Migrate existing V1 nodes when:

- you are already updating the node for other reasons
- you need a feature only available in V3 (such as explicit schema validation)
- you are publishing a new version and want the cleaner API

Do not migrate purely for the sake of migrating -- the V1 model still works
and is not deprecated.

## V1 Node Anatomy

A V1 node is a Python class with class-level attributes plus a callable
`INPUT_TYPES()` definition:

```python
class MyNode:
    CATEGORY = "MyNodes"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    FUNCTION = "process"

    def process(self, image, strength=1.0):
        # execution logic
        return (result,)
```

Registration happens through module-level dictionaries:

```python
NODE_CLASS_MAPPINGS = {"MyNode": MyNode}
NODE_DISPLAY_NAME_MAPPINGS = {"MyNode": "My Node"}
```

The pinned core calls `obj_class.INPUT_TYPES()` and `class_def.INPUT_TYPES()` at
runtime. For that reason, this repo treats the callable form as the preferred
copy-safe V1 example pattern. If you see `INPUT_TYPES = {...}` in older prose,
read it as shorthand for the dict shape, not as this repo's preferred runnable
example form.

## V3 Node Anatomy

For this repo's documented V3 surface, a V3 node inherits from
`io.ComfyNode`, declares typed inputs and outputs with `io.Schema`, and uses
an `execute()` signature whose parameter names match the input IDs.

> **Caveat:** The `ComfyExtension` class and `comfy_entrypoint()` convention
> shown in the V3 sketches below are not directly pinned from a Python source
> file. See the caveat in [Registration](registration.md) for the full
> explanation.

This is the copy-safe migration target used throughout the repo:

```python
from comfy_api.latest import ComfyExtension, io
from typing_extensions import override


class MyNode(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MyNode",
            display_name="My Node",
            category="MyNodes",
            inputs=[
                io.Image.Input("image"),
                io.Float.Input("strength", default=1.0, min=0.0, max=10.0),
            ],
            outputs=[io.Image.Output("output_image")],
        )

    @classmethod
    def execute(cls, image, strength=1.0):
        result = image * strength
        return io.NodeOutput(result)


class MyExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [MyNode]


async def comfy_entrypoint() -> MyExtension:
    return MyExtension()
```

## Step-by-Step Migration

### 1. Replace Class Attributes with `define_schema()`

V1 class attributes become schema inputs:

| V1 | V3 |
|----|----|
| `INPUT_TYPES` required entry | `io.<Type>.Input("...")` |
| `INPUT_TYPES` optional entry | `io.<Type>.Input("...", default=...)`; add `optional=True` when the socket itself may be disconnected |
| `RETURN_TYPES` | typed `io.<Type>.Output("...")` object in `outputs` |
| `CATEGORY` | `category` field in `io.Schema(...)` |
| `FUNCTION` | fixed `execute()` method name |

### 2. Change Inheritance

```python
# V1
class MyNode:

# V3
class MyNode(io.ComfyNode):
```

### 3. Move Execution Logic

V1 method name (from `FUNCTION`) becomes `execute()`. In the V3 shape this repo
documents, ComfyUI passes schema inputs to `execute()` as keyword arguments, so
the method signature should match the input IDs:

```python
# V1
def process(self, image, strength=1.0):
    result = image * strength
    return (result,)

# V3
@classmethod
def execute(cls, image, strength=1.0):
    result = image * strength
    return io.NodeOutput(result)
```

`_io.py` also shows that raw tuples are normalized into `io.NodeOutput`, but the
repo's V3 references use `io.NodeOutput(...)` explicitly because it is clearer
and safer in migration examples.

### 4. Update Registration

> **Caveat:** The `ComfyExtension` class and `comfy_entrypoint()` convention
> are not directly pinned from a Python source file. See the caveat in
> [Registration](registration.md).

```python
# V1
NODE_CLASS_MAPPINGS = {"MyNode": MyNode}
NODE_DISPLAY_NAME_MAPPINGS = {"MyNode": "My Node"}

# V3
class MyExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [MyNode]

async def comfy_entrypoint() -> MyExtension:
    return MyExtension()
```

## Common Pitfalls

### Input Type Specification

V1 uses tuple shorthand that V3 replaces with typed helpers:

```python
# V1 shorthand
("IMAGE",)  # just the type
("FLOAT", {"default": 1.0})  # type with options dict

# V3 explicit
io.Image.Input("image")
io.Float.Input("strength", default=1.0)
```

### Return Values

V1 returns a plain tuple. V3 returns through `io.NodeOutput`:

```python
# V1
return (result,)

# V3
return io.NodeOutput(result)
```

### Optional Inputs with No Default

In V1, optional inputs without a default are `None` if not provided.
In the repo's documented V3 shape, mark the schema input as optional and handle
`None` in `execute()`:

```python
io.Image.Input("optional_image", optional=True)
```

Then in `execute`:

```python
def execute(cls, optional_image=None):
    if optional_image is None:
        # handle missing optional
```

### Custom and Flexible Types

For custom datatypes, prefer explicit custom type helpers over hand-written
tuple strings in migration examples:

```python
CustomPipe = io.Custom("DETAILER_PIPE")
CustomPipe.Input("detailer_pipe", optional=True, force_input=True)
```

## V3 Advantages

Migration yields:

- explicit schema validation at registration time
- cleaner separation between input definition and execution logic
- better tooling support (type checkers, schema introspection)
- alignment with ComfyUI's own extension architecture

## Backward Compatibility

V1 and V3 nodes coexist in the same ComfyUI instance. Registration mechanisms
differ, but both produce equivalent graph nodes. Node packs with both V1 and
V3 nodes will work without conflict.

## Real-World Case Studies

Two worked case studies based on current ComfyUI-Impact-Pack source
demonstrate V1-to-V3 migration in practice:

- [Case Study: Pipe Nodes](v1-to-v3-case-study-pipe.md) -- widget-heavy
  pipe bundle nodes from Impact-Pack
- [Case Study: Segs Nodes](v1-to-v3-case-study-segs.md) -- batch-oriented
  segmentation nodes from Impact-Pack

Both are community case studies (Tier 2 evidence). They document the
current V1 structure of those files and describe the V3 equivalents
using standard migration conventions. They are not statements that
Impact-Pack has migrated those files.

## Read Next

- [Node Structure](node-structure.md)
- [Development Guide](development-guide.md)
- [Registration](registration.md)
- [Case Study: Pipe Nodes](v1-to-v3-case-study-pipe.md)
- [Case Study: Segs Nodes](v1-to-v3-case-study-segs.md)
