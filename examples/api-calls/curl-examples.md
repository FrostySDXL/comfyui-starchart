# Native ComfyUI API Call Examples

**Primary Source:** `references/snapshots/2026-06-26/comfyui-core-v0.26.0/server.py` (v0.26.0, commit `f6c162ddcfbd7eefb39c06fe5b8d4c46e8d09f40`)

These examples target native ComfyUI routes, not wrapper APIs.

## Submit a prompt

```bash
curl -X POST http://127.0.0.1:8188/prompt \
  -H "Content-Type: application/json" \
  --data @examples/api-calls/post-prompt.json
```

Expected success shape from the current pinned `server.py`:

```json
{
  "prompt_id": "<uuid-or-supplied-id>",
  "number": 0,
  "node_errors": {}
}
```

## Inspect queue state

```bash
curl http://127.0.0.1:8188/queue
```

The current pinned route returns:

- `queue_running`
- `queue_pending`

## Look up prompt history

```bash
curl http://127.0.0.1:8188/history/<prompt_id>
```

Use this after execution when you need the stored run record for a specific
prompt.

## Open a WebSocket session

```text
ws://127.0.0.1:8188/ws?clientId=<your-client-id>
```

The current pinned `server.py` sends an initial `status` event and can later send
execution-related messages tied to the same `client_id` used in `POST /prompt`.

## Notes

- `/api/...` prefixed copies also exist in the current pinned server setup
- exact message/event shapes are pinned to the repo's currently extracted
  upstream commit and may drift in future refreshes
