# Decision Tree: Custom Node Architecture

**Last Updated:** 2026-04-21
**Evidence:** Source-backed from pinned snapshots

## Overview

This page helps you decide what kind of custom node to build and how to
structure it. Work through the questions in order.

## Question 1: What Does Your Node Need to Do?

### Process data and output a result (image, model, text, etc.)

Go to Question 2.

### Only modify UI or editor behavior (no server execution)

You do not need a custom node. Use a **Frontend Extension** instead.

- [JavaScript Hooks](../hooks/javascript-hooks.md)
- [Extension Developer Path](../start-here/extension-developer.md)

---

## Question 2: Does Your Node Need Configuration Options?

### No -- the node is a pure pass-through or single-operation

A **simple V1 node** is sufficient:

```python
class PassthroughNode:
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "passthrough"

    def passthrough(self, image):
        return (image,)
```

Example: `examples/custom-nodes/minimal-node-template/`

### Yes -- sliders, dropdowns, toggles, or text inputs

Go to Question 3.

---

## Question 3: Does Your Node Have Multiple Distinct Operation Modes?

### Yes -- fundamentally different processing paths based on user choice

Use **dropdown-based mode selection** in INPUT_TYPES:

```python
"operation": (["scale", "crop", "pad"],),
```

Then branch in your execute method. Keep the modes coherent -- if they
require completely different inputs, consider splitting into separate nodes.

Example: `examples/custom-nodes/example-2-widgets/`

### No -- continuous or incremental configuration

Use **slider or number inputs**:

```python
"strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.1}),
```

---

## Question 4: Does Your Node Take a Batch and Produce Multiple Outputs?

### Yes -- batch processing, multi-output, or intermediate results

Design for **multi-output**:

```python
RETURN_TYPES = ("IMAGE", "MASK", "STRING")
RETURN_NAMES = ("processed", "mask", "log")
```

Emit progress events for long-running batch operations:

```python
PromptServer.instance.send_sync(
    "example.progress",
    {"index": i, "total": batch_size},
)
```

Example: `examples/custom-nodes/example-3-node-communication/`

### No -- single input, single output

Continue to Question 5.

---

## Question 5: Does Your Node Need Custom UI Beyond Standard Widgets?

### Yes -- custom canvas overlays, sidebar panels, or graph commands

Pair your Python node with a **Frontend Extension**. Keep the server node
logic clean and push UI behavior to the JS side.

- [Frontend Extension Patterns](../extensions/patterns.md)
- [JavaScript Hooks](../hooks/javascript-hooks.md)

Example: the Minimal Node Template (`examples/custom-nodes/minimal-node-template/`)
includes a frontend extension component alongside the server node.

### No -- standard ComfyUI widgets are sufficient

Go to Question 6.

---

## Question 6: V1 or V3?

### New node, new project, no existing V1 dependencies

Target **V3** for the cleaner schema and explicit execution contract:

```python
class MyNode(comfy.node_base.ComfyNode):
    @staticmethod
    def define_schema():
        return comfy.io.Schema(...)
```

See the [V1 to V3 Migration Guide](../custom-nodes/v1-to-v3-migration.md) for details.

### Existing node, maintaining compatibility, or depending on V1-only packages

Use **V1**. It is not deprecated and remains the dominant pattern in the
installed custom node base.

---

## Decision Summary

| Situation | Node Type |
|-----------|-----------|
| Pure pass-through, no config | Simple V1 node |
| Config widgets needed | V1 with INPUT_TYPES widgets |
| Multiple operation modes | Dropdown-based mode selection |
| Batch processing or multi-output | Multi-output V1 with event emission |
| Custom UI beyond widgets | Node + Frontend Extension |
| New project, no legacy | V3 node |
| Existing V1 node | V1 (migrate when updating) |

## Packaging for Distribution

If your node or node pack will be published:

1. Follow the [Manager Integration](../how-to/integrate-with-manager.md) checklist
2. Use `requirements.txt` for Python dependencies (keep versions loose)
3. Consider V3 if you want cleaner registration and schema introspection
4. Test on a clean ComfyUI instance before publishing

## Common Mistakes

- **Building a 200-node pack when you need 3 nodes** -- start small, expand as needed
- **Putting UI logic in the Python execute method** -- use frontend hooks instead
- **Using wildcard input types (`*`) when explicit types would work** -- explicit is more cacheable
- **Baking graph assumptions into node logic** -- nodes should be composable, not assume a specific graph shape

## Read Next

- [Node Structure](../custom-nodes/node-structure.md)
- [Registration](../custom-nodes/registration.md)
