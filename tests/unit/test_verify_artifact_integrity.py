"""Tests for scripts/verify/verify_artifact_integrity.py."""

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "verify_artifact_integrity.py"
ARTIFACT_FILES = [
    "server_endpoints.json",
    "js_hooks.json",
    "node_api_schema.json",
]


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_artifact_integrity", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VerifyArtifactIntegrityUnitTests(unittest.TestCase):
    """Unit tests for artifact integrity verification behavior."""

    def _write_fixture_tree(self, root: Path) -> tuple[Path, Path, Path]:
        canonical_dir = root / "references" / "raw"
        published_dir = root / "docs" / "artifacts" / "current"
        manifest_path = root / "docs" / "artifacts" / "manifest.json"
        canonical_dir.mkdir(parents=True)
        published_dir.mkdir(parents=True)

        artifact_payloads = {
            "server_endpoints.json": {"metadata": {"version": "v0.20.1"}, "endpoints": []},
            "js_hooks.json": {"metadata": {"version": "v1.44.13"}, "hooks": []},
            "node_api_schema.json": {"metadata": {"version": "v0.20.1"}, "object_info_fields": []},
        }

        manifest = {"version_key": "test-key", "artifacts": {}}
        for name, payload in artifact_payloads.items():
            artifact_text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
            (canonical_dir / name).write_text(artifact_text, encoding="utf-8")
            (published_dir / name).write_text(artifact_text, encoding="utf-8")
            digest = hashlib.sha256((published_dir / name).read_bytes()).hexdigest()
            manifest["artifacts"][name] = {
                "current_url": f"artifacts/current/{name}",
                "versioned_url": f"artifacts/versions/test-key/{name}",
                "sha256": digest,
                "version": payload["metadata"]["version"],
                "commit": "test-commit",
                "extracted_date": "2026-04-30",
                "sources": [f"references/snapshots/test/{name}"],
            }

        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return manifest_path, canonical_dir, published_dir

    def test_clean_pass_case(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path, canonical_dir, published_dir = self._write_fixture_tree(Path(tmpdir))
            self.assertEqual(
                module.verify_integrity(manifest_path, canonical_dir, published_dir),
                [],
            )

    def test_missing_current_artifact(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path, canonical_dir, published_dir = self._write_fixture_tree(Path(tmpdir))
            (published_dir / "js_hooks.json").unlink()

            errors = module.verify_integrity(manifest_path, canonical_dir, published_dir)

            self.assertTrue(any("Missing published artifact" in error for error in errors))

    def test_missing_canonical_artifact(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path, canonical_dir, published_dir = self._write_fixture_tree(Path(tmpdir))
            (canonical_dir / "js_hooks.json").unlink()

            errors = module.verify_integrity(manifest_path, canonical_dir, published_dir)

            self.assertTrue(any("Missing canonical artifact" in error for error in errors))

    def test_raw_current_mismatch(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path, canonical_dir, published_dir = self._write_fixture_tree(Path(tmpdir))
            (published_dir / "server_endpoints.json").write_text(
                '{"metadata": {"version": "different"}}\n',
                encoding="utf-8",
            )

            errors = module.verify_integrity(manifest_path, canonical_dir, published_dir)

            self.assertTrue(any("Canonical/published mismatch" in error for error in errors))

    def test_manifest_hash_mismatch(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path, canonical_dir, published_dir = self._write_fixture_tree(Path(tmpdir))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["artifacts"]["node_api_schema.json"]["sha256"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            errors = module.verify_integrity(manifest_path, canonical_dir, published_dir)

            self.assertTrue(any("Manifest hash mismatch" in error for error in errors))

    def test_missing_manifest_entry(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path, canonical_dir, published_dir = self._write_fixture_tree(Path(tmpdir))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            del manifest["artifacts"]["js_hooks.json"]
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            errors = module.verify_integrity(manifest_path, canonical_dir, published_dir)

            self.assertTrue(any("Missing manifest entry for js_hooks.json" == error for error in errors))

    def test_missing_manifest_file(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path, canonical_dir, published_dir = self._write_fixture_tree(Path(tmpdir))
            manifest_path.unlink()

            errors = module.verify_integrity(manifest_path, canonical_dir, published_dir)

            self.assertTrue(any("Missing manifest" in error for error in errors))

    def test_malformed_manifest_file(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path, canonical_dir, published_dir = self._write_fixture_tree(Path(tmpdir))
            manifest_path.write_text("{not-json}\n", encoding="utf-8")

            errors = module.verify_integrity(manifest_path, canonical_dir, published_dir)

            self.assertTrue(any("Failed to read manifest" in error for error in errors))


class VerifyArtifactIntegrityScriptTests(unittest.TestCase):
    """CLI tests for artifact integrity verifier."""

    def _write_fixture_tree(self, root: Path) -> tuple[Path, Path, Path]:
        return VerifyArtifactIntegrityUnitTests()._write_fixture_tree(root)

    def test_custom_path_execution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path, canonical_dir, published_dir = self._write_fixture_tree(Path(tmpdir))

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--manifest-path",
                    str(manifest_path),
                    "--canonical-dir",
                    str(canonical_dir),
                    "--published-dir",
                    str(published_dir),
                ],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("Artifact integrity verified", result.stdout)


if __name__ == "__main__":
    unittest.main()
