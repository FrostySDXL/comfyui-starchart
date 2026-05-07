#!/usr/bin/env python3
"""Run a lightweight blocking-checks smoke through run_all.py.

This wrapper exercises the blocking maintainer verification pipeline in one
subprocess without recursively rerunning the unit test suite, equivalent to
running run_all.py with --skip-tests.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ALL_SCRIPT = REPO_ROOT / "scripts" / "verify" / "run_all.py"


def build_command(*, skip_mkdocs: bool) -> list[str]:
    command = [sys.executable, str(RUN_ALL_SCRIPT), "--skip-tests"]
    if skip_mkdocs:
        command.append("--skip-mkdocs")
    return command


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run a blocking-checks smoke through scripts/verify/run_all.py without "
            "rerunning unit tests (equivalent to run_all.py --skip-tests)."
        )
    )
    parser.add_argument(
        "--skip-mkdocs",
        action="store_true",
        help="Forward --skip-mkdocs to run_all.py for focused debugging.",
    )
    args = parser.parse_args()

    command = build_command(skip_mkdocs=args.skip_mkdocs)
    print(f"Running pipeline smoke: {' '.join(command)}")
    try:
        result = subprocess.run(command, capture_output=True, text=True, cwd=str(REPO_ROOT))
    except FileNotFoundError as exc:
        print(f"FAILED: unable to run pipeline smoke: {exc}", file=sys.stderr)
        return 1
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    if result.returncode == 0:
        print("Pipeline smoke passed.")
    else:
        print(f"Pipeline smoke failed with exit code {result.returncode}.", file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
