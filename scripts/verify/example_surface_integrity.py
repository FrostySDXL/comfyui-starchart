#!/usr/bin/env python3
"""Validate static integrity of repo-local example surfaces."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = REPO_ROOT / "examples"
EXPECTED_EXAMPLE_FAMILIES = (
    "api-calls",
    "consumers",
    "custom-nodes",
    "extensions",
    "workflows",
)
README_REQUIRED_FAMILIES = ("consumers", "custom-nodes", "extensions")
ROUTED_DOC_RELATIVE_PATHS = (
    Path("src/content/docs/start-here/artifact-consumer.md"),
    Path("src/content/docs/start-here/author.md"),
    Path("src/content/docs/start-here/extension-developer.md"),
    Path("src/content/docs/start-here/tooling-builder.md"),
)
KNOWN_REPO_ROOT_PREFIXES = (
    ".github/",
    "src/content/docs/",
    "examples/",
    "references/",
    "scripts/",
    "tests/",
    "livedocs/",
)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
BACKTICK_PATH_RE = re.compile(r"`([^`]+)`")
ROUTED_PATH_RE = re.compile(r"examples/[A-Za-z0-9._/-]+/?")
API_PROMPT_GRAPH_PATH = Path("examples/api-calls/post-prompt.json")
OUTPUT_NODE_CLASS_TYPES = {"PreviewImage", "SaveImage"}


def validate_example_surface(repo_root: Path) -> list[str]:
    errors: list[str] = []
    errors.extend(check_expected_example_families(repo_root))
    errors.extend(check_readme_coverage(repo_root))
    errors.extend(check_routed_example_paths(repo_root))
    errors.extend(check_example_json_files(repo_root))
    errors.extend(check_example_readme_references(repo_root))
    return errors


def check_expected_example_families(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for family in EXPECTED_EXAMPLE_FAMILIES:
        family_path = repo_root / "examples" / family
        if not family_path.is_dir():
            errors.append(
                f"Missing example family directory: {family_path.relative_to(repo_root).as_posix()}"
            )
    return errors


def check_readme_coverage(repo_root: Path) -> list[str]:
    errors: list[str] = []
    examples_dir = repo_root / "examples"

    for family in EXPECTED_EXAMPLE_FAMILIES:
        family_path = examples_dir / family
        if (
            family_path.exists()
            and family_requires_readme(family_path)
            and not (family_path / "README.md").is_file()
        ):
            errors.append(
                f"Missing README.md: {family_path.relative_to(repo_root).as_posix()}/README.md"
            )

    for family in README_REQUIRED_FAMILIES:
        family_path = examples_dir / family
        if not family_path.is_dir():
            continue
        for child in sorted(path for path in family_path.iterdir() if path.is_dir()):
            if not (child / "README.md").is_file():
                errors.append(
                    f"Missing README.md: {child.relative_to(repo_root).as_posix()}/README.md"
                )

    return errors


def check_routed_example_paths(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for relative_doc_path in ROUTED_DOC_RELATIVE_PATHS:
        doc_path = repo_root / relative_doc_path
        if not doc_path.is_file():
            errors.append(f"Missing routed-doc source: {relative_doc_path.as_posix()}")
            continue
        text = doc_path.read_text(encoding="utf-8")
        for routed_path in sorted(set(ROUTED_PATH_RE.findall(text))):
            resolved = repo_root / routed_path.rstrip("/")
            if not resolved.exists():
                errors.append(
                    "Missing routed example path: "
                    f"{routed_path} referenced in {doc_path.relative_to(repo_root).as_posix()}"
                )
    return errors


def check_example_json_files(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for json_path in sorted((repo_root / "examples").rglob("*.json")):
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(
                "Invalid JSON: "
                f"{json_path.relative_to(repo_root).as_posix()} "
                f"(line {exc.lineno}, column {exc.colno}): {exc.msg}"
            )
            continue

        if json_path.relative_to(repo_root) == API_PROMPT_GRAPH_PATH:
            errors.extend(validate_api_prompt_graph_structure(payload, API_PROMPT_GRAPH_PATH))
    return errors


def validate_api_prompt_graph_structure(payload: object, relative_path: Path) -> list[str]:
    """Static proxy for API prompt graph shape; full runtime simulation is deferred."""

    errors: list[str] = []
    if not isinstance(payload, dict):
        return [f"API prompt graph must be an object: {relative_path.as_posix()}"]
    prompt = payload.get("prompt")
    if not isinstance(prompt, dict) or not prompt:
        return [f"API prompt graph missing non-empty prompt object: {relative_path.as_posix()}"]

    has_output_node = False
    for node_id, node in prompt.items():
        if not isinstance(node_id, str):
            errors.append(
                f"API prompt graph node ID must be a string in {relative_path.as_posix()}"
            )
            continue
        if not isinstance(node, dict):
            errors.append(f"API prompt graph node {node_id} must be an object")
            continue
        if node.get("class_type") in OUTPUT_NODE_CLASS_TYPES:
            has_output_node = True
        inputs = node.get("inputs", {})
        if not isinstance(inputs, dict):
            errors.append(f"API prompt graph node {node_id} inputs must be an object")
            continue
        for input_name, input_value in inputs.items():
            if is_linked_input(input_value):
                linked_node_id = input_value[0]
                if linked_node_id not in prompt:
                    errors.append(
                        "API prompt graph broken link: "
                        f"node {node_id} input {input_name} references missing node {linked_node_id}"
                    )

    if not has_output_node:
        errors.append(
            "API prompt graph must include at least one output node "
            f"({', '.join(sorted(OUTPUT_NODE_CLASS_TYPES))}) in {relative_path.as_posix()}"
        )
    return errors


def is_linked_input(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and isinstance(value[0], str)
        and isinstance(value[1], int)
    )


def check_example_readme_references(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for readme_path in sorted((repo_root / "examples").rglob("README.md")):
        text = readme_path.read_text(encoding="utf-8")
        for reference in extract_local_references(text):
            resolved = resolve_reference(repo_root, readme_path.parent, reference)
            if resolved is None:
                continue
            if not resolved.exists():
                errors.append(
                    "Broken local reference: "
                    f"{reference} in {readme_path.relative_to(repo_root).as_posix()}"
                )
    return errors


def extract_local_references(text: str) -> set[str]:
    references: set[str] = set()

    for match in MARKDOWN_LINK_RE.findall(text):
        reference = normalize_reference_token(match)
        if reference is not None:
            references.add(reference)

    for token in BACKTICK_PATH_RE.findall(text):
        reference = normalize_reference_token(token)
        if reference is not None:
            references.add(reference)

    return references


def normalize_reference_token(token: str) -> str | None:
    reference = token.strip()
    if not reference:
        return None
    if any(character.isspace() for character in reference):
        return None
    if reference.startswith(("http://", "https://", "mailto:", "#")):
        return None
    if reference.startswith("<") and reference.endswith(">"):
        return None
    reference = reference.split("#", 1)[0].split("?", 1)[0].strip()
    if not reference:
        return None
    if reference.startswith("GET ") or reference.startswith("POST "):
        return None
    if (
        reference.startswith("/")
        and not reference.startswith("./")
        and not reference.startswith("../")
    ):
        return None
    if "://" in reference:
        return None

    looks_like_path = any(
        reference.startswith(prefix) for prefix in KNOWN_REPO_ROOT_PREFIXES
    ) or reference.startswith(("./", "../"))
    if not looks_like_path:
        return None

    return reference.rstrip("/")


def resolve_reference(repo_root: Path, base_dir: Path, reference: str) -> Path | None:
    if any(reference.startswith(prefix) for prefix in KNOWN_REPO_ROOT_PREFIXES):
        return repo_root / reference
    if reference in {"README.md", "CONTRIBUTING.md", "AGENTS.md"}:
        return repo_root / reference
    return (base_dir / reference).resolve()


def family_requires_readme(family_path: Path) -> bool:
    return any(child.is_file() for child in family_path.iterdir())


def build_summary(repo_root: Path) -> str:
    readmes_checked = len(list((repo_root / "examples").rglob("README.md")))
    json_checked = len(list((repo_root / "examples").rglob("*.json")))
    return (
        "Example surface integrity OK: "
        f"families={len(EXPECTED_EXAMPLE_FAMILIES)}, "
        f"readmes={readmes_checked}, json_files={json_checked}, "
        f"routed_docs={len(ROUTED_DOC_RELATIVE_PATHS)}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate static README/path/JSON integrity for repo-local example surfaces."
    )
    parser.parse_args()

    errors = validate_example_surface(REPO_ROOT)
    if errors:
        for error in errors:
            print(f"FAILED: {error}", file=sys.stderr)
        return 1

    print(build_summary(REPO_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
