#!/usr/bin/env bash
# Poll the ComfyUI queue status
# Usage: COMFYUI_URL=http://127.0.0.1:8188 bash queue-status.sh
set -euo pipefail
COMFYUI_URL="${COMFYUI_URL:-http://127.0.0.1:8188}"
curl -s "${COMFYUI_URL}/queue" | python -m json.tool
