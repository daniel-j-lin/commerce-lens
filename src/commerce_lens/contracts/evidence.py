"""Structural evidence and interpretation contracts."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from commerce_lens.evidence.identifiers import canonical_json_fingerprint, generate_id

from commerce_lens.contracts.common import (
    ArtifactReference,
    Assumption,
    ClaimState,
    ClaimType,
    ContractBase,
    Limitation,
    Qualification,
    ScopeDefinition,
    SourceType,
    MetricState,
    utc_now,
)
from commerce_lens.contracts.execution import ScalarResultValue


class AlternativeExplanationStatus(str, Enum):
    EVIDENCE_SUPPORTED = "evidence_supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNTESTED_BUT_PLAUSIBLE = "untested_but_plausible"
    UNSUPPORTED = "unsupported"


class MetricReference(ContractBase):
    metric_id: str = Field(min_length=1)
    definition_version: str = Field(min_length=1)
    display_name: str | None = None


class EvidenceRole(str, Enum):
    METRIC_VALUE = "metric_value"
    METRIC_STATE = "metric_state"


class EvidenceAdmissibilityStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"


class ClaimPropositionType(str, Enum):
    METRIC_VALUE_EQUALS = "metric_value_equals"
    METRIC_STATE_IS = "metric_state_is"


P8_CLAIM_MATERIAL_USE = "descriptive_metric_claim"


class DatasetReference(ContractBase):
    dataset_id: str = Field(min_length=1)
    source_type: SourceType
    original_name: str = Field(min_length=1)
    content_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)
    registered_at: datetime = Field(default_factory=utc_now)
    snapshot_artifact: ArtifactReference | None = None
    selected_sheet: str | None = None
    selected_table: str | None = None
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class CanonicalDatasetReference(ContractBase):
    canonical_dataset_id: str = Field(min_length=1)
    source_dataset_id: str = Field(min_length=1)
    canonical_schema_version: str = Field(min_length=1)
    content_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact: ArtifactReference
    row_count: int | None = Field(default=None, ge=0)


class CanonicalizationRecord(ContractBase):
    canonicalization_id: str = Field(min_length=1)
    source_dataset_id: str = Field(min_length=1)
    canonical_dataset_id: str | None = None
    canonical_schema_version: str = Field(min_length=1)
    mapping_ref: str | None = None
    transformation_version: str | None = None
    mapping_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    eligibility_mode: str | None = None
    selected_sheet: str | None = None
    selected_table: str | None = None
    date_policy_ref: str | None = None
    currency_basis_ref: str | None = None
    unsupported_partial_refund_evidence: bool = False
    source_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    output_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    source_row_count: int | None = Field(default=None, ge=0)
    canonical_row_count: int | None = Field(default=None, ge=0)
    data_quality_result_ids: tuple[str, ...] = ()
    qualifications: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    failures: tuple[str, ...] = ()


class AdmissibleEvidence(ContractBase):
    evidence_id: str = Field(min_length=1)
    evidence_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    request_id: str | None = None
    sufficiency_id: str | None = None
    validated_result_ids: tuple[str, ...] = Field(min_length=1)
    validation_record_ids: tuple[str, ...] = ()
    executed_result_id: str | None = None
    execution_id: str | None = None
    applicable_required_evidence_requirement_ids: tuple[str, ...] = ()
    metric_refs: tuple[MetricReference, ...] = ()
    metric_ref: str | None = None
    metric_definition_version: str | None = None
    dataset_ref_id: str = Field(min_length=1)
    canonical_dataset_ref_id: str | None = None
    canonical_dataset_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    population_ref: str | None = None
    population_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    period_ref: str | None = None
    period_role: str | None = None
    supported_claim_type: ClaimType
    evidence_role: EvidenceRole | None = None
    scope: ScopeDefinition
    assumptions: tuple[Assumption, ...] = ()
    limitations: tuple[Limitation, ...] = ()
    qualifications: tuple[Qualification, ...] = ()
    artifact_ref: ArtifactReference | None = None

    @model_validator(mode="after")
    def validate_p6_single_validated_result(self) -> "AdmissibleEvidence":
        if len(self.validated_result_ids) != 1:
            raise ValueError("P6-001 AdmissibleEvidence requires exactly one ValidatedResult reference")
        return self


class EvidenceAdmissibilityRecord(ContractBase):
    admissibility_id: str = Field(min_length=1)
    evaluator_id: str = Field(min_length=1)
    evaluator_version: str = Field(min_length=1)
    request_id: str | None = None
    sufficiency_id: str | None = None
    validated_result_id: str | None = None
    validated_result_validation_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    validated_result_artifact_ref: ArtifactReference | None = None
    validation_record_ids: tuple[str, ...] = ()
    executed_result_id: str | None = None
    execution_id: str | None = None
    execution_record_id: str | None = None
    metric_ref: str | None = None
    metric_definition_version: str | None = None
    canonical_business_question_id: str | None = None
    dataset_ref_id: str | None = None
    canonical_dataset_ref_id: str | None = None
    canonical_dataset_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    population_ref: str | None = None
    population_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    period_ref: str | None = None
    period_role: str | None = None
    supported_claim_type: ClaimType | None = None
    evidence_role: EvidenceRole | None = None
    applicable_required_evidence_requirement_ids: tuple[str, ...] = ()
    sufficiency_authority_checked: bool = False
    assumptions: tuple[Assumption, ...] = ()
    qualifications: tuple[Qualification, ...] = ()
    limitations: tuple[Limitation, ...] = ()
    checks_performed: tuple[str, ...] = ()
    status: EvidenceAdmissibilityStatus
    failure_code: str | None = None
    failure_reason: str | None = None
    started_at: datetime = Field(default_factory=utc_now)
    ended_at: datetime
    admissible_evidence_id: str | None = None
    admissible_evidence_artifact_ref: ArtifactReference | None = None
    evidence_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_admissibility_record(self) -> "EvidenceAdmissibilityRecord":
        if self.started_at > self.ended_at:
            raise ValueError("EvidenceAdmissibilityRecord started_at must be before or equal to ended_at")
        if self.status is EvidenceAdmissibilityStatus.PASSED:
            if self.failure_code is not None or self.failure_reason is not None:
                raise ValueError("passed EvidenceAdmissibilityRecord cannot carry failure details")
            if self.admissible_evidence_id is None or self.admissible_evidence_artifact_ref is None:
                raise ValueError("passed EvidenceAdmissibilityRecord requires AdmissibleEvidence linkage")
        if self.status is EvidenceAdmissibilityStatus.FAILED and self.admissible_evidence_id is not None:
            raise ValueError("failed EvidenceAdmissibilityRecord cannot link successful AdmissibleEvidence")
        return self


class ClaimCandidate(ContractBase):
    claim_candidate_id: str = Field(default_factory=lambda: generate_id("clmcand"), min_length=1)
    claim_id: str | None = Field(default=None, min_length=1)
    claim_candidate_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    claim_type: ClaimType
    metric_ref: str | None = None
    metric_definition_version: str | None = None
    request_id: str | None = None
    dataset_ref_id: str | None = None
    canonical_dataset_ref_id: str | None = None
    canonical_dataset_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    intended_scope: ScopeDefinition
    population_ref: str | None = None
    population_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    period_ref: str | None = None
    period_role: str | None = None
    proposition_type: ClaimPropositionType | None = None
    claimed_value: ScalarResultValue | None = None
    claimed_metric_state: MetricState | None = None
    undefined_reason: str | None = None
    unit: str | None = None
    currency: str | None = None
    supporting_evidence_refs: tuple[str, ...] = ()
    supporting_validated_result_refs: tuple[str, ...] = ()
    intended_material_use: str | None = P8_CLAIM_MATERIAL_USE
    baseline_period_ref: str | None = None
    comparison_period_ref: str | None = None
    baseline_population_ref: str | None = None
    comparison_population_ref: str | None = None
    baseline_population_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    comparison_population_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    proposed_meaning: str | None = None
    material: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_structured_proposition_shape(self) -> "ClaimCandidate":
        if self.proposition_type is ClaimPropositionType.METRIC_VALUE_EQUALS:
            if self.claimed_value is None:
                raise ValueError("metric_value_equals ClaimCandidate requires claimed_value")
            if self.claimed_metric_state is not None:
                raise ValueError("metric_value_equals ClaimCandidate cannot carry claimed_metric_state")
        if self.proposition_type is ClaimPropositionType.METRIC_STATE_IS:
            if self.claimed_metric_state is None:
                raise ValueError("metric_state_is ClaimCandidate requires claimed_metric_state")
            if self.claimed_value is not None:
                raise ValueError("metric_state_is ClaimCandidate cannot carry claimed_value")
        return self


class ClaimDecision(ContractBase):
    claim_decision_id: str = Field(default_factory=lambda: generate_id("clmdec"), min_length=1)
    decision_id: str | None = Field(default=None, min_length=1)
    claim_candidate_ref: str | None = None
    claim_id: str | None = Field(default=None, min_length=1)
    policy_id: str = Field(default="commerce_lens_p8_claim_admissibility", min_length=1)
    policy_version: str = Field(min_length=1)
    claim_state: ClaimState
    reason: str = Field(min_length=1)
    failure_code: str | None = None
    supporting_evidence_refs: tuple[str, ...] = ()
    supporting_validated_result_refs: tuple[str, ...] = ()
    scope: ScopeDefinition | None = None
    population_ref: str | None = None
    population_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    period_ref: str | None = None
    period_role: str | None = None
    baseline_period_ref: str | None = None
    comparison_period_ref: str | None = None
    baseline_population_ref: str | None = None
    comparison_population_ref: str | None = None
    baseline_population_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    comparison_population_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    required_qualifications: tuple[Qualification, ...] = ()
    decision_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    decided_at: datetime = Field(default_factory=utc_now)
    artifact_ref: ArtifactReference | None = None

    @model_validator(mode="after")
    def validate_failure_code_for_state(self) -> "ClaimDecision":
        if self.claim_state is ClaimState.INADMISSIBLE and not self.failure_code:
            raise ValueError("Inadmissible ClaimDecision requires failure_code")
        if self.claim_state is not ClaimState.INADMISSIBLE and self.failure_code is not None:
            raise ValueError("Admissible ClaimDecision cannot carry failure_code")
        return self


def claim_candidate_semantic_fingerprint(candidate: ClaimCandidate) -> str:
    payload = {
        "claim_type": candidate.claim_type.value,
        "metric_ref": candidate.metric_ref,
        "metric_definition_version": candidate.metric_definition_version,
        "request_id": candidate.request_id,
        "dataset_ref_id": candidate.dataset_ref_id,
        "canonical_dataset_ref_id": candidate.canonical_dataset_ref_id,
        "canonical_dataset_fingerprint": candidate.canonical_dataset_fingerprint,
        "proposition_type": candidate.proposition_type.value if candidate.proposition_type else None,
        "claimed_value": _json_scalar(candidate.claimed_value),
        "claimed_metric_state": candidate.claimed_metric_state.value if candidate.claimed_metric_state else None,
        "undefined_reason": candidate.undefined_reason,
        "intended_scope": candidate.intended_scope.model_dump(mode="json"),
        "population_ref": candidate.population_ref,
        "population_fingerprint": candidate.population_fingerprint,
        "period_ref": candidate.period_ref,
        "period_role": candidate.period_role,
        "baseline_period_ref": candidate.baseline_period_ref,
        "comparison_period_ref": candidate.comparison_period_ref,
        "baseline_population_ref": candidate.baseline_population_ref,
        "comparison_population_ref": candidate.comparison_population_ref,
        "baseline_population_fingerprint": candidate.baseline_population_fingerprint,
        "comparison_population_fingerprint": candidate.comparison_population_fingerprint,
        "unit": candidate.unit,
        "currency": candidate.currency,
        "supporting_evidence_refs": sorted(candidate.supporting_evidence_refs),
        "supporting_validated_result_refs": sorted(candidate.supporting_validated_result_refs),
        "intended_material_use": candidate.intended_material_use,
    }
    return canonical_json_fingerprint(payload)


def claim_decision_semantic_fingerprint(decision: ClaimDecision, *, claim_candidate_fingerprint: str | None) -> str:
    payload = {
        "claim_candidate_fingerprint": claim_candidate_fingerprint,
        "policy_id": decision.policy_id,
        "policy_version": decision.policy_version,
        "claim_state": decision.claim_state.value,
        "supporting_evidence_refs": sorted(decision.supporting_evidence_refs),
        "supporting_validated_result_refs": sorted(decision.supporting_validated_result_refs),
        "scope": decision.scope.model_dump(mode="json") if decision.scope else None,
        "population_ref": decision.population_ref,
        "population_fingerprint": decision.population_fingerprint,
        "period_ref": decision.period_ref,
        "period_role": decision.period_role,
        "baseline_period_ref": decision.baseline_period_ref,
        "comparison_period_ref": decision.comparison_period_ref,
        "baseline_population_ref": decision.baseline_population_ref,
        "comparison_population_ref": decision.comparison_population_ref,
        "baseline_population_fingerprint": decision.baseline_population_fingerprint,
        "comparison_population_fingerprint": decision.comparison_population_fingerprint,
        "failure_code": decision.failure_code,
        "required_qualifications": [item.model_dump(mode="json") for item in decision.required_qualifications],
    }
    return canonical_json_fingerprint(payload)


def _json_scalar(value: ScalarResultValue | None) -> str | int | float | bool | None:
    if value is None:
        return None
    if hasattr(value, "to_eng_string"):
        return value.to_eng_string()
    return value


class Finding(ContractBase):
    finding_id: str = Field(min_length=1)
    claim_decision_id: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    scope: ScopeDefinition
    qualification_refs: tuple[str, ...] = ()


class AlternativeExplanation(ContractBase):
    explanation_id: str = Field(min_length=1)
    status: AlternativeExplanationStatus
    hypothesis: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = ()
    limitations: tuple[Limitation, ...] = ()


class Recommendation(ContractBase):
    recommendation_id: str = Field(min_length=1)
    supporting_finding_refs: tuple[str, ...] = Field(min_length=1)
    recommendation: str = Field(min_length=1)
    proportionality_note: str = Field(min_length=1)
    human_ownership_note: str = Field(min_length=1)
    limitations: tuple[Limitation, ...] = ()
