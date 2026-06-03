"""Tests for scripts/verify/extraction_idempotency.py."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "extraction_idempotency.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("extraction_idempotency", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExtractionIdempotencyTests(unittest.TestCase):
    """Test that extraction_idempotency.py runs correctly."""

    def test_extraction_idempotency_script_runs(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Checking", result.stdout)
        self.assertIn("All extraction outputs are idempotent.", result.stdout)

    def test_extraction_idempotency_imports(self):
        module = _load_module()
        self.assertTrue(hasattr(module, "verify_idempotency"))

    def test_get_extractor_args_uses_server_sources_list(self):
        module = _load_module()
        payload = {
            "metadata": {
                "sources": ["references/snapshots/server.py"],
                "version": "v0.19.3",
                "commit": "abc123",
                "extracted_date": "2026-04-29",
            },
            "coverage": {
                "description": "contract",
                "guaranteed_fields": [],
                "best_effort_fields": [],
                "deferred": [],
            },
            "endpoints": [],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "server_endpoints.json"
            json_path.write_text(json.dumps(payload), encoding="utf-8")
            script_name, args = module.get_extractor_args(json_path)

        self.assertEqual(script_name, "parse_server.py")
        self.assertEqual(
            args,
            [
                "references/snapshots/server.py",
                "--version",
                "v0.19.3",
                "--commit",
                "abc123",
            ],
        )


if __name__ == "__main__":
    unittest.main()
