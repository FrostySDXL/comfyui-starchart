import argparse
import json
import re
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "references" / "raw" / "server_endpoints.json"
DECORATOR_RE = re.compile(r'@routes\.(route|get|post|ws)\(\s*["\']([^"\']+)["\']')
DOCSTRING_RE = re.compile(r'\s*[rubfRUBF]*(["\']{3})(.*?)\1', re.DOTALL)
STATUS_RE = re.compile(r'status\s*=\s*(\d+)')

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
    ],
    "deferred": [
        "parameter typing",
        "richer error contracts",
        "full response-body fidelity for variable-return branches",
    ],
}


def _find_decorator_matches(lines: list[str]) -> list[tuple[int, re.Match]]:
    matches = []
    for index, line in enumerate(lines):
        match = DECORATOR_RE.search(line)
        if match:
            matches.append((index, match))
    return matches


def _get_function_block(lines: list[str], start_index: int, end_index: int) -> str:
    """Return the text between the decorator and the next decorator (or EOF)."""
    return "\n".join(lines[start_index:end_index])


def _get_helper_body(source_text: str, func_name: str) -> str:
    """Extract the body of a helper function defined in source_text."""
    pattern = rf'^\s*def\s+{re.escape(func_name)}\s*\([^)]*\):'
    lines = source_text.splitlines()
    for i, line in enumerate(lines):
        if re.match(pattern, line):
            indent = len(line) - len(line.lstrip())
            body_lines = []
            for j in range(i + 1, len(lines)):
                next_line = lines[j]
                if next_line.strip() == '':
                    body_lines.append(next_line)
                    continue
                next_indent = len(next_line) - len(next_line.lstrip())
                if next_indent <= indent:
                    break
                body_lines.append(next_line)
            return "\n".join(body_lines)
    return ""


def _extract_main_body(block: str) -> str:
    """Return the main function body, excluding nested function definitions."""
    lines = block.splitlines()
    start_idx = None
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith('def ') or stripped.startswith('async def '):
            start_idx = i
            break
    if start_idx is None:
        return block

    handler_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
    body_indent = handler_indent + 4

    result = []
    skip_depth = 0

    for line in lines[start_idx + 1:]:
        if not line.strip():
            if skip_depth == 0:
                result.append(line)
            continue

        line_indent = len(line) - len(line.lstrip())
        stripped = line.lstrip()

        if stripped.startswith('def ') or stripped.startswith('async def '):
            if line_indent >= body_indent:
                skip_depth += 1
                continue

        if skip_depth > 0:
            if line_indent <= body_indent:
                skip_depth = 0
                result.append(line)
            else:
                continue
        else:
            result.append(line)

    return '\n'.join(result)


def _extract_json_fields(payload_text: str) -> list[dict]:
    """Extract top-level dict keys from a literal dict string."""
    fields = []
    seen = set()
    # Handle multi-line dicts by searching the whole text for quoted keys
    for m in re.finditer(r'["\']([^"\']+)["\']\s*:', payload_text):
        name = m.group(1)
        if name not in seen:
            seen.add(name)
            fields.append({"name": name})
    return fields


def _extract_status_codes(block: str) -> list[int]:
    codes = set()
    for m in STATUS_RE.finditer(block):
        codes.add(int(m.group(1)))
    if not codes:
        codes.add(200)
    return sorted(codes)


def _find_all_json_response_args(block: str) -> list[tuple[str, str]]:
    """Find all web.json_response(...) calls and return (arg_text, after_text) pairs."""
    args = []
    start = 0
    while True:
        pos = block.find('web.json_response(', start)
        if pos == -1:
            break
        pos += len('web.json_response(')
        depth = 1
        idx = pos
        while idx < len(block) and depth > 0:
            ch = block[idx]
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            elif ch in '"\'':
                quote = ch
                idx += 1
                while idx < len(block) and block[idx] != quote:
                    if block[idx] == '\\':
                        idx += 1
                    idx += 1
            idx += 1
        arg_text = block[pos:idx - 1]
        after_text = block[idx:idx + 20]
        args.append((arg_text, after_text))
        start = idx
    return args


