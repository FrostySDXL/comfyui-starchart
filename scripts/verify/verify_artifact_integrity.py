#!/usr/bin/env python3
"""Verify canonical raw artifacts match published copies and manifest hashes.

Usage:
    python scripts/verify/verify_artifact_integrity.py

Exits 0 if the canonical raw artifacts, published current artifacts, and
manifest checksums are all aligned. Exits 1 on the first integrity failure.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST_PATH = REPO_ROOT / "docs" / "artifacts" / "manifest.json"
DEFAULT_CANONICAL_DIR = REPO_ROOT / "references" / "raw"
DEFAULT_PUBLISHED_DIR = REPO_ROOT / "docs" / "artifacts" / "current"
ARTIFACT_FILES = [
    "server_endpoints.json",
    "js_hooks.json",
    "node_api_schema.json",
]


def compute_sha256(path: Path) -> str:
    """Return a cross-platform SHA-256 hex digest for textual JSON artifacts.

    Git normalizes tracked text files to LF in the index, but Windows working
    trees may contain CRLF. Normalize CRLF to LF before hashing so manifest
    hashes remain stable across platforms and match committed artifact bytes.
    """
    file_bytes = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(file_bytes).hexdigest()


def load_manifest(path: Path) -> dict:
    """Load and return the parsed manifest JSON."""
    return json.loads(path.read_text(encoding="utf-8"))


def verify_integrity(
    manifest_path: Path,
    canonical_dir: Path,
    published_dir: Path,
) -> list[str]:
    """Return a list of integrity failures."""
    errors = []

    if not manifest_path.exists():
        return [f"Missing manifest: {manifest_path}"]

    try:
        manifest = load_manifest(manifest_path)
    except (json.JSONDecodeError, OSError) as exc:
        return [f"Failed to read manifest {manifest_path}: {exc}"]

    manifest_artifacts = manifest.get("artifacts")
    if not isinstance(manifest_artifacts, dict):
        return [f"Manifest artifacts block is missing or invalid: {manifest_path}"]

    for name in ARTIFACT_FILES:
        canonical_path = canonical_dir / name
        published_path = published_dir / name

        if not canonical_path.exists():
            errors.append(f"Missing canonical artifact: {canonical_path}")
            continue
        if not published_path.exists():
            errors.append(f"Missing published artifact: {published_path}")
            continue

        manifest_entry = manifest_artifacts.get(name)
        if not isinstance(manifest_entry, dict):
            errors.append(f"Missing manifest entry for {name}")
            continue

        canonical_hash = compute_sha256(canonical_path)
        published_hash = compute_sha256(published_path)

        if canonical_hash != published_hash:
            errors.append(
                f"Canonical/published mismatch for {name}: "
                f"canonical={canonical_hash} published={published_hash}"
            )

        manifest_hash = manifest_entry.get("sha256")
        if not isinstance(manifest_hash, str) or not manifest_hash:
            errors.append(f"Manifest sha256 missing or invalid for {name}")
            continue

        if manifest_hash != published_hash:
            errors.append(
                f"Manifest hash mismatch for {name}: "
                f"manifest={manifest_hash} published={published_hash}"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify canonical raw artifacts, published copies, and manifest hashes stay aligned."
    )
    parser.add_argument(
        "--manifest-path",
        default=str(DEFAULT_MANIFEST_PATH),
        help="Path to docs/artifacts/manifest.json",
    )
    parser.add_argument(
        "--canonical-dir",
        default=str(DEFAULT_CANONICAL_DIR),
        help="Directory containing canonical references/raw artifact JSON files",
    )
    parser.add_argument(
        "--published-dir",
        default=str(DEFAULT_PUBLISHED_DIR),
        help="Directory containing published docs/artifacts/current artifact JSON files",
    )
    args = parser.parse_args()

    errors = verify_integrity(
        manifest_path=Path(args.manifest_path),
        canonical_dir=Path(args.canonical_dir),
        published_dir=Path(args.published_dir),
    )

    if errors:
        print("Artifact integrity verification failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Artifact integrity verified for canonical published artifacts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
