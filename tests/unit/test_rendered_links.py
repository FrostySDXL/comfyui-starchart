"""Tests for rendered_links.py verification script."""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_module():
    """Load the rendered_links module."""
    spec = importlib.util.spec_from_file_location(
        "rendered_links",
        REPO_ROOT / "scripts" / "verify" / "rendered_links.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RenderedLinksImportTests(unittest.TestCase):
    """Test that rendered_links.py is importable and has expected functions."""

    def test_module_imports(self):
        """The rendered_links module should be importable."""
        module = load_module()
        self.assertTrue(hasattr(module, "extract_internal_links"))
        self.assertTrue(hasattr(module, "resolve_link"))
        self.assertTrue(hasattr(module, "link_to_dist_path"))
        self.assertTrue(hasattr(module, "verify_all_links"))

    def test_docstring_describes_purpose(self):
        """The module docstring should describe its purpose."""
        module = load_module()
        self.assertIn("internal navigation links", module.__doc__)
        self.assertIn("built HTML", module.__doc__)


class ExtractInternalLinksTests(unittest.TestCase):
    """Test the extract_internal_links function."""

    def setUp(self):
        self.module = load_module()
        self.site_base = "/comfyui-starchart"

    def test_extracts_absolute_internal_links(self):
        """Should extract links starting with site base."""
        html = '<a href="/comfyui-starchart/reference/glossary/">Glossary</a>'
        links = self.module.extract_internal_links(html, self.site_base)
        self.assertEqual(links, ["/comfyui-starchart/reference/glossary/"])

    def test_skips_external_links(self):
        """Should skip http/https links."""
        html = '<a href="https://docs.comfy.org/">External</a>'
        links = self.module.extract_internal_links(html, self.site_base)
        self.assertEqual(links, [])

    def test_skips_anchor_only_links(self):
        """Should skip anchor-only links."""
        html = '<a href="#section">Section</a>'
        links = self.module.extract_internal_links(html, self.site_base)
        self.assertEqual(links, [])

    def test_skips_static_assets(self):
        """Should skip links to CSS, JS, SVG, and other static files."""
        html = """
        <link href="/comfyui-starchart/_astro/common.css">
        <a href="/comfyui-starchart/favicon.svg">Icon</a>
        <a href="/comfyui-starchart/sitemap-index.xml">Sitemap</a>
        """
        links = self.module.extract_internal_links(html, self.site_base)
        self.assertEqual(links, [])

    def test_skips_astro_build_artifacts(self):
        """Should skip _astro and pagefind directories."""
        html = """
        <a href="/comfyui-starchart/_astro/something/">Astro</a>
        <a href="/comfyui-starchart/pagefind/search/">Search</a>
        """
        links = self.module.extract_internal_links(html, self.site_base)
        self.assertEqual(links, [])

    def test_extracts_relative_page_links(self):
        """Should extract relative links that look like page navigation."""
        html = '<a href="source-evidence-policy/">Policy</a>'
        links = self.module.extract_internal_links(html, self.site_base)
        self.assertEqual(links, ["source-evidence-policy/"])


class ResolveLinkTests(unittest.TestCase):
    """Test the resolve_link function."""

    def setUp(self):
        self.module = load_module()
        self.site_base = "/comfyui-starchart"

    def test_absolute_link_unchanged(self):
        """Absolute links starting with site base should be unchanged."""
        result = self.module.resolve_link(
            "/comfyui-starchart/reference/glossary/",
            "/comfyui-starchart/api/",
            self.site_base,
        )
        self.assertEqual(result, "/comfyui-starchart/reference/glossary/")

    def test_relative_link_resolved(self):
        """Relative links should be resolved against page URL."""
        result = self.module.resolve_link(
            "source-evidence-policy/",
            "/comfyui-starchart/reference/glossary/",
            self.site_base,
        )
        self.assertEqual(result, "/comfyui-starchart/reference/glossary/source-evidence-policy/")

    def test_parent_directory_link_resolved(self):
        """Parent directory links should be resolved correctly."""
        result = self.module.resolve_link(
            "../api/prompt-submission/",
            "/comfyui-starchart/deep-dives/workflow/",
            self.site_base,
        )
        self.assertEqual(result, "/comfyui-starchart/deep-dives/api/prompt-submission/")


class LinkToDistPathTests(unittest.TestCase):
    """Test the link_to_dist_path function."""

    def setUp(self):
        self.module = load_module()
        self.site_base = "/comfyui-starchart"

    def test_directory_link_to_index_html(self):
        """Directory links should map to index.html."""
        result = self.module.link_to_dist_path(
            "/comfyui-starchart/reference/glossary/", self.site_base
        )
        self.assertEqual(result, "reference/glossary/index.html")

    def test_root_link_to_index_html(self):
        """Root link should map to index.html."""
        result = self.module.link_to_dist_path("/comfyui-starchart/", self.site_base)
        self.assertEqual(result, "index.html")


class RenderedLinksScriptTests(unittest.TestCase):
    """Test that the script runs correctly on the repo."""

    def test_script_runs_on_valid_fixture(self):
        """The script should run without error on a valid fixture dist tree."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dist_dir = Path(tmpdir)
            source_dir = dist_dir / "reference"
            source_dir.mkdir(parents=True)
            (source_dir / "index.html").write_text(
                '<a href="/comfyui-starchart/reference/glossary/">Glossary</a>',
                encoding="utf-8",
            )
            glossary_dir = source_dir / "glossary"
            glossary_dir.mkdir()
            (glossary_dir / "index.html").write_text("<html></html>", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "verify" / "rendered_links.py"),
                    "--dist-dir",
                    str(dist_dir),
                ],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
            )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("All internal navigation links are valid", result.stdout)

    def test_script_fails_on_missing_dist(self):
        """The script should fail gracefully when dist/ doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "verify" / "rendered_links.py"),
                    "--dist-dir",
                    str(Path(tmpdir) / "nonexistent"),
                ],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("dist directory not found", result.stdout)


