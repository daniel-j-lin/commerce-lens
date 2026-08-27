"""Data Sufficiency structural contracts."""

from __future__ import annotations

from enum import Enum

from pydantic import Field

from commerce_lens.contracts.common import (
    Assumption,
    AvailableEvidence,
    ContractBase,
    EvidenceRequirement,
    FailureDetail,
    MetricState,
    Qualification,
)


class SufficiencyState(str, Enum):
    NOT_EVALUATED = "not_evaluated"
    SUFFICIENT = "sufficient"
    CLARIFICATION_REQUIRED = "clarification_required"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    DATA_QUALITY_FAILURE = "data_quality_failure"
    PARTIAL = "partial"


class MetricEligibility(ContractBase):
    metric_ref: str = Field(min_length=1)
    eligible: bool
    metric_state: MetricState | None = None
    failure_details: tuple[FailureDetail, ...] = ()


class ClarificationItem(ContractBase):
    item_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    affected_refs: tuple[str, ...] = ()


class DataSufficiencyResult(ContractBase):
    sufficiency_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    dataset_ref_id: str = Field(min_length=1)
    canonical_dataset_ref_id: str | None = None
    required_evidence: tuple[EvidenceRequirement, ...] = ()
    available_evidence: tuple[AvailableEvidence, ...] = ()
    metric_eligibility: tuple[MetricEligibility, ...] = ()
    data_quality_failures: tuple[FailureDetail, ...] = ()
    clarification_items: tuple[ClarificationItem, ...] = ()
    assumptions: tuple[Assumption, ...] = ()
    qualifications: tuple[Qualification, ...] = ()
    state: SufficiencyState

