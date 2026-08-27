"""Structural evidence and interpretation contracts."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

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
    validated_result_ids: tuple[str, ...] = Field(min_length=1)
    metric_refs: tuple[MetricReference, ...] = ()
    dataset_ref_id: str = Field(min_length=1)
    supported_claim_type: ClaimType
    scope: ScopeDefinition
    assumptions: tuple[Assumption, ...] = ()
    limitations: tuple[Limitation, ...] = ()
    qualifications: tuple[Qualification, ...] = ()


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
