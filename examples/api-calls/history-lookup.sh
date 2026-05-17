#!/usr/bin/env bash
# Retrieve prompt history by ID
# Usage: PROMPT_ID=<id> COMFYUI_URL=http://127.0.0.1:8188 bash history-lookup.sh
set -euo pipefail
COMFYUI_URL="${COMFYUI_URL:-http://127.0.0.1:8188}"
PROMPT_ID="${PROMPT_ID:?Set PROMPT_ID to the prompt ID to look up}"
curl -s "${COMFYUI_URL}/history/${PROMPT_ID}" | python -m json.tool
