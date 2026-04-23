# V1 to V3 Migration: Case Study -- Pipe Nodes

**Evidence:** Community pattern study based on pinned external version
**Community Package:** ComfyUI-Impact-Pack
**Package URL:** https://github.com/ltdrdata/ComfyUI-Impact-Pack
**License Note:** Upstream package license confirmed as GPL-3.0 via `gh repo view ltdrdata/ComfyUI-Impact-Pack --json licenseInfo`
**Pinned Commit:** `429d0159ad429e64d2b3916e6e7be9c22d025c3c`
**File Studied:** `modules/impact/pipe.py`
**File Blob SHA:** `4e782f6a88690b3ef6e376746ee0eabb7c8ea08e`
**Last Updated:** 2026-04-22

## What This Case Study Is

This page documents the V1 node patterns found in ComfyUI-Impact-Pack's pipe
module as a real-world migration reference. It is a community case study,
not an official ComfyUI migration guide. The patterns shown here reflect
what Impact-Pack currently ships; they are not the authoritative V3
equivalent.

## Important Scope Note

Impact-Pack's pipe nodes (such as `ToDetailerPipe`, `FromDetailerPipe`)
are currently V1 nodes. This case study examines their V1 structure and
describes the V3 equivalents using the standard V1-to-V3 migration
conventions. This is not a statement that Impact-Pack has migrated or will
migrate these nodes -- it is a migration feasibility study based on the
current V1 code.

## Source File Overview

`modules/impact/pipe.py` contains several V1 pipe nodes that bundle
multiple tensor types into a single composite "pipe" type. These pipes
carry model, CLIP, VAE, conditioning, and detector references as a single
connected unit between nodes.

The file was inspected at commit `429d0159ad429e64d2b3916e6e7be9c22d025c3c`.
No V3 migration was present at that commit.

## V1 Node Anatomy -- ToDetailerPipe

```python
class ToDetailerPipe:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
                     "model": ("MODEL",),
                     "clip": ("CLIP",),
                     "vae": ("VAE",),
                     "positive": ("CONDITIONING",),
                     "negative": ("CONDITIONING",),
                     "bbox_detector": ("BBOX_DETECTOR",),
                     "wildcard": ("STRING", {"multiline": True, "dynamicPrompts": False}),
                     ...
                },
                "optional": {
                      "sam_model_opt": ("SAM_MODEL",),
                      "segm_detector_opt": ("SEGM_DETECTOR",),
                      "detailer_hook": ("DETAILER_HOOK"),
                }}

    RETURN_TYPES = ("DETAILER_PIPE",)
    RETURN_NAMES = ("detailer_pipe",)
    FUNCTION = "doit"
    CATEGORY = "ImpactPack/Pipe"

    def doit(self, *args, **kwargs):
        pipe = (kwargs['model'], kwargs['clip'], kwargs['vae'],
                kwargs['positive'], kwargs['negative'], kwargs['wildcard'],
                kwargs['bbox_detector'], ...)
        return (pipe,)
```

## V3 Equivalent Anatomy

The following V3 code is a **proposed migration sketch**, not observed
Impact-Pack code at the pinned commit. It demonstrates how the V1 patterns
would map to V3 using standard migration conventions. The V3 equivalent
anatomy sections in this case study show community-written migration
proposals, not official Impact-Pack V3 implementations.

### `INPUT_TYPES` becomes typed `define_schema()` inputs

```python
from comfy_api.latest import io


DetailerPipe = io.Custom("DETAILER_PIPE")
SamModel = io.Custom("SAM_MODEL")
SegmDetector = io.Custom("SEGM_DETECTOR")
DetailerHook = io.Custom("DETAILER_HOOK")

class ToDetailerPipe(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="ToDetailerPipe",
            display_name="To Detailer Pipe",
            category="ImpactPack/Pipe",
            inputs=[
                io.Model.Input("model", force_input=True),
                io.Clip.Input("clip", force_input=True),
                io.Vae.Input("vae", force_input=True),
                io.Conditioning.Input("positive", force_input=True),
                io.Conditioning.Input("negative", force_input=True),
                io.Custom("BBOX_DETECTOR").Input("bbox_detector", force_input=True),
                io.String.Input("wildcard", default="", multiline=True, dynamic_prompts=False),
                SamModel.Input("sam_model_opt", optional=True, force_input=True),
                SegmDetector.Input("segm_detector_opt", optional=True, force_input=True),
                DetailerHook.Input("detailer_hook", optional=True, force_input=True),
            ],
            outputs=[DetailerPipe.Output("detailer_pipe")],
        )
```

