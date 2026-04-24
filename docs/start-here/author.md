# Start Here: Custom Node Author

**Evidence:** Mixed: source-backed (V1/V3 concepts) and scaffold examples (example ladder)
**Last Updated:** 2026-04-22

## Who This Path Is For

You want to build custom nodes for ComfyUI. This could be:

- nodes for your own workflow automation
- a node pack you intend to publish through ComfyUI-Manager
- internal tooling for a specific use case

**Prerequisites:** basic Python and a working ComfyUI installation.

## What You Need to Know

ComfyUI custom nodes follow a client-server model:

- **server side** is Python -- defines inputs, outputs, and execution logic
- **client side** is JavaScript -- renders widgets, responds to graph events,
  and sends/receives WebSocket messages

The two sides communicate through the PromptServer and the extension hooks
system. You do not need to understand both sides equally -- most nodes are
server-side Python only.

## Recommended Reading Order

1. [Custom Node Development Guide](../custom-nodes/development-guide.md) --
   mental model, V1 vs V3 overview, core constraints
2. [Node Structure](../custom-nodes/node-structure.md) -- INPUT_TYPES, RETURN_TYPES,
   FUNCTION, CATEGORY for V1; io.Schema and execute for V3
3. [Registration](../custom-nodes/registration.md) -- how ComfyUI discovers and
   loads your node
4. [Datatypes](../custom-nodes/datatypes.md) -- IMAGE, MODEL, CLIP, LATENT, STRING,
   and other built-in types
5. [Best Practices](../custom-nodes/best-practices.md) -- caching, validation,
   category naming, API-mode constraints

## V1 vs V3 Decision

See the [Decision Tree: Custom Node Architecture](../decision-trees/custom-node-architecture.md)
for a full branching guide on choosing V1, V3, and node structure patterns.

## If You Want to Publish Through Manager

Read [Integrate with Manager](../how-to/integrate-with-manager.md) in addition to
the above. Key requirements:

- git repository (typically GitHub)
- registration via ComfyUI-Manager's custom-node-list.json or the official
  registry
- `requirements.txt` for Python dependencies
- optional: `install.py`, `enable.py`, `disable.py`, `uninstall.py` lifecycle scripts

## Example Ladder

For incremental learning, work through these examples in order:

1. `examples/custom-nodes/minimal-node-template/` (the base
   example, corresponding to "example-1" in references) --
   single node, server-side only, official walkthrough example
2. `examples/custom-nodes/example-2-widgets/` --
   node with configuration widgets -- INPUT_TYPES with dropdowns and sliders
3. `examples/custom-nodes/example-3-node-communication/` --
   node communicating with other nodes -- batch processing, intermediate results
4. `examples/custom-nodes/example-4-progress-ui/` --
   node with frontend component -- custom server events and visible progress UI
5. `examples/custom-nodes/example-5-full-extension-package/` --
   complete small extension package -- multiple nodes, lifecycle scripts,
   Manager-ready structure

## First Practical Step

Create a single Python file in `custom_nodes/my_first_node.py` with a minimal
V1 node class, register it with `NODE_CLASS_MAPPINGS`, and restart ComfyUI.
Confirm the node appears in the Add Node menu before adding inputs or logic.

## Read Next

- [Custom Node Development Guide](../custom-nodes/development-guide.md) -- mental model and constraints
- [Node Structure](../custom-nodes/node-structure.md) -- INPUT_TYPES, RETURN_TYPES, and execution
- [Decision Tree: Custom Node Architecture](../decision-trees/custom-node-architecture.md) -- choose node type and V1 vs V3
- [Tutorial: Building Your First Node](../tutorials/building-first-node.md) -- guided walkthrough
