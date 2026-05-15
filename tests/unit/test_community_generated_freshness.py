"""Tests for scripts/verify/community_generated_freshness.py."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "community_generated_freshness.py"


class CommunityGeneratedFreshnessUnitTests(unittest.TestCase):
    """Direct unit tests for freshness check logic, fully hermetic."""

    def _import_module(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("community_generated_freshness", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _create_temp_generator(self, tmpdir: Path) -> Path:
        """Create a minimal temp generator script for hermetic testing."""
        generator_path = tmpdir / "generate_community_pages.py"
        input_path = tmpdir / "ecosystem_packages.json"
        generator_code = f'''
import json
from pathlib import Path

INPUT_PATH = Path(r"{input_path}")
OUTPUT_PATH = Path(r"{tmpdir}") / "map.md"

def build_markdown(data: dict) -> str:
    return "# Generated\\n\\n" + data.get("metadata", {{}}).get("title", "")
'''
        generator_path.write_text(generator_code, encoding="utf-8")
        return generator_path, input_path

    def test_freshness_passes_when_files_match(self):
        module = self._import_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            generator_path, input_path = self._create_temp_generator(tmpdir)

            # Write input JSON
            input_data = {"metadata": {"title": "Test Map"}}
            input_path.write_text(json.dumps(input_data), encoding="utf-8")

            # Write matching committed output
            committed_path = tmpdir / "map.md"
            committed_path.write_text("# Generated\n\nTest Map", encoding="utf-8")

            old_generator = module.GENERATOR
            old_committed = module.COMMITTED_PATH
            try:
                module.GENERATOR = generator_path
                module.COMMITTED_PATH = committed_path
                result = module.main()
                self.assertEqual(result, 0)
            finally:
                module.GENERATOR = old_generator
                module.COMMITTED_PATH = old_committed

    def test_freshness_fails_when_files_differ(self):
        module = self._import_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            generator_path, input_path = self._create_temp_generator(tmpdir)

            # Write input JSON
            input_data = {"metadata": {"title": "Test Map"}}
            input_path.write_text(json.dumps(input_data), encoding="utf-8")

            # Write stale committed output
            committed_path = tmpdir / "map.md"
            committed_path.write_text("# Stale\n\nOld Title", encoding="utf-8")

            old_generator = module.GENERATOR
            old_committed = module.COMMITTED_PATH
            try:
                module.GENERATOR = generator_path
                module.COMMITTED_PATH = committed_path
                result = module.main()
                self.assertEqual(result, 1)
            finally:
                module.GENERATOR = old_generator
                module.COMMITTED_PATH = old_committed


class CommunityGeneratedFreshnessScriptTests(unittest.TestCase):
    """Tests that the freshness script runs successfully on the real repo."""

    def test_script_runs_and_passes(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Generated community pages are fresh", result.stdout)


if __name__ == "__main__":
    unittest.main()
