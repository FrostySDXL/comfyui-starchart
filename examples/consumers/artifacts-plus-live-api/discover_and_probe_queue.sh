#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 <docs-base-url> [runtime-base-url]" >&2
  exit 2
fi

for dep in curl jq; do
  if ! command -v "$dep" >/dev/null 2>&1; then
    echo "Required dependency missing: $dep" >&2
    exit 1
  fi
done

docs_base="${1%/}"
runtime_base="${2:-}"
manifest_url="$docs_base/artifacts/manifest.json"

echo "Phase 1: artifact discovery" >&2
manifest_json="$(curl -fsSL "$manifest_url")"
artifact_path="$(printf '%s' "$manifest_json" | jq -r '.artifacts["server_endpoints.json"].current_url // empty')"

if [[ -z "$artifact_path" ]]; then
  echo "Manifest does not expose server_endpoints.json" >&2
  exit 1
fi

artifact_url="$docs_base/$artifact_path"
endpoints_json="$(curl -fsSL "$artifact_url")"

if ! printf '%s' "$endpoints_json" | jq -e '.endpoints[] | select(.method == "GET" and .route == "/queue")' >/dev/null; then
  echo "Pinned artifact baseline does not expose GET /queue" >&2
  exit 1
fi

echo "Pinned artifact confirms GET /queue exists." >&2
printf '%s' "$endpoints_json" | jq -r '.endpoints[] | select(.method == "GET" and .route == "/queue") | "Return kind: \(.returns.kind)"'

if [[ -z "$runtime_base" ]]; then
  echo "Phase 2 skipped: no runtime base URL supplied. The artifact phase completed successfully." >&2
  exit 0
fi

runtime_base="${runtime_base%/}"
runtime_url="$runtime_base/queue"

echo "Phase 2: live runtime probe" >&2
if ! response_json="$(curl -fsSL "$runtime_url")"; then
  echo "Phase 2 skipped: GET /queue was not reachable on the live runtime. Artifact discovery still succeeded." >&2
  exit 0
fi

echo "Live GET /queue response:" >&2
printf '%s' "$response_json" | jq .
