#!/usr/bin/env python3
"""Verify that delta-summary.json covers every canonical artifact family.

Usage:
    python scripts/verify/delta_summary_integrity.py

Exits 0 when public/artifacts/delta-summary.json has one top-level artifact
section for every canonical artifact listed by generate_snapshot_delta_summary.py.
Exits 1 when a section is missing, unexpected, or unreadable.
"""

import argparse
import json
import sys
from pathlib import Path

from scripts.common.display_path import display_path
from scripts.generate.generate_snapshot_delta_summary import CANONICAL_ARTIFACTS

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DELTA_SUMMARY = REPO_ROOT / "public" / "artifacts" / "delta-summary.json"


def _artifact_section_name(artifact_name: str) -> str:
    return artifact_name.removesuffix(".json")


def expected_artifact_sections() -> set[str]:
    """Return delta-summary top-level artifact sections required by canonical artifacts."""
    return {_artifact_section_name(name) for name in CANONICAL_ARTIFACTS}


def verify_delta_summary_integrity(summary_path: Path) -> list[str]:
    """Return integrity errors for a delta summary artifact."""
    if not summary_path.exists():
        return [f"Missing delta summary: {display_path(summary_path)}"]

    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [f"Failed to read delta summary {display_path(summary_path)}: {exc}"]

    artifacts = summary.get("artifacts")
    if not isinstance(artifacts, dict):
        return [
            f"Delta summary artifacts block is missing or invalid: {display_path(summary_path)}"
        ]

    expected = expected_artifact_sections()
    observed = set(artifacts)
    errors = [
        f"Missing delta-summary artifact section for {section}"
        for section in sorted(expected - observed)
    ]
    errors.extend(
        f"Unexpected delta-summary artifact section {section}"
        for section in sorted(observed - expected)
    )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify public/artifacts/delta-summary.json covers canonical artifacts."
    )
    parser.add_argument(
        "--summary-path",
        default=str(DEFAULT_DELTA_SUMMARY),
        help="Path to public/artifacts/delta-summary.json",
    )
    args = parser.parse_args()

    errors = verify_delta_summary_integrity(Path(args.summary_path))
    if errors:
        print("Delta summary integrity verification failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Delta summary integrity verified for canonical artifacts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
