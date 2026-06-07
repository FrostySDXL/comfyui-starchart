"""Unit tests for scripts/verify/governance_lifecycle.py."""

import datetime as dt
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "governance_lifecycle.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("governance_lifecycle", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _record(**overrides):
    record = {
        "purpose": "Test verifier purpose.",
        "owner": "Test owner.",
        "target_surface": "Test surface.",
        "false_positive_tolerance": {
            "level": "low",
            "justification": "Fixture is deterministic enough for low tolerance.",
        },
        "placement": "advisory",
        "promotion_criteria": "Promote after fixture evidence.",
        "demotion_criteria": "Demote after fixture evidence.",
        "removal_criteria": "Remove after fixture replacement.",
        "last_reviewed": "2026-06-07",
    }
    record.update(overrides)
    return record


class GovernanceLifecycleUnitTests(unittest.TestCase):
    """Direct unit tests for lifecycle validation helpers."""

    def test_accepts_typed_false_positive_tolerance_object(self):
        module = _load_module()
        manifest = {
            "records": {"scripts/verify/example.py": _record()},
            "exemptions": {},
        }

        with (
            patch.object(module, "direct_verifier_paths", return_value=set()),
            patch.object(module, "CONTRIBUTING_PATH") as contributing_path,
        ):
            contributing_path.read_text.return_value = "## Verifier Inventory\n"
            errors, warnings = module.validate_lifecycle_records(
                manifest, today=dt.date(2026, 6, 7)
            )

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_rejects_string_false_positive_tolerance(self):
        module = _load_module()
        manifest = {
            "records": {"scripts/verify/example.py": _record(false_positive_tolerance="low")},
            "exemptions": {},
        }

        with (
            patch.object(module, "direct_verifier_paths", return_value=set()),
            patch.object(module, "CONTRIBUTING_PATH") as contributing_path,
        ):
            contributing_path.read_text.return_value = "## Verifier Inventory\n"
            errors, _warnings = module.validate_lifecycle_records(
                manifest, today=dt.date(2026, 6, 7)
            )

        self.assertIn(
            "scripts/verify/example.py: false_positive_tolerance must be an object",
            errors,
        )

    def test_rejects_unknown_false_positive_level(self):
        module = _load_module()
        manifest = {
            "records": {
                "scripts/verify/example.py": _record(
                    false_positive_tolerance={
                        "level": "extreme",
                        "justification": "Invalid fixture level.",
                    }
                )
            },
            "exemptions": {},
        }

        with (
            patch.object(module, "direct_verifier_paths", return_value=set()),
            patch.object(module, "CONTRIBUTING_PATH") as contributing_path,
        ):
            contributing_path.read_text.return_value = "## Verifier Inventory\n"
            errors, _warnings = module.validate_lifecycle_records(
                manifest, today=dt.date(2026, 6, 7)
            )

        self.assertTrue(
            any("false_positive_tolerance.level must be one of" in error for error in errors)
        )

    def test_unwired_blocking_record_emits_warning(self):
        module = _load_module()
        manifest = {
            "records": {
                "scripts/verify/example.py": _record(placement="blocking"),
                "scripts/verify/wired.py": _record(placement="blocking"),
            }
        }

        warnings = module.check_wiring(
            manifest,
            run_all_text="wired.py",
            ci_text="scripts/verify/wired.py",
            advisory_text="",
        )

        self.assertIn(
            "scripts/verify/example.py: placement=blocking but not referenced in run_all.py",
            warnings,
        )
        self.assertIn(
            "scripts/verify/example.py: placement=blocking but not referenced in ci.yml",
            warnings,
        )
        self.assertFalse(any("wired.py" in warning for warning in warnings))

    def test_unsorted_manifest_serialization_is_rejected(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "verifier-lifecycle.json"
            manifest_path.write_text(
                json.dumps({"records": {}, "exemptions": {}}, indent=4),
                encoding="utf-8",
            )

            with patch.object(module, "REPO_ROOT", Path(tmpdir)):
                errors = module.check_manifest_serialization(manifest_path)

        self.assertEqual(
            errors,
            ["verifier-lifecycle.json: JSON must be sorted with stable two-space indentation"],
        )


if __name__ == "__main__":
    unittest.main()
