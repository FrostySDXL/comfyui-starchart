"""Tests for scripts/verify/example_runtime_smoke.py."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "example_runtime_smoke.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("example_runtime_smoke", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExampleRuntimeSmokeTests(unittest.TestCase):
    """Runtime smoke checks stay examples-only and opt-in."""

    def test_build_prompt_payload_replaces_model_and_client_id(self):
        module = _load_module()

        payload = module.build_prompt_payload(
            REPO_ROOT / "examples" / "api-calls" / "post-prompt.json",
            model_name="real-model.safetensors",
            client_id="client-123",
        )

        self.assertEqual(payload["client_id"], "client-123")
        self.assertIn("real-model.safetensors", str(payload))
        self.assertNotIn("YOUR_MODEL_NAME_HERE.safetensors", str(payload))

    def test_core_prompt_nodes_are_checked_against_object_info(self):
        module = _load_module()
        object_info = {name: {} for name in module.REQUIRED_PROMPT_CLASS_TYPES}

        self.assertEqual(module.missing_required_prompt_classes(object_info), [])

    def test_core_prompt_node_check_reports_missing_classes(self):
        module = _load_module()

        missing = module.missing_required_prompt_classes({"KSampler": {}})

        self.assertIn("SaveImage", missing)

    def test_extension_route_check_uses_examples_route_only(self):
        module = _load_module()

        with patch.object(
            module, "fetch_json", return_value={"message": "route ready"}
        ) as mock_fetch:
            self.assertTrue(module.check_extension_route("http://127.0.0.1:8188", timeout=5))

        mock_fetch.assert_called_once_with(
            "http://127.0.0.1:8188/minimal-route-registration/ping",
            5,
        )

    def test_websocket_status_supports_non_context_manager_client(self):
        module = _load_module()

        class FakeWebSocket:
            closed = False

            def recv(self):
                return '{"type":"status","data":{}}'

            def close(self):
                self.closed = True

        fake_ws = FakeWebSocket()

        with patch.dict(
            "sys.modules",
            {
                "websocket": type(
                    "FakeWebSocketModule",
                    (),
                    {"create_connection": lambda *args, **kwargs: fake_ws},
                )
            },
        ):
            self.assertTrue(module.check_websocket_status("http://127.0.0.1:8188", timeout=5))

        self.assertTrue(fake_ws.closed)


if __name__ == "__main__":
    unittest.main()
