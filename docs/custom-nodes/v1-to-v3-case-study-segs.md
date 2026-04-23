# V1 to V3 Migration: Case Study -- Batch-Oriented Segs Nodes

**Evidence:** Community pattern study based on pinned external version
**Community Package:** ComfyUI-Impact-Pack
**Package URL:** https://github.com/ltdrdata/ComfyUI-Impact-Pack
**License Note:** Upstream package license confirmed as GPL-3.0 via `gh repo view ltdrdata/ComfyUI-Impact-Pack --json licenseInfo`
**Pinned Commit:** `429d0159ad429e64d2b3916e6e7be9c22d025c3c`
**File Studied:** `modules/impact/segs_nodes.py`
**File Blob SHA:** `3edf9abec7acb007e9642962b6e5992b350bb4f5`
**Last Updated:** 2026-04-22

## What This Case Study Is

This page documents one batch-oriented V1 pattern from ComfyUI-Impact-Pack's
segmentation nodes module (`segs_nodes.py`) as a real-world migration
reference. It is a community case study, not an official ComfyUI migration
guide. The file contains several `SEGS` utilities; this page focuses on the
batch-aware `MaskToSEGS_for_AnimateDiff` node because it is a concrete
batch-oriented candidate in the pinned file.

## Important Scope Note

The nodes in `segs_nodes.py` are currently V1. This case study examines the
batch-handling structure of `MaskToSEGS_for_AnimateDiff` and describes a V3
equivalent. This is a migration feasibility study, not a statement that
Impact-Pack has migrated this node.

## Source File Overview

`modules/impact/segs_nodes.py` was inspected at commit
`429d0159ad429e64d2b3916e6e7be9c22d025c3c`. The file contains multiple
V1 nodes that operate on `SEGS` (segmentation) data. Relevant batch-aware
examples include:

- `MakeTileSEGS` -- creates segmentation tiles from an image
- `MaskToSEGS_for_AnimateDiff` -- switches to `core.batch_mask_to_segs(...)`
  when the input mask is a multi-frame batch
- `DefaultImageForSEGS` -- rebuilds cropped segment images across a batch by
  iterating over frames and concatenating tensors

The file is approximately 77KB. In the pinned version, it is a better source
for batch-oriented patterns than for true multi-output migration examples.

## V1 Node Anatomy -- `MaskToSEGS_for_AnimateDiff`

```python
class MaskToSEGS_for_AnimateDiff:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "mask": ("MASK",),
                "combined": ("BOOLEAN", {"default": False, ...}),
                "crop_factor": ("FLOAT", {"default": 3.0, ...}),
                "bbox_fill": ("BOOLEAN", {"default": False, ...}),
                "drop_size": ("INT", {"default": 10, ...}),
                "contour_fill": ("BOOLEAN", {"default": False, ...}),
            }
        }

    RETURN_TYPES = ("SEGS",)
    FUNCTION = "doit"
    CATEGORY = "ImpactPack/Operation"

    @staticmethod
    def doit(mask, combined, crop_factor, bbox_fill, drop_size, contour_fill=False):
        if (len(mask.shape) == 4 and mask.shape[1] > 1) or (len(mask.shape) == 3 and mask.shape[0] > 1):
            mask = utils.make_3d_mask(mask)
            if contour_fill:
                logging.info("... batch mask 'contour_fill' is not supported.")
            result = core.batch_mask_to_segs(mask, combined, crop_factor, bbox_fill, drop_size)
            return (result, )

        mask = utils.make_2d_mask(mask)
        segs = core.mask_to_segs(mask, combined, crop_factor, bbox_fill, drop_size, is_contour=contour_fill)
        ...
        return MaskToSEGS.doit(result_mask, False, crop_factor, False, drop_size, contour_fill)
```

## V3 Equivalent Anatomy

The following V3 code is a **proposed migration sketch**, not observed
Impact-Pack code at the pinned commit. It demonstrates how the V1 patterns
would map to V3 using standard migration conventions. The V3 equivalent
anatomy sections in this case study show community-written migration
proposals, not official Impact-Pack V3 implementations.

### `define_schema()`

```python
from comfy_api.latest import io


SEGS = io.Custom("SEGS")

class MaskToSEGSForAnimateDiff(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MaskToSEGSForAnimateDiff",
            display_name="Mask To SEGS for AnimateDiff",
            category="ImpactPack/Operation",
            inputs=[
                io.Mask.Input("mask", force_input=True),
                io.Boolean.Input("combined", default=False),
                io.Float.Input("crop_factor", default=3.0, min=1.0, max=100.0, step=0.1),
                io.Boolean.Input("bbox_fill", default=False),
                io.Int.Input("drop_size", default=10, min=1, max=4096, step=1),
                io.Boolean.Input("contour_fill", default=False),
            ],
            outputs=[SEGS.Output("segs")],
        )
```

