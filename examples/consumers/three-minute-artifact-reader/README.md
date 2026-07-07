# Three-Minute Artifact Reader Example

**Status:** Starter pattern

## What This Example Shows

This directory gives a no-runtime first success path for ComfyUI StarChart:

1. read the checked-in `public/artifacts/manifest.json`
2. print the pinned artifact baseline and canonical artifact names
3. read `public/artifacts/current/server_endpoints.json`
4. confirm whether key local API routes are present in the pinned baseline

It does not need a live ComfyUI instance, installed model, network request, or
site build.

## Files

- `read_starchart.py` - prints the current pinned baseline, artifact list, and
  route-presence checks from repo-local published artifacts

## Usage

From the repository root:

```bash
python examples/consumers/three-minute-artifact-reader/read_starchart.py
```

Expected output includes the current `version_key`, the four canonical extracted
artifact names, and route checks for `POST /prompt`, `GET /queue`,
`GET /history/{prompt_id}`, and `GET /ws`.

## What This Proves

- consumers can get useful pinned ComfyUI facts without cloning upstream ComfyUI
  source or starting a runtime
- `manifest.json` is the canonical discovery entrypoint for extracted artifacts
- `server_endpoints.json` can answer bounded route-presence questions for the
  pinned baseline

## What This Does Not Prove

- it is not an SDK or supported client library
- it does not validate live runtime reachability
- it does not describe extension-added routes or installed custom nodes
- it does not replace checksum validation for downloaded hosted artifacts

For the hosted artifact contract, read
[`src/content/docs/start-here/artifact-consumer.md`](../../../src/content/docs/start-here/artifact-consumer.md)
and
[`src/content/docs/reference/machine-readable-artifacts.md`](../../../src/content/docs/reference/machine-readable-artifacts.md).
