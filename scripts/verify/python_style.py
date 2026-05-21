#!/usr/bin/env python3
"""Run the repo's blocking Python style gate with Ruff."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.common.subprocess_utils import run_step

REPO_ROOT = Path(__file__).resolve().parents[2]
TARGETS = ["scripts", "tests"]


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
        if not run_step(cmd, description, cwd=str(REPO_ROOT)):
            return 1

    print("\n=== Python style verification passed ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
