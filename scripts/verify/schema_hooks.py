from __future__ import annotations

from scripts.verify.schema_common import _check_type, _type_label, validate_traceability

HOOK_SCHEMA = {
    "name": (str, True),
    "type": (str, True),
    "description": (str, True),
    "defined_in": ((str, type(None)), True),
    "invoked_in": (list, True),
    "signature": ((str, type(None)), False),
    "arguments": (list, False),
    "return_type": ((str, type(None)), False),
    "invocation_style": (list, False),
    "traceability": (dict, False),
}

HOOK_ARGUMENT_SCHEMA = {
    "name": (str, True),
    "type_hint": ((str, type(None)), False),
}


def validate_hooks(data: dict, filename: str) -> list[str]:
    errors = []
    hooks = data.get("hooks", [])
    for index, hook in enumerate(hooks):
        if not isinstance(hook, dict):
            errors.append(f"{filename}: hooks[{index}] is not a dict")
            continue
        for key, (expected_type, required) in HOOK_SCHEMA.items():
            if key not in hook:
                if required:
                    errors.append(f"{filename}: hooks[{index}] missing required key '{key}'")
                continue
            if not _check_type(hook[key], expected_type):
                errors.append(
                    f"{filename}: hooks[{index}].{key} expected {_type_label(expected_type)}, got {type(hook[key]).__name__}"
                )

        arguments = hook.get("arguments", [])
        if isinstance(arguments, list):
            for arg_index, argument in enumerate(arguments):
                if not isinstance(argument, dict):
                    errors.append(
                        f"{filename}: hooks[{index}].arguments[{arg_index}] is not a dict"
                    )
                    continue
                for key, (expected_type, required) in HOOK_ARGUMENT_SCHEMA.items():
                    if key not in argument:
                        if required:
                            errors.append(
                                f"{filename}: hooks[{index}].arguments[{arg_index}] missing required key '{key}'"
                            )
                        continue
                    if not _check_type(argument[key], expected_type):
                        errors.append(
                            f"{filename}: hooks[{index}].arguments[{arg_index}].{key} expected {_type_label(expected_type)}, got {type(argument[key]).__name__}"
                        )

        invocation_style = hook.get("invocation_style", [])
        if isinstance(invocation_style, list):
            for style_index, style in enumerate(invocation_style):
                if not isinstance(style, str):
                    errors.append(
                        f"{filename}: hooks[{index}].invocation_style[{style_index}] expected str, got {type(style).__name__}"
                    )

        traceability = hook.get("traceability")
        if isinstance(traceability, dict):
            errors.extend(
                validate_traceability(traceability, filename, f"hooks[{index}].traceability")
            )
    return errors
