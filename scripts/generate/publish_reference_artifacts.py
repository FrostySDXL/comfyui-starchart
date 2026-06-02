#!/usr/bin/env python3
"""Publish canonical extracted JSON artifacts into a stable, web-served public subtree.

Reads exactly three canonical artifacts from references/raw/:
- server_endpoints.json
- js_hooks.json
- node_api_schema.json

Excludes runtime-only artifacts such as object_info_runtime.json.

Writes:
- public/artifacts/current/<artifact>.json  (stable current copies)
- public/artifacts/versions/<key>/<artifact>.json  (versioned copies)
- public/artifacts/manifest.json  (discovery metadata)

Usage:
    python scripts/generate/publish_reference_artifacts.py
"""

import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Any

from scripts.common.display_path import display_path
from scripts.common.json_utils import compute_textual_json_sha256, load_json, write_json

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = REPO_ROOT / "references" / "raw"
OUTPUT_ROOT = REPO_ROOT / "public" / "artifacts"
CURRENT_DIR = OUTPUT_ROOT / "current"
VERSIONS_DIR = OUTPUT_ROOT / "versions"
SCHEMAS_DIR = OUTPUT_ROOT / "schemas"

ARTIFACT_SCHEMA_VERSION = "1.0.0"

ARTIFACT_FILES = [
    "server_endpoints.json",
    "js_hooks.json",
    "node_api_schema.json",
]


def _compute_sha256(path: Path) -> str:
    """Return a cross-platform SHA-256 hex digest for textual JSON artifacts.

    Git stores tracked text files with LF line endings, but Windows working
    trees may materialize them as CRLF. Normalize CRLF to LF before hashing so
    published manifest hashes are stable across operating systems.
    """
    return compute_textual_json_sha256(path)


def _derive_version_key(artifacts: dict[str, dict]) -> str:
    """Build a deterministic, human-readable version key from artifact metadata.

    Uses the core version (from server_endpoints or node_api_schema) and the
    frontend version (from js_hooks), plus the oldest extracted date present.
    """
    core_meta = artifacts.get("server_endpoints.json", {}).get("metadata", {})
    frontend_meta = artifacts.get("js_hooks.json", {}).get("metadata", {})

    core_version = core_meta.get("version", "unknown")
    frontend_version = frontend_meta.get("version", "unknown")

    dates = []
    for name in ARTIFACT_FILES:
        meta = artifacts.get(name, {}).get("metadata", {})
        d = meta.get("extracted_date")
        if d:
            dates.append(d)

    oldest_date = min(dates) if dates else "unknown"
    return f"core-{core_version}_frontend-{frontend_version}_{oldest_date}"


def _check_staleness(artifacts: dict[str, dict]) -> None:
    """Log warnings if any artifact looks stale based on extracted_date."""
    today = date.today()
    for name in ARTIFACT_FILES:
        meta = artifacts.get(name, {}).get("metadata", {})
        extracted = meta.get("extracted_date")
        if not extracted:
            print(f"WARNING: {name} has no extracted_date. Verify freshness before publishing.")
            continue
        try:
            extracted_dt = datetime.strptime(extracted, "%Y-%m-%d").date()
            age_days = (today - extracted_dt).days
            if age_days > 30:
                print(f"WARNING: {name} extracted_date is {age_days} days old ({extracted}).")
        except ValueError:
            print(f"WARNING: {name} has an unparsable extracted_date: {extracted}")


def _site_rel(file_path: Path) -> str:
    """Return a site-relative URL path using forward slashes.

    Paths are relative to the public root and omit a leading slash so they
    resolve correctly on GitHub Pages project sites as well as custom domains.
    """
    rel = file_path.relative_to(REPO_ROOT / "public")
    return rel.as_posix()


def build_manifest(
    artifacts: dict[str, dict],
    version_key: str,
    artifact_hashes: dict[str, str],
) -> dict:
    """Build the artifact manifest.

    Omits a dynamic timestamp so the manifest is deterministic for the same
    input artifacts. Idempotency matters for git diff hygiene and freshness
    verification.
    """
    manifest: dict[str, Any] = {
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "version_key": version_key,
        "schemas": {},
        "artifacts": {},
    }

    for name in ARTIFACT_FILES:
        schema_name = name.replace(".json", ".schema.json")
        manifest["schemas"][name] = {
            "schema_url": _site_rel(SCHEMAS_DIR / schema_name),
        }

    for name in ARTIFACT_FILES:
        meta = artifacts.get(name, {}).get("metadata", {})
        current_path = CURRENT_DIR / name
        versioned_path = VERSIONS_DIR / version_key / name

        manifest["artifacts"][name] = {
            "current_url": _site_rel(current_path),
            "versioned_url": _site_rel(versioned_path),
            "sha256": artifact_hashes[name],
            "version": meta.get("version", "unknown"),
            "commit": meta.get("commit", "unknown"),
            "extracted_date": meta.get("extracted_date", "unknown"),
            "sources": meta.get("sources") or [],
        }

    return manifest


def _ensure_published_schema_files_exist() -> bool:
    """Return True when all published schema files exist, else print an error."""
    missing = False
    for name in ARTIFACT_FILES:
        schema_name = name.replace(".json", ".schema.json")
        schema_path = SCHEMAS_DIR / schema_name
        if not schema_path.exists():
            print(f"ERROR: Published schema file not found: {display_path(schema_path)}")
            missing = True
    return not missing


def main() -> int:
    if not _ensure_published_schema_files_exist():
        return 1

    artifacts: dict[str, dict] = {}
    for name in ARTIFACT_FILES:
        path = SOURCE_DIR / name
        if not path.exists():
            print(f"ERROR: Required artifact not found: {display_path(path)}")
            return 1
        artifacts[name] = load_json(path)

    print("Artifact dates:")
    for name in ARTIFACT_FILES:
        meta = artifacts[name].get("metadata", {})
        extracted = meta.get("extracted_date", "N/A")
        print(f"  {name}: extracted_date={extracted}")

    _check_staleness(artifacts)

    version_key = _derive_version_key(artifacts)
    versioned_dir = VERSIONS_DIR / version_key
    artifact_hashes = {}

    # Write current and versioned copies
    CURRENT_DIR.mkdir(parents=True, exist_ok=True)
    versioned_dir.mkdir(parents=True, exist_ok=True)
    for name in ARTIFACT_FILES:
        source_path = SOURCE_DIR / name
        current_path = CURRENT_DIR / name
        versioned_path = versioned_dir / name
        artifact_hashes[name] = _compute_sha256(source_path)

        shutil.copy2(str(source_path), str(current_path))
        shutil.copy2(str(source_path), str(versioned_path))

    # Write manifest
    manifest = build_manifest(artifacts, version_key, artifact_hashes)
    manifest_path = OUTPUT_ROOT / "manifest.json"
    write_json(manifest_path, manifest)

    print(f"Published artifacts to {display_path(OUTPUT_ROOT)}")
    print(f"  Current:  {display_path(CURRENT_DIR)}")
    print(f"  Versioned: {display_path(versioned_dir)}")
    print(f"  Manifest: {display_path(manifest_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
