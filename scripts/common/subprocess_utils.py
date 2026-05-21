from __future__ import annotations

import subprocess
import sys


def run_step(cmd: list[str], description: str, cwd: str | None = None) -> bool:
    """Run a command and print a concise success or failure record."""
    print(f"\n=== {description} ===")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if result.stdout:
        print(result.stdout.rstrip())
    if result.returncode != 0:
        print(f"FAILED: {description}", file=sys.stderr)
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr)
        return False
    print(f"OK: {description}")
    return True
