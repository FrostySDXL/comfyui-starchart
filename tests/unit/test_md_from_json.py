import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "generate" / "md_from_json.py"
INPUT = REPO_ROOT / "references" / "raw" / "server_endpoints.json"
OUTPUT = REPO_ROOT / "docs" / "reference" / "server-py-summary.md"


class MarkdownGenerationTests(unittest.TestCase):
    def setUp(self):
        self.original = INPUT.read_text(encoding="utf-8")
        self.original_output = OUTPUT.read_text(encoding="utf-8")

    def tearDown(self):
        INPUT.write_text(self.original, encoding="utf-8")
        OUTPUT.write_text(self.original_output, encoding="utf-8")

    def test_generates_markdown_summary(self):
        INPUT.write_text(
            json.dumps(
                {
                    "metadata": {
                        "source": "sample server.py",
                        "extracted_date": "2026-04-19",
                        "version": "test"
                    },
                    "endpoints": [
                        {
                            "route": "/prompt",
                            "method": "POST",
                            "description": "Submit prompt",
                            "parameters": ["prompt"],
                            "returns": "prompt_id"
                        }
                    ]
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Generated reference pages from JSON", result.stdout)

        rendered = OUTPUT.read_text(encoding="utf-8")
        self.assertIn("# Server.py Summary", rendered)
        self.assertIn("sample server.py", rendered)
        self.assertIn("| POST | /prompt | Submit prompt |", rendered)

    def test_writes_placeholder_when_no_endpoints_exist(self):
        INPUT.write_text(
            json.dumps(
                {
                    "metadata": {
                        "source": "sample server.py",
                        "extracted_date": "2026-04-19",
                        "version": "test"
                    },
                    "endpoints": []
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        rendered = OUTPUT.read_text(encoding="utf-8")
        self.assertIn("No extracted endpoints are available yet", rendered)


if __name__ == "__main__":
    unittest.main()
