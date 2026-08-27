"""Deterministic Phase 2 Data Sufficiency evaluator."""

from __future__ import annotations

from datetime import date

from commerce_lens.canonical.models import CanonicalizationResult, PeriodCoverageEvidence
from commerce_lens.canonical.quality import DataQualityCheckResult, DataQualityConsequence
from commerce_lens.canonical.schema import CANONICAL_SCHEMA_VERSION
from commerce_lens.contracts.common import (
    AvailableEvidence,
    EvidenceRequirement,
    FailureDetail,
    FailureStage,
    MetricState,
    SUPPORTED_SCOPE_FILTER_FIELDS,
    SUPPORTED_SCOPE_FILTER_OPERATORS,
)
from commerce_lens.contracts.requests import AnalysisRequest
from commerce_lens.contracts.sufficiency import (
    ClarificationItem,
    DataSufficiencyResult,
    MetricEligibility,
    SufficiencyState,
)
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, stable_content_id


def evaluate_data_sufficiency(
    request: AnalysisRequest,
    canonicalization_result: CanonicalizationResult,
    *,
    available_evidence: tuple[AvailableEvidence, ...] = (),
    period_coverage_evidence: tuple[PeriodCoverageEvidence, ...] = (),
    clarification_items: tuple[ClarificationItem, ...] = (),
) -> DataSufficiencyResult:
    """Evaluate whether requested Metric chains may proceed to future execution."""
    linkage_failures = _linkage_failures(request, canonicalization_result)
    canonicalization_failures = _canonicalization_failures(canonicalization_result)
    requirement_failures = _required_evidence_failures(request.required_evidence, available_evidence)
    period_failures = _period_failures(request, period_coverage_evidence)
    scope_failures = _scope_failures(request)
    quality_failures = _quality_failures(canonicalization_result.data_quality_results)
    non_clarification_failures = (
        *linkage_failures,
        *canonicalization_failures,
        *requirement_failures,
        *period_failures,
        *scope_failures,
        *quality_failures,
    )
    metric_eligibility: list[MetricEligibility] = []
    any_clarification_failure = False
    for metric in request.metrics:
        metric_ref = metric.metric_id
        clarification_failures = _clarification_failures(request, clarification_items, metric_ref)
        any_clarification_failure = any_clarification_failure or bool(clarification_failures)
        scoped_failures = tuple(
            failure
            for failure in (*non_clarification_failures, *clarification_failures)
            if failure.dependency_scope in (None, metric_ref)
        )
        eligible = not scoped_failures
        metric_eligibility.append(
            MetricEligibility(
                metric_ref=metric_ref,
                eligible=eligible,
                metric_state=None if eligible else MetricState.INADMISSIBLE,
                failure_details=scoped_failures,
            )
        )

    eligible_count = sum(1 for eligibility in metric_eligibility if eligibility.eligible)
    if eligible_count == len(metric_eligibility):
        state = SufficiencyState.SUFFICIENT
    elif eligible_count > 0:
        state = SufficiencyState.PARTIAL
    elif any_clarification_failure and not non_clarification_failures:
        state = SufficiencyState.CLARIFICATION_REQUIRED
    elif any(failure.stage is FailureStage.INTAKE for failure in (*canonicalization_failures, *quality_failures)):
        state = SufficiencyState.DATA_QUALITY_FAILURE
    else:
        state = SufficiencyState.INSUFFICIENT_EVIDENCE

    all_failures = tuple((*non_clarification_failures, *tuple(f for item in metric_eligibility for f in item.failure_details if f.stage is FailureStage.SUFFICIENCY and f.reason.startswith("clarification required"))))
    sufficiency_fingerprint = canonical_json_fingerprint(
        {
            "request": request.model_dump(mode="json"),
            "canonicalization_record": canonicalization_result.record.model_dump(mode="json"),
            "canonical_dataset": (
                canonicalization_result.canonical_dataset.model_dump(mode="json")
                if canonicalization_result.canonical_dataset is not None
                else None
            ),
            "available_evidence": [evidence.model_dump(mode="json") for evidence in available_evidence],
            "coverage": [coverage.model_dump(mode="json") for coverage in period_coverage_evidence],
            "clarifications": [item.model_dump(mode="json") for item in clarification_items],
            "quality_results": [result.model_dump(mode="json") for result in canonicalization_result.data_quality_results],
            "metric_eligibility": [item.model_dump(mode="json") for item in metric_eligibility],
            "state": state.value,
        }
    )
    return DataSufficiencyResult(
        sufficiency_id=stable_content_id("suff", sufficiency_fingerprint),
        request_id=request.request_id,
        dataset_ref_id=request.dataset_ref_id,
        canonical_dataset_ref_id=(
            canonicalization_result.canonical_dataset.canonical_dataset_id
            if canonicalization_result.canonical_dataset is not None
            else None
        ),
        required_evidence=request.required_evidence,
        available_evidence=available_evidence,
        metric_eligibility=tuple(metric_eligibility),
        data_quality_failures=all_failures,
        clarification_items=clarification_items,
        assumptions=request.assumptions,
        qualifications=canonicalization_result.qualifications,
        state=state,
    )


