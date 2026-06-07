"""Tests for scripts/verify/delta_summary_integrity.py."""

import importlib.util
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "delta_summary_integrity.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("delta_summary_integrity", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DeltaSummaryIntegrityTests(unittest.TestCase):
    def _write_baseline(self, root: Path, *, route: str = "/a") -> None:
        root.mkdir(parents=True, exist_ok=True)
        (root / "server_endpoints.json").write_text(
            json.dumps(
                {"metadata": {}, "coverage": {}, "endpoints": [{"method": "GET", "route": route}]}
            ),
            encoding="utf-8",
        )
        (root / "js_hooks.json").write_text(
            json.dumps({"metadata": {}, "coverage": {}, "hooks": []}),
            encoding="utf-8",
        )
        (root / "node_api_schema.json").write_text(
            json.dumps(
                {
                    "metadata": {},
                    "coverage": {},
                    "object_info_fields": [],
                    "io_types": [],
                    "basic_input_shapes": {},
                    "typed_input_shapes": {},
                }
            ),
            encoding="utf-8",
        )
        (root / "websocket_events.json").write_text(
            json.dumps({"metadata": {}, "coverage": {}, "events": [], "binary_events": []}),
            encoding="utf-8",
        )

    def _write_summary_from_dirs(
        self, module, summary_path: Path, old_dir: Path, new_dir: Path
    ) -> None:
        old_artifacts = module._artifact_map(old_dir)
        new_artifacts = module._artifact_map(new_dir)
        summary = module.build_delta_summary(
            old_artifacts,
            new_artifacts,
            old_dir.as_posix(),
            new_dir.as_posix(),
        )
        summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    def test_missing_canonical_artifact_section_is_reported(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            summary_path = Path(tmpdir) / "delta-summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "artifacts": {
                            "server_endpoints": {},
                            "js_hooks": {},
                            "node_api_schema": {},
                        }
                    }
                ),
                encoding="utf-8",
            )

            errors = module.verify_delta_summary_integrity(summary_path)

        self.assertIn(
            "Missing delta-summary artifact section for websocket_events",
            errors,
        )

    def test_current_delta_summary_matches_canonical_artifact_set(self):
        module = _load_module()

        errors = module.verify_delta_summary_integrity(
            REPO_ROOT / "public" / "artifacts" / "delta-summary.json"
        )

        self.assertEqual(errors, [])

    def test_regenerated_delta_summary_exact_match_passes(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            old_dir = tmp_path / "old"
            new_dir = tmp_path / "new"
            self._write_baseline(old_dir)
            self._write_baseline(new_dir, route="/b")
            summary_path = tmp_path / "delta-summary.json"
            self._write_summary_from_dirs(module, summary_path, old_dir, new_dir)

            errors = module.regenerate_delta_summary_for_comparison(summary_path)

        self.assertEqual(errors, [])

    def test_regenerated_delta_summary_stale_output_fails(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            old_dir = tmp_path / "old"
            new_dir = tmp_path / "new"
            self._write_baseline(old_dir)
            self._write_baseline(new_dir, route="/b")
            summary_path = tmp_path / "delta-summary.json"
            self._write_summary_from_dirs(module, summary_path, old_dir, new_dir)
            data = json.loads(summary_path.read_text(encoding="utf-8"))
            data["artifacts"]["server_endpoints"]["added"] = []
            summary_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

            errors = module.regenerate_delta_summary_for_comparison(summary_path)

        self.assertTrue(any("regenerated output differs" in error for error in errors))

    def test_missing_comparison_path_fails_without_skip_regeneration(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            summary_path = tmp_path / "delta-summary.json"
            old_dir = tmp_path / "missing-old"
            new_dir = tmp_path / "new"
            self._write_baseline(new_dir)
            summary = module.build_delta_summary(
                module._artifact_map(new_dir),
                module._artifact_map(new_dir),
                old_dir.as_posix(),
                new_dir.as_posix(),
            )
            summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

            result = module.main(["--summary-path", str(summary_path)])

        self.assertEqual(result, 1)

    def test_skip_regeneration_keeps_membership_and_schema_checks_only(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            summary_path = tmp_path / "delta-summary.json"
            old_dir = tmp_path / "missing-old"
            new_dir = tmp_path / "new"
            self._write_baseline(new_dir)
            summary = module.build_delta_summary(
                module._artifact_map(new_dir),
                module._artifact_map(new_dir),
                old_dir.as_posix(),
                new_dir.as_posix(),
            )
            summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
            stdout = StringIO()

            with redirect_stdout(stdout):
                result = module.main(["--summary-path", str(summary_path), "--skip-regeneration"])

        self.assertEqual(result, 0)
        self.assertIn("regeneration skipped", stdout.getvalue())

    def test_skip_regeneration_does_not_bypass_membership_failure(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            summary_path = Path(tmpdir) / "delta-summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "comparison": {
                            "old": "missing-old",
                            "new": "missing-new",
                            "methodology": "artifact-directory-to-artifact-directory",
                        },
                        "notes": [],
                        "artifacts": {},
                    }
                ),
                encoding="utf-8",
            )

            result = module.main(["--summary-path", str(summary_path), "--skip-regeneration"])

        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
