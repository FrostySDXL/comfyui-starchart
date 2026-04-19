import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "extract" / "parse_server.py"
OUTPUT = REPO_ROOT / "references" / "raw" / "server_endpoints.json"


class ParseServerTests(unittest.TestCase):
    def test_requires_argument(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_extracts_routes_to_json(self):
        sample = '''
@routes.get("/history")
def history():
    """History listing."""
    return None

@routes.post("/prompt")
def prompt():
    return None

@routes.ws("/ws")
def socket():
    """Socket stream."""
    return None
'''

        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            server_path.write_text(sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(server_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Extracted 3 endpoints", result.stdout)

        data = json.loads(OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(len(data["endpoints"]), 3)
        self.assertEqual(data["endpoints"][0]["method"], "GET")
        self.assertEqual(data["endpoints"][0]["route"], "/history")
        self.assertEqual(data["endpoints"][0]["description"], "History listing.")


if __name__ == "__main__":
    unittest.main()
