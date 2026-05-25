import ast
import re

from scripts.extract.server_helpers import (
    _extract_helper_body_from_main_body,
    _extract_main_body,
)

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
            rf"{alias_pattern}\.get\(\s*['\"]([^'\"]+)['\"](?:\s*,\s*([^\)]+))?\)",
            body,
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
            rf"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*{alias_pattern}\[\s*['\"]([^'\"]+)['\"]\s*\]",
            body,
        ):
            variable_map[match.group(1)] = (match.group(2), location)
        for match in re.finditer(
            rf"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*{alias_pattern}\.get\(\s*['\"]([^'\"]+)['\"]",
            body,
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
