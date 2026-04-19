import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "extract" / "parse_hooks.py"
OUTPUT = REPO_ROOT / "references" / "raw" / "js_hooks.json"


class ParseHooksTests(unittest.TestCase):
    def setUp(self):
        self.original = OUTPUT.read_text(encoding="utf-8")

    def tearDown(self):
        OUTPUT.write_text(self.original, encoding="utf-8")

    def test_requires_argument(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_extracts_hooks_to_json(self):
        sample = '''
invokeExtensions("beforeRegisterNodeDef", nodeDef, nodeData)
invokeExtensionsAsync("setup")
app.registerExtension({
  async init() {},
  async setup() {},
  async nodeCreated(node) {}
})
'''

        with tempfile.TemporaryDirectory() as tmp:
            app_path = Path(tmp) / "app.js"
            app_path.write_text(sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(app_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Extracted", result.stdout)

        data = json.loads(OUTPUT.read_text(encoding="utf-8"))
        names = {entry["name"] for entry in data["hooks"]}
        self.assertIn("beforeRegisterNodeDef", names)
        self.assertIn("setup", names)
        self.assertIn("init", names)
        self.assertIn("nodeCreated", names)


if __name__ == "__main__":
    unittest.main()
