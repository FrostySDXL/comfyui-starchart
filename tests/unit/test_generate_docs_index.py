"""Tests for scripts/generate/generate_docs_index.py."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "generate" / "generate_docs_index.py"

spec = importlib.util.spec_from_file_location("generate_docs_index", SCRIPT)
generate_docs_index = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_docs_index)


class GenerateDocsIndexTests(unittest.TestCase):
    def _with_temp_repo_paths(self, root: Path):
        old_docs_root = generate_docs_index.DOCS_ROOT
        old_default_nav_source = generate_docs_index.DEFAULT_NAV_SOURCE
        generate_docs_index.DOCS_ROOT = root / "src" / "content" / "docs"
        generate_docs_index.DEFAULT_NAV_SOURCE = root / "src" / "site" / "sidebar-data.json"
        self.addCleanup(setattr, generate_docs_index, "DOCS_ROOT", old_docs_root)
        self.addCleanup(setattr, generate_docs_index, "DEFAULT_NAV_SOURCE", old_default_nav_source)

    def _write_sidebar_data(self, root: Path, entries: list[dict[str, object]]) -> None:
        sidebar_path = root / "src" / "site" / "sidebar-data.json"
        sidebar_path.parent.mkdir(parents=True, exist_ok=True)
        sidebar_path.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")

    def _write_page(
        self, root: Path, relative_path: str, title: str, evidence: str, scope: str
    ) -> None:
        page_path = root / "src" / "content" / "docs" / Path(relative_path)
        page_path.parent.mkdir(parents=True, exist_ok=True)
        page_path.write_text(
            "\n".join(
                [
                    "---",
                    f'title: "{title}"',
                    "---",
                    "",
                    f"**Evidence:** {evidence}",
                    "**Last Updated:** 2026-05-03",
                    "",
                    "## Scope",
                    "",
                    scope,
                    "",
                    "## Read Next",
                    "",
                    "- Example",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def test_build_docs_index_is_deterministic_and_extracts_expected_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._write_sidebar_data(
                root,
                [
                    {"label": "Home", "path": "index.md"},
                    {
                        "label": "Start Here",
                        "items": [
                            {"label": "Tooling Builder", "path": "start-here/tooling-builder.md"}
                        ],
                    },
                    {
                        "label": "Orientation",
                        "items": [
                            {
                                "label": "Troubleshooting",
                                "items": [
                                    {
                                        "label": "Troubleshooting",
                                        "path": "troubleshooting/index.md",
                                    },
                                    {
                                        "label": "API Integration",
                                        "path": "troubleshooting/api-integration.md",
                                    },
                                ],
                            }
                        ],
                    },
                ],
            )

            self._write_page(
                root,
                "index.md",
                "Docs Home",
                "Source-backed from pinned snapshots",
                "Home summary.",
            )
            self._write_page(
                root,
                "start-here/tooling-builder.md",
                "Start Here: Tooling Builder",
                "Operational guidance",
                "Tooling summary line.",
            )
            self._write_page(
                root,
                "troubleshooting/index.md",
                "Troubleshooting",
                "Operational guidance",
                "Troubleshooting summary first sentence.",
            )
            self._write_page(
                root,
                "troubleshooting/api-integration.md",
                "API Integration Troubleshooting",
                "Operational guidance",
                "API troubleshooting summary.",
            )

            first = generate_docs_index.build_docs_index(root)
            second = generate_docs_index.build_docs_index(root)

            self.assertEqual(first, second)
            self.assertEqual(
                [page["path"] for page in first["pages"]],
                [
                    "index.md",
                    "start-here/tooling-builder.md",
                    "troubleshooting/index.md",
                    "troubleshooting/api-integration.md",
                ],
            )
            tooling_entry = first["pages"][1]
            self.assertEqual(tooling_entry["title"], "Start Here: Tooling Builder")
            self.assertEqual(tooling_entry["nav_section"], "Start Here")
            self.assertEqual(tooling_entry["audience"], "consumer")
            self.assertEqual(tooling_entry["evidence"], "Operational guidance")
            self.assertEqual(tooling_entry["summary"], "Tooling summary line.")

            troubleshooting_entry = first["pages"][3]
            self.assertEqual(troubleshooting_entry["nav_section"], "Orientation / Troubleshooting")

    def test_scope_summary_uses_first_non_empty_paragraph_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._write_sidebar_data(root, [{"label": "Home", "path": "index.md"}])
            page_path = root / "src" / "content" / "docs" / "index.md"
            page_path.parent.mkdir(parents=True, exist_ok=True)
            page_path.write_text(
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
                        "First paragraph stays.",
                        "",
                        "Second paragraph is intentionally omitted.",
                        "",
                        "## Read Next",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            docs_index = generate_docs_index.build_docs_index(root)
            self.assertEqual(docs_index["pages"][0]["summary"], "First paragraph stays.")

    def test_excludes_generated_pages_even_if_listed_in_nav(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._write_sidebar_data(
                root,
                [
                    {"label": "Home", "path": "index.md"},
                    {
                        "label": "Ecosystem",
                        "items": [{"label": "Map", "path": "ecosystem/map.md"}],
                    },
                ],
            )

            self._write_page(root, "index.md", "Docs Home", "Operational guidance", "Home summary.")
            generated_path = root / "src" / "content" / "docs" / "ecosystem" / "map.md"
            generated_path.parent.mkdir(parents=True, exist_ok=True)
            generated_path.write_text(
                "\n".join(
                    [
                        "<!-- GENERATED FILE: do not edit directly -->",
                        "",
                        "---",
                        'title: "Ecosystem Map"',
                        "---",
                        "",
                        "**Evidence:** Community pattern study",
                        "",
                        "## Scope",
                        "",
                        "Generated summary.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            docs_index = generate_docs_index.build_docs_index(root)
            self.assertEqual([page["path"] for page in docs_index["pages"]], ["index.md"])

    def test_excludes_known_generated_paths_even_without_banner_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._write_sidebar_data(
                root,
                [
                    {"label": "Home", "path": "index.md"},
                    {
                        "label": "Reference",
                        "items": [
                            {
                                "label": "Server Py Summary",
                                "path": "reference/server-py-summary.md",
                            }
                        ],
                    },
                ],
            )

            self._write_page(root, "index.md", "Docs Home", "Operational guidance", "Home summary.")
            self._write_page(
                root,
                "reference/server-py-summary.md",
                "Server.py Summary",
                "Operational guidance",
                "Generated reference summary.",
            )

            docs_index = generate_docs_index.build_docs_index(root)
            self.assertEqual([page["path"] for page in docs_index["pages"]], ["index.md"])

    def test_sidebar_nav_can_preserve_checked_in_nav_section_semantics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._write_sidebar_data(
                root,
                [
                    {
                        "label": "Orientation",
                        "items": [
                            {
                                "label": "What's New",
                                "path": "whats-new/index.md",
                                "docs_index_nav_section": "Orientation / What's New",
                            },
                            {
                                "label": "Troubleshooting",
                                "items": [
                                    {"label": "Troubleshooting", "path": "troubleshooting/index.md"}
                                ],
                            },
                        ],
                    }
                ],
            )

            self._write_page(
                root,
                "whats-new/index.md",
                "What's New",
                "Operational guidance",
                "Latest changes summary.",
            )
            self._write_page(
                root,
                "troubleshooting/index.md",
                "Troubleshooting",
                "Operational guidance",
                "Troubleshooting summary.",
            )

            docs_index = generate_docs_index.build_docs_index(root)
            self.assertEqual(docs_index["pages"][0]["nav_section"], "Orientation / What's New")
            self.assertEqual(docs_index["pages"][1]["nav_section"], "Orientation / Troubleshooting")

    def test_sidebar_nav_override_supports_custom_fixture_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            custom_nav_path = root / "nav" / "custom-sidebar.json"
            custom_nav_path.parent.mkdir(parents=True, exist_ok=True)
            custom_nav_path.write_text(
                json.dumps(
                    [
                        {"label": "Home", "path": "index.md"},
                        {
                            "label": "Orientation",
                            "items": [
                                {
                                    "label": "Troubleshooting",
                                    "items": [
                                        {
                                            "label": "Troubleshooting",
                                            "path": "troubleshooting/index.md",
                                        }
                                    ],
                                }
                            ],
                        },
                    ],
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            self._write_page(root, "index.md", "Docs Home", "Operational guidance", "Home summary.")
            self._write_page(
                root,
                "troubleshooting/index.md",
                "Troubleshooting",
                "Operational guidance",
                "Troubleshooting summary.",
            )

            docs_index = generate_docs_index.build_docs_index(
                root, nav_source="nav/custom-sidebar.json"
            )
            self.assertEqual(
                [page["path"] for page in docs_index["pages"]],
                ["index.md", "troubleshooting/index.md"],
            )
            self.assertEqual(docs_index["pages"][1]["nav_section"], "Orientation / Troubleshooting")

    def test_frontmatter_title_is_preferred_without_leading_h1(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._write_sidebar_data(root, [{"label": "Home", "path": "index.md"}])
            page_path = root / "src" / "content" / "docs" / "index.md"
            page_path.parent.mkdir(parents=True, exist_ok=True)
            page_path.write_text(
                "\n".join(
                    [
                        "---",
                        'title: "Frontmatter Home"',
                        "---",
                        "",
                        "**Evidence:** Operational guidance",
                        "",
                        "## Scope",
                        "",
                        "Frontmatter summary.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            docs_index = generate_docs_index.build_docs_index(root)
            self.assertEqual(docs_index["pages"][0]["title"], "Frontmatter Home")

    def test_script_writes_expected_output_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "docs-index.json"

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--output", str(output_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(output_path.exists())
            data = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(data["artifact"], "docs-index.json")
            self.assertEqual(
                data["scope"]["surface"],
                "hand-authored published docs pages included in the checked-in docs navigation",
            )
            self.assertIn("pages", data)
            self.assertGreater(len(data["pages"]), 0)


if __name__ == "__main__":
    unittest.main()
