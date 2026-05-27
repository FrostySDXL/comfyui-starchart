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
        old_metadata_path = generate_docs_index.METADATA_PATH
        generate_docs_index.DOCS_ROOT = root / "src" / "content" / "docs"
        generate_docs_index.DEFAULT_NAV_SOURCE = root / "src" / "site" / "sidebar-data.json"
        generate_docs_index.METADATA_PATH = root / "references" / "docs-index-metadata.json"
        self.addCleanup(setattr, generate_docs_index, "DOCS_ROOT", old_docs_root)
        self.addCleanup(setattr, generate_docs_index, "DEFAULT_NAV_SOURCE", old_default_nav_source)
        self.addCleanup(setattr, generate_docs_index, "METADATA_PATH", old_metadata_path)

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

    def _write_metadata(self, root: Path, payload: dict[str, object]) -> Path:
        metadata_path = root / "references" / "docs-index-metadata.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return metadata_path

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
            self._write_metadata(root, {})

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
            self._write_metadata(root, {})
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
            self._write_metadata(root, {})
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

    def test_non_generated_reference_page_is_no_longer_excluded_by_deleted_page_list(self):
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
            self._write_metadata(root, {})
            self._write_page(
                root,
                "reference/server-py-summary.md",
                "Server.py Summary",
                "Operational guidance",
                "Generated reference summary.",
            )

            docs_index = generate_docs_index.build_docs_index(root)
            self.assertEqual(
                [page["path"] for page in docs_index["pages"]],
                ["index.md", "reference/server-py-summary.md"],
            )

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

            self._write_metadata(root, {})
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
            self._write_metadata(root, {})
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
            self._write_metadata(root, {})
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
                "hand-authored published docs pages included in the checked-in docs navigation with optional tooling-oriented enrichment",
            )
            self.assertIn("pages", data)
            self.assertGreater(len(data["pages"]), 0)

    def test_merges_tooling_metadata_under_nested_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._write_sidebar_data(
                root,
                [
                    {"label": "Home", "path": "index.md"},
                    {
                        "label": "API",
                        "items": [
                            {"label": "Prompt Submission", "path": "api/prompt-submission.md"}
                        ],
                    },
                ],
            )
            self._write_page(root, "index.md", "Docs Home", "Operational guidance", "Home summary.")
            self._write_page(
                root,
                "api/prompt-submission.md",
                "Prompt Submission",
                "Source-backed from pinned snapshots",
                "Prompt summary.",
            )
            self._write_metadata(
                root,
                {
                    "api/prompt-submission.md": {
                        "task_intents": ["submit-prompt"],
                        "related_artifacts": ["server_endpoints.json", "docs-index.json"],
                        "related_routes": ["POST /prompt"],
                        "related_events": ["execution_success", "executing"],
                        "runtime_required": True,
                        "stability_tier": "pinned-baseline",
                        "recommended_next_reads": ["index.md"],
                    }
                },
            )

            docs_index = generate_docs_index.build_docs_index(root)
            prompt_entry = next(
                page for page in docs_index["pages"] if page["path"] == "api/prompt-submission.md"
            )
            home_entry = next(page for page in docs_index["pages"] if page["path"] == "index.md")

            self.assertNotIn("task_intents", prompt_entry)
            self.assertEqual(
                prompt_entry["tooling_metadata"],
                {
                    "task_intents": ["submit-prompt"],
                    "related_artifacts": ["docs-index.json", "server_endpoints.json"],
                    "related_routes": ["POST /prompt"],
                    "related_events": ["executing", "execution_success"],
                    "runtime_required": True,
                    "stability_tier": "pinned-baseline",
                    "recommended_next_reads": ["index.md"],
                },
            )
            self.assertNotIn("tooling_metadata", home_entry)

    def test_build_docs_index_accepts_discover_hooks_task_intent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._write_sidebar_data(
                root,
                [
                    {"label": "Home", "path": "index.md"},
                    {
                        "label": "Hooks",
                        "items": [
                            {"label": "JavaScript Hooks", "path": "hooks/javascript-hooks.md"}
                        ],
                    },
                ],
            )
            self._write_page(root, "index.md", "Docs Home", "Operational guidance", "Home summary.")
            self._write_page(
                root,
                "hooks/javascript-hooks.md",
                "JavaScript Hooks",
                "Source-backed from pinned snapshots",
                "Hook summary.",
            )
            self._write_metadata(
                root,
                {
                    "hooks/javascript-hooks.md": {
                        "task_intents": ["discover-hooks"],
                        "related_artifacts": ["docs-index.json", "js_hooks.json"],
                        "related_routes": [],
                        "related_events": [],
                        "runtime_required": False,
                        "stability_tier": "pinned-baseline",
                        "recommended_next_reads": ["index.md"],
                    }
                },
            )

            docs_index = generate_docs_index.build_docs_index(root)
            hook_entry = next(
                page for page in docs_index["pages"] if page["path"] == "hooks/javascript-hooks.md"
            )

            self.assertEqual(
                hook_entry["tooling_metadata"]["task_intents"],
                ["discover-hooks"],
            )

    def test_build_docs_index_accepts_custom_node_and_architecture_task_intents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._write_sidebar_data(
                root,
                [
                    {"label": "Home", "path": "index.md"},
                    {
                        "label": "Architecture",
                        "items": [{"label": "Overview", "path": "architecture/overview.md"}],
                    },
                    {
                        "label": "Custom Nodes",
                        "items": [
                            {
                                "label": "Development Guide",
                                "path": "custom-nodes/development-guide.md",
                            }
                        ],
                    },
                ],
            )
            self._write_page(root, "index.md", "Docs Home", "Operational guidance", "Home summary.")
            self._write_page(
                root,
                "architecture/overview.md",
                "Architecture Overview",
                "Operational guidance",
                "Architecture summary.",
            )
            self._write_page(
                root,
                "custom-nodes/development-guide.md",
                "Custom Node Development Guide",
                "Operational guidance",
                "Custom node summary.",
            )
            self._write_metadata(
                root,
                {
                    "architecture/overview.md": {
                        "task_intents": ["understand-architecture"],
                        "related_artifacts": ["docs-index.json"],
                        "related_routes": [],
                        "related_events": [],
                        "runtime_required": False,
                        "stability_tier": "support-routing",
                        "recommended_next_reads": ["index.md"],
                    },
                    "custom-nodes/development-guide.md": {
                        "task_intents": ["build-custom-node"],
                        "related_artifacts": ["docs-index.json", "node_api_schema.json"],
                        "related_routes": [],
                        "related_events": [],
                        "runtime_required": False,
                        "stability_tier": "support-routing",
                        "recommended_next_reads": ["index.md"],
                    },
                },
            )

            docs_index = generate_docs_index.build_docs_index(root)
            architecture_entry = next(
                page for page in docs_index["pages"] if page["path"] == "architecture/overview.md"
            )
            custom_node_entry = next(
                page
                for page in docs_index["pages"]
                if page["path"] == "custom-nodes/development-guide.md"
            )

            self.assertEqual(
                architecture_entry["tooling_metadata"]["task_intents"],
                ["understand-architecture"],
            )
            self.assertEqual(
                custom_node_entry["tooling_metadata"]["task_intents"],
                ["build-custom-node"],
            )

    def test_invalid_new_task_intent_is_still_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._write_sidebar_data(root, [{"label": "Home", "path": "index.md"}])
            self._write_page(root, "index.md", "Docs Home", "Operational guidance", "Home summary.")
            self._write_metadata(
                root,
                {
                    "index.md": {
                        "task_intents": ["invent-unsupported-intent"],
                        "related_artifacts": ["docs-index.json"],
                        "related_routes": [],
                        "related_events": [],
                        "runtime_required": False,
                        "stability_tier": "support-routing",
                        "recommended_next_reads": [],
                    }
                },
            )

            with self.assertRaisesRegex(ValueError, "invalid task_intents values"):
                generate_docs_index.build_docs_index(root)

    def test_metadata_target_missing_from_generated_output_fails(self):
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
                                "label": "Generated Summary",
                                "path": "reference/generated-summary.md",
                            }
                        ],
                    },
                ],
            )
            self._write_page(root, "index.md", "Docs Home", "Operational guidance", "Home summary.")
            generated_path = (
                root / "src" / "content" / "docs" / "reference" / "generated-summary.md"
            )
            generated_path.parent.mkdir(parents=True, exist_ok=True)
            generated_path.write_text(
                "\n".join(
                    [
                        "<!-- GENERATED FILE: do not edit directly -->",
                        "",
                        "---",
                        'title: "Generated Summary"',
                        "---",
                        "",
                        "**Evidence:** Operational guidance",
                        "",
                        "## Scope",
                        "",
                        "Generated summary.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            self._write_metadata(
                root,
                {
                    "reference/generated-summary.md": {
                        "task_intents": ["route-docs-task"],
                        "related_artifacts": ["docs-index.json"],
                        "related_routes": [],
                        "related_events": [],
                        "runtime_required": False,
                        "stability_tier": "support-routing",
                        "recommended_next_reads": ["index.md"],
                    }
                },
            )

            with self.assertRaisesRegex(
                ValueError, "does not target a retained published docs page"
            ):
                generate_docs_index.build_docs_index(root)


if __name__ == "__main__":
    unittest.main()
