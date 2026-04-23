"""Tests for scripts/refresh_snapshots.py."""

import importlib.util
import sys
import unittest
from pathlib import Path

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

    def test_runtime_url_only_works(self):
        """Running with only --runtime-object-info-url should not fail argument validation."""
        import subprocess

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--runtime-object-info-url", "http://127.0.0.1:8188"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=10,
        )
        # It will fail at git check or runtime extraction, but not at argument parsing
        self.assertNotIn("at least one", result.stderr.lower() + result.stdout.lower())


class RefreshSnapshotsConstantsTests(unittest.TestCase):
    """Test that file list constants are correct."""

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


if __name__ == "__main__":
    unittest.main()