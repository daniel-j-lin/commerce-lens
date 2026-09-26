"""Private, fail-closed orchestration for the sole R7 diagnostic method."""

from __future__ import annotations

from dataclasses import dataclass

from commerce_lens.contracts.diagnostic import TestEligibility
from commerce_lens.contracts.evidence import CanonicalDatasetReference
from commerce_lens.contracts.populations import PopulationDefinition
from commerce_lens.contracts.common import utc_now
from commerce_lens.contracts.r7 import (
    DiagnosticEvidenceInputSet, DiagnosticExecutionRecord, DiagnosticTestRequest,
    PostTestDiagnosticEvaluation, R7EvaluationState, R7ExecutionStatus,
)
from commerce_lens.diagnostic.r7_evaluation import build_posttest_evaluation
from commerce_lens.diagnostic.r7_method_registry import R7_METHOD_REGISTRY
from commerce_lens.diagnostic.r7_evidence_authentication import (
    TrustedR7EvidenceAuthority,
    authenticate_evidence_input_set,
)
from commerce_lens.engine.r7_execution import R7ExecutionError, execute_r7_diagnostic
from commerce_lens.evidence.identifiers import generate_id
from commerce_lens.persistence.r6_repository import R6Repository
from commerce_lens.persistence.r7_repository import R7ArtifactType, R7Repository
from commerce_lens.diagnostic.governance import PreTestAuthorityRegistry
from commerce_lens.validation.r7_validator import validate_r7_result


@dataclass(frozen=True)
class R7ServiceOutcome:
    evaluation: PostTestDiagnosticEvaluation
    result_fingerprint: str | None
    validation_fingerprint: str | None


