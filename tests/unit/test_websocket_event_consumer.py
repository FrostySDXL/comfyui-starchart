"""Tests for examples/consumers/websocket-event-consumer/watch_events.py."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "examples" / "consumers" / "websocket-event-consumer" / "watch_events.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("websocket_event_consumer", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WebSocketEventConsumerTests(unittest.TestCase):
    """Unit tests for bounded frame filtering without a live runtime."""

    def test_imports_shared_binary_frame_helper_object(self):
        module = _load_module()

        self.assertIs(module.is_binary_frame, module.submit_and_monitor.is_binary_frame)

    def test_describe_frame_skips_binary_payload(self):
        module = _load_module()

        self.assertEqual(module.describe_frame(b"preview-bytes"), "binary preview frame skipped")

    def test_describe_frame_formats_known_json_event(self):
        module = _load_module()
        payload = json.dumps(
            {
                "type": "executing",
                "data": {"node": "7", "prompt_id": "prompt-1"},
            }
        )

        self.assertEqual(
            module.describe_frame(payload, prompt_id="prompt-1"),
            "executing node=7 prompt_id=prompt-1",
        )

    def test_describe_frame_ignores_other_prompt_events(self):
        module = _load_module()
        payload = json.dumps(
            {
                "type": "execution_success",
                "data": {"prompt_id": "other-prompt"},
            }
        )

        self.assertIsNone(module.describe_frame(payload, prompt_id="prompt-1"))


if __name__ == "__main__":
    unittest.main()
