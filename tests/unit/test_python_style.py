"""Tests for scripts/verify/python_style.py."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "python_style.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("python_style", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PythonStyleUnitTests(unittest.TestCase):
    """Unit tests for Ruff wrapper step order and failure propagation."""

    def test_success_path_runs_both_steps_in_order(self):
        module = _load_module()
        call_order = []

        def fake_run(cmd, **kwargs):
            call_order.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

        with patch("scripts.common.subprocess_utils.subprocess.run", side_effect=fake_run):
            with patch("sys.argv", ["python_style.py"]):
                result = module.main()

        self.assertEqual(result, 0)
        self.assertEqual(len(call_order), 2)
        self.assertIn("ruff", call_order[0])
        self.assertIn("check", call_order[0])
        self.assertIn("scripts", call_order[0])
        self.assertIn("tests", call_order[0])
        self.assertIn("ruff", call_order[1])
        self.assertIn("format", call_order[1])
        self.assertIn("--check", call_order[1])
        self.assertIn("scripts", call_order[1])
        self.assertIn("tests", call_order[1])

    def test_first_step_failure_stops_sequence(self):
        module = _load_module()
        call_order = []

        def fake_run(cmd, **kwargs):
            call_order.append(cmd)
            if "check" in cmd:
                return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="lint fail")
            return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

        with patch("scripts.common.subprocess_utils.subprocess.run", side_effect=fake_run):
            with patch("sys.argv", ["python_style.py"]):
                result = module.main()

        self.assertEqual(result, 1)
        self.assertEqual(len(call_order), 1)
        self.assertIn("check", call_order[0])

    def test_second_step_failure_returns_nonzero(self):
        module = _load_module()
        call_order = []

        def fake_run(cmd, **kwargs):
            call_order.append(cmd)
            if "format" in cmd:
                return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="format fail")
            return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

        with patch("scripts.common.subprocess_utils.subprocess.run", side_effect=fake_run):
            with patch("sys.argv", ["python_style.py"]):
                result = module.main()

        self.assertEqual(result, 1)
        self.assertEqual(len(call_order), 2)
        self.assertIn("check", call_order[0])
        self.assertIn("format", call_order[1])


class PythonStyleScriptTests(unittest.TestCase):
    """CLI smoke tests for the Python style wrapper."""

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("blocking Ruff-based Python style checks", result.stdout)


if __name__ == "__main__":
    unittest.main()
