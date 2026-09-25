"""Artifact-first immutable persistence for private R7 diagnostic artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import TypeVar

from commerce_lens.contracts.common import ArtifactReference, ContractBase
from commerce_lens.contracts.r7 import (
    DiagnosticEvidenceInputSet, DiagnosticExecutionRecord, DiagnosticTestRequest,
    DiagnosticValidationRecord, ExecutedDiagnosticResult, PostTestDiagnosticEvaluation,
    ValidatedDiagnosticResult,
)
from commerce_lens.contracts.diagnostic import AnalyticalOutcome
from commerce_lens.contracts.hypotheses import R6ToR7Handoff
from commerce_lens.diagnostic.r7_evidence_authentication import (
    TrustedR7EvidenceAuthority,
    authenticate_evidence_input_set,
)
from commerce_lens.diagnostic.r7_method_registry import R7_METHOD_REGISTRY
from commerce_lens.diagnostic.governance import PreTestAuthorityRegistry
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


@dataclass(frozen=True)
class CompleteR7Lineage:
    evaluation: PostTestDiagnosticEvaluation
    validated_result: ValidatedDiagnosticResult
    validation_record: DiagnosticValidationRecord
    executed_result: ExecutedDiagnosticResult
    execution_record: DiagnosticExecutionRecord
    request: DiagnosticTestRequest
    evidence_inputs: DiagnosticEvidenceInputSet
    r6_handoff: R6ToR7Handoff


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

    def load_complete_posttest_evaluation(
        self,
        evaluation_id: str,
        *,
        r6_repository,
        authority_registry: PreTestAuthorityRegistry,
        trusted_evidence_authority: TrustedR7EvidenceAuthority,
    ) -> CompleteR7Lineage:
        """Reload and authenticate the complete R6→R7 terminal graph."""
        evaluation = self.load(R7ArtifactType.POSTTEST_EVALUATION, evaluation_id)
        if evaluation.validated_result_ref is None:
            self._lineage_fail("terminal evaluation has no validated result")
        validated = self.load(R7ArtifactType.VALIDATED_RESULT, evaluation.validated_result_ref)
        validation = self.load(R7ArtifactType.VALIDATION_RECORD, evaluation.validation_event_ref)
        executed = self.load(R7ArtifactType.EXECUTED_RESULT, validation.executed_result_ref)
        execution = self.load(R7ArtifactType.EXECUTION_RECORD, evaluation.execution_event_ref)
        request = self.load(R7ArtifactType.TEST_REQUEST, evaluation.test_request_ref)
        evidence = self.load(R7ArtifactType.EVIDENCE_INPUT_SET, request.evidence_input_set_ref)

        handoff = r6_repository.load_r6_to_r7_handoff(
            request.handoff_ref, authority_registry=authority_registry,
        )
        R7_METHOD_REGISTRY.authenticate_bundle(
            method=request.method, support_criterion=request.support_criterion,
            validation_profile=request.validation_profile, implementation=request.implementation,
            family_id=handoff.family_id, family_version=handoff.family_version,
            family_fingerprint=handoff.family_fingerprint,
        )
        pretest = r6_repository.load_pretest_diagnostic_evaluation(
            handoff.pretest_evaluation_ref, authority_registry=authority_registry,
        )
        profile = r6_repository.load_resolved_required_evidence_profile(
            handoff.resolved_profile_ref, authority_registry=authority_registry,
        )
        judgments = r6_repository.load_requirement_judgment_bundle(
            pretest.requirement_judgment_bundle_ref, profile=profile,
        )
        authenticate_evidence_input_set(
            evidence, judgments=judgments, trusted_authority=trusted_evidence_authority,
            authority_registry=authority_registry,
        )
        expected_outcome = _lineage_outcome(validated.spearman_rho, validated.inconclusive_reasons)
        checks = (
            evaluation.validated_result_ref == validated.validated_result_id,
            evaluation.validation_event_ref == validation.validation_event_id,
            evaluation.execution_event_ref == execution.execution_event_id,
            evaluation.test_request_ref == request.test_request_id,
            evaluation.request_fingerprint == request.request_fingerprint,
            evaluation.method == request.method,
            evaluation.support_criterion == request.support_criterion,
            evaluation.handoff_ref == handoff.handoff_id,
            evaluation.handoff_fingerprint == handoff.handoff_fingerprint,
            evaluation.diagnostic_proposition_ref == handoff.diagnostic_proposition_ref,
            evaluation.diagnostic_proposition_fingerprint == handoff.diagnostic_proposition_fingerprint,
            evaluation.pretest_evaluation_ref == handoff.pretest_evaluation_ref,
            evaluation.pretest_evaluation_fingerprint == handoff.pretest_evaluation_fingerprint,
            evaluation.analytical_outcome is expected_outcome,
            validated.validation_event_id == validation.validation_event_id,
            validated.execution_event_id == execution.execution_event_id,
            validated.executed_result_ref == executed.executed_result_id,
            validated.result_fingerprint == executed.result_fingerprint,
            validated.validation_fingerprint == validation.validation_fingerprint,
            validated.test_request_ref == request.test_request_id,
            validated.method == request.method,
            validated.support_criterion == request.support_criterion,
            validated.validation_profile == request.validation_profile,
            validation.executed_result_ref == executed.executed_result_id,
            validation.executed_result_fingerprint == executed.result_fingerprint,
            validation.validation_profile == request.validation_profile,
            validation.validated_result_ref == validated.validated_result_id,
            executed.execution_event_id == execution.execution_event_id,
            executed.test_request_ref == request.test_request_id,
            executed.request_fingerprint == request.request_fingerprint,
            executed.method == request.method,
            executed.support_criterion == request.support_criterion,
            executed.validation_profile == request.validation_profile,
            executed.implementation == request.implementation,
            execution.result_ref == executed.executed_result_id,
            execution.test_request_ref == request.test_request_id,
            execution.request_fingerprint == request.request_fingerprint,
            execution.method == request.method,
            execution.implementation == request.implementation,
            request.evidence_input_set_ref == evidence.evidence_input_set_id,
            request.evidence_input_set_fingerprint == evidence.evidence_input_set_fingerprint,
            request.handoff_fingerprint == handoff.handoff_fingerprint,
            request.governed_hypothesis_ref == handoff.governed_hypothesis_ref,
            request.governed_hypothesis_fingerprint == handoff.governed_hypothesis_fingerprint,
            request.diagnostic_proposition_ref == handoff.diagnostic_proposition_ref,
            request.diagnostic_proposition_fingerprint == handoff.diagnostic_proposition_fingerprint,
            request.pretest_evaluation_ref == handoff.pretest_evaluation_ref,
            request.pretest_evaluation_fingerprint == handoff.pretest_evaluation_fingerprint,
            request.resolved_profile_ref == handoff.resolved_profile_ref,
            request.resolved_profile_fingerprint == handoff.resolved_profile_fingerprint,
            request.requirement_judgment_bundle_ref == pretest.requirement_judgment_bundle_ref,
            request.requirement_judgment_bundle_fingerprint == pretest.requirement_judgment_bundle_fingerprint,
        )
        if not all(checks):
            self._lineage_fail("adjacent R6/R7 bindings are inconsistent")
        return CompleteR7Lineage(evaluation, validated, validation, executed, execution, request, evidence, handoff)

    @staticmethod
    def _lineage_fail(message: str) -> None:
        raise R7ArtifactIntegrityError(f"lineage_mismatch: {message}")


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


def _lineage_outcome(rho: float | None, reasons: tuple[str, ...]) -> AnalyticalOutcome:
    if rho is None or reasons:
        return AnalyticalOutcome.NOT_EVALUATED
    if rho <= -0.5:
        return AnalyticalOutcome.CRITERION_MET
    if rho >= 0.5:
        return AnalyticalOutcome.PROPOSITION_CONTRADICTED
    return AnalyticalOutcome.CRITERION_NOT_MET
