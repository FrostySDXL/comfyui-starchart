#!/usr/bin/env python3
"""Fetch new upstream versions and refresh snapshots, extractors, and generated docs.

Clones the specified upstream repos at the given tags, copies required source
files into the snapshots directory, re-runs all extractors, and regenerates
markdown. Does NOT auto-commit -- leaves that for the human to review.

Usage:
    python scripts/refresh_snapshots.py --core-version v0.20.1
    python scripts/refresh_snapshots.py --frontend-version v1.44.13
    python scripts/refresh_snapshots.py --core-version v0.20.1 --frontend-version v1.44.13

Exits 0 if successful, exit 1 if any step fails.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCES_DIR = REPO_ROOT / "references"
REFERENCES_RAW_DIR = REPO_ROOT / "references" / "raw"
SNAPSHOTS_DIR = REPO_ROOT / "references" / "snapshots"
SCRIPTS_EXTRACT_DIR = REPO_ROOT / "scripts" / "extract"
SCRIPTS_GENERATE_DIR = REPO_ROOT / "scripts" / "generate"
PROVENANCE_OUTPUT_PATH = REPO_ROOT / "docs" / "artifacts" / "refresh-provenance.json"

# Source files to copy from each repo
CORE_FILES = [
    "server.py",
    "execution.py",
    "pyproject.toml",
    "requirements.txt",
    "app/frontend_management.py",
    "comfy_api/latest/_io.py",
    "comfy_api/latest/_input/basic_types.py",
]

FRONTEND_FILES = [
    "package.json",
    "src/scripts/app.ts",
    "src/types/comfy.ts",
    "src/services/litegraphService.ts",
]

CORE_REPO_URL = "https://github.com/Comfy-Org/ComfyUI.git"
FRONTEND_REPO_URL = "https://github.com/Comfy-Org/ComfyUI_Frontend.git"


def _repo_relative_path(path: Path | None) -> str | None:
    """Return a repo-relative path with forward slashes."""
    if path is None:
        return None
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def canonical_raw_artifacts_exist() -> bool:
    """Return True when a prior canonical raw baseline exists."""
    return REFERENCES_RAW_DIR.exists() and any(REFERENCES_RAW_DIR.iterdir())


def create_pre_refresh_backup() -> Path | None:
    """Create a repo-local backup of references/raw before mutation."""
    if not canonical_raw_artifacts_exist():
        return None

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = REFERENCES_DIR / f"raw_backup_{timestamp}"
    try:
        shutil.copytree(REFERENCES_RAW_DIR, backup_dir)
    except OSError as exc:
        raise RuntimeError(
            f"Failed to create pre-refresh backup at {_repo_relative_path(backup_dir)}: {exc}"
        ) from exc
    return backup_dir


def build_delta_summary_command(backup_dir: Path | None) -> str | None:
    """Build the next-step delta-summary command for maintainers."""
    if backup_dir is None:
        return None
    return (
        f'{sys.executable} scripts/generate/generate_snapshot_delta_summary.py '
        f'--old "{_repo_relative_path(backup_dir)}" '
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
        "backup_location": _repo_relative_path(backup_dir),
        "runtime_object_info": {
            "requested": runtime_object_info_requested,
            "merged_into_node_api_schema": runtime_object_info_merged,
        },
        "published": {
            "provenance_path": _repo_relative_path(PROVENANCE_OUTPUT_PATH),
            "manifest_included": False,
        },
        "next_steps": {
            "delta_summary_command": build_delta_summary_command(backup_dir),
        },
    }


def write_refresh_provenance(payload: dict) -> Path:
    """Write the refresh provenance payload to the published repo-local path."""
    try:
        PROVENANCE_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        PROVENANCE_OUTPUT_PATH.write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise RuntimeError(
            f"Failed to write refresh provenance to {_repo_relative_path(PROVENANCE_OUTPUT_PATH)}: {exc}"
        ) from exc
    return PROVENANCE_OUTPUT_PATH


def _run_cmd(cmd: list[str], description: str, cwd: str | None = None) -> subprocess.CompletedProcess:
    """Run a command and exit on failure."""
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        print(f"  FAILED: {description}")
        if result.stdout:
            print(f"  stdout: {result.stdout[:500]}")
        if result.stderr:
            print(f"  stderr: {result.stderr[:500]}")
    return result


def _resolve_commit(clone_dir: str) -> str:
    """Get the full commit hash from a cloned repo."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        cwd=clone_dir,
    )
    if result.returncode != 0:
        print(f"  FAILED to resolve commit hash: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()


def _copy_source_files(clone_dir: str, dest_dir: Path, files: list[str], repo_label: str) -> list[str]:
    """Copy source files from clone into snapshot directory.

    Returns a list of copied file paths (relative to dest_dir).
    """
    copied = []
    for rel_path in files:
        src = Path(clone_dir) / rel_path
        dst = dest_dir / rel_path
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dst))
            copied.append(rel_path)
            print(f"  Copied {repo_label}/{rel_path}")
        else:
            print(f"  WARNING: {rel_path} not found in {repo_label} clone at {clone_dir}")
    return copied


