"""Tests for scripts/refresh_snapshots.py."""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.common import refresh_git_ops

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
        self.assertNotEqual(
            result.returncode, 0, "Should exit non-zero when no version args provided"
        )
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
        self.assertIn("references/_refresh_backups/raw_<timestamp>/", result.stdout)

    def test_runtime_url_only_works(self):
        """Running with only --runtime-object-info-url should not fail argument validation."""
        module = _load_module()
        with (
            mock.patch.object(
                sys,
                "argv",
                [
                    str(SCRIPT_PATH),
                    "--runtime-object-info-url",
                    "http://127.0.0.1:8188",
                ],
            ),
            mock.patch.object(
                module,
                "verify_git_available",
                return_value=True,
            ),
            mock.patch.object(
                module,
                "create_pre_refresh_backup",
                return_value=None,
            ),
            mock.patch.object(
                module,
                "run_runtime_extraction",
                return_value=False,
            ) as runtime_mock,
        ):
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


class RefreshSnapshotsRuntimeTests(unittest.TestCase):
    """Test runtime extraction support."""

    def test_run_runtime_extraction_exists(self):
        """run_runtime_extraction should be defined and callable."""
        module = _load_module()
        self.assertTrue(hasattr(module, "run_runtime_extraction"))
        self.assertTrue(callable(module.run_runtime_extraction))


class RefreshSnapshotsSafetyAndProvenanceTests(unittest.TestCase):
    """Test refresh backup safety and provenance helpers."""

    def test_script_exposes_helper_wrappers(self):
        """The main script should keep the helper entrypoints available."""
        module = _load_module()
        self.assertTrue(callable(module.create_pre_refresh_backup))
        self.assertTrue(callable(module.build_refresh_provenance))
        self.assertTrue(callable(module.write_refresh_provenance))
        self.assertTrue(callable(module.compute_diff_summary))
        self.assertTrue(callable(module.build_follow_up_commands_from_provenance))

    def test_build_delta_summary_command_uses_repo_preferred_python_command(self):
        """Follow-up commands should use the repo's maintainer-friendly Python invocation."""
        module = _load_module()
        backup_dir = module.REPO_ROOT / "references" / "_refresh_backups" / "raw_20260518T010203Z"
        with mock.patch.object(
            module.refresh_support, "recommended_python_command", return_value="py -3.11"
        ) as command_mock:
            command = module.build_delta_summary_command(backup_dir)

        command_mock.assert_called_once_with(module.sys.platform)
        self.assertIn("py -3.11 scripts/generate/generate_snapshot_delta_summary.py", command)
        self.assertIn('--old "references/_refresh_backups/raw_20260518T010203Z"', command)

    def test_persist_refresh_provenance_passes_partial_refresh_state(self):
        """persist_refresh_provenance should preserve null backup/version state and write the built payload."""
        module = _load_module()
        args = mock.Mock(
            core_version=None,
            frontend_version="v1.44.13",
            runtime_object_info_url=None,
            skip_runtime_merge=False,
        )
        payload = {"refresh_date": "2026-05-18"}
        with (
            mock.patch.object(
                module, "build_refresh_provenance", return_value=payload
            ) as build_mock,
            mock.patch.object(
                module, "write_refresh_provenance", return_value=module.PROVENANCE_OUTPUT_PATH
            ) as write_mock,
        ):
            written = module.persist_refresh_provenance(
                args,
                "2026-05-18",
                None,
                "frontend-sha",
                None,
            )

        build_mock.assert_called_once_with(
            refresh_date="2026-05-18",
            requested_core_version=None,
            requested_frontend_version="v1.44.13",
            resolved_core_commit=None,
            resolved_frontend_commit="frontend-sha",
            backup_dir=None,
            runtime_object_info_requested=False,
            runtime_object_info_merged=False,
        )
        write_mock.assert_called_once_with(payload)
        self.assertEqual(written, module.PROVENANCE_OUTPUT_PATH)


