"""Tests for scripts/generate/generate_tooling_index.py."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "generate" / "generate_tooling_index.py"

spec = importlib.util.spec_from_file_location("generate_tooling_index", SCRIPT)
generate_tooling_index = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_tooling_index)


class GenerateToolingIndexTests(unittest.TestCase):
    def _with_temp_repo_paths(self, root: Path):
        old_docs_root = generate_tooling_index.DOCS_ROOT
        old_default_nav_source = generate_tooling_index.DEFAULT_NAV_SOURCE
        old_metadata_path = generate_tooling_index.METADATA_PATH
        generate_tooling_index.DOCS_ROOT = root / "src" / "content" / "docs"
        generate_tooling_index.DEFAULT_NAV_SOURCE = root / "src" / "site" / "sidebar-data.json"
        generate_tooling_index.METADATA_PATH = root / "references" / "tooling-index-metadata.json"
        self.addCleanup(setattr, generate_tooling_index, "DOCS_ROOT", old_docs_root)
        self.addCleanup(
            setattr, generate_tooling_index, "DEFAULT_NAV_SOURCE", old_default_nav_source
        )
        self.addCleanup(setattr, generate_tooling_index, "METADATA_PATH", old_metadata_path)

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
                    "",
                    "## Scope",
                    "",
                    scope,
                    "",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def _write_metadata(self, root: Path, payload: dict[str, object]) -> Path:
        metadata_path = root / "references" / "tooling-index-metadata.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return metadata_path

    def _make_fixture_repo(self, root: Path) -> None:
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
                    "label": "API",
                    "items": [
                        {"label": "Prompt Submission", "path": "api/prompt-submission.md"},
                        {"label": "WebSocket", "path": "api/websocket.md"},
                    ],
                },
                {
                    "label": "Reference",
                    "items": [
                        {"label": "Object Info", "path": "reference/object-info.md"},
                        {"label": "Server Py Summary", "path": "reference/server-py-summary.md"},
                    ],
                },
            ],
        )
        self._write_page(root, "index.md", "Docs Home", "Operational guidance", "Home summary.")
        self._write_page(
            root,
            "start-here/tooling-builder.md",
            "Start Here: Tooling Builder",
            "Operational guidance",
            "Tooling summary.",
        )
        self._write_page(
            root,
            "api/prompt-submission.md",
            "Prompt Submission",
            "Source-backed from pinned snapshots",
            "Prompt summary.",
        )
        self._write_page(
            root,
            "api/websocket.md",
            "WebSocket",
            "Source-backed from pinned snapshots",
            "WebSocket summary.",
        )
        self._write_page(
            root,
            "reference/object-info.md",
            "Object Info",
            "Source-backed from pinned snapshots",
            "Object info summary.",
        )
        self._write_page(
            root,
            "reference/server-py-summary.md",
            "Server Py Summary",
            "Operational guidance",
            "Generated summary placeholder.",
        )

    def test_generation_is_deterministic_and_covers_all_eligible_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._make_fixture_repo(root)
            self._write_metadata(
                root,
                {
                    "start-here/tooling-builder.md": {
                        "task_intents": ["route-docs-task"],
                        "related_artifacts": ["tooling-index.json", "docs-index.json"],
                        "related_routes": [],
                        "related_events": [],
                        "runtime_required": False,
                        "stability_tier": "support-routing",
                        "recommended_next_reads": ["api/prompt-submission.md"],
                    }
                },
            )

            first = generate_tooling_index.build_tooling_index(root)
            second = generate_tooling_index.build_tooling_index(root)

            self.assertEqual(first, second)
            self.assertEqual(
                [page["path"] for page in first["pages"]],
                [
                    "api/prompt-submission.md",
                    "api/websocket.md",
                    "index.md",
                    "reference/object-info.md",
                    "start-here/tooling-builder.md",
                ],
            )

    def test_metadata_merge_and_default_value_emission(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._make_fixture_repo(root)
            self._write_metadata(
                root,
                {
                    "api/websocket.md": {
                        "task_intents": ["monitor-execution"],
                        "related_artifacts": ["tooling-index.json", "server_endpoints.json"],
                        "related_routes": ["GET /ws"],
                        "related_events": ["status", "executing"],
                        "runtime_required": True,
                        "stability_tier": "pinned-baseline",
                        "recommended_next_reads": [
                            "api/prompt-submission.md",
                            "reference/object-info.md",
                        ],
                    }
                },
            )

            tooling_index = generate_tooling_index.build_tooling_index(root)
            websocket_entry = next(
                page for page in tooling_index["pages"] if page["path"] == "api/websocket.md"
            )
            home_entry = next(page for page in tooling_index["pages"] if page["path"] == "index.md")

            self.assertEqual(websocket_entry["task_intents"], ["monitor-execution"])
            self.assertEqual(
                websocket_entry["related_artifacts"],
                ["server_endpoints.json", "tooling-index.json"],
            )
            self.assertEqual(websocket_entry["related_events"], ["executing", "status"])
            self.assertTrue(websocket_entry["runtime_required"])
            self.assertEqual(home_entry["task_intents"], [])
            self.assertEqual(home_entry["related_routes"], [])
            self.assertIsNone(home_entry["runtime_required"])
            self.assertIsNone(home_entry["stability_tier"])

    def test_missing_metadata_target_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._make_fixture_repo(root)
            self._write_metadata(
                root,
                {
                    "missing/page.md": {
                        "task_intents": [],
                        "related_artifacts": [],
                        "related_routes": [],
                        "related_events": [],
                        "runtime_required": False,
                        "stability_tier": "support-routing",
                        "recommended_next_reads": [],
                    }
                },
            )
            with self.assertRaisesRegex(
                ValueError, "does not exist in checked-in published docs navigation"
            ):
                generate_tooling_index.build_tooling_index(root)

    def test_generated_pages_stay_excluded_even_if_metadata_is_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._make_fixture_repo(root)
            self._write_metadata(
                root,
                {
                    "reference/server-py-summary.md": {
                        "task_intents": ["route-docs-task"],
                        "related_artifacts": ["tooling-index.json"],
                        "related_routes": [],
                        "related_events": [],
                        "runtime_required": False,
                        "stability_tier": "support-routing",
                        "recommended_next_reads": [],
                    }
                },
            )
            tooling_index = generate_tooling_index.build_tooling_index(root)
            self.assertNotIn(
                "reference/server-py-summary.md", {page["path"] for page in tooling_index["pages"]}
            )

    def test_collect_excluded_metadata_paths_reports_excluded_nav_targets(self):
        metadata = {
            "reference/server-py-summary.md": {},
            "api/websocket.md": {},
        }
        eligible_paths = {"api/websocket.md", "index.md"}
        nav_paths = {"reference/server-py-summary.md", "api/websocket.md", "index.md"}

        excluded = generate_tooling_index.collect_excluded_metadata_paths(
            metadata, eligible_paths, nav_paths
        )

        self.assertEqual(excluded, ["reference/server-py-summary.md"])

    def test_invalid_stability_tier_rejected(self):
        self._assert_invalid_metadata(
            {
                "api/websocket.md": {
                    "task_intents": [],
                    "related_artifacts": [],
                    "related_routes": [],
                    "related_events": [],
                    "runtime_required": False,
                    "stability_tier": "stable-forever",
                    "recommended_next_reads": [],
                }
            },
            "invalid stability_tier",
        )

    def test_unknown_metadata_key_rejected(self):
        self._assert_invalid_metadata(
            {
                "api/websocket.md": {
                    "task_intents": [],
                    "related_artifacts": [],
                    "related_routes": [],
                    "related_events": [],
                    "runtime_required": False,
                    "stability_tier": "pinned-baseline",
                    "recommended_next_reads": [],
                    "unknown_field": True,
                }
            },
            "unknown metadata keys",
        )

    def test_wrong_field_type_rejected(self):
        self._assert_invalid_metadata(
            {
                "api/websocket.md": {
                    "task_intents": "monitor-execution",
                    "related_artifacts": [],
                    "related_routes": [],
                    "related_events": [],
                    "runtime_required": False,
                    "stability_tier": "pinned-baseline",
                    "recommended_next_reads": [],
                }
            },
            "task_intents must be an array of strings",
        )

    def test_broken_recommended_next_reads_rejected(self):
        self._assert_invalid_metadata(
            {
                "api/websocket.md": {
                    "task_intents": [],
                    "related_artifacts": [],
                    "related_routes": [],
                    "related_events": [],
                    "runtime_required": False,
                    "stability_tier": "pinned-baseline",
                    "recommended_next_reads": ["missing/page.md"],
                }
            },
            "recommended_next_reads targets are not eligible",
        )

    def test_invalid_related_routes_rejected(self):
        self._assert_invalid_metadata(
            {
                "api/websocket.md": {
                    "task_intents": [],
                    "related_artifacts": [],
                    "related_routes": ["get /ws"],
                    "related_events": [],
                    "runtime_required": False,
                    "stability_tier": "pinned-baseline",
                    "recommended_next_reads": [],
                }
            },
            "invalid related_routes",
        )

    def test_invalid_related_artifacts_rejected(self):
        self._assert_invalid_metadata(
            {
                "api/websocket.md": {
                    "task_intents": [],
                    "related_artifacts": ["made-up.json"],
                    "related_routes": [],
                    "related_events": [],
                    "runtime_required": False,
                    "stability_tier": "pinned-baseline",
                    "recommended_next_reads": [],
                }
            },
            "invalid related_artifacts",
        )

    def test_related_events_wrong_type_rejected_and_sorted_when_valid(self):
        self._assert_invalid_metadata(
            {
                "api/websocket.md": {
                    "task_intents": [],
                    "related_artifacts": [],
                    "related_routes": [],
                    "related_events": "status",
                    "runtime_required": False,
                    "stability_tier": "pinned-baseline",
                    "recommended_next_reads": [],
                }
            },
            "related_events must be an array of strings",
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._make_fixture_repo(root)
            self._write_metadata(
                root,
                {
                    "api/websocket.md": {
                        "task_intents": [],
                        "related_artifacts": [],
                        "related_routes": [],
                        "related_events": ["status", "executing", "execution_start"],
                        "runtime_required": False,
                        "stability_tier": "pinned-baseline",
                        "recommended_next_reads": [],
                    }
                },
            )
            tooling_index = generate_tooling_index.build_tooling_index(root)
            entry = next(
                page for page in tooling_index["pages"] if page["path"] == "api/websocket.md"
            )
            self.assertEqual(entry["related_events"], ["executing", "execution_start", "status"])

    def test_script_writes_output_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "tooling-index.json"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--output", str(output_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(output_path.exists())
            data = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(data["artifact"], "tooling-index.json")
            self.assertEqual(data["artifact_schema_version"], "0.1.0")
            self.assertGreater(len(data["pages"]), 0)

    def test_script_warns_for_excluded_metadata_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._make_fixture_repo(root)
            self._write_metadata(
                root,
                {
                    "reference/server-py-summary.md": {
                        "task_intents": ["route-docs-task"],
                        "related_artifacts": ["tooling-index.json"],
                        "related_routes": [],
                        "related_events": [],
                        "runtime_required": False,
                        "stability_tier": "support-routing",
                        "recommended_next_reads": [],
                    }
                },
            )
            output_path = root / "tooling-index.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--nav-source",
                    str(root / "src" / "site" / "sidebar-data.json"),
                    "--metadata",
                    str(root / "references" / "tooling-index-metadata.json"),
                    "--output",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("WARNING: metadata entry reference/server-py-summary.md", result.stdout)

    def _assert_invalid_metadata(self, payload: dict[str, object], expected_message: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._with_temp_repo_paths(root)
            self._make_fixture_repo(root)
            self._write_metadata(root, payload)
            with self.assertRaisesRegex(ValueError, expected_message):
                generate_tooling_index.build_tooling_index(root)


if __name__ == "__main__":
    unittest.main()