def _linkage_failures(
    request: AnalysisRequest,
    canonicalization_result: CanonicalizationResult,
) -> tuple[FailureDetail, ...]:
    failures: list[FailureDetail] = []
    record = canonicalization_result.record
    canonical_dataset = canonicalization_result.canonical_dataset
    if request.dataset_ref_id != record.source_dataset_id:
        failures.append(
            FailureDetail(
                stage=FailureStage.SUFFICIENCY,
                reason="AnalysisRequest dataset_ref_id does not match CanonicalizationRecord source_dataset_id",
                target_ref="dataset_ref_id",
                governing_ref="architecture:8.2",
            )
        )
    if request.canonical_schema_version != record.canonical_schema_version:
        failures.append(
            FailureDetail(
                stage=FailureStage.SUFFICIENCY,
                reason="AnalysisRequest canonical schema version does not match CanonicalizationRecord",
                target_ref="canonical_schema_version",
                governing_ref="architecture:8.2",
            )
        )
    if record.canonical_schema_version != CANONICAL_SCHEMA_VERSION:
        failures.append(
            FailureDetail(
                stage=FailureStage.SUFFICIENCY,
                reason="CanonicalizationRecord uses an unsupported canonical schema version",
                target_ref="canonical_schema_version",
                governing_ref="canonical_dictionary:9",
            )
        )
    if request.selected_sheet is not None and request.selected_sheet != record.selected_sheet:
        failures.append(
            FailureDetail(
                stage=FailureStage.SUFFICIENCY,
                reason="AnalysisRequest selected_sheet does not match CanonicalizationRecord selected_sheet",
                target_ref="selected_sheet",
                governing_ref="architecture:8.2",
            )
        )
    if request.selected_table is not None and request.selected_table != record.selected_table:
        failures.append(
            FailureDetail(
                stage=FailureStage.SUFFICIENCY,
                reason="AnalysisRequest selected_table does not match CanonicalizationRecord selected_table",
                target_ref="selected_table",
                governing_ref="architecture:8.2",
            )
        )
    if canonical_dataset is None:
        return tuple(failures)
    if record.source_dataset_id != canonical_dataset.source_dataset_id:
        failures.append(
            FailureDetail(
                stage=FailureStage.SUFFICIENCY,
                reason="CanonicalizationRecord source_dataset_id does not match CanonicalDatasetReference source_dataset_id",
                target_ref="canonical_dataset.source_dataset_id",
                governing_ref="architecture:9.2",
            )
        )
    if request.dataset_ref_id != canonical_dataset.source_dataset_id:
        failures.append(
            FailureDetail(
                stage=FailureStage.SUFFICIENCY,
                reason="AnalysisRequest dataset_ref_id does not match CanonicalDatasetReference source_dataset_id",
                target_ref="canonical_dataset.source_dataset_id",
                governing_ref="architecture:8.2",
            )
        )
    if record.canonical_dataset_id != canonical_dataset.canonical_dataset_id:
        failures.append(
            FailureDetail(
                stage=FailureStage.SUFFICIENCY,
                reason="CanonicalizationRecord canonical_dataset_id does not match CanonicalDatasetReference canonical_dataset_id",
                target_ref="canonical_dataset_id",
                governing_ref="architecture:9.2",
            )
        )
    if record.canonical_schema_version != canonical_dataset.canonical_schema_version:
        failures.append(
            FailureDetail(
                stage=FailureStage.SUFFICIENCY,
                reason="CanonicalizationRecord canonical schema version does not match CanonicalDatasetReference",
                target_ref="canonical_dataset.canonical_schema_version",
                governing_ref="architecture:9.2",
            )
        )
    if request.canonical_schema_version != canonical_dataset.canonical_schema_version:
        failures.append(
            FailureDetail(
                stage=FailureStage.SUFFICIENCY,
                reason="AnalysisRequest canonical schema version does not match CanonicalDatasetReference",
                target_ref="canonical_dataset.canonical_schema_version",
                governing_ref="architecture:8.2",
            )
        )
    if canonical_dataset.canonical_schema_version != CANONICAL_SCHEMA_VERSION:
        failures.append(
            FailureDetail(
                stage=FailureStage.SUFFICIENCY,
                reason="CanonicalDatasetReference uses an unsupported canonical schema version",
                target_ref="canonical_dataset.canonical_schema_version",
                governing_ref="canonical_dictionary:9",
            )
        )
    return tuple(failures)


