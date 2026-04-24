"""Tests for scripts/verify/run_all.py."""

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "run_all.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_all", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RunAllUnitTests(unittest.TestCase):
    """Unit tests for run_all step ordering and failure propagation."""

    def test_step_success(self):
        module = _load_module()
        with patch("scripts.verify.run_all.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "ok"
            mock_run.return_value.stderr = ""
            self.assertTrue(module.run_step(["echo", "ok"], "Test step"))

    def test_step_failure(self):
        module = _load_module()
        with patch("scripts.verify.run_all.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = "error"
            self.assertFalse(module.run_step(["false"], "Test step"))

    def test_runs_all_steps_in_order(self):
        module = _load_module()
        call_order = []

        def fake_run(cmd, **kwargs):
            call_order.append(cmd)
            result = subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")
            return result

        with patch("scripts.verify.run_all.subprocess.run", side_effect=fake_run):
            with patch("sys.argv", ["run_all.py"]):
                result = module.main()

        self.assertEqual(result, 0)
        self.assertTrue(any("unittest" in str(c) for c in call_order))
        self.assertTrue(any("cross_references.py" in str(c) for c in call_order))
        self.assertTrue(any("validate_schema.py" in str(c) for c in call_order))
        self.assertTrue(any("community_generated_freshness.py" in str(c) for c in call_order))
        self.assertTrue(any("community_page_coverage.py" in str(c) for c in call_order))
        self.assertTrue(any("mkdocs" in str(c) for c in call_order))

        # Verify order: tests first, then blocking verifiers, then mkdocs
        unittest_idx = next(i for i, c in enumerate(call_order) if "unittest" in str(c))
        cross_idx = next(i for i, c in enumerate(call_order) if "cross_references.py" in str(c))
        validate_idx = next(i for i, c in enumerate(call_order) if "validate_schema.py" in str(c))
        freshness_idx = next(i for i, c in enumerate(call_order) if "community_generated_freshness.py" in str(c))
        coverage_idx = next(i for i, c in enumerate(call_order) if "community_page_coverage.py" in str(c))
        mkdocs_idx = next(i for i, c in enumerate(call_order) if "mkdocs" in str(c))

        self.assertLess(unittest_idx, cross_idx)
        self.assertLess(cross_idx, validate_idx)
        self.assertLess(validate_idx, freshness_idx)
        self.assertLess(freshness_idx, coverage_idx)
        self.assertLess(coverage_idx, mkdocs_idx)

    def test_failure_stops_sequence(self):
        module = _load_module()
        call_order = []

        def fake_run(cmd, **kwargs):
            call_order.append(cmd)
            if "cross_references.py" in str(cmd):
                return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="fail")
            return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

        with patch("scripts.verify.run_all.subprocess.run", side_effect=fake_run):
            with patch("sys.argv", ["run_all.py"]):
                result = module.main()

        self.assertEqual(result, 1)
        self.assertTrue(any("cross_references.py" in str(c) for c in call_order))
        self.assertFalse(any("validate_schema.py" in str(c) for c in call_order))

    def test_skip_tests_flag(self):
        module = _load_module()
        call_order = []

        def fake_run(cmd, **kwargs):
            call_order.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

        with patch("scripts.verify.run_all.subprocess.run", side_effect=fake_run):
            with patch("sys.argv", ["run_all.py", "--skip-tests"]):
                result = module.main()

        self.assertEqual(result, 0)
        self.assertFalse(any("unittest" in str(c) for c in call_order))
        self.assertTrue(any("cross_references.py" in str(c) for c in call_order))

    def test_skip_mkdocs_flag(self):
        module = _load_module()
        call_order = []

        def fake_run(cmd, **kwargs):
            call_order.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

        with patch("scripts.verify.run_all.subprocess.run", side_effect=fake_run):
            with patch("sys.argv", ["run_all.py", "--skip-mkdocs"]):
                result = module.main()

        self.assertEqual(result, 0)
        self.assertTrue(any("unittest" in str(c) for c in call_order))
        self.assertFalse(any("mkdocs" in str(c) for c in call_order))


class RunAllScriptTests(unittest.TestCase):
    """Tests for the CLI script behavior."""

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--skip-tests", result.stdout)
        self.assertIn("--skip-mkdocs", result.stdout)


if __name__ == "__main__":
    unittest.main()
