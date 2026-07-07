"""Tests for scripts/verify/versioned_artifact_completeness.py."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from scripts.common.json_utils import compute_textual_json_sha256

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "versioned_artifact_completeness.py"
FIXTURE_ARTIFACT_SHA256 = "af47610019f4628607dbf81095ad2c0e4e15c9e6a37e02e49300ab3b80326fda"


def _load_module():
    spec = importlib.util.spec_from_file_location("versioned_artifact_completeness", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_manifest(root: Path, version_key: str = "current") -> Path:
    manifest_path = root / "public" / "artifacts" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    artifacts = {
        name: {"sha256": FIXTURE_ARTIFACT_SHA256}
        for name in (
            "server_endpoints.json",
            "js_hooks.json",
            "node_api_schema.json",
            "websocket_events.json",
        )
    }
    manifest_path.write_text(
        json.dumps(
            {
                "artifact_schema_version": "1.0.0",
                "version_key": version_key,
                "artifacts": artifacts,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _write_manifest_hashes(manifest_path: Path, artifact_dir: Path) -> None:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name in data["artifacts"]:
        data["artifacts"][name]["sha256"] = compute_textual_json_sha256(artifact_dir / name)
    manifest_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_schema_dir(root: Path) -> Path:
    schema_dir = root / "public" / "artifacts" / "schemas"
    schema_dir.mkdir(parents=True)
    for name in (
        "server_endpoints.schema.json",
        "js_hooks.schema.json",
        "node_api_schema.schema.json",
        "websocket_events.schema.json",
    ):
        (schema_dir / name).write_text(
            json.dumps({"type": "object", "required": ["metadata"]}, indent=2) + "\n",
            encoding="utf-8",
        )
    return schema_dir


def _write_artifacts(directory: Path, names: tuple[str, ...]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name in names:
        (directory / name).write_text('{"metadata": {}}\n', encoding="utf-8")


class TestVersionedArtifactCompletenessNegative(unittest.TestCase):
    """Required negative classification tests for versioned artifacts."""

    def test_missing_required_artifact_in_current_version(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path = _write_manifest(root)
            schema_dir = _write_schema_dir(root)
            versions_dir = root / "public" / "artifacts" / "versions"
            _write_artifacts(
                versions_dir / "current",
                tuple(
                    name for name in module.REQUIRED_ARTIFACTS if name != "websocket_events.json"
                ),
            )

            result = module.evaluate_versioned_artifacts(
                manifest_path, versions_dir, {}, schema_dir
            )

        self.assertTrue(any("current version is missing" in error for error in result.errors))

    def test_unexpected_file_in_current_version_directory(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path = _write_manifest(root)
            schema_dir = _write_schema_dir(root)
            versions_dir = root / "public" / "artifacts" / "versions"
            _write_artifacts(versions_dir / "current", module.REQUIRED_ARTIFACTS)
            (versions_dir / "current" / "extra_artifact.json").write_text("{}\n", encoding="utf-8")

            result = module.evaluate_versioned_artifacts(
                manifest_path, versions_dir, {}, schema_dir
            )

        current = result.by_version["current"]
        self.assertIn("extra_artifact.json", current.unexpected_artifacts)
        self.assertTrue(any("unexpected artifacts" in warning for warning in result.warnings))

    def test_empty_version_directory_classification(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path = _write_manifest(root, version_key="non-empty-current")
            schema_dir = _write_schema_dir(root)
            versions_dir = root / "public" / "artifacts" / "versions"
            (versions_dir / "empty-old").mkdir(parents=True)
            _write_artifacts(versions_dir / "non-empty-current", module.REQUIRED_ARTIFACTS)

            result = module.evaluate_versioned_artifacts(
                manifest_path, versions_dir, {}, schema_dir
            )

        empty = result.by_version["empty-old"]
        self.assertEqual(empty.classification, "empty")
        self.assertTrue(any("empty version directory" in warning for warning in result.warnings))
        self.assertNotEqual(empty.classification, "current-required-complete")

    def test_legacy_pre_websocket_events_exception_respected(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path = _write_manifest(root, version_key="current")
            schema_dir = _write_schema_dir(root)
            versions_dir = root / "public" / "artifacts" / "versions"
            legacy_key = "legacy"
            _write_artifacts(versions_dir / "current", module.REQUIRED_ARTIFACTS)
            _write_artifacts(
                versions_dir / legacy_key,
                tuple(
                    name for name in module.REQUIRED_ARTIFACTS if name != "websocket_events.json"
                ),
            )

            result = module.evaluate_versioned_artifacts(
                manifest_path,
                versions_dir,
                {legacy_key: "legacy-pre-websocket-events"},
                schema_dir,
            )

        legacy = result.by_version[legacy_key]
        self.assertEqual(legacy.classification, "legacy-pre-websocket-events")
        self.assertFalse(any(legacy_key in warning for warning in result.warnings))

    def test_classification_output_and_exceptions_are_stable(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path = _write_manifest(root, version_key="current")
            schema_dir = _write_schema_dir(root)
            versions_dir = root / "public" / "artifacts" / "versions"
            _write_artifacts(versions_dir / "current", module.REQUIRED_ARTIFACTS)
            _write_artifacts(versions_dir / "legacy", module.REQUIRED_ARTIFACTS[:3])
            exceptions = {"legacy": "legacy-pre-websocket-events"}

            first = module.evaluate_versioned_artifacts(
                manifest_path, versions_dir, exceptions, schema_dir
            )
            second = module.evaluate_versioned_artifacts(
                manifest_path, versions_dir, exceptions, schema_dir
            )

        self.assertEqual(module.format_report(first), module.format_report(second))
        self.assertEqual(module.sorted_retention_exceptions(exceptions), exceptions)

    def test_versioned_artifact_invalid_json_is_an_error(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path = _write_manifest(root, version_key="current")
            schema_dir = _write_schema_dir(root)
            versions_dir = root / "public" / "artifacts" / "versions"
            _write_artifacts(versions_dir / "current", module.REQUIRED_ARTIFACTS)
            (versions_dir / "current" / "server_endpoints.json").write_text(
                "{not-json}\n", encoding="utf-8"
            )

            result = module.evaluate_versioned_artifacts(
                manifest_path, versions_dir, {}, schema_dir
            )

        self.assertTrue(any("invalid JSON" in error for error in result.errors))

    def test_versioned_artifact_schema_violation_is_an_error(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path = _write_manifest(root, version_key="current")
            schema_dir = _write_schema_dir(root)
            versions_dir = root / "public" / "artifacts" / "versions"
            _write_artifacts(versions_dir / "current", module.REQUIRED_ARTIFACTS)
            (versions_dir / "current" / "node_api_schema.json").write_text("{}\n", encoding="utf-8")

            result = module.evaluate_versioned_artifacts(
                manifest_path, versions_dir, {}, schema_dir
            )

        self.assertTrue(any("published schema violation" in error for error in result.errors))

    def test_retained_complete_hash_mismatch_is_an_error(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path = _write_manifest(root, version_key="current")
            schema_dir = _write_schema_dir(root)
            versions_dir = root / "public" / "artifacts" / "versions"
            retained_key = "retained"
            _write_artifacts(versions_dir / "current", module.REQUIRED_ARTIFACTS)
            _write_artifacts(versions_dir / retained_key, module.REQUIRED_ARTIFACTS)
            retained_hashes = {
                retained_key: {
                    name: compute_textual_json_sha256(versions_dir / retained_key / name)
                    for name in module.REQUIRED_ARTIFACTS
                }
            }
            (versions_dir / retained_key / "server_endpoints.json").write_text(
                '{"metadata": {}, "changed": true}\n', encoding="utf-8"
            )

            result = module.evaluate_versioned_artifacts(
                manifest_path,
                versions_dir,
                {},
                schema_dir,
                retained_hashes,
            )

        self.assertTrue(any("sha256 mismatch" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
