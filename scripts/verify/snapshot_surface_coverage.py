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


def main() -> int:
    """CLI entry point."""
    core_root, frontend_root = find_current_snapshot_roots()
    failures = validate_snapshot_surface(core_root, frontend_root)
    if failures:
        print("Snapshot surface coverage failed. Missing required paths:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Snapshot surface coverage passed.")
    print(f"Core snapshot: {_repo_relative(core_root)}")
    print(f"Frontend snapshot: {_repo_relative(frontend_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