def _canonicalization_failures(canonicalization_result: CanonicalizationResult) -> tuple[FailureDetail, ...]:
    failures: list[FailureDetail] = []
    if canonicalization_result.canonical_dataset is None:
        failures.append(
            FailureDetail(
                stage=FailureStage.INTAKE,
                reason="successful canonicalization is required before future Metric execution",
                target_ref=canonicalization_result.record.canonicalization_id,
                governing_ref="architecture:7.4",
            )
        )
    for failure in (*canonicalization_result.failures, *canonicalization_result.record.failures):
        failures.append(
            FailureDetail(
                stage=FailureStage.INTAKE,
                reason=failure,
                target_ref=canonicalization_result.record.canonicalization_id,
                governing_ref="architecture:7.4",
            )
        )
    return tuple(dict.fromkeys(failures))


def _scope_failures(request: AnalysisRequest) -> tuple[FailureDetail, ...]:
    failures: list[FailureDetail] = []
    for scope_filter in request.scope.filters:
        if scope_filter.field not in SUPPORTED_SCOPE_FILTER_FIELDS:
            failures.append(
                FailureDetail(
                    stage=FailureStage.SUFFICIENCY,
                    reason=f"unsupported governed scope filter field: {scope_filter.field}",
                    target_ref=request.scope.scope_id,
                    governing_ref="canonical_dictionary:27",
                )
            )
        if scope_filter.operator not in SUPPORTED_SCOPE_FILTER_OPERATORS:
            failures.append(
                FailureDetail(
                    stage=FailureStage.SUFFICIENCY,
                    reason=f"unsupported governed scope filter operator: {scope_filter.operator}",
                    target_ref=request.scope.scope_id,
                    governing_ref="canonical_dictionary:27",
                )
            )
    return tuple(failures)


def _clarification_failures(
    request: AnalysisRequest,
    clarification_items: tuple[ClarificationItem, ...],
    metric_ref: str,
) -> tuple[FailureDetail, ...]:
    failures: list[FailureDetail] = []
    global_refs = {"global", "all", request.request_id, request.scope.scope_id, "comparison_periods"}
    for item in clarification_items:
        affected = set(item.affected_refs)
        if not affected or metric_ref in affected or affected & global_refs:
            failures.append(
                FailureDetail(
                    stage=FailureStage.SUFFICIENCY,
                    reason=f"clarification required: {item.question}",
                    target_ref=item.item_id,
                    governing_ref="evidence_contract:14",
                    dependency_scope=None if not affected or affected & global_refs else metric_ref,
                    independent_chains_may_continue=bool(affected) and not (affected & global_refs),
                )
            )
    return tuple(failures)


