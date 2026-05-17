---
title: "Subgraph Extension Behavior"
---

**Evidence:** Official docs-backed from docs.comfy.org
**Last Updated:** 2026-05-13
**Primary Source:** https://docs.comfy.org/custom-nodes/js/subgraphs

## Primary Sources

- https://docs.comfy.org/custom-nodes/js/subgraphs
- https://docs.comfy.org/custom-nodes/js/javascript_hooks

## Scope

This page covers subgraph-related extension behavior that is exposed at the
frontend hooks surface. It focuses on node identifiers, root-versus-active graph
distinctions, traversal patterns, subgraph events, widget-promotion behavior,
and cleanup concerns.

It does not document execution-model internals such as validation order, lazy
evaluation, or execution engine behavior.

## Node identifier types

Subgraph-aware extensions need to distinguish between node identity in the root
workflow and node identity inside the currently active graph view. The official
subgraph docs frame these identifiers as separate concerns because traversal and
UI behavior can depend on which graph context the extension is working in.

Use the documented identifier model from the subgraph docs instead of assuming a
single flat node namespace.

## Root graph versus active graph

Subgraph behavior depends on whether an extension is reasoning about:

- the root workflow graph
- the currently active graph or subgraph view

That distinction matters for extension code that walks nodes, resolves parents,
or updates UI state for the graph the user is currently viewing.

## Traversal patterns

The official subgraph docs treat traversal as a graph-context problem, not just
a list-walk problem. When an extension needs to find related nodes, parent
containers, or active descendants, it should follow the documented subgraph
traversal model instead of assuming all nodes are visible in one level.

This is primarily a hooks-surface and UI-traversal concern. It is not a claim
about execution scheduling or graph evaluation order.

## Subgraph events

Subgraph-aware extensions may need to react when the active graph context
changes. Treat these as UI-facing graph-context events rather than as a general
execution event system.

If the extension logic is really about workflow loading or startup sequencing,
route back to the relevant JavaScript hook such as `beforeConfigureGraph`,
`afterConfigureGraph`, or `setup`.

## Widget-promotion behavior

The official subgraph docs call out widget-promotion behavior as part of the
subgraph extension surface. Extensions that alter node UI or inspect promoted
widgets should keep that behavior in the frontend layer.

Do not flatten widget-promotion behavior into a stable execution-model guarantee.
It is better understood as part of the editor and graph-view behavior that the
frontend exposes.

## Cleanup concerns

Subgraph-aware UI integrations can leave stale listeners, stale graph-context
state, or stale node references behind if cleanup is skipped. Treat cleanup as a
normal part of subgraph-facing extension work, especially when the extension
tracks active graph changes or attaches UI behavior to nodes as views change.

## Stability note

If a subgraph behavior appears to move with active graph context, view changes,
or widget-promotion state, describe it as context-sensitive behavior rather than
as a fixed guarantee across all editor states.

## Read Next

- [JavaScript Hooks](javascript-hooks.md)
- [Extension Points](extension-points.md)
