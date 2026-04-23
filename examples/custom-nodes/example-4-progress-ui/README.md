# Example 4: Node with Progress UI

**Status:** Pattern example
**Level:** Intermediate -- builds on example-1, example-2, and example-3

## What This Example Is

A V1 custom node that emits custom server-side progress events during
execution, paired with a frontend JavaScript extension that listens for
those events and renders visible progress feedback in the ComfyUI editor.

This is the bridge between backend-only examples (example-1 through example-3)
and a full extension package (example-5). It demonstrates connected
client/server behavior without the full packaging burden of a complete
Manager-ready distribution.

## Why This Pattern Matters

Long-running nodes can freeze the ComfyUI interface if they do not yield
control. By emitting progress events, the node keeps the frontend informed
about how much work remains. The frontend extension receives those events
and updates the UI, so users see feedback instead of a frozen interface.

## Files

- `progress_emitter_node.py` -- V1 node that emits a custom progress event
- `web/js/progress-panel.js` -- frontend extension that listens and displays
- `__init__.py` -- package entry point exposing NODE_CLASS_MAPPINGS,
  NODE_DISPLAY_NAME_MAPPINGS, and WEB_DIRECTORY

## What to Study

- How to emit a custom server-side event using `PromptServer.instance.send_sync`
- Why the event name "my-progress" is an example name and not an official
  ComfyUI event
- How a frontend extension registers a listener for a custom event name
- How the frontend accesses event payload fields (`node_id`, `progress`, `stage`)
- How a node-scoped progress panel can use hidden `UNIQUE_ID` input data to
  keep feedback tied to the node that emitted the event
- Limitations of this pattern: it only works in the ComfyUI editor, not
  in API mode

## Custom Backend Event Emission

The node emits a custom event during each processing iteration:

```python
PromptServer.instance.send_sync(
    "my-progress",  # EXAMPLE name -- NOT an official ComfyUI event
    {
        "node_id": node_id,
        "progress": (i + 1) / total,
        "stage": f"iteration {i + 1} of {total}",
    },
)
```

The event name `"my-progress"` is chosen to illustrate the custom event
pattern. It is NOT an official ComfyUI event. Official ComfyUI events
(such as `executing`, `executed`, `progress`) are defined in the ComfyUI
server source and documented at docs.comfy.org. Custom event names will
only be recognized if a frontend extension is registered that listens for
them.

This example also uses the hidden `UNIQUE_ID` input pattern to include the
runtime node ID in each custom event payload. That keeps the frontend display
scoped to the node that emitted the update instead of treating all progress as
one global stream.

## Frontend Event Listening

The frontend extension registers a listener for the custom event name:

```javascript
app.registerExtension({
  name: "example.progress",
  setup() {
    app.api.addEventListener("my-progress", messageHandler);
  },
});
```

When the event fires, the handler creates or updates a fixed-position
progress panel for that specific `node_id` in the bottom-right corner of the
editor.

## API Mode Incompatibility

This pattern requires the ComfyUI editor frontend to be running. In API
mode (direct HTTP API calls without the editor), there is no frontend
extension system to receive the events. Nodes that rely on frontend event
listeners will still execute, but the progress feedback will not appear.

If you need progress reporting in API mode, use `GET /queue` during
execution to observe queued prompt status, and `GET /history/{prompt_id}`
after execution completes. Official WebSocket `progress` events are available
during execution but require a connected client to receive them.

## How It Builds on Example-3

Example-3 shows how to emit an event from a batch-processing node using
`PromptServer.instance.send_sync`. Example-4 extends this by:

1. Adding a configurable delay to simulate work per iteration
2. Emitting more granular progress data (stage name, percentage)
3. Including a complete frontend extension that renders visible feedback
4. Packaging both sides (Python + JavaScript) in a single example

## Evidence Level

- V1 node patterns: upstream source behavior (ComfyUI)
- PromptServer.send_sync: source-backed reference from ComfyUI server.py (pinned snapshot)
- Custom event names: this example uses an example name, not an official one
- Frontend extension registration: documented at docs.comfy.org
