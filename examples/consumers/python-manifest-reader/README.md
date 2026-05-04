# Python Manifest Reader Example

**Status:** Starter pattern

## What This Example Shows

This directory shows a small, bounded artifact-consumption flow for Python
tools:

1. load `artifacts/manifest.json`
2. resolve a canonical artifact URL from the manifest
3. validate the downloaded bytes against the manifest `sha256`
4. read one canonical artifact without depending on best-effort-only fields

## Files

- `read_manifest.py` - prints the manifest entry for a chosen canonical artifact
- `validate_artifact.py` - downloads one canonical artifact, validates its
  checksum, and prints a small guaranteed-field summary

## What This Proves

- consumers can start from the published manifest instead of hardcoding a
  versioned artifact path
- consumers can verify canonical current-copy integrity before using the file
- consumers can keep strict logic on guaranteed structure while ignoring
  descriptive best-effort fields

## What This Does Not Prove

- it is not an SDK or installable client library
- it does not cover runtime-only artifacts or live ComfyUI behavior
- it does not validate every field in every artifact

## Usage

```bash
py -3.11 examples/consumers/python-manifest-reader/read_manifest.py https://example.com/comfyui-knowledge-base server_endpoints.json
py -3.11 examples/consumers/python-manifest-reader/validate_artifact.py https://example.com/comfyui-knowledge-base server_endpoints.json
```

The intended path is an HTTP(S) published site URL. If you point the validator at
a repo-local `file://` checkout on Windows, it normalizes JSON newlines before
hashing so the local text checkout can still be compared to the manifest's
published checksum.

Use one of these canonical artifact keys:

- `server_endpoints.json`
- `js_hooks.json`
- `node_api_schema.json`

For the contract and support-artifact boundaries this example assumes, read
[`docs/reference/machine-readable-artifacts.md`](../../../docs/reference/machine-readable-artifacts.md).
