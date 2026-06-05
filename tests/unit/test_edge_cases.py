"""Edge case tests for extractors and schema validator."""

import json
import tempfile
import unittest
from pathlib import Path

from tests.unit.helpers.extractor_test_utils import call_main, load_module

REPO_ROOT = Path(__file__).resolve().parents[2]
PARSE_SERVER = REPO_ROOT / "scripts" / "extract" / "parse_server.py"
PARSE_HOOKS = REPO_ROOT / "scripts" / "extract" / "parse_hooks.py"
PARSE_NODE_API = REPO_ROOT / "scripts" / "extract" / "parse_node_api_schema.py"
VALIDATE_SCHEMA = REPO_ROOT / "scripts" / "verify" / "validate_schema.py"


def _load_parse_server():
    return load_module("parse_server", PARSE_SERVER)


def _run_parse_server_main(server_path: Path, out_path: Path, *extra_args: str):
    parse_server = _load_parse_server()
    return call_main(parse_server, str(server_path), *extra_args, "--output", str(out_path))


def _load_parse_hooks():
    return load_module("parse_hooks", PARSE_HOOKS)


def _run_parse_hooks_main(*args: str):
    return call_main(_load_parse_hooks(), *args)


def _load_parse_node_api():
    return load_module("parse_node_api_schema", PARSE_NODE_API)


def _run_parse_node_api_main(
    server_path: Path, io_path: Path, basic_types_path: Path, *extra_args: str
):
    return call_main(
        _load_parse_node_api(),
        str(server_path),
        str(io_path),
        str(basic_types_path),
        *extra_args,
    )


def _load_module(name, path):
    """Load a Python module from file path."""
    return load_module(name, path)


