# Ecosystem Map

**Evidence:** Community pattern study
**Last Updated:** 2026-04-21

Status labels were manually checked against public package pages on 2026-04-20
and should be re-verified before use. This page is a starting point, not a
permanent assessment.

## Overview

This page maps major ComfyUI ecosystem packages with their maintenance status.
Maintenance status is the most important signal for anyone deciding whether to
build on or depend on a community package.

A package that was popular two years ago may be effectively abandoned today.
Building new work on an abandoned dependency creates immediate maintenance debt.

Status labels on this page are time-bound assessments, not permanent facts.
Treat them as a starting point and confirm the current project state before
depending on a package.

## Maintenance Status Legend

| Status | Meaning |
|--------|---------|
| Actively Maintained | Regular releases within the last 6 months; issues/PRs get responses |
| Community Supported | Original author inactive; community may still merge PRs or release |
| Likely Unmaintained | No releases in over 12 months; no recent commits or responses |
| Unknown | Insufficient public signal to assess |

## How to Assess Maintenance

Before depending on a community package:

1. check the GitHub release page for release dates
2. scan recent commit history (last 30 commits) for activity
3. look at open issues -- are they accumulating without responses?
4. check whether a Discord or support channel exists with recent activity
5. verify the package works with your ComfyUI version before building workflows
   around it

## Package Managers and Distribution

### ComfyUI-Manager

- **Repo:** [ltdrdata/ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager)
- **Registry:** [registry.comfy.org](https://registry.comfy.org)
- **Status:** Actively Maintained
- **Last Release:** November 2025 (v8.28)
- **Role:** Primary distribution mechanism for custom node packs; also provides
  custom-node-list.json for discovery and Manager UI for install/update/remove

This is the de facto standard for ComfyUI package distribution. The Manager UI
has two flows: the legacy custom-node-list.json path and the newer
registry-backed flow. Both are relevant depending on what packages a user has
installed.

### ComfyUI Registry

- **URL:** [registry.comfy.org](https://registry.comfy.org)
- **Status:** Actively Maintained (official Comfy-org project)
- **Role:** Official package registry that backs the new Manager UI install
  experience. Packages registered here surface cleanly in the modern Manager UI.
  Arbitrary git URL installs are not supported in the new UI for security reasons.

## Node Packs

### ComfyUI-Impact-Pack

- **Repo:** [ltdrdata/ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack)
- **Status:** Actively Maintained
- **Last Release:** November 2025
- **Role:** Detector, Detailer, Upscaler, Pipe, and hook-provider nodes; the
  reference implementation of bundle-pipe datatypes in the community
- **Notable Patterns:** BASIC_PIPE, DETAILER_PIPE, and hook-combine nodes;
  extensive use of composition patterns for schedule and detailer hooks
- **Used By:** Large workflows involving image enhancement, face restoration,
  and inpainting pipelines

### WAS Node Suite

- **Repo:** [WASasQuatch/was-node-suite-comfyui](https://github.com/WASasquatch/was-node-suite-comfyui)
- **Registry:** [registry.comfy.org/nodes/was-ns](https://registry.comfy.org/nodes/was-ns)
- **Status:** Actively Maintained
- **Role:** Over 200 nodes covering image processing, masking, text handling,
  arithmetic, and video operations
- **Note:** A replacement pack provided for existing users following retirement of
  the original author; maintained by the community

### Efficiency Nodes

- **Repo:** [jags111/efficiency-nodes-comfyui](https://github.com/jags111/efficiency-nodes-comfyui)
- **Registry:** [registry.comfy.org/nodes/efficiency-nodes-comfyui](https://registry.comfy.org/nodes/efficiency-nodes-comfyui)
- **Status:** Actively Maintained
- **Version:** 2.0
- **Role:** Streamlined workflow nodes that reduce total node count; useful for
  simplifying complex graphs

## Tooling and Utilities

### ProfilerX

- **Role:** Runtime monitoring extension that listens to execution events and
  exposes per-node timing metrics through a frontend panel
- **Pattern:** Hybrid extension combining server hooks, frontend hooks, and
  custom routes for metrics display
- **Status:** Community Supported -- referenced as the canonical example of
  runtime monitoring in the extensions patterns page

### ComfyUI-Tooling-Nodes

- **Repo:** [Acly/comfyui-tooling-nodes](https://github.com/Acly/comfyui-tooling-nodes)
- **Role:** Extension-owned HTTP routes for cached image transfer, model
  inspection, and translation helpers; `/api/etn/...` routes that serve
  external tooling while ComfyUI handles generation
- **Pattern:** Tool-facing extension routes combined with normal ComfyUI prompt
  execution

### ComfyUI-CollatUI

- **Role:** Frontend extension for styling and UI improvements
- **Status:** Unknown -- verify current maintenance before building on this

## Deep-Dive Candidates

For learning extension and node pack architecture, these three packages are
the most instructive:

1. **ComfyUI-Manager** -- hybrid extension architecture, custom routes, server
   hooks, and frontend panel integration
2. **ComfyUI-Impact-Pack** -- V1 node patterns, pipe/bundle datatypes, and
   large-scale node pack organization
3. **efficiency-nodes-comfyui** -- V3-style node structure and workflow
   simplification patterns

## Scope Notes

This map covers packages that appear in ComfyUI-Manager's distribution list or
that are frequently referenced in official docs and community discussions. It
does not attempt to catalog every custom node repo -- there are thousands.

Package status reflects publicly observable signals only. A "Community
Supported" label does not guarantee responsiveness. Verify directly before
building production dependencies.

This map is repo-local and not automatically refreshed. When adding a new
package as a dependency, verify its current status rather than relying on this
page.
