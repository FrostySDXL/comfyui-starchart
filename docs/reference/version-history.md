# Version History

**Last Updated:** 2026-04-19
**Primary Source:** https://docs.comfy.org/changelog

## Primary Sources

- https://github.com/Comfy-Org/ComfyUI/releases
- https://docs.comfy.org/changelog

## Overview

This page is not a full release log. It is a compatibility-focused summary for
custom node and extension authors who need to track changes that can alter:

- node schema expectations
- frontend integration points
- server/runtime behavior
- Manager and packaging assumptions

For authoring work, recent ComfyUI releases matter less as isolated patch notes
and more as moving layers:

- core/backend execution behavior
- frontend package revisions
- V3 schema migration progress
- Manager and registry workflows

When upgrading, check both the official changelog and the GitHub releases page.
The changelog is easier to scan for themes; the releases page is better for
exact commit ranges and raw notes.

## Breaking Changes

Recent author-relevant themes from the official changelog and release notes:

### v0.19.x

- rapid patch cadence means extension authors should verify against exact patch
  versions, not just the minor line
- `v0.19.0` added `has_intermediate_output` for interactive UI nodes, expanded
  CURVE-related functionality, and continued frontend/version bumps
- releases in this line continue to add and rename nodes quickly, so docs that
  depend on exact node names or display names can go stale fast

### v0.18.x

- `v0.18.0` introduced `--fp16-intermediates`, additional Essentials-category
  support, asset/API alignment changes, and more Manager/frontend bumps
- memory-management and dtype behavior changed materially in this line, which
  matters for custom nodes that assume specific tensor precision or device flow

### v0.17.x

- `v0.17.0` brought larger architectural changes including asset architecture
  work, frontend updates, and more explicit Manager/version reporting
- patch releases in this line were mostly stabilization, but that still matters
  if your extension relied on unstable internal behavior

### v0.16.x to v0.15.x

- these releases continued broad V3-schema rollout, new widget/datatype
  surfaces, and API-node/platform expansion
- if you maintain older V1-style examples, this is where drift becomes more
  obvious because official patterns increasingly assume V3 concepts

### v0.8.x to v0.3.x

- official changelog entries in these ranges show repeated V3 migration work,
  new dynamic UI/input features, and frontend evolution
- examples include DynamicCombo, Autogrow, MatchType support and migration of
  more built-in node categories to V3 schema

The practical takeaway: compatibility breaks are often not one dramatic API
removal. They are cumulative drift across schema, frontend packaging, runtime
assumptions, and node metadata.

## Migration Notes

Before upgrading a custom node pack or extension against a newer ComfyUI line:

- verify whether your implementation depends on V1 internals when an official
  V3 path now exists
- re-check frontend assumptions whenever the changelog shows a frontend package
  bump or UI rework
- re-check Manager assumptions whenever docs mention registry or Manager version
  changes
- re-test datatypes and widget behavior when releases add new schema features
  such as CURVE, DynamicCombo, Autogrow, or intermediate-output flags
- avoid depending on undocumented execution internals when a newer supported
  hook exists

For this knowledge base, treat version-specific guidance as pinned to the cited
official pages plus whichever upstream commit or release your local ComfyUI
snapshot matches. If you cannot state the target ComfyUI version, do not make
strong compatibility claims.
