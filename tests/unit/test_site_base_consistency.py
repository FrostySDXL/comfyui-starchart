"""Tests for shared site base configuration consistency."""

import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_module():
    """Load the site_base_consistency verifier module."""
    spec = importlib.util.spec_from_file_location(
        "site_base_consistency",
        REPO_ROOT / "scripts" / "verify" / "site_base_consistency.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCrossLanguageSiteBaseFormula(unittest.TestCase):
    """Assert the Python formula matches the JavaScript helper contract."""

    def test_python_matches_javascript_for_subpath_with_trailing_slash(self):
        """A trailing base slash is stripped in the shared normalized site base."""
        module = load_module()

        self.assertEqual(
            module.normalize_site_base_no_trailing_slash(
                "https://example.com",
                "/docs/",
            ),
            "https://example.com/docs",
        )


class TestSiteBaseConfigConsistency(unittest.TestCase):
    """Validate the checked-in shared site config contract."""

    def test_site_config_has_exact_expected_keys(self):
        """The JSON config should expose only the shared site-base fields."""
        module = load_module()
        data = module.load_site_config()

        self.assertEqual(
            set(data),
            {"site", "base", "siteBaseNoTrailingSlash"},
        )

    def test_site_config_normalized_value_matches_formula(self):
        """The stored normalized value should be derived from site and base."""
        module = load_module()
        data = module.load_site_config()

        self.assertEqual(
            data["siteBaseNoTrailingSlash"],
            module.normalize_site_base_no_trailing_slash(data["site"], data["base"]),
        )


if __name__ == "__main__":
    unittest.main()
