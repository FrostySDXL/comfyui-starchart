from __future__ import annotations

import hashlib
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    """Load a JSON object from disk."""
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    """Write a JSON object with deterministic formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def compute_textual_json_sha256(path: Path) -> str:
    """Return a cross-platform SHA-256 digest for tracked textual JSON files."""
    file_bytes = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(file_bytes).hexdigest()


def compute_bytes_sha256(data: bytes) -> str:
    """Return the SHA-256 hex digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()
