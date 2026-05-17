# Examples: API Calls

**Status:** Source-backed examples
**Primary Sources:** https://github.com/Comfy-Org/ComfyUI/blob/master/server.py, https://docs.comfy.org/

## What This Directory Contains

These examples are derived from current upstream ComfyUI route behavior and are
meant as practical starter calls for tools that talk to native ComfyUI.

## Included Examples

- `post-prompt.json` - request body structure for `POST /prompt`
- `post-prompt.sh` - runnable shell script that submits `post-prompt.json`
- `queue-status.sh` - polls `GET /queue` with formatted JSON output
- `history-lookup.sh` - retrieves `GET /history/{prompt_id}` for a given prompt
- `curl-examples.md` - narrative walkthrough of prompt submission, queue polling,
  history lookup, and websocket connection examples

## Evidence Level

- upstream source behavior: current `server.py` route implementations
- official behavior: official docs where available
- community wrappers: excluded from these examples on purpose

## Runtime Validation

The opt-in `.github/workflows/runtime-smoke.yml` can validate `POST /prompt`
using `post-prompt.json` against a live ComfyUI instance. This is not part of
CPU-safe CI and must be triggered manually with a known ComfyUI URL.

## Artifact Connection

The route shapes in these examples align with the pinned endpoint metadata in
`server_endpoints.json`. See [Machine-Readable Artifacts](../../src/content/docs/reference/machine-readable-artifacts.md)
for the published artifact and manifest URLs.