def run_r7_diagnostic(*, request: DiagnosticTestRequest, evidence_inputs: DiagnosticEvidenceInputSet,
                      canonical_dataset: CanonicalDatasetReference, baseline_population: PopulationDefinition,
                      comparison_population: PopulationDefinition, r6_repository: R6Repository,
                      r7_repository: R7Repository, authority_registry: PreTestAuthorityRegistry,
                      trusted_evidence_authority: TrustedR7EvidenceAuthority) -> R7ServiceOutcome:
    handoff = r6_repository.load_r6_to_r7_handoff(request.handoff_ref, authority_registry=authority_registry)
    if handoff.handoff_fingerprint != request.handoff_fingerprint or handoff.test_eligibility is not TestEligibility.ELIGIBLE_NOT_EXECUTED:
        raise ValueError("R7_GATE_HANDOFF_NOT_ELIGIBLE")
    if (handoff.diagnostic_proposition_ref, handoff.diagnostic_proposition_fingerprint) != (request.diagnostic_proposition_ref, request.diagnostic_proposition_fingerprint):
        raise ValueError("R7_GATE_PROPOSITION_MISMATCH")
    if (
        (request.governed_hypothesis_ref, request.governed_hypothesis_fingerprint)
        != (handoff.governed_hypothesis_ref, handoff.governed_hypothesis_fingerprint)
        or (request.pretest_evaluation_ref, request.pretest_evaluation_fingerprint)
        != (handoff.pretest_evaluation_ref, handoff.pretest_evaluation_fingerprint)
        or (request.resolved_profile_ref, request.resolved_profile_fingerprint)
        != (handoff.resolved_profile_ref, handoff.resolved_profile_fingerprint)
        or request.scope_ref != handoff.scope_ref
        or (request.baseline_period_ref, request.comparison_period_ref)
        != (handoff.baseline_period_ref, handoff.comparison_period_ref)
        or {request.baseline_population_ref, request.comparison_population_ref}
        != set(handoff.population_refs)
    ):
        raise ValueError("R7_GATE_HANDOFF_LINEAGE_MISMATCH")
    if request.evidence_input_set_ref != evidence_inputs.evidence_input_set_id or request.evidence_input_set_fingerprint != evidence_inputs.evidence_input_set_fingerprint:
        raise ValueError("R7_GATE_EVIDENCE_SET_MISMATCH")
    method, _, _, _ = R7_METHOD_REGISTRY.authenticate_bundle(
        method=request.method, support_criterion=request.support_criterion,
        validation_profile=request.validation_profile, implementation=request.implementation,
        family_id=handoff.family_id, family_version=handoff.family_version,
        family_fingerprint=handoff.family_fingerprint,
    )
    if request.normalized_parameters != method.fixed_parameters:
        raise ValueError("R7_GATE_PARAMETER_OVERRIDE")
    pretest = r6_repository.load_pretest_diagnostic_evaluation(
        handoff.pretest_evaluation_ref, authority_registry=authority_registry,
    )
    profile = r6_repository.load_resolved_required_evidence_profile(
        handoff.resolved_profile_ref, authority_registry=authority_registry,
    )
    if (
        request.requirement_judgment_bundle_ref != pretest.requirement_judgment_bundle_ref
        or request.requirement_judgment_bundle_fingerprint != pretest.requirement_judgment_bundle_fingerprint
    ):
        raise ValueError("R7_GATE_JUDGMENT_BUNDLE_MISMATCH")
    judgments = r6_repository.load_requirement_judgment_bundle(
        pretest.requirement_judgment_bundle_ref, profile=profile,
    )
    judgment_ids = {item.judgment_id for item in judgments}
    if any(item.requirement_judgment_ref not in judgment_ids for item in evidence_inputs.bindings):
        raise ValueError("R7_GATE_EVIDENCE_JUDGMENT_UNKNOWN")
    authenticate_evidence_input_set(
        evidence_inputs, judgments=judgments,
        trusted_authority=trusted_evidence_authority,
        authority_registry=authority_registry,
    )
    r7_repository.persist(R7ArtifactType.EVIDENCE_INPUT_SET, evidence_inputs)
    r7_repository.persist(R7ArtifactType.TEST_REQUEST, request)
    try:
        execution = execute_r7_diagnostic(
            request=request, canonical_dataset=canonical_dataset, baseline_population=baseline_population,
            comparison_population=comparison_population, artifact_store=r7_repository.artifact_store,
        )
    except R7ExecutionError as exc:
        now = utc_now()
        failed = DiagnosticExecutionRecord(
            execution_event_id=generate_id("r7exec"), test_request_ref=request.test_request_id,
            request_fingerprint=request.request_fingerprint, method=request.method, implementation=request.implementation,
            started_at=now, ended_at=now, status=R7ExecutionStatus.FAILED,
            failure_code="R7_EXECUTION_FAILED", failure_reason=str(exc),
        )
        r7_repository.persist(R7ArtifactType.EXECUTION_RECORD, failed)
        evaluation = build_posttest_evaluation(
            request=request, execution=failed, validation=None, validated=None,
            state=R7EvaluationState.EXECUTION_FAILED, reason="R7_EXECUTION_FAILED",
        )
        r7_repository.persist(R7ArtifactType.POSTTEST_EVALUATION, evaluation)
        return R7ServiceOutcome(evaluation, None, None)
    r7_repository.persist(R7ArtifactType.EXECUTION_RECORD, execution.execution_record)
    r7_repository.persist(R7ArtifactType.EXECUTED_RESULT, execution.executed_result)
    validation = validate_r7_result(
        request=request, executed_result=execution.executed_result, canonical_dataset=canonical_dataset,
        baseline_population=baseline_population, comparison_population=comparison_population,
        artifact_store=r7_repository.artifact_store,
    )
    r7_repository.persist(R7ArtifactType.VALIDATION_RECORD, validation.validation_record)
    if validation.validated_result is not None:
        r7_repository.persist(R7ArtifactType.VALIDATED_RESULT, validation.validated_result)
    evaluation = build_posttest_evaluation(
        request=request, execution=execution.execution_record, validation=validation.validation_record,
        validated=validation.validated_result,
    )
    r7_repository.persist(R7ArtifactType.POSTTEST_EVALUATION, evaluation)
    # Authoritative completion requires recursive R6→R7 graph authentication.
    r7_repository.load_complete_posttest_evaluation(
        evaluation.evaluation_event_id, r6_repository=r6_repository,
        authority_registry=authority_registry,
        trusted_evidence_authority=trusted_evidence_authority,
    )
    return R7ServiceOutcome(evaluation, execution.executed_result.result_fingerprint, validation.validation_record.validation_fingerprint)
