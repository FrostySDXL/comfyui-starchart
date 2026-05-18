"""Unit tests for scripts/verify/stale_content.py."""

import datetime
import importlib.util
import json
import tempfile
import unittest
from os import sep
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "stale_content.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("stale_content", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _repo_rel(*parts: str) -> str:
    return sep.join(parts)


class StaleContentUnitTests(unittest.TestCase):
    """Direct unit tests for stale content detection helpers."""

    def test_find_stale_in_json_detects_nested_markers(self):
        module = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            raw_dir = root / "references" / "raw"
            raw_dir.mkdir(parents=True)
            (raw_dir / "sample.json").write_text(
                json.dumps(
                    {
                        "outer": {
                            "items": [
                                "clean",
                                "TODO: replace this placeholder",
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )
            (raw_dir / "invalid.json").write_text("{not-json", encoding="utf-8")

            with (
                patch.object(module, "REFERENCES_RAW_DIR", raw_dir),
                patch.object(module.Path, "cwd", return_value=root),
            ):
                stale = module.find_stale_in_json()

        self.assertEqual(
            stale,
            [
                (
                    _repo_rel("references", "raw", "sample.json"),
                    0,
                    'outer.items[1]: TODO in "TODO: replace this placeholder"',
                )
            ],
        )

    def test_find_stale_in_markdown_detects_real_markers_only(self):
        module = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            docs_dir = root / "src" / "content" / "docs"
            docs_dir.mkdir(parents=True)
            (docs_dir / "sample.md").write_text(
                "\n".join(
                    [
                        "# Sample",
                        "```json",
                        '  "description": "TODO in code block should be ignored"',
                        "```",
                        "| TODO | table row should be ignored |",
                        "description TODO needs follow-up",
                        "DEPRECATED route note",
                        "TODO plain note should not be flagged",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with (
                patch.object(module, "DOCS_DIR", docs_dir),
                patch.object(module.Path, "cwd", return_value=root),
            ):
                stale = module.find_stale_in_markdown()

        self.assertEqual(
            stale,
            [
                (
                    _repo_rel("src", "content", "docs", "sample.md"),
                    6,
                    "description TODO needs follow-up",
                ),
                (_repo_rel("src", "content", "docs", "sample.md"), 7, "DEPRECATED route note"),
                (
                    _repo_rel("src", "content", "docs", "sample.md"),
                    8,
                    "TODO plain note should not be flagged",
                ),
            ],
        )

    def test_find_stale_dates_flags_old_last_updated_values(self):
        module = _load_module()
        today = datetime.date.today()
        old_date = today - datetime.timedelta(days=31)
        fresh_date = today - datetime.timedelta(days=5)

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            docs_dir = root / "src" / "content" / "docs"
            docs_dir.mkdir(parents=True)
            (docs_dir / "stale.md").write_text(
                f"**Last Updated:** {old_date.isoformat()}\n", encoding="utf-8"
            )
            (docs_dir / "fresh.md").write_text(
                f"**Last Updated:** {fresh_date.isoformat()}\n", encoding="utf-8"
            )

            with (
                patch.object(module, "DOCS_DIR", docs_dir),
                patch.object(module.Path, "cwd", return_value=root),
            ):
                stale = module.find_stale_dates(30)

        self.assertEqual(
            stale,
            [
                (
                    _repo_rel("src", "content", "docs", "stale.md"),
                    0,
                    f"Last Updated {old_date.isoformat()} exceeds 30-day threshold (cutoff {today - datetime.timedelta(days=30)})",
                )
            ],
        )

    def test_find_stale_version_refs_flags_older_versions_only(self):
        module = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            docs_dir = root / "src" / "content" / "docs"
            docs_dir.mkdir(parents=True)
            (docs_dir / "versions.md").write_text(
                "\n".join(
                    [
                        "Uses behavior from v0.19.3 only.",
                        "Migration notes from v0.19.3 to v0.20.1 are current.",
                        "Current pin is v0.20.1.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with (
                patch.object(module, "DOCS_DIR", docs_dir),
                patch.object(module.Path, "cwd", return_value=root),
            ):
                stale = module.find_stale_version_refs("v0.20.1")

        self.assertEqual(
            stale,
            [
                (
                    _repo_rel("src", "content", "docs", "versions.md"),
                    1,
                    "References older ComfyUI version v0.19.3 (current pin: v0.20.1): Uses behavior from v0.19.3 only.",
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
