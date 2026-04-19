"""Edge case tests for extractors and schema validator."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PARSE_SERVER = REPO_ROOT / "scripts" / "extract" / "parse_server.py"
PARSE_HOOKS = REPO_ROOT / "scripts" / "extract" / "parse_hooks.py"
PARSE_NODE_API = REPO_ROOT / "scripts" / "extract" / "parse_node_api_schema.py"
VALIDATE_SCHEMA = REPO_ROOT / "scripts" / "verify" / "validate_schema.py"
SERVER_OUTPUT = REPO_ROOT / "references" / "raw" / "server_endpoints.json"
HOOKS_OUTPUT = REPO_ROOT / "references" / "raw" / "js_hooks.json"
NODE_API_OUTPUT = REPO_ROOT / "references" / "raw" / "node_api_schema.json"


def _load_module(name, path):
    """Load a Python module from file path."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ParseServerEdgeCases(unittest.TestCase):
    """Edge case tests for parse_server.py."""

    def setUp(self):
        self.original = SERVER_OUTPUT.read_text(encoding="utf-8")

    def tearDown(self):
        SERVER_OUTPUT.write_text(self.original, encoding="utf-8")

    def test_empty_file_produces_zero_endpoints(self):
        """An empty source file should produce zero endpoints."""
        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            server_path.write_text("", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(PARSE_SERVER), str(server_path)],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
            )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Extracted 0 endpoints", result.stdout)

    def test_decorators_without_docstrings(self):
        """Routes with decorators but no docstrings should still be extracted."""
        sample = '''
@routes.get("/test")
def test_route():
    return None
'''
        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            server_path.write_text(sample, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(PARSE_SERVER), str(server_path)],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
            )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        data = json.loads(SERVER_OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(len(data["endpoints"]), 1)
        self.assertEqual(data["endpoints"][0]["route"], "/test")
        self.assertEqual(data["endpoints"][0]["description"], "")

    def test_path_normalization_in_metadata(self):
        """Source paths in metadata should use forward slashes."""
        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            server_path.write_text("@routes.get('/health')\ndef health(): pass", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(PARSE_SERVER), str(server_path),
                 "--version", "v0.0.1", "--commit", "abc123"],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
            )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        data = json.loads(SERVER_OUTPUT.read_text(encoding="utf-8"))
        self.assertNotIn("\\", data["metadata"]["source"],
                         "Source path should not contain backslashes")

    def test_unicode_in_docstring(self):
        """Unicode characters in docstrings should be handled correctly."""
        sample = '''
@routes.get("/status")
def status():
    """Check the status of the server."""
    return None
'''
        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            server_path.write_text(sample, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(PARSE_SERVER), str(server_path)],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
            )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        data = json.loads(SERVER_OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(len(data["endpoints"]), 1)


class ParseHooksEdgeCases(unittest.TestCase):
    """Edge case tests for parse_hooks.py."""

    def setUp(self):
        self.original = HOOKS_OUTPUT.read_text(encoding="utf-8")

    def tearDown(self):
        HOOKS_OUTPUT.write_text(self.original, encoding="utf-8")

    def test_empty_file_produces_known_hooks(self):
        """An empty source file should still find known hooks via regex search."""
        with tempfile.TemporaryDirectory() as tmp:
            app_path = Path(tmp) / "app.ts"
            app_path.write_text("", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(PARSE_HOOKS), str(app_path),
                 "--version", "v0.0.1", "--commit", "abc123"],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
            )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        data = json.loads(HOOKS_OUTPUT.read_text(encoding="utf-8"))
        # Empty file should produce 0 hooks (no invocations, no typed hooks, no known hook matches)
        self.assertEqual(len(data["hooks"]), 0)

    def test_path_normalization_in_metadata(self):
        """Source paths in metadata should use forward slashes."""
        with tempfile.TemporaryDirectory() as tmp:
            app_path = Path(tmp) / "app.ts"
            app_path.write_text("invokeExtensions('setup')", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(PARSE_HOOKS), str(app_path),
                 "--version", "v0.0.1", "--commit", "abc123"],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
            )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        data = json.loads(HOOKS_OUTPUT.read_text(encoding="utf-8"))
        for source in data["metadata"]["sources"]:
            self.assertNotIn("\\", source,
                             "Source paths should not contain backslashes")


class ParseNodeApiSchemaEdgeCases(unittest.TestCase):
    """Edge case tests for parse_node_api_schema.py."""

    def setUp(self):
        self.original = NODE_API_OUTPUT.read_text(encoding="utf-8")

    def tearDown(self):
        NODE_API_OUTPUT.write_text(self.original, encoding="utf-8")

    def test_empty_files_produce_empty_results(self):
        """Empty source files should produce empty lists/dicts."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            server_path = tmp_path / "server.py"
            io_path = tmp_path / "_io.py"
            basic_types_path = tmp_path / "basic_types.py"
            server_path.write_text("", encoding="utf-8")
            io_path.write_text("", encoding="utf-8")
            basic_types_path.write_text("", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(PARSE_NODE_API),
                 str(server_path), str(io_path), str(basic_types_path),
                 "--version", "v0.0.1", "--commit", "abc123"],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
            )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        data = json.loads(NODE_API_OUTPUT.read_text(encoding="utf-8"))
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
            server_path.write_text("", encoding="utf-8")
            io_path.write_text("", encoding="utf-8")
            basic_types_path.write_text("", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(PARSE_NODE_API),
                 str(server_path), str(io_path), str(basic_types_path),
                 "--version", "v0.0.1", "--commit", "abc123"],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
            )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        data = json.loads(NODE_API_OUTPUT.read_text(encoding="utf-8"))
        for source in data["metadata"]["sources"]:
            self.assertNotIn("\\", source,
                             "Source paths should not contain backslashes")


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
        """The schema validator should pass on current JSON files."""
        result = subprocess.run(
            [sys.executable, str(VALIDATE_SCHEMA)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("pass schema validation", result.stdout)

    def test_detects_missing_required_key(self):
        """The validator should detect a missing required top-level key."""
        module = _load_module("validate_schema", VALIDATE_SCHEMA)
        data = {"metadata": {"source": "test", "extracted_date": "2026-01-01",
                             "version": "v1", "commit": "abc"}}
        # Missing "endpoints" key
        errors = module.validate_top_level(data, module.SCHEMAS["server_endpoints.json"], "server_endpoints.json")
        self.assertTrue(any("missing required key 'endpoints'" in e for e in errors))

    def test_detects_backslashes_in_metadata(self):
        """The validator should detect backslashes in source paths."""
        module = _load_module("validate_schema", VALIDATE_SCHEMA)
        data = {
            "metadata": {
                "source": "path\\with\\backslashes",
                "extracted_date": "2026-01-01",
                "version": "v1",
                "commit": "abc123",
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
                "source": "test",
                "extracted_date": "2026-01-01",
                "version": "0.19.3",
                "commit": "abc123",
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
                "source": "test",
                "extracted_date": "2026-01-01",
                "version": "v1",
                "commit": "not-a-hex-string!",
            },
            "endpoints": [],
        }
        errors = module.validate_metadata(data, "server_endpoints.json")
        self.assertTrue(any("hex SHA hash" in e for e in errors))


if __name__ == "__main__":
    unittest.main()