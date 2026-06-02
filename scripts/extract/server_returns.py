import re

from scripts.extract.server_helpers import _extract_main_body, _get_helper_body

STATUS_RE = re.compile(r"status\s*=\s*(\d+)")


def _extract_json_fields(payload_text: str) -> list[dict]:
    """Extract top-level dict keys from a literal dict string."""
    fields = []
    seen = set()
    for match in re.finditer(r'["\']([^"\']+)["\']\s*:', payload_text):
        name = match.group(1)
        if name not in seen:
            seen.add(name)
            fields.append({"name": name})
    return fields


def _extract_status_codes(block: str) -> list[int]:
    codes = set()
    for match in STATUS_RE.finditer(block):
        codes.add(int(match.group(1)))
    if not codes:
        codes.add(200)
    return sorted(codes)


def _find_all_json_response_args(block: str) -> list[tuple[str, int]]:
    """Find all web.json_response(...) calls and return (arg_text, call_index) pairs."""
    args = []
    start = 0
    while True:
        call_index = block.find("web.json_response(", start)
        if call_index == -1:
            break
        pos = call_index + len("web.json_response(")
        depth = 1
        idx = pos
        while idx < len(block) and depth > 0:
            ch = block[idx]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif ch in "\"'":
                quote = ch
                idx += 1
                while idx < len(block) and block[idx] != quote:
                    if block[idx] == "\\":
                        idx += 1
                    idx += 1
            idx += 1
        arg_text = block[pos : idx - 1]
        args.append((arg_text, call_index))
        start = idx
    return args


def _extract_dict_literal_from_assignment(block: str, variable_name: str, cutoff: int) -> str:
    prefix = block[:cutoff]
    pattern = re.compile(rf"\b{re.escape(variable_name)}\s*=\s*\{{")
    matches = list(pattern.finditer(prefix))
    if not matches:
        return ""

    brace_start = matches[-1].end() - 1
    depth = 0
    idx = brace_start
    while idx < len(prefix):
        char = prefix[idx]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return prefix[brace_start : idx + 1]
        elif char in "\"'":
            quote = char
            idx += 1
            while idx < len(prefix) and prefix[idx] != quote:
                if prefix[idx] == "\\":
                    idx += 1
                idx += 1
        idx += 1
    return ""


def _extract_augmented_dict_fields(block: str, variable_name: str, cutoff: int) -> list[dict]:
    fields = []
    seen = set()
    pattern = re.compile(
        rf'{re.escape(variable_name)}\["([^"\\]+)"\]\s*=|{re.escape(variable_name)}\[\'([^\'\\]+)\'\]\s*='
    )
    for match in pattern.finditer(block[:cutoff]):
        name = match.group(1) or match.group(2)
        if name and name not in seen:
            seen.add(name)
            fields.append({"name": name})
    return fields


def _extract_json_fields_from_arg(block: str, arg_text: str, call_index: int) -> list[dict]:
    stripped = arg_text.strip()
    direct_fields = _extract_json_fields(stripped)
    if direct_fields:
        return direct_fields

    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", stripped):
        dict_literal = _extract_dict_literal_from_assignment(block, stripped, call_index)
        fields = _extract_json_fields(dict_literal)
        seen = {field["name"] for field in fields}
        for field in _extract_augmented_dict_fields(block, stripped, call_index):
            if field["name"] not in seen:
                seen.add(field["name"])
                fields.append(field)
        return fields

    return []


def _infer_json_response(block: str) -> dict:
    block_status_codes = _extract_status_codes(block)
    calls = _find_all_json_response_args(block)

    best_arg = ""
    best_count = -1
    for arg, call_index in calls:
        if "status=4" in arg:
            continue
        count = len(_extract_json_fields_from_arg(block, arg, call_index))
        if count > best_count:
            best_count = count
            best_arg = arg
            best_call_index = call_index

    if "best_call_index" not in locals():
        best_call_index = -1

    if not best_arg and calls:
        best_arg, best_call_index = max(
            calls,
            key=lambda call: len(_extract_json_fields_from_arg(block, call[0], call[1])),
        )

    fields = _extract_json_fields_from_arg(block, best_arg, best_call_index)
    notes = []

    if best_arg and "status=" in best_arg:
        code_set: set[int] = set()
        for match in STATUS_RE.finditer(best_arg):
            code_set.add(int(match.group(1)))
        if not code_set:
            code_set.add(200)
        effective_codes: list[int] = sorted(code_set)
    elif best_arg:
        effective_codes = sorted({200, *block_status_codes})
    else:
        effective_codes = block_status_codes

    if 404 in effective_codes:
        notes.append("Returns 404 when the requested resource is not found.")
    if 400 in effective_codes:
        notes.append("Returns 400 for validation failures or bad requests.")
    if 403 in effective_codes:
        notes.append("Returns 403 for forbidden access attempts.")

    summary = "JSON response."
    if fields:
        summary = f"JSON object with fields: {', '.join(field['name'] for field in fields)}."

    return {
        "kind": "json",
        "summary": summary,
        "status_codes": effective_codes,
        "fields": fields,
        "notes": notes,
        "traceability": {
            "source_type": "source-backed",
            "strategy": "web.json_response",
        },
    }


def _infer_plain_response(block: str) -> dict:
    status_codes = _extract_status_codes(block)
    kind = "empty"
    summary = "Empty acknowledgement response."
    if "body=" in block:
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
        "traceability": {
            "source_type": "source-backed",
            "strategy": "web.Response",
        },
    }


def infer_returns(block: str, full_source: str = "") -> dict:
    """Inspect a handler block and infer structured return metadata."""
    main_body = _extract_main_body(block)

    if "web.WebSocketResponse(" in main_body:
        return {
            "kind": "websocket",
            "summary": "WebSocket connection upgrade.",
            "status_codes": [101],
            "fields": [],
            "notes": [],
            "traceability": {
                "source_type": "source-backed",
                "strategy": "web.WebSocketResponse",
            },
        }

    if "web.FileResponse(" in main_body:
        return {
            "kind": "file",
            "summary": "File response with inferred content type.",
            "status_codes": [200],
            "fields": [],
            "notes": [],
            "traceability": {
                "source_type": "source-backed",
                "strategy": "web.FileResponse",
            },
        }

    if "web.json_response(" in main_body:
        return _infer_json_response(main_body)

    if "web.Response(" in main_body:
        return _infer_plain_response(main_body)

    helper_match = re.search(r"return\s+(\w+)\s*\(", main_body)
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
        "traceability": {
            "source_type": "best-effort",
            "strategy": "fallback_unknown",
        },
    }
