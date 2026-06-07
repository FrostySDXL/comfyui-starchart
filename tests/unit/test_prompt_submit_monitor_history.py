"""Tests for examples/consumers/prompt-submit-monitor-history/submit_and_monitor.py."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO_ROOT / "examples" / "consumers" / "prompt-submit-monitor-history" / "submit_and_monitor.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("submit_and_monitor", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PromptSubmitMonitorHistoryTests(unittest.TestCase):
    """Offline coverage for helper behavior and HTTP error handling."""

    def test_build_ws_url_uses_ws_for_http_base(self):
        module = _load_module()

        self.assertEqual(
            module.build_ws_url("http://127.0.0.1:8188", "client-1"),
            "ws://127.0.0.1:8188/ws?clientId=client-1",
        )

    def test_build_ws_url_preserves_https_path_prefix(self):
        module = _load_module()

        self.assertEqual(
            module.build_ws_url("https://example.test/comfy", "client 1"),
            "wss://example.test/comfy/ws?clientId=client+1",
        )

    def test_event_filtering_helper_detects_binary_payloads(self):
        module = _load_module()

        self.assertTrue(module.is_binary_frame(b"preview"))
        self.assertFalse(module.is_binary_frame(json.dumps({"type": "status"})))

    def test_compact_event_message_formats_execution_status(self):
        module = _load_module()

        self.assertEqual(
            module.compact_event_message(
                "progress", {"node": "3", "value": 1, "max": 4, "prompt_id": "p1"}
            ),
            "progress node=3 value=1/4 prompt_id=p1",
        )

    def test_main_reports_prompt_submission_http_error(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow = Path(tmpdir) / "workflow.json"
            workflow.write_text("{}\n", encoding="utf-8")
            error = urllib.error.HTTPError(
                url="http://example.test/prompt",
                code=400,
                msg="Bad Request",
                hdrs=None,
                fp=None,
            )
            error.read = lambda: b'{"error":"bad prompt"}'

            with (
                patch.object(module, "http_json", side_effect=error),
                patch.object(
                    module.sys,
                    "argv",
                    [
                        "submit_and_monitor.py",
                        "--url",
                        "http://example.test",
                        "--workflow",
                        str(workflow),
                    ],
                ),
            ):
                result = module.main()

        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