### execute replaces the FUNCTION method

The following is a **proposed V3 migration** for the V1 `doit` method. It uses
the repo's documented V3 `execute(cls, ...)` contract, not an observed
Impact-Pack implementation. Treat it as a copy-safe starting point for local
migration experiments, then compare it against the full pinned tuple contract in
`modules/impact/pipe.py` before relying on it.

```python
    @classmethod
    def execute(
        cls,
        model,
        clip,
        vae,
        positive,
        negative,
        bbox_detector,
        wildcard="",
        sam_model_opt=None,
        segm_detector_opt=None,
        detailer_hook=None,
    ):
        # This sketch keeps only the tuple slots shown in the excerpt above.
        # A real migration should preserve every slot consumed downstream.
        pipe = (
            model,
            clip,
            vae,
            positive,
            negative,
            wildcard,
            bbox_detector,
            sam_model_opt,
            segm_detector_opt,
            detailer_hook,
        )

        return io.NodeOutput(pipe)
```

Key migration points demonstrated:
- `execute(cls, ...)` parameters replace `kwargs['key']` access
- optional inputs arrive as `None` when disconnected and should stay explicit
- the pipe tuple remains a community contract outside ComfyUI's built-in type set
- the migration sketch is intentionally partial and must be checked against the
  full pinned V1 tuple layout before reuse

> **Caveat:** The `ComfyExtension` class and `comfy_entrypoint()` convention
> shown here are not directly pinned from a Python source file. See the caveat
> in [Registration](../custom-nodes/registration.md).

```python
from typing_extensions import override
from comfy_api.latest import ComfyExtension


class ToDetailerPipeExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [ToDetailerPipe]


async def comfy_entrypoint() -> ToDetailerPipeExtension:
    return ToDetailerPipeExtension()
```

## Key Observations

### Composite pipe types are a community pattern

`DETAILER_PIPE` is not a built-in ComfyUI type. In the repo's documented V3
surface, the closest migration pattern is `io.Custom("DETAILER_PIPE")` plus an
explicit `force_input=True` socket contract where needed. The tuple layout is
still Impact-Pack-specific.

### Widget configuration is standard V1

The `wildcard` input uses `"multiline": True` and `"dynamicPrompts": False`
widget options. These map directly to `io.String.Input(...)` keyword arguments.

### Optional inputs with None defaults

The `sam_model_opt`, `segm_detector_opt`, and `detailer_hook` optional
inputs have no explicit default in V1. In the repo's documented V3 shape, mark
them `optional=True` and handle `None` in `execute()`.

### Multiple return types

`DETAILER_PIPE` stays a community-defined composite datatype. The proposed V3
output uses `io.Custom("DETAILER_PIPE").Output("detailer_pipe")` so the schema
matches the repo's documented V3 API surface.

## Migration Difficulty Assessment

| Aspect | Difficulty | Notes |
|--------|-----------|-------|
| INPUT_TYPES | Low | Direct mapping to typed `io.*.Input(...)` helpers |
| RETURN_TYPES | Low | Single composite type, tuple structure unchanged |
| execute method | Medium | Signature changes from `doit(*args, **kwargs)` to `execute(cls, ...)` |
| Registration | Medium | Requires repo-documented `ComfyExtension` + `comfy_entrypoint()` pattern |
| Testing | Medium | Pipe composite types require integration test |

## Read Next

- [V1 to V3 Migration Guide](v1-to-v3-migration.md)
- [Node Structure](../custom-nodes/node-structure.md)
- [Case Study: Segs Nodes](v1-to-v3-case-study-segs.md)
