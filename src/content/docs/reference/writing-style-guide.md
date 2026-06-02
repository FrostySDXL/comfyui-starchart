---
title: "Writing Style Guide"
---

**Last Updated:** 2026-06-01
**Related:** `source-evidence-policy.md` for evidence labeling rules
**Evidence:** Operational guidance

The page title should come from frontmatter `title`. Do not duplicate it with a
leading markdown `#` heading.

## Purpose

This guide defines the published-doc writing standard for this repository. Use
it with `source-evidence-policy.md` for evidence labels and with
`CONTRIBUTING.md` for maintainer workflow and the editorial checklist.

## Page Modes

Each page should read as one primary mode. Pick the dominant mode and stay
consistent.

### Reference

Use for APIs, schemas, hooks, node structures, and other lookup surfaces.

**Tone:** declarative. State what exists and how it behaves.

### Tutorial

Use for step-by-step instruction toward one defined outcome.

**Tone:** imperative. Tell the reader what to do next.

### Decision Guide

Use for option comparison, tradeoffs, and routing.

**Tone:** neutral. Explain what favors each option.

### Community Pattern Study

Use for patterns observed in external projects without implying native ComfyUI
behavior.

**Tone:** descriptive. Use framing such as `observed`, `demonstrates`, or
`community pattern`.

### Scaffold

Use only for intentionally incomplete pages.

**Tone:** direct and honest. State what is missing and do not over-polish it.

## Page-Type Decision Matrix

| Page type | Primary purpose | Key signal words |
|---|---|---|
| Reference | Look up a fact or surface | `is`, `returns`, `contains` |
| Tutorial | Follow steps to an outcome | `first`, `then`, `finally` |
| Decision Guide | Compare options | `vs`, `tradeoff`, `choose` |
| Community Pattern | Document an external pattern | `observed in`, `external` |
| Scaffold | Hold unfinished content honestly | `TODO`, `incomplete` |

If an opening could fit multiple modes, choose the dominant one and avoid mode
mixing.

## Minimum Acceptable Standard by Mode

Each mode has a minimum bar before the page is considered complete.

**Reference**

- Evidence label present and correct
- At least one concrete API item documented (field, method, hook, endpoint)
- No purely narrative prose; structure follows API item order

**Tutorial**

- Steps are numbered and actionable
- Each step has a clear before/after state or expected output
- A "What to expect when it works" section or equivalent closing

**Decision Guide**

- At least two options presented with explicit tradeoffs
- Explicit "choose X when ..." framing for each option
- No recommendation unless one option is clearly unsuitable for a stated case

**Community Pattern**

- Source repository or project named and linked
- Behavior described with "observed" or "demonstrates" framing, not "ComfyUI does"
- Explicit limitation statement: "this is external behavior, not native ComfyUI"

**Scaffold**

- Scope statement honestly describes what is missing
- No placeholder text that implies coverage the page does not have
- Scaffold label applied

## Start-Here and Decision-Tree Page Anti-Patterns

These pages are high-traffic entry points, so weak routing causes outsized
confusion.

**Do not do these on start-here pages:**

- Open with a repo overview instead of audience framing ("This repo contains...")
- List every doc section instead of recommending a specific sequence
- End without a concrete "first action" or "read this next" step
- Repeat the same framing that exists on adjacent decision-tree pages

**Do not do these on decision-tree pages:**

- Use decision trees as extended tutorials (branching steps are not the same as tutorial steps)
- End a branch without sending the reader to a concrete page or resource
- Cover more than three branching decision levels (readers lose track)
- Present options without stating what conditions favor each choice

Start-here pages should say "read these pages in this order." Decision trees
should say "answer these questions to know where to go next."

## Paragraph and Sentence Style

### Prefer short, direct sentences

Break long multi-clause sentences when each clause can stand on its own.

**Weak:** "The hook system, which is exposed both server-side and client-side,
allows custom code to register callbacks that run at defined points during
execution, though not all hooks are available in both contexts."

**Stronger:** "The hook system exposes callbacks at defined execution points.
Some hooks are available only server-side, others only client-side, and a subset
are available in both contexts."

### Use active voice

Active voice makes the actor clearer.

**Weak:** "The widget value is updated by the frontend when the user interacts
with the control."

**Stronger:** "The frontend updates the widget value when the user interacts with
the control."

### One idea per sentence

If a sentence contains two ideas that can stand alone, split them.

### Avoid filler phrases

Cut phrases that do not add meaning:

- "In order to" -> "To"
- "the fact that" -> omit or restructure
- "it is important to note that" -> say the thing directly
- "please note" -> say the thing

## Section Naming

Use these names consistently when the section type applies:

| Section | Use for |
|---------|---------|
| `Who This Page Is For` | Audience and prerequisites |
| `Evidence` | Evidence label and source citations |
| `Key Takeaways` | Decision summary or main points |
| `Read Next` | Intentional next-step links |
| `Scope` | What the page covers and what it does not |

Do not force every page to use every section. Use only what fits the page mode
and content.

## Cross-Linking Rules

Prefer a few intentional links over scattered inline references. End-of-page
`Read Next` or `Related Pages` sections usually work better than frequent
mid-paragraph link drops.

Link text should describe the destination, not `click here` or a raw URL.

**Weak:** "See https://docs.comfy.org/ for official docs."

**Stronger:** "See the [official ComfyUI documentation](https://docs.comfy.org/)."

## Evidence Labeling

Apply evidence labels exactly as defined in `source-evidence-policy.md`. Place
the label near the top of the page after the title metadata and opening scope.
Use `Operational guidance` for repo-local policy and process pages only; do not
use it to support claims about ComfyUI behavior.

If a page depends on the repo's pinned baseline, place the
`**Baseline verification status:**` block immediately under the opening
evidence/source metadata and before the first main section heading. Use it when
the page is verified against the current baseline, still relies on a prior
baseline, or only received mechanical citation updates after a refresh. Reuse
the exact wording patterns from `source-evidence-policy.md` instead of making up
new variants.

### Audience-routing pages with mixed evidence

`start-here/` pages may need mixed evidence treatment when they combine routing
guidance with source-backed factual claims.

- `Operational guidance` alone is not sufficient when the page also makes pinned
  behavior claims about routes, hooks, node models, or other ComfyUI surfaces.
- Choose the label that matches the strongest factual claims on the page, not
  just its navigational role.
- Do not force uniform evidence labels across all routing pages when their claim
  mix is genuinely different.

## What This Guide Does Not Cover

- Extractor and generator scripts (see `AGENTS.md`)
- Machine-readable reference schema and validation
- Extraction idempotency and upstream pin checks
- The maintainer operational review checklist (see `CONTRIBUTING.md`)

For those topics, refer to `AGENTS.md` and the verification scripts in
`scripts/verify/`.

## Quick Reference

- Pick one page mode and stay in it.
- Keep the opening scope honest.
- Use short sentences, concrete wording, and active voice.
- Prefer intentional `Read Next` links over scattered inline links.
- Apply evidence labels and baseline-status wording exactly as defined in
  `source-evidence-policy.md`.
- Use `CONTRIBUTING.md` for the maintainer workflow and editorial checklist.

## Read Next

- [Source Evidence Policy](source-evidence-policy.md)
- [Topic Scope](topic-scope.md)
- [Version Pin Status](version-pin-status.md)
