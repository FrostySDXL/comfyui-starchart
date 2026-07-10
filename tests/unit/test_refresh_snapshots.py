"""Tests for scripts/refresh_snapshots.py."""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.common import refresh_git_ops, snapshot_surface

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

    def test_key_functions_are_importable_and_callable(self):
        """The refresh_snapshots module should expose callable entrypoints."""
        module = _load_module()
        for name in [
            "main",
            "refresh_core",
            "refresh_frontend",
            "run_extractors",
            "run_markdown_generation",
        ]:
            with self.subTest(name=name):
                self.assertTrue(hasattr(module, name))
                self.assertTrue(callable(getattr(module, name)))


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

    def test_module_paths_are_existing_repo_local_paths(self):
        """Module path constants should resolve inside this repository."""
        module = _load_module()
        self.assertEqual(module.REPO_ROOT, REPO_ROOT)
        for name in [
            "REFERENCES_RAW_DIR",
            "SNAPSHOTS_DIR",
            "SCRIPTS_EXTRACT_DIR",
            "SCRIPTS_GENERATE_DIR",
        ]:
            with self.subTest(name=name):
                path = getattr(module, name)
                self.assertTrue(path.exists())
                self.assertTrue(str(path).startswith(str(module.REPO_ROOT)))

    def test_core_snapshot_surface_contract(self):
        """Core snapshot contract should require source files needed by extractors."""
        module = _load_module()
        required = set(snapshot_surface.CORE_REQUIRED_FILES)
        for rel_path in [
            "server.py",
            "execution.py",
            "protocol.py",
            "comfy_execution/progress.py",
            "pyproject.toml",
            "requirements.txt",
            "app/frontend_management.py",
            "comfy_api/latest/_io.py",
            "comfy_api/latest/_input/basic_types.py",
        ]:
            self.assertIn(rel_path, required)
        self.assertEqual(module.CORE_FILES, snapshot_surface.CORE_REQUIRED_FILES)
        self.assertIn("*.py", snapshot_surface.CORE_INCLUDE_GLOBS)
        self.assertIn("comfy_execution/**/*.py", snapshot_surface.CORE_INCLUDE_GLOBS)
        self.assertIn("comfy_api/latest/**/*.py", snapshot_surface.CORE_INCLUDE_GLOBS)

    def test_frontend_snapshot_surface_contract(self):
        """Frontend snapshot contract should require extractor source files."""
        module = _load_module()
        required = set(snapshot_surface.FRONTEND_REQUIRED_FILES)
        for rel_path in [
            "package.json",
            "src/scripts/app.ts",
            "src/types/comfy.ts",
            "src/services/litegraphService.ts",
        ]:
            self.assertIn(rel_path, required)
        self.assertEqual(module.FRONTEND_FILES, snapshot_surface.FRONTEND_REQUIRED_FILES)
        self.assertIn("src/scripts/**/*.ts", snapshot_surface.FRONTEND_INCLUDE_GLOBS)
        self.assertIn("src/api/**/*.tsx", snapshot_surface.FRONTEND_INCLUDE_GLOBS)

    def test_resolve_snapshot_files_returns_sorted_deduplicated_paths(self):
        """Resolver should include required files and controlled glob matches."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel_path in [
                "server.py",
                "protocol.py",
                "comfy_execution/progress.py",
                "app/frontend_management.py",
                "notes/readme.md",
            ]:
                path = root / rel_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("x", encoding="utf-8")

            resolved, missing = snapshot_surface.resolve_snapshot_files(
                root,
                ["server.py", "protocol.py", "comfy_execution/progress.py"],
                ["*.py", "app/**/*.py", "comfy_execution/**/*.py"],
            )

        self.assertEqual(missing, [])
        self.assertEqual(resolved, sorted(set(resolved)))
        self.assertIn("protocol.py", resolved)
        self.assertIn("comfy_execution/progress.py", resolved)
        self.assertIn("app/frontend_management.py", resolved)
        self.assertNotIn("notes/readme.md", resolved)

    def test_resolve_snapshot_files_reports_missing_required_paths(self):
        """Resolver should report required files missing from the clone root."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "server.py").write_text("x", encoding="utf-8")

            resolved, missing = snapshot_surface.resolve_snapshot_files(
                root,
                ["server.py", "protocol.py"],
                ["*.py"],
            )

        self.assertEqual(resolved, ["server.py"])
        self.assertEqual(missing, ["protocol.py"])

    def test_repo_urls_are_set(self):
        """CORE_REPO_URL and FRONTEND_REPO_URL should be set."""
        module = _load_module()
        cases = [
            (module.CORE_REPO_URL, "ComfyUI"),
            (module.FRONTEND_REPO_URL, "ComfyUI_Frontend"),
        ]
        for url, repo_name in cases:
            with self.subTest(repo_name=repo_name):
                self.assertIn("github.com", url)
                self.assertIn(repo_name, url)


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
        self.assertTrue(callable(module.run_runtime_extraction))

    def test_default_refresh_context_matches_module_paths(self):
        """Default RefreshContext should centralize refresh paths and command runner."""
        module = _load_module()
        self.assertIsInstance(module.DEFAULT_REFRESH_CONTEXT, module.RefreshContext)
        self.assertEqual(module.DEFAULT_REFRESH_CONTEXT.repo_root, module.REPO_ROOT)
        self.assertEqual(
            module.DEFAULT_REFRESH_CONTEXT.references_raw_dir,
            module.REFERENCES_RAW_DIR,
        )
        self.assertEqual(module.DEFAULT_REFRESH_CONTEXT.snapshots_dir, module.SNAPSHOTS_DIR)
        self.assertEqual(
            module.DEFAULT_REFRESH_CONTEXT.scripts_extract_dir,
            module.SCRIPTS_EXTRACT_DIR,
        )
        self.assertEqual(
            module.DEFAULT_REFRESH_CONTEXT.scripts_generate_dir,
            module.SCRIPTS_GENERATE_DIR,
        )
        self.assertEqual(
            module.DEFAULT_REFRESH_CONTEXT.provenance_output_path,
            module.PROVENANCE_OUTPUT_PATH,
        )
        self.assertEqual(module.DEFAULT_REFRESH_CONTEXT.python_executable, sys.executable)
        self.assertIs(module.DEFAULT_REFRESH_CONTEXT.run_cmd, module._run_cmd)

    def test_run_extractors_accepts_refresh_context(self):
        """run_extractors should use a supplied RefreshContext without global path lookups."""
        module = _load_module()
        context = module.RefreshContext(
            repo_root=Path("repo-root"),
            references_dir=Path("references"),
            references_raw_dir=Path("raw"),
            snapshots_dir=Path("snapshots"),
            scripts_extract_dir=Path("extract"),
            scripts_generate_dir=Path("generate"),
            provenance_output_path=Path("provenance.json"),
            python_executable="python-custom",
            run_cmd=mock.Mock(name="run_cmd"),
        )
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
                context=context,
            )

        pipeline_mock.assert_called_once_with(
            core_version="v0.20.1",
            core_commit="core-sha",
            frontend_version=None,
            frontend_commit=None,
            snapshot_date="2026-05-14",
            runtime_object_info_path=None,
            snapshots_dir=Path("snapshots"),
            python_executable="python-custom",
            scripts_extract_dir=Path("extract"),
            repo_root=Path("repo-root"),
            run_cmd=context.run_cmd,
        )
        self.assertEqual(result, expected)

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

    def test_refresh_git_ops_copy_source_files_copies_optional_existing_files(self):
        """_copy_source_files should copy existing optional files and skip missing ones."""
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
                required_files=["keep.py"],
            )

            self.assertEqual(copied, ["keep.py", "skip.txt"])
            self.assertTrue((dest_dir / "keep.py").exists())
            self.assertTrue((dest_dir / "skip.txt").exists())
            self.assertFalse((dest_dir / "missing.py").exists())

    def test_refresh_git_ops_copy_source_files_raises_for_missing_required_file(self):
        """_copy_source_files should fail loudly when a required file is absent."""
        with tempfile.TemporaryDirectory() as tmp:
            src_dir = Path(tmp) / "src"
            src_dir.mkdir()
            dest_dir = Path(tmp) / "dest"

            with self.assertRaises(RuntimeError) as exc:
                refresh_git_ops._copy_source_files(
                    str(src_dir),
                    dest_dir,
                    ["missing.py"],
                    "test-repo",
                    required_files=["missing.py"],
                )

        self.assertIn("missing.py", str(exc.exception))

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

    def test_refresh_git_ops_run_cmd_uses_clone_timeout(self):
        """Shared git helper should pass the clone timeout to subprocess.run."""
        with mock.patch.object(
            refresh_git_ops.subprocess,
            "run",
            return_value=mock.Mock(returncode=0, stdout="ok", stderr=""),
        ) as run_mock:
            refresh_git_ops._run_cmd(["git", "status"], "git status")

        self.assertEqual(
            run_mock.call_args.kwargs["timeout"], refresh_git_ops.DEFAULT_CLONE_TIMEOUT_SECONDS
        )

    def test_refresh_git_ops_run_cmd_failure_includes_tails_and_log_path(self):
        """Git failures should include bounded output tails and the full temp log path."""
        log_dir = Path(tempfile.gettempdir()) / "refresh-git-ops-test"
        with mock.patch.object(
            refresh_git_ops.subprocess,
            "run",
            return_value=mock.Mock(returncode=1, stdout="a" * 700, stderr="b" * 700),
        ):
            with self.assertRaises(RuntimeError) as exc:
                refresh_git_ops._run_cmd(["git", "status"], "git status", log_dir=log_dir)

        message = str(exc.exception)
        self.assertIn("stdout head:", message)
        self.assertIn("stdout tail:", message)
        self.assertIn("stderr head:", message)
        self.assertIn("stderr tail:", message)
        self.assertIn(str(log_dir / "log.txt"), message)

    def test_refresh_repo_snapshot_cleans_temp_log_dir(self):
        """Refresh helper should remove the per-invocation git log directory."""
        log_dir = Path(tempfile.gettempdir()) / "refresh-git-ops-cleanup-test"
        log_dir.mkdir(exist_ok=True)
        with (
            mock.patch.object(refresh_git_ops.tempfile, "mkdtemp", return_value=str(log_dir)),
            mock.patch.object(refresh_git_ops.tempfile, "TemporaryDirectory") as tmpdir_mock,
            mock.patch.object(refresh_git_ops, "_run_cmd", return_value=mock.Mock(stdout="sha\n")),
            mock.patch.object(refresh_git_ops, "_copy_source_files", return_value=[]),
        ):
            tmpdir_mock.return_value.__enter__.return_value = str(log_dir / "clone")
            refresh_git_ops._refresh_repo_snapshot(
                version="v0.20.1",
                snapshot_date="2026-05-14",
                repo_url="https://example.invalid/repo.git",
                snapshots_dir=Path(tempfile.gettempdir()),
                dest_prefix="repo",
                heading_label="Repo",
                clone_label="Repo",
                copy_label="repo",
                temp_prefix="repo-",
                files=[],
            )

        self.assertFalse(log_dir.exists())

    def test_refresh_git_ops_verify_git_available_returns_version_string(self):
        """Shared git availability helper should return the resolved version string."""
        with mock.patch.object(
            refresh_git_ops,
            "_run_cmd",
            return_value=mock.Mock(stdout="git version 2.50.0\n"),
        ):
            version = refresh_git_ops.verify_git_available()

        self.assertEqual(version, "git version 2.50.0")

    def test_refresh_wrappers_delegate_to_generic_snapshot_helper(self):
        """refresh_core and refresh_frontend should bind constants to the shared helper."""
        module = _load_module()
        cases = [
            (
                "core",
                module.refresh_core,
                "v0.20.1",
                ("core-sha", "comfyui-core-v0.20.1"),
                {
                    "repo_url": module.CORE_REPO_URL,
                    "dest_prefix": "comfyui-core",
                    "heading_label": "ComfyUI Core",
                    "clone_label": "ComfyUI core",
                    "copy_label": "core",
                    "temp_prefix": "comfyui-core-",
                    "files": module.CORE_FILES,
                    "required_files": module.snapshot_surface.CORE_REQUIRED_FILES,
                    "include_globs": module.snapshot_surface.CORE_INCLUDE_GLOBS,
                },
            ),
            (
                "frontend",
                module.refresh_frontend,
                "v1.44.13",
                ("frontend-sha", "comfyui-frontend-v1.44.13"),
                {
                    "repo_url": module.FRONTEND_REPO_URL,
                    "dest_prefix": "comfyui-frontend",
                    "heading_label": "ComfyUI Frontend",
                    "clone_label": "ComfyUI Frontend",
                    "copy_label": "frontend",
                    "temp_prefix": "comfyui-frontend-",
                    "files": module.FRONTEND_FILES,
                    "required_files": module.snapshot_surface.FRONTEND_REQUIRED_FILES,
                    "include_globs": module.snapshot_surface.FRONTEND_INCLUDE_GLOBS,
                },
            ),
        ]
        for name, refresh_func, version, expected_result, expected_kwargs in cases:
            with self.subTest(name=name):
                with mock.patch.object(
                    module,
                    "_refresh_repo_snapshot",
                    return_value=expected_result,
                ) as helper_mock:
                    result = refresh_func(version, "2026-05-14")

                helper_mock.assert_called_once_with(
                    version=version,
                    snapshot_date="2026-05-14",
                    **expected_kwargs,
                )
                self.assertEqual(result, expected_result)

    def test_run_extractors_preserves_server_hooks_schema_websocket_sequence(self):
        """refresh_pipeline.run_extractors should keep server, hooks, schema, then websocket order."""
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
            mock.patch.object(
                module.refresh_pipeline,
                "_run_websocket_events_extractor",
                side_effect=_record("websocket", "websocket summary"),
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

        self.assertEqual(events, ["server", "hooks", "schema", "websocket"])
        self.assertEqual(
            results,
            {
                "server_endpoints": "server summary",
                "js_hooks": "hooks summary",
                "node_api_schema": "schema summary",
                "websocket_events": "websocket summary",
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
