from datetime import date

import pytest
from pydantic import ValidationError

from commerce_lens.canonical.models import CanonicalizationResult, PeriodCoverageEvidence
from commerce_lens.canonical.quality import blocking
from commerce_lens.contracts.common import (
    AvailableEvidence,
    EvidenceRequirement,
    GroupingDimension,
    PeriodDefinition,
    ScopeDefinition,
    ScopeFilter,
)
from commerce_lens.contracts.evidence import CanonicalizationRecord, MetricReference
from commerce_lens.contracts.requests import AnalysisRequest
from commerce_lens.contracts.sufficiency import ClarificationItem, SufficiencyState
from commerce_lens.sufficiency import evaluate_data_sufficiency


def test_equal_complete_non_overlapping_periods_with_required_evidence_are_sufficient() -> None:
    request = _analysis_request(
        required_evidence=(
            EvidenceRequirement(
                requirement_id="req_currency",
                description="currency basis evidence",
                metric_ref="revenue_change",
            ),
        )
    )

    result = evaluate_data_sufficiency(
        request,
        _canonicalization_result(),
        available_evidence=(
            AvailableEvidence(
                evidence_id="ev_currency",
                description="currency basis present",
                satisfies_requirement_ids=("req_currency",),
            ),
        ),
        period_coverage_evidence=_coverage(request),
    )

    assert result.state is SufficiencyState.SUFFICIENT
    assert result.metric_eligibility[0].eligible


def test_unequal_overlap_absent_and_insufficient_coverage_fail_period_contract() -> None:
    unequal = _analysis_request(
        baseline=(date(2026, 1, 1), date(2026, 1, 3)),
        comparison=(date(2026, 1, 3), date(2026, 1, 4)),
    )

    result = evaluate_data_sufficiency(
        unequal,
        _canonicalization_result(),
        period_coverage_evidence=(
            PeriodCoverageEvidence(
                coverage_ref_id="cov_short",
                dataset_ref_id="ds_1",
                observed_start_date=date(2026, 1, 1),
                observed_end_date=date(2026, 1, 3),
                date_convention_ref="order_date_utc",
            ),
        ),
    )

    reasons = " ".join(failure.reason for failure in result.data_quality_failures)
    assert result.state is SufficiencyState.INSUFFICIENT_EVIDENCE
    assert "equal duration" in reasons
    assert "non-overlapping" in reasons
    assert "comparison period" in reasons


def test_transaction_absence_without_coverage_evidence_is_insufficient() -> None:
    request = _analysis_request()

    result = evaluate_data_sufficiency(request, _canonicalization_result(), period_coverage_evidence=())

    assert result.state is SufficiencyState.INSUFFICIENT_EVIDENCE
    assert any("coverage evidence" in failure.reason for failure in result.data_quality_failures)


def test_missing_required_evidence_blocks_only_affected_chain() -> None:
    request = _analysis_request(
        metrics=(
            MetricReference(metric_id="revenue_change", definition_version="v1"),
            MetricReference(metric_id="category_contribution", definition_version="v1"),
        ),
        required_evidence=(
            EvidenceRequirement(
                requirement_id="req_category",
                description="category attribution evidence",
                metric_ref="category_contribution",
            ),
        ),
    )

    result = evaluate_data_sufficiency(
        request,
        _canonicalization_result(),
        period_coverage_evidence=_coverage(request),
    )

    assert result.state is SufficiencyState.PARTIAL
    eligibility = {item.metric_ref: item.eligible for item in result.metric_eligibility}
    assert eligibility == {"revenue_change": True, "category_contribution": False}


def test_blocking_data_quality_can_block_only_affected_chain() -> None:
    request = _analysis_request(
        metrics=(
            MetricReference(metric_id="revenue_change", definition_version="v1"),
            MetricReference(metric_id="category_contribution", definition_version="v1"),
        )
    )
    quality = blocking(
        "canonical.category.mapping_inconsistent",
        "category_id",
        "canonical_dictionary:20",
        "category mapping inconsistency blocks category analysis",
        affected_metric_refs=("category_contribution",),
    )

    result = evaluate_data_sufficiency(
        request,
        _canonicalization_result(quality_results=(quality,)),
        period_coverage_evidence=_coverage(request),
    )

    assert result.state is SufficiencyState.PARTIAL
    assert {item.metric_ref: item.eligible for item in result.metric_eligibility} == {
        "revenue_change": True,
        "category_contribution": False,
    }


