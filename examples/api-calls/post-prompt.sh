#!/usr/bin/env bash
# Submit a workflow to ComfyUI via POST /prompt
# Usage: COMFYUI_URL=http://127.0.0.1:8188 COMFYUI_CLIENT_ID=<uuid> bash post-prompt.sh
set -euo pipefail
COMFYUI_URL="${COMFYUI_URL:-http://127.0.0.1:8188}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PAYLOAD_PATH="${SCRIPT_DIR}/post-prompt.json"

if [[ -n "${COMFYUI_CLIENT_ID:-}" ]]; then
  TEMP_PAYLOAD="$(mktemp)"
  trap 'rm -f "${TEMP_PAYLOAD}"' EXIT
  POST_PROMPT_PAYLOAD="${PAYLOAD_PATH}" POST_PROMPT_OUTPUT="${TEMP_PAYLOAD}" python - <<'PY'
import json
import os
from pathlib import Path

payload_path = Path(os.environ["POST_PROMPT_PAYLOAD"])
output_path = Path(os.environ["POST_PROMPT_OUTPUT"])
payload = json.loads(payload_path.read_text(encoding="utf-8"))
payload["client_id"] = os.environ["COMFYUI_CLIENT_ID"]
output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
  PAYLOAD_PATH="${TEMP_PAYLOAD}"
fi

curl -s -X POST "${COMFYUI_URL}/prompt" \
  -H "Content-Type: application/json" \
  -d "@${PAYLOAD_PATH}"
