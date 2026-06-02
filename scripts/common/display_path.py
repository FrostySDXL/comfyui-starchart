"""Render paths and command lists for non-leaking output.

Pure formatting. No I/O, no side effects.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable


def display_path(path: Path | str | None, *, repo_root: Path | None = None) -> str:
    """Return a stable, non-leaking string form of ``path``."""
    if path is None:
        return ""
    if repo_root is None:
        # Default repo root: this file's location's great-grandparent (scripts/common -> repo).
        repo_root = Path(__file__).resolve().parents[2]
    p = Path(path)
    try:
        return p.relative_to(repo_root).as_posix()
    except ValueError:
        return p.name


def display_command(cmd: Iterable[str]) -> str:
    """Render a subprocess command list with ``sys.executable`` replaced by 'python'
    and any absolute filesystem path arguments redacted to their basename."""
    parts = list(cmd)
    if parts and parts[0] == sys.executable:
        parts = ["python", *parts[1:]]
    parts = [p if not _looks_like_absolute_path(p) else display_path(p) for p in parts]
    return " ".join(parts)


def _looks_like_absolute_path(token: object) -> bool:
    """True if ``token`` is a string that ``Path`` treats as an absolute filesystem path.

    URLs like ``https://...`` are not absolute filesystem paths, so they pass through unchanged.
    """
    return isinstance(token, str) and Path(token).is_absolute()