class RenderedLinksDetectionTests(unittest.TestCase):
    """Test that the script detects broken links."""

    def setUp(self):
        self.module = load_module()

    def test_detects_broken_link(self):
        """Should detect a link to a non-existent page."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dist_dir = Path(tmpdir)
            # Create a page with a broken link
            page_dir = dist_dir / "test"
            page_dir.mkdir()
            html_file = page_dir / "index.html"
            html_file.write_text(
                '<a href="/comfyui-starchart/nonexistent/">Broken</a>',
                encoding="utf-8",
            )

            broken = self.module.verify_all_links(dist_dir, "/comfyui-starchart")
            self.assertEqual(len(broken), 1)
            # Normalize path separators for cross-platform compatibility
            broken_keys = [k.replace("\\", "/") for k in broken.keys()]
            self.assertIn("test/index.html", broken_keys)

    def test_passes_valid_link(self):
        """Should pass when link target exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dist_dir = Path(tmpdir)
            # Create source page
            source_dir = dist_dir / "source"
            source_dir.mkdir()
            source_html = source_dir / "index.html"
            source_html.write_text(
                '<a href="/comfyui-starchart/target/">Valid</a>',
                encoding="utf-8",
            )
            # Create target page
            target_dir = dist_dir / "target"
            target_dir.mkdir()
            target_html = target_dir / "index.html"
            target_html.write_text("<html></html>", encoding="utf-8")

            broken = self.module.verify_all_links(dist_dir, "/comfyui-starchart")
            self.assertEqual(len(broken), 0)

    def test_passes_valid_relative_link(self):
        """Should pass when a relative link resolves to an existing page."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dist_dir = Path(tmpdir)
            # Create a parent page that links to a sibling page with a relative path
            parent_dir = dist_dir / "reference"
            parent_dir.mkdir()
            parent_html = parent_dir / "index.html"
            parent_html.write_text(
                '<a href="glossary/">Glossary</a>',
                encoding="utf-8",
            )
            # Create the sibling page
            sibling_dir = parent_dir / "glossary"
            sibling_dir.mkdir()
            sibling_html = sibling_dir / "index.html"
            sibling_html.write_text("<html></html>", encoding="utf-8")

            broken = self.module.verify_all_links(dist_dir, "/comfyui-starchart")
            self.assertEqual(len(broken), 0)


if __name__ == "__main__":
    unittest.main()
