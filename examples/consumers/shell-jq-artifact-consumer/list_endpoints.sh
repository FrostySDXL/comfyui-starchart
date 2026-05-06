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

echo "Loading manifest: $manifest_url" >&2
manifest_json="$(curl -fsSL "$manifest_url")"

artifact_path="$(printf '%s' "$manifest_json" | jq -r '.artifacts["server_endpoints.json"].current_url // empty')"
if [[ -z "$artifact_path" ]]; then
  echo "Manifest does not expose server_endpoints.json" >&2
  exit 1
fi

artifact_url="$docs_base/$artifact_path"
echo "Loading endpoint artifact: $artifact_url" >&2
endpoints_json="$(curl -fsSL "$artifact_url")"

echo "Discovered endpoints:" 
printf '%s' "$endpoints_json" | jq -r '.endpoints[] | "\(.method) \(.route)"'

preferred_route="$(printf '%s' "$endpoints_json" | jq -r '
  [
    .endpoints[]
    | select(.method == "GET")
    | select((.parameters // []) | all(.location != "path"))
    | .route
  ]
  | map(select(. == "/queue" or . == "/history" or . == "/system_stats"))
  | .[0] // empty
')"

if [[ -z "$runtime_base" ]]; then
  echo "Runtime probe skipped: no runtime base URL supplied." >&2
  exit 0
fi

if [[ -z "$preferred_route" ]]; then
  echo "Runtime probe skipped: no preferred zero-parameter GET route was found in server_endpoints.json." >&2
  exit 0
fi

runtime_base="${runtime_base%/}"
runtime_url="$runtime_base$preferred_route"
echo "Probing live runtime endpoint: $runtime_url" >&2

if ! response_json="$(curl -fsSL "$runtime_url")"; then
  echo "Runtime probe skipped: artifact discovery succeeded, but the live runtime endpoint did not return a successful response." >&2
  exit 0
fi

echo "Live runtime response for $preferred_route:" 
printf '%s' "$response_json" | jq .
