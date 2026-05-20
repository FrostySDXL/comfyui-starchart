# Prompt Submit, Monitor, and History Example

**Status:** Starter pattern

## What This Example Shows

This directory shows a bounded runtime-dependent consumer flow:

1. read the artifact-routing guidance first
2. submit a workflow to `POST /prompt`
3. connect to `GET /ws`
4. print a small subset of execution-related messages
5. fetch `GET /history/{prompt_id}` after completion or timeout

## Files

- `submit_and_monitor.py` - submits one workflow, watches a bounded WebSocket message set, then looks up history for the returned `prompt_id`
- `workflow.example.json` - sample API-format workflow input that users will likely need to adapt to their own runtime

## Prerequisites

- Python 3.11+
- `websocket-client` installed from `requirements.lock`
- a live ComfyUI runtime URL such as `http://127.0.0.1:8188`
- a workflow JSON file that matches the target runtime's installed nodes, model names, and expected node IDs

## What This Proves

- a consumer can keep artifact guidance, prompt submission, live monitoring, and history lookup in one small script
- `prompt_id` is the stable handoff between submission, live monitoring, and post-run history lookup
- WebSocket monitoring and history lookup are complementary rather than interchangeable

## What This Does Not Prove

- it is not a supported SDK or reusable client library
- it does not claim that pinned artifacts fully encode every `POST /prompt` mutation rule
- it does not guarantee the bundled sample workflow will run unchanged on every ComfyUI instance

## Runtime Boundary

This example depends on a live runtime and an explicit Python WebSocket client
dependency. It is intentionally more operational than the artifact-only starter
patterns in this repo.

If the sample workflow does not match your runtime, replace node IDs, model
names, or the entire workflow payload before treating the script as a success
probe.

## Usage

```bash
py -3.11 examples/consumers/prompt-submit-monitor-history/submit_and_monitor.py --url http://127.0.0.1:8188 --workflow examples/consumers/prompt-submit-monitor-history/workflow.example.json
```

Optional flags:

- `--client-id` - set a stable client ID instead of an auto-generated one
- `--timeout-seconds` - stop waiting after a bounded interval and still try history lookup

For the contract and support-artifact boundaries this example assumes, read
[`src/content/docs/reference/machine-readable-artifacts.md`](../../../src/content/docs/reference/machine-readable-artifacts.md),
[`src/content/docs/start-here/tooling-builder.md`](../../../src/content/docs/start-here/tooling-builder.md),
and [`src/content/docs/how-to/consumer-starter-examples.md`](../../../src/content/docs/how-to/consumer-starter-examples.md).
