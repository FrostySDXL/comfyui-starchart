import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import importlib.util

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "extract" / "parse_node_api_schema.py"
OUTPUT = REPO_ROOT / "references" / "raw" / "node_api_schema.json"


def _load_validate_schema():
    spec = importlib.util.spec_from_file_location(
        "validate_schema",
        REPO_ROOT / "scripts" / "verify" / "validate_schema.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ParseNodeApiSchemaTests(unittest.TestCase):
    def setUp(self):
        self.original = OUTPUT.read_text(encoding="utf-8")

    def tearDown(self):
        OUTPUT.write_text(self.original, encoding="utf-8")

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
        server_sample = '''
def node_info(node_class):
    info = {}
    info['input'] = obj_class.INPUT_TYPES()
    info['output'] = obj_class.RETURN_TYPES
    info['display_name'] = node_class
    info['category'] = 'sd'
    info['search_aliases'] = []
    return info
'''

        io_sample = '''
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
'''

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
            server_path = tmp_path / "server.py"
            io_path = tmp_path / "_io.py"
            basic_types_path = tmp_path / "basic_types.py"
            server_path.write_text(server_sample, encoding="utf-8")
            io_path.write_text(io_sample, encoding="utf-8")
            basic_types_path.write_text(basic_types_sample, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(server_path),
                    str(io_path),
                    str(basic_types_path),
                    "--version",
                    "v-test",
                    "--commit",
                    "abc123",
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Extracted node API schema", result.stdout)

        data = json.loads(OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(data["metadata"]["version"], "v-test")
        self.assertEqual(data["metadata"]["commit"], "abc123")
        self.assertIn("input", data["object_info_fields"])
        self.assertIn("display_name", data["object_info_fields"])

        io_types = {entry["io_type"]: entry for entry in data["io_types"]}
        self.assertIn("BOOLEAN", io_types)
        self.assertEqual(io_types["BOOLEAN"]["input_class"], "WidgetInput")
        self.assertIn("default", io_types["BOOLEAN"]["input_parameters"])
        self.assertEqual(io_types["BOOLEAN"]["type_hint"], "bool")
        self.assertTrue(io_types["BOOLEAN"]["is_widget"])
        self.assertEqual(io_types["BOOLEAN"]["defined_in"], str(io_path).replace("\\", "/"))

        self.assertEqual(io_types["STRING"]["type_hint"], "str")
        self.assertEqual(io_types["STRING"]["output_parameters"], ["display_name", "tooltip", "is_output_list"])
        self.assertEqual(io_types["LOAD_3D_ANIMATION"]["type_hint"], "Model3DDict")
        self.assertEqual(io_types["POINT"]["type_hint"], "Any")
        self.assertEqual(io_types["HISTOGRAM"]["input_class"], None)
        self.assertEqual(io_types["HISTOGRAM"]["input_parameters"], [])

        self.assertEqual(data["basic_input_shapes"]["ImageInput"], "An image in format [B, H, W, C]")

        # Verify typed_input_shapes extraction
        self.assertIn("AudioInput", data["typed_input_shapes"])
        self.assertEqual(data["typed_input_shapes"]["AudioInput"]["description"], "TypedDict representing audio input.")
        self.assertIn("waveform", data["typed_input_shapes"]["AudioInput"]["fields"])
        self.assertEqual(data["typed_input_shapes"]["AudioInput"]["fields"]["waveform"]["type"], "torch.Tensor")
        self.assertIn("Tensor in format [B, C, T].", data["typed_input_shapes"]["AudioInput"]["fields"]["waveform"]["description"])

        # Verify coverage metadata
        self.assertIn("coverage", data)
        self.assertIn("description", data["coverage"])
        self.assertIn("deferred", data["coverage"])

        # Verify output passes schema validation
        validate_schema = _load_validate_schema()
        errors = validate_schema.validate_top_level(
            data, validate_schema.SCHEMAS["node_api_schema.json"], "node_api_schema.json"
        )
        errors.extend(validate_schema.validate_metadata(data, "node_api_schema.json"))
        errors.extend(validate_schema.validate_io_types(data, "node_api_schema.json"))
        self.assertEqual(errors, [], msg=f"Schema errors: {errors}")

        # Assert richer contract shape beyond top-level file existence
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
            self.assertIn("type_hint", entry)
            self.assertIn("is_widget", entry)
            self.assertIn("defined_in", entry)

    def test_bracket_aware_parameter_parsing(self):
        """Parameters with nested generic types like Dict[str, List[float]] should not produce bogus names."""
        # Import the module directly to test parse_parameters
        import importlib.util
        spec = importlib.util.spec_from_file_location("parse_node_api_schema", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

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
            ("display_name: str, default: CurveInput_=None, socketless: bool=False, optional: bool=False, tooltip: str=None", ["display_name", "default", "socketless", "optional", "tooltip"]),
            # This is the actual bug case - float]] should not appear
            ("display_name: str, default: CurveInput_=None, socketless: bool=True", ["display_name", "default", "socketless"]),
        ]

        for sig_text, expected in test_cases:
            result = module.parse_parameters(sig_text)
            self.assertEqual(result, expected, f"Failed for: {sig_text}")

    def test_match_type_without_top_level_type_remains_null(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("parse_node_api_schema", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        io_sample = '''
@comfytype(io_type="COMFY_MATCHTYPE_V3")
class MatchType(ComfyTypeIO):
    class Template:
        def __init__(self, template_id: str):
            self.template_id = template_id

    class Input(Input):
        def __init__(self, id: str, template: MatchType.Template):
            pass
'''

        io_types = module.extract_io_types(io_sample, "sample/_io.py")
        self.assertEqual(io_types[0]["type_hint"], None)


if __name__ == "__main__":
    unittest.main()
