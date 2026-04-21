# V1 to V3 Migration Guide

**Last Updated:** 2026-04-20
**Primary Sources:** https://docs.comfy.org/custom-nodes/overview, https://docs.comfy.org/custom-nodes/backend/migration

## Overview

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

A V1 node is a Python class with class-level attributes:

```python
class MyNode:
    CATEGORY = "MyNodes"
    INPUT_TYPES = {
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

## V3 Node Anatomy

A V3 node inherits from `io.ComfyNode` and uses an explicit schema:

```python
import comfy

class MyNode(comfy.node_base.ComfyNode):
    @staticmethod
    def define_schema():
        return comfy.io.Schema(
            inputs=[
                comfy.io.RequiredInput(("IMAGE",), "image"),
                comfy.io.OptionalInput(("FLOAT",), "strength",
                    default=1.0, min_value=0.0, max_value=10.0),
            ],
            outputs=[
                comfy.io.RequiredInput(("IMAGE",), "output_image"),
            ],
            name="MyNode",
            display_name="My Node",
            category="MyNodes",
        )

    def execute(self):
        image = self.get_input("image")
        strength = self.get_input("strength")
        result = self.process(image, strength)
        return comfy.io.NodeOutput(self, "output_image", result)
```

Registration uses a ComfyExtension entrypoint:

```python
class MyNodeExtension(comfy.extension.ComfyExtension):
    @staticmethod
    def get_nodes():
        return {"MyNode": MyNode}

comfy_entrypoint = MyNodeExtension
```

## Step-by-Step Migration

### 1. Replace Class Attributes with define_schema

V1 class attributes become schema inputs:

| V1 | V3 |
|----|----|
| `INPUT_TYPES` required entry | `comfy.io.RequiredInput` |
| `INPUT_TYPES` optional entry | `comfy.io.OptionalInput` with default |
| `RETURN_TYPES` | `comfy.io.RequiredInput` in outputs list |
| `CATEGORY` | `category` field in Schema |
| `FUNCTION` | rename the method to `execute` |

### 2. Change Inheritance

```python
# V1
class MyNode:

# V3
class MyNode(comfy.node_base.ComfyNode):
```

### 3. Move Execution Logic

V1 method name (from FUNCTION) becomes `execute`. Inputs are fetched via
`self.get_input()`:

```python
# V1
def process(self, image, strength=1.0):
    result = image * strength
    return (result,)

# V3
def execute(self):
    image = self.get_input("image")
    strength = self.get_input("strength")
    result = image * strength
    return comfy.io.NodeOutput(self, "output_image", result)
```

Note that V3 returns an `io.NodeOutput` wrapping the result, not a tuple
directly.

### 4. Update Registration

```python
# V1
NODE_CLASS_MAPPINGS = {"MyNode": MyNode}
NODE_DISPLAY_NAME_MAPPINGS = {"MyNode": "My Node"}

# V3
class MyExtension(comfy.extension.ComfyExtension):
    @staticmethod
    def get_nodes():
        return {"MyNode": MyNode}

comfy_entrypoint = MyExtension
```

## Common Pitfalls

### Input Type Specification

V1 uses tuple shorthand that V3 expands explicitly:

```python
# V1 shorthand
("IMAGE",)  # just the type
("FLOAT", {"default": 1.0})  # type with options dict

# V3 explicit
comfy.io.RequiredInput(("IMAGE",), "image")
comfy.io.OptionalInput(("FLOAT",), "strength", default=1.0)
```

### Return Values

V1 returns a plain tuple. V3 returns through `io.NodeOutput`:

```python
# V1
return (result,)

# V3
return comfy.io.NodeOutput(self, "output_image", result)
```

### Optional Inputs with No Default

In V1, optional inputs without a default are `None` if not provided.
In V3, use `OptionalInput` and handle `None` in `execute`:

```python
comfy.io.OptionalInput(("IMAGE",), "optional_image")
```

Then in `execute`:

```python
optional_image = self.get_input("optional_image")
if optional_image is None:
    # handle missing optional
```

### Widget Types

V1 uses `*` for wildcard or flexible types. V3 uses explicit type lists:

```python
# V1 wildcard
("*",)

# V3 equivalent
("IMAGE", "MASK", "LATENT")
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

## References

- Official migration docs: https://docs.comfy.org/custom-nodes/backend/migration
- V3 node authoring: https://docs.comfy.org/custom-nodes/overview
- This repo's custom node docs: [Development Guide](../custom-nodes/development-guide.md)
