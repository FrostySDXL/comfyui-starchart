import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.unit.helpers.extractor_test_utils import call_main, load_module

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "extract" / "parse_node_api_schema.py"

# ---------------------------------------------------------------------------
# Shared sample fixtures for extraction tests.
# ---------------------------------------------------------------------------

_SERVER_SAMPLE_FULL = """\
def node_info(node_class):
    info = {}
    info['input'] = obj_class.INPUT_TYPES()
    info['output'] = obj_class.RETURN_TYPES
    info['display_name'] = node_class
    info['category'] = 'sd'
    info['search_aliases'] = []
    return info
"""

_IO_SAMPLE_FULL = """\
from dataclasses import dataclass, field
from enum import Enum

@comfytype(io_type="BOOLEAN")
class Boolean(ComfyTypeIO):
    Type = bool

    class Input(WidgetInput):
        def __init__(self, id: str, default: bool=None, label_on: str=None):
            pass

@comfytype(io_type="STRING")
class String(ComfyTypeIO):
    Type = str

    class Input(WidgetInput):
        def __init__(self, id: str, multiline=False, default: str=None):
            pass

    class Output(Output):
        def __init__(self, id: str=None, display_name: str=None, tooltip: str=None, is_output_list=False):
            pass

@comfytype(io_type="LOAD_3D")
class Load3D(ComfyTypeIO):
    Type = Model3DDict

@comfytype(io_type="LOAD_3D_ANIMATION")
class Load3DAnimation(Load3D):
    ...

@comfytype(io_type="POINT")
class Point(ComfyTypeIO):
    Type = Any # NOTE: comment should not leak into extracted type hints

@comfytype(io_type="HISTOGRAM")
class Histogram(ComfyTypeIO):
    Type = list[int]

    def __init__(self, unique_id: str, prompt: object):
        pass

class Hidden(str, Enum):
    unique_id = "UNIQUE_ID"
    '''Unique node identifier.'''
    prompt = "PROMPT"
    extra_pnginfo = "EXTRA_PNGINFO"
    auth_token_comfy_org = "AUTH_TOKEN_COMFY_ORG"
    api_key_comfy_org = "API_KEY_COMFY_ORG"

@dataclass
class NodeInfoV1:
    input: dict=None
    display_name: str=None
    category: str=None
    api_node: bool=None

@dataclass
class PriceBadgeDepends:
    widgets: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)

@dataclass
class PriceBadge:
    expr: str
    depends_on: PriceBadgeDepends = field(default_factory=PriceBadgeDepends)
    engine: str = field(default="jsonata")

@dataclass
class Schema:
    node_id: str
    '''ID of node.'''
    display_name: str = None
    category: str = "sd"
    inputs: list[Input] = field(default_factory=list)
    outputs: list[Output] = field(default_factory=list)
    hidden: list[Hidden] = field(default_factory=list)
    is_output_node: bool=False
    is_api_node: bool=False
    price_badge: PriceBadge | None = None
    maybe_flag: bool | None = None

    def finalize(self):
        if self.is_api_node:
            if Hidden.auth_token_comfy_org not in self.hidden:
                self.hidden.append(Hidden.auth_token_comfy_org)
            if Hidden.api_key_comfy_org not in self.hidden:
                self.hidden.append(Hidden.api_key_comfy_org)
        if self.is_output_node:
            if Hidden.prompt not in self.hidden:
                self.hidden.append(Hidden.prompt)
            if Hidden.extra_pnginfo not in self.hidden:
                self.hidden.append(Hidden.extra_pnginfo)

    def get_v1_info(self, cls) -> NodeInfoV1:
        return NodeInfoV1()
"""

_BASIC_TYPES_SAMPLE_FULL = '''\
ImageInput = torch.Tensor
"""
An image in format [B, H, W, C]
"""

MaskInput = torch.Tensor
"""
A mask in format [B, H, W]
"""

class AudioInput(TypedDict):
    """
    TypedDict representing audio input.
    """

    waveform: torch.Tensor
    """
    Tensor in format [B, C, T].
    """

    sample_rate: int
'''


def _load_validate_schema():
    return load_module("validate_schema", REPO_ROOT / "scripts" / "verify" / "validate_schema.py")


def _load_parse_node_api_schema():
    return load_module("parse_node_api_schema", SCRIPT)


def _run_parse_node_api_schema_main(
    server_path: Path,
    io_path: Path,
    basic_types_path: Path,
    *extra_args: str,
):
    module = _load_parse_node_api_schema()
    return call_main(
        module,
        str(server_path),
        str(io_path),
        str(basic_types_path),
        *extra_args,
    )


