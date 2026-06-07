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

    def test_core_include_globs_cover_expected_snapshot_subtrees(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            core_root = Path(tmp) / "comfyui-core-v0.23.0"
            expected_matches = {
                "top_level.py",
                "app/routes/api.py",
                "comfy_execution/progress.py",
                "comfy_api/latest/_io.py",
            }
            for rel_path in expected_matches:
                path = core_root / rel_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("x = 1\n", encoding="utf-8")

            resolved, missing = module.snapshot_surface.resolve_snapshot_files(
                core_root,
                [],
                module.snapshot_surface.CORE_INCLUDE_GLOBS,
            )

        self.assertEqual(missing, [])
        self.assertTrue(expected_matches.issubset(set(resolved)))

    def test_frontend_include_globs_cover_expected_snapshot_subtrees(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            frontend_root = Path(tmp) / "comfyui-frontend-v1.46.6"
            expected_matches = {
                "src/scripts/app.ts",
                "src/scripts/ui.tsx",
                "src/types/comfy.ts",
                "src/types/comfy.tsx",
                "src/services/litegraphService.ts",
                "src/services/litegraphService.tsx",
                "src/api/client.ts",
                "src/api/client.tsx",
            }
            for rel_path in expected_matches:
                path = frontend_root / rel_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("export const x = 1;\n", encoding="utf-8")

            resolved, missing = module.snapshot_surface.resolve_snapshot_files(
                frontend_root,
                [],
                module.snapshot_surface.FRONTEND_INCLUDE_GLOBS,
            )

        self.assertEqual(missing, [])
        self.assertTrue(expected_matches.issubset(set(resolved)))

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

    def test_classify_snapshot_inventory_marks_partial_without_failure(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            snapshots_root = Path(tmp) / "snapshots"
            current_core = snapshots_root / "2026-06-03" / "comfyui-core-v0.23.0"
            current_frontend = snapshots_root / "2026-06-03" / "comfyui-frontend-v1.46.6"
            historical_core = snapshots_root / "2026-06-01" / "comfyui-core-v0.23.0"
            self._write_required_files(current_core, module.snapshot_surface.CORE_REQUIRED_FILES)
            self._write_required_files(
                current_frontend,
                module.snapshot_surface.FRONTEND_REQUIRED_FILES,
            )
            self._write_required_files(historical_core, ["server.py"])

            rows = module.classify_snapshot_inventory(
                snapshots_root,
                current_core,
                current_frontend,
            )

        by_date = {row["snapshot_date"]: row for row in rows}
        self.assertEqual(
            by_date["2026-06-03"]["completeness_class"],
            "current-required-complete",
        )
        self.assertEqual(
            by_date["2026-06-01"]["completeness_class"],
            "historical-partial",
        )
        self.assertIn("not suitable", by_date["2026-06-01"]["extraction_suitability"])

    def test_snapshot_inventory_classification_is_stable(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            snapshots_root = Path(tmp) / "snapshots"
            current_core = snapshots_root / "2026-06-03" / "comfyui-core-v0.23.0"
            current_frontend = snapshots_root / "2026-06-03" / "comfyui-frontend-v1.46.6"
            partial_core = snapshots_root / "2026-05-21" / "comfyui-core-v0.22.0"
            empty_snapshot = snapshots_root / "2026-04-30"
            self._write_required_files(current_core, module.snapshot_surface.CORE_REQUIRED_FILES)
            self._write_required_files(
                current_frontend,
                module.snapshot_surface.FRONTEND_REQUIRED_FILES,
            )
            self._write_required_files(partial_core, ["server.py", "execution.py"])
            empty_snapshot.mkdir(parents=True)

            first = module.classify_snapshot_inventory(
                snapshots_root,
                current_core,
                current_frontend,
            )
            second = module.classify_snapshot_inventory(
                snapshots_root,
                current_core,
                current_frontend,
            )

        self.assertEqual(first, second)
        self.assertEqual(
            [row["snapshot_date"] for row in first], sorted(row["snapshot_date"] for row in first)
        )


if __name__ == "__main__":
    unittest.main()
