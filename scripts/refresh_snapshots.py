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
import importlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

refresh_support = importlib.import_module("scripts.common.refresh_support")

REFERENCES_DIR = REPO_ROOT / "references"
REFERENCES_RAW_DIR = REPO_ROOT / "references" / "raw"
SNAPSHOTS_DIR = REPO_ROOT / "references" / "snapshots"
SCRIPTS_EXTRACT_DIR = REPO_ROOT / "scripts" / "extract"
SCRIPTS_GENERATE_DIR = REPO_ROOT / "scripts" / "generate"
PROVENANCE_OUTPUT_PATH = REPO_ROOT / "public" / "artifacts" / "refresh-provenance.json"

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
    return refresh_support.repo_relative_path(path, REPO_ROOT)


def canonical_raw_artifacts_exist() -> bool:
    """Return True when a prior canonical raw baseline exists."""
    return refresh_support.canonical_raw_artifacts_exist(REFERENCES_RAW_DIR)


def create_pre_refresh_backup() -> Path | None:
    """Create a repo-local backup of references/raw before mutation."""
    return refresh_support.create_pre_refresh_backup(
        REFERENCES_DIR,
        REFERENCES_RAW_DIR,
        REPO_ROOT,
    )


def build_delta_summary_command(backup_dir: Path | None) -> str | None:
    """Build the next-step delta-summary command for maintainers."""
    return refresh_support.build_delta_summary_command(
        backup_dir,
        REPO_ROOT,
        refresh_support.recommended_python_command(sys.platform),
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
    return refresh_support.build_refresh_provenance(
        refresh_date=refresh_date,
        requested_core_version=requested_core_version,
        requested_frontend_version=requested_frontend_version,
        resolved_core_commit=resolved_core_commit,
        resolved_frontend_commit=resolved_frontend_commit,
        backup_dir=backup_dir,
        runtime_object_info_requested=runtime_object_info_requested,
        runtime_object_info_merged=runtime_object_info_merged,
        repo_root=REPO_ROOT,
        provenance_output_path=PROVENANCE_OUTPUT_PATH,
        python_executable=refresh_support.recommended_python_command(sys.platform),
    )


def write_refresh_provenance(payload: dict) -> Path:
    """Write the refresh provenance payload to the published repo-local path."""
    return refresh_support.write_refresh_provenance(
        payload,
        PROVENANCE_OUTPUT_PATH,
        REPO_ROOT,
    )


def compute_diff_summary(old_json: dict, new_json: dict, json_name: str) -> list[str]:
    """Compare old and new JSON content and return a summary of changes."""
    return refresh_support.compute_diff_summary(old_json, new_json, json_name)


def _run_cmd(
    cmd: list[str], description: str, cwd: str | None = None
) -> subprocess.CompletedProcess:
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


def _copy_source_files(
    clone_dir: str, dest_dir: Path, files: list[str], repo_label: str
) -> list[str]:
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


def _refresh_repo_snapshot(
    *,
    version: str,
    snapshot_date: str,
    repo_url: str,
    dest_prefix: str,
    heading_label: str,
    clone_label: str,
    copy_label: str,
    temp_prefix: str,
    files: list[str],
) -> tuple[str, str]:
    """Clone a repo at a tag and copy the selected source files into snapshots."""
    tag = version
    dest_name = f"{dest_prefix}-{version}"
    dest_dir = SNAPSHOTS_DIR / snapshot_date / dest_name

    print(f"\n=== Refreshing {heading_label} {version} ===")

    with tempfile.TemporaryDirectory(prefix=temp_prefix) as tmpdir:
        result = _run_cmd(
            ["git", "clone", "--depth", "1", "--branch", tag, repo_url, tmpdir],
            f"cloning {clone_label} at {tag}",
        )
        if result.returncode != 0:
            print(f"  Failed to clone {clone_label} at {tag}")
            sys.exit(1)

        commit = _resolve_commit(tmpdir)
        print(f"  Resolved commit: {commit}")

        dest_dir.mkdir(parents=True, exist_ok=True)
        _copy_source_files(tmpdir, dest_dir, files, copy_label)

    return commit, dest_name


def refresh_core(version: str, snapshot_date: str) -> tuple[str, str]:
    """Clone ComfyUI core at the given version tag and copy source files.

    Returns (commit_hash, snapshot_dir_name).
    """
    return _refresh_repo_snapshot(
        version=version,
        snapshot_date=snapshot_date,
        repo_url=CORE_REPO_URL,
        dest_prefix="comfyui-core",
        heading_label="ComfyUI Core",
        clone_label="ComfyUI core",
        copy_label="core",
        temp_prefix="comfyui-core-",
        files=CORE_FILES,
    )


def refresh_frontend(version: str, snapshot_date: str) -> tuple[str, str]:
    """Clone ComfyUI Frontend at the given version tag and copy source files.

    Returns (commit_hash, snapshot_dir_name).
    """
    return _refresh_repo_snapshot(
        version=version,
        snapshot_date=snapshot_date,
        repo_url=FRONTEND_REPO_URL,
        dest_prefix="comfyui-frontend",
        heading_label="ComfyUI Frontend",
        clone_label="ComfyUI Frontend",
        copy_label="frontend",
        temp_prefix="comfyui-frontend-",
        files=FRONTEND_FILES,
    )


def run_runtime_extraction(url: str, version: str, commit: str) -> bool:
    """Run parse_from_api.py to capture runtime object_info.

    Returns True if successful.
    """
    print("\n--- Running parse_from_api.py ---")
    result = _run_cmd(
        [
            sys.executable,
            str(SCRIPTS_EXTRACT_DIR / "parse_from_api.py"),
            "--url",
            url,
            "--version",
            version,
            "--commit",
            commit,
            "--output",
            str(REFERENCES_RAW_DIR / "object_info_runtime.json"),
        ],
        "runtime object_info extraction",
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        print("  parse_from_api.py failed")
        return False
    print("  Runtime object_info captured")
    return True


def _run_server_extractor(core_dir: Path, core_version: str, core_commit: str) -> str | None:
    """Run `parse_server.py` for the refreshed core snapshot."""
    server_path = core_dir / "server.py"
    if not server_path.exists():
        return None

    print("\n--- Running parse_server.py ---")
    result = _run_cmd(
        [
            sys.executable,
            str(SCRIPTS_EXTRACT_DIR / "parse_server.py"),
            str(server_path),
            "--version",
            core_version,
            "--commit",
            core_commit,
        ],
        "parse_server.py extraction",
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        print("  parse_server.py failed")
        sys.exit(1)

    for line in result.stdout.strip().splitlines():
        if "Extracted" in line and "endpoints" in line:
            print(f"  {line}")
            return line
    return None


def _run_hooks_extractor(
    frontend_dir: Path,
    frontend_version: str,
    frontend_commit: str,
) -> str | None:
    """Run `parse_hooks.py` for the refreshed frontend snapshot."""
    source_paths = [
        frontend_dir / "src" / "scripts" / "app.ts",
        frontend_dir / "src" / "types" / "comfy.ts",
        frontend_dir / "src" / "services" / "litegraphService.ts",
    ]
    existing_sources = [str(path) for path in source_paths if path.exists()]
    if not existing_sources:
        return None

    print("\n--- Running parse_hooks.py ---")
    result = _run_cmd(
        [
            sys.executable,
            str(SCRIPTS_EXTRACT_DIR / "parse_hooks.py"),
            *existing_sources,
            "--version",
            frontend_version,
            "--commit",
            frontend_commit,
        ],
        "parse_hooks.py extraction",
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        print("  parse_hooks.py failed")
        sys.exit(1)

    for line in result.stdout.strip().splitlines():
        if "Extracted" in line and "hooks" in line:
            print(f"  {line}")
            return line
    return None


def _run_node_api_schema_extractor(
    core_dir: Path,
    core_version: str,
    core_commit: str,
    runtime_object_info_path: str | None,
) -> str | None:
    """Run `parse_node_api_schema.py` for the refreshed core snapshot."""
    server_path = core_dir / "server.py"
    io_path = core_dir / "comfy_api" / "latest" / "_io.py"
    basic_types_path = core_dir / "comfy_api" / "latest" / "_input" / "basic_types.py"
    if not server_path.exists() or not io_path.exists() or not basic_types_path.exists():
        return None

    print("\n--- Running parse_node_api_schema.py ---")
    cmd = [
        sys.executable,
        str(SCRIPTS_EXTRACT_DIR / "parse_node_api_schema.py"),
        str(server_path),
        str(io_path),
        str(basic_types_path),
        "--version",
        core_version,
        "--commit",
        core_commit,
    ]
    if runtime_object_info_path:
        cmd += ["--object-info-runtime-path", runtime_object_info_path]
    result = _run_cmd(
        cmd,
        "parse_node_api_schema.py extraction",
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        print("  parse_node_api_schema.py failed")
        sys.exit(1)

    for line in result.stdout.strip().splitlines():
        if "Extracted" in line:
            print(f"  {line}")
            return line
    return None


def run_extractors(
    core_version: str = None,
    core_commit: str = None,
    frontend_version: str = None,
    frontend_commit: str = None,
    snapshot_date: str = None,
    runtime_object_info_path: str = None,
) -> dict:
    """Re-run all extractors against the new snapshot files.

    Returns a dict with extraction results (counts of endpoints, hooks, etc.).
    """
    results = {}
    snapshot_base = SNAPSHOTS_DIR / snapshot_date

    if core_version and core_commit:
        core_dir = snapshot_base / f"comfyui-core-{core_version}"
        server_summary = _run_server_extractor(core_dir, core_version, core_commit)
        if server_summary:
            results["server_endpoints"] = server_summary

    if frontend_version and frontend_commit:
        frontend_dir = snapshot_base / f"comfyui-frontend-{frontend_version}"
        hooks_summary = _run_hooks_extractor(
            frontend_dir,
            frontend_version,
            frontend_commit,
        )
        if hooks_summary:
            results["js_hooks"] = hooks_summary

    if core_version and core_commit:
        core_dir = snapshot_base / f"comfyui-core-{core_version}"
        schema_summary = _run_node_api_schema_extractor(
            core_dir,
            core_version,
            core_commit,
            runtime_object_info_path,
        )
        if schema_summary:
            results["node_api_schema"] = schema_summary

    return results


def run_markdown_generation() -> bool:
    """Re-run the markdown generator.

    Returns True if successful.
    """
    print("\n--- Running md_from_json.py ---")
    result = _run_cmd(
        [sys.executable, str(SCRIPTS_GENERATE_DIR / "md_from_json.py")],
        "markdown generation",
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        print("  md_from_json.py failed")
        return False
    print(f"  {result.stdout.strip()}")
    return True


def verify_git_available() -> bool:
    """Verify git is available on PATH before refresh work starts."""
    git_check = subprocess.run(
        ["git", "--version"],
        capture_output=True,
        text=True,
    )
    if git_check.returncode != 0:
        print("Error: git is required but not found on PATH.")
        print("Install git or ensure it is available before running this script.")
        return False
    print(f"Git version: {git_check.stdout.strip()}")
    return True


def load_existing_raw_jsons() -> dict[str, dict]:
    """Load the current raw JSON artifacts for later diff reporting."""
    old_jsons = {}
    for json_file in REFERENCES_RAW_DIR.glob("*.json"):
        try:
            old_jsons[json_file.name] = json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            old_jsons[json_file.name] = {}
    return old_jsons


def refresh_requested_snapshots(
    core_version: str | None,
    frontend_version: str | None,
    snapshot_date: str,
) -> tuple[str | None, str | None]:
    """Run the requested core and frontend refresh steps."""
    core_commit = None
    frontend_commit = None

    if core_version:
        core_commit, _ = refresh_core(core_version, snapshot_date)

    if frontend_version:
        frontend_commit, _ = refresh_frontend(frontend_version, snapshot_date)

    return core_commit, frontend_commit


def capture_runtime_object_info(args: argparse.Namespace, core_commit: str | None) -> str | None:
    """Run the optional runtime object_info capture flow."""
    if not args.runtime_object_info_url:
        return None

    version = args.runtime_object_info_version or args.core_version or "unversioned"
    commit = args.runtime_object_info_commit or core_commit or ""
    if not run_runtime_extraction(args.runtime_object_info_url, version, commit):
        raise RuntimeError("Runtime extraction failed.")
    return str(REFERENCES_RAW_DIR / "object_info_runtime.json")


def print_change_summary(old_jsons: dict[str, dict]) -> None:
    """Print the post-refresh diff summary for raw JSON artifacts."""
    print("\n=== Change Summary ===")
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


def persist_refresh_provenance(
    args: argparse.Namespace,
    snapshot_date: str,
    core_commit: str | None,
    frontend_commit: str | None,
    backup_dir: Path | None,
) -> Path:
    """Build and write the refresh provenance payload."""
    provenance_payload = build_refresh_provenance(
        refresh_date=snapshot_date,
        requested_core_version=args.core_version,
        requested_frontend_version=args.frontend_version,
        resolved_core_commit=core_commit,
        resolved_frontend_commit=frontend_commit,
        backup_dir=backup_dir,
        runtime_object_info_requested=bool(args.runtime_object_info_url),
        runtime_object_info_merged=bool(
            args.runtime_object_info_url and not args.skip_runtime_merge
        ),
    )
    return write_refresh_provenance(provenance_payload)


def main():
    """Main entry point for snapshot refresh."""
    parser = argparse.ArgumentParser(
        description=(
            "Fetch new upstream versions and refresh snapshots, extractors, and docs. "
            "Creates an automatic repo-local backup before overwriting canonical raw artifacts "
            "under references/_refresh_backups/raw_<timestamp>/ and writes refresh provenance "
            "to public/artifacts/refresh-provenance.json."
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
        print(
            "\nError: at least one of --core-version, --frontend-version, or --runtime-object-info-url is required"
        )
        return 1

    if not verify_git_available():
        return 1

    snapshot_date = date.today().strftime("%Y-%m-%d")

    try:
        backup_dir = create_pre_refresh_backup()
    except RuntimeError as exc:
        print(f"Error: {exc}")
        return 1

    if backup_dir is not None:
        print(f"Pre-refresh backup created at: {_repo_relative_path(backup_dir)}")
    else:
        print("No prior canonical raw baseline found; skipping pre-refresh backup.")

    old_jsons = load_existing_raw_jsons()
    core_commit, frontend_commit = refresh_requested_snapshots(
        args.core_version,
        args.frontend_version,
        snapshot_date,
    )

    try:
        runtime_object_info_path = capture_runtime_object_info(args, core_commit)
    except RuntimeError as exc:
        print(f"\n{exc}")
        return 1

    # Re-run extractors
    run_extractors(
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

    print_change_summary(old_jsons)

    try:
        provenance_path = persist_refresh_provenance(
            args,
            snapshot_date,
            core_commit,
            frontend_commit,
            backup_dir,
        )
    except RuntimeError as exc:
        print(f"Error: {exc}")
        return 1

    print("\n=== Refresh Complete ===")
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
