---
title: "Source Evidence Policy"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-06-04
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

### Multiple evidence sources on one page

When a page legitimately uses more than one evidence source, separate each
qualifier with a semicolon and a space. Example:
`Official docs-backed from docs.comfy.org; Source-backed from pinned snapshots`.

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

### Baseline verification status for prose pages

When a prose page depends on the repo's pinned source baseline, add a
`**Baseline verification status:**` line in the opening metadata block after the
evidence and source lines. Use it to say whether the prose was re-reviewed
against the current baseline, still reflects a prior baseline, or only received
mechanical citation updates after a refresh.

Use the wording patterns below instead of inventing page-by-page variants:

```markdown
**Baseline verification status:** Citation paths were updated where mechanical drift was obvious, but prose claims in this page have not yet been fully re-reviewed against the current baseline.
```

```markdown
**Baseline verification status:** Verified against the prior pinned baseline: core `v0.22.0`, frontend `v1.45.12`, snapshots `2026-05-21`. Current-baseline re-review is still pending.
```

```markdown
**Baseline verification status:** This page has not been re-reviewed against the current baseline.
```

For pages with mixed entry-level status, say that explicitly in the baseline
status line and point readers to the inline notes. Do not collapse mixed status
to a fully current claim.

### Current advisory verifier failure criteria

`scripts/verify/evidence_metadata_freshness.py` currently checks only these deterministic rules:

1. covered pages must include `**Evidence:**` and `**Last Updated:**` in the opening metadata block
2. retained API, hooks, custom-node, architecture, object-info, and machine-readable-artifact pages must include an opening `**Baseline verification status:**` line
3. retained deep-dive pages that make current-baseline claims must also include that opening baseline-status line
4. baseline-status exception wording must match one of the approved phrasings below

The verifier is advisory-first. Do not add extra heuristics there without updating
this policy and the maintainer lifecycle guidance in `CONTRIBUTING.md`.

Approved non-current exception phrasings:

```markdown
**Baseline verification status:** Verified against the prior pinned baseline: core `v0.22.0`, frontend `v1.45.12`, snapshots `2026-05-21`. Current-baseline re-review is still pending.
```

```markdown
**Baseline verification status:** Citation paths were updated where mechanical drift was obvious, but prose claims in this page have not yet been fully re-reviewed against the current baseline.
```

```markdown
**Baseline verification status:** This page has not been re-reviewed against the current baseline.
```

Approved current-baseline phrasings:

```markdown
**Baseline verification status:** Re-reviewed for core v0.23.0 / frontend v1.46.6 transition.
```

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

The active pinned baseline is tracked on
[Version Pin Status](version-pin-status.md). The current pinned snapshot set now
lives under `references/snapshots/2026-06-03/`, while older pinned snapshot
directories such as `2026-06-01/`, `2026-05-21/`, `2026-05-18/`, and
`2026-04-19/` remain useful historical comparison points.

- official docs are cited across the repo
- several pages also cite upstream source URLs or pinned snapshot paths
- machine-readable reference files in `references/raw/` point at the active
  pinned snapshot files for their extracted data
- some prose pages may still reflect a prior baseline or only partial
  current-baseline review; those pages should declare that with a baseline
  verification status block near the top
- this policy now formally integrates with the writing style guide at
  `writing-style-guide.md`

## Writing Standard

When exact evidence is weak or incomplete:

- say that explicitly
- avoid words like "authoritative" or "source of truth"
- prefer phrasing like "source-backed reference", "summary of upstream behavior",
  or "community pattern example"

## Read Next

- [Writing Style Guide](writing-style-guide.md)
- [Version Pin Status](version-pin-status.md)
- [Topic Scope](topic-scope.md)
