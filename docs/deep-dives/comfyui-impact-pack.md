# ComfyUI-Impact-Pack (Community)

**Evidence:** Community pattern study based on pinned external version
**Community Package:** ComfyUI-Impact-Pack
**Package URL:** https://github.com/ltdrdata/ComfyUI-Impact-Pack
**Pinned Commit:** `429d0159ad429e64d2b3916e6e7be9c22d025c3c`
**Last Updated:** 2026-04-22

## Evidence Level Note

This page is a community pattern study (Tier 2). It documents patterns
observed in the Impact-Pack source code. It does not represent official
ComfyUI behavior. All Impact-Pack-specific claims carry the community
label; claims about ComfyUI itself are backed by Tier 1 sources where
applicable.

## What Impact-Pack Is

Impact-Pack is a large community extension for ComfyUI. It adds specialized
nodes for detail-aware image processing, segmentation-based editing, and
composite workflow patterns. It is not part of ComfyUI itself.

Key capabilities:
- **Detailer nodes** -- apply img2img-style refinement to specific regions
- **SEGS nodes** -- segmentation-based processing with per-segment control
- **Pipe datatypes** -- bundle multiple tensors into a single connector type
- **Hook system** -- injectable modifier behavior during sampling
- **Wildcard processing** -- dynamic prompt expansion

## Package Structure

```
ComfyUI-Impact-Pack/
  __init__.py              -- root entry point, NODE_CLASS_MAPPINGS aggregation
  install.py               -- dependency installation script
  node_list.json           -- optional package metadata file present at the pinned commit
  requirements.txt         -- Python dependencies
  modules/
    impact/
      __init__.py         -- impact sub-module entry point
      pipe.py             -- pipe datatype nodes (DETAILER_PIPE, BASIC_PIPE, etc.)
      hook_nodes.py        -- V1 nodes exposing hook providers to the graph
      hooks.py             -- hook provider classes
      impact_pack.py       -- main node definitions (129KB, very large)
      core.py              -- shared utility functions
      segs_nodes.py        -- segmentation node definitions
      detectors.py         -- detection utility nodes
      utils.py            -- general utilities
      wildcards.py         -- wildcard processing logic
      ...
  js/
    impact-pack.js         -- main frontend extension
    impact-image-util.js   -- image utility functions
    impact-segs-picker.js -- SEGS selection UI component
    ...
```

## Key Architectural Patterns

### 1. Pipe Datatype System

Impact-Pack invents its own composite datatype called `DETAILER_PIPE`
(and variants like `BASIC_PIPE`, `DETAILER_PIPE_SDXL`). A pipe bundles
multiple values (model, clip, vae, conditioning, etc.) into a single
connection:

```python
# From modules/impact/pipe.py (V1 pattern)
class ToDetailerPipe:
    RETURN_TYPES = ("DETAILER_PIPE",)
    FUNCTION = "doit"

    def doit(self, *args, **kwargs):
        pipe = (kwargs['model'], kwargs['clip'], kwargs['vae'],
                kwargs['positive'], kwargs['negative'], ...)
        return (pipe,)
```

The pipe is a plain Python tuple. There is no special ComfyUI-level type
enforcement -- downstream nodes unpack the tuple by position. This is a
community convention, not an official ComfyUI feature.

### 2. Hook Provider System

The hook system (in `modules/impact/hooks.py`) is one of Impact-Pack's
most distinctive architectural patterns. Hooks are injectable modifier
behaviors that wrap sampling steps:

```
Hook base class: PixelKSampleHook
  ├── DetailerHook        -- detail-aware sampling modifier
  ├── DetailerHookCombine -- combine multiple hooks
  ├── CoreMLHook          -- CoreML-based upscaling hook
  ├── VariationNoiseHook  -- inject variation noise into sampling
  └── PreviewDetailerHook -- preview image during sampling
```

The hook pattern uses method delegation. The base class defines a full
sampling lifecycle; subclasses override specific methods to modify
behavior:

```python
class PixelKSampleHook:
    def __init__(self):
        self.cur_step = 0
        self.total_step = 0

    def set_steps(self, info):
        self.cur_step, self.total_step = info

    def post_decode(self, pixels):
        return pixels

    def post_upscale(self, pixels, mask=None):
        return pixels
```

**Hook provider pattern:** `hook_nodes.py` exposes hooks to the graph
through V1 nodes. A provider node (e.g., `PreviewDetailerHookProvider`)
creates and returns a hook instance at graph-build time. The detailer
node then holds a reference to that hook and calls its methods during
sampling. This decouples hook configuration (in the node graph) from
hook execution (inside the sampler).

