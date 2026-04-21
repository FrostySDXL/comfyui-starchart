# Doc Quality Checklist

**Last Updated:** 2026-04-21
**Related:** `writing-style-guide.md`, `source-evidence-policy.md`

Use this checklist before marking any documentation page complete. Run through
each item and confirm it passes or note why it does not apply.

## Pre-submission Review

### Page shape and mode

- [ ] Page mode is explicit (Reference, Tutorial, Decision Guide,
    Community Pattern Study, or Scaffold)
- [ ] The mode matches the actual content -- not mixed with another mode
- [ ] The evidence label is present near the top of the page and is correct
    (Source-backed, Official docs-backed, Community pattern, or Scaffold)
- [ ] A scope statement appears in the opening paragraph or two

### Prose quality

- [ ] Sentences are short and direct; no long run-on sentences
- [ ] Active voice is used where applicable
- [ ] Filler phrases are removed (e.g., "in order to", "it is important to note that")
- [ ] Wording is concrete, not vague or inflated
- [ ] The page does not begin with filler or repetition of adjacent docs

### Structure and navigation

- [ ] Section order is intentional and follows the page mode
- [ ] "Who This Page Is For" appears when the audience is not obvious
- [ ] Key takeaways or a decision summary appear for decision guides
- [ ] "Read Next" or "Related Pages" appears at the end with intentional links
- [ ] Cross-links are navigational, not scattered incidental references
- [ ] No "see also" style filler that does not add specific value

### Evidence and claims

- [ ] Official vs community claims are clearly separated
- [ ] No claim of official ComfyUI behavior without a citation from
    `docs.comfy.org` or a pinned upstream source
- [ ] Source citations point to pinned snapshots or official docs where applicable
- [ ] "TODO" or "incomplete" markers are honest; incomplete pages use the
    Scaffold label
- [ ] No words like "authoritative" or "source of truth" without exact backing

### Build and links

- [ ] `python -m mkdocs build` passes without new errors
- [ ] All internal cross-references resolve to existing pages
- [ ] No broken or dangling links

## When to Use This Checklist

- Before opening a PR that touches documentation
- Before marking a doc page complete during a review session
- During the weekly doc review pass described in `CONTRIBUTING.md`

This checklist is not a gate for draft or scaffold pages. Use it when you are
ready to declare a page meets the repo's editorial standards.
