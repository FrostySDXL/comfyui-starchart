#!/usr/bin/env python3
"""Verify refresh provenance flags and follow-up chain consistency.

Usage:
    python scripts/verify/provenance_chain_integrity.py

The verifier is advisory-first for stale backup references and reverse-direction
flag drift. Broken required follow-up ordering or true flags without matching
artifact state are errors.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parents[2]
PROVENANCE_PATH = REPO_ROOT / "public" / "artifacts" / "refresh-provenance.json"
DELTA_SUMMARY_PATH = REPO_ROOT / "public" / "artifacts" / "delta-summary.json"
MANIFEST_PATH = REPO_ROOT / "public" / "artifacts" / "manifest.json"
CURRENT_DIR = REPO_ROOT / "public" / "artifacts" / "current"
REQUIRED_CURRENT_ARTIFACTS = (
    "server_endpoints.json",
    "js_hooks.json",
    "node_api_schema.json",
    "websocket_events.json",
)


class ProvenanceEvaluation(NamedTuple):
    """Provenance chain evaluation output."""

    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def _load_json_if_exists(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_repo_path(repo_root: Path, path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return repo_root / path


def _current_artifact_state_exists(repo_root: Path) -> bool:
    manifest = repo_root / "public" / "artifacts" / "manifest.json"
    current = repo_root / "public" / "artifacts" / "current"
    return manifest.is_file() and all(
        (current / name).is_file() for name in REQUIRED_CURRENT_ARTIFACTS
    )


def _expected_follow_up_commands(provenance: dict) -> list[str]:
    next_steps = provenance.get("next_steps", {})
    expected = [
        next_steps.get("publish_reference_artifacts_command"),
        next_steps.get("verify_artifact_integrity_command"),
    ]
    backup_location = provenance.get("backup_location")
    delta_command = next_steps.get("delta_summary_command")
    if backup_location and delta_command:
        expected.append(delta_command)
    expected.append(next_steps.get("run_all_command"))
    return [command for command in expected if isinstance(command, str)]


def validate_recommended_follow_up_order(provenance: dict) -> list[str]:
    """Return errors when recommended follow-up commands are absent or out of order."""
    next_steps = provenance.get("next_steps", {})
    actual = next_steps.get("recommended_follow_up_commands")
    expected = _expected_follow_up_commands(provenance)
    if actual != expected:
        return [
            "next_steps.recommended_follow_up_commands must be ordered as "
            "publish, verify integrity, delta summary when backup exists, run_all"
        ]
    return []


def validate_stale_backup_reference(
    repo_root: Path, provenance: dict, delta_summary: dict
) -> list[str]:
    """Return sorted warnings for stale backup_location references."""
    backup_location = provenance.get("backup_location")
    if not isinstance(backup_location, str) or not backup_location:
        return []

    warnings: list[str] = []
    backup_path = _resolve_repo_path(repo_root, backup_location)
    if not backup_path.exists():
        warnings.append(f"backup_location {backup_location} is missing on disk")
    elif backup_path.is_dir() and not any(backup_path.iterdir()):
        warnings.append(f"backup_location {backup_location} is empty on disk")

    comparison = delta_summary.get("comparison", {}) if isinstance(delta_summary, dict) else {}
    if comparison.get("old") != backup_location:
        warnings.append(
            f"backup_location {backup_location} is not referenced by delta-summary.json comparison.old"
        )
    return sorted(warnings)


def _validate_true_flags(repo_root: Path, provenance: dict, delta_summary: dict) -> list[str]:
    errors: list[str] = []
    published = provenance.get("published", {})
    backup_location = provenance.get("backup_location")
    if published.get("canonical_artifacts_updated_by_refresh") is True:
        if not _current_artifact_state_exists(repo_root):
            errors.append(
                "published.canonical_artifacts_updated_by_refresh is true but manifest/current artifacts are incomplete"
            )
    if published.get("delta_summary_updated_by_refresh") is True:
        if not (repo_root / "public" / "artifacts" / "delta-summary.json").is_file():
            errors.append(
                "published.delta_summary_updated_by_refresh is true but delta-summary.json is missing"
            )
        elif backup_location:
            comparison = (
                delta_summary.get("comparison", {}) if isinstance(delta_summary, dict) else {}
            )
            if comparison.get("old") != backup_location:
                errors.append(
                    "delta-summary.json comparison.old does not match provenance backup_location"
                )
    return errors


def _reverse_flag_warnings(repo_root: Path, provenance: dict) -> list[str]:
    warnings: list[str] = []
    published = provenance.get("published", {})
    if published.get("canonical_artifacts_updated_by_refresh") is False:
        if _current_artifact_state_exists(repo_root):
            warnings.append("canonical artifacts exist but flag is false")
    if published.get("delta_summary_updated_by_refresh") is False:
        if (repo_root / "public" / "artifacts" / "delta-summary.json").is_file():
            warnings.append("delta-summary.json exists but flag is false")
    return warnings


def evaluate_provenance_chain(repo_root: Path = REPO_ROOT) -> ProvenanceEvaluation:
    """Evaluate provenance chain consistency for a repository root."""
    provenance = _load_json_if_exists(
        repo_root / "public" / "artifacts" / "refresh-provenance.json"
    )
    delta_summary = _load_json_if_exists(repo_root / "public" / "artifacts" / "delta-summary.json")
    if not provenance:
        return ProvenanceEvaluation(("public/artifacts/refresh-provenance.json is missing",), ())

    errors: list[str] = []
    warnings: list[str] = []
    errors.extend(validate_recommended_follow_up_order(provenance))
    errors.extend(_validate_true_flags(repo_root, provenance, delta_summary))
    warnings.extend(validate_stale_backup_reference(repo_root, provenance, delta_summary))
    warnings.extend(_reverse_flag_warnings(repo_root, provenance))
    return ProvenanceEvaluation(tuple(sorted(errors)), tuple(sorted(warnings)))


def format_report(result: ProvenanceEvaluation) -> str:
    """Format deterministic provenance-chain output."""
    lines = ["Refresh provenance chain integrity report"]
    if result.errors:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in result.errors)
    if result.warnings:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in result.warnings)
    if not result.errors and not result.warnings:
        lines.append("No provenance chain issues found.")
    return "\n".join(lines) + "\n"


def main() -> int:
    """Run provenance chain integrity checks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    args = parser.parse_args()
    result = evaluate_provenance_chain(Path(args.repo_root))
    print(format_report(result), end="")
    if result.errors:
        print("Refresh provenance chain integrity failed.")
        return 1
    print("Refresh provenance chain integrity check completed with advisory warnings if listed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
