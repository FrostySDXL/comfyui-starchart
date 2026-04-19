#!/usr/bin/env python3
"""Verify extraction idempotency by re-running extractors against pinned snapshots.

Re-runs each extractor using the same arguments stored in JSON metadata and
compares the output to the existing JSON files. Reports any differences.

Usage:
    python scripts/verify/extraction_idempotency.py

Exits 0 if all outputs match, exits 1 with a diff report.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCES_RAW_DIR = REPO_ROOT / "references" / "raw"
SCRIPTS_EXTRACT_DIR = REPO_ROOT / "scripts" / "extract"


def get_extractor_args(json_path: Path) -> tuple[str, list[str]] | None:
    """Determine which extractor script to run and what args to use from JSON metadata.

    Returns (script_name, args) or None if the JSON has no usable metadata.
    """
    data = json.loads(json_path.read_text(encoding="utf-8"))
    metadata = data.get("metadata", {})

    if json_path.name == "server_endpoints.json":
        script = "parse_server.py"
        source = metadata.get("source", "")
        version = metadata.get("version", "")
        commit = metadata.get("commit", "")
        if not source or not version or not commit:
            return None
        # Normalize path separators
        source = source.replace("\\", "/")
        args = [str(REPO_ROOT / source), "--version", version, "--commit", commit]
        return script, args

    elif json_path.name == "js_hooks.json":
        script = "parse_hooks.py"
        sources = metadata.get("sources", [])
        version = metadata.get("version", "")
        commit = metadata.get("commit", "")
        if not sources or not version or not commit:
            return None
        # Normalize path separators
        normalized_sources = [s.replace("\\", "/") for s in sources]
        args = [str(REPO_ROOT / s) for s in normalized_sources]
        args.extend(["--version", version, "--commit", commit])
        return script, args

    elif json_path.name == "node_api_schema.json":
        script = "parse_node_api_schema.py"
        sources = metadata.get("sources", [])
        version = metadata.get("version", "")
        commit = metadata.get("commit", "")
        if not sources or not version or not commit:
            return None
        # Normalize path separators
        normalized_sources = [s.replace("\\", "/") for s in sources]
        args = [str(REPO_ROOT / s) for s in normalized_sources]
        args.extend(["--version", version, "--commit", commit])
        return script, args

    return None


def verify_idempotency(json_path: Path) -> list[str]:
    """Re-run the extractor for a JSON file and compare output.

    Returns a list of difference descriptions. Empty list means match.
    """
    result = get_extractor_args(json_path)
    if result is None:
        return [f"Cannot determine extractor args for {json_path.name}"]

    script_name, args = result
    script_path = SCRIPTS_EXTRACT_DIR / script_name

    # Read current content
    current_content = json_path.read_text(encoding="utf-8")

    # Run the extractor, capturing output to a temp location
    # The extractors write to the same JSON file, so we need to save and restore
    import tempfile
    import shutil

    with tempfile.TemporaryDirectory() as tmpdir:
        # Back up current content
        backup_path = Path(tmpdir) / "backup.json"
        backup_path.write_text(current_content, encoding="utf-8")

        # Run the extractor
        proc = subprocess.run(
            [sys.executable, str(script_path)] + args,
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

        if proc.returncode != 0:
            # Restore backup
            json_path.write_text(backup_path.read_text(encoding="utf-8"), encoding="utf-8")
            return [f"Extractor failed with return code {proc.returncode}: {proc.stderr[:200]}"]

        # Read new content
        new_content = json_path.read_text(encoding="utf-8")

        # Restore backup
        json_path.write_text(backup_path.read_text(encoding="utf-8"), encoding="utf-8")

    # Compare
    if current_content == new_content:
        return []

    # Parse both for structural comparison
    try:
        current_data = json.loads(current_content)
        new_data = json.loads(new_content)
    except json.JSONDecodeError:
        return [f"Output from {script_name} is not valid JSON"]

    # Compare structure
    differences = []
    if current_data.keys() != new_data.keys():
        differences.append(
            f"Top-level keys differ: {current_data.keys()} vs {new_data.keys()}"
        )

    # Compare endpoint/hook counts
    for key in current_data:
        if key == "metadata":
            continue
        current_len = len(current_data[key]) if isinstance(current_data[key], list) else 0
        new_len = len(new_data[key]) if isinstance(new_data[key], list) else 0
        if current_len != new_len:
            differences.append(
                f"{key}: count changed from {current_len} to {new_len}"
            )

    if not differences:
        # Content differs but structure matches -- still a difference
        differences.append(
            f"Content differs after re-running {script_name} "
            f"(byte-level difference, structure may be identical)"
        )

    return differences


def main():
    """Run idempotency verification for all extractable JSON files."""
    all_differences = []
    json_files = sorted(REFERENCES_RAW_DIR.glob("*.json"))

    for json_file in json_files:
        print(f"Checking {json_file.name}...")
        diffs = verify_idempotency(json_file)
        if diffs:
            for diff in diffs:
                print(f"  DIFF: {diff}")
            all_differences.extend([(json_file.name, d) for d in diffs])
        else:
            print(f"  OK: output matches")

    print()
    if not all_differences:
        print("All extraction outputs are idempotent.")
        return 0
    else:
        print(f"Found {len(all_differences)} difference(s) across {len(json_files)} file(s).")
        print("This may indicate the extractor has changed or source files have drifted.")
        return 1


if __name__ == "__main__":
    sys.exit(main())