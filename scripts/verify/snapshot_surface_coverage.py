#!/usr/bin/env python3
"""Verify current pinned snapshots satisfy the required source surface."""

import ast
import json
from pathlib import Path

from scripts.common import snapshot_surface

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCES_RAW_DIR = REPO_ROOT / "references" / "raw"
SNAPSHOTS_DIR = REPO_ROOT / "references" / "snapshots"


def _repo_relative(path: Path) -> str:
    """Return a repo-relative path using forward slashes."""
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _snapshot_root_from_source(source: str, marker: str) -> Path | None:
    """Return the snapshot root containing ``marker`` from a metadata source path."""
    parts = Path(source).parts
    for index, part in enumerate(parts):
        if part.startswith(marker):
            return REPO_ROOT / Path(*parts[: index + 1])
    return None


def _metadata_sources() -> list[str]:
    """Collect source paths from canonical raw artifact metadata."""
    sources: list[str] = []
    for raw_path in sorted(REFERENCES_RAW_DIR.glob("*.json")):
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        metadata = payload.get("metadata", {})
        for source in metadata.get("sources", []):
            if isinstance(source, str):
                sources.append(source)
    return sources


def _fallback_snapshot_root(prefix: str) -> Path | None:
    """Find the newest checked-in snapshot directory for ``prefix``."""
    candidates = sorted(SNAPSHOTS_DIR.glob(f"*/{prefix}*"), reverse=True)
    return candidates[0] if candidates else None


def find_current_snapshot_roots() -> tuple[Path | None, Path | None]:
    """Find current core and frontend snapshot roots from metadata or fallback scan."""
    core_root: Path | None = None
    frontend_root: Path | None = None
    for source in _metadata_sources():
        core_root = core_root or _snapshot_root_from_source(source, "comfyui-core-")
        frontend_root = frontend_root or _snapshot_root_from_source(source, "comfyui-frontend-")
    return (
        core_root or _fallback_snapshot_root("comfyui-core-"),
        frontend_root or _fallback_snapshot_root("comfyui-frontend-"),
    )


def missing_required_paths(root: Path | None, required_files: list[str]) -> list[str]:
    """Return repo-relative missing required files for a snapshot root."""
    if root is None:
        return [f"<missing snapshot root>/{rel_path}" for rel_path in required_files]
    return [
        _repo_relative(root / rel_path)
        for rel_path in required_files
        if not (root / rel_path).exists()
    ]


def server_imports_binary_event_types(server_path: Path) -> bool:
    """Return whether server.py imports BinaryEventTypes from protocol via AST."""
    tree = ast.parse(server_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "protocol":
            if any(alias.name == "BinaryEventTypes" for alias in node.names):
                return True
    return False


def validate_snapshot_surface(core_root: Path | None, frontend_root: Path | None) -> list[str]:
    """Return explicit failures for incomplete snapshot source surfaces."""
    failures: list[str] = []
    failures.extend(missing_required_paths(core_root, snapshot_surface.CORE_REQUIRED_FILES))
    failures.extend(missing_required_paths(frontend_root, snapshot_surface.FRONTEND_REQUIRED_FILES))

    if core_root is not None:
        server_path = core_root / "server.py"
        protocol_path = core_root / "protocol.py"
        if server_path.exists() and server_imports_binary_event_types(server_path):
            if not protocol_path.exists():
                failures.append(_repo_relative(protocol_path))
        progress_path = core_root / "comfy_execution" / "progress.py"
        if not progress_path.exists():
            failures.append(_repo_relative(progress_path))

    return sorted(set(failures))


def _snapshot_version(root: Path | None, prefix: str) -> str:
    """Return the upstream version suffix visible in a snapshot root."""
    if root is None:
        return "missing"
    name = root.name
    return name.removeprefix(prefix) if name.startswith(prefix) else name


def _first_child_with_prefix(snapshot_dir: Path, prefix: str) -> Path | None:
    """Return the first child directory whose name starts with ``prefix``."""
    matches = sorted(path for path in snapshot_dir.glob(f"{prefix}*") if path.is_dir())
    return matches[0] if matches else None


def classify_snapshot_inventory(
    snapshots_root: Path,
    current_core_root: Path | None,
    current_frontend_root: Path | None,
) -> list[dict[str, str]]:
    """Classify dated snapshot directories for maintainer inventory tables.

    The blocking verifier continues to validate only the current pinned baseline.
    This helper is advisory inventory logic for documenting historical snapshot
    suitability without making old partial captures block refresh verification.
    """
    rows: list[dict[str, str]] = []
    current_date = None
    if current_core_root is not None:
        current_date = current_core_root.parent.name
    elif current_frontend_root is not None:
        current_date = current_frontend_root.parent.name

    for snapshot_dir in sorted(path for path in snapshots_root.iterdir() if path.is_dir()):
        core_root = _first_child_with_prefix(snapshot_dir, "comfyui-core-")
        frontend_root = _first_child_with_prefix(snapshot_dir, "comfyui-frontend-")
        missing = validate_snapshot_surface(core_root, frontend_root)
        if snapshot_dir.name == current_date:
            completeness_class = (
                "current-required-complete" if not missing else "current-required-incomplete"
            )
            role = "current active pinned baseline"
            suitability = (
                "suitable for current extraction"
                if not missing
                else "not suitable for current extraction until required files are restored"
            )
        elif missing:
            completeness_class = "historical-partial"
            role = "historical retained snapshot"
            suitability = "not suitable for extraction without backfill"
        else:
            completeness_class = "historical-complete-known"
            role = "historical retained snapshot"
            suitability = "suitable for historical extraction if needed"

        rows.append(
            {
                "snapshot_date": snapshot_dir.name,
                "core_version": _snapshot_version(core_root, "comfyui-core-"),
                "frontend_version": _snapshot_version(frontend_root, "comfyui-frontend-"),
                "role": role,
                "completeness_class": completeness_class,
                "extraction_suitability": suitability,
            }
        )
    return rows


def main() -> int:
    """CLI entry point."""
    core_root, frontend_root = find_current_snapshot_roots()
    failures = validate_snapshot_surface(core_root, frontend_root)
    if failures:
        print("Snapshot surface coverage failed. Missing required paths:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    assert core_root is not None
    assert frontend_root is not None
    print("Snapshot surface coverage passed.")
    print(f"Core snapshot: {_repo_relative(core_root)}")
    print(f"Frontend snapshot: {_repo_relative(frontend_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
