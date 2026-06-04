# Native ComfyUI API Call Examples

**Primary Source:** `references/snapshots/2026-06-03/comfyui-core-v0.23.0/server.py` (v0.23.0, commit `a88e02b18576283b1ff25a4b564548c5dc42cbf6`)

These examples target native ComfyUI routes, not wrapper APIs.

## Submit a prompt

```bash
curl -X POST http://127.0.0.1:8188/prompt \
  -H "Content-Type: application/json" \
  --data @examples/api-calls/post-prompt.json
```

Expected success shape from current upstream `server.py`:

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

Current upstream route returns:

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

Current upstream `server.py` sends an initial `status` event and can later send
execution-related messages tied to the same `client_id` used in `POST /prompt`.

## Notes

- `/api/...` prefixed copies also exist in current upstream server setup
- exact message/event shapes are pinned to the repo's currently extracted
  upstream commit and may drift in future refreshes
