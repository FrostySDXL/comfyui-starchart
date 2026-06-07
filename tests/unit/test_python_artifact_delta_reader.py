"""Tests for examples/consumers/python-artifact-delta-reader/read_delta_summary.py."""

from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO_ROOT / "examples" / "consumers" / "python-artifact-delta-reader" / "read_delta_summary.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("read_delta_summary", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_delta_summary() -> dict:
    return {
        "comparison": {
            "old": "old/raw",
            "new": "new/raw",
            "methodology": "artifact-directory-to-artifact-directory",
            "source_kind": "test",
            "old_label": "old label",
            "new_label": "new label",
        },
        "artifacts": {
            "server_endpoints": {
                "old_count": 1,
                "new_count": 2,
                "added": ["GET /queue"],
                "removed": [],
                "changed": ["POST /prompt"],
            },
            "node_api_schema": {
                "io_types": {
                    "old_count": 3,
                    "new_count": 3,
                    "added": [],
                    "removed": [],
                    "changed": [],
                }
            },
        },
    }


class PythonArtifactDeltaReaderTests(unittest.TestCase):
    """Offline tests for local and remote delta-summary loading."""

    def test_load_json_from_local_path(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "delta-summary.json"
            path.write_text(json.dumps(_sample_delta_summary()), encoding="utf-8")

            payload = module.load_json_from_location(str(path))

        self.assertEqual(
            payload["comparison"]["methodology"], "artifact-directory-to-artifact-directory"
        )

    def test_load_json_from_file_url(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "delta-summary.json"
            path.write_text(json.dumps(_sample_delta_summary()), encoding="utf-8")

            payload = module.load_json_from_location(path.as_uri())

        self.assertEqual(payload["comparison"]["source_kind"], "test")

    def test_load_json_from_site_url_appends_artifact_path(self):
        module = _load_module()
        body = json.dumps(_sample_delta_summary()).encode("utf-8")

        with patch.object(
            module.urllib.request, "urlopen", return_value=io.BytesIO(body)
        ) as mock_urlopen:
            payload = module.load_json_from_location("https://example.test/starchart")

        self.assertEqual(payload["comparison"]["old"], "old/raw")
        mock_urlopen.assert_called_once_with(
            "https://example.test/starchart/artifacts/delta-summary.json"
        )

    def test_main_prints_comparison_and_nested_counts(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "delta-summary.json"
            path.write_text(json.dumps(_sample_delta_summary()), encoding="utf-8")
            output = io.StringIO()

            with redirect_stdout(output):
                result = module.main(["read_delta_summary.py", str(path)])

        self.assertEqual(result, 0)
        text = output.getvalue()
        self.assertIn("Methodology: artifact-directory-to-artifact-directory", text)
        self.assertIn("server_endpoints: old=1 new=2 added=1 removed=0 changed=1", text)
        self.assertIn("node_api_schema.io_types: old=3 new=3 added=0 removed=0 changed=0", text)


if __name__ == "__main__":
    unittest.main()
