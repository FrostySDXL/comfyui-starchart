"""Snapshot source surface contract for pinned upstream inputs."""

from pathlib import Path

CORE_REQUIRED_FILES = [
    "server.py",
    "execution.py",
    "protocol.py",
    "comfy_execution/progress.py",
    "pyproject.toml",
    "requirements.txt",
    "app/frontend_management.py",
    "comfy_api/latest/_io.py",
    "comfy_api/latest/_input/basic_types.py",
]

FRONTEND_REQUIRED_FILES = [
    "package.json",
    "src/scripts/app.ts",
    "src/types/comfy.ts",
    "src/services/litegraphService.ts",
]

CORE_INCLUDE_GLOBS = [
    "*.py",
    "app/**/*.py",
    "comfy_execution/**/*.py",
    "comfy_api/latest/**/*.py",
]

FRONTEND_INCLUDE_GLOBS = [
    "src/scripts/**/*.ts",
    "src/scripts/**/*.tsx",
    "src/types/**/*.ts",
    "src/types/**/*.tsx",
    "src/services/**/*.ts",
    "src/services/**/*.tsx",
    "src/api/**/*.ts",
    "src/api/**/*.tsx",
]


def _normalize_relative_path(path: Path) -> str:
    """Return a forward-slash relative path string."""
    return path.as_posix()


def resolve_snapshot_files(
    root: Path,
    required_files: list[str],
    include_globs: list[str],
) -> tuple[list[str], list[str]]:
    """Resolve required and controlled-glob snapshot files under ``root``.

    Returns ``(resolved_files, missing_required_files)``. Paths are repo-local to
    ``root``, forward-slash normalized, sorted, and de-duplicated. Missing glob
    matches are ignored; missing required files are reported separately.
    """
    resolved: set[str] = set()
    missing_required: list[str] = []

    for rel_path in required_files:
        normalized = rel_path.replace("\\", "/")
        if (root / normalized).exists():
            resolved.add(normalized)
        else:
            missing_required.append(normalized)

    for pattern in include_globs:
        for match in root.glob(pattern):
            if match.is_file():
                resolved.add(_normalize_relative_path(match.relative_to(root)))

    return sorted(resolved), sorted(set(missing_required))
