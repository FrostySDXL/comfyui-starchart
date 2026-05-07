#!/usr/bin/env python3
"""One-command blocking verification wrapper for maintainers.

Runs the default local pre-push sequence in the same blocking order as the
cross-platform CI blocking path (ubuntu-latest and windows-latest):
    1. Unit tests
    2. cross_references.py
    3. docs_index_freshness.py
    4. validate_schema.py
    5. verify_artifact_integrity.py
    6. markdown_top_level_spacing.py
    7. community_generated_freshness.py
    8. community_page_coverage.py
    9. mkdocs build

Advisory/non-blocking checks remain separate and are not included here.

Usage:
    python scripts/verify/run_all.py
    python scripts/verify/run_all.py --skip-tests
    python scripts/verify/run_all.py --skip-mkdocs

Exits 0 on success, exits 1 on the first blocking failure.
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_VERIFY_DIR = REPO_ROOT / "scripts" / "verify"


def run_step(cmd: list[str], description: str, cwd: str | None = None) -> bool:
    """Run a command and report success or failure."""
    print(f"\n=== {description} ===")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        print(f"FAILED: {description}", file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return False
    print(f"OK: {description}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the default blocking local verification sequence before push.",
        epilog=(
            "Mirrors the main CI job's blocking checks. Advisory checks such as "
            "stale_content.py and extraction_idempotency.py stay separate."
        ),
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip unit tests during focused iteration; rerun the full wrapper before push.",
    )
    parser.add_argument(
        "--skip-mkdocs",
        action="store_true",
        help="Skip the docs build during focused iteration; rerun the full wrapper before push.",
    )
    args = parser.parse_args()

    steps = []

    if not args.skip_tests:
        steps.append(
            (
                [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                "Unit tests",
            )
        )

    steps.append(
        (
            [sys.executable, str(SCRIPTS_VERIFY_DIR / "cross_references.py")],
            "Cross-reference verification",
        )
    )

    steps.append(
        (
            [sys.executable, str(SCRIPTS_VERIFY_DIR / "docs_index_freshness.py")],
            "Docs index freshness verification",
        )
    )

    steps.append(
        (
            [sys.executable, str(SCRIPTS_VERIFY_DIR / "validate_schema.py")],
            "Schema validation",
        )
    )

    steps.append(
        (
            [sys.executable, str(SCRIPTS_VERIFY_DIR / "verify_artifact_integrity.py")],
            "Artifact integrity verification",
        )
    )

    steps.append(
        (
            [sys.executable, str(SCRIPTS_VERIFY_DIR / "markdown_top_level_spacing.py")],
            "Markdown top-level spacing verification",
        )
    )

    steps.append(
        (
            [sys.executable, str(SCRIPTS_VERIFY_DIR / "community_generated_freshness.py")],
            "Generated community page freshness",
        )
    )

    steps.append(
        (
            [sys.executable, str(SCRIPTS_VERIFY_DIR / "community_page_coverage.py")],
            "Community page coverage",
        )
    )

    if not args.skip_mkdocs:
        steps.append(
            (
                [sys.executable, "-m", "mkdocs", "build"],
                "MkDocs build",
            )
        )

    for cmd, description in steps:
        if not run_step(cmd, description, cwd=str(REPO_ROOT)):
            return 1

    print("\n=== All verification steps passed ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
