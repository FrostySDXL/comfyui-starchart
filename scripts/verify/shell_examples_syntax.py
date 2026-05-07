#!/usr/bin/env python3
"""Validate example shell scripts with bash -n."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = REPO_ROOT / "examples"


def discover_example_shell_scripts(repo_root: Path) -> list[Path]:
    examples_dir = repo_root / "examples"
    return sorted(path.relative_to(repo_root) for path in examples_dir.rglob("*.sh"))


def find_bash_executable() -> str | None:
    candidates = [
        shutil.which("bash"),
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    return None


def validate_shell_scripts(repo_root: Path, scripts: list[Path]) -> int:
    bash_executable = find_bash_executable()
    if bash_executable is None:
        print(
            "FAILED: unable to find a bash executable for shell example validation.",
            file=sys.stderr,
        )
        return 1

    if not scripts:
        print("No shell example scripts found.")
        return 0

    failed = False
    for script in scripts:
        print(f"Checking shell syntax: {script}")
        result = subprocess.run(
            [bash_executable, "-n", script.as_posix()],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
        )
        if result.returncode != 0:
            failed = True
            print(f"FAILED: {script}", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr, end="")

    if failed:
        return 1

    print(f"Validated {len(scripts)} shell example script(s) with bash -n.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate example shell scripts under examples/ with bash -n."
    )
    parser.parse_args()
    return validate_shell_scripts(REPO_ROOT, discover_example_shell_scripts(REPO_ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
