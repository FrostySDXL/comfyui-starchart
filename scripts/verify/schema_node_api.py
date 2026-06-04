from __future__ import annotations

from scripts.verify.schema_common import (
    SchemaSpec,
    _check_type,
    _type_label,
    _validate_schema_shape,
    validate_parameter_details,
    validate_traceability,
)

IO_TYPE_SCHEMA: SchemaSpec = {
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

V3_SCHEMA_CONTRACT_SCHEMA = {
    "contract_version": (str, True),
    "schema_fields": (list, True),
    "node_info_fields": (list, True),
    "hidden_values": (dict, True),
    "price_badge_contract": (list, True),
    "node_flags": (list, True),
}

V3_DATACLASS_FIELD_SCHEMA = {
    "name": (str, True),
    "type_hint": (str, False),
    "required": (bool, True),
    "default": ((str, int, float, bool, type(None)), False),
    "default_factory": (str, False),
    "default_expression": (str, False),
    "description": (str, False),
    "defined_in": (str, True),
    "traceability": (dict, True),
}

V3_HIDDEN_VALUES_SCHEMA = {
    "hidden_enum": (list, True),
    "hidden_auto_injection": (list, True),
}

V3_HIDDEN_ENUM_ENTRY_SCHEMA = {
    "name": (str, True),
    "value": (str, False),
    "description": (str, False),
    "defined_in": (str, True),
    "traceability": (dict, True),
}

V3_HIDDEN_AUTO_INJECTION_SCHEMA = {
    "condition": (str, True),
    "injected": (list, True),
}

V3_PRICE_BADGE_CONTRACT_SCHEMA = {
    "class_name": (str, True),
    "fields": (list, True),
    "traceability": (dict, True),
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


def _validate_v3_dataclass_fields(fields: list, filename: str, path: str) -> list[str]:
    errors: list[str] = []
    for index, field in enumerate(fields):
        item_path = f"{path}[{index}]"
        if not isinstance(field, dict):
            errors.append(f"{filename}: {item_path} expected dict, got {type(field).__name__}")
            continue
        errors.extend(_validate_schema_shape(field, V3_DATACLASS_FIELD_SCHEMA, filename, item_path))
        traceability = field.get("traceability")
        if isinstance(traceability, dict):
            errors.extend(
                validate_traceability(traceability, filename, f"{item_path}.traceability")
            )
    return errors


def validate_v3_schema_contract(data: dict, filename: str) -> list[str]:
    errors: list[str] = []
    contract = data.get("v3_schema_contract")
    if contract is None:
        return errors
    if not isinstance(contract, dict):
        return [f"{filename}: v3_schema_contract expected dict, got {type(contract).__name__}"]

    errors.extend(
        _validate_schema_shape(
            contract,
            V3_SCHEMA_CONTRACT_SCHEMA,
            filename,
            "v3_schema_contract",
        )
    )

    schema_fields = contract.get("schema_fields")
    if isinstance(schema_fields, list):
        errors.extend(
            _validate_v3_dataclass_fields(
                schema_fields,
                filename,
                "v3_schema_contract.schema_fields",
            )
        )

    node_info_fields = contract.get("node_info_fields")
    if isinstance(node_info_fields, list):
        errors.extend(
            _validate_v3_dataclass_fields(
                node_info_fields,
                filename,
                "v3_schema_contract.node_info_fields",
            )
        )

    hidden_values = contract.get("hidden_values")
    if isinstance(hidden_values, dict):
        errors.extend(
            _validate_schema_shape(
                hidden_values,
                V3_HIDDEN_VALUES_SCHEMA,
                filename,
                "v3_schema_contract.hidden_values",
            )
        )
        hidden_enum = hidden_values.get("hidden_enum")
        if isinstance(hidden_enum, list):
            for index, entry in enumerate(hidden_enum):
                item_path = f"v3_schema_contract.hidden_values.hidden_enum[{index}]"
                if not isinstance(entry, dict):
                    errors.append(
                        f"{filename}: {item_path} expected dict, got {type(entry).__name__}"
                    )
                    continue
                errors.extend(
                    _validate_schema_shape(entry, V3_HIDDEN_ENUM_ENTRY_SCHEMA, filename, item_path)
                )
                traceability = entry.get("traceability")
                if isinstance(traceability, dict):
                    errors.extend(
                        validate_traceability(traceability, filename, f"{item_path}.traceability")
                    )
        hidden_auto_injection = hidden_values.get("hidden_auto_injection")
        if isinstance(hidden_auto_injection, list):
            for index, entry in enumerate(hidden_auto_injection):
                item_path = f"v3_schema_contract.hidden_values.hidden_auto_injection[{index}]"
                if not isinstance(entry, dict):
                    errors.append(
                        f"{filename}: {item_path} expected dict, got {type(entry).__name__}"
                    )
                    continue
                errors.extend(
                    _validate_schema_shape(
                        entry, V3_HIDDEN_AUTO_INJECTION_SCHEMA, filename, item_path
                    )
                )
                injected = entry.get("injected")
                if isinstance(injected, list):
                    for value_index, value in enumerate(injected):
                        if not isinstance(value, str):
                            errors.append(
                                f"{filename}: {item_path}.injected[{value_index}] expected str, got {type(value).__name__}"
                            )

    price_badge_contract = contract.get("price_badge_contract")
    if isinstance(price_badge_contract, list):
        for index, entry in enumerate(price_badge_contract):
            item_path = f"v3_schema_contract.price_badge_contract[{index}]"
            if not isinstance(entry, dict):
                errors.append(f"{filename}: {item_path} expected dict, got {type(entry).__name__}")
                continue
            errors.extend(
                _validate_schema_shape(entry, V3_PRICE_BADGE_CONTRACT_SCHEMA, filename, item_path)
            )
            traceability = entry.get("traceability")
            if isinstance(traceability, dict):
                errors.extend(
                    validate_traceability(traceability, filename, f"{item_path}.traceability")
                )
            fields = entry.get("fields")
            if isinstance(fields, list):
                errors.extend(
                    _validate_v3_dataclass_fields(fields, filename, f"{item_path}.fields")
                )

    field_names = {
        field.get("name")
        for field in contract.get("schema_fields", [])
        if isinstance(field, dict) and isinstance(field.get("name"), str)
    }
    node_flags = contract.get("node_flags")
    if isinstance(node_flags, list):
        for index, entry in enumerate(node_flags):
            item_path = f"v3_schema_contract.node_flags[{index}]"
            if not isinstance(entry, dict):
                errors.append(f"{filename}: {item_path} expected dict, got {type(entry).__name__}")
                continue
            missing = {"name", "schema_fields_ref"} - set(entry)
            for key in sorted(missing):
                errors.append(f"{filename}: {item_path} missing required key '{key}'")
            unexpected = set(entry) - {"name", "schema_fields_ref"}
            if unexpected:
                errors.append(
                    f"{filename}: {item_path} must contain exactly ['name', 'schema_fields_ref']"
                )
            if missing or unexpected:
                continue
            for key in ("name", "schema_fields_ref"):
                if not isinstance(entry[key], str):
                    errors.append(
                        f"{filename}: {item_path}.{key} expected str, got {type(entry[key]).__name__}"
                    )
            if (
                isinstance(entry.get("schema_fields_ref"), str)
                and entry["schema_fields_ref"] not in field_names
            ):
                errors.append(
                    f"{filename}: {item_path}.schema_fields_ref '{entry['schema_fields_ref']}' does not resolve to v3_schema_contract.schema_fields[].name"
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
