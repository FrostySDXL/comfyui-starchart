"""Tests for scripts/generate/generate_docs_index.py."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.verify.published_schema_validation import validate_against_published_artifact_schema

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "generate" / "generate_docs_index.py"

spec = importlib.util.spec_from_file_location("generate_docs_index", SCRIPT)
generate_docs_index = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_docs_index)


class GenerateDocsIndexTests(unittest.TestCase):
    def _metadata_entry(
        self,
        *,
        task_intents: list[str] | None = None,
        related_artifacts: list[str] | None = None,
        related_routes: list[str] | None = None,
        related_route_entries: list[dict[str, str]] | None = None,
        related_events: list[str] | None = None,
        runtime_required: bool = False,
        stability_tier: str = "support-routing",
        recommended_next_reads: list[str] | None = None,
        primary_task_intents: list[str] | None = None,
        excluded_task_intents: list[str] | None = None,
        metadata_reviewed_at: str | None = None,
        metadata_baseline: str | None = None,
        bare_next_read_reason: str | None = None,
    ) -> dict[str, object]:
        entry: dict[str, object] = {
            "task_intents": task_intents or ["route-docs-task"],
            "related_artifacts": related_artifacts or ["docs-index.json"],
            "related_routes": related_routes or [],
            "related_events": related_events or [],
            "runtime_required": runtime_required,
            "stability_tier": stability_tier,
            "recommended_next_reads": recommended_next_reads or [],
        }
        if related_route_entries is not None:
            entry["related_route_entries"] = related_route_entries
        if primary_task_intents is not None:
            entry["primary_task_intents"] = primary_task_intents
        if excluded_task_intents is not None:
            entry["excluded_task_intents"] = excluded_task_intents
        if metadata_reviewed_at is not None:
            entry["metadata_reviewed_at"] = metadata_reviewed_at
        if metadata_baseline is not None:
            entry["metadata_baseline"] = metadata_baseline
        if bare_next_read_reason is not None:
            entry["bare_next_read_reason"] = bare_next_read_reason
        return entry

    def _write_minimal_metadata(self, root: Path, paths: list[str]) -> Path:
        return self._write_metadata(
            root, {path: self._metadata_entry(recommended_next_reads=[]) for path in paths}
        )

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
            self._write_minimal_metadata(
                root,
                [
                    "index.md",
                    "start-here/tooling-builder.md",
                    "troubleshooting/index.md",
                    "troubleshooting/api-integration.md",
                ],
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
            self._write_minimal_metadata(root, ["index.md"])
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
            self._write_minimal_metadata(root, ["index.md"])
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
            self._write_minimal_metadata(root, ["index.md", "reference/server-py-summary.md"])
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

            self._write_minimal_metadata(root, ["whats-new/index.md", "troubleshooting/index.md"])
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
            self._write_minimal_metadata(root, ["index.md", "troubleshooting/index.md"])
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
            self._write_minimal_metadata(root, ["index.md"])
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
                    "index.md": self._metadata_entry(recommended_next_reads=[]),
                    "api/prompt-submission.md": {
                        "task_intents": ["submit-prompt"],
                        "related_artifacts": ["server_endpoints.json", "docs-index.json"],
                        "related_routes": ["POST /prompt"],
                        "related_events": ["execution_success", "executing"],
                        "runtime_required": True,
                        "stability_tier": "pinned-baseline",
                        "recommended_next_reads": ["index.md"],
                    },
                },
            )

            docs_index = generate_docs_index.build_docs_index(root)
            prompt_entry = next(
                page for page in docs_index["pages"] if page["path"] == "api/prompt-submission.md"
            )
            self.assertNotIn("task_intents", prompt_entry)
            self.assertEqual(
                prompt_entry["tooling_metadata"],
                {
                    "metadata_reviewed_at": None,
                    "metadata_baseline": None,
                    "task_intents": ["submit-prompt"],
                    "primary_task_intents": [],
                    "excluded_task_intents": [],
                    "related_artifacts": ["docs-index.json", "server_endpoints.json"],
                    "related_routes": ["POST /prompt"],
                    "related_route_entries": [
                        {
                            "route": "POST /prompt",
                            "route_type": "unknown",
                            "route_classification_reason": "metadata_not_provided",
                        }
                    ],
                    "related_events": ["executing", "execution_success"],
                    "runtime_required": True,
                    "stability_tier": "pinned-baseline",
                    "recommended_next_reads": ["index.md"],
                    "inbound_recommendations": [],
                },
            )

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
                    "index.md": self._metadata_entry(recommended_next_reads=[]),
                    "hooks/javascript-hooks.md": {
                        "task_intents": ["discover-hooks"],
                        "related_artifacts": ["docs-index.json", "js_hooks.json"],
                        "related_routes": [],
                        "related_events": [],
                        "runtime_required": False,
                        "stability_tier": "pinned-baseline",
                        "recommended_next_reads": ["index.md"],
                    },
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
                    "index.md": self._metadata_entry(recommended_next_reads=[]),
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
                    },
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
                    "index.md": self._metadata_entry(recommended_next_reads=[]),
                    "reference/generated-summary.md": {
                        "task_intents": ["route-docs-task"],
                        "related_artifacts": ["docs-index.json"],
                        "related_routes": [],
                        "related_events": [],
                        "runtime_required": False,
                        "stability_tier": "support-routing",
                        "recommended_next_reads": ["index.md"],
                    },
                },
            )

            with self.assertRaisesRegex(
                ValueError, "does not target a retained published docs page"
            ):
                generate_docs_index.build_docs_index(root)

    def test_allowed_bare_pages_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._write_sidebar_data(
                root,
                [
                    {
                        "label": "Reference",
                        "items": [
                            {
                                "label": "Source Evidence Policy",
                                "path": "reference/source-evidence-policy.md",
                            },
                            {
                                "label": "Writing Style Guide",
                                "path": "reference/writing-style-guide.md",
                            },
                            {
                                "label": "Version Pin Status",
                                "path": "reference/version-pin-status.md",
                            },
                            {"label": "Topic Scope", "path": "reference/topic-scope.md"},
                        ],
                    }
                ],
            )
            self._write_page(
                root,
                "reference/source-evidence-policy.md",
                "Source Evidence Policy",
                "Operational guidance",
                "Evidence policy summary.",
            )
            self._write_page(
                root,
                "reference/writing-style-guide.md",
                "Writing Style Guide",
                "Operational guidance",
                "Writing policy summary.",
            )
            self._write_page(
                root,
                "reference/version-pin-status.md",
                "Version Pin Status",
                "Operational guidance",
                "Status summary.",
            )
            self._write_page(
                root,
                "reference/topic-scope.md",
                "Topic Scope",
                "Operational guidance",
                "Scope boundary summary.",
            )
            self._write_metadata(root, {})

            docs_index = generate_docs_index.build_docs_index(root)
            for page in docs_index["pages"]:
                self.assertNotIn("tooling_metadata", page)

    def test_unexpected_bare_page_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._write_sidebar_data(
                root,
                [
                    {"label": "Home", "path": "index.md"},
                    {
                        "label": "API",
                        "items": [{"label": "Endpoints", "path": "api/endpoints.md"}],
                    },
                ],
            )
            self._write_page(root, "index.md", "Docs Home", "Operational guidance", "Home summary.")
            self._write_page(
                root,
                "api/endpoints.md",
                "API Endpoints",
                "Operational guidance",
                "Endpoint summary.",
            )
            self._write_metadata(
                root, {"index.md": self._metadata_entry(recommended_next_reads=[])}
            )

            with self.assertRaisesRegex(ValueError, "Unexpected bare pages: api/endpoints.md"):
                generate_docs_index.build_docs_index(root)

    def test_allowlisted_page_with_metadata_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._write_sidebar_data(
                root,
                [
                    {
                        "label": "Reference",
                        "items": [
                            {
                                "label": "Source Evidence Policy",
                                "path": "reference/source-evidence-policy.md",
                            },
                            {
                                "label": "Writing Style Guide",
                                "path": "reference/writing-style-guide.md",
                            },
                            {
                                "label": "Version Pin Status",
                                "path": "reference/version-pin-status.md",
                            },
                            {"label": "Topic Scope", "path": "reference/topic-scope.md"},
                        ],
                    }
                ],
            )
            self._write_page(
                root,
                "reference/source-evidence-policy.md",
                "Source Evidence Policy",
                "Operational guidance",
                "Evidence policy summary.",
            )
            self._write_page(
                root,
                "reference/writing-style-guide.md",
                "Writing Style Guide",
                "Operational guidance",
                "Writing policy summary.",
            )
            self._write_page(
                root,
                "reference/version-pin-status.md",
                "Version Pin Status",
                "Operational guidance",
                "Status summary.",
            )
            self._write_page(
                root,
                "reference/topic-scope.md",
                "Topic Scope",
                "Operational guidance",
                "Scope boundary summary.",
            )
            self._write_metadata(
                root,
                {
                    "reference/source-evidence-policy.md": {
                        "task_intents": ["route-docs-task"],
                        "related_artifacts": ["docs-index.json"],
                        "related_routes": [],
                        "related_events": [],
                        "runtime_required": False,
                        "stability_tier": "support-routing",
                        "recommended_next_reads": [],
                    },
                },
            )

            docs_index = generate_docs_index.build_docs_index(root)
            enriched = next(
                page
                for page in docs_index["pages"]
                if page["path"] == "reference/source-evidence-policy.md"
            )
            self.assertIn("tooling_metadata", enriched)
            bare = next(
                page for page in docs_index["pages"] if page["path"] == "reference/topic-scope.md"
            )
            self.assertNotIn("tooling_metadata", bare)

    def test_stale_allowlist_entry_fails(self):
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
                                "label": "Source Evidence Policy",
                                "path": "reference/source-evidence-policy.md",
                            },
                        ],
                    },
                ],
            )
            self._write_page(root, "index.md", "Docs Home", "Operational guidance", "Home summary.")
            self._write_page(
                root,
                "reference/source-evidence-policy.md",
                "Source Evidence Policy",
                "Operational guidance",
                "Evidence policy summary.",
            )
            self._write_metadata(
                root, {"index.md": self._metadata_entry(recommended_next_reads=[])}
            )
            stale_allowlist = frozenset(
                {
                    "reference/source-evidence-policy.md",
                    "reference/stale-removed-page.md",
                }
            )
            with patch.object(
                generate_docs_index, "INTENTIONALLY_BARE_PAGE_ALLOWLIST", stale_allowlist
            ):
                with self.assertRaisesRegex(ValueError, "allowlist entries are not retained"):
                    generate_docs_index.build_docs_index(root)

    def test_null_task_intents_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._write_sidebar_data(root, [{"label": "Home", "path": "index.md"}])
            self._write_page(root, "index.md", "Docs Home", "Operational guidance", "Home summary.")
            self._write_metadata(
                root,
                {
                    "index.md": {
                        "task_intents": None,
                        "related_artifacts": [],
                        "related_routes": [],
                        "related_events": [],
                        "runtime_required": False,
                        "stability_tier": "support-routing",
                        "recommended_next_reads": [],
                    },
                },
            )

            with self.assertRaisesRegex(ValueError, "task_intents must be an array of strings"):
                generate_docs_index.build_docs_index(root)

    def test_all_pages_have_metadata_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._write_sidebar_data(
                root,
                [
                    {"label": "Home", "path": "index.md"},
                    {
                        "label": "API",
                        "items": [{"label": "Endpoints", "path": "api/endpoints.md"}],
                    },
                    {
                        "label": "Architecture",
                        "items": [{"label": "Overview", "path": "architecture/overview.md"}],
                    },
                ],
            )
            self._write_page(root, "index.md", "Docs Home", "Operational guidance", "Home summary.")
            self._write_page(
                root,
                "api/endpoints.md",
                "API Endpoints",
                "Operational guidance",
                "Endpoint summary.",
            )
            self._write_page(
                root,
                "architecture/overview.md",
                "Architecture Overview",
                "Operational guidance",
                "Architecture summary.",
            )
            self._write_metadata(
                root,
                {
                    "index.md": self._metadata_entry(recommended_next_reads=[]),
                    "api/endpoints.md": {
                        "task_intents": ["discover-routes"],
                        "related_artifacts": ["server_endpoints.json"],
                        "related_routes": [],
                        "related_events": [],
                        "runtime_required": False,
                        "stability_tier": "pinned-baseline",
                        "recommended_next_reads": ["index.md"],
                    },
                    "architecture/overview.md": {
                        "task_intents": ["understand-architecture"],
                        "related_artifacts": ["docs-index.json"],
                        "related_routes": [],
                        "related_events": [],
                        "runtime_required": False,
                        "stability_tier": "support-routing",
                        "recommended_next_reads": ["index.md"],
                    },
                },
            )

            docs_index = generate_docs_index.build_docs_index(root)
            self.assertEqual(len(docs_index["pages"]), 3)
            for page in docs_index["pages"]:
                self.assertIn("tooling_metadata", page)

    def test_related_route_entries_emit_top_level_and_tooling_metadata_in_sync(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._write_sidebar_data(root, [{"label": "API", "path": "api/history-queue.md"}])
            self._write_page(
                root,
                "api/history-queue.md",
                "History and Queue",
                "Source-backed from pinned snapshots",
                "History summary.",
            )
            self._write_metadata(
                root,
                {
                    "api/history-queue.md": self._metadata_entry(
                        related_artifacts=["server_endpoints.json"],
                        related_routes=["GET /history", "GET /missing"],
                        related_route_entries=[
                            {"route": "GET /history", "route_type": "canonical"},
                        ],
                    )
                },
            )

            docs_index = generate_docs_index.build_docs_index(root)
            page = docs_index["pages"][0]

            self.assertEqual(page["route_classification_source"], "metadata")
            self.assertEqual(
                page["related_route_entries"],
                page["tooling_metadata"]["related_route_entries"],
            )
            self.assertEqual(
                page["related_route_entries"],
                [
                    {
                        "route": "GET /history",
                        "route_type": "canonical",
                        "route_classification_reason": "metadata_explicit",
                    },
                    {
                        "route": "GET /missing",
                        "route_type": "unknown",
                        "route_classification_reason": "metadata_not_provided",
                    },
                ],
            )

    def test_all_route_type_enum_values_are_accepted_and_capitalized_value_fails(self):
        entries = [
            {"route": f"GET /route-{route_type}", "route_type": route_type}
            for route_type in generate_docs_index.ROUTE_TYPE_VALUES
        ]
        metadata = {
            "index.md": self._metadata_entry(
                related_routes=[entry["route"] for entry in entries],
                related_route_entries=entries,
            )
        }
        generate_docs_index.validate_docs_index_metadata(metadata, {"index.md"}, {"index.md"})
        metadata["index.md"]["related_route_entries"] = [
            {"route": "GET /bad", "route_type": "Deprecated"}
        ]
        with self.assertRaisesRegex(ValueError, "invalid route_type"):
            generate_docs_index.validate_docs_index_metadata(metadata, {"index.md"}, {"index.md"})

    def test_task_intent_fields_are_sorted_and_excluded_intents_win(self):
        entry = self._metadata_entry(
            task_intents=["route-docs-task", "route-docs-task"],
            primary_task_intents=["route-docs-task"],
            excluded_task_intents=["onboarding", "route-docs-task", "onboarding"],
        )
        generate_docs_index.validate_docs_index_metadata(
            {"index.md": entry}, {"index.md"}, {"index.md"}
        )

        normalized = generate_docs_index.normalize_tooling_metadata(entry)

        self.assertEqual(normalized["task_intents"], ["route-docs-task"])
        self.assertEqual(normalized["primary_task_intents"], ["route-docs-task"])
        self.assertEqual(normalized["excluded_task_intents"], ["onboarding", "route-docs-task"])
        self.assertFalse(generate_docs_index.metadata_matches_intent(normalized, "route-docs-task"))
        self.assertFalse(generate_docs_index.metadata_matches_intent(normalized, "onboarding"))

    def test_primary_task_intents_must_be_subset_and_review_date_must_be_iso_date(self):
        with self.assertRaisesRegex(ValueError, "primary_task_intents values must be a subset"):
            generate_docs_index.validate_docs_index_metadata(
                {
                    "index.md": self._metadata_entry(
                        task_intents=["route-docs-task"],
                        primary_task_intents=["discover-routes"],
                    )
                },
                {"index.md"},
                {"index.md"},
            )
        with self.assertRaisesRegex(ValueError, "metadata_reviewed_at must be YYYY-MM-DD"):
            generate_docs_index.validate_docs_index_metadata(
                {"index.md": self._metadata_entry(metadata_reviewed_at="not-a-date")},
                {"index.md"},
                {"index.md"},
            )

    def test_recommended_next_read_to_bare_page_requires_reason(self):
        metadata = {
            "index.md": self._metadata_entry(
                recommended_next_reads=["reference/source-evidence-policy.md"]
            )
        }
        eligible = {"index.md", "reference/source-evidence-policy.md"}
        nav = set(eligible)
        with patch.object(
            generate_docs_index,
            "INTENTIONALLY_BARE_PAGE_ALLOWLIST",
            frozenset({"reference/source-evidence-policy.md"}),
        ):
            with self.assertRaisesRegex(ValueError, "bare_next_read_reason"):
                generate_docs_index.validate_docs_index_metadata(metadata, eligible, nav)
            metadata["index.md"]["bare_next_read_reason"] = "Policy page is intentionally bare."
            generate_docs_index.validate_docs_index_metadata(metadata, eligible, nav)

    def test_related_artifacts_are_validated_against_disk_backed_surfaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "references" / "raw").mkdir(parents=True)
            (root / "public" / "artifacts" / "current").mkdir(parents=True)
            (root / "public" / "artifacts" / "schemas").mkdir(parents=True)
            (root / "references" / "raw" / "server_endpoints.json").write_text("{}\n")
            (root / "public" / "artifacts" / "manifest.json").write_text(
                json.dumps({"artifacts": {"server_endpoints.json": {}}})
            )
            allowed = generate_docs_index.build_allowed_related_artifacts(root)
            self.assertIn("server_endpoints.json", allowed)
            self.assertIn("docs-index.json", allowed)
            self.assertNotIn("object_info_runtime.json", allowed)
            with self.assertRaisesRegex(ValueError, "invalid related_artifacts values"):
                generate_docs_index.validate_docs_index_metadata(
                    {
                        "index.md": self._metadata_entry(
                            related_artifacts=["object_info_runtime.json"]
                        )
                    },
                    {"index.md"},
                    {"index.md"},
                    allowed_artifacts=allowed,
                )

    def test_inbound_recommendations_are_generated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._write_sidebar_data(
                root,
                [
                    {"label": "Home", "path": "index.md"},
                    {"label": "API", "path": "api/endpoints.md"},
                ],
            )
            self._write_page(root, "index.md", "Docs Home", "Operational guidance", "Home.")
            self._write_page(root, "api/endpoints.md", "Endpoints", "Operational guidance", "API.")
            self._write_metadata(
                root,
                {
                    "index.md": self._metadata_entry(recommended_next_reads=["api/endpoints.md"]),
                    "api/endpoints.md": self._metadata_entry(recommended_next_reads=[]),
                },
            )

            docs_index = generate_docs_index.build_docs_index(root)
            api_page = next(
                page for page in docs_index["pages"] if page["path"] == "api/endpoints.md"
            )
            self.assertEqual(api_page["tooling_metadata"]["inbound_recommendations"], ["index.md"])

    def test_docs_index_schema_accepts_new_fields_and_rejects_drift(self):
        docs_index = generate_docs_index.build_docs_index(REPO_ROOT)
        self.assertEqual(
            validate_against_published_artifact_schema(
                docs_index, "docs-index.json", REPO_ROOT / "public" / "artifacts" / "schemas"
            ),
            [],
        )
        page = next(page for page in docs_index["pages"] if "related_route_entries" in page)
        broken = json.loads(json.dumps(docs_index))
        broken_page = next(p for p in broken["pages"] if p["path"] == page["path"])
        broken_page["tooling_metadata"].pop("related_route_entries")
        self.assertNotEqual(
            validate_against_published_artifact_schema(
                broken, "docs-index.json", REPO_ROOT / "public" / "artifacts" / "schemas"
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
