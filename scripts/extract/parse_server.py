import argparse
import ast
import json
import re
from datetime import datetime
from pathlib import Path

from scripts.common.path_normalization import normalize_repo_relative_path

REPO_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_PATH = REPO_ROOT / "references" / "raw" / "server_endpoints.json"
DECORATOR_RE = re.compile(r'@routes\.(route|get|post|ws)\(\s*["\']([^"\']+)["\']')
DOCSTRING_RE = re.compile(r'\s*[rubfRUBF]*(["\']{3})(.*?)\1', re.DOTALL)
STATUS_RE = re.compile(r"status\s*=\s*(\d+)")

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

ROUTE_PARAM_RE = re.compile(r"\{([^}]+)\}")
UNPARSEABLE_LITERAL = object()


def _normalize_literal(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _parse_literal(text: str):
    try:
        return _normalize_literal(ast.literal_eval(text.strip()))
    except (SyntaxError, ValueError):
        return UNPARSEABLE_LITERAL


def _extract_literal_choices(body: str, variable_name: str) -> list:
    patterns = [
        rf"\b{re.escape(variable_name)}\b\s+not\s+in\s+(\[[^\]]+\]|\([^\)]+\)|\{{[^\}}]+\}})",
        rf"\b{re.escape(variable_name)}\b\s+in\s+(\[[^\]]+\]|\([^\)]+\)|\{{[^\}}]+\}})",
    ]
    for pattern in patterns:
        match = re.search(pattern, body)
        if not match:
            continue
        try:
            values = ast.literal_eval(match.group(1))
        except (SyntaxError, ValueError):
            continue
        if isinstance(values, (list, tuple, set)):
            normalized = [_normalize_literal(value) for value in values]
            return sorted(normalized, key=lambda value: str(value))
    return []


def _merge_parameter_details(existing: dict, incoming: dict) -> dict:
    merged = dict(existing)
    if incoming.get("required"):
        merged["required"] = True
    if "default" in incoming and "default" not in merged:
        merged["default"] = incoming["default"]
    if incoming.get("allowed_values"):
        values = list(merged.get("allowed_values", []))
        for value in incoming["allowed_values"]:
            if value not in values:
                values.append(value)
        merged["allowed_values"] = values
    if "traceability" not in merged and incoming.get("traceability"):
        merged["traceability"] = incoming["traceability"]
    return merged


def _maybe_append_parameter(parameters: list[dict], parameter: dict) -> None:
    key = (parameter["name"], parameter["location"])
    for index, existing in enumerate(parameters):
        if (existing.get("name"), existing.get("location")) == key:
            parameters[index] = _merge_parameter_details(existing, parameter)
            return
    parameters.append(parameter)


def _parameter_traceability(strategy: str, detail: str) -> dict:
    traceability = {
        "source_type": "source-backed",
        "strategy": strategy,
    }
    if detail:
        traceability["detail"] = detail
    return traceability


def _extract_aliases(body: str, expression_patterns: list[str]) -> list[str]:
    aliases = []
    for expression_pattern in expression_patterns:
        for match in re.finditer(
            rf"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:await\s+)?{expression_pattern}", body
        ):
            alias = match.group(1)
            if alias not in aliases:
                aliases.append(alias)
    return aliases


def _extract_mapping_parameters(
    body: str, aliases: list[str], location: str, strategy_prefix: str
) -> tuple[list[dict], dict[str, tuple[str, str]]]:
    parameters: list[dict] = []
    variable_map: dict[str, tuple[str, str]] = {}

    for alias in aliases:
        alias_pattern = re.escape(alias)
        for match in re.finditer(rf"{alias_pattern}\[\s*['\"]([^'\"]+)['\"]\s*\]", body):
            name = match.group(1)
            _maybe_append_parameter(
                parameters,
                {
                    "name": name,
                    "location": location,
                    "required": True,
                    "traceability": _parameter_traceability(
                        f"{strategy_prefix}.subscription", alias
                    ),
                },
            )

        for match in re.finditer(
            rf"{alias_pattern}\.get\(\s*['\"]([^'\"]+)['\"](?:\s*,\s*([^\)]+))?\)", body
        ):
            name = match.group(1)
            default_text = match.group(2)
            parameter = {
                "name": name,
                "location": location,
                "required": default_text is None,
                "traceability": _parameter_traceability(f"{strategy_prefix}.get", alias),
            }
            if default_text is not None:
                parameter["required"] = False
                default_value = _parse_literal(default_text)
                if default_value is not UNPARSEABLE_LITERAL and default_value is not None:
                    parameter["default"] = default_value
            _maybe_append_parameter(parameters, parameter)

        for match in re.finditer(
            rf"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*{alias_pattern}\[\s*['\"]([^'\"]+)['\"]\s*\]", body
        ):
            variable_map[match.group(1)] = (match.group(2), location)
        for match in re.finditer(
            rf"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*{alias_pattern}\.get\(\s*['\"]([^'\"]+)['\"]", body
        ):
            variable_map[match.group(1)] = (match.group(2), location)

    for variable_name, (parameter_name, parameter_location) in variable_map.items():
        allowed_values = _extract_literal_choices(body, variable_name)
        if not allowed_values:
            continue
        _maybe_append_parameter(
            parameters,
            {
                "name": parameter_name,
                "location": parameter_location,
                "allowed_values": allowed_values,
                "traceability": _parameter_traceability("literal_membership_check", variable_name),
            },
        )

    return parameters, variable_map


def _extract_helper_body_from_main_body(main_body: str, full_source: str) -> str:
    helper_match = re.search(r"return\s+(\w+)\s*\(", main_body)
    if not helper_match or not full_source:
        return ""
    helper_name = helper_match.group(1)
    return _get_helper_body(full_source, helper_name)


def extract_parameters(route: str, block: str, full_source: str = "") -> list[dict]:
    parameters: list[dict] = []
    main_body = _extract_main_body(block)
    helper_body = _extract_helper_body_from_main_body(main_body, full_source)
    combined_body = main_body if not helper_body else f"{main_body}\n{helper_body}"

    for route_param in ROUTE_PARAM_RE.findall(route):
        _maybe_append_parameter(
            parameters,
            {
                "name": route_param,
                "location": "path",
                "required": True,
                "traceability": _parameter_traceability("route_token", route),
            },
        )

    query_aliases = ["request.rel_url.query", "request.query"]
    query_aliases.extend(
        _extract_aliases(combined_body, [r"request\.rel_url\.query", r"request\.query"])
    )
    path_aliases = ["request.match_info"]
    path_aliases.extend(_extract_aliases(combined_body, [r"request\.match_info"]))
    form_aliases = _extract_aliases(combined_body, [r"request\.post\(\)"])
    json_aliases = _extract_aliases(combined_body, [r"request\.json\(\)"])

    for extracted, _ in [
        _extract_mapping_parameters(combined_body, query_aliases, "query", "query_access"),
        _extract_mapping_parameters(combined_body, path_aliases, "path", "match_info_access"),
        _extract_mapping_parameters(combined_body, form_aliases, "form", "form_access"),
        _extract_mapping_parameters(combined_body, json_aliases, "json", "json_access"),
    ]:
        for parameter in extracted:
            _maybe_append_parameter(parameters, parameter)

    return parameters


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
    pattern = rf"^\s*def\s+{re.escape(func_name)}\s*\([^)]*\):"
    lines = source_text.splitlines()
    for i, line in enumerate(lines):
        if re.match(pattern, line):
            indent = len(line) - len(line.lstrip())
            body_lines = []
            for j in range(i + 1, len(lines)):
                next_line = lines[j]
                if next_line.strip() == "":
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
        if stripped.startswith("def ") or stripped.startswith("async def "):
            start_idx = i
            break
    if start_idx is None:
        return block

    handler_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
    body_indent = handler_indent + 4

    result = []
    skip_depth = 0

    for line in lines[start_idx + 1 :]:
        if not line.strip():
            if skip_depth == 0:
                result.append(line)
            continue

        line_indent = len(line) - len(line.lstrip())
        stripped = line.lstrip()

        if (
            stripped.startswith("def ") or stripped.startswith("async def ")
        ) and line_indent <= handler_indent:
            break

        if stripped.startswith("def ") or stripped.startswith("async def "):
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

    return "\n".join(result)


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

    # Prefer calls whose argument does not contain an error status (4xx).
    best_arg = ""
    best_count = -1
    for arg, _call_index in calls:
        if "status=4" in arg:
            continue
        count = len(_extract_json_fields_from_arg(block, arg, _call_index))
        if count > best_count:
            best_count = count
            best_arg = arg
            best_call_index = _call_index

    if "best_call_index" not in locals():
        best_call_index = -1

    # If every call looks like an error response, fall back to the one with the most fields.
    if not best_arg and calls:
        best_arg, best_call_index = max(
            calls,
            key=lambda c: len(_extract_json_fields_from_arg(block, c[0], c[1])),
        )

    fields = _extract_json_fields_from_arg(block, best_arg, best_call_index)
    notes = []

    # Determine effective status codes based on the selected call.
    # If the selected json_response has an explicit status= in its argument,
    # use those codes. Otherwise, default to [200] since json_response returns 200 by default.
    if best_arg and "status=" in best_arg:
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

    # Check for delegation to a local helper function
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
    print(f"Extracted {len(endpoints)} endpoints to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
