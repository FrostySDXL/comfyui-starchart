# Python Artifact Delta Reader Example

**Status:** Starter pattern

## What This Example Shows

This directory shows a small Python consumer flow for the published support
artifact `artifacts/delta-summary.json`:

1. download the delta summary directly from the published site
2. print the compared old/new version keys
3. print a compact changed-count summary for each artifact family

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

```bash
py -3.11 examples/consumers/python-artifact-delta-reader/read_delta_summary.py https://example.com/comfyui-knowledge-base
```

For the contract boundaries this example assumes, read
[`src/content/docs/reference/machine-readable-artifacts.md`](../../../src/content/docs/reference/machine-readable-artifacts.md).
