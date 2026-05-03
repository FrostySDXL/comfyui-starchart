"""Tests for scripts/refresh_snapshots.py."""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "refresh_snapshots.py"


def _load_module():
    """Load the refresh_snapshots module from file."""
    spec = importlib.util.spec_from_file_location("refresh_snapshots", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RefreshSnapshotsImportTests(unittest.TestCase):
    """Test that the refresh_snapshots module imports correctly."""

    def test_module_imports(self):
        """The refresh_snapshots module should be importable."""
        module = _load_module()
        self.assertTrue(hasattr(module, "main"))
        self.assertTrue(hasattr(module, "refresh_core"))
        self.assertTrue(hasattr(module, "refresh_frontend"))
        self.assertTrue(hasattr(module, "run_extractors"))
        self.assertTrue(hasattr(module, "run_markdown_generation"))

    def test_key_functions_are_callable(self):
        """Key functions should be callable."""
        module = _load_module()
        self.assertTrue(callable(module.main))
        self.assertTrue(callable(module.refresh_core))
        self.assertTrue(callable(module.refresh_frontend))
        self.assertTrue(callable(module.run_extractors))
        self.assertTrue(callable(module.run_markdown_generation))


class RefreshSnapshotsArgumentTests(unittest.TestCase):
    """Test that argument validation works correctly."""

    def test_missing_version_args_exits_nonzero(self):
        """Running without any version args should exit with code 1."""
        import subprocess

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=10,
        )
        self.assertNotEqual(result.returncode, 0, "Should exit non-zero when no version args provided")
        self.assertIn("at least one", result.stderr.lower() + result.stdout.lower())

    def test_help_flag_works(self):
        """The --help flag should work and display usage info."""
        import subprocess

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--core-version", result.stdout)
        self.assertIn("--frontend-version", result.stdout)
        self.assertIn("--runtime-object-info-url", result.stdout)
        self.assertIn("--skip-runtime-merge", result.stdout)
        self.assertIn("automatic repo-local backup", result.stdout.lower())

    def test_runtime_url_only_works(self):
        """Running with only --runtime-object-info-url should not fail argument validation."""
        module = _load_module()
        with mock.patch.object(
            sys,
            "argv",
            [
                str(SCRIPT_PATH),
                "--runtime-object-info-url",
                "http://127.0.0.1:8188",
            ],
        ), mock.patch.object(
            module.subprocess,
            "run",
            return_value=mock.Mock(returncode=0, stdout="git version 2.0.0\n", stderr=""),
        ), mock.patch.object(
            module,
            "create_pre_refresh_backup",
            return_value=None,
        ), mock.patch.object(
            module,
            "run_runtime_extraction",
            return_value=False,
        ) as runtime_mock:
            result = module.main()

        self.assertEqual(result, 1)
        runtime_mock.assert_called_once()


class RefreshSnapshotsConstantsTests(unittest.TestCase):
    """Test that file list constants are correct."""

    def test_module_repo_root_matches_repo(self):
        """Module REPO_ROOT should resolve to this repository root."""
        module = _load_module()
        self.assertEqual(module.REPO_ROOT, REPO_ROOT)

    def test_derived_paths_exist(self):
        """Derived script and references paths should exist in-repo."""
        module = _load_module()
        self.assertTrue(module.REFERENCES_RAW_DIR.exists())
        self.assertTrue(module.SNAPSHOTS_DIR.exists())
        self.assertTrue(module.SCRIPTS_EXTRACT_DIR.exists())
        self.assertTrue(module.SCRIPTS_GENERATE_DIR.exists())

    def test_core_files_list(self):
        """CORE_FILES should contain the expected source files."""
        module = _load_module()
        expected_core_files = [
            "server.py",
            "execution.py",
            "pyproject.toml",
            "requirements.txt",
            "app/frontend_management.py",
            "comfy_api/latest/_io.py",
            "comfy_api/latest/_input/basic_types.py",
        ]
        self.assertEqual(module.CORE_FILES, expected_core_files)

    def test_frontend_files_list(self):
        """FRONTEND_FILES should contain the expected source files."""
        module = _load_module()
        expected_frontend_files = [
            "package.json",
            "src/scripts/app.ts",
            "src/types/comfy.ts",
            "src/services/litegraphService.ts",
        ]
        self.assertEqual(module.FRONTEND_FILES, expected_frontend_files)

    def test_repo_urls_are_set(self):
        """CORE_REPO_URL and FRONTEND_REPO_URL should be set."""
        module = _load_module()
        self.assertIn("github.com", module.CORE_REPO_URL)
        self.assertIn("github.com", module.FRONTEND_REPO_URL)
        self.assertIn("ComfyUI", module.CORE_REPO_URL)
        self.assertIn("ComfyUI_Frontend", module.FRONTEND_REPO_URL)

    def test_paths_are_within_repo(self):
        """Key paths should resolve within the repo root."""
        module = _load_module()
        self.assertTrue(str(module.REFERENCES_RAW_DIR).startswith(str(module.REPO_ROOT)))
        self.assertTrue(str(module.SNAPSHOTS_DIR).startswith(str(module.REPO_ROOT)))
        self.assertTrue(str(module.SCRIPTS_EXTRACT_DIR).startswith(str(module.REPO_ROOT)))
        self.assertTrue(str(module.SCRIPTS_GENERATE_DIR).startswith(str(module.REPO_ROOT)))


