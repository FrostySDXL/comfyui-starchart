#!/usr/bin/env python3
"""Classify published versioned artifact directory completeness.

Usage:
    python scripts/verify/versioned_artifact_completeness.py

The verifier is advisory-first for retained historical directories. Current
version omissions are errors because the manifest's current version key must be
publishable as a complete canonical artifact set.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import NamedTuple

from scripts.common.json_utils import compute_textual_json_sha256
from scripts.verify.published_schema_validation import validate_against_published_artifact_schema

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST_PATH = REPO_ROOT / "public" / "artifacts" / "manifest.json"
DEFAULT_VERSIONS_DIR = REPO_ROOT / "public" / "artifacts" / "versions"
DEFAULT_SCHEMA_DIR = REPO_ROOT / "public" / "artifacts" / "schemas"

REQUIRED_ARTIFACTS = (
    "server_endpoints.json",
    "js_hooks.json",
    "node_api_schema.json",
    "websocket_events.json",
)

RETENTION_EXCEPTIONS = {
    "core-v0.21.1_frontend-v1.45.9_2026-05-18": "legacy-pre-websocket-events",
    "core-v0.22.0_frontend-v1.45.12_2026-05-21": "legacy-pre-websocket-events",
    "core-v0.23.0_frontend-v1.46.6_2026-06-01": "legacy-pre-websocket-events",
}

EXPECTED_RETAINED_COMPLETE_HASHES = {
    "core-v0.23.0_frontend-v1.46.6_2026-06-03": {
        "server_endpoints.json": "4cc10ad89bfeae48bdd45a07e5a672b452ff757a9127f4cdc3f450a752a21568",
        "js_hooks.json": "97b29257626d3a22f0d549e059c23572125f0f4be9f36f7e3630caa9e5f95468",
        "node_api_schema.json": "3cf27a19dbc1ff6f7321c531414a7fa5a27d7764d339492a3d3344e518bdde4c",
        "websocket_events.json": "cfa10c399a5f32b8d244c900313ae0d9e58c0b41ed2b44701f87aa44f6ed3f27",
    },
    "core-v0.24.0_frontend-v1.46.14_2026-06-13": {
        "server_endpoints.json": "5b9617e3983b144049c08373ab7b047b7c94b3db0623c235fea27b8e9442c760",
        "js_hooks.json": "552588680280a964ab867a916f06e5e9a5c0911b3c5dccff72260dc615e643f0",
        "node_api_schema.json": "638ee67eaa5e30f1b29f8797d687cd0d3e9dd35c200fff64dddd405514d4dd29",
        "websocket_events.json": "8e47de995e20eb123fa4fe51edb5c93c602bbf69ebc4cd5b75ccabb3d144d210",
    },
}


class DirectoryClassification(NamedTuple):
    """Classification for one versioned artifact directory."""

    version_key: str
    classification: str
    present_artifacts: tuple[str, ...]
    missing_artifacts: tuple[str, ...]
    unexpected_artifacts: tuple[str, ...]
    retention_exception: str
    recommendation: str


class EvaluationResult(NamedTuple):
    """Versioned artifact evaluation result."""

    current_version_key: str
    rows: tuple[DirectoryClassification, ...]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def by_version(self) -> dict[str, DirectoryClassification]:
        return {row.version_key: row for row in self.rows}


def sorted_retention_exceptions(exceptions: dict[str, str]) -> dict[str, str]:
    """Return retention exceptions sorted deterministically by version key."""
    return {key: exceptions[key] for key in sorted(exceptions)}


def _load_current_version_key(manifest_path: Path) -> str:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    version_key = manifest.get("version_key")
    if not isinstance(version_key, str) or not version_key:
        raise ValueError(f"{manifest_path.as_posix()}: missing non-empty version_key")
    return version_key


def _load_current_artifact_hashes(manifest_path: Path) -> dict[str, str]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError(f"{manifest_path.as_posix()}: missing artifacts object")

    hashes: dict[str, str] = {}
    for artifact_name in REQUIRED_ARTIFACTS:
        entry = artifacts.get(artifact_name)
        if not isinstance(entry, dict):
            raise ValueError(
                f"{manifest_path.as_posix()}: missing artifact entry for {artifact_name}"
            )
        sha256 = entry.get("sha256")
        if not isinstance(sha256, str) or not sha256:
            raise ValueError(f"{manifest_path.as_posix()}: missing sha256 for {artifact_name}")
        hashes[artifact_name] = sha256
    return hashes


def _json_files(directory: Path) -> tuple[str, ...]:
    return tuple(sorted(path.name for path in directory.glob("*.json") if path.is_file()))


def _classify_directory(
    version_dir: Path,
    current_version_key: str,
    exceptions: dict[str, str],
) -> DirectoryClassification:
    version_key = version_dir.name
    present = _json_files(version_dir)
    missing = tuple(name for name in REQUIRED_ARTIFACTS if name not in present)
    unexpected = tuple(name for name in present if name not in REQUIRED_ARTIFACTS)
    exception = exceptions.get(version_key, "")

    if not present:
        classification = "empty"
        recommendation = (
            "recommend follow-up removal if no active references require the placeholder"
        )
    elif version_key == current_version_key and not missing:
        classification = "current-required-complete"
        recommendation = "keep as current canonical versioned artifact set"
    elif version_key == current_version_key:
        classification = "current-required-incomplete"
        recommendation = "regenerate current versioned artifacts before publication"
    elif exception == "legacy-pre-websocket-events" and missing == ("websocket_events.json",):
        classification = "legacy-pre-websocket-events"
        recommendation = (
            "retain documented legacy exception unless source-backed regeneration is needed"
        )
    elif not missing:
        classification = "retained-complete"
        recommendation = "retain under bounded version-history policy"
    else:
        classification = "partial-undocumented"
        recommendation = "document exception or regenerate from source-backed snapshots"

    return DirectoryClassification(
        version_key=version_key,
        classification=classification,
        present_artifacts=present,
        missing_artifacts=missing,
        unexpected_artifacts=unexpected,
        retention_exception=exception,
        recommendation=recommendation,
    )


def _validate_versioned_artifact_file(artifact_path: Path, schema_dir: Path) -> list[str]:
    try:
        data = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [f"{artifact_path.parent.name}/{artifact_path.name}: invalid JSON: {exc}"]
    except OSError as exc:
        return [f"{artifact_path.parent.name}/{artifact_path.name}: failed to read: {exc}"]

    if not isinstance(data, dict):
        return [f"{artifact_path.parent.name}/{artifact_path.name}: top-level value is not a dict"]

    return [
        f"{artifact_path.parent.name}/{artifact_path.name}: {error}"
        for error in validate_against_published_artifact_schema(
            data,
            artifact_path.name,
            schema_dir,
        )
    ]


def _verify_artifact_hash(
    artifact_path: Path,
    expected_sha256: str,
) -> list[str]:
    try:
        actual_sha256 = compute_textual_json_sha256(artifact_path)
    except OSError as exc:
        return [f"{artifact_path.parent.name}/{artifact_path.name}: failed to hash: {exc}"]
    if actual_sha256 == expected_sha256:
        return []
    return [
        f"{artifact_path.parent.name}/{artifact_path.name}: sha256 mismatch: "
        f"expected {expected_sha256}, got {actual_sha256}"
    ]


def evaluate_versioned_artifacts(
    manifest_path: Path,
    versions_dir: Path,
    retention_exceptions: dict[str, str] | None = None,
    schema_dir: Path = DEFAULT_SCHEMA_DIR,
    expected_retained_hashes: dict[str, dict[str, str]] | None = None,
) -> EvaluationResult:
    """Evaluate versioned artifact completeness and retention exceptions."""
    exceptions = sorted_retention_exceptions(retention_exceptions or RETENTION_EXCEPTIONS)
    current_version_key = _load_current_version_key(manifest_path)
    current_artifact_hashes = _load_current_artifact_hashes(manifest_path)
    retained_hashes = (
        expected_retained_hashes
        if expected_retained_hashes is not None
        else EXPECTED_RETAINED_COMPLETE_HASHES
    )
    rows = tuple(
        _classify_directory(path, current_version_key, exceptions)
        for path in sorted(versions_dir.iterdir())
        if path.is_dir()
    )
    errors: list[str] = []
    warnings: list[str] = []

    if current_version_key not in {row.version_key for row in rows}:
        errors.append(f"current version directory is missing: {current_version_key}")

    for row in rows:
        if row.version_key == current_version_key and row.missing_artifacts:
            errors.append(
                f"{row.version_key}: current version is missing required artifacts: "
                f"{', '.join(row.missing_artifacts)}"
            )
        if row.unexpected_artifacts:
            warnings.append(
                f"{row.version_key}: unexpected artifacts: {', '.join(row.unexpected_artifacts)}"
            )
        if row.classification == "empty":
            if row.retention_exception != "empty-legacy-placeholder":
                warnings.append(
                    f"{row.version_key}: empty version directory lacks retention exception"
                )
            else:
                warnings.append(
                    f"{row.version_key}: empty version directory retained as legacy placeholder"
                )
        if row.classification == "partial-undocumented":
            warnings.append(
                f"{row.version_key}: partial version directory missing artifacts without exception: "
                f"{', '.join(row.missing_artifacts)}"
            )
        should_validate_content = row.classification in {
            "current-required-complete",
            "retained-complete",
        }
        for artifact_name in row.present_artifacts:
            if should_validate_content and artifact_name in REQUIRED_ARTIFACTS:
                artifact_path = versions_dir / row.version_key / artifact_name
                errors.extend(
                    _validate_versioned_artifact_file(
                        artifact_path,
                        schema_dir,
                    )
                )
                if row.classification == "current-required-complete":
                    expected_hash = current_artifact_hashes[artifact_name]
                else:
                    expected_hash = retained_hashes.get(row.version_key, {}).get(artifact_name, "")
                if expected_hash:
                    errors.extend(_verify_artifact_hash(artifact_path, expected_hash))
                else:
                    errors.append(
                        f"{row.version_key}/{artifact_name}: missing expected sha256 for "
                        f"{row.classification} artifact"
                    )

    return EvaluationResult(
        current_version_key=current_version_key,
        rows=rows,
        errors=tuple(errors),
        warnings=tuple(sorted(warnings)),
    )


def format_report(result: EvaluationResult) -> str:
    """Format deterministic classification output."""
    lines = [
        "Versioned artifact completeness report",
        f"Current version: {result.current_version_key}",
    ]
    for row in result.rows:
        lines.append(
            f"- {row.version_key}: {row.classification}; "
            f"present={list(row.present_artifacts)}; "
            f"missing={list(row.missing_artifacts)}; "
            f"unexpected={list(row.unexpected_artifacts)}; "
            f"exception={row.retention_exception or 'none'}; "
            f"decision={row.recommendation}"
        )
    if result.errors:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in result.errors)
    if result.warnings:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in result.warnings)
    return "\n".join(lines) + "\n"


def main() -> int:
    """Run versioned artifact completeness checks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest-path", default=str(DEFAULT_MANIFEST_PATH))
    parser.add_argument("--versions-dir", default=str(DEFAULT_VERSIONS_DIR))
    parser.add_argument("--schema-dir", default=str(DEFAULT_SCHEMA_DIR))
    args = parser.parse_args()

    result = evaluate_versioned_artifacts(
        Path(args.manifest_path),
        Path(args.versions_dir),
        RETENTION_EXCEPTIONS,
        Path(args.schema_dir),
    )
    print(format_report(result), end="")
    if result.errors:
        print("Versioned artifact completeness failed.")
        return 1
    print("Versioned artifact completeness check completed with advisory classifications.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
