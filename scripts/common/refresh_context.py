"""Shared refresh orchestration context for snapshot refresh helpers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CommandRunner = Callable[[list[str], str, str | None], Any]


@dataclass(frozen=True)
class RefreshContext:
    """Paths and callbacks used by refresh snapshot orchestration wrappers."""

    repo_root: Path
    references_dir: Path
    references_raw_dir: Path
    snapshots_dir: Path
    scripts_extract_dir: Path
    scripts_generate_dir: Path
    provenance_output_path: Path
    python_executable: str
    run_cmd: CommandRunner
