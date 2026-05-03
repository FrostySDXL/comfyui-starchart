"""Tests for scripts/verify/runtime_smoke.py."""

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "runtime_smoke.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("runtime_smoke", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeSmokeUnitTests(unittest.TestCase):
    """Direct unit tests for runtime_smoke functions."""

    def test_check_features_success(self):
        module = _load_module()
        with patch.object(module.http_utils, "get_json", return_value={"features": []}):
            self.assertTrue(module.check_features("http://127.0.0.1:8188", 10))

    def test_check_features_non_dict_fails(self):
        module = _load_module()
        with patch.object(module.http_utils, "get_json", return_value=[]):
            self.assertFalse(module.check_features("http://127.0.0.1:8188", 10))

    def test_check_system_stats_success(self):
        module = _load_module()
        with patch.object(module.http_utils, "get_json", return_value={"devices": []}):
            self.assertTrue(module.check_system_stats("http://127.0.0.1:8188", 10))

    def test_check_object_info_success(self):
        module = _load_module()
        with patch.object(module.http_utils, "get_json", return_value={"KSampler": {"input": {}}}):
            self.assertTrue(module.check_object_info("http://127.0.0.1:8188", 10))

    def test_check_object_info_empty_fails(self):
        module = _load_module()
        with patch.object(module.http_utils, "get_json", return_value={}):
            self.assertFalse(module.check_object_info("http://127.0.0.1:8188", 10))

    def test_check_post_prompt_success(self):
        module = _load_module()
        prompt_path = REPO_ROOT / "examples" / "api-calls" / "post-prompt.json"
        with patch.object(module.http_utils, "post_json", return_value={"prompt_id": "abc"}):
            self.assertTrue(module.check_post_prompt("http://127.0.0.1:8188", prompt_path, 10))

    def test_check_post_prompt_missing_file_skips(self):
        module = _load_module()
        self.assertTrue(module.check_post_prompt("http://127.0.0.1:8188", Path("/nonexistent.json"), 10))

    def test_main_runs_all_checks(self):
        module = _load_module()
        with patch.object(module.http_utils, "get_json", return_value={"test": 1}):
            with patch("sys.argv", [
                "runtime_smoke.py",
                "--url", "http://127.0.0.1:8188",
                "--skip-prompt",
            ]):
                result = module.main()

        self.assertEqual(result, 0)

    def test_main_failure_exits_nonzero(self):
        module = _load_module()
        with patch.object(module.http_utils, "get_json", return_value=[]):
            with patch("sys.argv", [
                "runtime_smoke.py",
                "--url", "http://127.0.0.1:8188",
                "--skip-prompt",
            ]):
                result = module.main()

        self.assertEqual(result, 1)


class RuntimeSmokeScriptTests(unittest.TestCase):
    """Tests for the CLI script behavior."""

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--skip-prompt", result.stdout)


if __name__ == "__main__":
    unittest.main()
