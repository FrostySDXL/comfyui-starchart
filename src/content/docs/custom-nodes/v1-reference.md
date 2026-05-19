---
title: "V1 Custom Node Reference"
---

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-05-19
**Primary Sources:** https://docs.comfy.org/custom-nodes/walkthrough, https://docs.comfy.org/custom-nodes/backend/server_overview, https://docs.comfy.org/custom-nodes/backend/more_on_inputs, `references/snapshots/2026-05-18/comfyui-core-v0.21.1/server.py`, `references/snapshots/2026-05-18/comfyui-core-v0.21.1/execution.py`, `references/snapshots/2026-05-18/comfyui-core-v0.21.1/comfy_api/latest/_io.py`
**Baseline verification status:** Verified against the current pinned baseline: core `v0.21.1`, frontend `v1.45.9`, snapshots `2026-05-18`.

## Scope

This page is the repo's single landing page for the legacy V1 custom-node
contract. It covers what a V1 node is, where to place it, which class members
matter, how registration works, how tuple returns behave, and which minimal
patterns are safe to copy. This repo still recommends V3 for new packages, but
V1 remains important when you are following the official walkthrough, reading
older node packs, or maintaining compatibility with existing V1 code.

## What a V1 node is

A V1 custom node is a plain Python class whose public contract is described with
class-level members and a callable `INPUT_TYPES()` definition. ComfyUI then
reads that contract during startup and execution by calling `obj_class.INPUT_TYPES()`
and `class_def.INPUT_TYPES()` in the pinned core snapshot.

Use this page when you need the legacy contract in one place. If you are
starting a new package and do not need V1 compatibility, go to the
[Custom Node Development Guide](development-guide.md) and
[Node Structure](node-structure.md) for the direct V3 path.

## Placement and discovery

For consumer authoring, the practical V1 install path is simple:

1. Place your Python file or package under `ComfyUI/custom_nodes/`.
2. Restart ComfyUI so startup discovery imports it again.
3. Export `NODE_CLASS_MAPPINGS` at module level so ComfyUI can register the
   node classes it found.

Keep the file or package small until the node appears in the Add Node menu.
That confirms placement, import, and registration before you debug node logic.

## Core V1 class anatomy

Most runnable V1 nodes need these pieces:

- `CATEGORY` -- Add Node menu placement
- `FUNCTION` -- instance method name ComfyUI calls at execution time
- `RETURN_TYPES` -- output datatypes in order
- `RETURN_NAMES` -- optional human-readable output labels
- `INPUT_TYPES()` -- required, optional, and hidden input definitions
- `NODE_CLASS_MAPPINGS` -- module-level registration export
- `NODE_DISPLAY_NAME_MAPPINGS` -- optional display-name override

Copy-safe anatomy:

```python
class MyV1Node:
    CATEGORY = "examples"
    FUNCTION = "run"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "hello", "multiline": False}),
            }
        }

    def run(self, text):
        return (text,)


NODE_CLASS_MAPPINGS = {
    "MyV1Node": MyV1Node,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MyV1Node": "My V1 Node",
}
```

### `INPUT_TYPES`: preferred form vs shorthand

For runnable V1 examples in this repo, prefer:

```python
@classmethod
def INPUT_TYPES(cls):
    return {...}
```

That is the copy-safe form because the pinned core calls `INPUT_TYPES()` as a
method. Some prose snippets elsewhere may show `INPUT_TYPES = {...}` to discuss
the dict shape quickly, but this repo's runnable examples and reference pages
should treat the callable form as the preferred pattern.

### `INPUT_TYPES()` structure

The returned dict usually contains one or more of these keys:

- `required`
- `optional`
- `hidden`

Each input entry maps the socket or widget name to a tuple definition:

- bare type: `("IMAGE",)`
- type plus widget options: `("FLOAT", {"default": 1.0, "min": 0.0})`
- dropdown widget: `(["brightest", "reddest"],)`

For `STRING`, the runtime value is Python `str`. Common widget options include
`default` and `multiline`.

## Registration exports

V1 registration happens through module-level dictionaries. The usual minimum is
`NODE_CLASS_MAPPINGS`:

```python
NODE_CLASS_MAPPINGS = {
    "MyV1Node": MyV1Node,
}
```

`NODE_DISPLAY_NAME_MAPPINGS` is optional, but useful when the Python class name
is not the label you want in the UI:

```python
NODE_DISPLAY_NAME_MAPPINGS = {
    "MyV1Node": "My V1 Node",
}
```

If ComfyUI can import the module from `custom_nodes/` but your node still does
not appear, verify these dictionaries first.

## Return tuple rules

V1 execution methods return plain tuples.

- One output still returns a tuple: `return (result,)`
- Two outputs return in declared order: `return (first, second)`
- `RETURN_NAMES`, when present, should match the output order used by
  `RETURN_TYPES`

Do not return a bare string or tensor for a single output. Keep the trailing
comma so Python builds a one-item tuple.

## Minimal no-import example

This example proves the smallest useful V1 shape without runtime-specific
imports:

```python
class HelloNode:
    CATEGORY = "examples"
    FUNCTION = "run"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    def run(self):
        return ("hello",)


NODE_CLASS_MAPPINGS = {"HelloNode": HelloNode}
NODE_DISPLAY_NAME_MAPPINGS = {"HelloNode": "Hello Node"}
```

Use this shape when you are debugging discovery, registration, or tuple return
behavior before adding real logic.

## Minimal `STRING` input/output example

This example keeps the contract explicit while showing one `STRING` input and
two `STRING` outputs:

```python
class StringEchoReference:
    CATEGORY = "examples/v1"
    FUNCTION = "run"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("original", "uppercased")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "hello", "multiline": False}),
            }
        }

    def run(self, text):
        return (text, text.upper())


NODE_CLASS_MAPPINGS = {"StringEchoReference": StringEchoReference}
NODE_DISPLAY_NAME_MAPPINGS = {"StringEchoReference": "String Echo Reference"}
```

For a repo-local file you can copy directly, see
`examples/custom-nodes/example-6-v1-string-reference/` in this repository.

## Trust framing for new work

This page exists because the official walkthrough and much existing community
code still teach the V1 shape. That does not change this repo's recommendation:
prefer V3 for new packages unless you have a compatibility or maintenance reason
to stay with V1.

## Read Next

- [Start Here: Custom Node Author](../start-here/author.md)
- [Node Structure](node-structure.md)
- [Registration](registration.md)
- [Building Your First Node](../tutorials/building-first-node.md)
- [V1 to V3 Migration Guide](v1-to-v3-migration.md)
