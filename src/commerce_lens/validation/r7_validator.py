"""Independent reconstruction validator for R7 diagnostic results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from math import isfinite, sqrt
from pathlib import Path
from statistics import median
from typing import Sequence

import duckdb

from commerce_lens.canonical.models import EligibilityState
from commerce_lens.contracts.common import SUPPORTED_SCOPE_FILTER_FIELDS, utc_now
from commerce_lens.contracts.evidence import CanonicalDatasetReference
from commerce_lens.contracts.populations import PopulationDefinition
from commerce_lens.contracts.r7 import (
    DiagnosticTestRequest, DiagnosticValidationCheck, DiagnosticValidationRecord,
    ExcludedWeeklyObservation, ExecutedDiagnosticResult, R7ValidationStatus,
    ValidatedDiagnosticResult, WeeklyDiagnosticObservation, executed_result_fingerprint,
)
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, generate_id, sha256_file, stable_content_id
from commerce_lens.persistence.artifact_store import ArtifactStore


@dataclass(frozen=True)
class R7ValidationOutcome:
    validation_record: DiagnosticValidationRecord
    validated_result: ValidatedDiagnosticResult | None


@dataclass(frozen=True)
class _Row:
    order_date: date
    product_id: str
    line_revenue: Decimal


@dataclass(frozen=True)
class _Expected:
    baseline_product_set_fingerprint: str
    baseline_product_count: int
    observations: tuple[WeeklyDiagnosticObservation, ...]
    excluded: tuple[ExcludedWeeklyObservation, ...]
    baseline_count: int
    comparison_count: int
    reference: Decimal | None
    rho: float | None
    reasons: tuple[str, ...]


def validate_r7_result(*, request: DiagnosticTestRequest, executed_result: ExecutedDiagnosticResult,
                       canonical_dataset: CanonicalDatasetReference, baseline_population: PopulationDefinition,
                       comparison_population: PopulationDefinition, artifact_store: ArtifactStore) -> R7ValidationOutcome:
    started = utc_now(); event_id = generate_id("r7val")
    path = _validator_verified_path(canonical_dataset, artifact_store)
    rows = _validator_load_rows(path, baseline_population, request.baseline_start, request.comparison_end)
    expected = _validator_reconstruct(request, rows)
    authority_ok = (
        executed_result.method == request.method
        and executed_result.support_criterion == request.support_criterion
        and executed_result.validation_profile == request.validation_profile
        and executed_result.implementation == request.implementation
    )
    observation_ok = executed_result.observations == expected.observations
    comparisons = {
        "method_version_fingerprint": authority_ok,
        "family_and_request_binding": executed_result.test_request_ref == request.test_request_id and executed_result.request_fingerprint == request.request_fingerprint,
        "weekly_bucket_membership_and_full_week_rule": observation_ok and executed_result.excluded_observations == expected.excluded,
        "baseline_product_set_reconstruction": executed_result.baseline_product_set_fingerprint == expected.baseline_product_set_fingerprint and executed_result.baseline_product_count == expected.baseline_product_count,
        "jaccard_distance_reconstruction": observation_ok and all(isfinite(item.jaccard_distance) and 0.0 <= item.jaccard_distance <= 1.0 for item in executed_result.observations),
        "weekly_revenue_reconciliation": observation_ok and all(item.weekly_revenue.is_finite() for item in executed_result.observations),
        "baseline_median_and_revenue_deviation": observation_ok and executed_result.baseline_weekly_revenue_reference == expected.reference,
        "independent_average_rank_and_tie_handling": observation_ok,
        "independent_spearman_recomputation": executed_result.spearman_rho == expected.rho and (executed_result.spearman_rho is None or isfinite(executed_result.spearman_rho)),
        "valid_excluded_counts_sample_minimums_and_vector_variation": (
            executed_result.baseline_week_count == expected.baseline_count
            and executed_result.comparison_week_count == expected.comparison_count
            and executed_result.inconclusive_reasons == expected.reasons
        ),
        "decision_boundary_domain": _validator_decision(executed_result.spearman_rho, executed_result.inconclusive_reasons) == _validator_decision(expected.rho, expected.reasons),
        "semantic_fingerprint": executed_result.result_fingerprint == _expected_fingerprint(request, executed_result.execution_event_id, expected),
    }
    checks = tuple(DiagnosticValidationCheck(check_id=key, passed=value, failure_code=None if value else "R7_VALIDATION_MISMATCH") for key, value in comparisons.items())
    status = R7ValidationStatus.PASSED if all(comparisons.values()) else R7ValidationStatus.FAILED
    validation_fp = canonical_json_fingerprint({"executed_result_fingerprint": executed_result.result_fingerprint, "checks": [c.model_dump(mode="json") for c in checks], "status": status.value})
    validated = None
    if status is R7ValidationStatus.PASSED:
        validated_id = stable_content_id("r7validated", validation_fp)
        validated = ValidatedDiagnosticResult(
            validated_result_id=validated_id, validation_event_id=event_id,
            execution_event_id=executed_result.execution_event_id, executed_result_ref=executed_result.executed_result_id,
            result_fingerprint=executed_result.result_fingerprint, validation_fingerprint=validation_fp,
            test_request_ref=request.test_request_id, method=request.method, support_criterion=request.support_criterion,
            validation_profile=request.validation_profile, baseline_week_count=executed_result.baseline_week_count,
            comparison_week_count=executed_result.comparison_week_count, spearman_rho=executed_result.spearman_rho,
            inconclusive_reasons=executed_result.inconclusive_reasons,
        )
    record = DiagnosticValidationRecord(
        validation_event_id=event_id, executed_result_ref=executed_result.executed_result_id,
        executed_result_fingerprint=executed_result.result_fingerprint, validation_profile=request.validation_profile,
        checks=checks, status=status, validated_result_ref=validated.validated_result_id if validated else None,
        started_at=started, ended_at=utc_now(), validation_fingerprint=validation_fp,
    )
    return R7ValidationOutcome(record, validated)


def _validator_verified_path(canonical: CanonicalDatasetReference, store: ArtifactStore) -> Path:
    path = store.safe_path(canonical.artifact.path)
    if not path.is_file() or canonical.artifact.fingerprint is None:
        raise ValueError("R7_VALIDATION_CANONICAL_ARTIFACT_MISSING")
    fingerprint = sha256_file(path)
    if fingerprint != canonical.artifact.fingerprint or fingerprint != canonical.content_fingerprint:
        raise ValueError("R7_VALIDATION_CANONICAL_ARTIFACT_INTEGRITY")
    return path


def _validator_load_rows(path: Path, population: PopulationDefinition, start: date, end: date) -> tuple[_Row, ...]:
    clauses = ["eligibility_status = ?", "order_date >= ?", "order_date <= ?"]
    params: list[object] = [str(path), EligibilityState.ELIGIBLE.value, start, end]
    for item in population.scope.filters:
        if item.field not in SUPPORTED_SCOPE_FILTER_FIELDS or item.operator != "equals":
            raise ValueError("R7_VALIDATION_SCOPE_FILTER_UNSUPPORTED")
        clauses.append(f'"{item.field}" = ?'); params.append(item.value)
    query = f"SELECT order_date, product_id, line_revenue FROM read_parquet(?) WHERE {' AND '.join(clauses)} ORDER BY order_date, product_id"
    return tuple(_Row(*row) for row in duckdb.connect(":memory:").execute(query, params).fetchall())


def _validator_full_weeks(start: date, end: date) -> tuple[tuple[date, date], ...]:
    cursor = start + timedelta(days=(-start.weekday()) % 7); result = []
    while cursor + timedelta(days=6) <= end:
        result.append((cursor, cursor + timedelta(days=6))); cursor += timedelta(days=7)
    return tuple(result)


def _validator_ranks(values: Sequence[object]) -> tuple[float, ...]:
    ordered = sorted(enumerate(values), key=lambda item: (item[1], item[0])); ranks = [0.0] * len(values); start = 0
    while start < len(ordered):
        stop = start + 1
        while stop < len(ordered) and ordered[stop][1] == ordered[start][1]: stop += 1
        value = ((start + 1) + stop) / 2.0
        for original, _ in ordered[start:stop]: ranks[original] = value
        start = stop
    return tuple(ranks)


def _validator_spearman(left: Sequence[object], right: Sequence[object]) -> float | None:
    if not left or len(left) != len(right): return None
    x = _validator_ranks(left); y = _validator_ranks(right); xm = sum(x)/len(x); ym = sum(y)/len(y)
    numerator = sum((a-xm)*(b-ym) for a,b in zip(x,y,strict=True))
    denominator = sqrt(sum((a-xm)**2 for a in x) * sum((b-ym)**2 for b in y))
    if denominator == 0.0: return None
    rho = numerator / denominator
    return max(-1.0, min(1.0, rho)) if isfinite(rho) else None


def _validator_reconstruct(request: DiagnosticTestRequest, rows: tuple[_Row, ...]) -> _Expected:
    baseline_products = frozenset(row.product_id for row in rows if request.baseline_start <= row.order_date <= request.baseline_end)
    raw = []; excluded = []
    for role, start, end in (("BASELINE", request.baseline_start, request.baseline_end), ("COMPARISON", request.comparison_start, request.comparison_end)):
        for week_start, week_end in _validator_full_weeks(start, end):
            week_id = f"{week_start.isocalendar().year}-W{week_start.isocalendar().week:02d}"
            week_rows = tuple(row for row in rows if week_start <= row.order_date <= week_end)
            products = frozenset(row.product_id for row in week_rows)
            if not products:
                excluded.append(ExcludedWeeklyObservation(week_id=week_id, period_role=role, reason="NO_AUTHENTICATED_ELIGIBLE_LINES")); continue
            union = products | baseline_products
            if not union:
                excluded.append(ExcludedWeeklyObservation(week_id=week_id, period_role=role, reason="EMPTY_JACCARD_UNION")); continue
            raw.append((week_id, week_start, week_end, role, products, sum((row.line_revenue for row in week_rows), Decimal("0")), 1.0-len(products & baseline_products)/len(union)))
    baseline_revenues = [item[5] for item in raw if item[3] == "BASELINE"]
    reference = Decimal(str(median(baseline_revenues))) if baseline_revenues else None
    deviations = [item[5]-reference for item in raw] if reference is not None else []
    distances = [item[6] for item in raw] if reference is not None else []
    distance_ranks = _validator_ranks(distances); deviation_ranks = _validator_ranks(deviations)
    observations = tuple(WeeklyDiagnosticObservation(
        week_id=item[0], week_start=item[1], week_end=item[2], period_role=item[3],
        product_set_fingerprint=canonical_json_fingerprint(sorted(item[4])), active_product_count=len(item[4]),
        jaccard_distance=item[6], weekly_revenue=item[5], revenue_deviation=deviations[index],
        distance_rank=distance_ranks[index], revenue_deviation_rank=deviation_ranks[index],
    ) for index,item in enumerate(raw))
    baseline_count = sum(item.period_role == "BASELINE" for item in observations); comparison_count = len(observations)-baseline_count
    reasons=[]
    if len(observations)<8: reasons.append("MINIMUM_TOTAL_WEEKS_NOT_MET")
    if baseline_count<4: reasons.append("MINIMUM_BASELINE_WEEKS_NOT_MET")
    if comparison_count<4: reasons.append("MINIMUM_COMPARISON_WEEKS_NOT_MET")
    if observations and len(set(distances))==1: reasons.append("CONSTANT_JACCARD_VECTOR")
    if observations and len(set(deviations))==1: reasons.append("CONSTANT_REVENUE_DEVIATION_VECTOR")
    rho = None if reasons else _validator_spearman(distances,deviations)
    if not reasons and rho is None: reasons.append("UNDEFINED_SPEARMAN_DENOMINATOR")
    return _Expected(canonical_json_fingerprint(sorted(baseline_products)),len(baseline_products),observations,tuple(excluded),baseline_count,comparison_count,reference,rho,tuple(reasons))


def _validator_decision(rho: float | None, reasons: tuple[str, ...]) -> str:
    if rho is None or reasons: return "NOT_EVALUATED"
    if rho <= -0.5: return "CRITERION_MET"
    if rho >= 0.5: return "PROPOSITION_CONTRADICTED"
    return "CRITERION_NOT_MET"


def _expected_fingerprint(request: DiagnosticTestRequest, execution_event_id: str, expected: _Expected) -> str:
    return executed_result_fingerprint({
        "executed_result_id":"pending", "execution_event_id":execution_event_id,
        "test_request_ref":request.test_request_id, "request_fingerprint":request.request_fingerprint,
        "method":request.method, "support_criterion":request.support_criterion,
        "validation_profile":request.validation_profile, "implementation":request.implementation,
        "baseline_product_set_fingerprint":expected.baseline_product_set_fingerprint,
        "baseline_product_count":expected.baseline_product_count, "observations":expected.observations,
        "excluded_observations":expected.excluded, "baseline_week_count":expected.baseline_count,
        "comparison_week_count":expected.comparison_count, "baseline_weekly_revenue_reference":expected.reference,
        "spearman_rho":expected.rho, "inconclusive_reasons":expected.reasons, "result_fingerprint":"0"*64,
    })