**DetailerHookCombine:** This hook chains multiple hooks together.
It holds a list of hook instances and delegates each lifecycle call
to every hook in sequence:

```python
class DetailerHookCombine(PixelKSampleHook):
    def __init__(self, hooks=None):
        super().__init__()
        self.hooks = hooks if hooks else []

    def post_decode(self, pixels):
        for hook in self.hooks:
            pixels = hook.post_decode(pixels)
        return pixels
```

The combine pattern lets workflow authors stack behaviors (e.g., preview
+ variation noise + CoreML upscale) without writing custom code. Each
individual hook modifies the pixel stream, and the combine pass applies
them in order.

### 3. SEGS (Segmentation) Data Structure

Impact-Pack defines a community convention for segmentation data called `SEGS`.
The structure is a tuple:

```
SEGS = (image_size_tuple, [seg_objects])
  where each seg_object has:
    cropped_image, crop_mask, confidence,
    crop_region, bbox, label, control_net_wrapper, ...
```

`segs_nodes.py` contains nodes that produce, filter, and transform SEGS data.
The SEGS structure enables per-segment operations -- each segment can be
processed independently and recombined.

### 4. Frontend Extension Layer

`js/impact-pack.js` registers ComfyUI frontend extensions that:

- Add custom UI panels for SEGS picking (`impact-segs-picker.js`)
- Add image utility overlays
- Handle SAM editor integration (`impact-sam-editor.js`)

The frontend extensions use the standard ComfyUI extension registration:

```javascript
app.registerExtension({
  name: "ImpactPack.detailer",
  setup() {
    // Register event listeners, add widgets, etc.
  },
});
```

### 5. Node Registration

Impact-Pack uses standard V1 registration throughout. The root
`__init__.py` aggregates `NODE_CLASS_MAPPINGS` from each module.
This matches the package layout used by both the legacy
custom-node-list flow and the newer registry-backed flow.

That layout alone does not make a package installable through Manager.
Registry-backed availability still requires registry publication, and the
legacy Manager flow still requires the package to be listed in the relevant
distribution channel.

### 6. Lifecycle Scripts

`install.py` handles dependency installation and model downloads.
Impact-Pack requires specific model files (SAM, bbox detectors) that
are downloaded during installation.

## Design Lessons for Extension Authors

### Pipe datatypes reduce connection clutter

Instead of connecting 8 separate wires (model, clip, vae, positive,
negative, bbox, sam, segs) between nodes, a pipe bundles them into one.
This is a practical ergonomic pattern for complex node graphs.

**Trade-off:** Pipe datatypes are not enforced by ComfyUI. A node that
expects a DETAILER_PIPE will silently unpack the wrong tuple shape if
the wrong node type is connected. This is a known limitation of the
community convention.

### Hook delegation enables composable behavior

The hook base class defines a complete sampling lifecycle. Subclasses
override specific methods to modify behavior. `DetailerHookCombine` chains
multiple hooks together. This pattern is clean and extensible.

**Trade-off:** Hooks are a community convention. They only work with
nodes that explicitly call the hook methods. Impact-Pack nodes call hooks;
other detailer nodes may not.

### SEGS structure enables per-segment processing

Segmentation data as a structured tuple enables nodes to iterate over
individual segments and apply different processing to each. This is
powerful for workflows that need per-region control.

**Trade-off:** The SEGS structure is Impact-Pack-specific. Nodes outside
Impact-Pack cannot consume or produce SEGS without explicit support.

## Maintenance and Compatibility Notes

- The package uses V1 node patterns throughout. There was no V3 migration
  present at commit `429d0159ad429e64d2b3916e6e7be9c22d025c3c`.
- Impact-Pack requires external model files (SAM, bbox detectors). The
  `install.py` script downloads these as part of setup.
- The package has its own frontend extension system that may conflict
  with other extensions that modify the same UI areas.
- SEGS and pipe datatypes are community conventions. Using them in a
  custom node requires matching Impact-Pack's tuple structure exactly.
- This page pins one repository revision. It does not make broader claims about
  project popularity, adoption, or release cadence beyond that revision.

## References

- Impact-Pack repo: https://github.com/ltdrdata/ComfyUI-Impact-Pack
- Impact-Pack is NOT part of ComfyUI. It is a community extension.

## Read Next

- [V1 to V3 Migration Guide](../custom-nodes/v1-to-v3-migration.md)
- [Case Study: Pipe Nodes](../custom-nodes/v1-to-v3-case-study-pipe.md)
- [Case Study: Segs Nodes](../custom-nodes/v1-to-v3-case-study-segs.md)
