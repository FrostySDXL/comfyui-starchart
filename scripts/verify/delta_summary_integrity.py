#!/usr/bin/env python3
"""Verify that delta-summary.json covers every canonical artifact family.

Usage:
    python scripts/verify/delta_summary_integrity.py

Exits 0 when public/artifacts/delta-summary.json has one top-level artifact
section for every canonical artifact listed by generate_snapshot_delta_summary.py,
passes its published schema, and matches regenerated output unless explicitly
skipped for archival comparisons.
Exits 1 when a section is missing, unexpected, stale, or unreadable.
"""

import argparse
import json
import sys
from pathlib import Path

from scripts.common.display_path import display_path
from scripts.generate.generate_snapshot_delta_summary import (
    CANONICAL_ARTIFACTS,
    _artifact_map,
    _comparison_source_kind,
    _current_raw_label,
    _raw_backup_label,
    build_delta_summary,
)
from scripts.verify.published_schema_validation import validate_against_published_artifact_schema

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DELTA_SUMMARY = REPO_ROOT / "public" / "artifacts" / "delta-summary.json"
PUBLISHED_SCHEMA_DIR = REPO_ROOT / "public" / "artifacts" / "schemas"


def _artifact_section_name(artifact_name: str) -> str:
    return artifact_name.removesuffix(".json")


def expected_artifact_sections() -> set[str]:
    """Return delta-summary top-level artifact sections required by canonical artifacts."""
    return {_artifact_section_name(name) for name in CANONICAL_ARTIFACTS}


def _read_delta_summary(summary_path: Path) -> tuple[dict | None, list[str]]:
    if not summary_path.exists():
        return None, [f"Missing delta summary: {display_path(summary_path)}"]

    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return None, [f"Failed to read delta summary {display_path(summary_path)}: {exc}"]
    if not isinstance(summary, dict):
        return None, [f"Delta summary top-level value is invalid: {display_path(summary_path)}"]
    return summary, []


def _resolve_comparison_path(path_value: str, summary_path: Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    candidate = REPO_ROOT / path
    if candidate.exists():
        return candidate
    return summary_path.parent / path


def verify_delta_summary_integrity(summary_path: Path) -> list[str]:
    """Return section-membership and schema-validity errors for a delta summary."""
    summary, errors = _read_delta_summary(summary_path)
    if errors or summary is None:
        return errors

    errors.extend(
        validate_against_published_artifact_schema(
            summary,
            "delta-summary.json",
            PUBLISHED_SCHEMA_DIR,
        )
    )
    artifacts = summary.get("artifacts")
    if not isinstance(artifacts, dict):
        errors.extend(
            [f"Delta summary artifacts block is missing or invalid: {display_path(summary_path)}"]
        )
        return errors

    expected = expected_artifact_sections()
    observed = set(artifacts)
    errors.extend(
        [
            f"Missing delta-summary artifact section for {section}"
            for section in sorted(expected - observed)
        ]
    )
    errors.extend(
        f"Unexpected delta-summary artifact section {section}"
        for section in sorted(observed - expected)
    )
    return errors


def regenerate_delta_summary_for_comparison(summary_path: Path) -> list[str]:
    """Return errors when checked-in delta summary differs from regenerated output."""
    summary, errors = _read_delta_summary(summary_path)
    if errors or summary is None:
        return errors

    comparison = summary.get("comparison")
    if not isinstance(comparison, dict):
        return [
            f"Delta summary comparison block is missing or invalid: {display_path(summary_path)}"
        ]

    old_value = comparison.get("old")
    new_value = comparison.get("new")
    if not isinstance(old_value, str) or not isinstance(new_value, str):
        return [f"Delta summary comparison old/new paths are invalid: {display_path(summary_path)}"]

    old_dir = _resolve_comparison_path(old_value, summary_path)
    new_dir = _resolve_comparison_path(new_value, summary_path)
    missing = [path for path in (old_dir, new_dir) if not path.is_dir()]
    if missing:
        return [
            "Delta summary regenerated-equality check cannot run because comparison "
            f"path is missing: {display_path(missing[0])}"
        ]

    try:
        old_artifacts = _artifact_map(old_dir)
        new_artifacts = _artifact_map(new_dir)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        return [f"Delta summary regeneration failed: {exc}"]

    regenerated = build_delta_summary(
        old_artifacts,
        new_artifacts,
        Path(old_value).as_posix(),
        Path(new_value).as_posix(),
        methodology=comparison.get("methodology", "artifact-directory-to-artifact-directory"),
        source_kind=_comparison_source_kind(Path(old_value), Path(new_value)),
        comparison_old_label=_raw_backup_label(Path(old_value)),
        comparison_new_label=_current_raw_label(Path(new_value), new_artifacts),
    )
    rendered = json.dumps(regenerated, indent=2, ensure_ascii=False) + "\n"
    current = summary_path.read_text(encoding="utf-8")
    if rendered != current:
        return [
            f"Delta summary is stale: regenerated output differs from {display_path(summary_path)}"
        ]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify public/artifacts/delta-summary.json covers canonical artifacts, "
            "passes schema validation, and matches regenerated output."
        )
    )
    parser.add_argument(
        "--summary-path",
        default=str(DEFAULT_DELTA_SUMMARY),
        help="Path to public/artifacts/delta-summary.json",
    )
    parser.add_argument(
        "--skip-regeneration",
        action="store_true",
        help=(
            "Skip regenerated-equality check (use for archival cases where comparison "
            "paths are intentionally absent)"
        ),
    )
    args = parser.parse_args(argv)

    summary_path = Path(args.summary_path)
    errors = verify_delta_summary_integrity(summary_path)
    if not args.skip_regeneration:
        errors.extend(regenerate_delta_summary_for_comparison(summary_path))
    if errors:
        print("Delta summary integrity verification failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    if args.skip_regeneration:
        print("Delta summary integrity verified for canonical artifacts; regeneration skipped.")
    else:
        print("Delta summary integrity verified for canonical artifacts and regenerated output.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
