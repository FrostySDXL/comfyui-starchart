# Example 3: Node Communicating with Other Nodes

**Status:** Pattern example
**Level:** Intermediate -- builds on example-1 and example-2

## What This Example Is

A V1 node that processes a batch of images sequentially, then outputs results
to two downstream nodes. Demonstrates batch input handling, multi-output
patterns, and how to structure a node that is meant to be part of a processing
chain rather than a terminal node.

This is the bridge between a self-contained processing node and a node that
is designed to participate in a multi-node pipeline.

## Files

- `image_chunker_node.py` -- splits a batch into individual images, applies a
  processing operation, and returns multiple outputs for downstream nodes

## What to Study

- How batch size flows through INPUT_TYPES and RETURN_TYPES
- Multi-output patterns (IMAGE, MASK)
- How to design a node that feeds two downstream nodes
- Using `PromptServer.instance.send_sync` to emit events during processing

## Key Patterns

### Batch Processing Loop

```python
def process_batch(self, images):
    batch_size = images.shape[0]
    results = []
    for i in range(batch_size):
        single_image = images[i].unsqueeze(0)  # restore batch dim
        processed = self.process_single(single_image)
        results.append(processed)
    return torch.cat(results, dim=0)
```

### Multi-Output Return

```python
RETURN_TYPES = ("IMAGE", "MASK", "STRING")
RETURN_NAMES = ("processed_images", "batch_mask", "summary")
# IMAGE: processed batch of frames
# MASK: max-intensity mask across the batch (thresholded)
# STRING: summary log line describing the operation
```

### Event Emission During Processing

```python
PromptServer.instance.send_sync(
    "example.chunker.progress",
    {"index": i + 1, "total": batch_size, "operation": operation},
)
```

The payload does not include a node ID; the event name carries the context
(`example.chunker.progress`). A paired frontend extension can listen for
this event and display a progress bar in the node's UI while processing runs.

## Evidence Level

- Batch tensor shapes: upstream source behavior (ComfyUI tensor conventions)
- Multi-output nodes: documented pattern in ComfyUI source
- PromptServer.send_sync: source-backed reference from ComfyUI server.py (pinned snapshot)