### execute method

The following is a **proposed V3 migration** for the V1 `doit` method. It uses
the repo's documented `execute(cls, ...)` contract and stays honest about the
batch/non-batch branch that still needs careful porting. This is not observed
upstream code.

```python
    @classmethod
    def execute(
        cls,
        mask,
        combined=False,
        crop_factor=3.0,
        bbox_fill=False,
        drop_size=10,
        contour_fill=False,
    ):
        # Preserve the V1 split: batched masks take the dedicated batch path,
        # while single masks stay on the legacy 2D-to-SEGS conversion path.
        if len(mask.shape) >= 3 and mask.shape[0] > 1:
            batched_mask = utils.make_3d_mask(mask)
            if contour_fill:
                # The V1 node logs and ignores this combination for batch input.
                contour_fill = False
            return io.NodeOutput(
                core.batch_mask_to_segs(
                    batched_mask,
                    combined,
                    crop_factor,
                    bbox_fill,
                    drop_size,
                )
            )

        single_mask = utils.make_2d_mask(mask)
        return io.NodeOutput(
            core.mask_to_segs(
                single_mask,
                combined,
                crop_factor,
                bbox_fill,
                drop_size,
                is_contour=contour_fill,
            )
        )
```

Key migration points demonstrated:
- `execute(cls, ...)` parameters replace V1 class-attribute wiring
- batch detection is explicit instead of hidden inside a long V1 helper body
- `SEGS` remains a community-defined tuple that still needs careful contract
  review in any real migration
- the worked example is a migration scaffold, not a claim that Impact-Pack has
  already shipped this V3 port

## Key Observations

### The file's clearest migration target is batch-aware mask handling

`MaskToSEGS_for_AnimateDiff` is a better case-study target than the previous
`SEGSFilters` framing because the pinned file shows an explicit batch branch:
multi-frame masks are detected from tensor shape and routed to
`core.batch_mask_to_segs(...)`.

### SEGS is a composite community type

`SEGS` is a structured tuple type used by Impact-Pack to represent
segmentation data. It is not a built-in ComfyUI type. In the repo's documented
V3 API surface, the closest equivalent is `io.Custom("SEGS")`. The V1 code shows:

```python
# SEGS structure: (image_size, [segs_list])
# where each seg in segs_list is a namedtuple or object with:
#   cropped_image, crop_mask, confidence, crop_region, bbox, label, ...
```

### Batch mode changes behavior, not just tensor shape

The batch branch does more than accept a larger tensor. It also disables one
feature combination: when the input is a batch mask, the node logs that
`contour_fill` is ignored and routes to the batch helper instead.

### Other nodes in the file extend the same batch idea

`DefaultImageForSEGS` computes `batch_count`, iterates over each frame, crops a
per-frame image, and concatenates the results with `torch.cat(...)`. That is a
second signal that this module contains real batch-oriented migration work even
when the public output type remains a single `SEGS` value.

### Optional inputs with `None` defaults still matter elsewhere in the file

Several neighboring nodes in `segs_nodes.py` still rely on optional inputs that
default to `None`. When porting more of the file, keep that pattern explicit in
V3 signatures:

```python
def execute(cls, segs_preprocessor=None):
    if segs_preprocessor is None:
        # use default behavior
        ...
```

## Migration Difficulty Assessment

| Aspect | Difficulty | Notes |
|--------|-----------|-------|
| INPUT_TYPES | Low | Direct mapping to typed `io.*.Input(...)` helpers |
| RETURN_TYPES | Low | Single SEGS output |
| execute method | Medium | The main risk is preserving the 2D vs batch branch correctly |
| Batch behavior | High | Tensor-shape detection and `contour_fill` fallback need runtime verification |
| Integration testing | High | SEGS remains a community composite type, not an official schema |

## Comparison: Pipe Nodes vs Segs Nodes

| Property | pipe.py | segs_nodes.py |
|----------|---------|--------------|
| V1 class attributes | Yes | Yes |
| io.Schema | No | No |
| Custom composite type | DETAILER_PIPE | SEGS |
| Multi-output | No | No |
| Batch processing | No | Yes |
| Explicit batch branch in studied node | No | Yes |
| Complex internal logic | Low | Medium-High |
| Estimated migration difficulty | Low-Medium | Medium-High |

## Read Next

- [V1 to V3 Migration Guide](v1-to-v3-migration.md)
- [Node Structure](../custom-nodes/node-structure.md)
- [Case Study: Pipe Nodes](v1-to-v3-case-study-pipe.md)
