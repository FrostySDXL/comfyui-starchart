# JavaScript Docs and Artifacts Example

**Status:** Starter pattern

## What This Example Shows

This directory shows a small JavaScript-side discovery flow:

1. load `artifacts/docs-index.json` as an optional docs-routing aid
2. locate a likely docs page for a tooling consumer task
3. load `artifacts/manifest.json` separately for canonical structured artifact
   access

## Files

- `load_docs_index.mjs` - reads the optional docs index and prints a small list
  of relevant published docs pages
- `load_manifest.mjs` - reads the canonical manifest and prints one artifact
  entry plus its published URLs

## What This Proves

- JavaScript tooling can use `docs-index.json` for bounded page discovery without
  treating it as a canonical artifact contract
- structured artifact access still starts from `manifest.json`
- consumer code can keep docs discovery and artifact consumption as separate
  concerns

## What This Does Not Prove

- it is not a supported library or package
- it does not replace reading the docs pages it discovers
- it does not promote `docs-index.json` into a new source of truth layer

## Usage

```bash
node examples/consumers/javascript-docs-and-artifacts/load_docs_index.mjs https://example.com/comfyui-knowledge-base tooling
node examples/consumers/javascript-docs-and-artifacts/load_manifest.mjs https://example.com/comfyui-knowledge-base js_hooks.json
```

The scripts also work against a repo-local built site or docs directory through a
`file://` base URL.

For the contract and support-artifact boundaries this example assumes, read
[`docs/reference/machine-readable-artifacts.md`](../../../docs/reference/machine-readable-artifacts.md).
