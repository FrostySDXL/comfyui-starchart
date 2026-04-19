# Object Info

**Last Updated:** 2026-04-19
**Primary Source:** https://github.com/Comfy-Org/ComfyUI/blob/master/server.py

## Primary Sources

- https://github.com/Comfy-Org/ComfyUI/blob/master/server.py

## Overview

`GET /object_info` is ComfyUI's node discovery endpoint. It returns the
metadata the frontend and external tooling need to understand which
nodes exist, what inputs they accept, what outputs they produce, and how
they should be displayed.

There are two related routes:

- `GET /object_info` — all registered nodes
- `GET /object_info/{node_class}` — one specific node class

Internally, both routes build their payload from
`nodes.NODE_CLASS_MAPPINGS` and a helper named `node_info()`.

## Response Structure

For standard nodes, `node_info()` assembles a JSON object with fields
including:

- `input` — raw input type definitions from `INPUT_TYPES()`
- `input_order` — ordering of required/optional input groups
- `is_input_list` — whether the node consumes list inputs
- `output` — declared return types
- `output_is_list` — per-output list flags
- `output_name` — human-readable output names when present
- `name` — node class name
- `display_name` — mapped UI display name when available
- `description` — node description when present
- `python_module` — source module path
- `category` — UI category path
- `output_node` — whether the node is an output node
- `has_intermediate_output` — whether the node can emit intermediate UI
- `output_tooltips` — optional output tooltip metadata
- `deprecated`, `experimental`, `dev_only` — capability flags when set
- `api_node` — API-node flag when present
- `search_aliases` — alternate search terms
- `essentials_category` — additional categorization metadata

For V1-compatible internal nodes derived from `_ComfyNodeInternal`, the
route can delegate to `GET_NODE_INFO_V1()` instead of manually building
the object.

Example shape:

```json
{
  "KSampler": {
    "input": {},
    "input_order": {},
    "output": ["LATENT"],
    "name": "KSampler",
    "display_name": "KSampler",
    "category": "sampling"
  }
}
```

## Dynamic UI Usage

This endpoint is what makes dynamic UIs possible. A client can:

- enumerate available nodes
- inspect input widgets and accepted types
- discover which nodes are outputs
- build menus from `category`
- render nicer labels from `display_name`
- adapt behavior for deprecated or experimental nodes

That makes `object_info` useful not only for the built-in ComfyUI
frontend, but also for API wrappers, custom editors, agent tooling, and
schema-aware documentation generators.

## Practical notes

- `GET /object_info` can be comparatively heavy because it walks every
  registered node class.
- `GET /object_info/{node_class}` is the better choice when you only need
  one node definition.
- Because the response is built from live registered nodes, custom nodes
  installed in the current ComfyUI instance appear naturally in the
  output.
