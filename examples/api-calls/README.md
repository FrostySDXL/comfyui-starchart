# Examples: API Calls

**Status:** Source-backed examples
**Primary Sources:** https://github.com/Comfy-Org/ComfyUI/blob/master/server.py, https://docs.comfy.org/

## What This Directory Contains

These examples are derived from current upstream ComfyUI route behavior and are
meant as practical starter calls for tools that talk to native ComfyUI.

## Included Examples

- `post-prompt.json` - request body structure for `POST /prompt`
- `curl-examples.md` - prompt submission, queue polling, history lookup, and
  websocket connection examples

## Evidence Level

- upstream source behavior: current `server.py` route implementations
- official behavior: official docs where available
- community wrappers: excluded from these examples on purpose

## Runtime Validation

The opt-in `.github/workflows/runtime-smoke.yml` can validate `POST /prompt`
using `post-prompt.json` against a live ComfyUI instance. This is not part of
CPU-safe CI and must be triggered manually with a known ComfyUI URL.
