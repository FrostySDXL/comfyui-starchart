---
title: "General Diagnostic Workflow"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-05-18

## Scope

This page gives a general triage workflow for readers who know something is
wrong but do not yet know whether the problem belongs to the standard API,
custom nodes, frontend extensions, published artifacts, or this repository's
own maintenance workflow.

It is a routing workflow, not a full support manual.

## Step 1: Identify Which System Is Failing

Start by separating these cases:

- **live ComfyUI runtime** -- prompt execution, routes, WebSocket, or installed nodes
- **this repo's published docs or artifacts** -- pages, generated JSON, or version-pinned references
- **your extension or node package** -- custom code sitting on top of ComfyUI

If you skip this boundary check, you can spend time debugging the wrong layer.

## Step 2: Classify the Surface

Use the smallest truthful label for the failure:

| Symptom | Start here |
|---|---|
| request or response does not match expectations | [API Integration Troubleshooting](api-integration.md) |
| custom node versus frontend responsibility is unclear | [Custom Node and Extension Boundaries](custom-node-and-extension-boundaries.md) |
| docs build, page shape, or generated-vs-hand-authored confusion | [Docs Authoring and Site Build](docs-authoring-and-site-build.md) |
| version-pinned artifact or schema expectation is unclear | [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md) |
| runtime-only verification or smoke workflow is unclear | [Runtime and CI Operations](../reference/runtime-ci-operations.md) |

## Step 3: Confirm the Version Baseline

Many false bug reports are really baseline mismatches.

- check which ComfyUI version you are running
- check whether the repo page you read is describing a pinned artifact baseline
- check whether the package or workflow depends on community-maintained code

If the issue depends on community packages, verify the package state directly
instead of assuming the ecosystem map is current enough on its own.

## Step 4: Reproduce With the Smallest Check You Can Run

Prefer the narrowest reproducible check:

- one API call instead of a full app flow
- one node load or import path instead of a full workflow
- one doc verifier instead of the whole repo wrapper when you are iterating on docs

Smaller checks make it easier to decide whether the failure is runtime,
packaging, or documentation drift.

## Step 5: Decide the Next Owner Surface

After the small reproduction, route to the next page instead of staying vague:

- if it is a live API/runtime question, continue through the API or runtime docs
- if it is a package-boundary question, continue through custom node or extension docs
- if it is repo maintenance drift, continue through the reference and workflow docs

## Read Next

- [API Integration Troubleshooting](api-integration.md)
- [Custom Node and Extension Boundaries](custom-node-and-extension-boundaries.md)
- [Docs Authoring and Site Build](docs-authoring-and-site-build.md)
- [Runtime and CI Operations](../reference/runtime-ci-operations.md)
