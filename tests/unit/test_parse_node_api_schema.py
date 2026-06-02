import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.unit.helpers.extractor_test_utils import call_main, load_module

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "extract" / "parse_node_api_schema.py"


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

    def test_extracts_object_info_and_io_types(self):
        server_sample = """
def node_info(node_class):
    info = {}
    info['input'] = obj_class.INPUT_TYPES()
    info['output'] = obj_class.RETURN_TYPES
    info['display_name'] = node_class
    info['category'] = 'sd'
    info['search_aliases'] = []
    return info
"""

        io_sample = """
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
"""

        basic_types_sample = '''
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

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            io_path = tmp_path / "_io.py"
            basic_types_path = tmp_path / "basic_types.py"
            io_path.write_text(io_sample, encoding="utf-8")
            basic_types_path.write_text(basic_types_sample, encoding="utf-8")

            parse_node_api_schema = _load_parse_node_api_schema()
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
                        ],
                        "runtime_sections": [],
                    },
                },
                "object_info_fields": parse_node_api_schema.extract_object_info_fields(
                    server_sample
                ),
                "io_types": parse_node_api_schema.extract_io_types(io_sample, str(io_path)),
                "basic_input_shapes": parse_node_api_schema.extract_basic_input_shapes(
                    basic_types_sample
                ),
                "typed_input_shapes": parse_node_api_schema.extract_typed_input_shapes(
                    basic_types_sample, str(basic_types_path)
                ),
                "coverage": {
                    "description": (
                        "Extracted from pinned source files only. "
                        "Runtime-only data such as per-node INPUT_TYPES schemas and custom node types are deferred beyond pinned-snapshot extraction."
                    ),
                    "sources_covered": ["tmp/server.py", "tmp/_io.py", "tmp/basic_types.py"],
                    "runtime_enriched": False,
                    "deferred": [
                        "runtime /object_info response",
                        "custom node definitions",
                        "per-node INPUT_TYPES schemas",
                    ],
                },
            }

            self.assertEqual(data["metadata"]["version"], "v-test")
            self.assertEqual(data["metadata"]["commit"], "abc123")
            self.assertIn("input", data["object_info_fields"])
            self.assertIn("display_name", data["object_info_fields"])

            io_types = {entry["io_type"]: entry for entry in data["io_types"]}
            self.assertIn("BOOLEAN", io_types)
            self.assertEqual(io_types["BOOLEAN"]["input_class"], "WidgetInput")
            self.assertIn("default", io_types["BOOLEAN"]["input_parameters"])
            self.assertEqual(io_types["BOOLEAN"]["input_parameter_details"][0]["name"], "default")
            self.assertEqual(io_types["BOOLEAN"]["input_parameter_details"][0]["type_hint"], "bool")
            self.assertEqual(io_types["BOOLEAN"]["type_hint"], "bool")
            self.assertTrue(io_types["BOOLEAN"]["is_widget"])
            self.assertEqual(io_types["BOOLEAN"]["defined_in"], str(io_path).replace("\\", "/"))

            self.assertEqual(io_types["STRING"]["type_hint"], "str")
            self.assertEqual(
                io_types["STRING"]["output_parameters"],
                ["display_name", "tooltip", "is_output_list"],
            )
            self.assertEqual(io_types["LOAD_3D_ANIMATION"]["type_hint"], "Model3DDict")
            self.assertEqual(io_types["POINT"]["type_hint"], "Any")
            self.assertEqual(io_types["HISTOGRAM"]["input_class"], None)
            self.assertEqual(io_types["HISTOGRAM"]["input_parameters"], [])

            self.assertEqual(
                data["basic_input_shapes"]["ImageInput"], "An image in format [B, H, W, C]"
            )
            self.assertIn("AudioInput", data["typed_input_shapes"])
            self.assertEqual(
                data["typed_input_shapes"]["AudioInput"]["description"],
                "TypedDict representing audio input.",
            )
            self.assertEqual(
                data["typed_input_shapes"]["AudioInput"]["defined_in"],
                str(basic_types_path).replace("\\", "/"),
            )
            self.assertIn("waveform", data["typed_input_shapes"]["AudioInput"]["fields"])
            self.assertEqual(
                data["typed_input_shapes"]["AudioInput"]["fields"]["waveform"]["type"],
                "torch.Tensor",
            )
            self.assertIn(
                "Tensor in format [B, C, T].",
                data["typed_input_shapes"]["AudioInput"]["fields"]["waveform"]["description"],
            )
            self.assertEqual(
                data["typed_input_shapes"]["AudioInput"]["fields"]["waveform"]["traceability"][
                    "strategy"
                ],
                "typed_dict_field",
            )

            self.assertIn("coverage", data)
            self.assertIn("description", data["coverage"])
            self.assertIn("deferred", data["coverage"])

            validate_schema = _load_validate_schema()
            errors = validate_schema.validate_top_level(
                data, validate_schema.SCHEMAS["node_api_schema.json"], "node_api_schema.json"
            )
            errors.extend(validate_schema.validate_metadata(data, "node_api_schema.json"))
            errors.extend(validate_schema.validate_io_types(data, "node_api_schema.json"))
            errors.extend(validate_schema.validate_typed_input_shapes(data, "node_api_schema.json"))
            self.assertEqual(errors, [], msg=f"Schema errors: {errors}")

            self.assertIn("metadata", data)
            self.assertIn("object_info_fields", data)
            self.assertIn("io_types", data)
            self.assertIn("basic_input_shapes", data)
            self.assertIn("typed_input_shapes", data)
            for entry in data["io_types"]:
                self.assertIn("io_type", entry)
                self.assertIn("class_name", entry)
                self.assertIn("input_class", entry)
                self.assertIn("input_parameters", entry)
                self.assertIn("input_parameter_details", entry)
                self.assertIn("type_hint", entry)
                self.assertIn("is_widget", entry)
                self.assertIn("defined_in", entry)

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
