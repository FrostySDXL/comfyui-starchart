"""Tests for scripts/verify/provenance_chain_integrity.py."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "provenance_chain_integrity.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("provenance_chain_integrity", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _base_provenance(backup: str | None = "references/_refresh_backups/raw_20260603T183637Z"):
    delta_command = None
    if backup is not None:
        delta_command = (
            f'python scripts/generate/generate_snapshot_delta_summary.py --old "{backup}" '
            '--new "references/raw" --output "public/artifacts/delta-summary.json"'
        )
    commands = [
        "python scripts/generate/publish_reference_artifacts.py",
        "python scripts/verify/verify_artifact_integrity.py",
    ]
    if delta_command is not None:
        commands.append(delta_command)
    commands.append("python scripts/verify/run_all.py")
    return {
        "backup_location": backup,
        "next_steps": {
            "publish_reference_artifacts_command": commands[0],
            "verify_artifact_integrity_command": commands[1],
            "delta_summary_command": delta_command,
            "run_all_command": "python scripts/verify/run_all.py",
            "recommended_follow_up_commands": commands,
        },
        "published": {
            "canonical_artifacts_updated_by_refresh": True,
            "delta_summary_updated_by_refresh": True,
            "manifest_included": True,
            "provenance_path": "public/artifacts/refresh-provenance.json",
        },
    }


def _write_current_artifacts(root: Path) -> None:
    _write_json(
        root / "public" / "artifacts" / "manifest.json",
        {"version_key": "current", "artifact_schema_version": "1.0.0"},
    )
    for name in (
        "server_endpoints.json",
        "js_hooks.json",
        "node_api_schema.json",
        "websocket_events.json",
    ):
        (root / "public" / "artifacts" / "current" / name).parent.mkdir(parents=True, exist_ok=True)
        (root / "public" / "artifacts" / "current" / name).write_text("{}\n", encoding="utf-8")


class ProvenanceChainIntegrityTests(unittest.TestCase):
    """Unit tests for provenance chain validation."""

    def test_recommended_commands_must_be_in_expected_order(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            backup = root / "references" / "_refresh_backups" / "raw_20260603T183637Z"
            backup.mkdir(parents=True)
            _write_json(
                root / "public" / "artifacts" / "refresh-provenance.json",
                _base_provenance(backup.as_posix()),
            )
            _write_current_artifacts(root)
            _write_json(
                root / "public" / "artifacts" / "delta-summary.json",
                {"comparison": {"old": backup.as_posix(), "new": "references/raw"}},
            )
            provenance = json.loads(
                (root / "public" / "artifacts" / "refresh-provenance.json").read_text()
            )
            provenance["next_steps"]["recommended_follow_up_commands"] = list(
                reversed(provenance["next_steps"]["recommended_follow_up_commands"])
            )
            _write_json(root / "public" / "artifacts" / "refresh-provenance.json", provenance)

            result = module.evaluate_provenance_chain(root)

        self.assertTrue(any("recommended_follow_up_commands" in error for error in result.errors))

    def test_stale_backup_warning_for_missing_empty_and_unreferenced_paths(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            missing = "references/_refresh_backups/raw_missing"
            _write_json(root / "missing.json", _base_provenance(missing))
            _write_json(root / "missing-delta.json", {"comparison": {"old": missing}})

            empty = "references/_refresh_backups/raw_empty"
            (root / empty).mkdir(parents=True)
            _write_json(root / "empty.json", _base_provenance(empty))
            _write_json(root / "empty-delta.json", {"comparison": {"old": empty}})

            unreferenced = "references/_refresh_backups/raw_unreferenced"
            (root / unreferenced).mkdir(parents=True)
            (root / unreferenced / "server_endpoints.json").write_text("{}\n", encoding="utf-8")
            _write_json(root / "unreferenced.json", _base_provenance(unreferenced))
            _write_json(root / "unreferenced-delta.json", {"comparison": {"old": "other"}})

            missing_result = module.validate_stale_backup_reference(
                root,
                json.loads((root / "missing.json").read_text()),
                json.loads((root / "missing-delta.json").read_text()),
            )
            empty_result = module.validate_stale_backup_reference(
                root,
                json.loads((root / "empty.json").read_text()),
                json.loads((root / "empty-delta.json").read_text()),
            )
            unreferenced_result = module.validate_stale_backup_reference(
                root,
                json.loads((root / "unreferenced.json").read_text()),
                json.loads((root / "unreferenced-delta.json").read_text()),
            )

        combined = missing_result + empty_result + unreferenced_result
        self.assertTrue(any("missing on disk" in warning for warning in combined))
        self.assertTrue(any("empty on disk" in warning for warning in combined))
        self.assertTrue(any("not referenced by delta-summary" in warning for warning in combined))

    def test_reverse_false_flag_warnings_when_state_exists(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_current_artifacts(root)
            _write_json(
                root / "public" / "artifacts" / "delta-summary.json",
                {"comparison": {"old": "backup"}},
            )
            provenance = _base_provenance(None)
            provenance["published"]["canonical_artifacts_updated_by_refresh"] = False
            provenance["published"]["delta_summary_updated_by_refresh"] = False
            _write_json(root / "public" / "artifacts" / "refresh-provenance.json", provenance)

            result = module.evaluate_provenance_chain(root)

        self.assertTrue(
            any(
                "canonical artifacts exist but flag is false" in warning
                for warning in result.warnings
            )
        )
        self.assertTrue(
            any(
                "delta-summary.json exists but flag is false" in warning
                for warning in result.warnings
            )
        )

    def test_all_false_flags_without_state_do_not_warn(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            provenance = _base_provenance(None)
            provenance["published"]["canonical_artifacts_updated_by_refresh"] = False
            provenance["published"]["delta_summary_updated_by_refresh"] = False
            _write_json(root / "public" / "artifacts" / "refresh-provenance.json", provenance)

            result = module.evaluate_provenance_chain(root)

        self.assertEqual(result.errors, ())
        self.assertEqual(result.warnings, ())

    def test_report_output_is_idempotent(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            backup = root / "references" / "_refresh_backups" / "raw_20260603T183637Z"
            backup.mkdir(parents=True)
            (backup / "server_endpoints.json").write_text("{}\n", encoding="utf-8")
            _write_current_artifacts(root)
            _write_json(
                root / "public" / "artifacts" / "refresh-provenance.json",
                _base_provenance(backup.as_posix()),
            )
            _write_json(
                root / "public" / "artifacts" / "delta-summary.json",
                {"comparison": {"old": backup.as_posix(), "new": "references/raw"}},
            )

            first = module.format_report(module.evaluate_provenance_chain(root))
            second = module.format_report(module.evaluate_provenance_chain(root))

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
