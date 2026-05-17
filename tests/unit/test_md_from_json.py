import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "generate" / "md_from_json.py"


class MarkdownGenerationTests(unittest.TestCase):
    def test_generates_markdown_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "server_endpoints.json"
            output_path = Path(tmp) / "server-py-summary.md"
            input_path.write_text(
                json.dumps(
                    {
                        "metadata": {
                            "sources": ["sample server.py", "extra/source.py"],
                            "extracted_date": "2026-04-19",
                            "version": "test",
                        },
                        "coverage": {
                            "description": "contract",
                            "guaranteed_fields": [],
                            "best_effort_fields": [],
                            "deferred": [],
                        },
                        "endpoints": [
                            {
                                "route": "/prompt",
                                "method": "POST",
                                "description": "Submit prompt",
                                "parameters": ["prompt"],
                                "returns": {
                                    "kind": "json",
                                    "summary": "Prompt queued with ID and any node errors.",
                                    "status_codes": [200, 400],
                                    "fields": [
                                        {"name": "prompt_id"},
                                        {"name": "number"},
                                        {"name": "node_errors"},
                                    ],
                                    "notes": ["Returns 400 for validation failures."],
                                },
                            }
                        ],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("Generated reference pages from JSON", result.stdout)

            rendered = output_path.read_text(encoding="utf-8")
            self.assertTrue(rendered.startswith('---\ntitle: "Server.py Summary"\n---\n\n'))
            self.assertIn("# Server.py Summary", rendered)
            self.assertIn("sample server.py", rendered)
            self.assertIn("extra/source.py", rendered)
            self.assertIn("| POST | /prompt | Submit prompt |", rendered)
            self.assertIn(
                "| /prompt | json | 200, 400 | Prompt queued with ID and any node errors. |",
                rendered,
            )
            self.assertIn("## Structured Return Details", rendered)
            self.assertIn(
                "| /prompt | prompt_id, number, node_errors | Returns 400 for validation failures. |",
                rendered,
            )

    def test_writes_placeholder_when_no_endpoints_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "server_endpoints.json"
            output_path = Path(tmp) / "server-py-summary.md"
            input_path.write_text(
                json.dumps(
                    {
                        "metadata": {
                            "sources": ["sample server.py"],
                            "extracted_date": "2026-04-19",
                            "version": "test",
                        },
                        "coverage": {
                            "description": "contract",
                            "guaranteed_fields": [],
                            "best_effort_fields": [],
                            "deferred": [],
                        },
                        "endpoints": [],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            rendered = output_path.read_text(encoding="utf-8")
            self.assertIn("No extracted endpoints are available yet", rendered)


if __name__ == "__main__":
    unittest.main()
