"""Tests for scripts/verify/delta_summary_integrity.py."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "delta_summary_integrity.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("delta_summary_integrity", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DeltaSummaryIntegrityTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
