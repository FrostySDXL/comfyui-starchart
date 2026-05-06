"""Tests for scripts/check_upstream_versions.py."""

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check_upstream_versions.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_upstream_versions", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CheckUpstreamVersionsUnitTests(unittest.TestCase):
    """Direct unit tests for check_upstream_versions functions."""

    def test_parse_version_tag_valid_semver(self):
        module = _load_module()
        self.assertEqual(module._parse_version_tag("v1.44.13"), (1, 44, 13))

    def test_parse_version_tag_requires_v_prefix(self):
        module = _load_module()
        self.assertIsNone(module._parse_version_tag("1.44.13"))

    def test_parse_version_tag_rejects_non_version_string(self):
        module = _load_module()
        self.assertIsNone(module._parse_version_tag("main"))

    def test_parse_version_tag_rejects_non_digit_suffix(self):
        module = _load_module()
        self.assertIsNone(module._parse_version_tag("v1.2.3-beta"))

    def test_is_newer_version_returns_false_for_none(self):
        module = _load_module()
        self.assertFalse(module._is_newer_version("v1.44.13", None))

    def test_is_newer_version_uses_tuple_fallback_when_packaging_cannot_parse(self):
        module = _load_module()
        with patch.object(module, "Version", side_effect=module.InvalidVersion("bad version")):
            self.assertTrue(module._is_newer_version("v1.2.3", "v1.2.4"))

    def test_is_newer_version_treats_prerelease_as_older_than_stable(self):
        module = _load_module()
        self.assertFalse(module._is_newer_version("v1.0.0", "v1.0.0-rc1"))

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

    def test_build_summary_older_latest_version_does_not_report_update(self):
        module = _load_module()
        summary = module._build_summary(
            {"version": "v0.20.1", "commit": "abc"},
            "v0.19.3",
            {"version": "v1.44.13", "commit": "def"},
            "v1.44.13",
        )
        self.assertFalse(summary["any_update_available"])
        self.assertFalse(summary["components"][0]["update_available"])
        self.assertEqual(summary["components"][0]["suggested_refresh_command"], "")

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
        with patch.object(module.http_utils, "get_json", return_value=[{"name": "v1.0.0"}]):
            result = module._fetch_json("http://example.com/tags")
        self.assertEqual(result, [{"name": "v1.0.0"}])

    def test_fetch_json_http_error(self):
        module = _load_module()
        with patch.object(module.http_utils, "get_json", side_effect=RuntimeError("HTTP error 500 from http://example.com/tags: Error")):
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
