import json

import pytest

from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore, R7ArtifactIndexRecord
from commerce_lens.persistence.r7_repository import R7ArtifactIntegrityError, R7ArtifactType, R7Repository
from tests.contracts.test_r7_contracts import _evidence_set


def test_r7_index_and_repository_round_trip_are_immutable(tmp_path):
    store = ArtifactStore(tmp_path / "artifacts")
    metadata = MetadataStore(tmp_path / "metadata.sqlite")
    repository = R7Repository(store, metadata)
    evidence = _evidence_set()
    reference = repository.persist(R7ArtifactType.EVIDENCE_INPUT_SET, evidence)
    assert repository.load(R7ArtifactType.EVIDENCE_INPUT_SET, evidence.evidence_input_set_id) == evidence
    assert repository.persist(R7ArtifactType.EVIDENCE_INPUT_SET, evidence) == reference
    assert metadata.schema_version() == 9
    assert len(metadata.list_r7_artifact_indexes()) == 1

    path = store.safe_path(reference.path)
    payload = json.loads(path.read_text())
    payload["diagnostic_proposition_ref"] = "tampered"
    path.write_text(json.dumps(payload))
    with pytest.raises(R7ArtifactIntegrityError, match="byte hash"):
        repository.load(R7ArtifactType.EVIDENCE_INPUT_SET, evidence.evidence_input_set_id)


def test_r7_index_rejects_same_identity_conflict(tmp_path):
    metadata = MetadataStore(tmp_path / "metadata.sqlite"); metadata.initialize()
    record = R7ArtifactIndexRecord(
        artifact_type="x", artifact_id="id", semantic_fingerprint="a" * 64,
        artifact_reference_id="art:1",
    )
    metadata.insert_r7_artifact_index(record)
    with pytest.raises(RuntimeError, match="stable R7 artifact index conflict"):
        metadata.insert_r7_artifact_index(record.model_copy(update={"semantic_fingerprint": "b" * 64}))
