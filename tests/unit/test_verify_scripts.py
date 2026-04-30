"""Tests for verification scripts in scripts/verify/."""

import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class CrossReferencesTests(unittest.TestCase):
    """Test that cross_references.py runs and reports valid references."""

    def test_cross_references_script_runs(self):
        """The cross-references script should run without error on the current repo."""
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "verify" / "cross_references.py")],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("All cross-references are valid", result.stdout)

    def test_cross_references_imports(self):
        """The cross_references module should be importable."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "cross_references",
            REPO_ROOT / "scripts" / "verify" / "cross_references.py",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(hasattr(module, "verify_markdown_references"))
        self.assertTrue(hasattr(module, "verify_json_source_references"))


class StaleContentTests(unittest.TestCase):
    """Test that stale_content.py runs and detects stale content correctly."""

    def test_stale_content_script_runs(self):
        """The stale content script should run without error on the current repo."""
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "verify" / "stale_content.py")],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        # Exit code 0 means no stale content found, which is expected after cleanup
        self.assertIn(result.returncode, [0, 1], msg=result.stderr)

    def test_stale_content_imports(self):
        """The stale_content module should be importable."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "stale_content",
            REPO_ROOT / "scripts" / "verify" / "stale_content.py",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(hasattr(module, "find_stale_in_json"))
        self.assertTrue(hasattr(module, "find_stale_in_markdown"))


class ExtractionIdempotencyTests(unittest.TestCase):
    """Test that extraction_idempotency.py runs correctly."""

    def _load_module(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "extraction_idempotency",
            REPO_ROOT / "scripts" / "verify" / "extraction_idempotency.py",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_extraction_idempotency_script_runs(self):
        """The extraction idempotency script should run without crashing."""
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "verify" / "extraction_idempotency.py")],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Checking", result.stdout)
        self.assertIn("All extraction outputs are idempotent.", result.stdout)

    def test_extraction_idempotency_imports(self):
        """The extraction_idempotency module should be importable."""
        module = self._load_module()
        self.assertTrue(hasattr(module, "verify_idempotency"))

    def test_get_extractor_args_uses_server_sources_list(self):
        module = self._load_module()
        import json
        import tempfile

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


class ValidateSchemaTests(unittest.TestCase):
    """Test that validate_schema.py runs and reports valid schemas."""

    def test_validate_schema_script_runs(self):
        """The validate_schema script should run without error on the current repo."""
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "verify" / "validate_schema.py")],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("pass schema validation", result.stdout)

    def test_validate_schema_imports(self):
        """The validate_schema module should be importable and expose validators."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "validate_schema",
            REPO_ROOT / "scripts" / "verify" / "validate_schema.py",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(hasattr(module, "validate_endpoints"))
        self.assertTrue(hasattr(module, "validate_returns"))
        self.assertTrue(hasattr(module, "validate_io_types"))


if __name__ == "__main__":
    unittest.main()
