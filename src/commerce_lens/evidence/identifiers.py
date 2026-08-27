"""Stable identifiers and deterministic fingerprints."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from uuid import uuid4


def generate_id(prefix: str) -> str:
    """Generate a collision-resistant event identifier."""
    normalized = _normalize_prefix(prefix)
    return f"{normalized}_{uuid4().hex}"


def stable_content_id(prefix: str, content_fingerprint: str, *, length: int = 24) -> str:
    """Create a type-prefixed stable ID from a content fingerprint or canonical hash."""
    normalized = _normalize_prefix(prefix)
    fingerprint = content_fingerprint.lower()
    if not _is_sha256_hex(fingerprint):
        fingerprint = sha256_bytes(fingerprint.encode("utf-8"))
    return f"{normalized}_{fingerprint[:length]}"


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: str | Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Fingerprint a file using streaming reads without mutating it."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(payload: object) -> bytes:
    """Serialize JSON-compatible data into deterministic canonical bytes."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def canonical_json_fingerprint(payload: object) -> str:
    return sha256_bytes(canonical_json_bytes(payload))


def _normalize_prefix(prefix: str) -> str:
    normalized = prefix.strip().lower().replace("-", "_")
    if not normalized or not normalized.replace("_", "").isalnum():
        raise ValueError("identifier prefix must be alphanumeric plus underscores")
    return normalized


def _is_sha256_hex(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)