def _infer_json_response(block: str) -> dict:
    block_status_codes = _extract_status_codes(block)
    calls = _find_all_json_response_args(block)

    # Prefer calls whose argument does not contain an error status (4xx).
    best_arg = ""
    best_count = -1
    for arg, _after in calls:
        if 'status=4' in arg:
            continue
        count = len(_extract_json_fields(arg))
        if count > best_count:
            best_count = count
            best_arg = arg

    # If every call looks like an error response, fall back to the one with the most fields.
    if not best_arg and calls:
        best_arg = max(calls, key=lambda c: len(_extract_json_fields(c[0])))[0]

    fields = _extract_json_fields(best_arg)
    notes = []

    # Determine effective status codes based on the selected call.
    # If the selected json_response has an explicit status= in its argument,
    # use those codes. Otherwise, default to [200] since json_response returns 200 by default.
    if best_arg and 'status=' in best_arg:
        # Extract explicit status codes from the selected call's argument
        effective_codes = set()
        for m in STATUS_RE.finditer(best_arg):
            effective_codes.add(int(m.group(1)))
        if not effective_codes:
            effective_codes.add(200)
        effective_codes = sorted(effective_codes)
    elif best_arg:
        # json_response defaults to 200 unless the selected call overrides it.
        # Preserve explicit error statuses seen in sibling branches so callers can
        # distinguish documented success and failure outcomes.
        effective_codes = sorted({200, *block_status_codes})
    else:
        # No json_response calls found; use block-level codes as fallback
        effective_codes = block_status_codes

    if 404 in effective_codes:
        notes.append("Returns 404 when the requested resource is not found.")
    if 400 in effective_codes:
        notes.append("Returns 400 for validation failures or bad requests.")
    if 403 in effective_codes:
        notes.append("Returns 403 for forbidden access attempts.")

    summary = "JSON response."
    if fields:
        summary = f"JSON object with fields: {', '.join(f['name'] for f in fields)}."

    return {
        "kind": "json",
        "summary": summary,
        "status_codes": effective_codes,
        "fields": fields,
        "notes": notes,
    }


def _infer_plain_response(block: str) -> dict:
    status_codes = _extract_status_codes(block)
    kind = "empty"
    summary = "Empty acknowledgement response."
    if 'body=' in block:
        kind = "binary"
        summary = "Binary or raw body response with explicit content type."

    notes = []
    if 404 in status_codes:
        notes.append("Returns 404 when the requested resource is not found.")
    if 400 in status_codes:
        notes.append("Returns 400 for validation failures or bad requests.")
    if 403 in status_codes:
        notes.append("Returns 403 for forbidden access attempts.")

    return {
        "kind": kind,
        "summary": summary,
        "status_codes": status_codes,
        "fields": [],
        "notes": notes,
    }


def infer_returns(block: str, full_source: str = "") -> dict:
    """Inspect a handler block and infer structured return metadata."""
    main_body = _extract_main_body(block)

    if 'web.WebSocketResponse(' in main_body:
        return {
            "kind": "websocket",
            "summary": "WebSocket connection upgrade.",
            "status_codes": [101],
            "fields": [],
            "notes": [],
        }

    if 'web.FileResponse(' in main_body:
        return {
            "kind": "file",
            "summary": "File response with inferred content type.",
            "status_codes": [200],
            "fields": [],
            "notes": [],
        }

    if 'web.json_response(' in main_body:
        return _infer_json_response(main_body)

    if 'web.Response(' in main_body:
        return _infer_plain_response(main_body)

    # Check for delegation to a local helper function
    helper_match = re.search(r'return\s+(\w+)\s*\(', main_body)
    if helper_match and full_source:
        helper_name = helper_match.group(1)
        helper_body = _get_helper_body(full_source, helper_name)
        if helper_body:
            nested = infer_returns(helper_body, "")
            if nested["kind"] != "unknown":
                return nested

    return {
        "kind": "unknown",
        "summary": "Response shape could not be inferred from current parser.",
        "status_codes": [200],
        "fields": [],
        "notes": [],
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

        endpoints.append(
            {
                "route": route,
                "method": method,
                "description": description,
                "parameters": [],
                "returns": returns,
            }
        )

    return endpoints


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract ComfyUI server routes to JSON")
    parser.add_argument("server_path", nargs="?", help="Path to ComfyUI server.py")
    parser.add_argument("--version", default=None, help="Pinned upstream version or tag")
    parser.add_argument("--commit", default=None, help="Pinned upstream commit hash")
    args = parser.parse_args()

    if not args.server_path:
        parser.print_usage()
        return 1

    source_path = Path(args.server_path)
    source_text = source_path.read_text(encoding="utf-8")
    endpoints = extract_endpoints(source_text)

    payload = {
        "metadata": {
            "sources": [str(source_path).replace("\\", "/")],
            "extracted_date": datetime.now().strftime("%Y-%m-%d"),
            "version": args.version or "unversioned",
            "commit": args.commit,
        },
        "coverage": ENDPOINT_COVERAGE,
        "endpoints": endpoints,
    }

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {len(endpoints)} endpoints to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
