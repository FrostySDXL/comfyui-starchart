"""Tests for scripts/verify/snapshot_surface_coverage.py."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "snapshot_surface_coverage.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("snapshot_surface_coverage", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SnapshotSurfaceCoverageTests(unittest.TestCase):
    """Unit tests for required snapshot surface verification."""

    def _write_required_files(self, root: Path, required_files: list[str]) -> None:
        for rel_path in required_files:
            path = root / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            if rel_path == "server.py":
                path.write_text("from protocol import BinaryEventTypes\n", encoding="utf-8")
            else:
                path.write_text("x = 1\n", encoding="utf-8")

    def test_passing_snapshot_with_required_files(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            core_root = root / "snapshots" / "2026-06-03" / "comfyui-core-v0.23.0"
            frontend_root = root / "snapshots" / "2026-06-03" / "comfyui-frontend-v1.46.6"
            self._write_required_files(core_root, module.snapshot_surface.CORE_REQUIRED_FILES)
            self._write_required_files(
                frontend_root,
                module.snapshot_surface.FRONTEND_REQUIRED_FILES,
            )

            failures = module.validate_snapshot_surface(core_root, frontend_root)

        self.assertEqual(failures, [])

    def test_missing_protocol_py_failure(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            core_root = Path(tmp) / "comfyui-core-v0.23.0"
            frontend_root = Path(tmp) / "comfyui-frontend-v1.46.6"
            self._write_required_files(core_root, module.snapshot_surface.CORE_REQUIRED_FILES)
            self._write_required_files(
                frontend_root,
                module.snapshot_surface.FRONTEND_REQUIRED_FILES,
            )
            (core_root / "protocol.py").unlink()

            failures = module.validate_snapshot_surface(core_root, frontend_root)

        self.assertTrue(any("protocol.py" in failure for failure in failures))

    def test_missing_progress_py_failure(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            core_root = Path(tmp) / "comfyui-core-v0.23.0"
            frontend_root = Path(tmp) / "comfyui-frontend-v1.46.6"
            self._write_required_files(core_root, module.snapshot_surface.CORE_REQUIRED_FILES)
            self._write_required_files(
                frontend_root,
                module.snapshot_surface.FRONTEND_REQUIRED_FILES,
            )
            (core_root / "comfy_execution" / "progress.py").unlink()

            failures = module.validate_snapshot_surface(core_root, frontend_root)

        self.assertTrue(any("comfy_execution/progress.py" in failure for failure in failures))

    def test_missing_frontend_required_file_failure(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            core_root = Path(tmp) / "comfyui-core-v0.23.0"
            frontend_root = Path(tmp) / "comfyui-frontend-v1.46.6"
            self._write_required_files(core_root, module.snapshot_surface.CORE_REQUIRED_FILES)
            self._write_required_files(
                frontend_root,
                module.snapshot_surface.FRONTEND_REQUIRED_FILES,
            )
            (frontend_root / "src" / "scripts" / "app.ts").unlink()

            failures = module.validate_snapshot_surface(core_root, frontend_root)

        self.assertTrue(any("src/scripts/app.ts" in failure for failure in failures))

    def test_targeted_import_rule_ignores_comments_and_strings(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            server_path.write_text(
                "# from protocol import BinaryEventTypes\n"
                "text = 'from protocol import BinaryEventTypes'\n",
                encoding="utf-8",
            )

            imports_enum = module.server_imports_binary_event_types(server_path)

        self.assertFalse(imports_enum)

    def test_targeted_import_rule_detects_ast_import(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            server_path.write_text("from protocol import BinaryEventTypes\n", encoding="utf-8")

            imports_enum = module.server_imports_binary_event_types(server_path)

        self.assertTrue(imports_enum)


if __name__ == "__main__":
    unittest.main()
