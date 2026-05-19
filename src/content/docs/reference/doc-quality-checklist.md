---
title: "Doc Quality Checklist"
---

**Last Updated:** 2026-05-19
**Related:** `writing-style-guide.md`, `source-evidence-policy.md`
**Evidence:** Operational guidance

Use this checklist before marking any documentation page complete. Run through
each item and confirm it passes or note why it does not apply.

## Pre-submission Review

Items marked (Required) must pass before a page is merged. (Recommended) items should be addressed but may be deferred with a comment. (Optional) items are best-effort.

### Page shape and mode

- [ ] (Required) Page mode is explicit and matches content
- [ ] (Required) Evidence label is present near the top of the page and is correct
- [ ] (Required) A scope statement appears in the opening paragraph or two

### Prose quality

- [ ] (Recommended) Sentences are short and direct; active voice is used where applicable
- [ ] (Recommended) Filler phrases are removed (e.g., "in order to", "it is important to note that")
- [ ] (Optional) Wording is concrete, not vague or inflated
- [ ] (Optional) The page does not begin with filler or repetition of adjacent docs

### Structure and navigation

- [ ] (Optional) Section order is intentional and follows the page mode
- [ ] (Recommended) "Who This Page Is For" appears when the audience is not obvious
- [ ] (Optional) Key takeaways or a decision summary appear for decision guides
- [ ] (Recommended) "Read Next" or "Related Pages" appears at the end with intentional links
- [ ] (Optional) Cross-links are navigational, not scattered incidental references
- [ ] (Optional) No "see also" style filler that does not add specific value

### Evidence and claims

- [ ] (Required) No claim of official ComfyUI behavior without a citation from `docs.comfy.org` or a pinned upstream source
- [ ] (Recommended) Official vs community claims are clearly separated
- [ ] (Recommended) Repo-local policy/process pages use `Operational guidance` and do not use that label to imply ComfyUI behavior claims are source-backed
- [ ] (Required) After a snapshot refresh, baseline verification status wording was reviewed; if the page is not fully current, the opening block says so explicitly
- [ ] (Optional) Source citations point to pinned snapshots or official docs where applicable
- [ ] (Optional) "TODO" or "incomplete" markers are honest; incomplete pages use the Scaffold label
- [ ] (Optional) No words like "authoritative" or "source of truth" without exact backing

### Build and links

- [ ] (Required) `npm run build` passes without new errors
- [ ] (Required) `references/` path mentions and navigational links resolve to valid targets
- [ ] (Recommended) No broken or dangling links

## When to Use This Checklist

- Before opening a PR that touches documentation
- Before marking a doc page complete during a review session
- During the weekly doc review pass described in `CONTRIBUTING.md`

This checklist is not a gate for draft or scaffold pages. Use it when you are
ready to declare a page meets the repo's editorial standards.
