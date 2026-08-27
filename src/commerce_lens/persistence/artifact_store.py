"""Controlled local artifact paths and immutable source snapshots."""

from __future__ import annotations

import shutil
from pathlib import Path

from commerce_lens.contracts.common import ArtifactReference
from commerce_lens.evidence.identifiers import sha256_file, stable_content_id


class ArtifactStore:
    """Manage local runtime artifact paths under a configured root."""

    REQUIRED_DIRS = ("sources", "canonical", "runs", "temporary")

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()

    def ensure_layout(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        for name in self.REQUIRED_DIRS:
            self.safe_path(name).mkdir(parents=True, exist_ok=True)

    def safe_path(self, *parts: str | Path) -> Path:
        if not parts:
            return self.root
        for part in parts:
            if Path(part).is_absolute():
                raise ValueError("artifact paths must be relative to the artifact root")
        candidate = self.root.joinpath(*map(Path, parts)).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError("artifact path escapes configured root")
        return candidate

    def source_snapshot_path(self, original_name: str, fingerprint: str) -> Path:
        safe_name = Path(original_name).name or "source"
        return self.safe_path("sources", fingerprint[:2], fingerprint, safe_name)

    def snapshot_source(self, source_path: str | Path) -> ArtifactReference:
        self.ensure_layout()
        source = Path(source_path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"source file does not exist: {source}")
        expected_fingerprint = sha256_file(source)
        destination = self.source_snapshot_path(source.name, expected_fingerprint)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            if sha256_file(destination) != expected_fingerprint:
                raise ValueError("existing source snapshot fingerprint mismatch")
        else:
            shutil.copy2(source, destination)
        snapshot_fingerprint = sha256_file(destination)
        if snapshot_fingerprint != expected_fingerprint:
            raise ValueError("source snapshot fingerprint mismatch after copy")
        snapshot_size = destination.stat().st_size
        return ArtifactReference(
            artifact_id=stable_content_id("art", snapshot_fingerprint),
            path=str(destination.relative_to(self.root)),
            fingerprint=snapshot_fingerprint,
            media_type="application/octet-stream",
            size_bytes=snapshot_size,
        )
