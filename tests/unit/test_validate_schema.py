"""Tests for scripts/verify/validate_schema.py."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "validate_schema.py"


class ValidateSchemaUnitTests(unittest.TestCase):
    """Direct unit tests for validation functions."""

    def _import_module(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("validate_schema", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_valid_server_endpoints_pass(self):
        module = self._import_module()
        data = {
            "metadata": {
                "source": "references/snapshots/server.py",
                "extracted_date": "2026-04-22",
                "version": "v0.19.3",
                "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
            },
            "endpoints": [
                {
                    "route": "/prompt",
                    "method": "POST",
                    "description": "Queue a prompt.",
                    "parameters": [],
                    "returns": {
                        "kind": "json",
                        "summary": "Prompt queued with ID and any node errors.",
                        "status_codes": [200, 400],
                        "fields": [
                            {"name": "prompt_id", "type_hint": "str", "description": "UUID of the queued prompt"},
                            {"name": "number", "type_hint": "int"},
                            {"name": "node_errors", "type_hint": "dict"},
                        ],
                        "notes": ["Returns 400 for validation failures."],
                    },
                },
                {
                    "route": "/ws",
                    "method": "GET",
                    "description": "WebSocket stream.",
                    "parameters": [],
                    "returns": {
                        "kind": "websocket",
                        "summary": "Upgraded WebSocket connection.",
                        "status_codes": [101],
                        "fields": [],
                        "notes": [],
                    },
                },
            ],
        }
        errors = module.validate_endpoints(data, "server_endpoints.json")
        self.assertEqual(errors, [])

    def test_malformed_returns_missing_kind_fails(self):
        module = self._import_module()
        data = {
            "metadata": {
                "source": "references/snapshots/server.py",
                "extracted_date": "2026-04-22",
                "version": "v0.19.3",
                "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
            },
            "endpoints": [
                {
                    "route": "/prompt",
                    "method": "POST",
                    "description": "Queue a prompt.",
                    "parameters": [],
                    "returns": {
                        "summary": "missing kind",
                        "status_codes": [],
                        "fields": [],
                        "notes": [],
                    },
                }
            ],
        }
        errors = module.validate_endpoints(data, "server_endpoints.json")
        self.assertTrue(any("missing required key 'kind'" in e for e in errors))

    def test_malformed_returns_status_codes_not_int_fails(self):
        module = self._import_module()
        data = {
            "metadata": {
                "source": "references/snapshots/server.py",
                "extracted_date": "2026-04-22",
                "version": "v0.19.3",
                "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
            },
            "endpoints": [
                {
                    "route": "/prompt",
                    "method": "POST",
                    "description": "Queue a prompt.",
                    "parameters": [],
                    "returns": {
                        "kind": "json",
                        "summary": "ok",
                        "status_codes": [200, "400"],
                        "fields": [],
                        "notes": [],
                    },
                }
            ],
        }
        errors = module.validate_endpoints(data, "server_endpoints.json")
        self.assertTrue(any("status_codes[1] expected int" in e for e in errors))

    def test_malformed_returns_field_missing_name_fails(self):
        module = self._import_module()
        data = {
            "metadata": {
                "source": "references/snapshots/server.py",
                "extracted_date": "2026-04-22",
                "version": "v0.19.3",
                "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
            },
            "endpoints": [
                {
                    "route": "/prompt",
                    "method": "POST",
                    "description": "Queue a prompt.",
                    "parameters": [],
                    "returns": {
                        "kind": "json",
                        "summary": "ok",
                        "status_codes": [200],
                        "fields": [{"type_hint": "str"}],
                        "notes": [],
                    },
                }
            ],
        }
        errors = module.validate_endpoints(data, "server_endpoints.json")
        self.assertTrue(any("fields[0] missing required key 'name'" in e for e in errors))

    def test_legacy_string_returns_are_rejected(self):
        """String returns are no longer accepted; structured dict is required."""
        module = self._import_module()
        data = {
            "metadata": {
                "source": "references/snapshots/server.py",
                "extracted_date": "2026-04-22",
                "version": "v0.19.3",
                "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
            },
            "endpoints": [
                {
                    "route": "/prompt",
                    "method": "POST",
                    "description": "Queue a prompt.",
                    "parameters": [],
                    "returns": "TODO",
                }
            ],
        }
        errors = module.validate_endpoints(data, "server_endpoints.json")
        self.assertTrue(any("expected dict" in e for e in errors))

    def test_valid_node_api_schema_passes(self):
        module = self._import_module()
        data = {
            "metadata": {
                "sources": ["references/snapshots/server.py"],
                "extracted_date": "2026-04-22",
                "version": "v0.19.3",
                "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
            },
            "object_info_fields": ["input", "output"],
            "io_types": [
                {
                    "io_type": "BOOLEAN",
                    "class_name": "Boolean",
                    "input_class": "WidgetInput",
                    "input_parameters": ["default"],
                }
            ],
            "basic_input_shapes": {"ImageInput": "An image tensor."},
        }
        errors = module.validate_top_level(data, module.SCHEMAS["node_api_schema.json"], "node_api_schema.json")
        errors.extend(module.validate_metadata(data, "node_api_schema.json"))
        errors.extend(module.validate_io_types(data, "node_api_schema.json"))
        self.assertEqual(errors, [])

    def test_malformed_io_type_missing_class_name_fails(self):
        module = self._import_module()
        data = {
            "metadata": {
                "sources": ["references/snapshots/_io.py"],
                "extracted_date": "2026-04-22",
                "version": "v0.19.3",
                "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
            },
            "object_info_fields": [],
            "io_types": [
                {
                    "io_type": "BOOLEAN",
                    "input_class": "WidgetInput",
                    "input_parameters": [],
                }
            ],
            "basic_input_shapes": {},
        }
        errors = module.validate_io_types(data, "node_api_schema.json")
        self.assertTrue(any("io_types[0] missing required key 'class_name'" in e for e in errors))


class ValidateSchemaScriptTests(unittest.TestCase):
    """Tests that the validation script runs successfully on the repo."""

    def test_script_runs_and_passes(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("pass schema validation", result.stdout)


if __name__ == "__main__":
    unittest.main()