class RefreshSnapshotsDiffSummaryTests(unittest.TestCase):
    """Test the diff summary computation."""

    def test_endpoint_diff_detects_additions(self):
        """compute_diff_summary should detect new endpoints."""
        module = _load_module()
        old = {"endpoints": [{"route": "/ws", "method": "GET"}]}
        new = {"endpoints": [{"route": "/ws", "method": "GET"}, {"route": "/new", "method": "POST"}]}
        changes = module.compute_diff_summary(old, new, "server_endpoints.json")
        self.assertTrue(any("New endpoints" in c for c in changes))

    def test_endpoint_diff_detects_removals(self):
        """compute_diff_summary should detect removed endpoints."""
        module = _load_module()
        old = {"endpoints": [{"route": "/ws", "method": "GET"}, {"route": "/old", "method": "POST"}]}
        new = {"endpoints": [{"route": "/ws", "method": "GET"}]}
        changes = module.compute_diff_summary(old, new, "server_endpoints.json")
        self.assertTrue(any("Removed endpoints" in c for c in changes))

    def test_hook_diff_detects_changes(self):
        """compute_diff_summary should detect hook changes."""
        module = _load_module()
        old = {"hooks": [{"name": "init"}]}
        new = {"hooks": [{"name": "init"}, {"name": "newHook"}]}
        changes = module.compute_diff_summary(old, new, "js_hooks.json")
        self.assertTrue(any("New hooks" in c for c in changes))

    def test_no_changes_detected(self):
        """compute_diff_summary should report no changes when content is identical."""
        module = _load_module()
        old = {"endpoints": [{"route": "/ws", "method": "GET"}]}
        new = {"endpoints": [{"route": "/ws", "method": "GET"}]}
        changes = module.compute_diff_summary(old, new, "server_endpoints.json")
        self.assertTrue(any("No endpoint changes" in c for c in changes))

    def test_schema_diff_detects_provenance_mode_change(self):
        """compute_diff_summary should detect provenance mode changes."""
        module = _load_module()
        old = {"metadata": {"provenance": {"mode": "source-only"}}, "object_info_fields": [], "io_types": []}
        new = {"metadata": {"provenance": {"mode": "hybrid"}}, "object_info_fields": [], "io_types": []}
        changes = module.compute_diff_summary(old, new, "node_api_schema.json")
        self.assertTrue(any("Provenance mode changed" in c for c in changes))

    def test_schema_diff_detects_runtime_node_count_change(self):
        """compute_diff_summary should detect runtime_object_info size changes."""
        module = _load_module()
        old = {"metadata": {}, "object_info_fields": [], "io_types": [], "runtime_object_info": {"A": {}}}
        new = {"metadata": {}, "object_info_fields": [], "io_types": [], "runtime_object_info": {"A": {}, "B": {}}}
        changes = module.compute_diff_summary(old, new, "node_api_schema.json")
        self.assertTrue(any("Runtime object_info node count" in c for c in changes))

    def test_schema_diff_no_changes_with_runtime(self):
        """compute_diff_summary should report no changes when runtime and schema are stable."""
        module = _load_module()
        old = {"metadata": {"provenance": {"mode": "hybrid"}}, "object_info_fields": ["input"], "io_types": [], "runtime_object_info": {"A": {}}}
        new = {"metadata": {"provenance": {"mode": "hybrid"}}, "object_info_fields": ["input"], "io_types": [], "runtime_object_info": {"A": {}}}
        changes = module.compute_diff_summary(old, new, "node_api_schema.json")
        self.assertTrue(any("No schema changes" in c for c in changes))


