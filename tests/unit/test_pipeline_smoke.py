"""Tests for scripts/verify/pipeline_smoke.py."""

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "pipeline_smoke.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("pipeline_smoke", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PipelineSmokeUnitTests(unittest.TestCase):
    """Unit tests for command construction and exit propagation."""

    def test_build_command_defaults_to_skip_tests(self):
        module = _load_module()

        command = module.build_command(skip_mkdocs=False)

        self.assertEqual(command[0], sys.executable)
        self.assertEqual(command[1], str(module.RUN_ALL_SCRIPT))
        self.assertEqual(command[2:], ["--skip-tests"])

    def test_build_command_can_forward_skip_mkdocs(self):
        module = _load_module()

        command = module.build_command(skip_mkdocs=True)

        self.assertEqual(command[2:], ["--skip-tests", "--skip-mkdocs"])

    def test_main_returns_subprocess_exit_code(self):
        module = _load_module()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                [sys.executable, str(module.RUN_ALL_SCRIPT), "--skip-tests"],
                0,
                stdout="ok\n",
                stderr="",
            )

            with patch("sys.argv", ["pipeline_smoke.py"]):
                result = module.main()

        self.assertEqual(result, 0)
        mock_run.assert_called_once()

    def test_main_propagates_nonzero_subprocess_exit_code(self):
        module = _load_module()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                [sys.executable, str(module.RUN_ALL_SCRIPT), "--skip-tests"],
                1,
                stdout="failed\n",
                stderr="boom\n",
            )

            with patch("sys.argv", ["pipeline_smoke.py"]):
                result = module.main()

        self.assertEqual(result, 1)

    def test_main_handles_missing_run_all_script_cleanly(self):
        module = _load_module()

        with patch("subprocess.run", side_effect=FileNotFoundError("missing")):
            with patch("sys.argv", ["pipeline_smoke.py"]):
                result = module.main()

        self.assertEqual(result, 1)


class PipelineSmokeScriptTests(unittest.TestCase):
    """CLI-level tests for pipeline_smoke.py."""

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("skip-tests", result.stdout)
        self.assertIn("run_all.py", result.stdout)


if __name__ == "__main__":
    unittest.main()
