# Version History

**Evidence:** Official docs-backed from docs.comfy.org; Operational guidance
**Last Updated:** 2026-05-07
**Primary Source:** https://docs.comfy.org/changelog

## Primary Sources

- https://github.com/Comfy-Org/ComfyUI/releases
- https://docs.comfy.org/changelog

## Scope

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
exact tags, dates, and raw notes. Treat the sections below as review priorities
surfaced by those official release summaries, not as a pinned behavioral ledger.

## Compatibility Review Priorities

The following sections summarize themes that appear in the official changelog
and release notes. Use them to decide what to re-test first when upgrading.

### v0.19.x

- official release notes in this line show frequent patch releases, so extension
  authors should verify against exact patch versions rather than the minor line alone
- `v0.19.0` release notes call out additions such as `has_intermediate_output`,
  CURVE-related work, and continued frontend-version movement
- when this line changes node names, display names, or UI-facing metadata,
  downstream docs can go stale quickly

### v0.18.x

- `v0.18.0` release notes highlight `--fp16-intermediates`, additional
  Essentials-category support, asset/API alignment changes, and more
  Manager/frontend bumps
- this line is a good place to re-check dtype, precision, and device-flow
  assumptions in custom nodes

### v0.17.x

- `v0.17.0` release notes highlight larger architectural work, frontend updates,
  and more explicit Manager/version reporting
- later patches in this line are still worth re-testing if an extension relied
  on unstable or lightly documented internal behavior

### v0.16.x to v0.15.x

- official changelog entries across these lines continue the V3-schema rollout,
  add widget/datatype surfaces, and expand API-node/platform coverage
- older V1-style examples are more likely to drift here because official
  patterns increasingly assume V3 concepts

### v0.8.x to v0.3.x

- official changelog entries in these ranges show repeated V3 migration work,
  new dynamic UI/input features, and frontend evolution
- examples called out in the official notes include DynamicCombo, Autogrow,
  MatchType support, and migration of more built-in node categories to V3 schema

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

The repository's machine-readable artifacts are extracted from a pinned baseline
and published with versioned copies. When you need exact API or schema behavior
for a specific ComfyUI version, prefer the pinned artifacts over broad release
notes. See [Machine-Readable Artifacts](machine-readable-artifacts.md) for the
manifest and stable URLs.

## Read Next

- [Writing Style Guide](writing-style-guide.md)
- [Source Evidence Policy](source-evidence-policy.md)