class ParseNodeApiSchemaTests(unittest.TestCase):
    def test_requires_arguments(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    # -- Focused extraction tests (decomposed from former monolithic test) --

    def test_extract_object_info_fields_returns_expected_keys(self):
        module = _load_parse_node_api_schema()
        fields = module.extract_object_info_fields(_SERVER_SAMPLE_FULL)
        self.assertIn("input", fields)
        self.assertIn("display_name", fields)
        self.assertIn("price_badge", fields)

    def test_extract_io_types_core_cases(self):
        module = _load_parse_node_api_schema()
        with tempfile.TemporaryDirectory() as tmp:
            io_path = Path(tmp) / "_io.py"
            io_path.write_text(_IO_SAMPLE_FULL, encoding="utf-8")
            io_types = module.extract_io_types(_IO_SAMPLE_FULL, str(io_path))
            by_io_type = {entry["io_type"]: entry for entry in io_types}

            cases = [
                (
                    "boolean input metadata",
                    "BOOLEAN",
                    lambda entry: (
                        self.assertEqual(entry["input_class"], "WidgetInput"),
                        self.assertIn("default", entry["input_parameters"]),
                        self.assertEqual(entry["input_parameter_details"][0]["name"], "default"),
                        self.assertEqual(entry["input_parameter_details"][0]["type_hint"], "bool"),
                        self.assertEqual(entry["type_hint"], "bool"),
                        self.assertTrue(entry["is_widget"]),
                        self.assertEqual(entry["defined_in"], str(io_path).replace("\\", "/")),
                    ),
                ),
                (
                    "string output metadata",
                    "STRING",
                    lambda entry: (
                        self.assertEqual(entry["type_hint"], "str"),
                        self.assertEqual(
                            entry["output_parameters"],
                            ["display_name", "tooltip", "is_output_list"],
                        ),
                    ),
                ),
                (
                    "inherited type hint",
                    "LOAD_3D_ANIMATION",
                    lambda entry: self.assertEqual(entry["type_hint"], "Model3DDict"),
                ),
                (
                    "comment-stripped type hint",
                    "POINT",
                    lambda entry: self.assertEqual(entry["type_hint"], "Any"),
                ),
                (
                    "no input class",
                    "HISTOGRAM",
                    lambda entry: (
                        self.assertEqual(entry["input_class"], None),
                        self.assertEqual(entry["input_parameters"], []),
                    ),
                ),
            ]

            for name, io_type, assert_entry in cases:
                with self.subTest(name=name):
                    assert_entry(by_io_type[io_type])

    def test_extract_basic_input_shapes_captures_docstring(self):
        module = _load_parse_node_api_schema()
        shapes = module.extract_basic_input_shapes(_BASIC_TYPES_SAMPLE_FULL)
        self.assertEqual(shapes["ImageInput"], "An image in format [B, H, W, C]")

    def test_extract_v3_schema_contract_captures_dataclass_fields(self):
        module = _load_parse_node_api_schema()
        contract = module.extract_v3_schema_contract(_IO_SAMPLE_FULL, "sample/_io.py")

        self.assertEqual(contract["contract_version"], "3.0")
        schema_fields = {field["name"]: field for field in contract["schema_fields"]}
        for name in [
            "node_id",
            "display_name",
            "category",
            "inputs",
            "outputs",
            "is_output_node",
            "is_api_node",
        ]:
            self.assertIn(name, schema_fields)
            self.assertEqual(schema_fields[name]["defined_in"], "sample/_io.py")
            self.assertIn("traceability", schema_fields[name])

        self.assertEqual(schema_fields["node_id"]["type_hint"], "str")
        self.assertTrue(schema_fields["node_id"]["required"])
        self.assertEqual(schema_fields["node_id"]["description"], "ID of node.")
        self.assertEqual(schema_fields["inputs"]["default_factory"], "list")

        node_info_fields = {field["name"] for field in contract["node_info_fields"]}
        self.assertIn("display_name", node_info_fields)
        self.assertIn("api_node", node_info_fields)

        badge_fields = {
            item["class_name"]: {field["name"] for field in item["fields"]}
            for item in contract["price_badge_contract"]
        }
        self.assertIn("expr", badge_fields["PriceBadge"])
        self.assertIn("widgets", badge_fields["PriceBadgeDepends"])

    def test_extract_v3_schema_contract_captures_hidden_values_and_node_flags(self):
        module = _load_parse_node_api_schema()
        contract = module.extract_v3_schema_contract(_IO_SAMPLE_FULL, "sample/_io.py")

        hidden_names = {entry["name"] for entry in contract["hidden_values"]["hidden_enum"]}
        self.assertIn("auth_token_comfy_org", hidden_names)

        injections = {
            entry["condition"]: entry["injected"]
            for entry in contract["hidden_values"]["hidden_auto_injection"]
        }
        self.assertEqual(
            injections["is_api_node"],
            ["auth_token_comfy_org", "api_key_comfy_org"],
        )
        self.assertEqual(injections["is_output_node"], ["prompt", "extra_pnginfo"])

        schema_field_names = {field["name"] for field in contract["schema_fields"]}
        self.assertEqual(
            contract["node_flags"],
            [
                {"name": "is_output_node", "schema_fields_ref": "is_output_node"},
                {"name": "is_api_node", "schema_fields_ref": "is_api_node"},
            ],
        )
        self.assertNotIn(
            "maybe_flag",
            {entry["name"] for entry in contract["node_flags"]},
        )
        for entry in contract["node_flags"]:
            self.assertEqual(set(entry), {"name", "schema_fields_ref"})
            self.assertIn(entry["schema_fields_ref"], schema_field_names)

    def test_partial_hidden_auto_injection_adds_deferred_coverage_note(self):
        module = _load_parse_node_api_schema()
        deferred = []
        contract = module.extract_v3_schema_contract(
            """
from dataclasses import dataclass

@dataclass
class Schema:
    is_api_node: bool = False

    def finalize(self):
        if self.is_api_node:
            self.hidden.append(Hidden.auth_token)
""",
            "sample/_io.py",
            coverage_deferred=deferred,
        )

        self.assertEqual(
            contract["hidden_values"]["hidden_auto_injection"],
            [{"condition": "is_api_node", "injected": ["auth_token"]}],
        )
        self.assertTrue(
            any("Schema.finalize" in note and "hidden_auto_injection" in note for note in deferred),
            msg=deferred,
        )

    def test_output_only_hidden_auto_injection_is_extracted_with_partial_note(self):
        module = _load_parse_node_api_schema()
        deferred = []
        contract = module.extract_v3_schema_contract(
            """
from dataclasses import dataclass

@dataclass
class Schema:
    is_api_node: bool = False
    is_output_node: bool = False

    def finalize(self):
        if self.is_output_node:
            self.hidden.append(Hidden.prompt)
            self.hidden.append(Hidden.extra_pnginfo)
""",
            "sample/_io.py",
            coverage_deferred=deferred,
        )

        self.assertEqual(
            contract["hidden_values"]["hidden_auto_injection"],
            [{"condition": "is_output_node", "injected": ["prompt", "extra_pnginfo"]}],
        )
        self.assertTrue(
            any("is_api_node" in note and "hidden_auto_injection" in note for note in deferred),
            msg=deferred,
        )

    def test_extract_v3_schema_contract_empty_when_no_v3_dataclasses_exist(self):
        module = _load_parse_node_api_schema()
        contract = module.extract_v3_schema_contract("class NotSchema: pass", "sample/_io.py")

        self.assertEqual(contract["contract_version"], "3.0")
        self.assertEqual(contract["schema_fields"], [])
        self.assertEqual(contract["node_info_fields"], [])

    def test_extract_typed_input_shapes_audio(self):
        module = _load_parse_node_api_schema()
        with tempfile.TemporaryDirectory() as tmp:
            basic_path = Path(tmp) / "basic_types.py"
            basic_path.write_text(_BASIC_TYPES_SAMPLE_FULL, encoding="utf-8")
            typed = module.extract_typed_input_shapes(_BASIC_TYPES_SAMPLE_FULL, str(basic_path))

            self.assertIn("AudioInput", typed)
            audio = typed["AudioInput"]
            self.assertEqual(audio["description"], "TypedDict representing audio input.")
            self.assertEqual(
                audio["defined_in"],
                str(basic_path).replace("\\", "/"),
            )
            self.assertIn("waveform", audio["fields"])
            self.assertEqual(audio["fields"]["waveform"]["type"], "torch.Tensor")
            self.assertIn(
                "Tensor in format [B, C, T].",
                audio["fields"]["waveform"]["description"],
            )
            self.assertEqual(
                audio["fields"]["waveform"]["traceability"]["strategy"],
                "typed_dict_field",
            )

    def test_full_pipeline_produces_schema_valid_output(self):
        """Integration test: the full extraction pipeline produces
        schema-valid output with all required top-level sections."""
        module = _load_parse_node_api_schema()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            io_path = tmp_path / "_io.py"
            basic_types_path = tmp_path / "basic_types.py"
            io_path.write_text(_IO_SAMPLE_FULL, encoding="utf-8")
            basic_types_path.write_text(_BASIC_TYPES_SAMPLE_FULL, encoding="utf-8")

            data = {
                "metadata": {
                    "sources": ["tmp/server.py", "tmp/_io.py", "tmp/basic_types.py"],
                    "extracted_date": "2026-05-03",
                    "version": "v-test",
                    "commit": "abc123",
                    "provenance": {
                        "mode": "source-only",
                        "source_sections": [
                            "object_info_fields",
                            "io_types",
                            "basic_input_shapes",
                            "typed_input_shapes",
                            "v3_schema_contract",
                        ],
                        "runtime_sections": [],
                    },
                },
                "object_info_fields": module.extract_object_info_fields(_SERVER_SAMPLE_FULL),
                "io_types": module.extract_io_types(_IO_SAMPLE_FULL, str(io_path)),
                "basic_input_shapes": module.extract_basic_input_shapes(_BASIC_TYPES_SAMPLE_FULL),
                "typed_input_shapes": module.extract_typed_input_shapes(
                    _BASIC_TYPES_SAMPLE_FULL, str(basic_types_path)
                ),
                "v3_schema_contract": module.extract_v3_schema_contract(
                    _IO_SAMPLE_FULL, str(io_path)
                ),
                "coverage": {
                    "description": "test",
                    "sources_covered": ["tmp/server.py"],
                    "runtime_enriched": False,
                    "best_effort_fields": ["v3_schema_contract.schema_fields"],
                    "deferred": [],
                },
            }

            self.assertEqual(data["metadata"]["version"], "v-test")
            self.assertIn("metadata", data)
            self.assertIn("object_info_fields", data)
            self.assertIn("io_types", data)
            self.assertIn("basic_input_shapes", data)
            self.assertIn("typed_input_shapes", data)
            self.assertIn("v3_schema_contract", data)
            for entry in data["io_types"]:
                for key in (
                    "io_type",
                    "class_name",
                    "input_class",
                    "input_parameters",
                    "input_parameter_details",
                    "type_hint",
                    "is_widget",
                    "defined_in",
                ):
                    self.assertIn(key, entry)

            validate_schema = _load_validate_schema()
            errors = validate_schema.validate_top_level(
                data,
                validate_schema.SCHEMAS["node_api_schema.json"],
                "node_api_schema.json",
            )
            errors.extend(validate_schema.validate_metadata(data, "node_api_schema.json"))
            errors.extend(validate_schema.validate_io_types(data, "node_api_schema.json"))
            errors.extend(validate_schema.validate_typed_input_shapes(data, "node_api_schema.json"))
            errors.extend(validate_schema.validate_v3_schema_contract(data, "node_api_schema.json"))
            self.assertEqual(errors, [], msg=f"Schema errors: {errors}")

    def test_metadata_sources_and_defined_in_are_repo_relative_when_inputs_are_in_repo(self):
        server_sample = """
def node_info(node_class):
    info = {}
    info['input'] = obj_class.INPUT_TYPES()
    return info
"""
        io_sample = """
@comfytype(io_type="BOOLEAN")
class Boolean(ComfyTypeIO):
    Type = bool
"""
        basic_types_sample = '''
ImageInput = torch.Tensor
"""An image tensor."""
'''

        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            tmp_path = Path(tmp)
            server_path = tmp_path / "server.py"
            io_path = tmp_path / "_io.py"
            basic_types_path = tmp_path / "basic_types.py"
            out_path = tmp_path / "node_api_schema.json"
            server_path.write_text(server_sample, encoding="utf-8")
            io_path.write_text(io_sample, encoding="utf-8")
            basic_types_path.write_text(basic_types_sample, encoding="utf-8")

            exit_code, _stdout, stderr = _run_parse_node_api_schema_main(
                server_path,
                io_path,
                basic_types_path,
                "--output",
                str(out_path),
            )

            self.assertEqual(exit_code, 0, msg=stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(
                data["metadata"]["sources"],
                [
                    server_path.relative_to(REPO_ROOT).as_posix(),
                    io_path.relative_to(REPO_ROOT).as_posix(),
                    basic_types_path.relative_to(REPO_ROOT).as_posix(),
                ],
            )
            self.assertEqual(
                data["io_types"][0]["defined_in"],
                io_path.relative_to(REPO_ROOT).as_posix(),
            )
            self.assertEqual(
                data["typed_input_shapes"],
                {},
            )

    def test_prompt_conditioning_surface_summarizes_source_and_runtime_metadata(self):
        module = _load_parse_node_api_schema()

        io_types = [
            {
                "io_type": "STRING",
                "class_name": "String",
                "input_class": "WidgetInput",
                "input_parameters": ["multiline", "default"],
                "output_parameters": ["display_name"],
                "input_parameter_details": [
                    {"name": "multiline", "default": False},
                    {"name": "default", "type_hint": "str"},
                ],
                "output_parameter_details": [{"name": "display_name", "type_hint": "str"}],
                "type_hint": "str",
                "defined_in": "references/snapshots/comfy_api/latest/_io.py",
                "is_widget": True,
            },
            {
                "io_type": "CONDITIONING",
                "class_name": "Conditioning",
                "input_class": None,
                "input_parameters": [],
                "output_parameters": [],
                "input_parameter_details": [],
                "output_parameter_details": [],
                "type_hint": "CondList",
                "defined_in": "references/snapshots/comfy_api/latest/_io.py",
                "is_widget": False,
            },
        ]
        runtime_object_info = {
            "CLIPTextEncode": {
                "input": {"required": {"text": ["STRING"], "clip": ["CLIP"]}},
                "output": ["CONDITIONING"],
            },
            "PreviewText": {
                "input": {"required": {"text": ["STRING"]}},
                "output": ["STRING"],
            },
        }

        surface = module.build_prompt_conditioning_surface(io_types, runtime_object_info)

        self.assertEqual(surface["traceability"]["source_type"], "source-backed")
        self.assertEqual(
            surface["text_input_io_types"][0],
            {
                "io_type": "STRING",
                "class_name": "String",
                "type_hint": "str",
                "is_widget": True,
                "input_parameters": ["multiline", "default"],
                "supports_multiline_parameter": True,
                "output_parameters": ["display_name"],
                "defined_in": "references/snapshots/comfy_api/latest/_io.py",
            },
        )
        self.assertEqual(
            surface["conditioning_io_types"][0],
            {
                "io_type": "CONDITIONING",
                "class_name": "Conditioning",
                "type_hint": "CondList",
                "is_widget": False,
                "input_parameters": [],
                "output_parameters": [],
                "defined_in": "references/snapshots/comfy_api/latest/_io.py",
            },
        )
        # Base-key parity: text_input and conditioning entries must share
        # the same base key set. ``supports_multiline_parameter`` is
        # allowed as a STRING-specific extension (set to True/False for
        # text widgets) and is not present on CONDITIONING entries.
        base_keys = {
            "io_type",
            "class_name",
            "type_hint",
            "is_widget",
            "input_parameters",
            "output_parameters",
            "defined_in",
        }
        text_keys = set(surface["text_input_io_types"][0].keys())
        cond_keys = set(surface["conditioning_io_types"][0].keys())
        self.assertEqual(
            text_keys - {"supports_multiline_parameter"},
            base_keys,
            f"text_input_io_types[0] must have all base keys, got {text_keys}",
        )
        self.assertEqual(
            cond_keys,
            base_keys,
            f"conditioning_io_types[0] must have all base keys, got {cond_keys}",
        )
        self.assertEqual(
            surface["runtime_node_output_summary"],
            [
                {
                    "class_name": "CLIPTextEncode",
                    "input_names": ["clip", "text"],
                    "input_types": {"clip": ["CLIP"], "text": ["STRING"]},
                    "output_types": ["CONDITIONING"],
                    "output_includes_conditioning": True,
                },
                {
                    "class_name": "PreviewText",
                    "input_names": ["text"],
                    "input_types": {"text": ["STRING"]},
                    "output_types": ["STRING"],
                    "output_includes_conditioning": False,
                },
            ],
        )

    def test_prompt_conditioning_surface_source_only_mode(self):
        """Source-only mode (no runtime_object_info) must still
        return text and conditioning entries with empty runtime fields."""
        module = _load_parse_node_api_schema()

        io_types = [
            {
                "io_type": "STRING",
                "class_name": "String",
                "input_class": "WidgetInput",
                "input_parameters": ["multiline"],
                "output_parameters": ["display_name"],
                "input_parameter_details": [{"name": "multiline", "default": False}],
                "output_parameter_details": [{"name": "display_name", "type_hint": "str"}],
                "type_hint": "str",
                "defined_in": "references/snapshots/comfy_api/latest/_io.py",
                "is_widget": True,
            },
            {
                "io_type": "CONDITIONING",
                "class_name": "Conditioning",
                "input_class": None,
                "input_parameters": [],
                "output_parameters": [],
                "input_parameter_details": [],
                "output_parameter_details": [],
                "type_hint": "CondList",
                "defined_in": "references/snapshots/comfy_api/latest/_io.py",
                "is_widget": False,
            },
        ]

        surface = module.build_prompt_conditioning_surface(io_types, None)

        self.assertEqual(surface["runtime_node_output_summary"], [])
        self.assertEqual(surface["traceability"]["runtime_bounded_sections"], [])
        self.assertEqual(surface["traceability"]["source_type"], "source-backed")
        # Both text and conditioning entries must still be extracted
        # even when no runtime snapshot is provided.
        self.assertEqual(len(surface["text_input_io_types"]), 1)
        self.assertEqual(len(surface["conditioning_io_types"]), 1)
        # Base-key parity (source-only mode): text and conditioning
        # entries must share the same key set, with STRING-specific
        # extension.
        base_keys = {
            "io_type",
            "class_name",
            "type_hint",
            "is_widget",
            "input_parameters",
            "output_parameters",
            "defined_in",
        }
        text_keys = set(surface["text_input_io_types"][0].keys())
        cond_keys = set(surface["conditioning_io_types"][0].keys())
        self.assertEqual(text_keys - {"supports_multiline_parameter"}, base_keys)
        self.assertEqual(cond_keys, base_keys)

    def test_prompt_conditioning_surface_empty_dict_distinct_from_none(self):
        """Empty dict ``{}`` must be treated as runtime-data-provided
        (distinct from ``None``), populating ``runtime_bounded_sections``
        even though ``runtime_node_output_summary`` is empty."""
        module = _load_parse_node_api_schema()

        io_types = [
            {
                "io_type": "STRING",
                "class_name": "String",
                "input_parameters": ["multiline"],
                "output_parameters": ["display_name"],
                "type_hint": "str",
                "defined_in": "references/snapshots/comfy_api/latest/_io.py",
                "is_widget": True,
            }
        ]

        surface = module.build_prompt_conditioning_surface(io_types, {})

        self.assertEqual(surface["runtime_node_output_summary"], [])
        self.assertEqual(
            surface["traceability"]["runtime_bounded_sections"],
            ["runtime_node_output_summary"],
            "runtime_bounded_sections must be populated when runtime data is provided, even if empty",
        )

    def test_prompt_conditioning_surface_empty_io_types(self):
        """Empty io_types list produces empty text_input and conditioning arrays
        while runtime_node_output_summary still populates from runtime_object_info."""
        module = _load_parse_node_api_schema()

        io_types: list = []
        runtime_object_info = {
            "CLIPTextEncode": {
                "input": {"required": {"text": ["STRING", {"multiline": True}]}},
                "output": ["CONDITIONING"],
            }
        }

        surface = module.build_prompt_conditioning_surface(io_types, runtime_object_info)
        self.assertEqual(surface["text_input_io_types"], [])
        self.assertEqual(surface["conditioning_io_types"], [])
        self.assertEqual(len(surface["runtime_node_output_summary"]), 1)
        self.assertEqual(surface["runtime_node_output_summary"][0]["class_name"], "CLIPTextEncode")

    def test_prompt_conditioning_surface_string_without_multiline(self):
        """STRING entry without 'multiline' in input_parameters must have
        supports_multiline_parameter=False."""
        module = _load_parse_node_api_schema()

        io_types = [
            {
                "io_type": "STRING",
                "class_name": "String",
                "input_parameters": ["default"],
                "output_parameters": [],
                "is_widget": True,
                "type_hint": "str",
                "defined_in": "references/snapshots/comfy_api/latest/_io.py",
            }
        ]

        surface = module.build_prompt_conditioning_surface(io_types)
        self.assertEqual(len(surface["text_input_io_types"]), 1)
        self.assertFalse(surface["text_input_io_types"][0]["supports_multiline_parameter"])

    def test__runtime_input_type_variants(self):
        """Direct unit coverage for _runtime_input_type helper function."""
        module = _load_parse_node_api_schema()

        # Bare string -> list with one element
        self.assertEqual(module._runtime_input_type("STRING"), ["STRING"])

        # List of strings -> first element wrapped
        self.assertEqual(module._runtime_input_type(["STRING"]), ["STRING"])

        # List with a dict variant -> first string element extracted
        self.assertEqual(module._runtime_input_type(["STRING", {"multiline": True}]), ["STRING"])

        # Empty list -> empty list
        self.assertEqual(module._runtime_input_type([]), [])

        # Non-list, non-str -> empty list
        self.assertEqual(module._runtime_input_type(42), [])

    def test__runtime_input_types_variants(self):
        """Direct unit coverage for _runtime_input_types helper function.
        The function extracts ``input_info = node_info.get("input", {})``
        first, so test fixtures must wrap sections under ``input``."""
        module = _load_parse_node_api_schema()

        # Normal node_info dict with input key wrapping sections
        node_info = {
            "input": {
                "required": {"prompt": ["STRING", {"multiline": True}]},
                "optional": {"negative": ["STRING", {"multiline": True}]},
                "hidden": {"seed": ["INT"]},
            }
        }
        result = module._runtime_input_types(node_info)
        self.assertEqual(result, {"prompt": ["STRING"], "negative": ["STRING"], "seed": ["INT"]})

        # Empty input dict
        self.assertEqual(module._runtime_input_types({}), {})

        # Non-dict input value in node_info
        node_info_with_bad = {
            "input": {
                "required": {"prompt": ["STRING"]},
                "optional": "not_a_dict",
                "hidden": {},
            }
        }
        result = module._runtime_input_types(node_info_with_bad)
        self.assertEqual(result, {"prompt": ["STRING"]})

    def test_bracket_aware_parameter_parsing(self):
        """Parameters with nested generic types like Dict[str, List[float]] should not produce bogus names."""
        # Import the module directly to test parse_parameters
        module = _load_parse_node_api_schema()

        # Test cases: (input, expected_names)
        test_cases = [
            # Simple case - should work as before
            ("name: str, default: bool", ["name", "default"]),
            # Nested generic with comma - should NOT split inside brackets
            ("config: Dict[str, List[float]], timeout: int", ["config", "timeout"]),
            # Multiple nested generics
            ("mapping: Dict[str, Tuple[int, str]], data: Any", ["mapping", "data"]),
            # Optional with Union
            ("value: Optional[Union[str, int]]", ["value"]),
            # Realistic signature from CurveInput
            (
                "display_name: str, default: CurveInput_=None, socketless: bool=False, optional: bool=False, tooltip: str=None",
                ["display_name", "default", "socketless", "optional", "tooltip"],
            ),
            # This is the actual bug case - float]] should not appear
            (
                "display_name: str, default: CurveInput_=None, socketless: bool=True",
                ["display_name", "default", "socketless"],
            ),
        ]

        for sig_text, expected in test_cases:
            result = module.parse_parameters(sig_text)
            self.assertEqual(result, expected, f"Failed for: {sig_text}")

    def test_match_type_without_top_level_type_remains_null(self):
        module = _load_parse_node_api_schema()

        io_sample = """
@comfytype(io_type="COMFY_MATCHTYPE_V3")
class MatchType(ComfyTypeIO):
    class Template:
        def __init__(self, template_id: str):
            self.template_id = template_id

    class Input(Input):
        def __init__(self, id: str, template: MatchType.Template):
            pass
"""

        io_types = module.extract_io_types(io_sample, "sample/_io.py")
        self.assertEqual(io_types[0]["type_hint"], None)

    def test_parameter_details_capture_literal_choices(self):
        module = _load_parse_node_api_schema()

        details = module.parse_parameter_details(
            'control_after_refresh: Literal["first", "last"]="first", timeout: int=None'
        )
        self.assertEqual(details[0]["name"], "control_after_refresh")
        self.assertEqual(details[0]["allowed_values"], ["first", "last"])
        self.assertEqual(details[0]["default"], "first")

    def test_hybrid_mode_merges_runtime_snapshot(self):
        server_sample = """
def node_info(node_class):
    info = {}
    info['input'] = obj_class.INPUT_TYPES()
    return info
"""
        io_sample = """
@comfytype(io_type="BOOLEAN")
class Boolean(ComfyTypeIO):
    Type = bool
    class Input(WidgetInput):
        def __init__(self, id: str, default: bool=None):
            pass
"""
        basic_types_sample = '''
ImageInput = torch.Tensor
"""An image tensor."""
'''
        runtime_snapshot = {
            "metadata": {
                "url": "http://127.0.0.1:8188",
                "version": "v0.19.3",
                "commit": "abc123",
                "extracted_date": "2026-04-22",
                "response_sha256": "deadbeef",
            },
            "object_info": {
                "KSampler": {
                    "input": {},
                    "output": ["LATENT"],
                }
            },
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            server_path = tmp_path / "server.py"
            io_path = tmp_path / "_io.py"
            basic_types_path = tmp_path / "basic_types.py"
            runtime_path = tmp_path / "object_info_runtime.json"
            out_path = tmp_path / "node_api_schema.json"
            server_path.write_text(server_sample, encoding="utf-8")
            io_path.write_text(io_sample, encoding="utf-8")
            basic_types_path.write_text(basic_types_sample, encoding="utf-8")
            runtime_path.write_text(json.dumps(runtime_snapshot), encoding="utf-8")

            exit_code, _stdout, stderr = _run_parse_node_api_schema_main(
                server_path,
                io_path,
                basic_types_path,
                "--version",
                "v-test",
                "--commit",
                "abc123",
                "--object-info-runtime-path",
                str(runtime_path),
                "--output",
                str(out_path),
            )

            self.assertEqual(exit_code, 0, msg=stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))

            # Provenance metadata
            self.assertIn("provenance", data["metadata"])
            self.assertEqual(data["metadata"]["provenance"]["mode"], "hybrid")
            self.assertIn("source_sections", data["metadata"]["provenance"])
            self.assertIn("runtime_sections", data["metadata"]["provenance"])
            self.assertIn("runtime_object_info", data["metadata"]["provenance"]["runtime_sections"])

            # Runtime data merged
            self.assertIn("runtime_object_info", data)
            self.assertEqual(data["runtime_object_info"]["KSampler"]["output"], ["LATENT"])

            # Coverage reflects hybrid mode
            self.assertTrue(data["coverage"]["runtime_enriched"])
            self.assertNotIn("runtime /object_info response", data["coverage"]["deferred"])

            # Schema validation passes
            validate_schema = _load_validate_schema()
            errors = validate_schema.validate_top_level(
                data, validate_schema.SCHEMAS["node_api_schema.json"], "node_api_schema.json"
            )
            errors.extend(validate_schema.validate_metadata(data, "node_api_schema.json"))
            errors.extend(validate_schema.validate_io_types(data, "node_api_schema.json"))
            errors.extend(validate_schema.validate_typed_input_shapes(data, "node_api_schema.json"))
            self.assertEqual(errors, [], msg=f"Schema errors: {errors}")

    def test_source_only_mode_no_runtime_sections(self):
        server_sample = """
def node_info(node_class):
    info = {}
    info['input'] = obj_class.INPUT_TYPES()
    return info
"""
        io_sample = """
@comfytype(io_type="BOOLEAN")
class Boolean(ComfyTypeIO):
    Type = bool
    class Input(WidgetInput):
        def __init__(self, id: str, default: bool=None):
            pass
"""
        basic_types_sample = '''
ImageInput = torch.Tensor
"""An image tensor."""
'''

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            server_path = tmp_path / "server.py"
            io_path = tmp_path / "_io.py"
            basic_types_path = tmp_path / "basic_types.py"
            out_path = tmp_path / "node_api_schema.json"
            server_path.write_text(server_sample, encoding="utf-8")
            io_path.write_text(io_sample, encoding="utf-8")
            basic_types_path.write_text(basic_types_sample, encoding="utf-8")

            exit_code, _stdout, stderr = _run_parse_node_api_schema_main(
                server_path,
                io_path,
                basic_types_path,
                "--version",
                "v-test",
                "--commit",
                "abc123",
                "--output",
                str(out_path),
            )

            self.assertEqual(exit_code, 0, msg=stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))

            self.assertEqual(data["metadata"]["provenance"]["mode"], "source-only")
            self.assertNotIn("runtime_object_info", data)
            self.assertFalse(data["coverage"]["runtime_enriched"])

    def test_hybrid_mode_with_runtime_snapshot_missing_object_info_stays_bounded(self):
        server_sample = """
def node_info(node_class):
    info = {}
    info['input'] = obj_class.INPUT_TYPES()
    return info
"""
        io_sample = """
@comfytype(io_type="BOOLEAN")
class Boolean(ComfyTypeIO):
    Type = bool
"""
        basic_types_sample = '''
ImageInput = torch.Tensor
"""An image tensor."""
'''
        runtime_snapshot = {
            "metadata": {
                "url": "http://127.0.0.1:8188",
                "version": "v0.19.3",
                "commit": "abc123",
                "extracted_date": "2026-04-22",
                "response_sha256": "deadbeef",
            },
            "unexpected": {"value": True},
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            server_path = tmp_path / "server.py"
            io_path = tmp_path / "_io.py"
            basic_types_path = tmp_path / "basic_types.py"
            runtime_path = tmp_path / "object_info_runtime.json"
            out_path = tmp_path / "node_api_schema.json"
            server_path.write_text(server_sample, encoding="utf-8")
            io_path.write_text(io_sample, encoding="utf-8")
            basic_types_path.write_text(basic_types_sample, encoding="utf-8")
            runtime_path.write_text(json.dumps(runtime_snapshot), encoding="utf-8")

            exit_code, _stdout, stderr = _run_parse_node_api_schema_main(
                server_path,
                io_path,
                basic_types_path,
                "--object-info-runtime-path",
                str(runtime_path),
                "--output",
                str(out_path),
            )

            self.assertEqual(exit_code, 0, msg=stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(data["metadata"]["provenance"]["mode"], "hybrid")
            self.assertTrue(data["coverage"]["runtime_enriched"])
            self.assertEqual(data["runtime_object_info"], {})

    def test_custom_output_path_writes_outside_canonical_reference(self):
        server_sample = """
def node_info(node_class):
    info = {}
    info['input'] = obj_class.INPUT_TYPES()
    return info
"""
        io_sample = """
@comfytype(io_type="BOOLEAN")
class Boolean(ComfyTypeIO):
    Type = bool
    class Input(WidgetInput):
        def __init__(self, id: str, default: bool=None):
            pass
"""
        basic_types_sample = '''
ImageInput = torch.Tensor
"""An image tensor."""
'''

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            server_path = tmp_path / "server.py"
            io_path = tmp_path / "_io.py"
            basic_types_path = tmp_path / "basic_types.py"
            output_path = tmp_path / "artifacts" / "node_api_schema_runtime.json"
            server_path.write_text(server_sample, encoding="utf-8")
            io_path.write_text(io_sample, encoding="utf-8")
            basic_types_path.write_text(basic_types_sample, encoding="utf-8")

            exit_code, stdout, stderr = _run_parse_node_api_schema_main(
                server_path,
                io_path,
                basic_types_path,
                "--version",
                "v-test",
                "--commit",
                "abc123",
                "--output",
                str(output_path),
            )

            self.assertEqual(exit_code, 0, msg=stderr)
            self.assertTrue(output_path.exists())
            data = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(data["metadata"]["version"], "v-test")
            # Script output redacts the absolute user path; only the basename appears.
            self.assertIn(output_path.name, stdout)


if __name__ == "__main__":
    unittest.main()
