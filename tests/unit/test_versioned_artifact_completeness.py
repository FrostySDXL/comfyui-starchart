"""Tests for scripts/verify/versioned_artifact_completeness.py."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "versioned_artifact_completeness.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("versioned_artifact_completeness", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_manifest(root: Path, version_key: str = "current") -> Path:
    manifest_path = root / "public" / "artifacts" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "artifact_schema_version": "1.0.0",
                "version_key": version_key,
                "artifacts": {},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _write_artifacts(directory: Path, names: tuple[str, ...]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name in names:
        (directory / name).write_text("{}\n", encoding="utf-8")


class TestVersionedArtifactCompletenessNegative(unittest.TestCase):
    """Required negative classification tests for versioned artifacts."""

    def test_missing_required_artifact_in_current_version(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path = _write_manifest(root)
            versions_dir = root / "public" / "artifacts" / "versions"
            _write_artifacts(
                versions_dir / "current",
                tuple(
                    name for name in module.REQUIRED_ARTIFACTS if name != "websocket_events.json"
                ),
            )

            result = module.evaluate_versioned_artifacts(manifest_path, versions_dir, {})

        self.assertTrue(any("current version is missing" in error for error in result.errors))

    def test_unexpected_file_in_current_version_directory(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path = _write_manifest(root)
            versions_dir = root / "public" / "artifacts" / "versions"
            _write_artifacts(versions_dir / "current", module.REQUIRED_ARTIFACTS)
            (versions_dir / "current" / "extra_artifact.json").write_text("{}\n", encoding="utf-8")

            result = module.evaluate_versioned_artifacts(manifest_path, versions_dir, {})

        current = result.by_version["current"]
        self.assertIn("extra_artifact.json", current.unexpected_artifacts)
        self.assertTrue(any("unexpected artifacts" in warning for warning in result.warnings))

    def test_empty_version_directory_classification(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path = _write_manifest(root, version_key="non-empty-current")
            versions_dir = root / "public" / "artifacts" / "versions"
            (versions_dir / "empty-old").mkdir(parents=True)
            _write_artifacts(versions_dir / "non-empty-current", module.REQUIRED_ARTIFACTS)

            result = module.evaluate_versioned_artifacts(manifest_path, versions_dir, {})

        empty = result.by_version["empty-old"]
        self.assertEqual(empty.classification, "empty")
        self.assertTrue(any("empty version directory" in warning for warning in result.warnings))
        self.assertNotEqual(empty.classification, "current-required-complete")

    def test_legacy_pre_websocket_events_exception_respected(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path = _write_manifest(root, version_key="current")
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
            )

        legacy = result.by_version[legacy_key]
        self.assertEqual(legacy.classification, "legacy-pre-websocket-events")
        self.assertFalse(any(legacy_key in warning for warning in result.warnings))

    def test_classification_output_and_exceptions_are_stable(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path = _write_manifest(root, version_key="current")
            versions_dir = root / "public" / "artifacts" / "versions"
            _write_artifacts(versions_dir / "current", module.REQUIRED_ARTIFACTS)
            _write_artifacts(versions_dir / "legacy", module.REQUIRED_ARTIFACTS[:3])
            exceptions = {"legacy": "legacy-pre-websocket-events"}

            first = module.evaluate_versioned_artifacts(manifest_path, versions_dir, exceptions)
            second = module.evaluate_versioned_artifacts(manifest_path, versions_dir, exceptions)

        self.assertEqual(module.format_report(first), module.format_report(second))
        self.assertEqual(module.sorted_retention_exceptions(exceptions), exceptions)


if __name__ == "__main__":
    unittest.main()
