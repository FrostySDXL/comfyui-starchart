"""Fixture-backed integration tests for extractor entrypoints."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.unit.helpers.extractor_test_utils import REPO_ROOT, call_main, load_module

FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "extractors"


def _load_validate_schema():
    return load_module("validate_schema", REPO_ROOT / "scripts" / "verify" / "validate_schema.py")


class ExtractorIntegrationTests(unittest.TestCase):
    def test_parse_server_main_handles_fixture_file(self):
        module = load_module("parse_server", REPO_ROOT / "scripts" / "extract" / "parse_server.py")
        validate_schema = _load_validate_schema()

        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "server_endpoints.json"
            exit_code, _stdout, stderr = call_main(
                module,
                str(FIXTURE_DIR / "server_fixture.py"),
                "--version",
                "v-fixture",
                "--commit",
                "abc123",
                "--output",
                str(output_path),
            )

            self.assertEqual(exit_code, 0, msg=stderr)
            data = json.loads(output_path.read_text(encoding="utf-8"))

        errors = validate_schema.validate_top_level(
            data, validate_schema.SCHEMAS["server_endpoints.json"], "server_endpoints.json"
        )
        errors.extend(validate_schema.validate_metadata(data, "server_endpoints.json"))
        errors.extend(validate_schema.validate_coverage(data, "server_endpoints.json"))
        errors.extend(validate_schema.validate_endpoints(data, "server_endpoints.json"))
        self.assertEqual(errors, [])

        endpoint_map = {endpoint["route"]: endpoint for endpoint in data["endpoints"]}
        self.assertGreaterEqual(len(endpoint_map), 5)
        self.assertEqual(endpoint_map["/ws"]["returns"]["kind"], "websocket")
        self.assertEqual(endpoint_map["/api/jobs"]["returns"]["kind"], "json")
        self.assertIn(
            "queue_running",
            {field["name"] for field in endpoint_map["/queue"]["returns"]["fields"]},
        )
        self.assertIn(
            ("job_id", "path"),
            {(p["name"], p["location"]) for p in endpoint_map["/api/jobs/{job_id}"]["parameters"]},
        )
        self.assertIn(
            ("prompt", "json"),
            {(p["name"], p["location"]) for p in endpoint_map["/prompt"]["parameters"]},
        )
        self.assertIn(
            "prompt_id",
            {field["name"] for field in endpoint_map["/prompt"]["returns"]["fields"]},
        )

    def test_parse_hooks_main_handles_fixture_files(self):
        module = load_module("parse_hooks", REPO_ROOT / "scripts" / "extract" / "parse_hooks.py")
        validate_schema = _load_validate_schema()

        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "js_hooks.json"
            exit_code, _stdout, stderr = call_main(
                module,
                str(FIXTURE_DIR / "comfy_fixture.ts"),
                str(FIXTURE_DIR / "app_fixture.ts"),
                str(FIXTURE_DIR / "litegraph_service_fixture.ts"),
                "--version",
                "v-fixture",
                "--commit",
                "abc123",
                "--output",
                str(output_path),
            )

            self.assertEqual(exit_code, 0, msg=stderr)
            data = json.loads(output_path.read_text(encoding="utf-8"))

        errors = validate_schema.validate_top_level(
            data, validate_schema.SCHEMAS["js_hooks.json"], "js_hooks.json"
        )
        errors.extend(validate_schema.validate_metadata(data, "js_hooks.json"))
        errors.extend(validate_schema.validate_coverage(data, "js_hooks.json"))
        errors.extend(validate_schema.validate_hooks(data, "js_hooks.json"))
        self.assertEqual(errors, [])

        hook_map = {hook["name"]: hook for hook in data["hooks"]}
        self.assertGreaterEqual(len(hook_map), 4)
        self.assertEqual(hook_map["setup"]["return_type"], "Promise<void> | void")
        self.assertEqual(hook_map["beforeRegisterNodeDef"]["arguments"][0]["name"], "nodeType")
        self.assertEqual(hook_map["beforeRegisterNodeDef"]["return_type"], "Promise<void> | void")
        self.assertIn("async", hook_map["setup"]["invocation_style"])
        self.assertIn("sync", hook_map["nodeCreated"]["invocation_style"])
        self.assertIn("nodeCreated", hook_map)
        self.assertIn("init", hook_map)

    def test_parse_node_api_schema_main_handles_fixture_files(self):
        module = load_module(
            "parse_node_api_schema", REPO_ROOT / "scripts" / "extract" / "parse_node_api_schema.py"
        )
        validate_schema = _load_validate_schema()

        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "node_api_schema.json"
            exit_code, _stdout, stderr = call_main(
                module,
                str(FIXTURE_DIR / "node_server_fixture.py"),
                str(FIXTURE_DIR / "_io_fixture.py"),
                str(FIXTURE_DIR / "basic_types_fixture.py"),
                "--version",
                "v-fixture",
                "--commit",
                "abc123",
                "--output",
                str(output_path),
            )

            self.assertEqual(exit_code, 0, msg=stderr)
            data = json.loads(output_path.read_text(encoding="utf-8"))

        errors = validate_schema.validate_top_level(
            data,
            validate_schema.SCHEMAS["node_api_schema.json"],
            "node_api_schema.json",
        )
        errors.extend(validate_schema.validate_metadata(data, "node_api_schema.json"))
        errors.extend(validate_schema.validate_coverage(data, "node_api_schema.json"))
        errors.extend(validate_schema.validate_io_types(data, "node_api_schema.json"))
        errors.extend(validate_schema.validate_typed_input_shapes(data, "node_api_schema.json"))
        self.assertEqual(errors, [])

        io_types = {entry["io_type"]: entry for entry in data["io_types"]}
        self.assertIn("STRING", io_types)
        self.assertEqual(io_types["BOOLEAN"]["type_hint"], "bool")
        self.assertEqual(io_types["LOAD_3D_ANIMATION"]["type_hint"], "Model3DDict")
        self.assertIn("AudioInput", data["typed_input_shapes"])
        self.assertEqual(
            data["typed_input_shapes"]["AudioInput"]["fields"]["sample_rate"]["type"],
            "int",
        )
        self.assertIn("input", data["object_info_fields"])
        self.assertIn("display_name", data["object_info_fields"])


if __name__ == "__main__":
    unittest.main()
