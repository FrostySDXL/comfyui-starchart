"""Unit tests for scripts/common/display_path.py.

Contract:
- In-repo absolute paths print as repo-relative posix strings.
- Out-of-repo absolute paths print as the basename only.
- ``None`` prints as the empty string.
- ``display_command`` replaces ``sys.executable`` as the first arg with "python".
"""

from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "common" / "display_path.py"

# Use platform-appropriate absolute paths so the tests exercise the
# ``is_absolute() == True`` branch on both Windows and POSIX runners.
# ``Path("/foo")`` is absolute on POSIX but drive-relative (not
# absolute) on Windows, so a naive forward-slash literal would silently
# change test semantics across platforms.
FAKE_REPO = Path("C:/fake/repo") if os.name == "nt" else Path("/fake/repo")
ABS_OUTSIDE_TMP = Path("C:/example/tmp") if os.name == "nt" else Path("/example/tmp")
ABS_OUTSIDE_FILE = (
    Path("C:/example/tmp/outside/x.json")
    if os.name == "nt"
    else Path("/example/tmp/outside/x.json")
)


def _load_module():
    spec = importlib.util.spec_from_file_location("display_path", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DisplayPathTests(unittest.TestCase):
    def test_in_repo_absolute_path_returns_repo_relative_posix(self):
        module = _load_module()
        inside = FAKE_REPO / "references" / "raw" / "x.json"
        self.assertEqual(
            module.display_path(inside, repo_root=FAKE_REPO),
            "references/raw/x.json",
        )

    def test_out_of_repo_absolute_path_returns_basename_only(self):
        module = _load_module()
        self.assertEqual(
            module.display_path(ABS_OUTSIDE_FILE, repo_root=FAKE_REPO),
            "x.json",
        )

    def test_none_returns_empty_string(self):
        module = _load_module()
        self.assertEqual(module.display_path(None, repo_root=FAKE_REPO), "")

    def test_display_command_replaces_sys_executable_with_python(self):
        module = _load_module()
        self.assertEqual(
            module.display_command([sys.executable, "scripts/verify/run_all.py", "--skip-tests"]),
            "python scripts/verify/run_all.py --skip-tests",
        )

    def test_display_path_accepts_string_input(self):
        module = _load_module()
        inside_str = str(FAKE_REPO / "references" / "raw" / "x.json")
        self.assertEqual(
            module.display_path(inside_str, repo_root=FAKE_REPO),
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
        tmpdir = str(ABS_OUTSIDE_TMP / "tmpabc")
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
            [sys.executable, "scripts/x.py", "--input", str(ABS_OUTSIDE_TMP / "thing.json")]
        )
        self.assertEqual(
            result,
            "python scripts/x.py --input thing.json",
        )

    def test_display_command_preserves_non_https_url_with_drive_like_prefix(self):
        module = _load_module()
        # A URL whose first component is a single ASCII letter followed by ``://``
        # must NOT be redacted, even on Windows where ``Path("g://...").is_absolute()``
        # could otherwise be confused with a drive letter.
        result = module.display_command(
            ["git", "clone", "git://github.com/user/repo.git", str(ABS_OUTSIDE_TMP / "dest")]
        )
        self.assertEqual(
            result,
            "git clone git://github.com/user/repo.git dest",
        )

    def test_display_path_preserves_url_with_drive_like_prefix(self):
        module = _load_module()
        # ``g://host/path`` must pass through unchanged, not be redacted to ``path``.
        self.assertEqual(
            module.display_path("g://host/path", repo_root=FAKE_REPO),
            "g://host/path",
        )


if __name__ == "__main__":
    unittest.main()
