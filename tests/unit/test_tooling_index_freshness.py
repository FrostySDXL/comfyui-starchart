"""Tests for scripts/verify/tooling_index_freshness.py."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "tooling_index_freshness.py"


class ToolingIndexFreshnessUnitTests(unittest.TestCase):
    def _import_module(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("tooling_index_freshness", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_freshness_passes_when_generated_output_matches_committed_file(self):
        module = self._import_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            committed_path = tmpdir / "tooling-index.json"
            tooling_index = {
                "artifact": "tooling-index.json",
                "artifact_schema_version": "0.1.0",
                "scope": {"surface": "test navigation", "excludes": []},
                "pages": [{"title": "Docs Home", "path": "index.md"}],
            }
            committed_path.write_text(json.dumps(tooling_index, indent=2) + "\n", encoding="utf-8")

            old_output_path = module.generate_tooling_index.OUTPUT_PATH
            old_build = module.generate_tooling_index.build_tooling_index
            old_committed_path = module.COMMITTED_PATH
            try:
                module.generate_tooling_index.OUTPUT_PATH = committed_path
                module.COMMITTED_PATH = committed_path
                module.generate_tooling_index.build_tooling_index = lambda repo_root: tooling_index
                result = module.main()
                self.assertEqual(result, 0)
            finally:
                module.generate_tooling_index.OUTPUT_PATH = old_output_path
                module.generate_tooling_index.build_tooling_index = old_build
                module.COMMITTED_PATH = old_committed_path

    def test_freshness_fails_when_committed_file_is_stale(self):
        module = self._import_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            committed_path = tmpdir / "tooling-index.json"
            stale_index = {
                "artifact": "tooling-index.json",
                "artifact_schema_version": "0.1.0",
                "scope": {"surface": "test", "excludes": []},
                "pages": [{"title": "Stale", "path": "stale.md"}],
            }
            committed_path.write_text(json.dumps(stale_index, indent=2) + "\n", encoding="utf-8")

            fresh_index = {
                "artifact": "tooling-index.json",
                "artifact_schema_version": "0.1.0",
                "scope": {"surface": "test navigation", "excludes": []},
                "pages": [{"title": "Fresh", "path": "fresh.md"}],
            }

            old_output_path = module.generate_tooling_index.OUTPUT_PATH
            old_build = module.generate_tooling_index.build_tooling_index
            old_committed_path = module.COMMITTED_PATH
            try:
                module.generate_tooling_index.OUTPUT_PATH = committed_path
                module.COMMITTED_PATH = committed_path
                module.generate_tooling_index.build_tooling_index = lambda repo_root: fresh_index
                result = module.main()
                self.assertEqual(result, 1)
            finally:
                module.generate_tooling_index.OUTPUT_PATH = old_output_path
                module.generate_tooling_index.build_tooling_index = old_build
                module.COMMITTED_PATH = old_committed_path


class ToolingIndexFreshnessScriptTests(unittest.TestCase):
    def test_script_runs_and_passes(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("tooling-index.json is fresh", result.stdout)


if __name__ == "__main__":
    unittest.main()
