"""Tests for examples/consumers/python-manifest-reader/validate_artifact.py."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "examples" / "consumers" / "python-manifest-reader" / "validate_artifact.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("validate_artifact", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidateArtifactTests(unittest.TestCase):
    """Entry-point tests using local file URLs and checksum fixtures."""

    def test_main_accepts_valid_checksum(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_manifest_fixture(root, checksum_override=None)

            result = module.main(["validate_artifact.py", root.as_uri(), "server_endpoints.json"])

        self.assertEqual(result, 0)

    def test_main_rejects_mismatched_checksum(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_manifest_fixture(root, checksum_override="0" * 64)

            result = module.main(["validate_artifact.py", root.as_uri(), "server_endpoints.json"])

        self.assertEqual(result, 1)

    def test_missing_manifest_raises_file_error(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            with self.assertRaises(Exception):
                module.main(["validate_artifact.py", root.as_uri(), "server_endpoints.json"])

    @staticmethod
    def _write_manifest_fixture(root: Path, checksum_override: str | None) -> None:
        artifacts_dir = root / "artifacts"
        current_dir = artifacts_dir / "current"
        current_dir.mkdir(parents=True)
        artifact = {
            "endpoints": [],
            "coverage": {"guaranteed_fields": [], "best_effort_fields": []},
        }
        artifact_bytes = json.dumps(artifact).encode("utf-8")
        artifact_path = current_dir / "server_endpoints.json"
        artifact_path.write_bytes(artifact_bytes)
        sha256 = checksum_override or hashlib.sha256(artifact_bytes).hexdigest()
        manifest = {
            "artifacts": {
                "server_endpoints.json": {
                    "current_url": "artifacts/current/server_endpoints.json",
                    "sha256": sha256,
                }
            }
        }
        (artifacts_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
