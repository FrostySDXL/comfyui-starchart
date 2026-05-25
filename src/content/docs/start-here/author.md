---
title: "Start Here: Custom Node Author"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-05-24

## Who This Path Is For

You want to build custom nodes for ComfyUI. This could be:

- nodes for your own workflow automation
- a node pack you intend to publish through ComfyUI-Manager
- internal tooling for a specific use case

**Prerequisites:** basic Python and a working ComfyUI installation.

## First Practical Step

Start with one small server-side node. Define a narrow input/output contract,
load it in ComfyUI, and confirm it appears in the Add Node menu before adding
extra UI or packaging concerns.

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
   mental model, constraints, and stable authoring habits
2. [Node Structure](../custom-nodes/node-structure.md) -- schema and execution
   shape
3. [Registration](../custom-nodes/registration.md) -- how ComfyUI discovers the
   node package
4. [Datatypes](../custom-nodes/datatypes.md) -- built-in types and data-shape
   expectations

## V1 and V3

New authoring should prefer the modern guidance in the retained custom-node
pages. Older V1 patterns still matter when reading legacy repos, but they are no
longer broken out into separate retained routing pages.

## Example Boundary

Use the repo examples as bounded patterns, not as a full curriculum:

- `examples/custom-nodes/minimal-node-template/`
- `examples/custom-nodes/example-2-widgets/`
- `examples/custom-nodes/example-3-node-communication/`
- `examples/custom-nodes/example-4-progress-ui/`

## When to Switch to Repo-Local Workflow Docs

Stay in the published docs path unless you are contributing back to this
repository. If you start editing repo pages, examples, or scripts, switch to the
repo's `CONTRIBUTING.md` file for workflow and verification guidance.

## Read Next

- [Custom Node Development Guide](../custom-nodes/development-guide.md) -- mental model and constraints
- [Node Structure](../custom-nodes/node-structure.md) -- INPUT_TYPES, RETURN_TYPES, and execution
- [Registration](../custom-nodes/registration.md) -- discovery and package exposure
- [Datatypes](../custom-nodes/datatypes.md) -- built-in types and constraints
- [Start Here: Extension Developer](extension-developer.md) -- when the behavior
  crosses into frontend or server extension work
