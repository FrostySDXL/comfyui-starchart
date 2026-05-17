"""Tests for scripts/verify/community_page_coverage.py."""

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "community_page_coverage.py"


class CommunityPageCoverageUnitTests(unittest.TestCase):
    """Direct unit tests for coverage check logic."""

    def _import_module(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("community_page_coverage", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_detects_community_label_in_evidence_line(self):
        module = self._import_module()
        content = "# Title\n\n**Evidence:** Community pattern study based on pinned external version\n\n## Scope\n"
        self.assertTrue(module.has_community_evidence_label(content))

    def test_detects_community_label_plural(self):
        module = self._import_module()
        content = "# Title\n\n**Evidence:** Official docs-backed; Community pattern studies (case studies)\n\n## Scope\n"
        self.assertTrue(module.has_community_evidence_label(content))

    def test_extracts_exact_evidence_label(self):
        module = self._import_module()
        content = "# Title\n\n**Evidence:** Official docs-backed from docs.comfy.org; Community pattern study based on pinned external version\n"
        self.assertEqual(
            module.extract_evidence_label(content),
            "Official docs-backed from docs.comfy.org; Community pattern study based on pinned external version",
        )

    def test_ignores_community_mention_without_evidence_line(self):
        module = self._import_module()
        content = "# Checklist\n\n- Page mode is explicit (Reference, Community Pattern Study, or Scaffold)\n"
        self.assertFalse(module.has_community_evidence_label(content))

    def test_finds_labeled_pages(self):
        module = self._import_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_dir = Path(tmpdir) / "src" / "content" / "docs"
            docs_dir.mkdir(parents=True)
            (docs_dir / "page1.md").write_text(
                "**Evidence:** Community pattern study\n", encoding="utf-8"
            )
            (docs_dir / "page2.md").write_text(
                "**Evidence:** Official docs-backed\n", encoding="utf-8"
            )
            (docs_dir / "sub").mkdir(parents=True)
            (docs_dir / "sub" / "page3.md").write_text(
                "**Evidence:** Community pattern study based on pinned version\n", encoding="utf-8"
            )

            # Monkey-patch REPO_ROOT so relative paths resolve correctly
            old_repo_root = module.REPO_ROOT
            try:
                module.REPO_ROOT = Path(tmpdir)
                labeled = module.find_community_labeled_pages(docs_dir)
                self.assertIn("src/content/docs/page1.md", labeled)
                self.assertIn("src/content/docs/sub/page3.md", labeled)
                self.assertNotIn("src/content/docs/page2.md", labeled)
            finally:
                module.REPO_ROOT = old_repo_root

    def test_loads_tracked_pages(self):
        module = self._import_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "community_pages.json"
            data = {
                "pages": [
                    {"page_path": "src/content/docs/a.md"},
                    {"page_path": "src/content/docs/b.md"},
                ]
            }
            json_path.write_text(json.dumps(data), encoding="utf-8")
            tracked = module.load_tracked_pages(json_path)
            self.assertEqual(set(tracked), {"src/content/docs/a.md", "src/content/docs/b.md"})

    def test_loads_page_metadata(self):
        module = self._import_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "community_pages.json"
            data = {
                "pages": [
                    {
                        "page_path": "src/content/docs/a.md",
                        "evidence_label": "Community pattern study",
                        "page_kind": "hand_authored_study",
                        "source_type": "pinned_external_repo",
                    }
                ]
            }
            json_path.write_text(json.dumps(data), encoding="utf-8")
            tracked = module.load_tracked_pages(json_path)
            self.assertEqual(
                tracked["src/content/docs/a.md"]["evidence_label"], "Community pattern study"
            )

    def test_coverage_passes_when_complete(self):
        module = self._import_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            docs_dir = repo_root / "src" / "content" / "docs"
            docs_dir.mkdir(parents=True)
            (docs_dir / "page1.md").write_text(
                "**Evidence:** Community pattern study\n", encoding="utf-8"
            )

            json_path = repo_root / "community_pages.json"
            data = {
                "pages": [
                    {
                        "page_path": "src/content/docs/page1.md",
                        "evidence_label": "Community pattern study",
                    },
                ]
            }
            json_path.write_text(json.dumps(data), encoding="utf-8")

            old_repo_root = module.REPO_ROOT
            old_docs_dir = module.DOCS_DIR
            old_json_path = module.COMMUNITY_PAGES_JSON
            try:
                module.REPO_ROOT = repo_root
                module.DOCS_DIR = docs_dir
                module.COMMUNITY_PAGES_JSON = json_path
                result = module.main()
                self.assertEqual(result, 0)
            finally:
                module.REPO_ROOT = old_repo_root
                module.DOCS_DIR = old_docs_dir
                module.COMMUNITY_PAGES_JSON = old_json_path

    def test_coverage_fails_when_labeled_page_missing_from_json(self):
        module = self._import_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            docs_dir = repo_root / "src" / "content" / "docs"
            docs_dir.mkdir(parents=True)
            (docs_dir / "page1.md").write_text(
                "**Evidence:** Community pattern study\n", encoding="utf-8"
            )

            json_path = repo_root / "community_pages.json"
            data = {"pages": []}
            json_path.write_text(json.dumps(data), encoding="utf-8")

            old_repo_root = module.REPO_ROOT
            old_docs_dir = module.DOCS_DIR
            old_json_path = module.COMMUNITY_PAGES_JSON
            try:
                module.REPO_ROOT = repo_root
                module.DOCS_DIR = docs_dir
                module.COMMUNITY_PAGES_JSON = json_path
                result = module.main()
                self.assertEqual(result, 1)
            finally:
                module.REPO_ROOT = old_repo_root
                module.DOCS_DIR = old_docs_dir
                module.COMMUNITY_PAGES_JSON = old_json_path

    def test_coverage_fails_when_tracked_file_missing(self):
        module = self._import_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            docs_dir = repo_root / "src" / "content" / "docs"
            docs_dir.mkdir(parents=True)

            json_path = repo_root / "community_pages.json"
            data = {
                "pages": [
                    {"page_path": "src/content/docs/missing.md"},
                ]
            }
            json_path.write_text(json.dumps(data), encoding="utf-8")

            old_repo_root = module.REPO_ROOT
            old_docs_dir = module.DOCS_DIR
            old_json_path = module.COMMUNITY_PAGES_JSON
            try:
                module.REPO_ROOT = repo_root
                module.DOCS_DIR = docs_dir
                module.COMMUNITY_PAGES_JSON = json_path
                result = module.main()
                self.assertEqual(result, 1)
            finally:
                module.REPO_ROOT = old_repo_root
                module.DOCS_DIR = old_docs_dir
                module.COMMUNITY_PAGES_JSON = old_json_path

    def test_coverage_fails_when_evidence_label_drifts_from_metadata(self):
        module = self._import_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            docs_dir = repo_root / "src" / "content" / "docs"
            docs_dir.mkdir(parents=True)
            (docs_dir / "page1.md").write_text(
                "**Evidence:** Official docs-backed from docs.comfy.org; Community pattern study based on pinned external version\n",
                encoding="utf-8",
            )

            json_path = repo_root / "community_pages.json"
            data = {
                "pages": [
                    {
                        "page_path": "src/content/docs/page1.md",
                        "evidence_label": "Official docs-backed; Community pattern study",
                        "page_kind": "hand_authored_guide",
                        "source_type": "hybrid",
                    }
                ]
            }
            json_path.write_text(json.dumps(data), encoding="utf-8")

            old_repo_root = module.REPO_ROOT
            old_docs_dir = module.DOCS_DIR
            old_json_path = module.COMMUNITY_PAGES_JSON
            try:
                module.REPO_ROOT = repo_root
                module.DOCS_DIR = docs_dir
                module.COMMUNITY_PAGES_JSON = json_path
                result = module.main()
                self.assertEqual(result, 1)
            finally:
                module.REPO_ROOT = old_repo_root
                module.DOCS_DIR = old_docs_dir
                module.COMMUNITY_PAGES_JSON = old_json_path

    def test_repo_local_policy_page_does_not_emit_orphan_warning(self):
        module = self._import_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            docs_dir = repo_root / "src" / "content" / "docs" / "reference"
            docs_dir.mkdir(parents=True)
            (docs_dir / "community-maintenance-policy.md").write_text(
                "**Evidence:** Operational guidance\n", encoding="utf-8"
            )

            json_path = repo_root / "community_pages.json"
            data = {
                "pages": [
                    {
                        "page_path": "src/content/docs/reference/community-maintenance-policy.md",
                        "evidence_label": "Operational guidance",
                        "page_kind": "hand_authored_policy",
                        "source_type": "repo_local",
                    }
                ]
            }
            json_path.write_text(json.dumps(data), encoding="utf-8")

            old_repo_root = module.REPO_ROOT
            old_docs_dir = module.DOCS_DIR
            old_json_path = module.COMMUNITY_PAGES_JSON
            try:
                module.REPO_ROOT = repo_root
                module.DOCS_DIR = repo_root / "src" / "content" / "docs"
                module.COMMUNITY_PAGES_JSON = json_path
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    result = module.main()
                self.assertEqual(result, 0)
                self.assertNotIn("Community page coverage warnings", stdout.getvalue())
            finally:
                module.REPO_ROOT = old_repo_root
                module.DOCS_DIR = old_docs_dir
                module.COMMUNITY_PAGES_JSON = old_json_path

    def test_non_policy_tracked_page_without_community_label_still_warns(self):
        module = self._import_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            docs_dir = repo_root / "src" / "content" / "docs"
            docs_dir.mkdir(parents=True)
            (docs_dir / "guide.md").write_text(
                "**Evidence:** Official docs-backed from docs.comfy.org\n", encoding="utf-8"
            )

            json_path = repo_root / "community_pages.json"
            data = {
                "pages": [
                    {
                        "page_path": "src/content/docs/guide.md",
                        "evidence_label": "Official docs-backed from docs.comfy.org",
                        "page_kind": "hand_authored_guide",
                        "source_type": "hybrid",
                    }
                ]
            }
            json_path.write_text(json.dumps(data), encoding="utf-8")

            old_repo_root = module.REPO_ROOT
            old_docs_dir = module.DOCS_DIR
            old_json_path = module.COMMUNITY_PAGES_JSON
            try:
                module.REPO_ROOT = repo_root
                module.DOCS_DIR = docs_dir
                module.COMMUNITY_PAGES_JSON = json_path
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    result = module.main()
                self.assertEqual(result, 0)
                self.assertIn("Community page coverage warnings", stdout.getvalue())
                self.assertIn("src/content/docs/guide.md", stdout.getvalue())
            finally:
                module.REPO_ROOT = old_repo_root
                module.DOCS_DIR = old_docs_dir
                module.COMMUNITY_PAGES_JSON = old_json_path


class CommunityPageCoverageScriptTests(unittest.TestCase):
    """Tests that the coverage script runs successfully on the real repo."""

    def test_script_runs(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        # Should pass (0) because all community-labeled pages are tracked
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Community page coverage is complete", result.stdout)


if __name__ == "__main__":
    unittest.main()
