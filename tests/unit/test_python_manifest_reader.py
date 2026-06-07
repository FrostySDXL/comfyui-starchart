"""Tests for examples/consumers/python-manifest-reader/read_manifest.py."""

from __future__ import annotations

import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "examples" / "consumers" / "python-manifest-reader" / "read_manifest.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("read_manifest", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PythonManifestReaderTests(unittest.TestCase):
    """Offline tests for manifest loading and artifact-key handling."""

    def test_load_json_uses_urlopen(self):
        module = _load_module()
        body = json.dumps({"artifact_schema_version": "1"}).encode("utf-8")

        with patch.object(module, "urlopen", return_value=io.BytesIO(body)) as mock_urlopen:
            payload = module.load_json("https://example.test/artifacts/manifest.json")

        self.assertEqual(payload["artifact_schema_version"], "1")
        mock_urlopen.assert_called_once_with("https://example.test/artifacts/manifest.json")

    def test_main_rejects_unknown_artifact_key(self):
        module = _load_module()
        with patch.object(module, "load_json", return_value={"artifacts": {}}):
            result = module.main(["read_manifest.py", "https://example.test", "missing.json"])

        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
