import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def normalize_repo_path(value: str | Path) -> str:
    return str(value).replace("\\", "/")


def normalize_to_posix(value: str | Path) -> str:
    """Alias for normalizing repo-local path text to forward slashes."""
    return normalize_repo_path(value)


def has_backslashes(value: str | Path) -> bool:
    return "\\" in str(value)


def normalize_repo_relative_path(value: str | Path, repo_root: str | Path) -> str:
    normalized = normalize_repo_path(value)
    repo_prefix = normalize_repo_path(repo_root).rstrip("/") + "/"
    if normalized.startswith(repo_prefix):
        return normalized[len(repo_prefix) :]
    return normalized
