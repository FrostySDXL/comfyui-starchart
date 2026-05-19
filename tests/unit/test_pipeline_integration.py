"""In-process integration test for the extract -> generate -> publish -> verify pipeline."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.unit.helpers.extractor_test_utils import REPO_ROOT, call_main, load_module

FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "extractors"
SCHEMAS_DIR = REPO_ROOT / "public" / "artifacts" / "schemas"


def _load_validate_schema():
    return load_module("validate_schema", REPO_ROOT / "scripts" / "verify" / "validate_schema.py")


def _validate_server_endpoints(validate_schema, data: dict) -> list[str]:
    errors = validate_schema.validate_top_level(
        data, validate_schema.SCHEMAS["server_endpoints.json"], "server_endpoints.json"
    )
    errors.extend(validate_schema.validate_metadata(data, "server_endpoints.json"))
    errors.extend(validate_schema.validate_coverage(data, "server_endpoints.json"))
    errors.extend(validate_schema.validate_endpoints(data, "server_endpoints.json"))
    return errors


def _validate_js_hooks(validate_schema, data: dict) -> list[str]:
    errors = validate_schema.validate_top_level(
        data, validate_schema.SCHEMAS["js_hooks.json"], "js_hooks.json"
    )
    errors.extend(validate_schema.validate_metadata(data, "js_hooks.json"))
    errors.extend(validate_schema.validate_coverage(data, "js_hooks.json"))
    errors.extend(validate_schema.validate_hooks(data, "js_hooks.json"))
    return errors


def _validate_node_api_schema(validate_schema, data: dict) -> list[str]:
    errors = validate_schema.validate_top_level(
        data,
        validate_schema.SCHEMAS["node_api_schema.json"],
        "node_api_schema.json",
    )
    errors.extend(validate_schema.validate_metadata(data, "node_api_schema.json"))
    errors.extend(validate_schema.validate_coverage(data, "node_api_schema.json"))
    errors.extend(validate_schema.validate_io_types(data, "node_api_schema.json"))
    errors.extend(validate_schema.validate_typed_input_shapes(data, "node_api_schema.json"))
    return errors


class PipelineIntegrationTests(unittest.TestCase):
    def _copy_published_schemas(self, root: Path) -> None:
        target = root / "public" / "artifacts" / "schemas"
        target.mkdir(parents=True, exist_ok=True)
        for schema_path in SCHEMAS_DIR.glob("*.schema.json"):
            shutil.copy(schema_path, target / schema_path.name)

    def _patch_publish_module_paths(self, module, root: Path) -> None:
        overrides = {
            "REPO_ROOT": root,
            "SOURCE_DIR": root / "references" / "raw",
            "OUTPUT_ROOT": root / "public" / "artifacts",
            "CURRENT_DIR": root / "public" / "artifacts" / "current",
            "VERSIONS_DIR": root / "public" / "artifacts" / "versions",
            "SCHEMAS_DIR": root / "public" / "artifacts" / "schemas",
        }
        for name, value in overrides.items():
            original = getattr(module, name)
            self.addCleanup(setattr, module, name, original)
            setattr(module, name, value)

    def test_fixture_pipeline_runs_extract_generate_publish_verify_in_process(self):
        parse_server = load_module(
            "parse_server", REPO_ROOT / "scripts" / "extract" / "parse_server.py"
        )
        parse_hooks = load_module(
            "parse_hooks", REPO_ROOT / "scripts" / "extract" / "parse_hooks.py"
        )
        parse_node_api_schema = load_module(
            "parse_node_api_schema",
            REPO_ROOT / "scripts" / "extract" / "parse_node_api_schema.py",
        )
        md_from_json = load_module(
            "md_from_json", REPO_ROOT / "scripts" / "generate" / "md_from_json.py"
        )
        publish_reference_artifacts = load_module(
            "publish_reference_artifacts",
            REPO_ROOT / "scripts" / "generate" / "publish_reference_artifacts.py",
        )
        validate_schema = _load_validate_schema()
        verify_artifact_integrity = load_module(
            "verify_artifact_integrity",
            REPO_ROOT / "scripts" / "verify" / "verify_artifact_integrity.py",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            raw_dir = root / "references" / "raw"
            docs_ref_dir = root / "src" / "content" / "docs" / "reference"
            raw_dir.mkdir(parents=True, exist_ok=True)
            docs_ref_dir.mkdir(parents=True, exist_ok=True)
            self._copy_published_schemas(root)

            exit_code, _stdout, stderr = call_main(
                parse_server,
                str(FIXTURE_DIR / "server_fixture.py"),
                "--version",
                "v-fixture",
                "--commit",
                "abc123",
                "--output",
                str(raw_dir / "server_endpoints.json"),
            )
            self.assertEqual(exit_code, 0, msg=stderr)

            exit_code, _stdout, stderr = call_main(
                parse_hooks,
                str(FIXTURE_DIR / "comfy_fixture.ts"),
                str(FIXTURE_DIR / "app_fixture.ts"),
                str(FIXTURE_DIR / "litegraph_service_fixture.ts"),
                "--version",
                "v-fixture",
                "--commit",
                "abc123",
                "--output",
                str(raw_dir / "js_hooks.json"),
            )
            self.assertEqual(exit_code, 0, msg=stderr)

            exit_code, _stdout, stderr = call_main(
                parse_node_api_schema,
                str(FIXTURE_DIR / "node_server_fixture.py"),
                str(FIXTURE_DIR / "_io_fixture.py"),
                str(FIXTURE_DIR / "basic_types_fixture.py"),
                "--version",
                "v-fixture",
                "--commit",
                "abc123",
                "--output",
                str(raw_dir / "node_api_schema.json"),
            )
            self.assertEqual(exit_code, 0, msg=stderr)

            server_data = json.loads(
                (raw_dir / "server_endpoints.json").read_text(encoding="utf-8")
            )
            hooks_data = json.loads((raw_dir / "js_hooks.json").read_text(encoding="utf-8"))
            schema_data = json.loads((raw_dir / "node_api_schema.json").read_text(encoding="utf-8"))

            self.assertEqual(_validate_server_endpoints(validate_schema, server_data), [])
            self.assertEqual(_validate_js_hooks(validate_schema, hooks_data), [])
            self.assertEqual(_validate_node_api_schema(validate_schema, schema_data), [])

            exit_code, _stdout, stderr = call_main(
                md_from_json,
                "--input",
                str(raw_dir / "server_endpoints.json"),
                "--output",
                str(docs_ref_dir / "server-py-summary.md"),
            )
            self.assertEqual(exit_code, 0, msg=stderr)

            generated_page = (docs_ref_dir / "server-py-summary.md").read_text(encoding="utf-8")
            self.assertIn("bounded generated inventory", generated_page)
            self.assertIn("[API Endpoints](../api/endpoints.md)", generated_page)

            self._patch_publish_module_paths(publish_reference_artifacts, root)
            self.assertEqual(publish_reference_artifacts.main(), 0)

            manifest_path = root / "public" / "artifacts" / "manifest.json"
            current_dir = root / "public" / "artifacts" / "current"
            self.assertTrue(manifest_path.exists())
            self.assertTrue((current_dir / "server_endpoints.json").exists())
            self.assertTrue((current_dir / "js_hooks.json").exists())
            self.assertTrue((current_dir / "node_api_schema.json").exists())

            integrity_errors = verify_artifact_integrity.verify_integrity(
                manifest_path, raw_dir, current_dir
            )
            self.assertEqual(integrity_errors, [])


if __name__ == "__main__":
    unittest.main()
