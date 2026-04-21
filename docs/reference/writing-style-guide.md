# Writing Style Guide

**Last Updated:** 2026-04-21
**Related:** `source-evidence-policy.md` for evidence labeling rules

## Purpose

This guide defines the editorial standards for contributing to this repository.
It covers page modes, sentence and paragraph style, section naming conventions,
and cross-linking rules.

Use this guide alongside `source-evidence-policy.md`, which defines the evidence
labeling system this repo uses to make trust boundaries explicit.

## Page Modes

Every page should read as one primary mode. Choose the mode that fits the page
purpose and keep the writing consistent with that mode throughout.

### Reference

Documents API surfaces, data structures, schemas, hook catalogs, and other
items that are looked up rather than read cover-to-cover. Reference pages state
what exists and how it works, not how to use it in a workflow.

**Tone:** Declarative. Describe what is, not how to get there.

**Example opening:** "The `ChatOnMessage` server hook fires after any incoming
WebSocket message is parsed and before any per-type handler runs."

### Tutorial

Guides a reader through a sequence of steps to achieve a defined outcome.
Tutorials assume the reader is building something and needs instruction.

**Tone:** Imperative. Direct the reader with clear action steps.

**Example opening:** "This tutorial walks through registering a custom node class
that exposes a widget-based parameter to the ComfyUI frontend."

### Decision Guide

Helps a reader choose between options by laying out tradeoffs, constraints, and
context. Decision guides do not prescribe a single path; they equip the reader
to decide.

**Tone:** Neutral and balanced. Present options without steering unless one is
clearly unsuitable.

**Example opening:** "When integrating ComfyUI into an external service, the
choice between direct API calls and the WebSocket transport depends on whether
you need real-time feedback or simple fire-and-forget requests."

### Community Pattern Study

Documents a pattern observed in an external repository or ecosystem project.
Use this mode to capture useful examples without implying they define native
ComfyUI behavior.

**Tone:** Descriptive. Show what a project does and what patterns it demonstrates,
with explicit framing that the behavior is external.

**Example opening:** "ProfilerX is a ComfyUI extension that instruments the
execution graph to collect per-node timing metrics. This page documents its
analysis approach as a community-observed pattern."

### Scaffold

A page that is intentionally incomplete. Scaffolds hold a place for content
that has not yet been written to the repo's full standard. They should be honest
about their incompleteness.

**Tone:** Direct and honest. State what is missing.

**Do not over-polish scaffold pages.** Mark them with the Scaffold evidence
label and keep scope statements honest.

## Paragraph and Sentence Style

### Prefer short, direct sentences

Long sentences with multiple clauses are harder to scan and easier to
misread. Break compound sentences when each clause could stand alone.

**Weak:** "The hook system, which is exposed both server-side and client-side,
allows custom code to register callbacks that run at defined points during
execution, though not all hooks are available in both contexts."

**Stronger:** "The hook system exposes callbacks at defined execution points.
Some hooks are available only server-side, others only client-side, and a subset
are available in both contexts."

### Use active voice

Active voice makes it clearer who or what is acting.

**Weak:** "The widget value is updated by the frontend when the user interacts
with the control."

**Stronger:** "The frontend updates the widget value when the user interacts with
the control."

### One idea per sentence

If a sentence contains "and" where both clauses could be separate sentences,
split them. If "and" connects two ideas that must stay together to make sense,
keep it.

### Avoid filler phrases

Remove phrases that do not add information:

- "In order to" -> "To"
- "the fact that" -> omit or restructure
- "it is important to note that" -> say the thing directly
- "please note" -> say the thing

## Section Naming

Use these preferred names consistently where the section type applies:

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

### Prefer intentional links over scattered references

A few deliberate "Read Next" links at the end of a page are more useful than
many inline references that interrupt the prose.

### Use descriptive link text

Link text should describe what the reader will find, not "click here" or the
raw URL.

**Weak:** "See https://docs.comfy.org/ for official docs."

**Stronger:** "See the [official ComfyUI documentation](https://docs.comfy.org/)."

### Group related links

Place "Read Next" or "Related Pages" links in a dedicated block rather than
scattering them through the text.

## Evidence Labeling

Apply evidence labels as defined in `source-evidence-policy.md`. Place the
label near the top of the page, after the title and scope statement. Use the
qualified form when a pinned source is available.

## What This Guide Does Not Cover

- Extractor and generator scripts (see `AGENTS.md`)
- Machine-readable reference schema and validation
- Extraction idempotency and upstream pin checks
- The operational review checklist (see `doc-quality-checklist.md`)

For those topics, refer to `AGENTS.md` and the verification scripts in
`scripts/verify/`.
