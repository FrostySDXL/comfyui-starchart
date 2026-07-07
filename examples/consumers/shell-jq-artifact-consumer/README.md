# Shell + jq Artifact Consumer Example

**Status:** Starter pattern

## What This Example Shows

This directory shows a small shell-side artifact discovery flow:

1. load `artifacts/manifest.json`
2. resolve `server_endpoints.json` from the manifest
3. list endpoint method and route pairs with `jq`
4. optionally probe one zero-parameter `GET` route when a live ComfyUI runtime is available

## Files

- `list_endpoints.sh` - fetches the manifest, resolves the published endpoint artifact, lists routes, and optionally probes one live `GET` endpoint

## Prerequisites

- `curl`
- `jq`
- a published documentation site base URL such as `https://frostysdxl.github.io/comfyui-starchart`

## What This Proves

- shell tooling can start from `manifest.json` instead of hardcoding artifact URLs
- `jq` is sufficient for bounded endpoint discovery against the published artifact
- the live-runtime step is optional and clearly separate from artifact discovery

## What This Does Not Prove

- it is not an SDK or supported client library
- it does not promote `/api` aliases into a canonical machine-readable route surface
- it does not turn best-effort endpoint metadata into a full runtime truth layer
- it does not prove that a runtime is reachable unless you supply a live runtime URL

## Usage

Artifact-only:

```bash
bash examples/consumers/shell-jq-artifact-consumer/list_endpoints.sh https://frostysdxl.github.io/comfyui-starchart
```

Artifact discovery plus optional live probe:

```bash
bash examples/consumers/shell-jq-artifact-consumer/list_endpoints.sh https://frostysdxl.github.io/comfyui-starchart http://127.0.0.1:8188
```

If you omit the runtime URL, the script completes after artifact discovery and
prints a note that the runtime probe was skipped.

For the contract boundaries this example assumes, read
[`src/content/docs/reference/machine-readable-artifacts.md`](../../../src/content/docs/reference/machine-readable-artifacts.md)
and the overview page
[`src/content/docs/start-here/artifact-consumer.md`](../../../src/content/docs/start-here/artifact-consumer.md).
