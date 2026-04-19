# ComfyUI Knowledge Base

**Last Updated:** 2026-04-19
**Primary Source:** https://docs.comfy.org/

## Primary Sources

- https://docs.comfy.org/
- https://github.com/Comfy-Org/ComfyUI

## Overview

This repository is a source-backed working knowledge base for ComfyUI authors,
especially people building:

- custom nodes
- frontend or server extensions
- route-backed tools and dashboards
- reference extractors and generated docs

Use it as a local, reviewable layer between scattered upstream sources and your
own implementation work. The goal is not to mirror all ComfyUI docs, but to
capture the parts most useful for development and maintenance.

## Navigation Map

- `docs/api/` for HTTP endpoints, WebSocket behavior, prompt submission, queue,
  and history semantics
- `docs/hooks/` for JavaScript hooks, server hooks, and extension points
- `docs/custom-nodes/` for V3-oriented node authoring guidance, registration,
  datatypes, and best practices
- `docs/extensions/` for higher-level extension architecture patterns and
  case-study analysis such as ProfilerX
- `docs/reference/` for compact summaries and version-tracking pages
- `docs/tutorials/` for task-oriented build guides that combine multiple
  concepts
- `docs/how-to/` for focused operational recipes like adding routes or Manager
  integration

If you are new to ComfyUI development, start with:

1. `custom-nodes/development-guide.md`
2. `hooks/extension-points.md`
3. `extensions/patterns.md`
4. the relevant tutorial or how-to page for your task

## Version Pinning

ComfyUI changes quickly, so every page in this knowledge base should be read as
version-sensitive unless it explicitly says otherwise.

Interpret pages using this order of trust:

1. cited official docs page
2. cited upstream source file or release notes
3. this repository's summary of those sources

When adding or updating content:

- prefer official docs and upstream source code as primary sources
- record the source URL in the page header
- treat release-specific notes as tied to the current upstream changelog and
  release history
- update or pin snapshot material in `references/` when exact source state
  matters

Current pinned extraction baseline:

- ComfyUI core `v0.19.3` (`3086026401180c9216bcb6ace442a4e3587d2c66`)
- official frontend `v1.42.11` (`3dc4061d484d61cb89366de25bf5e2f8a65da4d0`)

If a page and the current upstream source disagree, trust upstream first and
update this repository accordingly.

## Evidence Levels

Keep the following distinction strict throughout this repo:

- official behavior: stated in `docs.comfy.org`
- upstream source behavior: visible in cited ComfyUI source files for a specific
  version or commit
- community pattern examples: useful ecosystem implementations that are not part
  of native ComfyUI's contract

Use community repositories for implementation ideas and packaging patterns, not
as the definition of official ComfyUI behavior.
