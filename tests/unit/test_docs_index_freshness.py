"""Tests for scripts/verify/docs_index_freshness.py."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "docs_index_freshness.py"


class DocsIndexFreshnessUnitTests(unittest.TestCase):
    """Direct unit tests for docs-index freshness logic."""

    def _import_module(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("docs_index_freshness", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_freshness_passes_when_generated_output_matches_committed_file(self):
        module = self._import_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            committed_path = tmpdir / "docs-index.json"
            docs_index = {
                "artifact": "docs-index.json",
                "artifact_schema_version": "1.0.0",
                "scope": {"surface": "test", "excludes": []},
                "pages": [{"title": "Docs Home", "path": "index.md"}],
            }
            committed_path.write_text(json.dumps(docs_index, indent=2) + "\n", encoding="utf-8")

            old_output_path = module.generate_docs_index.OUTPUT_PATH
            old_build_docs_index = module.generate_docs_index.build_docs_index
            old_committed_path = module.COMMITTED_PATH
            try:
                module.generate_docs_index.OUTPUT_PATH = committed_path
                module.COMMITTED_PATH = committed_path
                module.generate_docs_index.build_docs_index = lambda repo_root: docs_index
                result = module.main()
                self.assertEqual(result, 0)
            finally:
                module.generate_docs_index.OUTPUT_PATH = old_output_path
                module.generate_docs_index.build_docs_index = old_build_docs_index
                module.COMMITTED_PATH = old_committed_path

    def test_freshness_fails_when_committed_file_is_stale(self):
        module = self._import_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            committed_path = tmpdir / "docs-index.json"
            stale_index = {
                "artifact": "docs-index.json",
                "artifact_schema_version": "1.0.0",
                "scope": {"surface": "test", "excludes": []},
                "pages": [{"title": "Stale", "path": "stale.md"}],
            }
            committed_path.write_text(json.dumps(stale_index, indent=2) + "\n", encoding="utf-8")

            fresh_index = {
                "artifact": "docs-index.json",
                "artifact_schema_version": "1.0.0",
                "scope": {"surface": "test", "excludes": []},
                "pages": [{"title": "Fresh", "path": "fresh.md"}],
            }

            old_output_path = module.generate_docs_index.OUTPUT_PATH
            old_build_docs_index = module.generate_docs_index.build_docs_index
            old_committed_path = module.COMMITTED_PATH
            try:
                module.generate_docs_index.OUTPUT_PATH = committed_path
                module.COMMITTED_PATH = committed_path
                module.generate_docs_index.build_docs_index = lambda repo_root: fresh_index
                result = module.main()
                self.assertEqual(result, 1)
            finally:
                module.generate_docs_index.OUTPUT_PATH = old_output_path
                module.generate_docs_index.build_docs_index = old_build_docs_index
                module.COMMITTED_PATH = old_committed_path


class DocsIndexFreshnessScriptTests(unittest.TestCase):
    """Tests that the freshness script runs successfully on the real repo."""

    def test_script_runs_and_passes(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("docs-index.json is fresh", result.stdout)


if __name__ == "__main__":
    unittest.main()
