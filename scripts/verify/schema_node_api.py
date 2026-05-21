from __future__ import annotations

from scripts.verify.schema_common import (
    _check_type,
    _type_label,
    validate_parameter_details,
    validate_traceability,
)

IO_TYPE_SCHEMA = {
    "io_type": (str, True),
    "class_name": (str, True),
    "input_class": ((str, type(None)), True),
    "input_parameters": (list, True),
    "output_parameters": (list, False),
    "input_parameter_details": (list, False),
    "output_parameter_details": (list, False),
    "type_hint": ((str, type(None)), False),
    "defined_in": (str, False),
    "is_widget": (bool, False),
}

TYPED_INPUT_SHAPE_SCHEMA = {
    "description": (str, True),
    "fields": (dict, True),
    "defined_in": (str, False),
}

TYPED_INPUT_FIELD_SCHEMA = {
    "type": (str, True),
    "description": (str, False),
    "traceability": (dict, False),
}


def validate_io_types(data: dict, filename: str) -> list[str]:
    errors = []
    io_types = data.get("io_types", [])
    for index, entry in enumerate(io_types):
        if not isinstance(entry, dict):
            errors.append(f"{filename}: io_types[{index}] is not a dict")
            continue
        for key, (expected_type, required) in IO_TYPE_SCHEMA.items():
            if key not in entry:
                if required:
                    errors.append(f"{filename}: io_types[{index}] missing required key '{key}'")
                continue
            if not _check_type(entry[key], expected_type):
                errors.append(
                    f"{filename}: io_types[{index}].{key} expected {_type_label(expected_type)}, got {type(entry[key]).__name__}"
                )

        for detail_key in ("input_parameter_details", "output_parameter_details"):
            details = entry.get(detail_key)
            if isinstance(details, list):
                errors.extend(
                    validate_parameter_details(details, filename, f"io_types[{index}].{detail_key}")
                )
    return errors


def validate_typed_input_shapes(data: dict, filename: str) -> list[str]:
    errors: list[str] = []
    typed_input_shapes = data.get("typed_input_shapes", {})
    if not isinstance(typed_input_shapes, dict):
        return errors

    for shape_name, shape in typed_input_shapes.items():
        if not isinstance(shape, dict):
            errors.append(f"{filename}: typed_input_shapes['{shape_name}'] is not a dict")
            continue
        for key, (expected_type, required) in TYPED_INPUT_SHAPE_SCHEMA.items():
            if key not in shape:
                if required:
                    errors.append(
                        f"{filename}: typed_input_shapes['{shape_name}'] missing required key '{key}'"
                    )
                continue
            if not _check_type(shape[key], expected_type):
                errors.append(
                    f"{filename}: typed_input_shapes['{shape_name}'].{key} expected {_type_label(expected_type)}, got {type(shape[key]).__name__}"
                )

        fields = shape.get("fields", {})
        if isinstance(fields, dict):
            for field_name, field in fields.items():
                if not isinstance(field, dict):
                    errors.append(
                        f"{filename}: typed_input_shapes['{shape_name}'].fields['{field_name}'] is not a dict"
                    )
                    continue
                for key, (expected_type, required) in TYPED_INPUT_FIELD_SCHEMA.items():
                    if key not in field:
                        if required:
                            errors.append(
                                f"{filename}: typed_input_shapes['{shape_name}'].fields['{field_name}'] missing required key '{key}'"
                            )
                        continue
                    if not _check_type(field[key], expected_type):
                        errors.append(
                            f"{filename}: typed_input_shapes['{shape_name}'].fields['{field_name}'].{key} expected {_type_label(expected_type)}, got {type(field[key]).__name__}"
                        )

                traceability = field.get("traceability")
                if isinstance(traceability, dict):
                    errors.extend(
                        validate_traceability(
                            traceability,
                            filename,
                            f"typed_input_shapes['{shape_name}'].fields['{field_name}'].traceability",
                        )
                    )
    return errors


def validate_object_info_runtime(data: dict, filename: str) -> list[str]:
    errors = []
    object_info = data.get("object_info", {})
    if not isinstance(object_info, dict):
        return [f"{filename}: object_info is not a dict"]

    for key, value in object_info.items():
        if not isinstance(key, str):
            errors.append(f"{filename}: object_info key {key!r} is not a string")
        if not isinstance(value, dict):
            errors.append(f"{filename}: object_info['{key}'] is not a dict")
    return errors
