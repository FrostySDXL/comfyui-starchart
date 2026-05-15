from __future__ import annotations

import importlib.util
import io
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def call_main(module, *args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    original_argv = sys.argv
    sys.argv = [getattr(module, "__file__", "module"), *args]
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                exit_code = module.main()
            except SystemExit as exc:
                exit_code = exc.code
    finally:
        sys.argv = original_argv
    if exit_code is None:
        exit_code = 0
    elif isinstance(exit_code, bool):
        exit_code = int(exit_code)
    elif not isinstance(exit_code, int):
        exit_code = 1
    return exit_code, stdout.getvalue(), stderr.getvalue()