class RefreshSnapshotsRuntimeTests(unittest.TestCase):
    """Test runtime extraction support."""

    def test_run_runtime_extraction_exists(self):
        """run_runtime_extraction should be defined and callable."""
        module = _load_module()
        self.assertTrue(hasattr(module, "run_runtime_extraction"))
        self.assertTrue(callable(module.run_runtime_extraction))


class RefreshSnapshotsSafetyAndProvenanceTests(unittest.TestCase):
    """Test refresh backup safety and provenance helpers."""

    def test_create_pre_refresh_backup_when_raw_exists(self):
        """A repo-local backup should be created when canonical raw artifacts exist."""
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            raw_dir = tmp_path / "references" / "raw"
            raw_dir.mkdir(parents=True)
            sample_file = raw_dir / "server_endpoints.json"
            sample_file.write_text('{"ok": true}\n', encoding="utf-8")

            with mock.patch.object(module, "REFERENCES_DIR", tmp_path / "references"), \
                 mock.patch.object(module, "REFERENCES_RAW_DIR", raw_dir):
                backup_dir = module.create_pre_refresh_backup()
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
            raw_dir = tmp_path / "references" / "raw"
            raw_dir.mkdir(parents=True)

            with mock.patch.object(module, "REFERENCES_DIR", tmp_path / "references"), \
                 mock.patch.object(module, "REFERENCES_RAW_DIR", raw_dir):
                backup_dir = module.create_pre_refresh_backup()

        self.assertIsNone(backup_dir)

    def test_create_pre_refresh_backup_raises_on_copy_failure(self):
        """Backup creation failures should raise a clear runtime error."""
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            raw_dir = tmp_path / "references" / "raw"
            raw_dir.mkdir(parents=True)
            (raw_dir / "server_endpoints.json").write_text('{"ok": true}\n', encoding="utf-8")

            with mock.patch.object(module, "REFERENCES_DIR", tmp_path / "references"), \
                 mock.patch.object(module, "REFERENCES_RAW_DIR", raw_dir), \
                 mock.patch.object(module.shutil, "copytree", side_effect=OSError("copy failed")):
                with self.assertRaises(RuntimeError) as exc:
                    module.create_pre_refresh_backup()

        self.assertIn("Failed to create pre-refresh backup", str(exc.exception))

    def test_write_refresh_provenance_persists_required_fields(self):
        """Refresh provenance output should persist the documented minimum fields."""
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            backup_dir = tmp_path / "references" / "raw_backup_20260503T010203Z"
            backup_dir.mkdir(parents=True)
            provenance_path = tmp_path / "docs" / "artifacts" / "refresh-provenance.json"

            with mock.patch.object(module, "REPO_ROOT", tmp_path), \
                 mock.patch.object(module, "PROVENANCE_OUTPUT_PATH", provenance_path):
                payload = module.build_refresh_provenance(
                    refresh_date="2026-05-03",
                    requested_core_version="v0.20.1",
                    requested_frontend_version="v1.44.13",
                    resolved_core_commit="abc123",
                    resolved_frontend_commit="def456",
                    backup_dir=backup_dir,
                    runtime_object_info_requested=True,
                    runtime_object_info_merged=False,
                )
                written_path = module.write_refresh_provenance(payload)

            self.assertEqual(written_path, provenance_path)
            persisted = json.loads(provenance_path.read_text(encoding="utf-8"))

        self.assertEqual(persisted["refresh_date"], "2026-05-03")
        self.assertEqual(persisted["requested_versions"]["core"], "v0.20.1")
        self.assertEqual(persisted["requested_versions"]["frontend"], "v1.44.13")
        self.assertEqual(persisted["resolved_commits"]["core"], "abc123")
        self.assertEqual(persisted["resolved_commits"]["frontend"], "def456")
        self.assertEqual(
            persisted["backup_location"],
            "references/raw_backup_20260503T010203Z",
        )
        self.assertTrue(persisted["runtime_object_info"]["requested"])
        self.assertFalse(persisted["runtime_object_info"]["merged_into_node_api_schema"])
        self.assertEqual(
            persisted["published"]["provenance_path"],
            "docs/artifacts/refresh-provenance.json",
        )
        self.assertFalse(persisted["published"]["manifest_included"])
        self.assertIn("generate_snapshot_delta_summary.py", persisted["next_steps"]["delta_summary_command"])


if __name__ == "__main__":
    unittest.main()