def _required_evidence_failures(
    requirements: tuple[EvidenceRequirement, ...],
    available_evidence: tuple[AvailableEvidence, ...],
) -> tuple[FailureDetail, ...]:
    satisfied = {
        requirement_id
        for evidence in available_evidence
        for requirement_id in evidence.satisfies_requirement_ids
    }
    failures = []
    for requirement in requirements:
        if requirement.requirement_id in satisfied:
            continue
        failures.append(
            FailureDetail(
                stage=FailureStage.SUFFICIENCY,
                reason=f"required evidence is missing: {requirement.description}",
                target_ref=requirement.requirement_id,
                governing_ref="evidence_contract:13",
                dependency_scope=requirement.metric_ref,
                independent_chains_may_continue=requirement.metric_ref is not None,
            )
        )
    return tuple(failures)


def _period_failures(
    request: AnalysisRequest,
    coverage_evidence: tuple[PeriodCoverageEvidence, ...],
) -> tuple[FailureDetail, ...]:
    failures: list[FailureDetail] = []
    baseline = request.baseline_period
    comparison = request.comparison_period
    if baseline.date_convention_ref != comparison.date_convention_ref:
        failures.append(_period_failure("baseline and comparison use different date conventions"))
    if baseline.end_date >= comparison.start_date:
        failures.append(_period_failure("baseline must be earlier than comparison and non-overlapping"))
    if _inclusive_days(baseline.start_date, baseline.end_date) != _inclusive_days(
        comparison.start_date, comparison.end_date
    ):
        failures.append(_period_failure("baseline and comparison periods must have equal duration"))
    if not _period_is_covered(
        request.dataset_ref_id,
        baseline.start_date,
        baseline.end_date,
        baseline.date_convention_ref,
        coverage_evidence,
    ):
        failures.append(_period_failure("explicit coverage evidence does not span the baseline period"))
    if not _period_is_covered(
        request.dataset_ref_id,
        comparison.start_date,
        comparison.end_date,
        comparison.date_convention_ref,
        coverage_evidence,
    ):
        failures.append(_period_failure("explicit coverage evidence does not span the comparison period"))
    return tuple(failures)


def _period_failure(reason: str) -> FailureDetail:
    return FailureDetail(
        stage=FailureStage.SUFFICIENCY,
        reason=reason,
        target_ref="comparison_periods",
        governing_ref="canonical_dictionary:15",
    )


def _period_is_covered(
    dataset_ref_id: str,
    start_date: date,
    end_date: date,
    date_convention_ref: str,
    coverage_evidence: tuple[PeriodCoverageEvidence, ...],
) -> bool:
    return any(
        coverage.dataset_ref_id == dataset_ref_id
        and coverage.date_convention_ref == date_convention_ref
        and coverage.observed_start_date <= start_date
        and coverage.observed_end_date >= end_date
        for coverage in coverage_evidence
    )


def _inclusive_days(start_date: date, end_date: date) -> int:
    return (end_date - start_date).days + 1


def _quality_failures(quality_results: tuple[DataQualityCheckResult, ...]) -> tuple[FailureDetail, ...]:
    failures: list[FailureDetail] = []
    for result in quality_results:
        if result.consequence is not DataQualityConsequence.BLOCKING:
            continue
        if result.affected_metric_refs:
            for metric_ref in result.affected_metric_refs:
                failures.append(_quality_failure(result, metric_ref))
        else:
            failures.append(_quality_failure(result, None))
    return tuple(failures)


def _quality_failure(result: DataQualityCheckResult, metric_ref: str | None) -> FailureDetail:
    return FailureDetail(
        stage=FailureStage.INTAKE,
        reason=result.reason,
        target_ref=result.target,
        governing_ref=result.governing_ref,
        dependency_scope=metric_ref,
        independent_chains_may_continue=metric_ref is not None,
    )
