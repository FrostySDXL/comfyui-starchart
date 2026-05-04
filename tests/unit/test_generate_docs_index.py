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
    def _write_page(self, root: Path, relative_path: str, title: str, evidence: str, scope: str) -> None:
        page_path = root / "docs" / Path(relative_path)
        page_path.parent.mkdir(parents=True, exist_ok=True)
        page_path.write_text(
            "\n".join(
                [
                    f"# {title}",
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
            (root / "mkdocs.yml").write_text(
                "\n".join(
                    [
                        "nav:",
                        "  - Home: index.md",
                        "  - Start Here:",
                        "      - start-here/tooling-builder.md",
                        "  - Orientation:",
                        "      - Troubleshooting:",
                        "          - troubleshooting/index.md",
                        "          - troubleshooting/api-integration.md",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self._write_page(root, "index.md", "Docs Home", "Source-backed from pinned snapshots", "Home summary.")
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
            (root / "mkdocs.yml").write_text("nav:\n  - Home: index.md\n", encoding="utf-8")
            page_path = root / "docs" / "index.md"
            page_path.parent.mkdir(parents=True, exist_ok=True)
            page_path.write_text(
                "\n".join(
                    [
                        "# Docs Home",
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
            (root / "mkdocs.yml").write_text(
                "\n".join(
                    [
                        "nav:",
                        "  - Home: index.md",
                        "  - Ecosystem:",
                        "      - ecosystem/map.md",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self._write_page(root, "index.md", "Docs Home", "Operational guidance", "Home summary.")
            generated_path = root / "docs" / "ecosystem" / "map.md"
            generated_path.parent.mkdir(parents=True, exist_ok=True)
            generated_path.write_text(
                "\n".join(
                    [
                        "<!-- GENERATED FILE: do not edit directly -->",
                        "",
                        "# Ecosystem Map",
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
            self.assertIn("pages", data)
            self.assertGreater(len(data["pages"]), 0)


if __name__ == "__main__":
    unittest.main()
