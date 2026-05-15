from pathlib import Path


def normalize_repo_path(value: str | Path) -> str:
    return str(value).replace("\\", "/")


def has_backslashes(value: str | Path) -> bool:
    return "\\" in str(value)


def normalize_repo_relative_path(value: str | Path, repo_root: str | Path) -> str:
    normalized = normalize_repo_path(value)
    repo_prefix = normalize_repo_path(repo_root).rstrip("/") + "/"
    if normalized.startswith(repo_prefix):
        return normalized[len(repo_prefix) :]
    return normalized