class RefreshSnapshotsOrchestrationTests(unittest.TestCase):
    """Test the thinner orchestration helpers used by main()."""

    def test_verify_git_available_returns_false_on_missing_git(self):
        """Git preflight should fail cleanly when git is unavailable."""
        module = _load_module()
        with mock.patch.object(
            module.refresh_git_ops,
            "verify_git_available",
            side_effect=RuntimeError("FAILED: checking git availability"),
        ):
            self.assertFalse(module.verify_git_available())

    def test_refresh_requested_snapshots_calls_requested_refreshes(self):
        """Requested core and frontend refreshes should map to their helpers."""
        module = _load_module()
        with (
            mock.patch.object(
                module, "refresh_core", return_value=("core-sha", "core-dir")
            ) as core_mock,
            mock.patch.object(
                module,
                "refresh_frontend",
                return_value=("frontend-sha", "frontend-dir"),
            ) as frontend_mock,
        ):
            core_commit, frontend_commit = module.refresh_requested_snapshots(
                "v0.20.1",
                "v1.44.13",
                "2026-05-14",
            )

        core_mock.assert_called_once_with("v0.20.1", "2026-05-14")
        frontend_mock.assert_called_once_with("v1.44.13", "2026-05-14")
        self.assertEqual(core_commit, "core-sha")
        self.assertEqual(frontend_commit, "frontend-sha")

    def test_capture_runtime_object_info_uses_runtime_specific_fallbacks(self):
        """Runtime capture should derive version and commit from the current execution context."""
        module = _load_module()
        args = mock.Mock(
            runtime_object_info_url="http://127.0.0.1:8188",
            runtime_object_info_version=None,
            core_version="v0.20.1",
            runtime_object_info_commit=None,
        )
        with mock.patch.object(module, "run_runtime_extraction", return_value=True) as runtime_mock:
            path = module.capture_runtime_object_info(args, "core-sha")

        runtime_mock.assert_called_once_with(
            "http://127.0.0.1:8188",
            "v0.20.1",
            "core-sha",
        )
        self.assertEqual(path, str(module.REFERENCES_RAW_DIR / "object_info_runtime.json"))

    def test_main_success_path_uses_orchestration_helpers(self):
        """main() should delegate to the orchestration helpers and still return 0 on success."""
        module = _load_module()
        provenance_payload = {
            "next_steps": {
                "recommended_follow_up_commands": [
                    "py -3.11 scripts/generate/publish_reference_artifacts.py",
                    "py -3.11 scripts/verify/verify_artifact_integrity.py",
                    "py -3.11 scripts/verify/run_all.py",
                ]
            }
        }
        with (
            mock.patch.object(sys, "argv", [str(SCRIPT_PATH), "--core-version", "v0.20.1"]),
            mock.patch.object(module, "verify_git_available", return_value=True),
            mock.patch.object(module, "create_pre_refresh_backup", return_value=None),
            mock.patch.object(module, "load_existing_raw_jsons", return_value={}) as load_mock,
            mock.patch.object(
                module,
                "refresh_requested_snapshots",
                return_value=("core-sha", None),
            ) as refresh_mock,
            mock.patch.object(
                module, "capture_runtime_object_info", return_value=None
            ) as runtime_mock,
            mock.patch.object(module, "run_extractors") as extractors_mock,
            mock.patch.object(module, "run_markdown_generation", return_value=True),
            mock.patch.object(module, "print_change_summary") as change_mock,
            mock.patch.object(
                module,
                "persist_refresh_provenance",
                return_value=module.PROVENANCE_OUTPUT_PATH,
            ) as provenance_mock,
            mock.patch.object(
                module.Path,
                "read_text",
                return_value=json.dumps(provenance_payload),
            ),
        ):
            result = module.main()

        self.assertEqual(result, 0)
        load_mock.assert_called_once_with()
        refresh_mock.assert_called_once_with("v0.20.1", None, mock.ANY)
        runtime_mock.assert_called_once()
        extractors_mock.assert_called_once()
        change_mock.assert_called_once_with({})
        provenance_mock.assert_called_once()

    def test_main_returns_one_when_refresh_requested_snapshots_raises(self):
        """main() should fail cleanly when the refresh step raises a runtime error."""
        module = _load_module()
        with (
            mock.patch.object(sys, "argv", [str(SCRIPT_PATH), "--core-version", "v0.20.1"]),
            mock.patch.object(module, "verify_git_available", return_value=True),
            mock.patch.object(module, "create_pre_refresh_backup", return_value=None),
            mock.patch.object(module, "load_existing_raw_jsons", return_value={}),
            mock.patch.object(
                module,
                "refresh_requested_snapshots",
                side_effect=RuntimeError("FAILED: cloning ComfyUI core at v0.20.1"),
            ),
        ):
            result = module.main()

        self.assertEqual(result, 1)


