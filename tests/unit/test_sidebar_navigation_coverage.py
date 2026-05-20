"""Tests for scripts/verify/sidebar_navigation_coverage.py."""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "sidebar_navigation_coverage.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("sidebar_navigation_coverage", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SidebarNavigationCoverageUnitTests(unittest.TestCase):
    """Unit tests for sidebar coverage logic."""

    def test_collect_sidebar_paths_accepts_nested_valid_entries(self):
        module = _load_module()
        entries = [
            {"label": "Home", "path": "index.md"},
            {
                "label": "Reference",
                "items": [
                    {"label": "Glossary", "path": "reference/glossary.md"},
                    {"label": "API", "path": "reference/api.md"},
                ],
            },
        ]

        paths, errors = module.collect_sidebar_paths(entries)

        self.assertEqual(paths, ["index.md", "reference/glossary.md", "reference/api.md"])
        self.assertEqual(errors, [])

    def test_collect_sidebar_paths_reports_non_markdown_path(self):
        module = _load_module()

        paths, errors = module.collect_sidebar_paths([{"label": "Bad", "path": "index"}])

        self.assertEqual(paths, ["index"])
        self.assertIn("Sidebar page path must end in .md: index (Bad)", errors)

    def test_collect_sidebar_paths_reports_invalid_entry(self):
        module = _load_module()

        paths, errors = module.collect_sidebar_paths([{"label": "Broken"}])

        self.assertEqual(paths, [])
        self.assertIn("Invalid sidebar entry at Broken: expected path or items", errors)

    def test_collect_hand_authored_docs_paths_excludes_generated_pages(self):
        module = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            (docs_root / "reference").mkdir(parents=True)
            (docs_root / "reference" / "glossary.md").write_text("# Glossary\n", encoding="utf-8")
            (docs_root / "reference" / "server-py-summary.md").write_text(
                "# Generated\n", encoding="utf-8"
            )
            (docs_root / "ecosystem").mkdir(parents=True)
            (docs_root / "ecosystem" / "map.md").write_text("# Generated\n", encoding="utf-8")

            collected = module.collect_hand_authored_docs_paths(docs_root)

        self.assertEqual(collected, {"reference/glossary.md"})


class SidebarNavigationCoverageScriptTests(unittest.TestCase):
    """CLI tests for sidebar_navigation_coverage.py."""

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("sidebar", result.stdout.lower())

    def test_script_runs_and_passes(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Sidebar navigation coverage is complete.", result.stdout)


if __name__ == "__main__":
    unittest.main()
