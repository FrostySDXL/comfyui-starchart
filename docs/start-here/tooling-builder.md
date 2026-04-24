# Start Here: Tooling Builder

**Evidence:** Operational guidance
**Last Updated:** 2026-04-24

## Who This Path Is For

You are building tools, agents, or external services that interact with ComfyUI
programmatically. This includes:

- automation scripts that submit workflows
- IDE plugins or graph editors
- monitoring or profiling dashboards
- agents that discover or invoke nodes

**Prerequisites:** basic HTTP/WebSocket knowledge and familiarity with JSON.

## References That Matter Most

| Artifact | Location | Use for |
|----------|----------|---------|
| Node metadata | [`references/raw/object_info_runtime.json`](../reference/object-info.md) | Discover inputs, outputs, and types for any node |
| HTTP API routes | [`docs/api/endpoints.md`](../api/endpoints.md) | Submit prompts, poll history, manage queue |
| WebSocket events | [`docs/api/websocket.md`](../api/websocket.md) | Real-time execution progress and completion |
| Server hooks | [`docs/hooks/server-hooks.md`](../hooks/server-hooks.md) | Understand server-side extension points |
| JavaScript hooks | [`docs/hooks/javascript-hooks.md`](../hooks/javascript-hooks.md) | Understand frontend extension points |
| Worked examples | `examples/` | Concrete API calls and extension patterns |

## Standard API vs Extension Routes

- **Standard API** (`/prompt`, `/history`, `/queue`, `/object_info`) requires no
  server modifications and is documented in this repo's API reference. Use this
  for remote automation.
- **Extension routes** (`/api/etn/...` or custom routes) require a corresponding
  extension installed inside ComfyUI. Use this only when you need runtime state
  the standard API does not expose.

If you are unsure which you need, start with the standard API and move to
extension routes only after confirming the data you need is unavailable.

## Machine-Readable vs Prose-Only Artifacts

- **Machine-readable:** JSON files under `references/raw/`, snapshot files under
  `references/snapshots/`, code in `examples/`, and API endpoint documentation.
- **Prose-only:** decision guides, tutorials, deep dives, and community pattern
  studies. These explain intent and tradeoffs but are not structured for parsing.

Build tooling against machine-readable artifacts. Use prose pages for context
and design decisions.

## First Practical Step

Retrieve the `object_info` data from your ComfyUI instance. Parse one node's
`input` and `output` definitions from the response and print them. This
confirms the node metadata artifact is accessible and parseable.

## Read Next

- [API Endpoints](../api/endpoints.md)
- [Object Info](../reference/object-info.md)
- [WebSocket Events](../api/websocket.md)
- [Decision Tree: API Integration](../decision-trees/api-integration.md)
