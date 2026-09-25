"""Artifact-first immutable persistence for private R7 diagnostic artifacts."""

from __future__ import annotations

import json
from enum import Enum
from typing import TypeVar

from commerce_lens.contracts.common import ArtifactReference, ContractBase
from commerce_lens.contracts.r7 import (
    DiagnosticEvidenceInputSet, DiagnosticExecutionRecord, DiagnosticTestRequest,
    DiagnosticValidationRecord, ExecutedDiagnosticResult, PostTestDiagnosticEvaluation,
    ValidatedDiagnosticResult,
)
from commerce_lens.evidence.identifiers import canonical_json_bytes, canonical_json_fingerprint, sha256_bytes, sha256_file
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore, R7ArtifactIndexRecord


class R7ArtifactType(str, Enum):
    EVIDENCE_INPUT_SET = "diagnostic_evidence_input_set"
    TEST_REQUEST = "diagnostic_test_request"
    EXECUTION_RECORD = "diagnostic_execution_record"
    EXECUTED_RESULT = "executed_diagnostic_result"
    VALIDATION_RECORD = "diagnostic_validation_record"
    VALIDATED_RESULT = "validated_diagnostic_result"
    POSTTEST_EVALUATION = "posttest_diagnostic_evaluation"


class R7ArtifactIntegrityError(RuntimeError):
    pass


T = TypeVar("T", bound=ContractBase)

_MODELS = {
    R7ArtifactType.EVIDENCE_INPUT_SET: DiagnosticEvidenceInputSet,
    R7ArtifactType.TEST_REQUEST: DiagnosticTestRequest,
    R7ArtifactType.EXECUTION_RECORD: DiagnosticExecutionRecord,
    R7ArtifactType.EXECUTED_RESULT: ExecutedDiagnosticResult,
    R7ArtifactType.VALIDATION_RECORD: DiagnosticValidationRecord,
    R7ArtifactType.VALIDATED_RESULT: ValidatedDiagnosticResult,
    R7ArtifactType.POSTTEST_EVALUATION: PostTestDiagnosticEvaluation,
}


class R7Repository:
    def __init__(self, artifact_store: ArtifactStore, metadata_store: MetadataStore) -> None:
        self.artifact_store = artifact_store; self.metadata_store = metadata_store
        self.metadata_store.initialize()

    def persist(self, artifact_type: R7ArtifactType, model: ContractBase) -> ArtifactReference:
        artifact_id, semantic_fp = _identity(artifact_type, model)
        payload = model.model_dump(mode="json")
        content = canonical_json_bytes(payload)
        relative = f"runs/r7/{artifact_type.value}/{artifact_id}.json"
        existing = self.metadata_store.get_r7_artifact_index(artifact_type.value, artifact_id)
        if existing:
            reference = self.metadata_store.get_artifact_reference(existing.artifact_reference_id)
            if not reference or existing.semantic_fingerprint != semantic_fp or self.artifact_store.safe_path(reference.path).read_bytes() != content:
                raise R7ArtifactIntegrityError("immutable R7 artifact overwrite conflict")
            return reference
        reference = self.artifact_store.write_json_artifact(relative, payload)
        if reference.fingerprint != sha256_bytes(content):
            raise R7ArtifactIntegrityError("canonical byte hash mismatch")
        self.metadata_store.insert_artifact_reference(reference)
        self.metadata_store.insert_r7_artifact_index(R7ArtifactIndexRecord(
            artifact_type=artifact_type.value, artifact_id=artifact_id,
            semantic_fingerprint=semantic_fp, artifact_reference_id=reference.artifact_id,
        ))
        self.load(artifact_type, artifact_id)
        return reference

    def load(self, artifact_type: R7ArtifactType, artifact_id: str) -> ContractBase:
        index = self.metadata_store.get_r7_artifact_index(artifact_type.value, artifact_id)
        if index is None:
            raise R7ArtifactIntegrityError("R7 artifact index missing")
        reference = self.metadata_store.get_artifact_reference(index.artifact_reference_id)
        if reference is None:
            raise R7ArtifactIntegrityError("R7 artifact reference missing")
        path = self.artifact_store.safe_path(reference.path)
        if not path.is_file() or sha256_file(path) != reference.fingerprint:
            raise R7ArtifactIntegrityError("R7 artifact byte hash mismatch")
        model = _MODELS[artifact_type].model_validate(json.loads(path.read_text()))
        loaded_id, loaded_fp = _identity(artifact_type, model)
        if loaded_id != artifact_id or loaded_fp != index.semantic_fingerprint:
            raise R7ArtifactIntegrityError("R7 semantic identity mismatch")
        return model


def _identity(artifact_type: R7ArtifactType, model: ContractBase) -> tuple[str, str]:
    pairs = {
        R7ArtifactType.EVIDENCE_INPUT_SET: ("evidence_input_set_id", "evidence_input_set_fingerprint"),
        R7ArtifactType.TEST_REQUEST: ("test_request_id", "request_fingerprint"),
        R7ArtifactType.EXECUTED_RESULT: ("executed_result_id", "result_fingerprint"),
        R7ArtifactType.VALIDATION_RECORD: ("validation_event_id", "validation_fingerprint"),
        R7ArtifactType.VALIDATED_RESULT: ("validated_result_id", "validation_fingerprint"),
        R7ArtifactType.POSTTEST_EVALUATION: ("evaluation_event_id", "evaluation_fingerprint"),
    }
    if artifact_type is R7ArtifactType.EXECUTION_RECORD:
        return model.execution_event_id, canonical_json_fingerprint(model.model_dump(mode="json"))
    id_field, fp_field = pairs[artifact_type]
    return str(getattr(model, id_field)), str(getattr(model, fp_field))
