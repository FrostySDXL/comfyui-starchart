from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.common import json_utils


class JsonUtilsTests(unittest.TestCase):
    def test_compute_textual_json_sha256_normalizes_crlf(self):
        with tempfile.TemporaryDirectory() as tmp:
            crlf_path = Path(tmp) / "sample-crlf.json"
            lf_path = Path(tmp) / "sample-lf.json"
            crlf_path.write_bytes(b'{\r\n  "a": 1\r\n}\r\n')
            lf_path.write_bytes(b'{\n  "a": 1\n}\n')

            self.assertEqual(
                json_utils.compute_textual_json_sha256(crlf_path),
                json_utils.compute_textual_json_sha256(lf_path),
            )

    def test_compute_bytes_sha256(self):
        self.assertEqual(
            json_utils.compute_bytes_sha256(b"hello"),
            "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
        )

    def test_load_and_write_json_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.json"
            payload = {"x": 1, "y": [2, 3]}
            json_utils.write_json(path, payload)
            self.assertEqual(json_utils.load_json(path), payload)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), payload)
