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
import sys
from datetime import date
from pathlib import Path

from scripts.common import refresh_git_ops, refresh_pipeline, refresh_support

REPO_ROOT = Path(__file__).resolve().parents[1]

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


def _run_cmd(cmd: list[str], description: str, cwd: str | None = None):
    """Compatibility wrapper around the shared git/runtime command helper."""
    return refresh_git_ops._run_cmd(cmd, description, cwd=cwd)


def _resolve_commit(clone_dir: str) -> str:
    """Compatibility wrapper around the shared git commit resolver."""
    return refresh_git_ops._resolve_commit(clone_dir)


def _copy_source_files(
    clone_dir: str, dest_dir: Path, files: list[str], repo_label: str
) -> list[str]:
    """Compatibility wrapper around the shared snapshot copy helper."""
    return refresh_git_ops._copy_source_files(clone_dir, dest_dir, files, repo_label)


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
    """Compatibility wrapper around the shared snapshot refresh helper."""
    return refresh_git_ops._refresh_repo_snapshot(
        version=version,
        snapshot_date=snapshot_date,
        repo_url=repo_url,
        snapshots_dir=SNAPSHOTS_DIR,
        dest_prefix=dest_prefix,
        heading_label=heading_label,
        clone_label=clone_label,
        copy_label=copy_label,
        temp_prefix=temp_prefix,
        files=files,
    )


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
    try:
        _run_cmd(
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
    except RuntimeError as exc:
        print(f"  {exc}")
        print("  parse_from_api.py failed")
        return False
    print("  Runtime object_info captured")
    return True


def _run_server_extractor(core_dir: Path, core_version: str, core_commit: str) -> str | None:
    """Run `parse_server.py` for the refreshed core snapshot."""
    try:
        return refresh_pipeline._run_server_extractor(
            core_dir,
            core_version,
            core_commit,
            python_executable=sys.executable,
            scripts_extract_dir=SCRIPTS_EXTRACT_DIR,
            repo_root=REPO_ROOT,
            run_cmd=_run_cmd,
        )
    except RuntimeError:
        sys.exit(1)


def _run_hooks_extractor(
    frontend_dir: Path,
    frontend_version: str,
    frontend_commit: str,
) -> str | None:
    """Run `parse_hooks.py` for the refreshed frontend snapshot."""
    try:
        return refresh_pipeline._run_hooks_extractor(
            frontend_dir,
            frontend_version,
            frontend_commit,
            python_executable=sys.executable,
            scripts_extract_dir=SCRIPTS_EXTRACT_DIR,
            repo_root=REPO_ROOT,
            run_cmd=_run_cmd,
        )
    except RuntimeError:
        sys.exit(1)


def _run_node_api_schema_extractor(
    core_dir: Path,
    core_version: str,
    core_commit: str,
    runtime_object_info_path: str | None,
) -> str | None:
    """Run `parse_node_api_schema.py` for the refreshed core snapshot."""
    try:
        return refresh_pipeline._run_node_api_schema_extractor(
            core_dir,
            core_version,
            core_commit,
            runtime_object_info_path,
            python_executable=sys.executable,
            scripts_extract_dir=SCRIPTS_EXTRACT_DIR,
            repo_root=REPO_ROOT,
            run_cmd=_run_cmd,
        )
    except RuntimeError:
        sys.exit(1)


def run_extractors(
    core_version: str | None = None,
    core_commit: str | None = None,
    frontend_version: str | None = None,
    frontend_commit: str | None = None,
    snapshot_date: str | None = None,
    runtime_object_info_path: str | None = None,
) -> dict:
    """Re-run all extractors against the new snapshot files.

    Returns a dict with extraction results (counts of endpoints, hooks, etc.).
    """
    return refresh_pipeline.run_extractors(
        core_version=core_version,
        core_commit=core_commit,
        frontend_version=frontend_version,
        frontend_commit=frontend_commit,
        snapshot_date=snapshot_date,
        runtime_object_info_path=runtime_object_info_path,
        snapshots_dir=SNAPSHOTS_DIR,
        python_executable=sys.executable,
        scripts_extract_dir=SCRIPTS_EXTRACT_DIR,
        repo_root=REPO_ROOT,
        run_cmd=_run_cmd,
    )


def run_markdown_generation() -> bool:
    """Re-run the markdown generator.

    Returns True if successful.
    """
    return refresh_pipeline.run_markdown_generation(
        python_executable=sys.executable,
        scripts_generate_dir=SCRIPTS_GENERATE_DIR,
        repo_root=REPO_ROOT,
        run_cmd=_run_cmd,
    )


def verify_git_available() -> bool:
    """Verify git is available on PATH before refresh work starts."""
    try:
        git_version = refresh_git_ops.verify_git_available()
    except RuntimeError as exc:
        print(f"Error: {exc}")
        print("Install git or ensure it is available before running this script.")
        return False
    print(f"Git version: {git_version}")
    return True


def load_existing_raw_jsons() -> dict[str, dict]:
    """Load the current raw JSON artifacts for later diff reporting."""
    return refresh_pipeline.load_existing_raw_jsons(REFERENCES_RAW_DIR)


def refresh_requested_snapshots(
    core_version: str | None,
    frontend_version: str | None,
    snapshot_date: str,
) -> tuple[str | None, str | None]:
    """Run the requested core and frontend refresh steps."""
    return refresh_pipeline.refresh_requested_snapshots(
        core_version,
        frontend_version,
        snapshot_date,
        refresh_core=refresh_core,
        refresh_frontend=refresh_frontend,
    )


def capture_runtime_object_info(args: argparse.Namespace, core_commit: str | None) -> str | None:
    """Run the optional runtime object_info capture flow."""
    return refresh_pipeline.capture_runtime_object_info(
        args,
        core_commit,
        references_raw_dir=REFERENCES_RAW_DIR,
        run_runtime_extraction=run_runtime_extraction,
    )


def print_change_summary(old_jsons: dict[str, dict]) -> None:
    """Print the post-refresh diff summary for raw JSON artifacts."""
    refresh_pipeline.print_change_summary(
        old_jsons,
        references_raw_dir=REFERENCES_RAW_DIR,
        compute_diff_summary=compute_diff_summary,
    )


def build_follow_up_commands_from_provenance(provenance_payload: dict) -> list[str]:
    """Return the ordered post-refresh follow-up commands from provenance state."""
    return refresh_pipeline.build_follow_up_commands_from_provenance(provenance_payload)


def persist_refresh_provenance(
    args: argparse.Namespace,
    snapshot_date: str,
    core_commit: str | None,
    frontend_commit: str | None,
    backup_dir: Path | None,
) -> Path:
    """Build and write the refresh provenance payload."""
    return refresh_pipeline.persist_refresh_provenance(
        args,
        snapshot_date,
        core_commit,
        frontend_commit,
        backup_dir,
        build_refresh_provenance=build_refresh_provenance,
        write_refresh_provenance=write_refresh_provenance,
    )


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
    try:
        core_commit, frontend_commit = refresh_requested_snapshots(
            args.core_version,
            args.frontend_version,
            snapshot_date,
        )
    except RuntimeError as exc:
        print(f"Error: {exc}")
        return 1

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
    provenance_payload = json.loads(provenance_path.read_text(encoding="utf-8"))
    follow_up_commands = build_follow_up_commands_from_provenance(provenance_payload)
    if follow_up_commands:
        print("Recommended follow-up commands:")
        for command in follow_up_commands:
            print(f"  {command}")
    print("\nReview the changes and commit manually if everything looks correct.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