def refresh_core(version: str, snapshot_date: str) -> tuple[str, str]:
    """Clone ComfyUI core at the given version tag and copy source files.

    Returns (commit_hash, snapshot_dir_name).
    """
    tag = version
    dest_name = f"comfyui-core-{version}"
    dest_dir = SNAPSHOTS_DIR / snapshot_date / dest_name

    print(f"\n=== Refreshing ComfyUI Core {version} ===")

    with tempfile.TemporaryDirectory(prefix="comfyui-core-") as tmpdir:
        # Clone at the specified tag with minimal history
        result = _run_cmd(
            ["git", "clone", "--depth", "1", "--branch", tag, CORE_REPO_URL, tmpdir],
            f"cloning ComfyUI core at {tag}",
        )
        if result.returncode != 0:
            print(f"  Failed to clone ComfyUI core at {tag}")
            sys.exit(1)

        # Resolve commit hash
        commit = _resolve_commit(tmpdir)
        print(f"  Resolved commit: {commit}")

        # Create destination directory
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Copy source files
        _copy_source_files(tmpdir, dest_dir, CORE_FILES, "core")

    return commit, dest_name


def refresh_frontend(version: str, snapshot_date: str) -> tuple[str, str]:
    """Clone ComfyUI Frontend at the given version tag and copy source files.

    Returns (commit_hash, snapshot_dir_name).
    """
    tag = version
    dest_name = f"comfyui-frontend-{version}"
    dest_dir = SNAPSHOTS_DIR / snapshot_date / dest_name

    print(f"\n=== Refreshing ComfyUI Frontend {version} ===")

    with tempfile.TemporaryDirectory(prefix="comfyui-frontend-") as tmpdir:
        # Clone at the specified tag with minimal history
        result = _run_cmd(
            ["git", "clone", "--depth", "1", "--branch", tag, FRONTEND_REPO_URL, tmpdir],
            f"cloning ComfyUI Frontend at {tag}",
        )
        if result.returncode != 0:
            print(f"  Failed to clone ComfyUI Frontend at {tag}")
            sys.exit(1)

        # Resolve commit hash
        commit = _resolve_commit(tmpdir)
        print(f"  Resolved commit: {commit}")

        # Create destination directory
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Copy source files
        _copy_source_files(tmpdir, dest_dir, FRONTEND_FILES, "frontend")

    return commit, dest_name


