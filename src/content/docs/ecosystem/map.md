---
title: "Ecosystem Map"
---

<!-- GENERATED FILE: do not edit directly. Edit references/community/ecosystem_packages.json and run python scripts/generate/generate_community_pages.py. Note: curated follow-up study highlights are maintained in the generator code, not in the JSON source. -->

# Ecosystem Map

**Evidence:** Community pattern study
**Last Updated:** 2026-05-06

Status labels were manually checked against public package pages and should be
re-verified before use. This page is a starting point, not a permanent assessment.

## Overview

This page maps major ComfyUI ecosystem packages with their maintenance status.
Maintenance status is the most important signal for anyone deciding whether to
build on or depend on a community package.

For how this catalog is generated, how maintenance tiers are interpreted, and
what this page does and does not claim, see
[Community Generated Surfaces](../reference/community-generated-surfaces.md).

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

- **Repo:** [https://github.com/ltdrdata/ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager)
- **Registry:** [https://registry.comfy.org](https://registry.comfy.org)
- **Status:** Actively Maintained
- **Last Release:** v8.28
- **Role:** Primary distribution mechanism for custom node packs; provides custom-node-list.json for discovery and Manager UI for install/update/remove
- **Notable Patterns:** legacy custom-node-list.json path, registry-backed flow
- **Used By:** Most ComfyUI users
- **Last Verified:** 2026-04-22

## Registry

### ComfyUI Registry

- **Registry:** [https://registry.comfy.org](https://registry.comfy.org)
- **Status:** Actively Maintained
- **Role:** Official package registry that backs the new Manager UI install experience; packages registered here surface cleanly in the modern Manager UI
- **Notable Patterns:** registry-backed install flow
- **Used By:** All registry-published packages
- **Last Verified:** 2026-04-22

## Node Packs

### ComfyUI-Impact-Pack

- **Repo:** [https://github.com/ltdrdata/ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack)
- **Status:** Actively Maintained
- **Pinned Commit:** `429d0159ad429e64d2b3916e6e7be9c22d025c3c`
- **Role:** Detector, Detailer, Upscaler, Pipe, and hook-provider nodes; the reference implementation of bundle-pipe datatypes in the community
- **Notable Patterns:** BASIC_PIPE, DETAILER_PIPE, hook-combine nodes, extensive use of composition patterns for schedule and detailer hooks
- **Used By:** Large workflows involving image enhancement, face restoration, and inpainting pipelines
- **Last Verified:** 2026-04-22

### comfyui_controlnet_aux

- **Repo:** [https://github.com/Fannovel16/comfyui_controlnet_aux](https://github.com/Fannovel16/comfyui_controlnet_aux)
- **Status:** Actively Maintained
- **Role:** Control and preprocessing node pack with 30+ annotator-backed preprocessors, an AIO preprocessor entry point, and structured pose output patterns that are useful for extension and API integration study.
- **Notable Patterns:** node_wrappers architecture, AIO Aux Preprocessor, structured OpenPose and DWPose JSON outputs, dev_interface extension path
- **Used By:** Workflows that depend on ControlNet preprocessing, pose extraction, and reusable annotator wrappers
- **Last Verified:** 2026-05-05
- **Caveats:** Research confidence: HIGH. Community-observed package; verify current upstream state before depending on it.

### ComfyUI-AnimateDiff-Evolved

- **Repo:** [https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved](https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved)
- **Status:** Actively Maintained
- **Role:** Video and animation node pack that extends motion-module sampling with sliding context windows, keyframe scheduling, and batch latent manipulation for temporally coherent generation.
- **Notable Patterns:** sliding context windows, motion-module view options, keyframe scheduling, batch latent manipulation
- **Used By:** Animation workflows that need motion-module scheduling and temporal coherence controls inside ComfyUI
- **Last Verified:** 2026-05-05
- **Caveats:** Research confidence: HIGH. Community-observed package; verify current upstream state before depending on it.

### ComfyUI-VideoHelperSuite

- **Repo:** [https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)
- **Status:** Actively Maintained
- **Role:** Video I/O and batch utility node pack that wraps ffmpeg with JSON-defined codec profiles and adds reusable latent and image batch helpers for animation pipelines.
- **Notable Patterns:** JSON-defined video format profiles, ffmpeg-backed video I/O, latent and image batch utilities, custom VHS_FILENAMES datatype
- **Used By:** Animation and video workflows that need video export, import, and batch manipulation utilities around core ComfyUI graphs
- **Last Verified:** 2026-05-05
- **Caveats:** Research confidence: HIGH. Community-observed package; verify current upstream state before depending on it.

### WAS Node Suite

- **Repo:** [https://github.com/WASasquatch/was-node-suite-comfyui](https://github.com/WASasquatch/was-node-suite-comfyui)
- **Registry:** [https://registry.comfy.org/nodes/was-ns](https://registry.comfy.org/nodes/was-ns)
- **Status:** Actively Maintained
- **Role:** Over 200 nodes covering image processing, masking, text handling, arithmetic, and video operations
- **Used By:** General ComfyUI users needing utility nodes
- **Last Verified:** 2026-04-22
- **Caveats:** A replacement pack provided for existing users following retirement of the original author; maintained by the community

### Efficiency Nodes

- **Repo:** [https://github.com/jags111/efficiency-nodes-comfyui](https://github.com/jags111/efficiency-nodes-comfyui)
- **Registry:** [https://registry.comfy.org/nodes/efficiency-nodes-comfyui](https://registry.comfy.org/nodes/efficiency-nodes-comfyui)
- **Status:** Actively Maintained
- **Last Release:** 2.0
- **Role:** Streamlined workflow nodes that reduce total node count; useful for simplifying complex graphs
- **Notable Patterns:** workflow simplification patterns
- **Used By:** Users building large or repetitive workflows
- **Last Verified:** 2026-04-22

## Tooling and Utilities

### ProfilerX

- **Repo:** [https://github.com/ryanontheinside/ComfyUI_ProfilerX](https://github.com/ryanontheinside/ComfyUI_ProfilerX)
- **Status:** Community Supported
- **Role:** Runtime monitoring extension that listens to execution events and exposes per-node timing metrics through a frontend panel
- **Notable Patterns:** hybrid extension combining server hooks, frontend hooks, and custom routes for metrics display
- **Used By:** Referenced as the canonical example of runtime monitoring in the extensions patterns page
- **Last Verified:** 2026-04-22

### ComfyUI-Tooling-Nodes

- **Repo:** [https://github.com/Acly/comfyui-tooling-nodes](https://github.com/Acly/comfyui-tooling-nodes)
- **Status:** Actively Maintained
- **Role:** Extension-owned HTTP routes for cached image transfer, model inspection, and translation helpers; /api/etn/... routes that serve external tooling while ComfyUI handles generation
- **Notable Patterns:** tool-facing extension routes combined with normal ComfyUI prompt execution
- **Used By:** External tooling integrations
- **Last Verified:** 2026-04-22

## Deep-Dive Candidates

For learning extension and node pack architecture, these three packages are
the most instructive follow-up studies in the current catalog:

1. **ComfyUI-Manager** -- hybrid extension architecture, custom routes, server
   hooks, and frontend panel integration
2. **comfyui_controlnet_aux** -- large-scale preprocessor wrapper design,
   structured pose-data outputs, and extension-friendly annotator packaging
3. **ComfyUI-AnimateDiff-Evolved** -- advanced animation scheduling,
   sliding context windows, and motion-module workflow design

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

