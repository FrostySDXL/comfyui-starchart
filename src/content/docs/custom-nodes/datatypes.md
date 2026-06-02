---
title: "Datatypes"
---

**Evidence:** Official docs-backed from docs.comfy.org
**Last Updated:** 2026-06-01
**Primary Source:** https://docs.comfy.org/custom-nodes/backend/datatypes
**Baseline verification status:** Re-reviewed for core v0.23.0 / frontend v1.46.6 transition.

## Primary Sources

- https://docs.comfy.org/custom-nodes/backend/datatypes
- https://docs.comfy.org/custom-nodes/backend/more_on_inputs
- https://docs.comfy.org/custom-nodes/backend/server_overview

## Scope

ComfyUI datatypes serve two roles at once:

- they constrain which nodes can connect in the client
- they determine the Python object shape your node receives at runtime

For most node authors, the key rule is simple: choose the narrowest
correct datatype and understand the real Python value behind it.

## Standard Types

### Primitive widget types

Common primitive types include:

- `INT` -> Python `int`
- `FLOAT` -> Python `float`
- `STRING` -> Python `str`
- `BOOLEAN` -> Python `bool`
- `COMBO` -> declared as a list of strings, returns one selected `str`

The official docs also list standard widget options such as:

- `default`
- `min`, `max`, `step`
- `multiline`
- `placeholder`
- `forceInput`
- `defaultInput`
- `lazy`
- `rawLink`

### Tensor and structured data types

Important runtime datatypes include:

- `IMAGE` -> `torch.Tensor` shaped `[B, H, W, C]`
- `MASK` -> `torch.Tensor` shaped `[H, W]` or batched variants
- `LATENT` -> `dict` containing at least `samples`, usually shaped
  `[B, C, H, W]`, with optional fields `noise_mask` and `batch_index`
- `AUDIO` -> `dict` containing `waveform` and `sample_rate`
  (the upstream `_io.py` TypedDict uses `sampler_rate`; the
  `basic_types.py` TypedDict and the artifact use `sample_rate`.
  Prefer `sample_rate` -- it matches the published TypedDict in
  `basic_types.py` and the extracted artifact.)

From the current datatype guidance:

- `IMAGE` is batch-first and channel-last, not PyTorch's more common
  `[B, C, H, W]`
- `LATENT` commonly uses 1/8 image resolution in height and width
- model-ish types like `MODEL`, `CLIP`, and `VAE` are usually opaque
  objects passed through rather than tensor values you reshape directly

### Comfy-specific execution types

The backend docs also call out more advanced pipeline types such as:

- `NOISE`
- `SAMPLER`
- `SIGMAS`
- `GUIDER`
- `CONDITIONING`

These are important for advanced sampling nodes, but many node authors
can avoid them initially and focus on `IMAGE`, `MASK`, `LATENT`, and
primitive types.

Additional execution types defined in the v0.23.0 IO type registry
include `HOOKS`, `HOOK_KEYFRAMES`, `TIMESTEPS_RANGE`,
`LATENT_OPERATION`, `FLOW_CONTROL`, `ACCUMULATION`, `TRACKS`,
`LOAD_3D`, and `LOAD_3D_ANIMATION`. See the pinned
`node_api_schema.json` artifact for the full 76-type inventory.

### 3D data types (v0.23.0)

The current baseline adds six 3D IO types:

- `SPLAT` -> `SPLAT` custom type for Gaussian splat data
- `FILE_3D_PLY` -> `File3DPLY` for PLY mesh files
- `FILE_3D_SPLAT` -> `File3DSPLAT` for splat file loading
- `FILE_3D_SPZ` -> `File3DSPZ` for compressed splat files
- `FILE_3D_KSPLAT` -> `File3DKSPLAT` for K-splat files
- `LOAD3D_MODEL_INFO` -> `Load3DModelInfo` for 3D model metadata

These join the existing 3D file types (`FILE_3D`, `FILE_3D_GLB`,
`FILE_3D_GLTF`, `FILE_3D_FBX`, `FILE_3D_OBJ`, `FILE_3D_STL`,
`FILE_3D_USDZ`). Use the narrowest applicable file type for your
node rather than the generic `FILE_3D` wildcard.

## Custom Patterns

### Custom datatypes

If you want your own nodes to exchange extension-specific objects, you
can define a custom uppercase datatype name such as `CHEESE` in V1-style
definitions, or use typed helpers in newer V3-style code.

The official backend docs highlight one important caveat: because the
frontend does not automatically know how to render a custom datatype as a
widget, custom datatypes usually need `forceInput: True` so they behave
as sockets rather than widgets.

### Wildcard inputs

The frontend supports `*` as a wildcard input type, but the backend does
not fully validate it in the same way as standard types. The official
docs recommend pairing wildcard inputs with a `VALIDATE_INPUTS`
implementation that accepts `input_types` and performs custom checking.

### Dynamic and hidden inputs

`more_on_inputs` also documents important non-standard input patterns:

- hidden inputs like `UNIQUE_ID`, `PROMPT`, `EXTRA_PNGINFO`, and
  `DYNPROMPT`
- dynamically created optional inputs captured through custom optional
  dictionaries and `**kwargs`

These patterns are powerful, but should be treated as advanced features,
not default design choices.

## Key Takeaways

- document tensor layout explicitly when exposing image-like data
- preserve extra keys when modifying structured objects like `LATENT`
- avoid wildcard inputs unless a strict type cannot express the node's
  contract
- prefer custom datatypes for extension-internal object passing rather
  than overloading unrelated built-in types

## Read Next

- [Node Structure](node-structure.md)
- [Development Guide](development-guide.md)
