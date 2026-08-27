"""Analysis request contract."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from commerce_lens.contracts.common import (
    CONTRACT_VERSION,
    Assumption,
    ContractBase,
    EvidenceRequirement,
    GroupingDimension,
    PeriodDefinition,
    ScopeDefinition,
    utc_now,
)
from commerce_lens.contracts.evidence import MetricReference
from commerce_lens.evidence.identifiers import generate_id


class RequestedOutput(ContractBase):
    output_id: str = Field(min_length=1)
    shape: str = Field(min_length=1)
    metric_refs: tuple[str, ...] = ()
    ranking_limit: int | None = Field(default=None, ge=1)


class AnalysisRequest(ContractBase):
    request_id: str = Field(default_factory=lambda: generate_id("req"))
    contract_version: str = CONTRACT_VERSION
    created_at: datetime = Field(default_factory=utc_now)
    canonical_business_question_id: str = Field(min_length=1)
    original_question_text: str | None = None
    metrics: tuple[MetricReference, ...] = Field(min_length=1)
    baseline_period: PeriodDefinition
    comparison_period: PeriodDefinition
    scope: ScopeDefinition
    grouping: GroupingDimension = GroupingDimension.NONE
    required_evidence: tuple[EvidenceRequirement, ...] = ()
    dataset_ref_id: str = Field(min_length=1)
    selected_sheet: str | None = None
    selected_table: str | None = None
    assumptions: tuple[Assumption, ...] = ()
    canonical_schema_version: str = Field(min_length=1)
    metric_registry_version: str = Field(min_length=1)
    requested_outputs: tuple[RequestedOutput, ...] = ()

