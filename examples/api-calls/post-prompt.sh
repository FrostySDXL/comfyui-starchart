#!/usr/bin/env bash
# Submit a workflow to ComfyUI via POST /prompt
# Usage: COMFYUI_URL=http://127.0.0.1:8188 bash post-prompt.sh
set -euo pipefail
COMFYUI_URL="${COMFYUI_URL:-http://127.0.0.1:8188}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
curl -s -X POST "${COMFYUI_URL}/prompt" \
  -H "Content-Type: application/json" \
  -d "@${SCRIPT_DIR}/post-prompt.json"
