#!/usr/bin/env python3
"""Validate governance lifecycle and new-surface policy records.

Usage:
    python scripts/verify/governance_lifecycle.py

The verifier is advisory-first. Structural lifecycle manifest violations exit 1.
Policy wiring and stale-review findings are reported as warnings while this
signal is being tuned.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "references" / "verifier-lifecycle.json"
CONTRIBUTING_PATH = REPO_ROOT / "CONTRIBUTING.md"
MACHINE_ARTIFACTS_PATH = (
    REPO_ROOT / "src" / "content" / "docs" / "reference" / "machine-readable-artifacts.md"
)
RUN_ALL_PATH = REPO_ROOT / "scripts" / "verify" / "run_all.py"
CI_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"
ADVISORY_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "advisory-checks.yml"
VERIFY_DIR = REPO_ROOT / "scripts" / "verify"
SCHEMA_DIR = REPO_ROOT / "public" / "artifacts" / "schemas"
SUPPORT_ARTIFACT_DIR = REPO_ROOT / "public" / "artifacts"

LIFECYCLE_REVIEW_MAX_AGE_DAYS = 180

REQUIRED_FIELDS = (
    "purpose",
    "owner",
    "target_surface",
    "false_positive_tolerance",
    "placement",
    "promotion_criteria",
    "demotion_criteria",
    "removal_criteria",
    "last_reviewed",
)
VALID_PLACEMENTS = {"blocking", "supplemental", "advisory", "manual", "workflow"}
VALID_FALSE_POSITIVE_LEVELS = {"none", "low", "medium", "high"}
HELPER_MODULE_PREFIXES = ("schema_",)
HELPER_MODULES = {"__init__.py", "published_schema_validation.py"}


def _repo_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def canonical_manifest_text(data: dict[str, Any]) -> str:
    """Return the canonical JSON serialization for the lifecycle manifest."""
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    """Load the lifecycle manifest."""
    return json.loads(path.read_text(encoding="utf-8"))


def direct_verifier_paths(verify_dir: Path = VERIFY_DIR) -> set[str]:
    """Return standalone verifier scripts that require lifecycle records."""
    paths: set[str] = set()
    for path in verify_dir.glob("*.py"):
        if path.name in HELPER_MODULES:
            continue
        if path.name.startswith(HELPER_MODULE_PREFIXES):
            continue
        paths.add(_repo_path(path))
    return paths


def inventory_keys(contributing_text: str) -> set[str]:
    """Extract code-spanned verifier/workflow keys from inventory table rows."""
    marker = "## Verifier Inventory"
    if marker not in contributing_text:
        return set()
    inventory = contributing_text.split(marker, 1)[1]
    keys: set[str] = set()
    for line in inventory.splitlines():
        if not line.startswith("|"):
            continue
        match = re.search(r"`([^`]+)`", line)
        if match:
            keys.add(match.group(1))
    return keys


def _validate_false_positive_tolerance(key: str, value: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return [f"{key}: false_positive_tolerance must be an object"]
    unexpected = set(value) - {"level", "justification"}
    missing = {"level", "justification"} - set(value)
    if unexpected:
        errors.append(f"{key}: false_positive_tolerance has unexpected keys: {sorted(unexpected)}")
    if missing:
        errors.append(f"{key}: false_positive_tolerance missing keys: {sorted(missing)}")
    level = value.get("level")
    if level not in VALID_FALSE_POSITIVE_LEVELS:
        errors.append(
            f"{key}: false_positive_tolerance.level must be one of {sorted(VALID_FALSE_POSITIVE_LEVELS)}"
        )
    justification = value.get("justification")
    if not isinstance(justification, str) or not justification.strip():
        errors.append(f"{key}: false_positive_tolerance.justification must be non-empty")
    return errors


def validate_lifecycle_records(
    manifest: dict[str, Any], today: dt.date | None = None
) -> tuple[list[str], list[str]]:
    """Validate manifest shape, required fields, and review-age warnings."""
    if today is None:
        today = dt.date.today()
    errors: list[str] = []
    warnings: list[str] = []

    records = manifest.get("records")
    exemptions = manifest.get("exemptions", {})
    if not isinstance(records, dict):
        return ["manifest.records must be an object"], warnings
    if not isinstance(exemptions, dict):
        errors.append("manifest.exemptions must be an object")

    for key, record in sorted(records.items()):
        if not isinstance(record, dict):
            errors.append(f"{key}: lifecycle record must be an object")
            continue
        for field in REQUIRED_FIELDS:
            if field not in record:
                errors.append(f"{key}: missing required field {field}")
        placement = record.get("placement")
        if placement not in VALID_PLACEMENTS:
            errors.append(f"{key}: placement must be one of {sorted(VALID_PLACEMENTS)}")
        errors.extend(
            _validate_false_positive_tolerance(key, record.get("false_positive_tolerance"))
        )
        reviewed = record.get("last_reviewed")
        if not isinstance(reviewed, str):
            errors.append(f"{key}: last_reviewed must be an ISO-8601 date string")
            continue
        try:
            reviewed_date = dt.date.fromisoformat(reviewed)
        except ValueError:
            errors.append(f"{key}: last_reviewed must be an ISO-8601 date string")
            continue
        if today - reviewed_date > dt.timedelta(days=LIFECYCLE_REVIEW_MAX_AGE_DAYS):
            warnings.append(
                f"{key}: last_reviewed {reviewed} is older than "
                f"{LIFECYCLE_REVIEW_MAX_AGE_DAYS} days"
            )

    expected = direct_verifier_paths()
    missing = sorted(expected - set(records) - set(exemptions))
    for key in missing:
        errors.append(f"{key}: direct verifier has no lifecycle record or exemption")

    contributing_text = CONTRIBUTING_PATH.read_text(encoding="utf-8")
    for key in sorted(inventory_keys(contributing_text) - set(records) - set(exemptions)):
        errors.append(f"{key}: inventory row has no lifecycle record or exemption")

    return errors, warnings


def check_manifest_serialization(path: Path = MANIFEST_PATH) -> list[str]:
    """Return errors if the lifecycle manifest is not canonical JSON."""
    data = load_manifest(path)
    actual = path.read_text(encoding="utf-8")
    expected = canonical_manifest_text(data)
    if actual != expected:
        return [f"{_repo_path(path)}: JSON must be sorted with stable two-space indentation"]
    return []


def check_wiring(
    manifest: dict[str, Any],
    run_all_text: str,
    ci_text: str,
    advisory_text: str,
) -> list[str]:
    """Return advisory warnings for lifecycle placement wiring drift."""
    warnings: list[str] = []
    records = manifest.get("records", {})
    for key, record in sorted(records.items()):
        if not isinstance(record, dict):
            continue
        if not key.startswith("scripts/verify/"):
            continue
        script_name = Path(key).name
        placement = record.get("placement")
        if placement == "blocking":
            if script_name not in run_all_text:
                warnings.append(f"{key}: placement=blocking but not referenced in run_all.py")
            if key not in ci_text and script_name not in ci_text:
                warnings.append(f"{key}: placement=blocking but not referenced in ci.yml")
        elif (
            placement == "advisory"
            and key not in advisory_text
            and script_name not in advisory_text
        ):
            warnings.append(f"{key}: placement=advisory but not referenced in advisory-checks.yml")
    return warnings


def _walk_schema_closures(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        if value.get("additionalProperties") is False:
            found.append(path)
        for key, child in value.items():
            found.extend(_walk_schema_closures(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_walk_schema_closures(child, f"{path}[{index}]"))
    return found


def check_schema_closure_policy(contributing_text: str) -> list[str]:
    """Warn when closed schema objects lack documented policy coverage."""
    warnings: list[str] = []
    for schema_file in sorted(SCHEMA_DIR.glob("*.json")):
        data = json.loads(schema_file.read_text(encoding="utf-8"))
        closures = _walk_schema_closures(data)
        if not closures:
            continue
        repo_path = _repo_path(schema_file)
        if repo_path not in contributing_text:
            warnings.append(
                f"{repo_path}: closed schema object lacks CONTRIBUTING.md closure entry"
            )
    return warnings


def check_support_artifact_policy(machine_text: str, contributing_text: str) -> list[str]:
    """Warn when published support artifacts lack classification/admission text."""
    warnings: list[str] = []
    for artifact in sorted(SUPPORT_ARTIFACT_DIR.glob("*.json")):
        name = artifact.name
        if name not in machine_text:
            warnings.append(
                f"public/artifacts/{name}: missing machine-readable artifact classification"
            )
        if f"Admission case: `{name}`" not in contributing_text:
            warnings.append(f"public/artifacts/{name}: missing CONTRIBUTING.md admission case")
    return warnings


def main() -> int:
    """Run governance lifecycle checks."""
    errors: list[str] = []
    warnings: list[str] = []

    manifest = load_manifest()
    errors.extend(check_manifest_serialization())
    lifecycle_errors, lifecycle_warnings = validate_lifecycle_records(manifest)
    errors.extend(lifecycle_errors)
    warnings.extend(lifecycle_warnings)

    contributing_text = CONTRIBUTING_PATH.read_text(encoding="utf-8")
    machine_text = MACHINE_ARTIFACTS_PATH.read_text(encoding="utf-8")
    warnings.extend(
        check_wiring(
            manifest,
            RUN_ALL_PATH.read_text(encoding="utf-8"),
            CI_WORKFLOW_PATH.read_text(encoding="utf-8"),
            ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8"),
        )
    )
    warnings.extend(check_schema_closure_policy(contributing_text))
    warnings.extend(check_support_artifact_policy(machine_text, contributing_text))

    if errors:
        print("GOVERNANCE LIFECYCLE ERRORS:")
        for error in errors:
            print(f"  {error}")
    if warnings:
        print("GOVERNANCE LIFECYCLE WARNINGS:")
        for warning in warnings:
            print(f"  {warning}")
    if not errors and not warnings:
        print("Governance lifecycle policy records are current.")
    elif not errors:
        print("Governance lifecycle policy records are structurally valid with advisory warnings.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
