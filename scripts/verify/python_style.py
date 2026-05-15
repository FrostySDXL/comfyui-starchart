#!/usr/bin/env python3
"""Run the repo's blocking Python style gate with Ruff."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TARGETS = ["scripts", "tests"]


def run_step(cmd: list[str], description: str) -> bool:
    """Run one Ruff step and report a concise result."""
    print(f"\n=== {description} ===")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    if result.stdout:
        print(result.stdout.rstrip())
    if result.returncode != 0:
        print(f"FAILED: {description}", file=sys.stderr)
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr)
        return False
    print(f"OK: {description}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the blocking Ruff-based Python style checks for this repo."
    )
    parser.parse_args()

    steps = [
        ([sys.executable, "-m", "ruff", "check", *TARGETS], "Ruff lint check"),
        (
            [sys.executable, "-m", "ruff", "format", "--check", *TARGETS],
            "Ruff format check",
        ),
    ]

    for cmd, description in steps:
        if not run_step(cmd, description):
            return 1

    print("\n=== Python style verification passed ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
