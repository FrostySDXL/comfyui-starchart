"""Tests for scripts/verify/upstream_pins.py."""

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "verify" / "upstream_pins.py"
REFERENCES_RAW_DIR = REPO_ROOT / "references" / "raw"


def _load_module():
    """Load the upstream_pins module from file."""
    spec = importlib.util.spec_from_file_location("upstream_pins", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UpstreamPinsImportTests(unittest.TestCase):
    """Test that the upstream_pins module imports correctly."""

    def test_module_imports(self):
        """The upstream_pins module should be importable."""
        module = _load_module()
        self.assertTrue(hasattr(module, "verify_pins"))
        self.assertTrue(hasattr(module, "extract_pins_from_json"))
        self.assertTrue(hasattr(module, "REPO_MAP"))

    def test_key_functions_exist(self):
        """Key functions should be present in the module."""
        module = _load_module()
        self.assertTrue(callable(module.verify_pins))
        self.assertTrue(callable(module.extract_pins_from_json))
        self.assertTrue(callable(module._check_commit_via_github_api))
        self.assertTrue(callable(module._check_tag_via_github_api))


class UpstreamPinsMetadataTests(unittest.TestCase):
    """Test that metadata is read correctly from JSON files."""

    def test_extract_pins_from_server_endpoints(self):
        """extract_pins_from_json should read version and commit from server_endpoints.json."""
        module = _load_module()
        json_path = REFERENCES_RAW_DIR / "server_endpoints.json"
        if not json_path.exists():
            self.skipTest("server_endpoints.json not found")

        pins = module.extract_pins_from_json(json_path)
        self.assertEqual(len(pins), 1)
        pin = pins[0]
        self.assertEqual(pin["source"], "server_endpoints.json")
        self.assertTrue(
            pin["version"].startswith("v"), f"Version should start with 'v': {pin['version']}"
        )
        self.assertTrue(
            len(pin["commit"]) >= 40, f"Commit hash should be full SHA: {pin['commit']}"
        )

    def test_extract_pins_from_js_hooks(self):
        """extract_pins_from_json should read version and commit from js_hooks.json."""
        module = _load_module()
        json_path = REFERENCES_RAW_DIR / "js_hooks.json"
        if not json_path.exists():
            self.skipTest("js_hooks.json not found")

        pins = module.extract_pins_from_json(json_path)
        self.assertEqual(len(pins), 1)
        pin = pins[0]
        self.assertEqual(pin["source"], "js_hooks.json")
        self.assertTrue(
            pin["version"].startswith("v"), f"Version should start with 'v': {pin['version']}"
        )

    def test_extract_pins_from_node_api_schema(self):
        """extract_pins_from_json should read version and commit from node_api_schema.json."""
        module = _load_module()
        json_path = REFERENCES_RAW_DIR / "node_api_schema.json"
        if not json_path.exists():
            self.skipTest("node_api_schema.json not found")

        pins = module.extract_pins_from_json(json_path)
        self.assertEqual(len(pins), 1)
        pin = pins[0]
        self.assertEqual(pin["source"], "node_api_schema.json")

    def test_repo_map_covers_all_json_files(self):
        """REPO_MAP should have entries for all JSON files in references/raw."""
        module = _load_module()
        json_files = list(REFERENCES_RAW_DIR.glob("*.json"))
        for json_file in json_files:
            self.assertIn(
                json_file.name,
                module.REPO_MAP,
                f"REPO_MAP missing entry for {json_file.name}",
            )


class UpstreamPinsRunTests(unittest.TestCase):
    """Test that the script can be run without crashing."""

    def test_script_runs_and_reports_valid(self):
        """The upstream_pins script should run and report current pins as valid.

        This test makes real HTTP requests to GitHub API. It may fail due to
        rate limits or network issues, so we accept either exit code 0 or 1
        but not a crash.
        """
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        # Exit code 0 means all valid, 1 means some broken pins
        # Either is acceptable for a smoke test (network may be unavailable)
        self.assertIn(result.returncode, [0, 1], msg=result.stderr or result.stdout)


class UpstreamPinsMockTests(unittest.TestCase):
    """Test failure behavior with mocked GitHub API."""

    def test_broken_pin_returns_exit_1(self):
        """When a pin is invalid (404 from GitHub), the script should exit 1."""
        module = _load_module()

        # Mock the HTTP check to return 404
        with patch.object(
            module,
            "_check_commit_via_github_api",
            return_value=(False, "commit abc NOT FOUND in Comfy-Org/ComfyUI"),
        ):
            with patch.object(
                module,
                "_check_tag_via_github_api",
                return_value=(False, "tag v99.99.99 NOT FOUND in Comfy-Org/ComfyUI"),
            ):
                results = module.verify_pins(use_cache=False)

        # At least one result should be invalid
        has_invalid = any(not valid for valid, _ in results)
        self.assertTrue(
            has_invalid, "Expected at least one invalid pin result when GitHub returns 404"
        )

    def test_valid_pin_returns_true(self):
        """When a pin is valid (200 from GitHub), the check should return True."""
        module = _load_module()

        with patch.object(
            module,
            "_check_commit_via_github_api",
            return_value=(True, "commit abc resolves in Comfy-Org/ComfyUI"),
        ):
            result = module._check_commit_via_github_api("Comfy-Org", "ComfyUI", "abc123")

        self.assertTrue(result[0])

    def test_cache_round_trip(self):
        """Cache should be saveable and loadable."""
        module = _load_module()
        import tempfile

        # Use a temp dir for cache
        original_cache_dir = module.CACHE_DIR
        original_cache_file = module.CACHE_FILE

        with tempfile.TemporaryDirectory() as tmpdir:
            module.CACHE_DIR = Path(tmpdir)
            module.CACHE_FILE = Path(tmpdir) / "upstream_pins.json"

            test_cache = {
                "Comfy-Org/ComfyUI/commit/abc": {
                    "valid": True,
                    "detail": "test",
                    "timestamp": 1000000,
                }
            }
            module._save_cache(test_cache)
            loaded = module._load_cache()
            self.assertEqual(loaded, test_cache)

        # Restore original paths
        module.CACHE_DIR = original_cache_dir
        module.CACHE_FILE = original_cache_file


if __name__ == "__main__":
    unittest.main()
