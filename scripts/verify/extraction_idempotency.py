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
        source = source.replace("\\", "/")
        args = [source, "--version", version, "--commit", commit]
        return script, args

    elif json_path.name == "js_hooks.json":
        script = "parse_hooks.py"
        sources = metadata.get("sources", [])
        version = metadata.get("version", "")
        commit = metadata.get("commit", "")
        if not sources or not version or not commit:
            return None
        normalized_sources = [s.replace("\\", "/") for s in sources]
        args = normalized_sources.copy()
        args.extend(["--version", version, "--commit", commit])
        return script, args

    elif json_path.name == "node_api_schema.json":
        script = "parse_node_api_schema.py"
        sources = metadata.get("sources", [])
        version = metadata.get("version", "")
        commit = metadata.get("commit", "")
        if not sources or not version or not commit:
            return None
        normalized_sources = [s.replace("\\", "/") for s in sources]
        args = normalized_sources.copy()
        args.extend(["--version", version, "--commit", commit])
        return script, args

    return None


def _normalize_paths(value):
    if isinstance(value, str):
        normalized = value.replace("\\", "/")
        repo_root = str(REPO_ROOT).replace("\\", "/") + "/"
        if normalized.startswith(repo_root):
            return normalized[len(repo_root):]
        return normalized
    if isinstance(value, list):
        return [_normalize_paths(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_paths(item) for key, item in value.items()}
    return value


def _normalize_for_comparison(data: dict) -> dict:
    normalized = _normalize_paths(data)
    metadata = dict(normalized.get("metadata", {}))
    metadata.pop("extracted_date", None)
    normalized["metadata"] = metadata
    return normalized


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

    current_normalized = _normalize_for_comparison(current_data)
    new_normalized = _normalize_for_comparison(new_data)
    differences = []

    if current_normalized == new_normalized:
        return []

    if current_normalized.keys() != new_normalized.keys():
        differences.append(
            f"Top-level keys differ: {current_normalized.keys()} vs {new_normalized.keys()}"
        )

    for key in current_normalized:
        if key == "metadata":
            continue
        current_value = current_normalized.get(key)
        new_value = new_normalized.get(key)
        if isinstance(current_value, list) and isinstance(new_value, list):
            if len(current_value) != len(new_value):
                differences.append(
                    f"{key}: count changed from {len(current_value)} to {len(new_value)}"
                )

    if not differences:
        differences.append(
            f"Normalized content differs after re-running {script_name}"
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