class RefreshSnapshotsBoundaryTests(unittest.TestCase):
    """Test clarified clone/copy and extractor helper boundaries."""

    def test_refresh_git_ops_copy_source_files_copies_only_existing(self):
        """_copy_source_files should copy only files that exist, skip missing files."""
        with tempfile.TemporaryDirectory() as tmp:
            src_dir = Path(tmp) / "src"
            src_dir.mkdir()
            (src_dir / "keep.py").write_text("x = 1", encoding="utf-8")
            (src_dir / "skip.txt").write_text("y", encoding="utf-8")

            dest_dir = Path(tmp) / "dest"

            copied = refresh_git_ops._copy_source_files(
                str(src_dir),
                dest_dir,
                ["keep.py", "missing.py", "skip.txt"],
                "test-repo",
            )

            self.assertEqual(copied, ["keep.py", "skip.txt"])
            self.assertTrue((dest_dir / "keep.py").exists())
            self.assertTrue((dest_dir / "skip.txt").exists())
            self.assertFalse((dest_dir / "missing.py").exists())

    def test_refresh_git_ops_run_cmd_raises_on_failure(self):
        """Shared git helper should raise instead of silently returning failures."""
        with mock.patch.object(
            refresh_git_ops.subprocess,
            "run",
            return_value=mock.Mock(returncode=1, stdout="bad", stderr="worse"),
        ):
            with self.assertRaises(RuntimeError) as exc:
                refresh_git_ops._run_cmd(["git", "status"], "git status")

        self.assertIn("FAILED: git status", str(exc.exception))

    def test_refresh_git_ops_verify_git_available_returns_version_string(self):
        """Shared git availability helper should return the resolved version string."""
        with mock.patch.object(
            refresh_git_ops,
            "_run_cmd",
            return_value=mock.Mock(stdout="git version 2.50.0\n"),
        ):
            version = refresh_git_ops.verify_git_available()

        self.assertEqual(version, "git version 2.50.0")

    def test_refresh_core_delegates_to_generic_snapshot_helper(self):
        """refresh_core should bind the core constants to the shared snapshot helper."""
        module = _load_module()
        with mock.patch.object(
            module,
            "_refresh_repo_snapshot",
            return_value=("core-sha", "comfyui-core-v0.20.1"),
        ) as helper_mock:
            result = module.refresh_core("v0.20.1", "2026-05-14")

        helper_mock.assert_called_once_with(
            version="v0.20.1",
            snapshot_date="2026-05-14",
            repo_url=module.CORE_REPO_URL,
            dest_prefix="comfyui-core",
            heading_label="ComfyUI Core",
            clone_label="ComfyUI core",
            copy_label="core",
            temp_prefix="comfyui-core-",
            files=module.CORE_FILES,
        )
        self.assertEqual(result, ("core-sha", "comfyui-core-v0.20.1"))

    def test_refresh_frontend_delegates_to_generic_snapshot_helper(self):
        """refresh_frontend should bind the frontend constants to the shared snapshot helper."""
        module = _load_module()
        with mock.patch.object(
            module,
            "_refresh_repo_snapshot",
            return_value=("frontend-sha", "comfyui-frontend-v1.44.13"),
        ) as helper_mock:
            result = module.refresh_frontend("v1.44.13", "2026-05-14")

        helper_mock.assert_called_once_with(
            version="v1.44.13",
            snapshot_date="2026-05-14",
            repo_url=module.FRONTEND_REPO_URL,
            dest_prefix="comfyui-frontend",
            heading_label="ComfyUI Frontend",
            clone_label="ComfyUI Frontend",
            copy_label="frontend",
            temp_prefix="comfyui-frontend-",
            files=module.FRONTEND_FILES,
        )
        self.assertEqual(result, ("frontend-sha", "comfyui-frontend-v1.44.13"))

    def test_run_extractors_preserves_server_hooks_schema_sequence(self):
        """refresh_pipeline.run_extractors should keep the server, hooks, then schema extractor order."""
        module = _load_module()
        events = []

        def _record(name, value):
            def inner(*args, **kwargs):
                events.append(name)
                return value

            return inner

        with (
            mock.patch.object(
                module.refresh_pipeline,
                "_run_server_extractor",
                side_effect=_record("server", "server summary"),
            ),
            mock.patch.object(
                module.refresh_pipeline,
                "_run_hooks_extractor",
                side_effect=_record("hooks", "hooks summary"),
            ),
            mock.patch.object(
                module.refresh_pipeline,
                "_run_node_api_schema_extractor",
                side_effect=_record("schema", "schema summary"),
            ),
        ):
            results = module.refresh_pipeline.run_extractors(
                core_version="v0.20.1",
                core_commit="core-sha",
                frontend_version="v1.44.13",
                frontend_commit="frontend-sha",
                snapshot_date="2026-05-14",
                runtime_object_info_path="references/raw/object_info_runtime.json",
                snapshots_dir=module.SNAPSHOTS_DIR,
                python_executable=module.sys.executable,
                scripts_extract_dir=module.SCRIPTS_EXTRACT_DIR,
                repo_root=module.REPO_ROOT,
                run_cmd=module._run_cmd,
            )

        self.assertEqual(events, ["server", "hooks", "schema"])
        self.assertEqual(
            results,
            {
                "server_endpoints": "server summary",
                "js_hooks": "hooks summary",
                "node_api_schema": "schema summary",
            },
        )

    def test_run_extractors_wrapper_delegates_to_refresh_pipeline(self):
        """run_extractors should remain a thin wrapper over refresh_pipeline."""
        module = _load_module()
        expected = {"server_endpoints": "summary"}
        with mock.patch.object(
            module.refresh_pipeline,
            "run_extractors",
            return_value=expected,
        ) as pipeline_mock:
            result = module.run_extractors(
                core_version="v0.20.1",
                core_commit="core-sha",
                frontend_version=None,
                frontend_commit=None,
                snapshot_date="2026-05-14",
                runtime_object_info_path=None,
            )

        pipeline_mock.assert_called_once()
        self.assertEqual(result, expected)

    def test_run_markdown_generation_skips_when_no_output_is_configured(self):
        """Markdown generation should not call md_from_json.py without an output path."""
        module = _load_module()

        def fake_run_cmd(cmd, description, cwd=None):
            raise AssertionError(f"unexpected command: {cmd}")

        result = module.refresh_pipeline.run_markdown_generation(
            python_executable="python",
            scripts_generate_dir=module.SCRIPTS_GENERATE_DIR,
            repo_root=module.REPO_ROOT,
            run_cmd=fake_run_cmd,
        )

        self.assertTrue(result)

    def test_build_follow_up_commands_from_provenance_omits_missing_delta_step(self):
        """Recommended command rendering should skip the delta step when no backup exists."""
        module = _load_module()
        commands = module.build_follow_up_commands_from_provenance(
            {
                "next_steps": {
                    "publish_reference_artifacts_command": "publish",
                    "verify_artifact_integrity_command": "verify",
                    "delta_summary_command": None,
                    "run_all_command": "run-all",
                }
            }
        )

        self.assertEqual(commands, ["publish", "verify", "run-all"])

    def test_persist_refresh_provenance_adds_recommended_follow_up_sequence(self):
        """Persisted provenance should include the ordered follow-up command sequence."""
        module = _load_module()
        args = mock.Mock(
            core_version="v0.20.1",
            frontend_version="v1.44.13",
            runtime_object_info_url=None,
            skip_runtime_merge=False,
        )
        payload = {
            "next_steps": {
                "publish_reference_artifacts_command": "publish",
                "verify_artifact_integrity_command": "verify",
                "delta_summary_command": "delta",
                "run_all_command": "run-all",
            }
        }
        with (
            mock.patch.object(
                module,
                "build_refresh_provenance",
                return_value=payload,
            ),
            mock.patch.object(
                module,
                "write_refresh_provenance",
                return_value=module.PROVENANCE_OUTPUT_PATH,
            ) as write_mock,
        ):
            written = module.persist_refresh_provenance(
                args,
                "2026-05-18",
                "core-sha",
                "frontend-sha",
                module.REPO_ROOT / "references" / "_refresh_backups" / "raw_20260518T010203Z",
            )

        persisted_payload = write_mock.call_args.args[0]
        self.assertEqual(
            persisted_payload["next_steps"]["recommended_follow_up_commands"],
            ["publish", "verify", "delta", "run-all"],
        )
        self.assertEqual(written, module.PROVENANCE_OUTPUT_PATH)


if __name__ == "__main__":
    unittest.main()
