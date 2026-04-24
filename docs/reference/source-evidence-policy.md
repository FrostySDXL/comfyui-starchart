# Source Evidence Policy

**Last Updated:** 2026-04-23
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

### Operational guidance

Page defines repo-local policy, process, maintenance workflow, or operating
rules. Use this label for documentation about how this repository is maintained,
not for claims about native ComfyUI behavior.

Qualifier (preferred): `Operational guidance`

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

### Repo-local policy or process

Use `Operational guidance` for repo-local policy, process, and operations pages.
These pages describe how this repository is maintained and verified. They do not
raise the trust level of any ComfyUI behavior claim.

## When Evidence Is Weak or Incomplete

- say that explicitly
- avoid words like "authoritative" or "source of truth"
- prefer phrasing like "source-backed reference", "summary of upstream behavior",
  or "community pattern example"
- use the Scaffold label if the page covers material that has not yet been
  researched to the standard the repo requires

## Evidence Edge-Case Examples

These examples show how to apply the evidence rules in ambiguous situations:

**Upstream source disagrees with official docs**
If `docs.comfy.org` says one behavior and the pinned source shows another, prefer the source and note the discrepancy explicitly. Example: "Source-backed: the pinned server source shows the hook fires on line 847 of `server.py`, which differs from the docs description."

**No official docs and no pinned source for an API item**
If the item exists in `object_info` or the API schema but has no documentation and no source snapshot yet, use "Source-backed (pinned snapshot)" with the snapshot path, and note the gap explicitly. Do not invent behavior.

**Behavior is inferred from multiple sources, not a single one**
If the behavior is reconstructed from several source files, use "Source-backed from pinned snapshots" and list each relevant file in the evidence label. Do not flatten to a single citation.

**A community repo demonstrates a pattern the official docs do not cover**
Use the Community Pattern label. Do not promote it to Source-backed or Official docs-backed without a separate upstream verification step.

**The page covers a ComfyUI feature added after the most recent snapshot pin**
If a feature is in `master` but not yet in a pinned snapshot, note it: "Source-backed from ComfyUI master (unpinned)" -- do not use the unqualified Source-backed label. Flag for snapshot refresh.

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
