"""Tests for scripts/common/http_utils.py."""

import json
import ssl
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from scripts.common import http_utils


def _make_response(payload: bytes, content_type: str = "application/json"):
    fake = MagicMock()
    fake.read.return_value = payload
    fake.headers.get_content_type.return_value = content_type
    fake.__enter__ = MagicMock(return_value=fake)
    fake.__exit__ = MagicMock(return_value=False)
    return fake


def _http_error(code: int):
    return HTTPError("http://127.0.0.1:8188/object_info", code, "boom", {}, None)


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

    def test_cap_exceeded_raises_before_json_parse(self):
        with patch.object(http_utils, "urlopen", return_value=_make_response(b'{"ok": true}')):
            with self.assertRaises(RuntimeError) as ctx:
                http_utils.get_json("http://127.0.0.1:8188/object_info", max_bytes=4)

        self.assertIn("exceeds 4 byte limit", str(ctx.exception))

    def test_content_type_message_for_invalid_json(self):
        with patch.object(
            http_utils,
            "urlopen",
            return_value=_make_response(b"not-json", content_type="text/plain"),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                http_utils.get_json("http://127.0.0.1:8188/object_info")

        self.assertIn("content-type text/plain", str(ctx.exception))

    def test_ssl_context_forwarding(self):
        context = ssl.create_default_context()
        with patch.object(
            http_utils, "urlopen", return_value=_make_response(b'{"ok": true}')
        ) as mock_urlopen:
            self.assertEqual(
                http_utils.get_json("https://127.0.0.1:8188/object_info", ssl_context=context),
                {"ok": True},
            )

        self.assertIs(mock_urlopen.call_args.kwargs["context"], context)

    def test_retry_success_after_one_500(self):
        with patch.object(
            http_utils,
            "urlopen",
            side_effect=[_http_error(500), _make_response(b'{"ok": true}')],
        ) as mock_urlopen:
            with patch.object(http_utils.random, "uniform", return_value=0.25) as mock_uniform:
                with patch.object(http_utils.time, "sleep") as mock_sleep:
                    self.assertEqual(
                        http_utils.get_json("http://127.0.0.1:8188/object_info"), {"ok": True}
                    )

        self.assertEqual(mock_urlopen.call_count, 2)
        mock_uniform.assert_called_once_with(0, 1.0)
        mock_sleep.assert_called_once_with(0.25)

    def test_retry_exhausted_returns_last_error(self):
        with patch.object(
            http_utils,
            "urlopen",
            side_effect=[_http_error(500), _http_error(502), _http_error(503), _http_error(504)],
        ) as mock_urlopen:
            with patch.object(http_utils.random, "uniform", return_value=0.1):
                with patch.object(http_utils.time, "sleep") as mock_sleep:
                    with self.assertRaises(http_utils.RetryBudgetExceeded):
                        http_utils.get_json("http://127.0.0.1:8188/object_info")

        self.assertEqual(mock_urlopen.call_count, http_utils.DEFAULT_MAX_RETRIES)
        self.assertLessEqual(sum(call.args[0] for call in mock_sleep.call_args_list), 5.0)

    def test_retry_skips_4xx_other_than_408_429(self):
        with patch.object(
            http_utils,
            "urlopen",
            side_effect=[_http_error(404), _make_response(b'{"ok": true}')],
        ) as mock_urlopen:
            with self.assertRaises(RuntimeError) as ctx:
                http_utils.get_json("http://127.0.0.1:8188/object_info")

        self.assertIn("HTTP error 404", str(ctx.exception))
        self.assertEqual(mock_urlopen.call_count, 1)

    def test_retry_skips_non_retryable_500_class(self):
        self.assertNotIn(501, http_utils.RETRYABLE_STATUS_CODES)
        with patch.object(
            http_utils,
            "urlopen",
            side_effect=[_http_error(501), _make_response(b'{"ok": true}')],
        ) as mock_urlopen:
            with self.assertRaises(RuntimeError) as ctx:
                http_utils.get_json("http://127.0.0.1:8188/object_info")

        self.assertIn("HTTP error 501", str(ctx.exception))
        self.assertEqual(mock_urlopen.call_count, 1)

    def test_backoff_cap_enforced(self):
        with patch.object(
            http_utils,
            "urlopen",
            side_effect=[_http_error(500), _http_error(502), _http_error(503)],
        ) as mock_urlopen:
            with patch.object(http_utils.random, "uniform", side_effect=[0.2, 4.9]):
                with patch.object(http_utils.time, "sleep") as mock_sleep:
                    with self.assertRaises(http_utils.RetryBudgetExceeded):
                        http_utils.get_json("http://127.0.0.1:8188/object_info")

        self.assertEqual(mock_urlopen.call_count, 2)
        self.assertEqual([call.args[0] for call in mock_sleep.call_args_list], [0.2])

    def test_jitter_is_random_within_band(self):
        delays = [0.0, 0.1, 0.25, 0.5] * 13
        with patch.object(http_utils.random, "uniform", side_effect=delays) as mock_uniform:
            for _ in range(50):
                with patch.object(
                    http_utils,
                    "urlopen",
                    side_effect=[_http_error(500), _make_response(b'{"ok": true}')],
                ):
                    with patch.object(http_utils.time, "sleep") as mock_sleep:
                        http_utils.get_json("http://127.0.0.1:8188/object_info")
                        delay = mock_sleep.call_args.args[0]
                        self.assertGreaterEqual(delay, 0)
                        self.assertLessEqual(delay, 1.0)

        self.assertEqual(mock_uniform.call_count, 50)


if __name__ == "__main__":
    unittest.main()
