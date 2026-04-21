# Source Evidence Policy

**Last Updated:** 2026-04-21
**Primary Sources:** https://docs.comfy.org/, https://github.com/Comfy-Org/ComfyUI

## Purpose

This repository is a source-backed reference for ComfyUI development work. It is
not itself the source of truth for ComfyUI behavior.

## Evidence Levels

Apply this order of trust when writing or revising content:

1. official ComfyUI documentation pages on `docs.comfy.org`
2. upstream ComfyUI source files and release notes
3. this repository's summaries, extracted references, and example write-ups
4. community repositories and ecosystem articles

## Evidence Labels

Every page in this repository should carry one of the following evidence labels
in its opening section. Place the label immediately after the page title and scope
statement.

### Source-backed

Behavior is derived from current ComfyUI source code. Include the source file
path or URL, and pin to a commit when possible.

Qualifier (preferred): `Source-backed from pinned snapshots`

### Official docs-backed

Behavior is stated in official ComfyUI documentation on `docs.comfy.org`.

Qualifier (preferred): `Official docs-backed from docs.comfy.org`

### Community pattern

Examples from external repositories such as custom node packs, wrapper APIs,
dashboards, or monitoring extensions. These show useful patterns without
defining native ComfyUI behavior.

Qualifier (preferred): `Community pattern study based on pinned external version`

### Scaffold

Page is intentionally incomplete. Editors should not over-polish scaffold pages
beyond their intended state. Keep scope statements honest about what is missing.

## Labeling Rules

### Official behavior

Use this label only when the behavior is stated in official ComfyUI docs.

### Upstream source behavior

Use this label when behavior is derived from current ComfyUI source code. Include
the source file path or URL, and pin to a commit when possible.

### Community pattern example

Use this label for examples from external repositories such as custom node packs,
wrapper APIs, dashboards, or monitoring extensions. These examples can show
useful patterns without defining native ComfyUI behavior.

## When Evidence Is Weak or Incomplete

- say that explicitly
- avoid words like "authoritative" or "source of truth"
- prefer phrasing like "source-backed reference", "summary of upstream behavior",
  or "community pattern example"
- use the Scaffold label if the page covers material that has not yet been
  researched to the standard the repo requires

## Current Status

- official docs are cited across the repo
- several pages also cite upstream source URLs
- pinned source snapshots have been added under `references/snapshots/2026-04-19/`
- machine-readable reference files in `references/raw/` now point at those pinned
  snapshot files for their extracted data
- broader prose documentation still needs ongoing review to replace broad `master`
  URLs with exact pinned references where precision matters
- this policy now formally integrates with the writing style guide at
  `docs/reference/writing-style-guide.md`

## Writing Standard

When exact evidence is weak or incomplete:

- say that explicitly
- avoid words like "authoritative" or "source of truth"
- prefer phrasing like "source-backed reference", "summary of upstream behavior",
  or "community pattern example"
