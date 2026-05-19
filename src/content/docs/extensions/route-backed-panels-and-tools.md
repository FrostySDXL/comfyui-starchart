---
title: "Route-Backed Panels and Tools"
---

**Evidence:** Official docs-backed from docs.comfy.org; Community pattern study based on pinned external version
**Last Updated:** 2026-05-18
**Primary Sources:** https://docs.comfy.org/development/comfyui-server/comms_routes, https://docs.comfy.org/custom-nodes/js/javascript_hooks, `https://github.com/Acly/comfyui-tooling-nodes`, `https://github.com/ryanontheinside/ComfyUI_ProfilerX`

## Scope

This page documents the route-backed tool pattern: a frontend panel or control
surface paired with extension-owned HTTP routes.

It covers when this pattern fits, what contracts it creates, and how to keep it
bounded. It does not replace the lower-level custom-route implementation guide.

## When This Pattern Fits

Use a route-backed tool when you need both of these:

- a frontend surface such as a panel, menu action, or inspector
- explicit request/response access to server-owned state or helper behavior

Common examples include:

- dashboards that fetch runtime or stored status
- inspectors that query server metadata on demand
- tool integrations that upload, download, or translate data outside prompt
  submission

## Minimal Shape

The pattern has three parts:

1. frontend registration code adds a panel, action, or listener
2. frontend code calls an extension-owned route with `fetchApi(...)`
3. backend route handlers return stable JSON or perform a narrow command

If you only have step 2 without a real UI or tool-facing need, you may not need
the pattern at all. If you need graph-executable behavior, add a custom node
instead of pushing workflow logic into routes.

## Contract Checklist

Keep the route surface narrow:

- namespace the route to the extension instead of overloading built-in paths
- validate incoming fields before mutating state
- return stable JSON shapes that frontend code can depend on
- keep route functions thin and move logic into helpers or modules
- treat the route as a public compatibility surface once the panel or an
  external tool depends on it

## Choose This Pattern When

| Need | Better fit |
|---|---|
| Editor panel needs server state on demand | route-backed panel |
| External tool needs helper endpoints beside normal prompt execution | route-backed tool |
| UI-only graph changes with no server state | frontend-only extension |
| Workflow-visible data processing | custom node |
| Execution observation without a UI contract | server hooks |

## Community Pattern Examples

These are external examples, not native ComfyUI requirements:

- `Acly/comfyui-tooling-nodes` demonstrates extension-owned `/api/etn/...`
  helper routes for tool-facing integrations
- `ryanontheinside/ComfyUI_ProfilerX` demonstrates a panel plus route-backed
  metrics and archive access for monitoring workflows

Use them as pattern studies. Do not assume their route names or payload shapes
are part of ComfyUI's native API.

## Read Next

- [Add Custom Routes](../how-to/add-custom-routes.md)
- [Extension Lifecycle Boundaries](extension-lifecycle-boundaries.md)
- [ProfilerX Analysis](profilerx-analysis.md)
- [Decision Tree: Choosing an Integration Approach](../decision-trees/api-integration.md)
