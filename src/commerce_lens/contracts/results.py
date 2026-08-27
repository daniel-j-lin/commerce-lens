"""Analysis result contract."""

from __future__ import annotations

from pydantic import Field

from commerce_lens.contracts.common import (
    CONTRACT_VERSION,
    ArtifactReference,
    Assumption,
    ContractBase,
    FailureDetail,
    Limitation,
    MetricState,
    Qualification,
    RunStatus,
)
from commerce_lens.contracts.evidence import ClaimDecision
from commerce_lens.contracts.sufficiency import SufficiencyState


class MetricResult(ContractBase):
    metric_ref: str = Field(min_length=1)
    metric_state: MetricState
    executed_result_refs: tuple[str, ...] = ()
    validation_record_refs: tuple[str, ...] = ()
    validated_result_refs: tuple[str, ...] = ()
    admissible_evidence_refs: tuple[str, ...] = ()
    failure_details: tuple[FailureDetail, ...] = ()
    qualifications: tuple[Qualification, ...] = ()
    limitations: tuple[Limitation, ...] = ()


class AnalysisResult(ContractBase):
    request_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    contract_version: str = CONTRACT_VERSION
    traceability_id: str | None = None
    run_status: RunStatus
    data_sufficiency_ref: str | None = None
    data_sufficiency_state: SufficiencyState | None = None
    metric_results: tuple[MetricResult, ...] = ()
    failure_details: tuple[FailureDetail, ...] = ()
    executed_result_refs: tuple[str, ...] = ()
    validation_record_refs: tuple[str, ...] = ()
    validated_result_refs: tuple[str, ...] = ()
    admissible_evidence_refs: tuple[str, ...] = ()
    claim_decisions: tuple[ClaimDecision, ...] = ()
    qualifications: tuple[Qualification, ...] = ()
    assumptions: tuple[Assumption, ...] = ()
    limitations: tuple[Limitation, ...] = ()
    blocked_metric_refs: tuple[str, ...] = ()
    artifacts: tuple[ArtifactReference, ...] = ()