def run_runtime_extraction(url: str, version: str, commit: str) -> bool:
    """Run parse_from_api.py to capture runtime object_info.

    Returns True if successful.
    """
    print(f"\n--- Running parse_from_api.py ---")
    result = _run_cmd(
        [
            sys.executable,
            str(SCRIPTS_EXTRACT_DIR / "parse_from_api.py"),
            "--url", url,
            "--version", version,
            "--commit", commit,
            "--output", str(REFERENCES_RAW_DIR / "object_info_runtime.json"),
        ],
        "runtime object_info extraction",
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        print(f"  parse_from_api.py failed")
        return False
    print(f"  Runtime object_info captured")
    return True


def run_extractors(core_version: str = None, core_commit: str = None,
                   frontend_version: str = None, frontend_commit: str = None,
                   snapshot_date: str = None,
                   runtime_object_info_path: str = None) -> dict:
    """Re-run all extractors against the new snapshot files.

    Returns a dict with extraction results (counts of endpoints, hooks, etc.).
    """
    results = {}
    snapshot_base = SNAPSHOTS_DIR / snapshot_date

    # Run parse_server.py if core was refreshed
    if core_version and core_commit:
        core_dir = snapshot_base / f"comfyui-core-{core_version}"
        server_path = core_dir / "server.py"
        if server_path.exists():
            print(f"\n--- Running parse_server.py ---")
            result = _run_cmd(
                [
                    sys.executable,
                    str(SCRIPTS_EXTRACT_DIR / "parse_server.py"),
                    str(server_path),
                    "--version", core_version,
                    "--commit", core_commit,
                ],
                "parse_server.py extraction",
                cwd=str(REPO_ROOT),
            )
            if result.returncode != 0:
                print(f"  parse_server.py failed")
                sys.exit(1)
            # Count endpoints from output
            for line in result.stdout.strip().splitlines():
                if "Extracted" in line and "endpoints" in line:
                    print(f"  {line}")
                    results["server_endpoints"] = line

    # Run parse_hooks.py if frontend was refreshed
    if frontend_version and frontend_commit:
        frontend_dir = snapshot_base / f"comfyui-frontend-{frontend_version}"
        source_paths = [
            frontend_dir / "src" / "scripts" / "app.ts",
            frontend_dir / "src" / "types" / "comfy.ts",
            frontend_dir / "src" / "services" / "litegraphService.ts",
        ]
        existing_sources = [str(p) for p in source_paths if p.exists()]
        if existing_sources:
            print(f"\n--- Running parse_hooks.py ---")
            result = _run_cmd(
                [
                    sys.executable,
                    str(SCRIPTS_EXTRACT_DIR / "parse_hooks.py"),
                ] + existing_sources + [
                    "--version", frontend_version,
                    "--commit", frontend_commit,
                ],
                "parse_hooks.py extraction",
                cwd=str(REPO_ROOT),
            )
            if result.returncode != 0:
                print(f"  parse_hooks.py failed")
                sys.exit(1)
            for line in result.stdout.strip().splitlines():
                if "Extracted" in line and "hooks" in line:
                    print(f"  {line}")
                    results["js_hooks"] = line

    # Run parse_node_api_schema.py if core was refreshed
    if core_version and core_commit:
        core_dir = snapshot_base / f"comfyui-core-{core_version}"
        server_path = core_dir / "server.py"
        io_path = core_dir / "comfy_api" / "latest" / "_io.py"
        basic_types_path = core_dir / "comfy_api" / "latest" / "_input" / "basic_types.py"
        if server_path.exists() and io_path.exists() and basic_types_path.exists():
            print(f"\n--- Running parse_node_api_schema.py ---")
            cmd = [
                sys.executable,
                str(SCRIPTS_EXTRACT_DIR / "parse_node_api_schema.py"),
                str(server_path),
                str(io_path),
                str(basic_types_path),
                "--version", core_version,
                "--commit", core_commit,
            ]
            if runtime_object_info_path:
                cmd += ["--object-info-runtime-path", runtime_object_info_path]
            result = _run_cmd(
                cmd,
                "parse_node_api_schema.py extraction",
                cwd=str(REPO_ROOT),
            )
            if result.returncode != 0:
                print(f"  parse_node_api_schema.py failed")
                sys.exit(1)
            for line in result.stdout.strip().splitlines():
                if "Extracted" in line:
                    print(f"  {line}")
                    results["node_api_schema"] = line

    return results


def run_markdown_generation() -> bool:
    """Re-run the markdown generator.

    Returns True if successful.
    """
    print(f"\n--- Running md_from_json.py ---")
    result = _run_cmd(
        [sys.executable, str(SCRIPTS_GENERATE_DIR / "md_from_json.py")],
        "markdown generation",
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        print(f"  md_from_json.py failed")
        return False
    print(f"  {result.stdout.strip()}")
    return True


def compute_diff_summary(old_json: dict, new_json: dict, json_name: str) -> list[str]:
    """Compare old and new JSON content and return a summary of changes."""
    changes = []

    if json_name == "server_endpoints.json":
        old_routes = {e["route"] for e in old_json.get("endpoints", [])}
        new_routes = {e["route"] for e in new_json.get("endpoints", [])}
        added = new_routes - old_routes
        removed = old_routes - new_routes
        if added:
            changes.append(f"  New endpoints: {sorted(added)}")
        if removed:
            changes.append(f"  Removed endpoints: {sorted(removed)}")
        if not added and not removed:
            changes.append(f"  No endpoint changes ({len(new_routes)} total)")

    elif json_name == "js_hooks.json":
        old_hooks = {h["name"] for h in old_json.get("hooks", [])}
        new_hooks = {h["name"] for h in new_json.get("hooks", [])}
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

        old_types = {t["class_name"] for t in old_json.get("io_types", [])}
        new_types = {t["class_name"] for t in new_json.get("io_types", [])}
        added_types = new_types - old_types
        removed_types = old_types - new_types
        if added_types:
            changes.append(f"  New IO types: {sorted(added_types)}")
        if removed_types:
            changes.append(f"  Removed IO types: {sorted(removed_types)}")

        # Runtime provenance diff
        old_prov = old_json.get("metadata", {}).get("provenance", {})
        new_prov = new_json.get("metadata", {}).get("provenance", {})
        old_mode = old_prov.get("mode", "source-only")
        new_mode = new_prov.get("mode", "source-only")
        if old_mode != new_mode:
            changes.append(f"  Provenance mode changed: {old_mode} -> {new_mode}")

        old_runtime = old_json.get("runtime_object_info", {})
        new_runtime = new_json.get("runtime_object_info", {})
        old_count = len(old_runtime) if isinstance(old_runtime, dict) else 0
        new_count = len(new_runtime) if isinstance(new_runtime, dict) else 0
        if old_count != new_count:
            changes.append(f"  Runtime object_info node count: {old_count} -> {new_count}")

        if not added and not removed and not added_types and not removed_types and old_mode == new_mode and old_count == new_count:
            changes.append(f"  No schema changes")

    return changes


def main():
    """Main entry point for snapshot refresh."""
    parser = argparse.ArgumentParser(
        description=(
            "Fetch new upstream versions and refresh snapshots, extractors, and docs. "
            "Creates an automatic repo-local backup before overwriting canonical raw artifacts "
            "and writes refresh provenance to docs/artifacts/refresh-provenance.json."
        )
    )
    parser.add_argument(
        "--core-version",
        default=None,
        help="ComfyUI core version tag to fetch (e.g., v0.20.1)",
    )
    parser.add_argument(
        "--frontend-version",
        default=None,
        help="ComfyUI frontend version tag to fetch (e.g., v1.44.13)",
    )
    parser.add_argument(
        "--runtime-object-info-url",
        default=None,
        help="URL of a running ComfyUI instance to capture runtime object_info",
    )
    parser.add_argument(
        "--runtime-object-info-version",
        default=None,
        help="Version tag for the runtime object_info capture",
    )
    parser.add_argument(
        "--runtime-object-info-commit",
        default=None,
        help="Commit hash for the runtime object_info capture",
    )
    parser.add_argument(
        "--skip-runtime-merge",
        action="store_true",
        help="Skip merging runtime object_info into node_api_schema even if runtime URL is provided",
    )
    args = parser.parse_args()

    if not args.core_version and not args.frontend_version and not args.runtime_object_info_url:
        parser.print_usage()
        print("\nError: at least one of --core-version, --frontend-version, or --runtime-object-info-url is required")
        return 1

    # Pre-flight: verify git is available
    git_check = subprocess.run(
        ["git", "--version"],
        capture_output=True,
        text=True,
    )
    if git_check.returncode != 0:
        print("Error: git is required but not found on PATH.")
        print("Install git or ensure it is available before running this script.")
        return 1
    print(f"Git version: {git_check.stdout.strip()}")

    snapshot_date = date.today().strftime("%Y-%m-%d")
    core_commit = None
    frontend_commit = None
    runtime_object_info_path = None

    try:
        backup_dir = create_pre_refresh_backup()
    except RuntimeError as exc:
        print(f"Error: {exc}")
        return 1

    if backup_dir is not None:
        print(f"Pre-refresh backup created at: {_repo_relative_path(backup_dir)}")
    else:
        print("No prior canonical raw baseline found; skipping pre-refresh backup.")

    # Save current JSON content for diff comparison
    old_jsons = {}
    for json_file in REFERENCES_RAW_DIR.glob("*.json"):
        try:
            old_jsons[json_file.name] = json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            old_jsons[json_file.name] = {}

    # Refresh core
    if args.core_version:
        core_commit, _ = refresh_core(args.core_version, snapshot_date)

    # Refresh frontend
    if args.frontend_version:
        frontend_commit, _ = refresh_frontend(args.frontend_version, snapshot_date)

    # Runtime object_info capture
    if args.runtime_object_info_url:
        version = args.runtime_object_info_version or args.core_version or "unversioned"
        commit = args.runtime_object_info_commit or core_commit or ""
        if not run_runtime_extraction(args.runtime_object_info_url, version, commit):
            print("\nRuntime extraction failed.")
            return 1
        runtime_object_info_path = str(REFERENCES_RAW_DIR / "object_info_runtime.json")

    # Re-run extractors
    extraction_results = run_extractors(
        core_version=args.core_version,
        core_commit=core_commit,
        frontend_version=args.frontend_version,
        frontend_commit=frontend_commit,
        snapshot_date=snapshot_date,
        runtime_object_info_path=None if args.skip_runtime_merge else runtime_object_info_path,
    )

    # Re-run markdown generation
    if not run_markdown_generation():
        print("\nMarkdown generation failed.")
        return 1

    # Compute diff summary
    print(f"\n=== Change Summary ===")
    for json_file in sorted(REFERENCES_RAW_DIR.glob("*.json")):
        try:
            new_data = json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        old_data = old_jsons.get(json_file.name, {})
        changes = compute_diff_summary(old_data, new_data, json_file.name)
        if changes:
            print(f"\n{json_file.name}:")
            for change in changes:
                print(change)

    provenance_payload = build_refresh_provenance(
        refresh_date=snapshot_date,
        requested_core_version=args.core_version,
        requested_frontend_version=args.frontend_version,
        resolved_core_commit=core_commit,
        resolved_frontend_commit=frontend_commit,
        backup_dir=backup_dir,
        runtime_object_info_requested=bool(args.runtime_object_info_url),
        runtime_object_info_merged=bool(args.runtime_object_info_url and not args.skip_runtime_merge),
    )
    try:
        provenance_path = write_refresh_provenance(provenance_payload)
    except RuntimeError as exc:
        print(f"Error: {exc}")
        return 1

    print(f"\n=== Refresh Complete ===")
    print(f"Snapshot date: {snapshot_date}")
    if args.core_version:
        print(f"Core version: {args.core_version} (commit: {core_commit})")
    if args.frontend_version:
        print(f"Frontend version: {args.frontend_version} (commit: {frontend_commit})")
    if args.runtime_object_info_url:
        print(f"Runtime object_info captured from: {args.runtime_object_info_url}")
        if args.skip_runtime_merge:
            print("Runtime merge skipped (--skip-runtime-merge)")
        else:
            print("Runtime object_info merged into node_api_schema")
    print(f"Refresh provenance written to: {_repo_relative_path(provenance_path)}")
    if backup_dir is not None:
        print(f"Delta summary command: {build_delta_summary_command(backup_dir)}")
    print("\nReview the changes and commit manually if everything looks correct.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
