from __future__ import annotations

import logging
import subprocess
import sys

logger = logging.getLogger(__name__)

DEFAULT_VERIFIER_TIMEOUT_SECONDS = 120
DEFAULT_CLONE_TIMEOUT_SECONDS = 300


def _print_operator(message: str, *, file=None) -> None:
    print(message, file=file)


def run_step(
    cmd: list[str],
    description: str,
    cwd: str | None = None,
    timeout_seconds: int = DEFAULT_VERIFIER_TIMEOUT_SECONDS,
) -> bool:
    """Run a command and print a concise success or failure record.

    Verifier steps default to ``DEFAULT_VERIFIER_TIMEOUT_SECONDS`` (120 seconds).
    Slower clone/fetch call sites should pass ``DEFAULT_CLONE_TIMEOUT_SECONDS``
    (300 seconds) explicitly.
    """
    _print_operator(f"\n=== {description} ===")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        _print_operator(f"FAILED: {description}", file=sys.stderr)
        _print_operator(f"Timed out after {timeout_seconds}s", file=sys.stderr)
        if exc.stdout:
            _print_operator(str(exc.stdout).rstrip(), file=sys.stderr)
        if exc.stderr:
            _print_operator(str(exc.stderr).rstrip(), file=sys.stderr)
        return False
    if result.stdout:
        _print_operator(result.stdout.rstrip())
    if result.returncode != 0:
        _print_operator(f"FAILED: {description}", file=sys.stderr)
        if result.stderr:
            _print_operator(result.stderr.rstrip(), file=sys.stderr)
        return False
    _print_operator(f"OK: {description}")
    return True
