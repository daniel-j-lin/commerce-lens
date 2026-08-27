from datetime import date

import pytest
from pydantic import ValidationError

from commerce_lens.contracts.common import (
    ClaimState,
    ClaimType,
    EvidenceRequirement,
    FailureDetail,
    FailureStage,
    GroupingDimension,
    MetricState,
    PeriodDefinition,
    RunStatus,
    ScopeDefinition,
)
from commerce_lens.contracts.evidence import AlternativeExplanationStatus, ClaimDecision, MetricReference
from commerce_lens.contracts.execution import ExecutedResult, ExecutionStatus
from commerce_lens.contracts.requests import AnalysisRequest
from commerce_lens.contracts.results import AnalysisResult, MetricResult
from commerce_lens.contracts.sufficiency import SufficiencyState


def test_run_metric_and_claim_states_are_separate_domains() -> None:
    assert RunStatus.COMPLETED.value == "completed"
    assert MetricState.VALID.value == "Valid"
    assert ClaimState.ADMISSIBLE.value == "Admissible"
    assert RunStatus.COMPLETED.value != MetricState.VALID.value
    assert MetricState.INADMISSIBLE.value == ClaimState.INADMISSIBLE.value
    assert MetricState.INADMISSIBLE.__class__ is not ClaimState.INADMISSIBLE.__class__


def test_invalid_enum_value_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AnalysisResult(request_id="req_1", run_id="run_1", run_status="success")


def test_analysis_request_round_trips_json() -> None:
    request = AnalysisRequest(
        canonical_business_question_id="canonical_revenue_change",
        metrics=(MetricReference(metric_id="revenue", definition_version="v1"),),
        baseline_period=PeriodDefinition(
            period_id="baseline",
            label="Baseline",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            date_convention_ref="order_date_utc",
        ),
        comparison_period=PeriodDefinition(
            period_id="comparison",
            label="Comparison",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
            date_convention_ref="order_date_utc",
        ),
        scope=ScopeDefinition(scope_id="all_eligible"),
        grouping=GroupingDimension.PRODUCT,
        dataset_ref_id="ds_abc",
        canonical_schema_version="v1",
        metric_registry_version="v1",
    )

    restored = AnalysisRequest.model_validate_json(request.model_dump_json())
    assert restored == request
    assert restored.original_question_text is None


def test_partial_analysis_result_keeps_independent_metric_states() -> None:
    result = AnalysisResult(
        request_id="req_1",
        run_id="run_1",
        run_status=RunStatus.PARTIALLY_COMPLETED,
        metric_results=(
            MetricResult(metric_ref="revenue_change", metric_state=MetricState.VALID),
            MetricResult(
                metric_ref="revenue_change_pct",
                metric_state=MetricState.UNDEFINED,
                failure_details=(
                    FailureDetail(
                        stage=FailureStage.EXECUTION,
                        reason="governed denominator is zero",
                        target_ref="revenue_change_pct",
                    ),
                ),
            ),
        ),
        blocked_metric_refs=("revenue_change_pct",),
    )

    assert result.run_status is RunStatus.PARTIALLY_COMPLETED
    assert [metric.metric_state for metric in result.metric_results] == [MetricState.VALID, MetricState.UNDEFINED]
    assert not hasattr(result, "success")


def test_undefined_executed_result_requires_explicit_reason() -> None:
    with pytest.raises(ValidationError):
        ExecutedResult(
            result_id="res_1",
            execution_id="exe_1",
            metric_ref="revenue_change_pct",
            scope_ref="scope_1",
            metric_state=MetricState.UNDEFINED,
            execution_status=ExecutionStatus.COMPLETED,
        )


def test_claim_decision_state_validation() -> None:
    decision = ClaimDecision(
        decision_id="dec_1",
        claim_id="claim_1",
        policy_version="v1",
        claim_state=ClaimState.INADMISSIBLE,
        reason="policy not implemented",
    )
    assert decision.claim_state is ClaimState.INADMISSIBLE
    assert decision.model_dump(mode="json")["claim_state"] == "Inadmissible"
    assert ClaimType.DESCRIPTIVE.value == "descriptive"


def test_alternative_explanation_status_matches_governed_evidence_states() -> None:
    assert {status.value for status in AlternativeExplanationStatus} == {
        "evidence_supported",
        "partially_supported",
        "untested_but_plausible",
        "unsupported",
    }


def test_evidence_requirement_claim_type_uses_governed_taxonomy() -> None:
    requirement = EvidenceRequirement(
        requirement_id="req_evidence_1",
        description="Metric evidence required",
        claim_type=ClaimType.DIAGNOSTIC,
    )
    assert requirement.claim_type is ClaimType.DIAGNOSTIC

    with pytest.raises(ValidationError):
        EvidenceRequirement(
            requirement_id="req_evidence_2",
            description="Metric evidence required",
            claim_type="interesting_story",
        )


def test_analysis_result_data_sufficiency_state_uses_structural_enum() -> None:
    result = AnalysisResult(
        request_id="req_1",
        run_id="run_1",
        run_status=RunStatus.BLOCKED,
        data_sufficiency_state=SufficiencyState.INSUFFICIENT_EVIDENCE,
    )
    assert result.data_sufficiency_state is SufficiencyState.INSUFFICIENT_EVIDENCE

    with pytest.raises(ValidationError):
        AnalysisResult(
            request_id="req_1",
            run_id="run_1",
            run_status=RunStatus.BLOCKED,
            data_sufficiency_state="probably_fine",
        )
