from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "common" / "refresh_pipeline.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("refresh_pipeline", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RefreshPipelineWebsocketExtractorTests(unittest.TestCase):
    def test_run_websocket_events_extractor_uses_core_and_frontend_sources(self):
        module = _load_module()
        with tempfile_like_tree() as root:
            core_dir = root / "snapshots" / "2026-06-03" / "comfyui-core-v0.23.0"
            frontend_dir = root / "snapshots" / "2026-06-03" / "comfyui-frontend-v1.46.6"
            for rel_path in [
                "server.py",
                "main.py",
                "execution.py",
                "protocol.py",
                "comfy_execution/progress.py",
            ]:
                path = core_dir / rel_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("x", encoding="utf-8")
            app_path = frontend_dir / "src" / "scripts" / "app.ts"
            app_path.parent.mkdir(parents=True, exist_ok=True)
            app_path.write_text("x", encoding="utf-8")

            run_cmd = mock.Mock(return_value=mock.Mock(stdout="Extracted 10 WebSocket events\n"))
            summary = module._run_websocket_events_extractor(
                core_dir,
                "v0.23.0",
                "core-sha",
                frontend_dir,
                "v1.46.6",
                "frontend-sha",
                python_executable="python",
                scripts_extract_dir=root / "scripts" / "extract",
                repo_root=root,
                run_cmd=run_cmd,
            )

        self.assertEqual(summary, "Extracted 10 WebSocket events")
        command = run_cmd.call_args.args[0]
        self.assertEqual(command[0], "python")
        self.assertTrue(command[1].endswith("parse_websocket_events.py"))
        self.assertEqual(
            command[2:8],
            [
                str(core_dir / "server.py"),
                str(core_dir / "main.py"),
                str(core_dir / "execution.py"),
                str(core_dir / "protocol.py"),
                str(core_dir / "comfy_execution" / "progress.py"),
                str(app_path),
            ],
        )
        self.assertEqual(
            command[8:],
            [
                "--version",
                "v0.23.0+v1.46.6",
                "--commit",
                "core-sha",
                "--frontend-commit",
                "frontend-sha",
            ],
        )

    def test_run_extractors_skips_websocket_when_pair_is_unavailable(self):
        module = _load_module()
        with tempfile_like_tree() as root:
            with mock.patch.object(module, "_run_server_extractor", return_value="server summary"):
                results = module.run_extractors(
                    core_version="v0.23.0",
                    core_commit="core-sha",
                    frontend_version=None,
                    frontend_commit=None,
                    snapshot_date="2026-06-03",
                    runtime_object_info_path=None,
                    snapshots_dir=root / "snapshots",
                    python_executable="python",
                    scripts_extract_dir=root / "scripts" / "extract",
                    repo_root=root,
                    run_cmd=mock.Mock(),
                )

        self.assertEqual(results, {"server_endpoints": "server summary"})

    def test_run_extractors_runs_hooks_for_frontend_only_refresh(self):
        module = _load_module()
        with tempfile_like_tree() as root:
            with mock.patch.object(module, "_run_hooks_extractor", return_value="hooks summary"):
                results = module.run_extractors(
                    core_version=None,
                    core_commit=None,
                    frontend_version="v1.46.6",
                    frontend_commit="frontend-sha",
                    snapshot_date="2026-06-03",
                    runtime_object_info_path=None,
                    snapshots_dir=root / "snapshots",
                    python_executable="python",
                    scripts_extract_dir=root / "scripts" / "extract",
                    repo_root=root,
                    run_cmd=mock.Mock(),
                )

        self.assertEqual(results, {"js_hooks": "hooks summary"})


class tempfile_like_tree:
    def __enter__(self):
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        return Path(self._tmp.name)

    def __exit__(self, exc_type, exc, tb):
        self._tmp.cleanup()
        return False


if __name__ == "__main__":
    unittest.main()
