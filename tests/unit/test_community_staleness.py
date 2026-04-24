"""Tests for scripts/verify/community_staleness.py."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "community_staleness.py"


class CommunityStalenessUnitTests(unittest.TestCase):
    """Direct unit tests for staleness checking functions."""

    def _import_module(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("community_staleness", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_future_date_not_stale(self):
        module = self._import_module()
        data = {
            "packages": [
                {
                    "name": "Future Pack",
                    "needs_review_after": "2099-01-01",
                }
            ]
        }
        stale = module.check_stale(data, "ecosystem_packages.json", "packages")
        self.assertEqual(stale, [])

    def test_past_date_is_stale(self):
        module = self._import_module()
        data = {
            "packages": [
                {
                    "name": "Past Pack",
                    "needs_review_after": "2000-01-01",
                }
            ]
        }
        stale = module.check_stale(data, "ecosystem_packages.json", "packages")
        self.assertTrue(any("Past Pack" in s for s in stale))

    def test_invalid_date_reported(self):
        module = self._import_module()
        data = {
            "packages": [
                {
                    "name": "Bad Date Pack",
                    "needs_review_after": "not-a-date",
                }
            ]
        }
        stale = module.check_stale(data, "ecosystem_packages.json", "packages")
        self.assertTrue(any("invalid needs_review_after date" in s for s in stale))

    def test_invalid_json_is_treated_as_failure(self):
        module = self._import_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            community_dir = Path(tmpdir)
            (community_dir / "ecosystem_packages.json").write_text("{", encoding="utf-8")
            (
                community_dir / "community_pages.json"
            ).write_text('{"pages": []}', encoding="utf-8")

            old_dir = module.COMMUNITY_DIR
            try:
                module.COMMUNITY_DIR = community_dir
                result = module.main()
                self.assertEqual(result, 1)
            finally:
                module.COMMUNITY_DIR = old_dir


class CommunityStalenessScriptTests(unittest.TestCase):
    """Tests that the community staleness script runs successfully."""

    def test_script_runs(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        # Exit code 0 means nothing is stale, 1 means stale entries exist.
        self.assertIn(result.returncode, [0, 1], msg=result.stderr)
        if result.returncode == 0:
            self.assertIn("No stale community metadata entries found", result.stdout)


if __name__ == "__main__":
    unittest.main()
