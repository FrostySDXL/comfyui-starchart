---
title: "Known Limitations"
---

**Evidence:** Official docs-backed from docs.comfy.org; Source-backed from pinned snapshots
**Last Updated:** 2026-05-18

## Scope

This page is intentionally small. It only keeps limitations that can be
verified against the repo's pinned ComfyUI snapshots or official docs.

**Tier note:** This page uses two evidence tiers. Tier 1 covers limitations
verified directly against official docs or this repo's pinned snapshots. Tier 2
covers curated community-reported limitations only when the report is specific,
reproducible, and clearly labeled as external evidence. In the current
revision, every listed entry is Tier 1 because no additional Tier 2 item met
the page's evidence threshold. The curation policy on this page is Operational
guidance.

## Curation Policy

Before adding an entry:

1. Verify the limitation against the current pinned ComfyUI baseline.
2. Cite the exact docs.comfy.org page or pinned snapshot file.
3. State the verified version scope directly.
4. Prefer omission over a broad or weakly sourced claim.

---

## Category Map

Use the sub-pages below instead of treating every limitation as one flat list.

### API and Execution Boundaries

Use [API and Execution Boundaries](api-execution-boundaries.md) for limitations
caused by API mode, queue/history behavior, runtime `object_info`, and
execution-event boundaries.

### Service Surface Boundaries

Use [Service Surface Boundaries](service-surface-boundaries.md) for limitations
specific to official cloud or MCP surfaces.

### Extension Boundaries

Use [Extension Boundaries](extension-boundaries.md) for Manager, registry, and
extension-package lifecycle constraints.

---

## Adding an Entry

When adding an entry, use this template:

```markdown
### Limitation Title

**Source:** [exact docs.comfy.org page or pinned snapshot path]

**Verified in:** [pinned version or exact doc scope]

**Status:** [open, fixed, or behavioral constraint]

**Description:** [clear description of the limitation]

**Workaround:** [if one exists, with caveats]

**Last verified:** [date]
```

---

## Maintenance

Review this page when the repo's ComfyUI version pin changes. Remove entries
that no longer reproduce or that depend on community-only evidence.

## Read Next

- [API and Execution Boundaries](api-execution-boundaries.md)
- [Service Surface Boundaries](service-surface-boundaries.md)
- [Extension Boundaries](extension-boundaries.md)
