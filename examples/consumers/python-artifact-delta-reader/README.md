# Python Artifact Delta Reader Example

**Status:** Starter pattern
**Validation tiers:** static, offline unit-tested

## What This Example Shows

This directory shows a small Python consumer flow for the published support
artifact `artifacts/delta-summary.json`:

1. load the delta summary from a published site URL, direct JSON URL,
   `file://` URL, or local JSON path
2. print the current `comparison` metadata
3. print compact counts for each top-level or nested artifact section

## Files

- `read_delta_summary.py` - fetches `artifacts/delta-summary.json` and prints a
  compact baseline-to-baseline summary

## What This Proves

- consumers can use the published delta summary without scraping docs pages
- support artifacts can be useful even when they are outside the canonical
  manifest contract
- a consumer can keep delta inspection lightweight and read-only

## What This Does Not Prove

- it does not validate the canonical artifact checksums
- it does not treat `delta-summary.json` as a manifest-discovered canonical
  artifact
- it does not prove anything about a live ComfyUI runtime

## Usage

Published site base URL:

```bash
py -3.11 examples/consumers/python-artifact-delta-reader/read_delta_summary.py https://frostysdxl.github.io/comfyui-starchart
```

Local offline artifact:

```bash
py -3.11 examples/consumers/python-artifact-delta-reader/read_delta_summary.py public/artifacts/delta-summary.json
```

Direct `file://` URL:

```bash
py -3.11 examples/consumers/python-artifact-delta-reader/read_delta_summary.py file:///path/to/delta-summary.json
```

For the contract boundaries this example assumes, read
[`src/content/docs/reference/machine-readable-artifacts.md`](../../../src/content/docs/reference/machine-readable-artifacts.md).