def _analysis_request(
    *,
    baseline: tuple[date, date] = (date(2026, 1, 1), date(2026, 1, 2)),
    comparison: tuple[date, date] = (date(2026, 1, 3), date(2026, 1, 4)),
    metrics: tuple[MetricReference, ...] = (
        MetricReference(metric_id="revenue_change", definition_version="v1"),
    ),
    required_evidence: tuple[EvidenceRequirement, ...] = (),
    selected_sheet: str | None = None,
    selected_table: str | None = None,
) -> AnalysisRequest:
    return AnalysisRequest(
        canonical_business_question_id="canonical_revenue_change",
        metrics=metrics,
        baseline_period=PeriodDefinition(
            period_id="baseline",
            label="Baseline",
            start_date=baseline[0],
            end_date=baseline[1],
            date_convention_ref="order_date_utc",
        ),
        comparison_period=PeriodDefinition(
            period_id="comparison",
            label="Comparison",
            start_date=comparison[0],
            end_date=comparison[1],
            date_convention_ref="order_date_utc",
        ),
        scope=ScopeDefinition(scope_id="all_eligible"),
        grouping=GroupingDimension.NONE,
        dataset_ref_id="ds_1",
        selected_sheet=selected_sheet,
        selected_table=selected_table,
        canonical_schema_version="canonical_mvp_v1",
        metric_registry_version="v1",
        required_evidence=required_evidence,
    )


def _coverage(request: AnalysisRequest) -> tuple[PeriodCoverageEvidence, ...]:
    return (
        PeriodCoverageEvidence(
            coverage_ref_id="cov_all",
            dataset_ref_id=request.dataset_ref_id,
            observed_start_date=request.baseline_period.start_date,
            observed_end_date=request.comparison_period.end_date,
            date_convention_ref=request.baseline_period.date_convention_ref,
        ),
    )


def _canonicalization_result(
    quality_results=(),
    *,
    source_dataset_id: str = "ds_1",
    schema_version: str = "canonical_mvp_v1",
    canonical_dataset_present: bool = True,
    record_source_dataset_id: str | None = None,
    canonical_dataset_source_id: str | None = None,
    record_canonical_dataset_id: str | None = "cds_1",
    canonical_dataset_id: str | None = None,
    canonical_dataset_schema_version: str | None = None,
    record_selected_sheet: str | None = None,
    record_selected_table: str | None = None,
) -> CanonicalizationResult:
    from commerce_lens.contracts.common import ArtifactReference
    from commerce_lens.contracts.evidence import CanonicalDatasetReference

    record_source_id = record_source_dataset_id or source_dataset_id
    canonical_source_id = canonical_dataset_source_id or source_dataset_id
    dataset_id = canonical_dataset_id or record_canonical_dataset_id or "cds_1"
    dataset_schema_version = canonical_dataset_schema_version or schema_version
    canonical_dataset = (
        CanonicalDatasetReference(
            canonical_dataset_id=dataset_id,
            source_dataset_id=canonical_source_id,
            canonical_schema_version=dataset_schema_version,
            content_fingerprint="a" * 64,
            artifact=ArtifactReference(artifact_id="art_1", path="canonical/cds_1.parquet"),
            row_count=1,
        )
        if canonical_dataset_present
        else None
    )
    return CanonicalizationResult(
        record=CanonicalizationRecord(
            canonicalization_id="canonrec_1",
            source_dataset_id=record_source_id,
            canonical_dataset_id=record_canonical_dataset_id if canonical_dataset_present else None,
            canonical_schema_version=schema_version,
            selected_sheet=record_selected_sheet,
            selected_table=record_selected_table,
        ),
        canonical_dataset=canonical_dataset,
        data_quality_results=quality_results,
        failures=() if canonical_dataset_present else ("canonicalization failed",),
    )


def test_dataset_and_schema_mismatch_fail_closed() -> None:
    request = _analysis_request()
    mismatched_dataset = _canonicalization_result(source_dataset_id="other_ds")
    mismatched_schema = _canonicalization_result(schema_version="other_schema")

    dataset_result = evaluate_data_sufficiency(
        request,
        mismatched_dataset,
        period_coverage_evidence=_coverage(request),
    )
    schema_result = evaluate_data_sufficiency(
        request,
        mismatched_schema,
        period_coverage_evidence=_coverage(request),
    )

    assert dataset_result.state is SufficiencyState.INSUFFICIENT_EVIDENCE
    assert schema_result.state is SufficiencyState.INSUFFICIENT_EVIDENCE
    assert not dataset_result.metric_eligibility[0].eligible
    assert not schema_result.metric_eligibility[0].eligible


def test_canonical_dataset_reference_lineage_mismatches_fail_closed() -> None:
    request = _analysis_request()
    cases = (
        _canonicalization_result(canonical_dataset_source_id="other_ds"),
        _canonicalization_result(record_canonical_dataset_id="cds_record", canonical_dataset_id="cds_reference"),
        _canonicalization_result(canonical_dataset_schema_version="other_schema"),
    )

    for canonicalization_result in cases:
        result = evaluate_data_sufficiency(
            request,
            canonicalization_result,
            period_coverage_evidence=_coverage(request),
        )

        assert result.state is SufficiencyState.INSUFFICIENT_EVIDENCE
        assert not result.metric_eligibility[0].eligible
        assert result.data_quality_failures


def test_analysis_request_matching_sheet_selection_remains_sufficient() -> None:
    request = _analysis_request(selected_sheet="SheetA")

    result = evaluate_data_sufficiency(
        request,
        _canonicalization_result(record_selected_sheet="SheetA"),
        period_coverage_evidence=_coverage(request),
    )

    assert result.state is SufficiencyState.SUFFICIENT
    assert result.metric_eligibility[0].eligible


