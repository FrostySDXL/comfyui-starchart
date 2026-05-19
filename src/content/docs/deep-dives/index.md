---
title: "Deep Dives Section Guide"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-05-19

## Scope

This hub routes readers through the Deep Dives section. Use it to choose the
first analysis page to read, not as a replacement for the individual deep dives.

## Who This Section Is For

- extension authors who need higher-context official-docs guidance
- tooling builders comparing adjacent ComfyUI surfaces before implementation
- maintainers or advanced contributors investigating architecture tradeoffs

## Read First

- [Start Here: Tooling Builder](../start-here/tooling-builder.md) if you are
  still deciding whether you need a deep dive or a quicker routing page
- [Workflow JSON as an Interchange Surface](workflow-json-schema.md) if your work
  starts with workflow documents or graph interchange
- [Execution Pipeline](../architecture/execution-pipeline.md) if you need the
  main server-side execution path before reading inversion or packaging analysis

## Choose by topic

| Goal | Page |
|------|------|
| Understand workflow JSON as a tooling surface | [Workflow JSON as an Interchange Surface](workflow-json-schema.md) |
| Understand the official execution-model inversion guidance | [Execution Model Inversion](execution-model-inversion.md) |
| Understand registry packaging and compatibility contracts | [Registry Packaging and Compatibility](registry-packaging-and-compatibility.md) |
| Study a community package through bounded repo-local analysis | [ComfyUI-Manager (Community)](comfyui-manager.md), [ComfyUI-Impact-Pack (Community)](comfyui-impact-pack.md) |

## Section notes

- Official-docs-backed pages in this section explain why a surface matters and
  what boundaries it creates.
- Community-labeled pages are package studies, not official platform contracts.
- When you need route, hook, or node specifics after a deep dive, return to the
  corresponding API, Hooks, or Custom Nodes reference sections.

## Read Next

- [API Section Guide](../api/index.md)
- [Hooks Section Guide](../hooks/index.md)
- [Custom Nodes Section Guide](../custom-nodes/index.md)
