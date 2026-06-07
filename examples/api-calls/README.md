# Examples: API Calls

**Status:** Source-backed examples
**Primary Sources:** `references/snapshots/2026-06-03/comfyui-core-v0.23.0/server.py` (v0.23.0, commit `a88e02b18576283b1ff25a4b564548c5dc42cbf6`), https://docs.comfy.org/
**Validation tiers:** static, pinned-source, opt-in runtime smoke

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

`post-prompt.json` is an API-format prompt graph for `POST /prompt`, not an
editor-exported workflow JSON document. Replace
`YOUR_MODEL_NAME_HERE.safetensors` with a checkpoint filename installed in your
ComfyUI runtime before submitting it.

The checked-in payload uses the fixed placeholder client ID
`00000000-0000-4000-8000-000000000000`. Override it with
`COMFYUI_CLIENT_ID=<uuid>` when running `post-prompt.sh` if you also connect a
WebSocket client for event tracking. Simultaneous submissions that share a
`client_id` can collide on WebSocket event subscription and make event
correlation ambiguous.

The opt-in `.github/workflows/runtime-smoke.yml` can validate `POST /prompt`
using `post-prompt.json` against a live ComfyUI instance. This is not part of
CPU-safe CI and must be triggered manually with a known ComfyUI URL.

For examples-only runtime validation, use:

```bash
python scripts/verify/example_runtime_smoke.py --url http://127.0.0.1:8188 --comfyui-root D:/projects/comfyui-test-runtime --model-name <installed-checkpoint.safetensors>
```

## Artifact Connection

The route shapes in these examples align with the pinned endpoint metadata in
`server_endpoints.json`. See [Machine-Readable Artifacts](../../src/content/docs/reference/machine-readable-artifacts.md)
for the published artifact and manifest URLs.
