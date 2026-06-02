---
title: "Topic Scope"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-06-01

> **Operational Note:** This page defines what belongs in the published docs
> surface, what belongs only in repo-local maintainer guidance, and what should
> be pruned or archived instead of kept live under `src/content/docs/`.

**Primary Sources:** `AGENTS.md`, `CONTRIBUTING.md`

## Current Scope Rule

The published docs surface is intentionally bounded. It exists to help readers
build against ComfyUI and consume this repo's pinned reference material without
turning the site into a second maintainer handbook.

## What Belongs in Published Docs

Keep content published when it is one of these:

- start-here routing for a durable reader audience
- source-backed or official-docs-backed reference pages for retained API, hook,
  custom-node, architecture, and deep-dive topics
- bounded operational guidance that readers need to interpret the published
  artifacts or editorial trust model

Published pages should stay reusable, reader-facing, and stable enough that
they do not need constant workflow maintenance.

## What Belongs Only in `CONTRIBUTING.md` and `AGENTS.md`

Keep content repo-local when it is primarily maintainer workflow material, such
as:

- verification command inventories
- CI, workflow, and release-maintenance procedures
- generator, extractor, and verifier operating details
- refresh, rollback, and failure-path playbooks
- machine-oriented startup guidance for future agents

If the main reader benefit is "how maintainers operate this repo," it belongs in
`CONTRIBUTING.md` or `AGENTS.md`, not in the published docs tree.

## What Should Be Pruned or Archived Instead

Prune or archive content when it is one of these:

- overlapping routing pages that no longer add a unique reader path
- tutorial, troubleshooting, or ecosystem pages that duplicate stronger retained
  reference pages
- narrow maintainer procedures that drift quickly
- pages whose best remaining value is historical, not active navigation

Do not keep low-value pages alive by hiding them from the sidebar. If they are
not part of the retained surface, they should leave the active published tree.

## Practical Decision Rule

Before adding a new page, ask:

1. Does this help a reader build against ComfyUI or interpret the repo's pinned
   artifacts?
2. Is the page durable enough to keep current without turning into a workflow
   chore?
3. Would the same information be more truthful in `CONTRIBUTING.md` or
   `AGENTS.md`?

If the answer to the third question is yes, keep it repo-local.

## New Section Stop Rule

Do not add a new published docs section unless maintainers can state the
maintenance case, owner, verification path, and retirement criteria in
`CONTRIBUTING.md` before the section lands.

## Read Next

- [Machine-Readable Artifacts](machine-readable-artifacts.md)
- [Source Evidence Policy](source-evidence-policy.md)
- [Writing Style Guide](writing-style-guide.md)
