"""Tests for scripts/generate/publish_reference_artifacts.py."""

import json
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "generate" / "publish_reference_artifacts.py"
SOURCE_DIR = REPO_ROOT / "references" / "raw"
SCHEMAS_DIR = REPO_ROOT / "docs" / "artifacts" / "schemas"


class PublishReferenceArtifactsUnitTests(unittest.TestCase):
    """Direct unit tests for packaging functions."""

    def _import_module(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("publish_reference_artifacts", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _sample_artifacts(self):
        return {
            "server_endpoints.json": {
                "metadata": {
                    "version": "v0.19.3",
                    "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
                    "extracted_date": "2026-04-23",
                    "sources": ["references/snapshots/2026-04-19/comfyui-core-v0.19.3/server.py"],
                },
                "endpoints": [],
            },
            "js_hooks.json": {
                "metadata": {
                    "version": "v1.42.11",
                    "commit": "3dc4061d484d61cb89366de25bf5e2f8a65da4d0",
                    "extracted_date": "2026-04-19",
                    "sources": [
                        "references/snapshots/2026-04-19/comfyui-frontend-v1.42.11/src/scripts/app.ts"
                    ],
                },
                "hooks": [],
            },
            "node_api_schema.json": {
                "metadata": {
                    "version": "v0.19.3",
                    "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
                    "extracted_date": "2026-04-23",
                    "sources": [
                        "references/snapshots/2026-04-19/comfyui-core-v0.19.3/server.py"
                    ],
                },
                "object_info": {},
            },
        }

    def test_derive_version_key(self):
        module = self._import_module()
        artifacts = self._sample_artifacts()
        key = module._derive_version_key(artifacts)
        self.assertEqual(key, "core-v0.19.3_frontend-v1.42.11_2026-04-19")

    def test_derive_version_key_missing_date_uses_unknown(self):
        module = self._import_module()
        artifacts = {
            "server_endpoints.json": {"metadata": {"version": "v0.19.3"}},
            "js_hooks.json": {"metadata": {"version": "v1.42.11"}},
            "node_api_schema.json": {"metadata": {"version": "v0.19.3"}},
        }
        key = module._derive_version_key(artifacts)
        self.assertTrue(key.startswith("core-v0.19.3_frontend-v1.42.11_"))
        self.assertIn("unknown", key)

    def test_check_staleness_warns_on_old_date(self):
        module = self._import_module()
        old_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        artifacts = {
            "server_endpoints.json": {
                "metadata": {"extracted_date": old_date}
            },
            "js_hooks.json": {"metadata": {"extracted_date": old_date}},
            "node_api_schema.json": {"metadata": {"extracted_date": old_date}},
        }
        # Should not raise; function logs warnings via print
        module._check_staleness(artifacts)

    def test_check_staleness_warns_on_missing_date(self):
        module = self._import_module()
        artifacts = {
            "server_endpoints.json": {"metadata": {}},
            "js_hooks.json": {"metadata": {}},
            "node_api_schema.json": {"metadata": {}},
        }
        module._check_staleness(artifacts)

    def test_build_manifest_structure(self):
        module = self._import_module()
        artifacts = self._sample_artifacts()
        artifact_hashes = {
            name: hashlib.sha256(name.encode("utf-8")).hexdigest()
            for name in module.ARTIFACT_FILES
        }
        manifest = module.build_manifest(
            artifacts,
            "core-v0.19.3_frontend-v1.42.11_2026-04-19",
            artifact_hashes,
        )

        # published_at is intentionally omitted for idempotency
        self.assertNotIn("published_at", manifest)
        self.assertEqual(manifest["artifact_schema_version"], module.ARTIFACT_SCHEMA_VERSION)
        self.assertEqual(manifest["version_key"], "core-v0.19.3_frontend-v1.42.11_2026-04-19")
        self.assertIn("schemas", manifest)
        self.assertIn("artifacts", manifest)

        for name in ["server_endpoints.json", "js_hooks.json", "node_api_schema.json"]:
            self.assertIn(name, manifest["schemas"])
            schema_entry = manifest["schemas"][name]
            self.assertIn("schema_url", schema_entry)
            self.assertTrue(schema_entry["schema_url"].endswith(".schema.json"))
            self.assertNotIn("\\", schema_entry["schema_url"])
            self.assertFalse(schema_entry["schema_url"].startswith("/"))
            self.assertIn(name, manifest["artifacts"])
            entry = manifest["artifacts"][name]
            self.assertIn("current_url", entry)
            self.assertIn("versioned_url", entry)
            self.assertIn("sha256", entry)
            self.assertIn("version", entry)
            self.assertIn("commit", entry)
            self.assertIn("extracted_date", entry)
            self.assertIn("sources", entry)
            self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
            # URLs must use forward slashes and must not start with /
            # so they resolve correctly on GitHub Pages project sites
            self.assertNotIn("\\", entry["current_url"])
            self.assertNotIn("\\", entry["versioned_url"])
            self.assertFalse(entry["current_url"].startswith("/"))
            self.assertFalse(entry["versioned_url"].startswith("/"))

    def test_build_manifest_propagates_versions(self):
        module = self._import_module()
        artifacts = self._sample_artifacts()
        artifact_hashes = {
            name: hashlib.sha256(name.encode("utf-8")).hexdigest()
            for name in module.ARTIFACT_FILES
        }
        manifest = module.build_manifest(artifacts, "test-key", artifact_hashes)
        self.assertEqual(manifest["artifacts"]["server_endpoints.json"]["version"], "v0.19.3")
        self.assertEqual(manifest["artifacts"]["js_hooks.json"]["version"], "v1.42.11")

    def test_build_manifest_source_vs_sources(self):
        module = self._import_module()
        artifacts = self._sample_artifacts()
        artifact_hashes = {
            name: hashlib.sha256(name.encode("utf-8")).hexdigest()
            for name in module.ARTIFACT_FILES
        }
        manifest = module.build_manifest(artifacts, "test-key", artifact_hashes)
        self.assertIsInstance(manifest["artifacts"]["server_endpoints.json"]["sources"], list)
        self.assertEqual(
            manifest["artifacts"]["server_endpoints.json"]["sources"],
            ["references/snapshots/2026-04-19/comfyui-core-v0.19.3/server.py"],
        )
        self.assertIsInstance(manifest["artifacts"]["js_hooks.json"]["sources"], list)
        self.assertEqual(
            manifest["artifacts"]["js_hooks.json"]["sources"],
            ["references/snapshots/2026-04-19/comfyui-frontend-v1.42.11/src/scripts/app.ts"],
        )

    def test_build_manifest_is_deterministic_for_identical_inputs(self):
        module = self._import_module()
        artifacts = self._sample_artifacts()
        artifact_hashes = {
            name: hashlib.sha256(name.encode("utf-8")).hexdigest()
            for name in module.ARTIFACT_FILES
        }

        first = module.build_manifest(artifacts, "test-key", artifact_hashes)
        second = module.build_manifest(artifacts, "test-key", artifact_hashes)

        self.assertEqual(first, second)

    def test_site_rel_uses_forward_slashes(self):
        module = self._import_module()
        test_path = REPO_ROOT / "docs" / "artifacts" / "current" / "server_endpoints.json"
        rel = module._site_rel(test_path)
        self.assertEqual(rel, "artifacts/current/server_endpoints.json")
        self.assertNotIn("\\", rel)
        self.assertFalse(rel.startswith("/"))

    def test_generator_no_longer_uses_singular_source_fallback(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn('meta.get("source")', text)
        self.assertNotIn('meta["source"]', text)


class PublishReferenceArtifactsScriptTests(unittest.TestCase):
    """Tests that the packaging script runs and produces expected outputs."""

    def test_script_runs_and_produces_outputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            # Create minimal directory structure
            (tmp_root / "references" / "raw").mkdir(parents=True)
            (tmp_root / "docs" / "artifacts" / "current").mkdir(parents=True)
            (tmp_root / "docs" / "artifacts" / "schemas").mkdir(parents=True)
            (tmp_root / "scripts" / "generate").mkdir(parents=True)

            # Copy generator script
            shutil.copy(SCRIPT, tmp_root / "scripts" / "generate" / "publish_reference_artifacts.py")
            for schema_path in SCHEMAS_DIR.glob("*.schema.json"):
                shutil.copy(schema_path, tmp_root / "docs" / "artifacts" / "schemas" / schema_path.name)

            # Write minimal artifact JSONs
            artifacts = {
                "server_endpoints.json": {
                    "metadata": {
                        "version": "v0.19.3",
                        "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
                        "extracted_date": "2026-04-23",
                        "sources": ["snapshots/server.py"],
                    },
                    "endpoints": [],
                },
                "js_hooks.json": {
                    "metadata": {
                        "version": "v1.42.11",
                        "commit": "3dc4061d484d61cb89366de25bf5e2f8a65da4d0",
                        "extracted_date": "2026-04-19",
                        "sources": ["snapshots/app.ts"],
                    },
                    "hooks": [],
                },
                "node_api_schema.json": {
                    "metadata": {
                        "version": "v0.19.3",
                        "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
                        "extracted_date": "2026-04-23",
                        "sources": ["snapshots/server.py"],
                    },
                    "object_info": {},
                },
            }
            for name, data in artifacts.items():
                (tmp_root / "references" / "raw" / name).write_text(
                    json.dumps(data), encoding="utf-8"
                )

            # Run script
            result = subprocess.run(
                [sys.executable, str(tmp_root / "scripts" / "generate" / "publish_reference_artifacts.py")],
                capture_output=True,
                text=True,
                cwd=str(tmp_root),
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

            # Verify current copies
            for name in artifacts:
                current_path = tmp_root / "docs" / "artifacts" / "current" / name
                self.assertTrue(current_path.exists(), f"Missing current copy: {name}")
                loaded = json.loads(current_path.read_text(encoding="utf-8"))
                self.assertEqual(loaded["metadata"]["version"], artifacts[name]["metadata"]["version"])

            # Verify versioned copies
            versioned_dir = tmp_root / "docs" / "artifacts" / "versions" / "core-v0.19.3_frontend-v1.42.11_2026-04-19"
            for name in artifacts:
                versioned_path = versioned_dir / name
                self.assertTrue(versioned_path.exists(), f"Missing versioned copy: {name}")

            # Verify manifest
            manifest_path = tmp_root / "docs" / "artifacts" / "manifest.json"
            self.assertTrue(manifest_path.exists())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["artifact_schema_version"], "1.0.0")
            self.assertIn("schemas", manifest)
            self.assertIn("artifacts", manifest)
            self.assertIn("server_endpoints.json", manifest["artifacts"])
            self.assertIn("server_endpoints.json", manifest["schemas"])
            self.assertIn("current_url", manifest["artifacts"]["server_endpoints.json"])
            self.assertIn("versioned_url", manifest["artifacts"]["server_endpoints.json"])
            self.assertIn("sha256", manifest["artifacts"]["server_endpoints.json"])
            self.assertEqual(
                manifest["schemas"]["server_endpoints.json"]["schema_url"],
                "artifacts/schemas/server_endpoints.schema.json",
            )
            for name in artifacts:
                published_path = tmp_root / "docs" / "artifacts" / "current" / name
                expected_hash = hashlib.sha256(published_path.read_bytes()).hexdigest()
                self.assertEqual(manifest["artifacts"][name]["sha256"], expected_hash)
            self.assertTrue(
                all(isinstance(entry.get("sources", []), list) for entry in manifest["artifacts"].values())
            )

    def test_script_fails_when_artifact_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            (tmp_root / "references" / "raw").mkdir(parents=True)
            (tmp_root / "docs" / "artifacts").mkdir(parents=True)
            (tmp_root / "scripts" / "generate").mkdir(parents=True)
            shutil.copy(SCRIPT, tmp_root / "scripts" / "generate" / "publish_reference_artifacts.py")

            # Only write one artifact, omitting the others
            data = {"metadata": {"version": "v0.19.3", "extracted_date": "2026-04-23"}, "endpoints": []}
            (tmp_root / "references" / "raw" / "server_endpoints.json").write_text(
                json.dumps(data), encoding="utf-8"
            )

            result = subprocess.run(
                [sys.executable, str(tmp_root / "scripts" / "generate" / "publish_reference_artifacts.py")],
                capture_output=True,
                text=True,
                cwd=str(tmp_root),
            )
            self.assertNotEqual(result.returncode, 0)

    def test_script_fails_when_schema_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            (tmp_root / "references" / "raw").mkdir(parents=True)
            (tmp_root / "docs" / "artifacts").mkdir(parents=True)
            (tmp_root / "scripts" / "generate").mkdir(parents=True)
            shutil.copy(SCRIPT, tmp_root / "scripts" / "generate" / "publish_reference_artifacts.py")

            artifacts = {
                "server_endpoints.json": {
                    "metadata": {
                        "version": "v0.19.3",
                        "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
                        "extracted_date": "2026-04-23",
                        "sources": ["snapshots/server.py"],
                    },
                    "endpoints": [],
                },
                "js_hooks.json": {
                    "metadata": {
                        "version": "v1.42.11",
                        "commit": "3dc4061d484d61cb89366de25bf5e2f8a65da4d0",
                        "extracted_date": "2026-04-19",
                        "sources": ["snapshots/app.ts"],
                    },
                    "hooks": [],
                },
                "node_api_schema.json": {
                    "metadata": {
                        "version": "v0.19.3",
                        "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
                        "extracted_date": "2026-04-23",
                        "sources": ["snapshots/server.py"],
                    },
                    "object_info": {},
                },
            }
            for name, data in artifacts.items():
                (tmp_root / "references" / "raw" / name).write_text(
                    json.dumps(data), encoding="utf-8"
                )

            result = subprocess.run(
                [sys.executable, str(tmp_root / "scripts" / "generate" / "publish_reference_artifacts.py")],
                capture_output=True,
                text=True,
                cwd=str(tmp_root),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Published schema file not found", result.stdout)


if __name__ == "__main__":
    unittest.main()