def test_analysis_request_sheet_selection_mismatch_fails_closed() -> None:
    request = _analysis_request(selected_sheet="SheetB")

    result = evaluate_data_sufficiency(
        request,
        _canonicalization_result(record_selected_sheet="SheetA"),
        period_coverage_evidence=_coverage(request),
    )

    assert result.state is SufficiencyState.INSUFFICIENT_EVIDENCE
    assert not result.metric_eligibility[0].eligible
    assert any(failure.target_ref == "selected_sheet" for failure in result.data_quality_failures)


def test_analysis_request_table_selection_mismatch_fails_closed() -> None:
    request = _analysis_request(selected_table="table_a")

    result = evaluate_data_sufficiency(
        request,
        _canonicalization_result(record_selected_table="table_b"),
        period_coverage_evidence=_coverage(request),
    )

    assert result.state is SufficiencyState.INSUFFICIENT_EVIDENCE
    assert not result.metric_eligibility[0].eligible
    assert any(failure.target_ref == "selected_table" for failure in result.data_quality_failures)


def test_omitted_request_selection_keeps_governed_record_selection_valid() -> None:
    request = _analysis_request()

    result = evaluate_data_sufficiency(
        request,
        _canonicalization_result(record_selected_sheet="SheetA", record_selected_table="table_a"),
        period_coverage_evidence=_coverage(request),
    )

    assert result.state is SufficiencyState.SUFFICIENT
    assert result.metric_eligibility[0].eligible


def test_request_selection_without_matching_record_selection_fails_closed() -> None:
    request = _analysis_request(selected_sheet="SheetA", selected_table="table_a")

    result = evaluate_data_sufficiency(
        request,
        _canonicalization_result(),
        period_coverage_evidence=_coverage(request),
    )

    assert result.state is SufficiencyState.INSUFFICIENT_EVIDENCE
    assert not result.metric_eligibility[0].eligible
    assert {failure.target_ref for failure in result.data_quality_failures} >= {"selected_sheet", "selected_table"}


def test_missing_successful_canonical_dataset_blocks_sufficiency() -> None:
    request = _analysis_request()

    result = evaluate_data_sufficiency(
        request,
        _canonicalization_result(canonical_dataset_present=False),
        period_coverage_evidence=_coverage(request),
    )

    assert result.state is SufficiencyState.DATA_QUALITY_FAILURE
    assert not result.metric_eligibility[0].eligible
    assert any("successful canonicalization" in failure.reason for failure in result.data_quality_failures)


def test_scoped_clarification_blocks_only_affected_chain() -> None:
    request = _analysis_request(
        metrics=(
            MetricReference(metric_id="revenue_change", definition_version="v1"),
            MetricReference(metric_id="category_contribution", definition_version="v1"),
        )
    )

    result = evaluate_data_sufficiency(
        request,
        _canonicalization_result(),
        period_coverage_evidence=_coverage(request),
        clarification_items=(
            ClarificationItem(
                item_id="clarify_category",
                question="Which governed category attribution should be used?",
                affected_refs=("category_contribution",),
            ),
        ),
    )

    assert result.state is SufficiencyState.PARTIAL
    assert {item.metric_ref: item.eligible for item in result.metric_eligibility} == {
        "revenue_change": True,
        "category_contribution": False,
    }


def test_global_clarification_blocks_all_chains() -> None:
    request = _analysis_request(
        metrics=(
            MetricReference(metric_id="revenue_change", definition_version="v1"),
            MetricReference(metric_id="category_contribution", definition_version="v1"),
        )
    )

    result = evaluate_data_sufficiency(
        request,
        _canonicalization_result(),
        period_coverage_evidence=_coverage(request),
        clarification_items=(
            ClarificationItem(
                item_id="clarify_scope",
                question="Which comparison scope is governed?",
                affected_refs=(request.scope.scope_id,),
            ),
        ),
    )

    assert result.state is SufficiencyState.CLARIFICATION_REQUIRED
    assert not any(item.eligible for item in result.metric_eligibility)


def test_unsupported_scope_filter_is_rejected_by_contract() -> None:
    with pytest.raises(ValidationError):
        ScopeFilter(field="customer_id", operator="equals", value="c1")
    with pytest.raises(ValidationError):
        ScopeFilter(field="product_id", operator="contains", value="p1")


def test_sufficiency_identity_includes_scoped_clarification_inputs() -> None:
    request = _analysis_request(
        metrics=(
            MetricReference(metric_id="revenue_change", definition_version="v1"),
            MetricReference(metric_id="category_contribution", definition_version="v1"),
        )
    )
    without_clarification = evaluate_data_sufficiency(
        request,
        _canonicalization_result(),
        period_coverage_evidence=_coverage(request),
    )
    with_clarification = evaluate_data_sufficiency(
        request,
        _canonicalization_result(),
        period_coverage_evidence=_coverage(request),
        clarification_items=(
            ClarificationItem(
                item_id="clarify_category",
                question="Which governed category attribution should be used?",
                affected_refs=("category_contribution",),
            ),
        ),
    )

    assert without_clarification.sufficiency_id != with_clarification.sufficiency_id
