#!/usr/bin/env python3
"""One-command blocking verification wrapper for maintainers.

Runs the default local pre-push sequence in the same blocking order as the
cross-platform CI blocking path (ubuntu-latest and windows-latest):
    1. Unit tests
    2. Node-side tests
    3. python_style.py
    4. cross_references.py
    5. docs_index_freshness.py
    6. validate_schema.py
    7. verify_artifact_integrity.py
    8. markdown_top_level_spacing.py
    9. sidebar_navigation_coverage.py
    10. astro check
    11. astro build
    12. rendered_links.py

Advisory/non-blocking checks remain separate and are not included here.

Usage:
    python scripts/verify/run_all.py
    python scripts/verify/run_all.py --skip-tests

Exits 0 on success, exits 1 on the first blocking failure.
"""

import argparse
import sys
from pathlib import Path

from scripts.common.subprocess_utils import run_step

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_VERIFY_DIR = REPO_ROOT / "scripts" / "verify"
NPM_EXECUTABLE = "npm.cmd" if sys.platform == "win32" else "npm"


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
        help="Skip Python and Node test suites during focused iteration; rerun the full wrapper before push.",
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
                [NPM_EXECUTABLE, "test"],
                "Node-side tests",
            )
        )

    steps.append(
        (
            [sys.executable, str(SCRIPTS_VERIFY_DIR / "python_style.py")],
            "Python style verification",
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
            [sys.executable, str(SCRIPTS_VERIFY_DIR / "sidebar_navigation_coverage.py")],
            "Sidebar navigation coverage",
        )
    )

    steps.append(
        (
            [NPM_EXECUTABLE, "run", "check"],
            "Astro check",
        )
    )

    steps.append(
        (
            [NPM_EXECUTABLE, "run", "build"],
            "Astro build",
        )
    )

    steps.append(
        (
            [sys.executable, str(SCRIPTS_VERIFY_DIR / "rendered_links.py")],
            "Rendered links verification",
        )
    )

    for cmd, description in steps:
        if not run_step(cmd, description, cwd=str(REPO_ROOT)):
            return 1

    print("\n=== All verification steps passed ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
