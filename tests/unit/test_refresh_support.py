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

    def test_recommended_python_command_uses_windows_launcher(self):
        """Windows follow-up commands should use the repo's Python launcher rule."""
        module = _load_module()
        self.assertEqual(module.recommended_python_command("win32"), "py -3.11")

    def test_recommended_python_command_uses_python_on_non_windows(self):
        """Non-Windows follow-up commands should stay portable."""
        module = _load_module()
        self.assertEqual(module.recommended_python_command("linux"), "python")


class RefreshSupportPathTests(unittest.TestCase):
    """Test repo-relative path handling."""

    def test_repo_relative_path_returns_relative_path(self):
        """Paths inside the repo should be normalized to forward-slash-relative form."""
        module = _load_module()
        repo_root = Path("D:/repo")
        path = repo_root / "references" / "raw" / "server_endpoints.json"
        self.assertEqual(
            module.repo_relative_path(path, repo_root),
            "references/raw/server_endpoints.json",
        )

    def test_repo_relative_path_leaves_external_path_posix(self):
        """Paths outside the repo should still be returned in POSIX form."""
        module = _load_module()
        repo_root = Path("D:/repo")
        external = Path("D:/other/file.txt")
        self.assertEqual(module.repo_relative_path(external, repo_root), "D:/other/file.txt")


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
            self.assertEqual(backup_dir.parent.name, "references")
            self.assertTrue(backup_dir.name.startswith("raw_backup_"))
            copied = backup_dir / "server_endpoints.json"
            self.assertTrue(copied.exists())
            self.assertEqual(copied.read_text(encoding="utf-8"), '{"ok": true}\n')

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
        backup_dir = repo_root / "references" / "raw_backup_20260503T010203Z"
        command = module.build_delta_summary_command(backup_dir, repo_root, "py -3.11")
        self.assertIn("py -3.11 scripts/generate/generate_snapshot_delta_summary.py", command)
        self.assertIn('--old "references/raw_backup_20260503T010203Z"', command)

    def test_write_refresh_provenance_persists_required_fields(self):
        """Refresh provenance output should persist the documented minimum fields."""
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            backup_dir = tmp_path / "references" / "raw_backup_20260503T010203Z"
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
        self.assertEqual(persisted["backup_location"], "references/raw_backup_20260503T010203Z")
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

    def test_endpoint_diff_detects_additions(self):
        """compute_diff_summary should detect new endpoints."""
        module = _load_module()
        old = {"endpoints": [{"route": "/ws", "method": "GET"}]}
        new = {
            "endpoints": [{"route": "/ws", "method": "GET"}, {"route": "/new", "method": "POST"}]
        }
        changes = module.compute_diff_summary(old, new, "server_endpoints.json")
        self.assertTrue(any("New endpoints" in change for change in changes))

    def test_endpoint_diff_detects_removals(self):
        """compute_diff_summary should detect removed endpoints."""
        module = _load_module()
        old = {
            "endpoints": [{"route": "/ws", "method": "GET"}, {"route": "/old", "method": "POST"}]
        }
        new = {"endpoints": [{"route": "/ws", "method": "GET"}]}
        changes = module.compute_diff_summary(old, new, "server_endpoints.json")
        self.assertTrue(any("Removed endpoints" in change for change in changes))

    def test_hook_diff_detects_changes(self):
        """compute_diff_summary should detect hook changes."""
        module = _load_module()
        old = {"hooks": [{"name": "init"}]}
        new = {"hooks": [{"name": "init"}, {"name": "newHook"}]}
        changes = module.compute_diff_summary(old, new, "js_hooks.json")
        self.assertTrue(any("New hooks" in change for change in changes))

    def test_hook_diff_detects_removals(self):
        """compute_diff_summary should detect removed hooks."""
        module = _load_module()
        old = {"hooks": [{"name": "init"}, {"name": "oldHook"}]}
        new = {"hooks": [{"name": "init"}]}
        changes = module.compute_diff_summary(old, new, "js_hooks.json")
        self.assertTrue(any("Removed hooks" in change for change in changes))

    def test_no_changes_detected(self):
        """compute_diff_summary should report no changes when content is identical."""
        module = _load_module()
        old = {"endpoints": [{"route": "/ws", "method": "GET"}]}
        new = {"endpoints": [{"route": "/ws", "method": "GET"}]}
        changes = module.compute_diff_summary(old, new, "server_endpoints.json")
        self.assertTrue(any("No endpoint changes" in change for change in changes))

    def test_schema_diff_detects_provenance_mode_change(self):
        """compute_diff_summary should detect provenance mode changes."""
        module = _load_module()
        old = {
            "metadata": {"provenance": {"mode": "source-only"}},
            "object_info_fields": [],
            "io_types": [],
        }
        new = {
            "metadata": {"provenance": {"mode": "hybrid"}},
            "object_info_fields": [],
            "io_types": [],
        }
        changes = module.compute_diff_summary(old, new, "node_api_schema.json")
        self.assertTrue(any("Provenance mode changed" in change for change in changes))

    def test_schema_diff_detects_runtime_node_count_change(self):
        """compute_diff_summary should detect runtime_object_info size changes."""
        module = _load_module()
        old = {
            "metadata": {},
            "object_info_fields": [],
            "io_types": [],
            "runtime_object_info": {"A": {}},
        }
        new = {
            "metadata": {},
            "object_info_fields": [],
            "io_types": [],
            "runtime_object_info": {"A": {}, "B": {}},
        }
        changes = module.compute_diff_summary(old, new, "node_api_schema.json")
        self.assertTrue(any("Runtime object_info node count" in change for change in changes))

    def test_schema_diff_no_changes_with_runtime(self):
        """compute_diff_summary should report no changes when runtime and schema are stable."""
        module = _load_module()
        old = {
            "metadata": {"provenance": {"mode": "hybrid"}},
            "object_info_fields": ["input"],
            "io_types": [],
            "runtime_object_info": {"A": {}},
        }
        new = {
            "metadata": {"provenance": {"mode": "hybrid"}},
            "object_info_fields": ["input"],
            "io_types": [],
            "runtime_object_info": {"A": {}},
        }
        changes = module.compute_diff_summary(old, new, "node_api_schema.json")
        self.assertTrue(any("No schema changes" in change for change in changes))


if __name__ == "__main__":
    unittest.main()
