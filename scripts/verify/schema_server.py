from __future__ import annotations

from scripts.verify.schema_common import (
    _check_type,
    _type_label,
    validate_parameter_details,
    validate_returns,
)

ENDPOINT_SCHEMA = {
    "route": (str, True),
    "method": (str, True),
    "description": (str, True),
    "parameters": (list, True),
    "returns": (dict, True),
}


def validate_endpoints(data: dict, filename: str) -> list[str]:
    errors = []
    endpoints = data.get("endpoints", [])
    for index, endpoint in enumerate(endpoints):
        if not isinstance(endpoint, dict):
            errors.append(f"{filename}: endpoints[{index}] is not a dict")
            continue
        for key, (expected_type, required) in ENDPOINT_SCHEMA.items():
            if key not in endpoint:
                if required:
                    errors.append(f"{filename}: endpoints[{index}] missing required key '{key}'")
                continue
            if not _check_type(endpoint[key], expected_type):
                errors.append(
                    f"{filename}: endpoints[{index}].{key} expected {_type_label(expected_type)}, got {type(endpoint[key]).__name__}"
                )

        returns = endpoint.get("returns")
        if isinstance(returns, dict):
            errors.extend(validate_returns(returns, filename, f"endpoints[{index}].returns"))

        parameters = endpoint.get("parameters")
        if isinstance(parameters, list):
            errors.extend(
                validate_parameter_details(parameters, filename, f"endpoints[{index}].parameters")
            )
    return errors
