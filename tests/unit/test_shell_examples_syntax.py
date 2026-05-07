"""Tests for scripts/verify/shell_examples_syntax.py."""

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "shell_examples_syntax.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("shell_examples_syntax", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ShellExamplesSyntaxUnitTests(unittest.TestCase):
    """Unit tests for shell example discovery and validation."""

    def test_discover_example_shell_scripts_returns_sorted_repo_relative_paths(self):
        module = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            first = root / "examples" / "b.sh"
            second = root / "examples" / "nested" / "a.sh"
            second.parent.mkdir(parents=True)
            first.parent.mkdir(parents=True, exist_ok=True)
            first.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            second.write_text("#!/usr/bin/env bash\n", encoding="utf-8")

            discovered = module.discover_example_shell_scripts(root)

        self.assertEqual(discovered, [Path("examples/b.sh"), Path("examples/nested/a.sh")])

    def test_validate_shell_scripts_returns_zero_when_no_scripts_found(self):
        module = _load_module()

        with patch.object(module, "find_bash_executable", return_value="/bin/bash"):
            with patch("subprocess.run") as mock_run:
                result = module.validate_shell_scripts(REPO_ROOT, [])

        self.assertEqual(result, 0)
        mock_run.assert_not_called()

    def test_validate_shell_scripts_uses_bash_n(self):
        module = _load_module()

        with patch.object(module, "find_bash_executable", return_value="/bin/bash"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess(
                    ["/bin/bash", "-n", "examples/demo.sh"],
                    0,
                    stdout="",
                    stderr="",
                )

                result = module.validate_shell_scripts(REPO_ROOT, [Path("examples/demo.sh")])

        self.assertEqual(result, 0)
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertEqual(args[0][:2], ["/bin/bash", "-n"])
        self.assertEqual(kwargs["cwd"], str(REPO_ROOT))

    def test_find_bash_executable_uses_explicit_override_first(self):
        module = _load_module()

        with patch.object(module.shutil, "which", side_effect=lambda value: None):
            with patch.dict(os.environ, {"COMFYUI_KB_BASH": "/env/bash"}, clear=False):
                with patch.object(module.Path, "exists", return_value=True):
                    result = module.find_bash_executable("/explicit/bash")

        self.assertEqual(result, str(module.Path("/explicit/bash")))

    def test_find_bash_executable_uses_env_var_when_no_override(self):
        module = _load_module()

        with patch.object(module.shutil, "which", side_effect=lambda value: None):
            with patch.dict(os.environ, {"COMFYUI_KB_BASH": "/env/bash"}, clear=False):
                with patch.object(module.Path, "exists", return_value=True):
                    result = module.find_bash_executable()

        self.assertEqual(result, str(module.Path("/env/bash")))

    def test_validate_shell_scripts_fails_when_bash_missing(self):
        module = _load_module()

        with patch.object(module, "find_bash_executable", return_value=None):
            result = module.validate_shell_scripts(REPO_ROOT, [Path("examples/demo.sh")])

        self.assertEqual(result, 1)

    def test_validate_shell_scripts_fails_when_bash_reports_syntax_error(self):
        module = _load_module()

        with patch.object(module, "find_bash_executable", return_value="/bin/bash"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess(
                    ["/bin/bash", "-n", "examples/demo.sh"],
                    2,
                    stdout="",
                    stderr="syntax error\n",
                )

                result = module.validate_shell_scripts(REPO_ROOT, [Path("examples/demo.sh")])

        self.assertEqual(result, 1)


class ShellExamplesSyntaxScriptTests(unittest.TestCase):
    """CLI-level tests for shell_examples_syntax.py."""

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("examples", result.stdout)
        self.assertIn("bash -n", result.stdout)
        self.assertIn("--bash-executable", result.stdout)


if __name__ == "__main__":
    unittest.main()
