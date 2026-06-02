"""Render paths and command lists for non-leaking output.

Pure formatting. No I/O, no side effects.

Contract for ``display_path`` and ``display_command``:

- ``None`` and empty input render as the empty string.
- URL strings (anything containing the ``://`` URL-scheme separator) pass
  through unchanged. They are never reclassified as absolute filesystem
  paths, regardless of platform. Examples: ``https://github.com/...``,
  ``git://host/path``, ``ssh://host/path``, ``g://host/path`` (where a
  single-letter scheme could otherwise be misread as a Windows drive).
- Strings recognized as absolute filesystem paths and located inside the
  resolved repo root render as repo-relative POSIX paths.
- Strings recognized as absolute filesystem paths but outside the repo
  root render as their basename only.
- Relative filesystem paths render as their basename only (best-effort
  fallback when the path is not inside the repo root).
- For ``display_command``, the first element ``sys.executable`` is
  replaced with ``"python"``; absolute-path arguments are passed through
  ``display_path`` and therefore follow the rules above.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable


def _looks_like_url(token: object) -> bool:
    """True if ``token`` is a string that contains a URL-scheme separator.

    The presence of ``://`` is the universal marker for any URI scheme and
    is used here to defend against platform-specific misclassification of
    single-letter schemes (e.g. ``g://host/path``) as Windows drive
    letters.
    """
    return isinstance(token, str) and "://" in token


def display_path(path: Path | str | None, *, repo_root: Path | None = None) -> str:
    """Return a stable, non-leaking string form of ``path``.

    See the module docstring for the full contract. URL inputs and ``None``
    are handled before filesystem-path classification, so the basename
    fallback only ever fires on real filesystem paths.
    """
    if path is None:
        return ""
    # Empty string must behave identically to None per the module contract
    # ("None and empty input render as the empty string"). An explicit
    # guard here avoids depending on the accidental exception-fallback
    # behavior of Path("").
    if isinstance(path, str) and path == "":
        return ""
    if isinstance(path, Path) and not str(path):
        return ""
    if isinstance(path, str) and _looks_like_url(path):
        return path
    if repo_root is None:
        # Default repo root: this file's location's great-grandparent (scripts/common -> repo).
        repo_root = Path(__file__).resolve().parents[2]
    try:
        p = Path(path)
    except TypeError:
        return ""
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

    URLs (recognized by the ``://`` scheme separator) are never classified
    as absolute filesystem paths, even on platforms where ``Path`` happens
    to treat the leading component as a drive letter.
    """
    if not isinstance(token, str):
        return False
    if _looks_like_url(token):
        return False
    return Path(token).is_absolute()
