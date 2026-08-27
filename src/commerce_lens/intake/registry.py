"""Dataset registration for read-only sources."""

from __future__ import annotations

from pathlib import Path

from commerce_lens.contracts.evidence import DatasetReference
from commerce_lens.contracts.common import SourceType
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, stable_content_id
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore


class DatasetRegistry:
    """Register immutable source references and optional local snapshots."""

    def __init__(self, artifact_store: ArtifactStore, metadata_store: MetadataStore | None = None) -> None:
        self.artifact_store = artifact_store
        self.metadata_store = metadata_store

    def register_source(
        self,
        source_path: str | Path,
        source_type: SourceType,
        *,
        selected_sheet: str | None = None,
        selected_table: str | None = None,
        metadata: dict[str, str | int | float | bool | None] | None = None,
    ) -> DatasetReference:
        path = Path(source_path).expanduser().resolve()
        snapshot = self.artifact_store.snapshot_source(path)
        identity_fingerprint = canonical_json_fingerprint(
            {
                "source_type": source_type.value,
                "content_fingerprint": snapshot.fingerprint,
                "selected_sheet": selected_sheet,
                "selected_table": selected_table,
            }
        )
        dataset = DatasetReference(
            dataset_id=stable_content_id("ds", identity_fingerprint),
            source_type=source_type,
            original_name=path.name,
            content_fingerprint=snapshot.fingerprint or "",
            size_bytes=path.stat().st_size,
            snapshot_artifact=snapshot,
            selected_sheet=selected_sheet,
            selected_table=selected_table,
            metadata=metadata or {},
        )
        if self.metadata_store is not None:
            self.metadata_store.initialize()
            return self.metadata_store.insert_dataset(dataset)
        return dataset

