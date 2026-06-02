import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from scripts.common.display_path import display_path
from scripts.common.path_normalization import normalize_repo_relative_path
from scripts.extract.server_blocks import _find_decorator_matches, _get_function_block
from scripts.extract.server_parameters import extract_parameters
from scripts.extract.server_returns import infer_returns

REPO_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_PATH = REPO_ROOT / "references" / "raw" / "server_endpoints.json"
DOCSTRING_RE = re.compile(r'\s*[rubfRUBF]*(["\']{3})(.*?)\1', re.DOTALL)

ENDPOINT_COVERAGE = {
    "description": "Static extraction of ComfyUI HTTP and WebSocket endpoint structure.",
    "guaranteed_fields": [
        "endpoints[].route",
        "endpoints[].method",
        "endpoints[].returns.kind",
        "endpoints[].returns.status_codes",
    ],
    "best_effort_fields": [
        "endpoints[].description",
        "endpoints[].parameters",
        "endpoints[].returns.summary",
        "endpoints[].returns.fields",
        "endpoints[].returns.traceability",
    ],
    "deferred": [
        "deep parameter typing and validation semantics",
        "richer error contracts",
        "full response-body fidelity for variable-return branches",
    ],
}


def extract_endpoints(source_text: str) -> list[dict]:
    lines = source_text.splitlines()
    endpoints: list[dict] = []
    matches = _find_decorator_matches(lines)

    for k, (index, match) in enumerate(matches):
        decorator_kind, route = match.groups()
        method = decorator_kind.upper() if decorator_kind != "route" else "ROUTE"

        if k + 1 < len(matches):
            next_index = matches[k + 1][0]
        else:
            next_index = len(lines)

        block = _get_function_block(lines, index, next_index)
        doc_match = DOCSTRING_RE.search(block)
        description = ""
        if doc_match:
            description = " ".join(doc_match.group(2).strip().split())

        returns = infer_returns(block, source_text)
        parameters = extract_parameters(route, block, source_text)

        notes = []
        if method in ("POST", "PUT", "PATCH") and parameters:
            notes.append(
                "Parameters marked 'required' reflect static subscript access "
                "patterns, not API-level requiredness. Only fields that cause "
                "the handler to return an error status when missing are truly "
                "mandatory. Consult the prose API docs for precise "
                "mutation-request contracts."
            )

        endpoints.append(
            {
                "route": route,
                "method": method,
                "description": description,
                "parameters": parameters,
                "returns": returns,
                "notes": notes,
            }
        )

    return endpoints


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract ComfyUI server routes to JSON")
    parser.add_argument("server_path", nargs="?", help="Path to ComfyUI server.py")
    parser.add_argument("--version", default=None, help="Pinned upstream version or tag")
    parser.add_argument("--commit", default=None, help="Pinned upstream commit hash")
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="Output JSON path")
    args = parser.parse_args()

    if not args.server_path:
        parser.print_usage()
        return 1

    source_path = Path(args.server_path)
    source_text = source_path.read_text(encoding="utf-8")
    endpoints = extract_endpoints(source_text)

    payload = {
        "metadata": {
            "sources": [normalize_repo_relative_path(source_path, REPO_ROOT)],
            "extracted_date": datetime.now().strftime("%Y-%m-%d"),
            "version": args.version or "unversioned",
            "commit": args.commit,
        },
        "coverage": ENDPOINT_COVERAGE,
        "endpoints": endpoints,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {len(endpoints)} endpoints to {display_path(output_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
