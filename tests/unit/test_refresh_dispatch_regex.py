"""Tests for refresh workflow dispatch version tag validation."""

import re
import unittest

VERSION_TAG_REGEX = r"^v[0-9]+\.[0-9]+\.[0-9]+\Z"


class RefreshDispatchRegexTests(unittest.TestCase):
    """Mirror the GitHub Actions refresh input version-tag policy."""

    def test_accepts_canonical_release_tags(self):
        for value in ("v0.22.0", "v0.22.10", "v1.0.0", "v100.200.300"):
            with self.subTest(value=value):
                self.assertIsNotNone(re.match(VERSION_TAG_REGEX, value))

    def test_rejects_non_canonical_tags(self):
        rejected_values = (
            "v0.22.0-rc.1",
            "v0.22.0.dev0",
            "v0.22",
            "0.22.0",
            "v0.22.0+build.1",
            "v0.22.0/",
            "",
            "   ",
            "v0.22.0\n",
        )

        for value in rejected_values:
            with self.subTest(value=value):
                self.assertIsNone(re.match(VERSION_TAG_REGEX, value))

    def test_match_and_fullmatch_acceptance_are_identical(self):
        values = (
            "v0.22.0",
            "v0.22.10",
            "v1.0.0",
            "v100.200.300",
            "v0.22.0-rc.1",
            "v0.22.0.dev0",
            "v0.22",
            "0.22.0",
            "v0.22.0+build.1",
            "v0.22.0/",
            "",
            "   ",
            "v0.22.0\n",
        )

        for value in values:
            with self.subTest(value=value):
                match_accepts = re.match(VERSION_TAG_REGEX, value) is not None
                fullmatch_accepts = re.fullmatch(VERSION_TAG_REGEX, value) is not None
                self.assertEqual(match_accepts, fullmatch_accepts)


if __name__ == "__main__":
    unittest.main()
