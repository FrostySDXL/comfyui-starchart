"""Tests for scripts/verify/cross_references.py."""

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "cross_references.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("cross_references", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CrossReferencesTests(unittest.TestCase):
    """Test that cross_references.py runs and reports bounded path checks."""

    def test_cross_references_script_runs(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("All references-path checks are valid", result.stdout)

    def test_cross_references_imports(self):
        module = _load_module()
        self.assertTrue(hasattr(module, "verify_markdown_references"))
        self.assertTrue(hasattr(module, "verify_json_source_references"))
        self.assertIn("does not validate general intra-doc markdown links", module.__doc__)


if __name__ == "__main__":
    unittest.main()
