# Example: Official Custom Node Walkthrough

**Status:** Source-backed example
**Primary Source:** https://docs.comfy.org/custom-nodes/walkthrough

## What This Example Is

This directory captures the official custom-node walkthrough example from the
ComfyUI docs: an `Image Selector` node that chooses one image from a batch.

It is useful as a real starter example because it includes:

- a backend Python node
- registration mappings
- a frontend extension example
- an official workflow JSON that exercises the node

## Files

- `image_selector_node.py` - backend node example derived from the walkthrough
- `web/js/imageSelector.js` - frontend event-listener example from the walkthrough
- `workflow.json` - official example workflow JSON from the Comfy docs repo

## Evidence Level

- official behavior: the walkthrough page and linked workflow JSON
- upstream source behavior: not claimed here beyond what the walkthrough states
- community behavior: not used in this example

## Usage Notes

- treat this as a documented example, not a full production node pack
- verify against your installed ComfyUI version before shipping a real package
- if a local upstream ComfyUI checkout is available later, pin this example to a
  specific commit in `references/snapshots/`
- this example intentionally uses `@classmethod def INPUT_TYPES(cls)` because the
  pinned ComfyUI core calls `INPUT_TYPES()` as a method at runtime

## Runtime Validation

The opt-in `.github/workflows/runtime-smoke.yml` can exercise the minimal-node
example against a live ComfyUI instance if the workflow is configured to submit
the included `workflow.json`. This is not part of CPU-safe CI and must be
triggered manually with a known ComfyUI URL.
