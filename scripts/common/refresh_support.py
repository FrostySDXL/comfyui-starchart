import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def repo_relative_path(path: Path | None, repo_root: Path) -> str | None:
    """Return a repo-relative path with forward slashes."""
    if path is None:
        return None
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def canonical_raw_artifacts_exist(references_raw_dir: Path) -> bool:
    """Return True when a prior canonical raw baseline exists."""
    return references_raw_dir.exists() and any(references_raw_dir.iterdir())


def create_pre_refresh_backup(
    references_dir: Path,
    references_raw_dir: Path,
    repo_root: Path,
) -> Path | None:
    """Create a repo-local backup of references/raw before mutation."""
    if not canonical_raw_artifacts_exist(references_raw_dir):
        return None

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = references_dir / f"raw_backup_{timestamp}"
    try:
        shutil.copytree(references_raw_dir, backup_dir)
    except OSError as exc:
        backup_path = repo_relative_path(backup_dir, repo_root)
        raise RuntimeError(f"Failed to create pre-refresh backup at {backup_path}: {exc}") from exc
    return backup_dir


def build_delta_summary_command(
    backup_dir: Path | None,
    repo_root: Path,
    python_executable: str,
) -> str | None:
    """Build the next-step delta-summary command for maintainers."""
    if backup_dir is None:
        return None
    backup_path = repo_relative_path(backup_dir, repo_root)
    return (
        f"{python_executable} scripts/generate/generate_snapshot_delta_summary.py "
        f'--old "{backup_path}" '
        f'--new "references/raw" '
        f'--output "docs/artifacts/delta-summary.json"'
    )


def build_refresh_provenance(
    *,
    refresh_date: str,
    requested_core_version: str | None,
    requested_frontend_version: str | None,
    resolved_core_commit: str | None,
    resolved_frontend_commit: str | None,
    backup_dir: Path | None,
    runtime_object_info_requested: bool,
    runtime_object_info_merged: bool,
    repo_root: Path,
    provenance_output_path: Path,
    python_executable: str,
) -> dict:
    """Build the durable refresh provenance payload."""
    return {
        "refresh_date": refresh_date,
        "requested_versions": {
            "core": requested_core_version,
            "frontend": requested_frontend_version,
        },
        "resolved_commits": {
            "core": resolved_core_commit,
            "frontend": resolved_frontend_commit,
        },
        "backup_location": repo_relative_path(backup_dir, repo_root),
        "runtime_object_info": {
            "requested": runtime_object_info_requested,
            "merged_into_node_api_schema": runtime_object_info_merged,
        },
        "published": {
            "provenance_path": repo_relative_path(provenance_output_path, repo_root),
            "manifest_included": False,
        },
        "next_steps": {
            "delta_summary_command": build_delta_summary_command(
                backup_dir,
                repo_root,
                python_executable,
            )
        },
    }


def write_refresh_provenance(
    payload: dict,
    provenance_output_path: Path,
    repo_root: Path,
) -> Path:
    """Write the refresh provenance payload to the published repo-local path."""
    try:
        provenance_output_path.parent.mkdir(parents=True, exist_ok=True)
        provenance_output_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        output_path = repo_relative_path(provenance_output_path, repo_root)
        raise RuntimeError(f"Failed to write refresh provenance to {output_path}: {exc}") from exc
    return provenance_output_path


def compute_diff_summary(old_json: dict, new_json: dict, json_name: str) -> list[str]:
    """Compare old and new JSON content and return a summary of changes."""
    changes = []

    if json_name == "server_endpoints.json":
        old_routes = {endpoint["route"] for endpoint in old_json.get("endpoints", [])}
        new_routes = {endpoint["route"] for endpoint in new_json.get("endpoints", [])}
        added = new_routes - old_routes
        removed = old_routes - new_routes
        if added:
            changes.append(f"  New endpoints: {sorted(added)}")
        if removed:
            changes.append(f"  Removed endpoints: {sorted(removed)}")
        if not added and not removed:
            changes.append(f"  No endpoint changes ({len(new_routes)} total)")

    elif json_name == "js_hooks.json":
        old_hooks = {hook["name"] for hook in old_json.get("hooks", [])}
        new_hooks = {hook["name"] for hook in new_json.get("hooks", [])}
        added = new_hooks - old_hooks
        removed = old_hooks - new_hooks
        if added:
            changes.append(f"  New hooks: {sorted(added)}")
        if removed:
            changes.append(f"  Removed hooks: {sorted(removed)}")
        if not added and not removed:
            changes.append(f"  No hook changes ({len(new_hooks)} total)")

    elif json_name == "node_api_schema.json":
        old_fields = set(old_json.get("object_info_fields", []))
        new_fields = set(new_json.get("object_info_fields", []))
        added = new_fields - old_fields
        removed = old_fields - new_fields
        if added:
            changes.append(f"  New object_info fields: {sorted(added)}")
        if removed:
            changes.append(f"  Removed object_info fields: {sorted(removed)}")

        old_types = {io_type["class_name"] for io_type in old_json.get("io_types", [])}
        new_types = {io_type["class_name"] for io_type in new_json.get("io_types", [])}
        added_types = new_types - old_types
        removed_types = old_types - new_types
        if added_types:
            changes.append(f"  New IO types: {sorted(added_types)}")
        if removed_types:
            changes.append(f"  Removed IO types: {sorted(removed_types)}")

        old_provenance = old_json.get("metadata", {}).get("provenance", {})
        new_provenance = new_json.get("metadata", {}).get("provenance", {})
        old_mode = old_provenance.get("mode", "source-only")
        new_mode = new_provenance.get("mode", "source-only")
        if old_mode != new_mode:
            changes.append(f"  Provenance mode changed: {old_mode} -> {new_mode}")

        old_runtime = old_json.get("runtime_object_info", {})
        new_runtime = new_json.get("runtime_object_info", {})
        old_count = len(old_runtime) if isinstance(old_runtime, dict) else 0
        new_count = len(new_runtime) if isinstance(new_runtime, dict) else 0
        if old_count != new_count:
            changes.append(f"  Runtime object_info node count: {old_count} -> {new_count}")

        if (
            not added
            and not removed
            and not added_types
            and not removed_types
            and old_mode == new_mode
            and old_count == new_count
        ):
            changes.append("  No schema changes")

    return changes
