"""Tests for scripts/extract/parse_from_api.py."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "extract" / "parse_from_api.py"
HTTP_UTILS = REPO_ROOT / "scripts" / "common" / "http_utils.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("parse_from_api", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_http_utils_module():
    spec = importlib.util.spec_from_file_location("http_utils", HTTP_UTILS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ParseFromApiUnitTests(unittest.TestCase):
    """Direct unit tests for parse_from_api functions."""

    def test_compute_sha256(self):
        module = _load_module()
        self.assertEqual(
            module.compute_sha256(b"hello"),
            "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
        )

    def test_build_snapshot_structure(self):
        module = _load_module()
        snapshot = module.build_snapshot(
            url="http://127.0.0.1:8188",
            version="v0.19.3",
            commit="abc123",
            object_info={"KSampler": {"input": {}}},
            raw_bytes=b"{}",
        )
        self.assertIn("metadata", snapshot)
        self.assertIn("object_info", snapshot)
        self.assertEqual(snapshot["metadata"]["url"], "http://127.0.0.1:8188")
        self.assertEqual(snapshot["metadata"]["version"], "v0.19.3")
        self.assertEqual(snapshot["metadata"]["commit"], "abc123")
        self.assertEqual(snapshot["metadata"]["response_sha256"], module.compute_sha256(b"{}"))

    def test_fetch_object_info_success(self):
        module = _load_module()
        fake_payload = {"KSampler": {"input": {}}}
        fake_bytes = json.dumps(fake_payload).encode("utf-8")

        with patch.object(module.http_utils, "get_json_with_bytes", return_value=(fake_payload, fake_bytes)) as mock_get_json:
            result, raw_bytes = module.fetch_object_info("http://127.0.0.1:8188", timeout=10)

        self.assertEqual(result, fake_payload)
        self.assertEqual(raw_bytes, fake_bytes)
        mock_get_json.assert_called_once_with("http://127.0.0.1:8188/object_info", timeout=10)

    def test_fetch_object_info_http_error(self):
        module = _load_module()
        with patch.object(
            module.http_utils,
            "get_json_with_bytes",
            side_effect=RuntimeError("HTTP error 500 from http://127.0.0.1:8188/object_info: Internal Server Error"),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                module.fetch_object_info("http://127.0.0.1:8188", timeout=10)
        self.assertIn("HTTP error 500", str(ctx.exception))

    def test_fetch_object_info_invalid_json(self):
        module = _load_module()
        with patch.object(
            module.http_utils,
            "get_json_with_bytes",
            side_effect=RuntimeError("Invalid JSON from http://127.0.0.1:8188/object_info: bad payload"),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                module.fetch_object_info("http://127.0.0.1:8188", timeout=10)
        self.assertIn("Invalid JSON", str(ctx.exception))

    def test_fetch_object_info_non_dict_response(self):
        module = _load_module()
        with patch.object(module.http_utils, "get_json_with_bytes", return_value=([], b"[]")):
            with self.assertRaises(RuntimeError) as ctx:
                module.fetch_object_info("http://127.0.0.1:8188", timeout=10)
        self.assertIn("Expected dict response", str(ctx.exception))

    def test_deterministic_hash(self):
        module = _load_module()
        data = json.dumps({"a": 1, "b": 2}, sort_keys=True, separators=(",", ":")).encode("utf-8")
        hash1 = module.compute_sha256(data)
        hash2 = module.compute_sha256(data)
        self.assertEqual(hash1, hash2)


class HttpUtilsBehaviorTests(unittest.TestCase):
    """Behavior tests for the shared HTTP helper used by extractor/runtime scripts."""

    def test_get_json_timeout_is_wrapped_consistently(self):
        module = _load_http_utils_module()
        with patch.object(module, "urlopen", side_effect=TimeoutError):
            with self.assertRaises(RuntimeError) as ctx:
                module.get_json("http://127.0.0.1:8188/object_info", timeout=5)
        self.assertIn("Timeout reaching http://127.0.0.1:8188/object_info after 5s", str(ctx.exception))


class ParseFromApiScriptTests(unittest.TestCase):
    """Tests for the CLI script behavior."""

    def test_cli_missing_url_fails(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertNotEqual(result.returncode, 0)

    def test_cli_success_with_mock(self):
        module = _load_module()
        fake_payload = {"KSampler": {"input": {}}}
        fake_bytes = json.dumps(fake_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "object_info_runtime_test.json"

            with patch.object(module.http_utils, "get_json_with_bytes", return_value=(fake_payload, fake_bytes)):
                with patch("sys.argv", [
                    "parse_from_api.py",
                    "--url", "http://127.0.0.1:8188",
                    "--version", "v0.19.3",
                    "--commit", "3086026401180c9216bcb6ace442a4e3587d2c66",
                    "--output", str(output_path),
                ]):
                    result = module.main()

            self.assertEqual(result, 0)
            self.assertTrue(output_path.exists())
            data = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(data["metadata"]["version"], "v0.19.3")
            self.assertEqual(data["metadata"]["commit"], "3086026401180c9216bcb6ace442a4e3587d2c66")
            self.assertIn("object_info", data)


if __name__ == "__main__":
    unittest.main()
