"""Tests for scripts/common/refresh_support.py."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "common" / "refresh_support.py"


def _load_module():
    """Load the refresh_support module from file."""
    spec = importlib.util.spec_from_file_location("refresh_support", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RefreshSupportImportTests(unittest.TestCase):
    """Test that the support module imports correctly."""

    def test_module_imports(self):
        """The refresh_support module should be importable."""
        module = _load_module()
        self.assertTrue(hasattr(module, "recommended_python_command"))
        self.assertTrue(hasattr(module, "repo_relative_path"))
        self.assertTrue(hasattr(module, "create_pre_refresh_backup"))
        self.assertTrue(hasattr(module, "build_refresh_provenance"))
        self.assertTrue(hasattr(module, "compute_diff_summary"))


class RefreshSupportCommandTests(unittest.TestCase):
    """Test repo-preferred maintainer command rendering."""

    def test_recommended_python_command_uses_portable_python(self):
        module = _load_module()
        for platform in ["win32", "linux"]:
            with self.subTest(platform=platform):
                self.assertEqual(module.recommended_python_command(platform), "python")


class RefreshSupportPathTests(unittest.TestCase):
    """Test repo-relative path handling."""

    def test_repo_relative_path_normalization_cases(self):
        module = _load_module()
        repo_root = Path("D:/repo")
        cases = [
            (
                repo_root / "references" / "raw" / "server_endpoints.json",
                "references/raw/server_endpoints.json",
            ),
            (Path("D:/other/file.txt"), "D:/other/file.txt"),
        ]

        for path, expected in cases:
            with self.subTest(path=path):
                self.assertEqual(module.repo_relative_path(path, repo_root), expected)


class RefreshSupportBackupTests(unittest.TestCase):
    """Test refresh backup safety helpers."""

    def test_canonical_raw_artifacts_exist_when_populated(self):
        """A populated raw directory should count as an existing baseline."""
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_dir = Path(tmpdir) / "references" / "raw"
            raw_dir.mkdir(parents=True)
            (raw_dir / "server_endpoints.json").write_text('{"ok": true}\n', encoding="utf-8")
            self.assertTrue(module.canonical_raw_artifacts_exist(raw_dir))

    def test_create_pre_refresh_backup_when_raw_exists(self):
        """A repo-local backup should be created when canonical raw artifacts exist."""
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            references_dir = tmp_path / "references"
            raw_dir = references_dir / "raw"
            raw_dir.mkdir(parents=True)
            sample_file = raw_dir / "server_endpoints.json"
            sample_file.write_text('{"ok": true}\n', encoding="utf-8")

            backup_dir = module.create_pre_refresh_backup(references_dir, raw_dir, tmp_path)

            self.assertIsNotNone(backup_dir)
            self.assertEqual(backup_dir.parent.name, "_refresh_backups")
            self.assertEqual(backup_dir.parent.parent.name, "references")
            self.assertTrue(backup_dir.name.startswith("raw_"))
            copied = backup_dir / "server_endpoints.json"
            self.assertTrue(copied.exists())
            self.assertEqual(copied.read_text(encoding="utf-8"), '{"ok": true}\n')

    def test_create_pre_refresh_backup_creates_parent_directory(self):
        """Backup creation should create the dedicated backup parent directory when missing."""
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            references_dir = tmp_path / "references"
            raw_dir = references_dir / "raw"
            raw_dir.mkdir(parents=True)
            (raw_dir / "server_endpoints.json").write_text('{"ok": true}\n', encoding="utf-8")

            backup_root = references_dir / "_refresh_backups"
            self.assertFalse(backup_root.exists())

            backup_dir = module.create_pre_refresh_backup(references_dir, raw_dir, tmp_path)

            self.assertIsNotNone(backup_dir)
            self.assertTrue(backup_root.exists())
            self.assertEqual(backup_dir.parent, backup_root)

    def test_create_pre_refresh_backup_skips_when_no_prior_baseline(self):
        """No backup should be created when canonical raw artifacts do not yet exist."""
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            references_dir = tmp_path / "references"
            raw_dir = references_dir / "raw"
            raw_dir.mkdir(parents=True)

            backup_dir = module.create_pre_refresh_backup(references_dir, raw_dir, tmp_path)

        self.assertIsNone(backup_dir)

    def test_create_pre_refresh_backup_raises_on_copy_failure(self):
        """Backup creation failures should raise a clear runtime error."""
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            references_dir = tmp_path / "references"
            raw_dir = references_dir / "raw"
            raw_dir.mkdir(parents=True)
            (raw_dir / "server_endpoints.json").write_text('{"ok": true}\n', encoding="utf-8")

            with mock.patch.object(module.shutil, "copytree", side_effect=OSError("copy failed")):
                with self.assertRaises(RuntimeError) as exc:
                    module.create_pre_refresh_backup(references_dir, raw_dir, tmp_path)

        self.assertIn("Failed to create pre-refresh backup", str(exc.exception))


class RefreshSupportProvenanceTests(unittest.TestCase):
    """Test refresh provenance helpers."""

    def test_build_delta_summary_command_returns_none_without_backup(self):
        """No delta command should be suggested when no backup exists."""
        module = _load_module()
        command = module.build_delta_summary_command(None, Path("D:/repo"), "py -3.11")
        self.assertIsNone(command)

    def test_build_delta_summary_command_uses_repo_relative_backup_path(self):
        """Delta summary command should reference the backup relative to the repo root."""
        module = _load_module()
        repo_root = Path("D:/repo")
        backup_dir = repo_root / "references" / "_refresh_backups" / "raw_20260503T010203Z"
        command = module.build_delta_summary_command(backup_dir, repo_root, "py -3.11")
        self.assertIn("py -3.11 scripts/generate/generate_snapshot_delta_summary.py", command)
        self.assertIn('--old "references/_refresh_backups/raw_20260503T010203Z"', command)

    def test_build_delta_summary_command_targets_canonical_new_output_locations(self):
        """Delta summary command should keep the canonical new/output paths stable."""
        module = _load_module()
        command = module.build_delta_summary_command(
            Path("D:/repo/references/_refresh_backups/raw_20260503T010203Z"),
            Path("D:/repo"),
            "py -3.11",
        )

        self.assertIn('--new "references/raw"', command)
        self.assertIn('--output "public/artifacts/delta-summary.json"', command)

    def test_write_refresh_provenance_persists_required_fields(self):
        """Refresh provenance output should persist the documented minimum fields."""
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            backup_dir = tmp_path / "references" / "_refresh_backups" / "raw_20260503T010203Z"
            backup_dir.mkdir(parents=True)
            provenance_path = tmp_path / "public" / "artifacts" / "refresh-provenance.json"

            payload = module.build_refresh_provenance(
                refresh_date="2026-05-03",
                requested_core_version="v0.20.1",
                requested_frontend_version="v1.44.13",
                resolved_core_commit="abc123",
                resolved_frontend_commit="def456",
                backup_dir=backup_dir,
                runtime_object_info_requested=True,
                runtime_object_info_merged=False,
                repo_root=tmp_path,
                provenance_output_path=provenance_path,
                python_executable="py -3.11",
            )
            written_path = module.write_refresh_provenance(payload, provenance_path, tmp_path)

            self.assertEqual(written_path, provenance_path)
            persisted = json.loads(provenance_path.read_text(encoding="utf-8"))

        self.assertEqual(persisted["refresh_date"], "2026-05-03")
        self.assertEqual(persisted["requested_versions"]["core"], "v0.20.1")
        self.assertEqual(persisted["requested_versions"]["frontend"], "v1.44.13")
        self.assertEqual(persisted["resolved_commits"]["core"], "abc123")
        self.assertEqual(persisted["resolved_commits"]["frontend"], "def456")
        self.assertEqual(
            persisted["backup_location"],
            "references/_refresh_backups/raw_20260503T010203Z",
        )
        self.assertTrue(persisted["runtime_object_info"]["requested"])
        self.assertFalse(persisted["runtime_object_info"]["merged_into_node_api_schema"])
        self.assertEqual(
            persisted["published"]["provenance_path"],
            "public/artifacts/refresh-provenance.json",
        )
        self.assertFalse(persisted["published"]["manifest_included"])
        self.assertFalse(persisted["published"]["canonical_artifacts_updated_by_refresh"])
        self.assertFalse(persisted["published"]["delta_summary_updated_by_refresh"])
        self.assertEqual(
            persisted["next_steps"]["publish_reference_artifacts_command"],
            "py -3.11 scripts/generate/publish_reference_artifacts.py",
        )
        self.assertEqual(
            persisted["next_steps"]["verify_artifact_integrity_command"],
            "py -3.11 scripts/verify/verify_artifact_integrity.py",
        )
        self.assertIn(
            "generate_snapshot_delta_summary.py",
            persisted["next_steps"]["delta_summary_command"],
        )
        self.assertEqual(
            persisted["next_steps"]["run_all_command"],
            "py -3.11 scripts/verify/run_all.py",
        )

    def test_build_refresh_provenance_preserves_partial_refresh_state(self):
        """Partial refresh runs should keep nulls while preserving operator follow-up commands."""
        module = _load_module()
        payload = module.build_refresh_provenance(
            refresh_date="2026-05-18",
            requested_core_version=None,
            requested_frontend_version="v1.44.13",
            resolved_core_commit=None,
            resolved_frontend_commit="def456",
            backup_dir=None,
            runtime_object_info_requested=False,
            runtime_object_info_merged=False,
            repo_root=Path("D:/repo"),
            provenance_output_path=Path("D:/repo/public/artifacts/refresh-provenance.json"),
            python_executable="py -3.11",
        )

        self.assertIsNone(payload["requested_versions"]["core"])
        self.assertEqual(payload["requested_versions"]["frontend"], "v1.44.13")
        self.assertIsNone(payload["resolved_commits"]["core"])
        self.assertEqual(payload["resolved_commits"]["frontend"], "def456")
        self.assertIsNone(payload["backup_location"])
        self.assertIsNone(payload["next_steps"]["delta_summary_command"])
        self.assertEqual(
            payload["next_steps"]["publish_reference_artifacts_command"],
            "py -3.11 scripts/generate/publish_reference_artifacts.py",
        )
        self.assertEqual(
            payload["next_steps"]["verify_artifact_integrity_command"],
            "py -3.11 scripts/verify/verify_artifact_integrity.py",
        )
        self.assertEqual(
            payload["next_steps"]["run_all_command"],
            "py -3.11 scripts/verify/run_all.py",
        )

    def test_build_refresh_provenance_keeps_follow_up_truth_values_false_until_post_refresh_steps_run(
        self,
    ):
        """Refresh provenance should truthfully report that publish/delta steps still remain."""
        module = _load_module()
        payload = module.build_refresh_provenance(
            refresh_date="2026-05-18",
            requested_core_version="v0.20.1",
            requested_frontend_version=None,
            resolved_core_commit="abc123",
            resolved_frontend_commit=None,
            backup_dir=Path("D:/repo/references/_refresh_backups/raw_20260518T010203Z"),
            runtime_object_info_requested=False,
            runtime_object_info_merged=False,
            repo_root=Path("D:/repo"),
            provenance_output_path=Path("D:/repo/public/artifacts/refresh-provenance.json"),
            python_executable="py -3.11",
        )

        self.assertFalse(payload["published"]["canonical_artifacts_updated_by_refresh"])
        self.assertFalse(payload["published"]["delta_summary_updated_by_refresh"])
        self.assertFalse(payload["published"]["manifest_included"])

    def test_write_refresh_provenance_raises_clear_runtime_error_on_write_failure(self):
        """Write failures should be wrapped in a clear runtime error."""
        module = _load_module()
        repo_root = Path("D:/repo")
        provenance_path = repo_root / "public" / "artifacts" / "refresh-provenance.json"
        payload = {"refresh_date": "2026-05-14"}

        with mock.patch.object(Path, "write_text", side_effect=OSError("disk full")):
            with self.assertRaises(RuntimeError) as exc:
                module.write_refresh_provenance(payload, provenance_path, repo_root)

        self.assertIn("Failed to write refresh provenance", str(exc.exception))
        self.assertIn("public/artifacts/refresh-provenance.json", str(exc.exception))


class RefreshSupportDiffSummaryTests(unittest.TestCase):
    """Test the diff summary computation."""

    def test_compute_diff_summary_cases(self):
        module = _load_module()
        cases = [
            (
                "endpoint additions",
                {"endpoints": [{"route": "/ws", "method": "GET"}]},
                {
                    "endpoints": [
                        {"route": "/ws", "method": "GET"},
                        {"route": "/new", "method": "POST"},
                    ]
                },
                "server_endpoints.json",
                "New endpoints",
            ),
            (
                "endpoint removals",
                {
                    "endpoints": [
                        {"route": "/ws", "method": "GET"},
                        {"route": "/old", "method": "POST"},
                    ]
                },
                {"endpoints": [{"route": "/ws", "method": "GET"}]},
                "server_endpoints.json",
                "Removed endpoints",
            ),
            (
                "hook additions",
                {"hooks": [{"name": "init"}]},
                {"hooks": [{"name": "init"}, {"name": "newHook"}]},
                "js_hooks.json",
                "New hooks",
            ),
            (
                "hook removals",
                {"hooks": [{"name": "init"}, {"name": "oldHook"}]},
                {"hooks": [{"name": "init"}]},
                "js_hooks.json",
                "Removed hooks",
            ),
            (
                "no endpoint changes",
                {"endpoints": [{"route": "/ws", "method": "GET"}]},
                {"endpoints": [{"route": "/ws", "method": "GET"}]},
                "server_endpoints.json",
                "No endpoint changes",
            ),
            (
                "provenance mode change",
                {
                    "metadata": {"provenance": {"mode": "source-only"}},
                    "object_info_fields": [],
                    "io_types": [],
                },
                {
                    "metadata": {"provenance": {"mode": "hybrid"}},
                    "object_info_fields": [],
                    "io_types": [],
                },
                "node_api_schema.json",
                "Provenance mode changed",
            ),
            (
                "runtime node count change",
                {
                    "metadata": {},
                    "object_info_fields": [],
                    "io_types": [],
                    "runtime_object_info": {"A": {}},
                },
                {
                    "metadata": {},
                    "object_info_fields": [],
                    "io_types": [],
                    "runtime_object_info": {"A": {}, "B": {}},
                },
                "node_api_schema.json",
                "Runtime object_info node count",
            ),
            (
                "no schema changes with runtime",
                {
                    "metadata": {"provenance": {"mode": "hybrid"}},
                    "object_info_fields": ["input"],
                    "io_types": [],
                    "runtime_object_info": {"A": {}},
                },
                {
                    "metadata": {"provenance": {"mode": "hybrid"}},
                    "object_info_fields": ["input"],
                    "io_types": [],
                    "runtime_object_info": {"A": {}},
                },
                "node_api_schema.json",
                "No schema changes",
            ),
        ]

        for name, old, new, filename, expected_change in cases:
            with self.subTest(name=name):
                changes = module.compute_diff_summary(old, new, filename)
                self.assertTrue(any(expected_change in change for change in changes))


if __name__ == "__main__":
    unittest.main()
