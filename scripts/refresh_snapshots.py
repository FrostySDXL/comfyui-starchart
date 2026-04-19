#!/usr/bin/env python3
"""Fetch new upstream versions and refresh snapshots, extractors, and generated docs.

Clones the specified upstream repos at the given tags, copies required source
files into the snapshots directory, re-runs all extractors, and regenerates
markdown. Does NOT auto-commit -- leaves that for the human to review.

Usage:
    python scripts/refresh_snapshots.py --core-version v0.19.4
    python scripts/refresh_snapshots.py --frontend-version v1.42.12
    python scripts/refresh_snapshots.py --core-version v0.19.4 --frontend-version v1.42.12

Exits 0 if successful, exit 1 if any step fails.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCES_RAW_DIR = REPO_ROOT / "references" / "raw"
SNAPSHOTS_DIR = REPO_ROOT / "references" / "snapshots"
SCRIPTS_EXTRACT_DIR = REPO_ROOT / "scripts" / "extract"
SCRIPTS_GENERATE_DIR = REPO_ROOT / "scripts" / "generate"

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


def run_extractors(core_version: str = None, core_commit: str = None,
                   frontend_version: str = None, frontend_commit: str = None,
                   snapshot_date: str = None) -> dict:
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
            result = _run_cmd(
                [
                    sys.executable,
                    str(SCRIPTS_EXTRACT_DIR / "parse_node_api_schema.py"),
                    str(server_path),
                    str(io_path),
                    str(basic_types_path),
                    "--version", core_version,
                    "--commit", core_commit,
                ],
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

        if not added and not removed and not added_types and not removed_types:
            changes.append(f"  No schema changes")

    return changes


def main():
    """Main entry point for snapshot refresh."""
    parser = argparse.ArgumentParser(
        description="Fetch new upstream versions and refresh snapshots, extractors, and docs."
    )
    parser.add_argument(
        "--core-version",
        default=None,
        help="ComfyUI core version tag to fetch (e.g., v0.19.4)",
    )
    parser.add_argument(
        "--frontend-version",
        default=None,
        help="ComfyUI frontend version tag to fetch (e.g., v1.42.12)",
    )
    args = parser.parse_args()

    if not args.core_version and not args.frontend_version:
        parser.print_usage()
        print("\nError: at least one of --core-version or --frontend-version is required")
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

    # Re-run extractors
    extraction_results = run_extractors(
        core_version=args.core_version,
        core_commit=core_commit,
        frontend_version=args.frontend_version,
        frontend_commit=frontend_commit,
        snapshot_date=snapshot_date,
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

    print(f"\n=== Refresh Complete ===")
    print(f"Snapshot date: {snapshot_date}")
    if args.core_version:
        print(f"Core version: {args.core_version} (commit: {core_commit})")
    if args.frontend_version:
        print(f"Frontend version: {args.frontend_version} (commit: {frontend_commit})")
    print("\nReview the changes and commit manually if everything looks correct.")
    return 0


if __name__ == "__main__":
    sys.exit(main())