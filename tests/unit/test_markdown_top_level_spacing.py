"""Tests for scripts/verify/markdown_top_level_spacing.py."""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "markdown_top_level_spacing.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("markdown_top_level_spacing", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MarkdownTopLevelSpacingUnitTests(unittest.TestCase):
    """Unit tests for leading-space markdown verification."""

    def test_detects_indented_top_level_heading(self):
        module = _load_module()
        issues = module.find_leading_space_issues("# Title\n\n ## Scope\n")
        self.assertEqual(issues, [(3, " ## Scope")])

    def test_detects_indented_metadata_label(self):
        module = _load_module()
        issues = module.find_leading_space_issues(" **Last Updated:** 2026-05-07\n")
        self.assertEqual(issues, [(1, " **Last Updated:** 2026-05-07")])

    def test_ignores_fenced_code_blocks(self):
        module = _load_module()
        content = "```md\n ## Scope\n **Last Updated:** nope\n```\n"
        issues = module.find_leading_space_issues(content)
        self.assertEqual(issues, [])

    def test_verify_directory_reports_repo_relative_paths(self):
        module = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            docs_dir = root / "docs"
            docs_dir.mkdir()
            bad_file = docs_dir / "bad.md"
            bad_file.write_text("# Bad\n\n ## Scope\n", encoding="utf-8")

            issues = module.verify_docs_directory(root, docs_dir)

        self.assertEqual(issues, [("docs/bad.md", 3, " ## Scope")])


class MarkdownTopLevelSpacingScriptTests(unittest.TestCase):
    """CLI tests for markdown_top_level_spacing.py."""

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("top-level markdown", result.stdout)


if __name__ == "__main__":
    unittest.main()
