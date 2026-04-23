# API to Workflow: Prompt Lifecycle

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-04-22
**Primary Sources:**
- `references/snapshots/2026-04-19/comfyui-core-v0.19.3/server.py` (v0.19.3, commit 308602640)
- `references/snapshots/2026-04-19/comfyui-core-v0.19.3/execution.py` (v0.19.3, commit 308602640)
- https://docs.comfy.org/development/comfyui-server/comms_routes

## Who This Page Is For

You are integrating ComfyUI into an external service or building an API
client and need to understand how a prompt moves from an HTTP submission
through to queued execution.

## Scope

This tutorial traces the complete prompt lifecycle: from `POST /prompt`
submission, through validation, queue insertion, and `prompt_id` response,
to how clients track progress and retrieve results via history lookup.

## Step 1: Submit the Prompt

`POST /prompt` is the entrypoint for executing a workflow. The request
body is a JSON object with at minimum a `prompt` graph:

```json
{
  "prompt": {
    "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "model.safetensors"}},
    "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "a photo of an object", "clip": ["1", 1]}}
  },
  "client_id": "my-session-id",
  "extra_data": {}
}
```

The `prompt` value is a dictionary keyed by node ID. Each node entry
has a `class_type` that names the node class and an `inputs` dictionary
that provides argument values.

## Step 2: Server-Side Validation

Before anything is queued, `server.py` calls `execution.validate_prompt`.
The validation checks in `execution.py` confirm that:

- every node in the graph has a valid `class_type`
- each input link references an existing node and output slot
- linked output types match expected input types
- required inputs are present
- literal values fall within `min`/`max` bounds for the target widget
- combo and list values are part of the allowed options

If validation fails, the server returns HTTP 400 with an `error` object
and a `node_errors` structure that identifies which nodes failed.

## Step 3: Queue Insertion

On validation success, the handler:

1. Applies any node replacements via `node_replace_manager`
2. Adds `client_id` to `extra_data`
3. Removes sensitive keys listed in `SENSITIVE_EXTRA_DATA_KEYS` from the
   public extra_data before it is stored
4. Stamps `extra_data["create_time"]` with the current timestamp in
   milliseconds
5. Enqueues a tuple containing: queue number, prompt ID, prompt payload,
   filtered extra_data, outputs to execute, and a separate sensitive
   data bundle

Queue order is controlled by the optional `number` field. If `front: true`
is set without an explicit number, the generated number is negated so the
job runs earlier than others.

## Step 4: The `prompt_id` Response

On success, `POST /prompt` returns:

```json
{
  "prompt_id": "<prompt_id>",
  "number": 12,
  "node_errors": {}
}
```

The returned `prompt_id` is the key for all subsequent tracking calls.
Record it immediately after a successful submission.

## Step 5: Track Progress

After submission, there are two complementary tracking paths:

**WebSocket path** -- connect to `GET /ws` with the same `client_id`
used during submission. The socket delivers live execution events:
`execution_start`, `executing`, `executed`, `execution_success`, or
`execution_error`. See [API to Workflow: Execution Events](api-to-workflow-execution-events.md)
for the full event sequence.

**HTTP polling path** -- use `GET /queue` to check whether the prompt
is still running or pending:

```json
{
  "queue_running": [
    [
      12,
      "<prompt_id>",
      {
        "3": {
          "class_type": "KSampler",
          "inputs": {}
        }
      },
      {
        "client_id": "my-session-id",
        "create_time": 1713520000000
      },
      ["3"]
    ]
  ],
  "queue_pending": []
}
```

`GET /queue` returns sanitized queue tuples, not object summaries. In the
current source the five visible positions are `number`, `prompt_id`, `prompt`,
`extra_data`, and `outputs_to_execute`.

## Step 6: Retrieve Results

Once the prompt is no longer in the queue, call
`GET /history/{prompt_id}` to retrieve stored outputs and metadata:

```json
{
  "<prompt_id>": {
    "outputs": {
      "2": {"ui": {"images": [{"filename": "output.png", ...}]}}
    },
    "meta": {"nodes": {"2": {"class_type": "CLIPTextEncode", ...}}}
  }
}
```

History is keyed by `prompt_id`. The `outputs` dictionary is keyed by
node ID. UI-facing outputs (images, text) are under the `ui` sub-key.

## Complete Request-Response Sequence

```
Client                        ComfyUI Server
  |                                   |
  |-------- POST /prompt ------------>|
  |     {prompt, client_id, ...}      |-- validate_prompt()
  |                                   |-- apply node replacements
  |                                   |-- enqueue prompt
  |<------- {prompt_id, number} -----|  HTTP 200
  |                                   |
  |========== GET /ws ===============>|
  |     (WebSocket open)              |
  |                                   |
  |     [execution_start event]       |
  |     [executing event per node]    |
  |     [executed event per node]     |
  |     [execution_success event]     |
  |                                   |
  |<======== GET /history/{id} =======|
  |     {outputs, meta}               |
```

## Common Pitfalls

- Forgetting to record `prompt_id` immediately after `POST /prompt` --
  it is required for all subsequent tracking calls
- Using `client_id` inconsistently between submission and WebSocket
  connection -- events target the specific `client_id` attached to the
  prompt
- Assuming history is permanent -- it is tied to the prompt queue/history
  machinery and is cleared by `POST /history` with `clear: true` or
  when ComfyUI restarts
- Submitting a graph with invalid `class_type` values -- validation
  catches this, but only if the node is registered in `NODE_CLASS_MAPPINGS`

## Read Next

- [API to Workflow: Execution Events](api-to-workflow-execution-events.md)
- [Prompt Submission](../api/prompt-submission.md)
- [WebSocket](../api/websocket.md)
