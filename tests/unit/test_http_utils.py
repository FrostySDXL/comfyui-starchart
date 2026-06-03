"""Tests for scripts/common/http_utils.py."""

import json
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from scripts.common import http_utils


def _make_response(payload: bytes):
    fake = MagicMock()
    fake.read.return_value = payload
    fake.__enter__ = MagicMock(return_value=fake)
    fake.__exit__ = MagicMock(return_value=False)
    return fake


class HttpUtilsTests(unittest.TestCase):
    def test_get_json_returns_payload(self):
        with patch.object(http_utils, "urlopen", return_value=_make_response(b'{"ok": true}')):
            self.assertEqual(http_utils.get_json("http://127.0.0.1:8188/object_info"), {"ok": True})

    def test_get_json_with_bytes_returns_payload_and_raw_bytes(self):
        raw = b'{"ok": true}'
        with patch.object(http_utils, "urlopen", return_value=_make_response(raw)):
            payload, raw_bytes = http_utils.get_json_with_bytes("http://127.0.0.1:8188/object_info")

        self.assertEqual(payload, {"ok": True})
        self.assertEqual(raw_bytes, raw)

    def test_post_json_sends_encoded_json_payload(self):
        with patch.object(
            http_utils, "urlopen", return_value=_make_response(b'{"queued": true}')
        ) as mock_urlopen:
            result = http_utils.post_json("http://127.0.0.1:8188/prompt", {"prompt": {}})

        self.assertEqual(result, {"queued": True})
        request = mock_urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(json.loads(request.data.decode("utf-8")), {"prompt": {}})

    def test_http_error_is_wrapped(self):
        error = HTTPError("http://127.0.0.1:8188/object_info", 500, "boom", {}, None)
        with patch.object(http_utils, "urlopen", side_effect=error):
            with self.assertRaises(RuntimeError) as ctx:
                http_utils.get_json("http://127.0.0.1:8188/object_info")

        self.assertIn("HTTP error 500", str(ctx.exception))

    def test_url_error_is_wrapped(self):
        with patch.object(http_utils, "urlopen", side_effect=URLError("refused")):
            with self.assertRaises(RuntimeError) as ctx:
                http_utils.get_json("http://127.0.0.1:8188/object_info")

        self.assertIn("URL error reaching http://127.0.0.1:8188/object_info", str(ctx.exception))

    def test_timeout_is_wrapped(self):
        with patch.object(http_utils, "urlopen", side_effect=TimeoutError):
            with self.assertRaises(RuntimeError) as ctx:
                http_utils.get_json("http://127.0.0.1:8188/object_info", timeout=5)

        self.assertIn(
            "Timeout reaching http://127.0.0.1:8188/object_info after 5s", str(ctx.exception)
        )

    def test_invalid_json_is_wrapped(self):
        with patch.object(http_utils, "urlopen", return_value=_make_response(b"not-json")):
            with self.assertRaises(RuntimeError) as ctx:
                http_utils.get_json("http://127.0.0.1:8188/object_info")

        self.assertIn("Invalid JSON from http://127.0.0.1:8188/object_info", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
