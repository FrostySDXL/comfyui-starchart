"""Unit tests for scripts/common/display_path.py.

Contract:
- In-repo absolute paths print as repo-relative posix strings.
- Out-of-repo absolute paths print as the basename only.
- ``None`` prints as the empty string.
- ``display_command`` replaces ``sys.executable`` as the first arg with "python".
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "common" / "display_path.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("display_path", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DisplayPathTests(unittest.TestCase):
    def test_in_repo_absolute_path_returns_repo_relative_posix(self):
        module = _load_module()
        fake_repo = Path(r"C:\fake\repo")
        inside = fake_repo / "references" / "raw" / "x.json"
        self.assertEqual(
            module.display_path(inside, repo_root=fake_repo),
            "references/raw/x.json",
        )

    def test_out_of_repo_absolute_path_returns_basename_only(self):
        module = _load_module()
        fake_repo = Path(r"C:\fake\repo")
        outside = Path(r"C:\example\tmp\outside\x.json")
        self.assertEqual(
            module.display_path(outside, repo_root=fake_repo),
            "x.json",
        )

    def test_none_returns_empty_string(self):
        module = _load_module()
        self.assertEqual(module.display_path(None, repo_root=Path(r"C:\fake\repo")), "")

    def test_display_command_replaces_sys_executable_with_python(self):
        module = _load_module()
        self.assertEqual(
            module.display_command([sys.executable, "scripts/verify/run_all.py", "--skip-tests"]),
            "python scripts/verify/run_all.py --skip-tests",
        )

    def test_display_path_accepts_string_input(self):
        module = _load_module()
        fake_repo = Path(r"C:\fake\repo")
        self.assertEqual(
            module.display_path(r"C:\fake\repo\references\raw\x.json", repo_root=fake_repo),
            "references/raw/x.json",
        )

    def test_display_command_preserves_non_python_first_arg(self):
        module = _load_module()
        self.assertEqual(
            module.display_command(["git", "status"]),
            "git status",
        )

    def test_display_command_redacts_absolute_path_args_to_basename(self):
        module = _load_module()
        # Simulates `git clone … <tmpdir>` where tmpdir is an absolute path.
        tmpdir = r"C:\example\tmp\tmpabc"
        result = module.display_command(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                "v0.20.1",
                "https://example.com/repo",
                tmpdir,
            ]
        )
        self.assertEqual(
            result,
            "git clone --depth 1 --branch v0.20.1 https://example.com/repo tmpabc",
        )

    def test_display_command_redacts_absolute_path_arg_after_sys_executable(self):
        module = _load_module()
        # Simulates `python scripts/x.py --input <abs-path>`.
        result = module.display_command(
            [sys.executable, "scripts/x.py", "--input", r"C:\example\tmp\thing.json"]
        )
        self.assertEqual(
            result,
            "python scripts/x.py --input thing.json",
        )


if __name__ == "__main__":
    unittest.main()
