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
        self.assertTrue(any("test" in str(c) and module.NPM_EXECUTABLE in c for c in call_order))
        self.assertTrue(any("python_style.py" in str(c) for c in call_order))
        self.assertTrue(any("cross_references.py" in str(c) for c in call_order))
        self.assertTrue(any("docs_index_freshness.py" in str(c) for c in call_order))
        self.assertTrue(any("validate_schema.py" in str(c) for c in call_order))
        self.assertTrue(any("verify_artifact_integrity.py" in str(c) for c in call_order))
        self.assertTrue(any("markdown_top_level_spacing.py" in str(c) for c in call_order))
        self.assertTrue(any("community_generated_freshness.py" in str(c) for c in call_order))
        self.assertTrue(any("community_page_coverage.py" in str(c) for c in call_order))
        self.assertTrue(any("sidebar_navigation_coverage.py" in str(c) for c in call_order))
        self.assertTrue(any(c == [module.NPM_EXECUTABLE, "run", "check"] for c in call_order))
        self.assertTrue(any(c == [module.NPM_EXECUTABLE, "run", "build"] for c in call_order))
        self.assertTrue(any("rendered_links.py" in str(c) for c in call_order))

        # Verify order: tests first, then Python/style verifiers, then sidebar/check/build
        unittest_idx = next(i for i, c in enumerate(call_order) if "unittest" in str(c))
        npm_test_idx = next(
            i for i, c in enumerate(call_order) if c == [module.NPM_EXECUTABLE, "test"]
        )
        python_style_idx = next(i for i, c in enumerate(call_order) if "python_style.py" in str(c))
        cross_idx = next(i for i, c in enumerate(call_order) if "cross_references.py" in str(c))
        docs_index_idx = next(
            i for i, c in enumerate(call_order) if "docs_index_freshness.py" in str(c)
        )
        validate_idx = next(i for i, c in enumerate(call_order) if "validate_schema.py" in str(c))
        integrity_idx = next(
            i for i, c in enumerate(call_order) if "verify_artifact_integrity.py" in str(c)
        )
        spacing_idx = next(
            i for i, c in enumerate(call_order) if "markdown_top_level_spacing.py" in str(c)
        )
        freshness_idx = next(
            i for i, c in enumerate(call_order) if "community_generated_freshness.py" in str(c)
        )
        coverage_idx = next(
            i for i, c in enumerate(call_order) if "community_page_coverage.py" in str(c)
        )
        sidebar_idx = next(
            i for i, c in enumerate(call_order) if "sidebar_navigation_coverage.py" in str(c)
        )
        astro_check_idx = next(
            i for i, c in enumerate(call_order) if c == [module.NPM_EXECUTABLE, "run", "check"]
        )
        astro_build_idx = next(
            i for i, c in enumerate(call_order) if c == [module.NPM_EXECUTABLE, "run", "build"]
        )
        rendered_links_idx = next(
            i for i, c in enumerate(call_order) if "rendered_links.py" in str(c)
        )

        self.assertLess(unittest_idx, cross_idx)
        self.assertLess(unittest_idx, npm_test_idx)
        self.assertLess(npm_test_idx, python_style_idx)
        self.assertLess(unittest_idx, python_style_idx)
        self.assertLess(python_style_idx, cross_idx)
        self.assertLess(cross_idx, docs_index_idx)
        self.assertLess(docs_index_idx, validate_idx)
        self.assertLess(validate_idx, integrity_idx)
        self.assertLess(integrity_idx, spacing_idx)
        self.assertLess(integrity_idx, freshness_idx)
        self.assertLess(spacing_idx, freshness_idx)
        self.assertLess(freshness_idx, coverage_idx)
        self.assertLess(coverage_idx, sidebar_idx)
        self.assertLess(sidebar_idx, astro_check_idx)
        self.assertLess(astro_check_idx, astro_build_idx)
        self.assertLess(astro_build_idx, rendered_links_idx)

    def test_failure_stops_sequence(self):
        module = _load_module()
        call_order = []

        def fake_run(cmd, **kwargs):
            call_order.append(cmd)
            if "python_style.py" in str(cmd):
                return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="style fail")
            return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

        with patch("scripts.verify.run_all.subprocess.run", side_effect=fake_run):
            with patch("sys.argv", ["run_all.py"]):
                result = module.main()

        self.assertEqual(result, 1)
        self.assertTrue(any("python_style.py" in str(c) for c in call_order))
        self.assertFalse(any("cross_references.py" in str(c) for c in call_order))
        self.assertFalse(any("docs_index_freshness.py" in str(c) for c in call_order))
        self.assertFalse(any("validate_schema.py" in str(c) for c in call_order))

    def test_integrity_failure_stops_before_downstream_steps(self):
        module = _load_module()
        call_order = []

        def fake_run(cmd, **kwargs):
            call_order.append(cmd)
            if "verify_artifact_integrity.py" in str(cmd):
                return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="integrity fail")
            return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

        with patch("scripts.verify.run_all.subprocess.run", side_effect=fake_run):
            with patch("sys.argv", ["run_all.py"]):
                result = module.main()

        self.assertEqual(result, 1)
        self.assertTrue(any("verify_artifact_integrity.py" in str(c) for c in call_order))
        self.assertFalse(any("markdown_top_level_spacing.py" in str(c) for c in call_order))
        self.assertFalse(any("community_generated_freshness.py" in str(c) for c in call_order))
        self.assertFalse(any("sidebar_navigation_coverage.py" in str(c) for c in call_order))
        self.assertFalse(any("rendered_links.py" in str(c) for c in call_order))

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
        self.assertFalse(any(c == [module.NPM_EXECUTABLE, "test"] for c in call_order))
        self.assertTrue(any("python_style.py" in str(c) for c in call_order))
        self.assertTrue(any("cross_references.py" in str(c) for c in call_order))
        self.assertTrue(any("docs_index_freshness.py" in str(c) for c in call_order))
        self.assertTrue(any("sidebar_navigation_coverage.py" in str(c) for c in call_order))
        self.assertTrue(any("rendered_links.py" in str(c) for c in call_order))

    def test_sidebar_failure_stops_before_astro_steps(self):
        module = _load_module()
        call_order = []

        def fake_run(cmd, **kwargs):
            call_order.append(cmd)
            if "sidebar_navigation_coverage.py" in str(cmd):
                return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="sidebar fail")
            return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

        with patch("scripts.verify.run_all.subprocess.run", side_effect=fake_run):
            with patch("sys.argv", ["run_all.py"]):
                result = module.main()

        self.assertEqual(result, 1)
        self.assertTrue(any("sidebar_navigation_coverage.py" in str(c) for c in call_order))
        self.assertFalse(any(c == [module.NPM_EXECUTABLE, "run", "check"] for c in call_order))
        self.assertFalse(any(c == [module.NPM_EXECUTABLE, "run", "build"] for c in call_order))
        self.assertFalse(any("rendered_links.py" in str(c) for c in call_order))

    def test_rendered_links_failure_stops_after_build(self):
        module = _load_module()
        call_order = []

        def fake_run(cmd, **kwargs):
            call_order.append(cmd)
            if "rendered_links.py" in str(cmd):
                return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="rendered fail")
            return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

        with patch("scripts.verify.run_all.subprocess.run", side_effect=fake_run):
            with patch("sys.argv", ["run_all.py"]):
                result = module.main()

        self.assertEqual(result, 1)
        self.assertTrue(any(c == [module.NPM_EXECUTABLE, "run", "build"] for c in call_order))
        self.assertTrue(any("rendered_links.py" in str(c) for c in call_order))


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
        self.assertIn("blocking local verification", result.stdout)
        self.assertIn("Advisory checks", result.stdout)

    def test_module_docstring_mentions_cross_platform_blocking_path(self):
        module = _load_module()
        self.assertIn("cross-platform CI blocking path", module.__doc__)


if __name__ == "__main__":
    unittest.main()
