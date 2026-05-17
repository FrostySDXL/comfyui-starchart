# Artifacts Plus Live API Example

**Status:** Starter pattern

## What This Example Shows

This directory shows a two-phase hybrid consumer flow:

1. read `artifacts/manifest.json`
2. resolve `server_endpoints.json`
3. confirm that a standard zero-parameter `GET` route such as `/queue` exists in the pinned artifact baseline
4. optionally call that route against a live ComfyUI runtime and print the live JSON response

## Files

- `discover_and_probe_queue.sh` - artifact-first route discovery followed by an optional live `GET /queue` probe

## Prerequisites

- `curl`
- `jq`
- a published docs/artifacts base URL
- optionally, a live ComfyUI runtime URL such as `http://127.0.0.1:8188`

## What This Proves

- artifacts are enough to discover whether a standard route belongs to the pinned baseline
- a consumer can keep discovery and live interaction as separate phases
- the runtime portion can stay optional without making the artifact-only phase misleading

## What This Intentionally Leaves Out

- it does not submit prompts or claim that artifact metadata fully describes `POST /prompt` request semantics
- it does not treat `/api/...` aliases as the canonical route surface
- it does not prove anything about queue contents, runtime reachability, or extension-added routes until the live call actually succeeds

This example uses a simple `GET /queue` probe because it keeps the runtime step
honest and bounded. Artifact metadata can show that the route exists in the
pinned baseline, but only a live runtime can answer what the queue looks like
right now.

## Usage

Artifact discovery only:

```bash
bash examples/consumers/artifacts-plus-live-api/discover_and_probe_queue.sh https://example.com/comfyui-knowledge-base
```

Artifact discovery plus live runtime probe:

```bash
bash examples/consumers/artifacts-plus-live-api/discover_and_probe_queue.sh https://example.com/comfyui-knowledge-base http://127.0.0.1:8188
```

If you omit the runtime URL or the runtime is unreachable, the script stops after
the artifact phase and prints a clear note about the skipped live step.

For the contract boundaries this example assumes, read
[`src/content/docs/reference/machine-readable-artifacts.md`](../../../src/content/docs/reference/machine-readable-artifacts.md),
[`src/content/docs/start-here/tooling-builder.md`](../../../src/content/docs/start-here/tooling-builder.md),
and [`src/content/docs/how-to/consumer-starter-examples.md`](../../../src/content/docs/how-to/consumer-starter-examples.md).
