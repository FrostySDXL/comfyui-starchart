---
title: "V3 Node Structure"
---

**Evidence:** Official docs-backed from docs.comfy.org
**Last Updated:** 2026-05-21
**Primary Source:** https://docs.comfy.org/custom-nodes/v3_migration
**Baseline verification status:** This page has not been re-reviewed against the current baseline.

## Primary Sources

- https://docs.comfy.org/custom-nodes/backend/server_overview
- https://docs.comfy.org/custom-nodes/backend/more_on_inputs
- https://docs.comfy.org/custom-nodes/backend/datatypes
- https://docs.comfy.org/custom-nodes/v3_migration

## Scope

This page is the repo's main V3 node structure reference.
In V3, a custom node is a Python class derived from `io.ComfyNode`.
Instead of scattering configuration across multiple legacy class
attributes, the node declares its public contract in one schema object
and implements behavior in one execution method.

Legacy V1 patterns still appear in older repos, but this reduced surface keeps
the retained node-structure reference focused on the modern V3 shape.

Minimal V3 shape:

```python
from comfy_api.latest import io

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
        return io.NodeOutput(text)
```

## Schema Fields

Important `io.Schema` fields include:

- `node_id` — globally unique identifier
- `display_name` — label shown in the UI
- `category` — Add Node menu path
- `description` — optional explanatory text
- `inputs` — list of input schema objects
- `outputs` — list of output schema objects
- `hidden` — hidden server-provided values
- `is_output_node` — marks side-effect or terminal nodes
- `is_experimental`, `is_deprecated`, `is_dev_only` — visibility flags
- `is_api_node` — marks API-only nodes
- `is_input_list` — receive list inputs as lists
- `not_idempotent` — disables normal caching assumptions
- `accept_all_inputs` — accept arbitrary inputs
- `search_aliases` — alternate search terms

The most important required field is `node_id`. Keep it unique and
stable, because it becomes part of the node's external identity.

## Inputs and Outputs

### V3 input definitions

Inputs are declared as typed schema objects such as:

- `io.Image.Input("image")`
- `io.Float.Input("strength", default=1.0, min=0.0, max=1.0)`
- `io.String.Input("text", multiline=True)`

Execution parameters must match input IDs exactly.

### V3 output definitions

Outputs are declared similarly, for example:

- `io.Image.Output("IMAGE")`
- `io.String.Output()`

The `execute()` method must return `io.NodeOutput(...)` with the same
number and ordering as the schema outputs.

### Common datatypes

From the current datatype guidance:

- `IMAGE` is a float tensor shaped `[B, H, W, C]`
- `MASK` is typically `[H, W]` or `[B, H, W]`
- `LATENT` is a dict containing at least `samples`
- model-like objects such as `MODEL`, `CLIP`, and `VAE` are usually
  opaque pass-through objects, not tensors you manipulate directly

## Hidden inputs

The legacy backend docs explain the conceptual hidden inputs clearly,
and the same ideas remain useful in modern node design:

- `UNIQUE_ID` — the node's runtime ID
- `PROMPT` — the full prompt payload
- `EXTRA_PNGINFO` — metadata propagated into saved PNGs
- `DYNPROMPT` — mutable prompt graph for advanced expansion cases

Use hidden inputs sparingly. They are powerful, but they couple the node
to workflow or runtime context rather than just dataflow.

## Flexible inputs

The backend docs describe several advanced patterns:

- custom datatypes for passing extension-specific Python objects
- wildcard inputs using `*`
- dynamically created inputs captured through optional dictionaries and
  `**kwargs`

These are useful, but they increase complexity. Prefer fixed, typed
inputs unless the node genuinely needs dynamic behavior.

## Read Next

- [Registration](registration.md)
- [Datatypes](datatypes.md)