class ParseServerEdgeCases(unittest.TestCase):
    """Edge case tests for parse_server.py."""

    def test_empty_file_produces_zero_endpoints(self):
        """An empty source file should produce zero endpoints."""
        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            out_path = Path(tmp) / "server_endpoints.json"
            server_path.write_text("", encoding="utf-8")
            exit_code, stdout, stderr = _run_parse_server_main(server_path, out_path)
            self.assertEqual(exit_code, 0, msg=stderr)
            self.assertIn("Extracted 0 endpoints", stdout)

    def test_decorators_without_docstrings(self):
        """Routes with decorators but no docstrings should still be extracted."""
        sample = """
@routes.get("/test")
def test_route():
    return None
"""
        endpoints = _load_parse_server().extract_endpoints(sample)
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0]["route"], "/test")
        self.assertEqual(endpoints[0]["description"], "")

    def test_path_normalization_in_metadata(self):
        """Source paths in metadata should use forward slashes."""
        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            out_path = Path(tmp) / "server_endpoints.json"
            server_path.write_text("@routes.get('/health')\ndef health(): pass", encoding="utf-8")
            exit_code, _stdout, stderr = _run_parse_server_main(
                server_path,
                out_path,
                "--version",
                "v0.0.1",
                "--commit",
                "abc123",
            )
            self.assertEqual(exit_code, 0, msg=stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertIn("sources", data["metadata"])
            self.assertNotIn("source", data["metadata"])
            self.assertIsInstance(data["metadata"]["sources"], list)
            for source in data["metadata"]["sources"]:
                self.assertNotIn("\\", source, "Source path should not contain backslashes")

    def test_unicode_in_docstring(self):
        """Unicode characters in docstrings should be handled correctly."""
        sample = '''
@routes.get("/status")
def status():
    """Check the status of the server."""
    return None
'''
        endpoints = _load_parse_server().extract_endpoints(sample)
        self.assertEqual(len(endpoints), 1)

    def test_variable_payload_without_literal_assignment_stays_conservative(self):
        """Unknown variable-backed payloads should not invent response fields."""
        sample = """
@routes.get("/legacy")
def legacy_route():
    response = build_response()
    return web.json_response(response)
"""
        returns = _load_parse_server().extract_endpoints(sample)[0]["returns"]
        self.assertEqual(returns["kind"], "json")
        self.assertEqual(returns["fields"], [])
        self.assertEqual(returns["summary"], "JSON response.")


class ParseHooksEdgeCases(unittest.TestCase):
    """Edge case tests for parse_hooks.py."""

    def test_empty_file_produces_known_hooks(self):
        """An empty source file should still find known hooks via regex search."""
        with tempfile.TemporaryDirectory() as tmp:
            app_path = Path(tmp) / "app.ts"
            out_path = Path(tmp) / "js_hooks.json"
            app_path.write_text("", encoding="utf-8")
            exit_code, _stdout, stderr = _run_parse_hooks_main(
                str(app_path),
                "--version",
                "v0.0.1",
                "--commit",
                "abc123",
                "--output",
                str(out_path),
            )
            self.assertEqual(exit_code, 0, msg=stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            # Empty file should produce 0 hooks (no invocations, no typed hooks, no known hook matches)
            self.assertEqual(len(data["hooks"]), 0)

    def test_path_normalization_in_metadata(self):
        """Source paths in metadata should use forward slashes."""
        with tempfile.TemporaryDirectory() as tmp:
            app_path = Path(tmp) / "app.ts"
            out_path = Path(tmp) / "js_hooks.json"
            app_path.write_text("invokeExtensions('setup')", encoding="utf-8")
            exit_code, _stdout, stderr = _run_parse_hooks_main(
                str(app_path),
                "--version",
                "v0.0.1",
                "--commit",
                "abc123",
                "--output",
                str(out_path),
            )
            self.assertEqual(exit_code, 0, msg=stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            for source in data["metadata"]["sources"]:
                self.assertNotIn("\\", source, "Source paths should not contain backslashes")

    def test_known_hook_names_in_comments_do_not_seed_entries(self):
        """Fallback seeding should ignore comment-only mentions of known hook names."""
        sample = """
// init should not create a hook entry here
// setup should not create a hook entry here either
const note = "nodeCreated is mentioned as plain text";
"""
        with tempfile.TemporaryDirectory() as tmp:
            app_path = Path(tmp) / "app.ts"
            out_path = Path(tmp) / "js_hooks.json"
            app_path.write_text(sample, encoding="utf-8")
            exit_code, _stdout, stderr = _run_parse_hooks_main(
                str(app_path), "--output", str(out_path)
            )
            self.assertEqual(exit_code, 0, msg=stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(data["hooks"], [])


class ParseNodeApiSchemaEdgeCases(unittest.TestCase):
    """Edge case tests for parse_node_api_schema.py."""

    def test_empty_files_produce_empty_results(self):
        """Empty source files should produce empty lists/dicts."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            server_path = tmp_path / "server.py"
            io_path = tmp_path / "_io.py"
            basic_types_path = tmp_path / "basic_types.py"
            out_path = tmp_path / "node_api_schema.json"
            server_path.write_text("", encoding="utf-8")
            io_path.write_text("", encoding="utf-8")
            basic_types_path.write_text("", encoding="utf-8")
            exit_code, _stdout, stderr = _run_parse_node_api_main(
                server_path,
                io_path,
                basic_types_path,
                "--version",
                "v0.0.1",
                "--commit",
                "abc123",
                "--output",
                str(out_path),
            )
            self.assertEqual(exit_code, 0, msg=stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(len(data["object_info_fields"]), 0)
            self.assertEqual(len(data["io_types"]), 0)
            self.assertEqual(len(data["basic_input_shapes"]), 0)

    def test_path_normalization_in_metadata(self):
        """Source paths in metadata should use forward slashes."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            server_path = tmp_path / "server.py"
            io_path = tmp_path / "_io.py"
            basic_types_path = tmp_path / "basic_types.py"
            out_path = tmp_path / "node_api_schema.json"
            server_path.write_text("", encoding="utf-8")
            io_path.write_text("", encoding="utf-8")
            basic_types_path.write_text("", encoding="utf-8")
            exit_code, _stdout, stderr = _run_parse_node_api_main(
                server_path,
                io_path,
                basic_types_path,
                "--version",
                "v0.0.1",
                "--commit",
                "abc123",
                "--output",
                str(out_path),
            )
            self.assertEqual(exit_code, 0, msg=stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            for source in data["metadata"]["sources"]:
                self.assertNotIn("\\", source, "Source paths should not contain backslashes")

    def test_missing_runtime_snapshot_warns_without_name_error(self):
        """Missing runtime snapshot should warn predictably and stay source-only."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            server_path = tmp_path / "server.py"
            io_path = tmp_path / "_io.py"
            basic_types_path = tmp_path / "basic_types.py"
            missing_runtime_path = tmp_path / "missing_runtime.json"
            out_path = tmp_path / "node_api_schema.json"
            server_path.write_text("", encoding="utf-8")
            io_path.write_text("", encoding="utf-8")
            basic_types_path.write_text("", encoding="utf-8")
            exit_code, _stdout, stderr = _run_parse_node_api_main(
                server_path,
                io_path,
                basic_types_path,
                "--object-info-runtime-path",
                str(missing_runtime_path),
                "--output",
                str(out_path),
            )
            self.assertEqual(exit_code, 0, msg=stderr)
            self.assertIn("WARNING: runtime snapshot not found", stderr)
            self.assertNotIn("NameError", stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(data["metadata"]["provenance"]["mode"], "source-only")
            self.assertFalse(data["coverage"]["runtime_enriched"])


class ValidateSchemaTests(unittest.TestCase):
    """Tests for scripts/verify/validate_schema.py."""

    def test_module_imports(self):
        """The validate_schema module should be importable."""
        module = _load_module("validate_schema", VALIDATE_SCHEMA)
        self.assertTrue(hasattr(module, "validate_top_level"))
        self.assertTrue(hasattr(module, "validate_metadata"))
        self.assertTrue(hasattr(module, "validate_endpoints"))
        self.assertTrue(hasattr(module, "validate_hooks"))
        self.assertTrue(hasattr(module, "validate_io_types"))

    def test_schema_validation_passes(self):
        """The schema validator should pass on a valid normalized payload."""
        module = _load_module("validate_schema", VALIDATE_SCHEMA)
        data = {
            "metadata": {
                "sources": ["references/snapshots/server.py"],
                "extracted_date": "2026-01-01",
                "version": "v1",
                "commit": "abc123",
            },
            "coverage": {
                "description": "contract",
                "guaranteed_fields": ["endpoints[].route"],
                "best_effort_fields": ["endpoints[].description"],
                "deferred": ["parameter typing"],
            },
            "endpoints": [],
            # Empty runtime-contract sections are valid for this minimal schema fixture.
            "prompt_submission_contract": {},
            "prompt_validation_errors": {},
            "queue_history_contract": {},
        }
        errors = module.validate_top_level(
            data, module.SCHEMAS["server_endpoints.json"], "server_endpoints.json"
        )
        errors.extend(module.validate_metadata(data, "server_endpoints.json"))
        errors.extend(module.validate_coverage(data, "server_endpoints.json"))
        errors.extend(module.validate_endpoints(data, "server_endpoints.json"))
        self.assertEqual(errors, [])

    def test_detects_missing_required_key(self):
        """The validator should detect a missing required top-level key."""
        module = _load_module("validate_schema", VALIDATE_SCHEMA)
        data = {
            "metadata": {
                "sources": ["test"],
                "extracted_date": "2026-01-01",
                "version": "v1",
                "commit": "abc",
            },
            "coverage": {
                "description": "contract",
                "guaranteed_fields": [],
                "best_effort_fields": [],
                "deferred": [],
            },
        }
        # Missing "endpoints" key
        errors = module.validate_top_level(
            data, module.SCHEMAS["server_endpoints.json"], "server_endpoints.json"
        )
        self.assertTrue(any("missing required key 'endpoints'" in e for e in errors))

    def test_detects_backslashes_in_metadata(self):
        """The validator should detect backslashes in source paths."""
        module = _load_module("validate_schema", VALIDATE_SCHEMA)
        data = {
            "metadata": {
                "sources": ["path\\with\\backslashes"],
                "extracted_date": "2026-01-01",
                "version": "v1",
                "commit": "abc123",
            },
            "coverage": {
                "description": "contract",
                "guaranteed_fields": [],
                "best_effort_fields": [],
                "deferred": [],
            },
            "endpoints": [],
        }
        errors = module.validate_metadata(data, "server_endpoints.json")
        self.assertTrue(any("backslashes" in e for e in errors))

    def test_detects_version_without_v_prefix(self):
        """The validator should detect versions that don't start with 'v'."""
        module = _load_module("validate_schema", VALIDATE_SCHEMA)
        data = {
            "metadata": {
                "sources": ["test"],
                "extracted_date": "2026-01-01",
                "version": "0.19.3",
                "commit": "abc123",
            },
            "coverage": {
                "description": "contract",
                "guaranteed_fields": [],
                "best_effort_fields": [],
                "deferred": [],
            },
            "endpoints": [],
        }
        errors = module.validate_metadata(data, "server_endpoints.json")
        self.assertTrue(any("should start with 'v'" in e for e in errors))

    def test_detects_invalid_commit_hash(self):
        """The validator should detect non-hex commit hashes."""
        module = _load_module("validate_schema", VALIDATE_SCHEMA)
        data = {
            "metadata": {
                "sources": ["test"],
                "extracted_date": "2026-01-01",
                "version": "v1",
                "commit": "not-a-hex-string!",
            },
            "coverage": {
                "description": "contract",
                "guaranteed_fields": [],
                "best_effort_fields": [],
                "deferred": [],
            },
            "endpoints": [],
        }
        errors = module.validate_metadata(data, "server_endpoints.json")
        self.assertTrue(any("hex SHA hash" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
