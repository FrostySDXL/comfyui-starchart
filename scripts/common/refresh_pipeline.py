import argparse
import json
from pathlib import Path


def _run_server_extractor(
    core_dir: Path,
    core_version: str,
    core_commit: str,
    *,
    python_executable: str,
    scripts_extract_dir: Path,
    repo_root: Path,
    run_cmd,
) -> str | None:
    """Run `parse_server.py` for the refreshed core snapshot."""
    server_path = core_dir / "server.py"
    if not server_path.exists():
        return None

    print("\n--- Running parse_server.py ---")
    try:
        result = run_cmd(
            [
                python_executable,
                str(scripts_extract_dir / "parse_server.py"),
                str(server_path),
                "--version",
                core_version,
                "--commit",
                core_commit,
            ],
            "parse_server.py extraction",
            cwd=str(repo_root),
        )
    except RuntimeError as exc:
        print(f"  {exc}")
        print("  parse_server.py failed")
        raise RuntimeError("parse_server.py extraction failed")

    for line in result.stdout.strip().splitlines():
        if "Extracted" in line and "endpoints" in line:
            print(f"  {line}")
            return line
    return None


def _run_hooks_extractor(
    frontend_dir: Path,
    frontend_version: str,
    frontend_commit: str,
    *,
    python_executable: str,
    scripts_extract_dir: Path,
    repo_root: Path,
    run_cmd,
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
    try:
        result = run_cmd(
            [
                python_executable,
                str(scripts_extract_dir / "parse_hooks.py"),
                *existing_sources,
                "--version",
                frontend_version,
                "--commit",
                frontend_commit,
            ],
            "parse_hooks.py extraction",
            cwd=str(repo_root),
        )
    except RuntimeError as exc:
        print(f"  {exc}")
        print("  parse_hooks.py failed")
        raise RuntimeError("parse_hooks.py extraction failed")

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
    *,
    python_executable: str,
    scripts_extract_dir: Path,
    repo_root: Path,
    run_cmd,
) -> str | None:
    """Run `parse_node_api_schema.py` for the refreshed core snapshot."""
    server_path = core_dir / "server.py"
    io_path = core_dir / "comfy_api" / "latest" / "_io.py"
    basic_types_path = core_dir / "comfy_api" / "latest" / "_input" / "basic_types.py"
    if not server_path.exists() or not io_path.exists() or not basic_types_path.exists():
        return None

    print("\n--- Running parse_node_api_schema.py ---")
    cmd = [
        python_executable,
        str(scripts_extract_dir / "parse_node_api_schema.py"),
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
    try:
        result = run_cmd(
            cmd,
            "parse_node_api_schema.py extraction",
            cwd=str(repo_root),
        )
    except RuntimeError as exc:
        print(f"  {exc}")
        print("  parse_node_api_schema.py failed")
        raise RuntimeError("parse_node_api_schema.py extraction failed")

    for line in result.stdout.strip().splitlines():
        if "Extracted" in line:
            print(f"  {line}")
            return line
    return None


def run_extractors(
    *,
    core_version: str | None,
    core_commit: str | None,
    frontend_version: str | None,
    frontend_commit: str | None,
    snapshot_date: str,
    runtime_object_info_path: str | None,
    snapshots_dir: Path,
    python_executable: str,
    scripts_extract_dir: Path,
    repo_root: Path,
    run_cmd,
) -> dict:
    """Re-run all extractors against the new snapshot files."""
    results = {}
    snapshot_base = snapshots_dir / snapshot_date

    if core_version and core_commit:
        core_dir = snapshot_base / f"comfyui-core-{core_version}"
        server_summary = _run_server_extractor(
            core_dir,
            core_version,
            core_commit,
            python_executable=python_executable,
            scripts_extract_dir=scripts_extract_dir,
            repo_root=repo_root,
            run_cmd=run_cmd,
        )
        if server_summary:
            results["server_endpoints"] = server_summary

    if frontend_version and frontend_commit:
        frontend_dir = snapshot_base / f"comfyui-frontend-{frontend_version}"
        hooks_summary = _run_hooks_extractor(
            frontend_dir,
            frontend_version,
            frontend_commit,
            python_executable=python_executable,
            scripts_extract_dir=scripts_extract_dir,
            repo_root=repo_root,
            run_cmd=run_cmd,
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
            python_executable=python_executable,
            scripts_extract_dir=scripts_extract_dir,
            repo_root=repo_root,
            run_cmd=run_cmd,
        )
        if schema_summary:
            results["node_api_schema"] = schema_summary

    return results


def run_markdown_generation(
    *,
    python_executable: str,
    scripts_generate_dir: Path,
    repo_root: Path,
    run_cmd,
) -> bool:
    """Re-run the markdown generator."""
    print("\n--- Running md_from_json.py ---")
    try:
        result = run_cmd(
            [python_executable, str(scripts_generate_dir / "md_from_json.py")],
            "markdown generation",
            cwd=str(repo_root),
        )
    except RuntimeError as exc:
        print(f"  {exc}")
        print("  md_from_json.py failed")
        return False
    print(f"  {result.stdout.strip()}")
    return True


def load_existing_raw_jsons(references_raw_dir: Path) -> dict[str, dict]:
    """Load the current raw JSON artifacts for later diff reporting."""
    old_jsons = {}
    for json_file in references_raw_dir.glob("*.json"):
        try:
            old_jsons[json_file.name] = json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            old_jsons[json_file.name] = {}
    return old_jsons


def refresh_requested_snapshots(
    core_version: str | None,
    frontend_version: str | None,
    snapshot_date: str,
    *,
    refresh_core,
    refresh_frontend,
) -> tuple[str | None, str | None]:
    """Run the requested core and frontend refresh steps."""
    core_commit = None
    frontend_commit = None

    if core_version:
        core_commit, _ = refresh_core(core_version, snapshot_date)

    if frontend_version:
        frontend_commit, _ = refresh_frontend(frontend_version, snapshot_date)

    return core_commit, frontend_commit


def capture_runtime_object_info(
    args: argparse.Namespace,
    core_commit: str | None,
    *,
    references_raw_dir: Path,
    run_runtime_extraction,
) -> str | None:
    """Run the optional runtime object_info capture flow."""
    if not args.runtime_object_info_url:
        return None

    version = args.runtime_object_info_version or args.core_version or "unversioned"
    commit = args.runtime_object_info_commit or core_commit or ""
    if not run_runtime_extraction(args.runtime_object_info_url, version, commit):
        raise RuntimeError("Runtime extraction failed.")
    return str(references_raw_dir / "object_info_runtime.json")


def print_change_summary(
    old_jsons: dict[str, dict],
    *,
    references_raw_dir: Path,
    compute_diff_summary,
) -> None:
    """Print the post-refresh diff summary for raw JSON artifacts."""
    print("\n=== Change Summary ===")
    for json_file in sorted(references_raw_dir.glob("*.json")):
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


def build_follow_up_commands_from_provenance(provenance_payload: dict) -> list[str]:
    """Return the ordered post-refresh follow-up commands from provenance state."""
    next_steps = provenance_payload.get("next_steps", {})
    commands = [
        next_steps.get("publish_reference_artifacts_command"),
        next_steps.get("verify_artifact_integrity_command"),
        next_steps.get("delta_summary_command"),
        next_steps.get("run_all_command"),
    ]
    return [command for command in commands if command]


def persist_refresh_provenance(
    args: argparse.Namespace,
    snapshot_date: str,
    core_commit: str | None,
    frontend_commit: str | None,
    backup_dir: Path | None,
    *,
    build_refresh_provenance,
    write_refresh_provenance,
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
    provenance_payload.setdefault("next_steps", {})["recommended_follow_up_commands"] = (
        build_follow_up_commands_from_provenance(provenance_payload)
    )
    return write_refresh_provenance(provenance_payload)
