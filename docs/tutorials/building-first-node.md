# Building Your First Node

**Evidence:** Official docs-backed from docs.comfy.org
**Last Updated:** 2026-05-05
**Primary Source:** https://docs.comfy.org/custom-nodes/walkthrough

## Primary Sources

- https://docs.comfy.org/custom-nodes/walkthrough
- https://docs.comfy.org/custom-nodes/backend/server_overview
- https://docs.comfy.org/custom-nodes/overview

## Scope

The official walkthrough starts with a simple V1-style image-selection
node and gradually adds options and client messaging. It is still a good
beginner tutorial because it explains the execution model clearly, even
though new projects should usually prefer V3 structure for long-term
work.

Expected outcome:

- create a minimal custom node package
- define one node that takes `IMAGE` input and returns `IMAGE`
- register it so ComfyUI can discover it
- verify that it appears in the UI and runs in a workflow

## Step-by-Step Build

### 1. Scaffold a node package

The official guide recommends starting from a working ComfyUI install and
using `comfy-cli`:

```bash
cd ComfyUI/custom_nodes
comfy node scaffold
```

That creates the package skeleton and can optionally include a web
directory for frontend JavaScript.

If you are testing a single-file V1 example instead of a full scaffolded
package, place that file under `ComfyUI/custom_nodes/` and restart ComfyUI
before you check the Add Node menu. That confirms discovery and placement first.

### 2. Define a minimal node

The walkthrough's first example uses a V1-style node class with:

- `CATEGORY`
- `INPUT_TYPES`
- `RETURN_TYPES`
- `FUNCTION`

The core idea is still valid for any version: define one clear input,
one clear output, and one execution method.

### 3. Implement the execution method

The official sample works on `IMAGE`, which means a batch-shaped tensor.
It calculates a score per image and returns one selected image as a
single-image batch.

Important beginner takeaways from the walkthrough:

- `IMAGE` means an image batch, not just one image
- selecting one image usually requires adding back a batch dimension with
  `unsqueeze(0)`
- a single V1 output still must be returned as a tuple with a trailing
  comma

### 4. Register the node

The walkthrough then registers the node in legacy V1 mappings:

```python
NODE_CLASS_MAPPINGS = {
    "Image Selector": ImageSelector,
}
```

That is correct for the tutorial's V1 structure. For new V3 projects,
the equivalent concept is to expose the node through `ComfyExtension`
and `comfy_entrypoint()`.

### 5. Add a simple option

The walkthrough extends the node with a `COMBO`-style dropdown input so
the node can choose the brightest, reddest, greenest, or bluest image.

That is a useful beginner pattern because it demonstrates:

- how widget inputs are declared
- how execution parameters match declared inputs
- how to evolve a node contract without changing its core shape

### 6. Add optional frontend behavior

The guide finishes by sending a message from Python to the frontend and
registering a small JS extension that listens for it.

This shows the boundary between:

- backend node execution
- frontend extension setup

It also demonstrates why some nodes become client/server hybrids rather
than pure backend nodes.

## Verification

After adding a first node, verify the basics in order:

- restart ComfyUI so the node package is reloaded
- confirm the node appears in the Add Node menu under the expected
  category
- connect it in a minimal workflow with known inputs
- run the workflow and confirm the output datatype and UI behavior are
  correct
- if the node includes frontend JS, reload the webpage and verify the
  browser-side behavior too

## Recommendation for modern projects

Use the official walkthrough to understand concepts, but build new node
packages with modern V3 structure when possible. The tutorial is best
read as a mental model for how a node works, not as the final word on
today's preferred packaging pattern.

## Read Next

- [Node Structure](../custom-nodes/node-structure.md)
- [Registration](../custom-nodes/registration.md)
