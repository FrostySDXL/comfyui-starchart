import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "extract" / "parse_node_api_schema.py"
OUTPUT = REPO_ROOT / "references" / "raw" / "node_api_schema.json"


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
    class Input(WidgetInput):
        def __init__(self, id: str, default: bool=None, label_on: str=None):
            pass

@comfytype(io_type="STRING")
class String(ComfyTypeIO):
    class Input(WidgetInput):
        def __init__(self, id: str, multiline=False, default: str=None):
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

        self.assertEqual(data["basic_input_shapes"]["ImageInput"], "An image in format [B, H, W, C]")


if __name__ == "__main__":
    unittest.main()
