"""Tests for examples/extensions/minimal-route-registration README invocation."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "examples" / "extensions" / "minimal-route-registration" / "__init__.py"


class MinimalRouteRegistrationTests(unittest.TestCase):
    """Ensure the documented hyphenated-path import shape is executable."""

    def test_readme_spec_from_file_location_snippet_calls_main(self):
        spec = importlib.util.spec_from_file_location("minimal_route_registration", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.assertIsNone(module.main())


if __name__ == "__main__":
    unittest.main()
