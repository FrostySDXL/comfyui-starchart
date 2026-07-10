"""Tests for scripts/verify/markdown_top_level_spacing.py."""

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "markdown_top_level_spacing.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("markdown_top_level_spacing", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MarkdownTopLevelSpacingUnitTests(unittest.TestCase):
    """Unit tests for leading-space markdown verification."""

    def test_find_leading_space_issues(self):
        module = _load_module()
        cases = [
            (
                "indented top-level heading",
                "# Title\n\n ## Scope\n",
                [(3, " ## Scope")],
            ),
            (
                "indented metadata label",
                " **Last Updated:** 2026-05-07\n",
                [(1, " **Last Updated:** 2026-05-07")],
            ),
            (
                "fenced code block ignored",
                "```md\n ## Scope\n **Last Updated:** nope\n```\n",
                [],
            ),
            ("empty file", "", []),
            (
                "fenced block only file",
                "```python\n   ## Scope\n   **Last Updated:** no\n```\n",
                [],
            ),
            (
                "multiple fenced blocks toggle cleanly",
                "```md\n ## Scope\n```\n\n```text\n **Last Updated:** nope\n```\n\n  ## Real issue\n",
                [(9, "  ## Real issue")],
            ),
            (
                "deeply indented heading",
                "# Title\n\n   ### Deep heading\n",
                [(3, "   ### Deep heading")],
            ),
        ]

        for name, content, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(module.find_leading_space_issues(content), expected)

    def test_verify_directory_reports_repo_relative_paths(self):
        module = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            docs_dir = root / "src" / "content" / "docs"
            docs_dir.mkdir(parents=True)
            bad_file = docs_dir / "bad.md"
            bad_file.write_text("# Bad\n\n ## Scope\n", encoding="utf-8")

            issues = module.verify_docs_directory(root, docs_dir)

        self.assertEqual(issues, [("src/content/docs/bad.md", 3, " ## Scope")])


class MarkdownTopLevelSpacingScriptTests(unittest.TestCase):
    """CLI tests for markdown_top_level_spacing.py."""

    def test_help_flag(self):
        module = _load_module()
        stdout = io.StringIO()

        with patch.object(sys, "argv", [str(SCRIPT), "--help"]):
            with contextlib.redirect_stdout(stdout):
                with self.assertRaises(SystemExit) as exc:
                    module.main()

        self.assertEqual(exc.exception.code, 0)
        self.assertIn("top-level markdown", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
