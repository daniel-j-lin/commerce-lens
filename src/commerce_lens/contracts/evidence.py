"""Structural evidence and interpretation contracts."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field, model_validator

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
    utc_now,
)


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
    claim_id: str = Field(min_length=1)
    claim_type: ClaimType
    intended_scope: ScopeDefinition
    proposed_meaning: str = Field(min_length=1)
    supporting_evidence_refs: tuple[str, ...] = ()
    supporting_validated_result_refs: tuple[str, ...] = ()
    material: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClaimDecision(ContractBase):
    decision_id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)
    claim_state: ClaimState
    reason: str = Field(min_length=1)
    supporting_evidence_refs: tuple[str, ...] = ()
    supporting_validated_result_refs: tuple[str, ...] = ()
    required_qualifications: tuple[Qualification, ...] = ()
    decided_at: datetime = Field(default_factory=utc_now)


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
