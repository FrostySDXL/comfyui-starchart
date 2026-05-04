 # API Integration Troubleshooting

 **Evidence:** Official docs-backed from docs.comfy.org and source-backed from pinned snapshots
 **Last Updated:** 2026-05-03

 ## Scope

 This page covers bounded integration confusion that already appears in the API,
 start-here, and known-limitations docs. It routes you to the right surface
 instead of restating the full API reference.

 ## Problem: I am not sure whether I need the standard API or an extension route

 Start with the standard API when built-in routes such as `/prompt`, `/history`,
 `/queue`, or `/object_info` already expose the data you need. Move to
 extension-owned routes only when you need behavior or state that the standard
 API does not publish.

 Read next:

 - [API Endpoints](../api/endpoints.md)
 - [Add Custom Routes](../how-to/add-custom-routes.md)
 - [Start Here: Tooling Builder](../start-here/tooling-builder.md)

 ## Problem: I expected frontend features to work in API mode

 API mode is an HTTP and WebSocket integration surface. It does not load the
 ComfyUI editor or frontend extension registration path, so frontend-only node
 behavior and custom UI features do not carry over automatically.

 Read next:

 - [Known Limitations](../known-limitations/index.md)
 - [Start Here: Service Integration](../start-here/service-integration.md)
 - [JavaScript Hooks](../hooks/javascript-hooks.md)

## Problem: I expected the WebSocket to replace every other status lookup

 The WebSocket is the main progress stream, but it is not a complete substitute
 for queue and history endpoints. Use WebSocket events for live execution state,
 `GET /queue` for queue lists, and `GET /history/{prompt_id}` for stored output
 details after execution completes.

 Read next:

- [WebSocket](../api/websocket.md)
- [History and Queue](../api/history-queue.md)
- [Prompt Submission](../api/prompt-submission.md)

## Problem: I expected runtime `/object_info` to match the repo's canonical published artifacts

The live `/object_info` route reflects the node state of the ComfyUI instance
you are talking to. The repo's canonical published artifact contract is smaller
and intentionally pinned. Use published artifacts for stable baseline tooling,
and add runtime `object_info` only when you need installed custom-node state.

Read next:

- [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md)
- [Start Here: Tooling Builder](../start-here/tooling-builder.md)
- [Known Limitations](../known-limitations/index.md)
