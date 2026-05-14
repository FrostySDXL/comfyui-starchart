# Deep Dive: Workflow JSON as an Interchange Surface

**Evidence:** Official docs-backed from docs.comfy.org
**Last Updated:** 2026-05-13
**Primary Source:** https://docs.comfy.org/specs/workflow_json

## Scope

This page explains why the official workflow JSON specification matters as an
interchange surface for ComfyUI tooling. It is not a field-by-field schema
reference and not a tutorial for hand-authoring workflows.

The current official specification defines workflow JSON with JSON Schema and
publishes versioned schema documents. That makes the format useful not only for
editor persistence, but also for validation, generation, migration checks, and
tooling that needs a durable graph-shaped document format.

## Why workflow JSON matters

Workflow JSON is the strongest officially documented graph interchange surface in
 the ComfyUI ecosystem. It gives tooling authors a stable place to reason about:

- graph identity through node, link, group, and reroute objects
- editor-state persistence such as positions, sizes, and canvas metadata
- workflow-level metadata under `extra` and `models`
- versioned compatibility expectations through the schema itself

That role is different from the prompt submission API. `POST /prompt` is the
native execution entrypoint for an API-valid prompt graph. Workflow JSON is the
officially specified document surface that tools can inspect, transform, store,
or export before any API-specific conversion happens.

## Workflow JSON versus prompt execution payloads

The most important boundary for tool authors is that workflow JSON and prompt
submission are adjacent surfaces, not interchangeable ones.

- workflow JSON captures an editor-facing workflow document
- `/prompt` accepts an execution graph payload that passes server validation
- some community clients convert workflow exports into API-ready prompt graphs

That means a tooling pipeline often has two stages:

1. read or generate a workflow JSON document
2. convert or normalize it into the prompt graph shape required by execution

This repo's [Prompt Submission](../api/prompt-submission.md) page documents the
execution contract. Treat workflow JSON as the better surface for document-level
tooling, diffing, migration support, and graph exchange.

## Where schema structure matters

The official schema is valuable because it narrows what a conforming tool can
assume.

### Version is explicit

The current latest schema is published as workflow version `1`. That explicit
version field gives tooling a stable branch point for validation logic and for
future migration code.

### Required structure is narrow

The schema requires only a small core at the top level, including `version`,
`state`, and `nodes`. Many other surfaces are optional or allow additional
properties. That is a practical signal that tools should distinguish:

- truly required graph content
- optional editor metadata
- tolerated extension or future fields

### Nodes and links are typed but extensible

The schema constrains important shapes such as node IDs, positions, link source
and target references, and widget value containers. At the same time, many
objects allow additional properties. That combination supports two common tool
behaviors:

- strict validation of core graph wiring
- conservative preservation of fields a tool does not fully understand

For generators and migration tools, this is a key design signal: validate the
officially specified structure, but do not strip unknown fields casually.

### Workflow metadata is first-class

The schema includes top-level `models` metadata and optional `extra.info`
workflow metadata such as name, author, description, version, and timestamps.
That makes workflow JSON more than a node list. It is also a packaging surface
for workflow identity and associated assets.

## What the official spec does and does not guarantee

The official workflow JSON page gives a published schema and versioned format.
That supports claims about the document structure itself.

It does not by itself guarantee:

- that every workflow JSON document is directly executable through `/prompt`
- that editor-exported fields map one-to-one to server validation rules
- that community wrapper conversion logic reflects native ComfyUI behavior
- that undocumented extra fields have long-term semantics beyond schema
  tolerance

In practice, this means tooling authors should separate three concerns:

- workflow document validation against the published schema
- prompt-graph validation against server execution rules
- project-specific conversion or migration rules layered on top

## Tooling implications

### Good fit for local tooling

Workflow JSON is the right surface when you need to:

- lint exported workflows before execution
- store workflows in source control with predictable structure
- generate graphs from higher-level templates
- compare or migrate workflows across schema versions
- attach workflow metadata and model references in one document

### Not a substitute for node metadata discovery

Workflow JSON tells you how a workflow document is shaped. It does not replace
runtime node discovery. Use [Object Info](../reference/object-info.md) when a
tool needs the current server's node inputs, outputs, and widget metadata.

### Not a substitute for API contract verification

If a tool ultimately submits work to ComfyUI, it still has to respect the
execution-side rules documented in [Prompt Submission](../api/prompt-submission.md).
Schema-valid workflow documents and execution-valid prompt graphs overlap, but
they are not the same claim.

## Read Next

- [Tooling Builder](../start-here/tooling-builder.md)
- [Object Info](../reference/object-info.md)
- [Prompt Submission](../api/prompt-submission.md)
