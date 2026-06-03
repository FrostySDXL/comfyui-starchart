"""Tests for scripts/verify/wait_for_runtime.py."""

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "wait_for_runtime.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("wait_for_runtime", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WaitForRuntimeUnitTests(unittest.TestCase):
    def test_fetch_json_success(self):
        module = _load_module()

        with patch.object(module.http_utils, "get_json", return_value={"ready": True}):
            result = module.fetch_json("http://127.0.0.1:8188/object_info", timeout=5)

        self.assertEqual(result, {"ready": True})

    def test_wait_for_runtime_retries_until_ready(self):
        module = _load_module()

        with patch.object(
            module, "fetch_json", side_effect=[RuntimeError("still booting"), {"KSampler": {}}]
        ):
            with patch.object(module.time, "monotonic", side_effect=[0, 1, 2]):
                with patch.object(module.time, "sleep") as mock_sleep:
                    result = module.wait_for_runtime(
                        "http://127.0.0.1:8188/object_info",
                        timeout=10,
                        interval=1,
                        require_non_empty=True,
                    )

        self.assertEqual(result, 0)
        mock_sleep.assert_called_once_with(1)

    def test_wait_for_runtime_times_out_on_empty_dict_when_required(self):
        module = _load_module()

        with patch.object(module, "fetch_json", return_value={}):
            with patch.object(module.time, "monotonic", side_effect=[0, 0, 5, 5]):
                with patch.object(module.time, "sleep") as mock_sleep:
                    result = module.wait_for_runtime(
                        "http://127.0.0.1:8188/object_info",
                        timeout=5,
                        interval=1,
                        require_non_empty=True,
                    )

        self.assertEqual(result, 1)
        mock_sleep.assert_called_once_with(1)


class WaitForRuntimeScriptTests(unittest.TestCase):
    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("--require-non-empty", result.stdout)


if __name__ == "__main__":
    unittest.main()
