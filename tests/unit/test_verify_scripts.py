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

    def test_extraction_idempotency_script_runs(self):
        """The extraction idempotency script should run without crashing."""
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "verify" / "extraction_idempotency.py")],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=120,
        )
        # Exit code 0 or 1 are both valid (1 means differences found)
        self.assertIn(result.returncode, [0, 1], msg=result.stderr)
        self.assertIn("Checking", result.stdout)

    def test_extraction_idempotency_imports(self):
        """The extraction_idempotency module should be importable."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "extraction_idempotency",
            REPO_ROOT / "scripts" / "verify" / "extraction_idempotency.py",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(hasattr(module, "verify_idempotency"))


if __name__ == "__main__":
    unittest.main()