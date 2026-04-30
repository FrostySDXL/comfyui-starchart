"""Tests for scripts/check_upstream_versions.py."""

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check_upstream_versions.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_upstream_versions", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CheckUpstreamVersionsUnitTests(unittest.TestCase):
    """Direct unit tests for check_upstream_versions functions."""

    def test_read_pinned_version_success(self):
        module = _load_module()
        data = {
            "metadata": {
                "version": "v0.19.3",
                "commit": "abc123",
            }
        }
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=json.dumps(data)):
                result = module._read_pinned_version(Path("dummy.json"))
        self.assertEqual(result, {"version": "v0.19.3", "commit": "abc123"})

    def test_read_pinned_version_missing_file(self):
        module = _load_module()
        result = module._read_pinned_version(Path("/nonexistent/file.json"))
        self.assertIsNone(result)

    def test_read_pinned_version_invalid_json(self):
        module = _load_module()
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value="not json"):
                result = module._read_pinned_version(Path("dummy.json"))
        self.assertIsNone(result)

    def test_latest_tag_from_github_success(self):
        module = _load_module()
        fake_response = [{"name": "v0.20.0"}]
        with patch.object(module, "_fetch_json", return_value=fake_response):
            result = module._latest_tag_from_github("https://api.github.com/repos/Comfy-Org/ComfyUI/tags?per_page=1")
        self.assertEqual(result, "v0.20.0")

    def test_latest_tag_from_github_empty(self):
        module = _load_module()
        with patch.object(module, "_fetch_json", return_value=[]):
            result = module._latest_tag_from_github("https://api.github.com/repos/Comfy-Org/ComfyUI/tags?per_page=1")
        self.assertIsNone(result)

    def test_latest_tag_from_github_picks_highest_semver_tag(self):
        module = _load_module()
        fake_response = [
            {"name": "main"},
            {"name": "v0.19.3"},
            {"name": "v0.20.1"},
            {"name": "nightly"},
            {"name": "v0.20.0"},
        ]
        with patch.object(module, "_fetch_json", return_value=fake_response):
            result = module._latest_tag_from_github("https://api.github.com/repos/Comfy-Org/ComfyUI/tags?per_page=1")
        self.assertEqual(result, "v0.20.1")

    def test_build_summary_update_available(self):
        module = _load_module()
        summary = module._build_summary(
            {"version": "v0.19.3", "commit": "abc"},
            "v0.20.0",
            {"version": "v1.42.11", "commit": "def"},
            "v1.43.0",
        )
        self.assertTrue(summary["any_update_available"])
        core = summary["components"][0]
        self.assertTrue(core["update_available"])
        self.assertIn("v0.20.0", core["suggested_refresh_command"])

    def test_build_summary_no_update(self):
        module = _load_module()
        summary = module._build_summary(
            {"version": "v0.19.3", "commit": "abc"},
            "v0.19.3",
            {"version": "v1.42.11", "commit": "def"},
            "v1.42.11",
        )
        self.assertFalse(summary["any_update_available"])
        self.assertFalse(summary["components"][0]["update_available"])

    def test_build_markdown_contains_versions(self):
        module = _load_module()
        summary = module._build_summary(
            {"version": "v0.19.3", "commit": "abc"},
            "v0.20.0",
            {"version": "v1.42.11", "commit": "def"},
            "v1.42.11",
        )
        md = module._build_markdown(summary)
        self.assertIn("v0.19.3", md)
        self.assertIn("v0.20.0", md)
        self.assertIn("Next Actions", md)

    def test_fetch_json_success(self):
        module = _load_module()
        fake_data = json.dumps([{"name": "v1.0.0"}]).encode("utf-8")
        fake_response = MagicMock()
        fake_response.read.return_value = fake_data
        fake_response.__enter__ = MagicMock(return_value=fake_response)
        fake_response.__exit__ = MagicMock(return_value=False)

        with patch.object(module, "urlopen", return_value=fake_response):
            result = module._fetch_json("http://example.com/tags")
        self.assertEqual(result, [{"name": "v1.0.0"}])

    def test_fetch_json_http_error(self):
        module = _load_module()
        from urllib.error import HTTPError
        with patch.object(
            module, "urlopen",
            side_effect=HTTPError("http://example.com", 500, "Error", {}, None),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                module._fetch_json("http://example.com/tags")
        self.assertIn("HTTP error 500", str(ctx.exception))


class CheckUpstreamVersionsScriptTests(unittest.TestCase):
    """Tests for the CLI script behavior."""

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--output-json", result.stdout)

    def test_runs_with_mocked_github(self):
        module = _load_module()

        def fake_latest_tag(url: str) -> str:
            if "ComfyUI_Frontend" in url:
                return "v1.42.11"
            return "v0.19.3"

        with patch.object(module, "_latest_tag_from_github", side_effect=fake_latest_tag):
            with patch("sys.argv", ["check_upstream_versions.py"]):
                result = module.main()

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
