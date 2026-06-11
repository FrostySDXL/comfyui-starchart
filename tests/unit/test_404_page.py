"""Tests for the custom 404 page content contract."""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PAGE_PATH = REPO_ROOT / "src" / "pages" / "404.astro"
DOCS_ROOT = REPO_ROOT / "src" / "content" / "docs"


class TestFourOhFourPageContent(unittest.TestCase):
    """Validate the custom 404 page remains minimal and user-facing."""

    def test_404_page_file_exists_and_not_under_docs_root(self):
        """The 404 page should be an Astro page, not a docs collection route."""
        self.assertTrue(PAGE_PATH.is_file())
        self.assertNotIn(DOCS_ROOT, PAGE_PATH.parents)

    def test_404_page_contains_heading_and_body_paragraph(self):
        """The page should contain the required heading and body paragraph."""
        content = PAGE_PATH.read_text(encoding="utf-8")

        self.assertIn("Page not found", content)
        self.assertRegex(content, r"<p[\s>]")

    def test_404_page_lists_three_or_more_navigation_targets(self):
        """The page should link to enough recovery targets for stranded readers."""
        content = PAGE_PATH.read_text(encoding="utf-8")
        targets = (
            "Home",
            "start-here/tooling-builder",
            "reference/topic-scope",
            "github.com/FrostySDXL/comfyui-starchart",
        )

        self.assertGreaterEqual(sum(target in content for target in targets), 3)

    def test_404_page_uses_starlight_markdown_content_class(self):
        """The page should use Starlight's markdown body class."""
        content = PAGE_PATH.read_text(encoding="utf-8")

        self.assertTrue(re.search(r'class=["\'][^"\']*sl-markdown-content', content))


if __name__ == "__main__":
    unittest.main()
