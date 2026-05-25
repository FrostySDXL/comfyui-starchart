"""Tests for scripts/common/published_docs_surface.py."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.common import published_docs_surface


class PublishedDocsSurfaceTests(unittest.TestCase):
    def _write_sidebar_data(self, root: Path, entries: list[dict[str, object]]) -> Path:
        sidebar_path = root / "src" / "site" / "sidebar-data.json"
        sidebar_path.parent.mkdir(parents=True, exist_ok=True)
        sidebar_path.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
        return sidebar_path

    def _write_page(self, root: Path, relative_path: str, body: str) -> None:
        page_path = root / "src" / "content" / "docs" / Path(relative_path)
        page_path.parent.mkdir(parents=True, exist_ok=True)
        page_path.write_text(body, encoding="utf-8")

    def test_flatten_sidebar_nav_and_base_entry_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nav_source = self._write_sidebar_data(
                root,
                [
                    {"label": "Home", "path": "index.md"},
                    {
                        "label": "Start Here",
                        "items": [
                            {"label": "Tooling Builder", "path": "start-here/tooling-builder.md"}
                        ],
                    },
                ],
            )
            self._write_page(
                root,
                "index.md",
                "\n".join(
                    [
                        "---",
                        'title: "Docs Home"',
                        "---",
                        "",
                        "**Evidence:** Operational guidance",
                        "",
                        "## Scope",
                        "",
                        "Home summary.",
                    ]
                )
                + "\n",
            )
            self._write_page(
                root,
                "start-here/tooling-builder.md",
                "\n".join(
                    [
                        "---",
                        'title: "Start Here: Tooling Builder"',
                        "---",
                        "",
                        "**Evidence:** Operational guidance",
                        "",
                        "## Scope",
                        "",
                        "Tooling summary.",
                    ]
                )
                + "\n",
            )

            pages = published_docs_surface.build_published_docs_surface(
                root,
                nav_source,
                root / "src" / "content" / "docs",
            )

            self.assertEqual(
                [page["path"] for page in pages], ["index.md", "start-here/tooling-builder.md"]
            )
            self.assertEqual(
                set(pages[1].keys()),
                {"title", "path", "nav_section", "audience", "evidence", "summary"},
            )
            self.assertEqual(pages[1]["nav_section"], "Start Here")
            self.assertEqual(pages[1]["audience"], "consumer")

    def test_title_evidence_and_scope_extractors(self):
        text = "\n".join(
            [
                "---",
                'title: "Frontmatter Title"',
                "---",
                "",
                "**Evidence:** Source-backed from pinned snapshots",
                "",
                "## Scope",
                "",
                "First paragraph.",
                "",
                "Second paragraph omitted.",
            ]
        )
        self.assertEqual(
            published_docs_surface.extract_title(text, "fallback"), "Frontmatter Title"
        )
        self.assertEqual(
            published_docs_surface.extract_evidence(text),
            "Source-backed from pinned snapshots",
        )
        self.assertEqual(published_docs_surface.extract_scope_summary(text), "First paragraph.")

    def test_generated_page_detection_and_exclusion_behavior(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nav_source = self._write_sidebar_data(
                root,
                [
                    {"label": "Home", "path": "index.md"},
                    {"label": "Map", "path": "ecosystem/map.md"},
                ],
            )
            self._write_page(
                root,
                "index.md",
                '---\ntitle: "Home"\n---\n\n## Scope\n\nHome summary.\n',
            )
            self._write_page(
                root,
                "ecosystem/map.md",
                "<!-- GENERATED FILE: do not edit directly -->\n\n## Scope\n\nGenerated summary.\n",
            )

            self.assertTrue(
                published_docs_surface.is_generated_page(
                    "<!-- GENERATED FILE: do not edit directly -->\n"
                )
            )
            pages = published_docs_surface.build_published_docs_surface(
                root,
                nav_source,
                root / "src" / "content" / "docs",
            )
            self.assertEqual([page["path"] for page in pages], ["index.md"])

    def test_non_generated_reference_page_is_no_longer_excluded_by_deleted_page_list(self):
        nav_entry = {
            "nav_label": "Server Py Summary",
            "nav_section": "Reference",
            "path": "reference/server-py-summary.md",
        }
        with tempfile.TemporaryDirectory() as tmp:
            docs_root = Path(tmp)
            page_path = docs_root / "reference" / "server-py-summary.md"
            page_path.parent.mkdir(parents=True, exist_ok=True)
            page_path.write_text('---\ntitle: "Server Py Summary"\n---\n', encoding="utf-8")
            self.assertEqual(
                published_docs_surface.build_page_entry(nav_entry, docs_root),
                {
                    "title": "Server Py Summary",
                    "path": "reference/server-py-summary.md",
                    "nav_section": "Reference",
                    "audience": None,
                    "evidence": None,
                    "summary": None,
                },
            )


if __name__ == "__main__":
    unittest.main()
