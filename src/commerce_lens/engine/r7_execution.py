"""Deterministic execution of the sole owner-authorized R7 method."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from math import isfinite, sqrt
from pathlib import Path
from statistics import median
from typing import Iterable, Sequence

import duckdb

from commerce_lens.canonical.models import EligibilityState
from commerce_lens.contracts.common import SUPPORTED_SCOPE_FILTER_FIELDS, utc_now
from commerce_lens.contracts.evidence import CanonicalDatasetReference
from commerce_lens.contracts.populations import PopulationDefinition
from commerce_lens.contracts.r7 import (
    DiagnosticExecutionRecord, DiagnosticTestRequest, ExcludedWeeklyObservation,
    ExecutedDiagnosticResult, R7ExecutionStatus, WeeklyDiagnosticObservation,
    executed_result_fingerprint,
)
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, generate_id, sha256_file, stable_content_id
from commerce_lens.persistence.artifact_store import ArtifactStore


class R7ExecutionError(RuntimeError):
    """The authenticated method could not be executed."""


@dataclass(frozen=True)
class R7Transaction:
    order_date: date
    product_id: str
    line_revenue: Decimal


@dataclass(frozen=True)
class R7ExecutionOutcome:
    execution_record: DiagnosticExecutionRecord
    executed_result: ExecutedDiagnosticResult


def average_ranks(values: Sequence[object]) -> tuple[float, ...]:
    """Return stable one-based average ranks, including exact tie handling."""
    indexed = sorted(enumerate(values), key=lambda item: (item[1], item[0]))
    ranks = [0.0] * len(values)
    index = 0
    while index < len(indexed):
        end = index + 1
        while end < len(indexed) and indexed[end][1] == indexed[index][1]:
            end += 1
        rank = ((index + 1) + end) / 2.0
        for original, _ in indexed[index:end]:
            ranks[original] = rank
        index = end
    return tuple(ranks)


def spearman_rho(left: Sequence[object], right: Sequence[object]) -> float | None:
    if len(left) != len(right) or not left:
        return None
    x = average_ranks(left); y = average_ranks(right)
    x_mean = sum(x) / len(x); y_mean = sum(y) / len(y)
    numerator = sum((a - x_mean) * (b - y_mean) for a, b in zip(x, y, strict=True))
    x_ss = sum((a - x_mean) ** 2 for a in x); y_ss = sum((b - y_mean) ** 2 for b in y)
    denominator = sqrt(x_ss * y_ss)
    if denominator == 0.0:
        return None
    value = numerator / denominator
    if not isfinite(value):
        return None
    return max(-1.0, min(1.0, value))


def full_iso_weeks(start: date, end: date) -> tuple[tuple[date, date], ...]:
    first = start + timedelta(days=(-start.weekday()) % 7)
    weeks = []
    cursor = first
    while cursor + timedelta(days=6) <= end:
        weeks.append((cursor, cursor + timedelta(days=6)))
        cursor += timedelta(days=7)
    return tuple(weeks)


def calculate_r7_result(
    *, request: DiagnosticTestRequest, transactions: Iterable[R7Transaction], execution_event_id: str,
) -> ExecutedDiagnosticResult:
    rows = tuple(transactions)
    baseline_rows = tuple(row for row in rows if request.baseline_start <= row.order_date <= request.baseline_end)
    baseline_products = frozenset(row.product_id for row in baseline_rows)
    baseline_fp = canonical_json_fingerprint(sorted(baseline_products))
    raw: list[tuple[str, date, date, str, frozenset[str], Decimal, float]] = []
    excluded: list[ExcludedWeeklyObservation] = []
    for role, start, end in (
        ("BASELINE", request.baseline_start, request.baseline_end),
        ("COMPARISON", request.comparison_start, request.comparison_end),
    ):
        for week_start, week_end in full_iso_weeks(start, end):
            week_id = f"{week_start.isocalendar().year}-W{week_start.isocalendar().week:02d}"
            week_rows = tuple(row for row in rows if week_start <= row.order_date <= week_end)
            products = frozenset(row.product_id for row in week_rows)
            if not products:
                excluded.append(ExcludedWeeklyObservation(week_id=week_id, period_role=role, reason="NO_AUTHENTICATED_ELIGIBLE_LINES"))
                continue
            union = products | baseline_products
            if not union:
                excluded.append(ExcludedWeeklyObservation(week_id=week_id, period_role=role, reason="EMPTY_JACCARD_UNION"))
                continue
            revenue = sum((row.line_revenue for row in week_rows), Decimal("0"))
            distance = 1.0 - (len(products & baseline_products) / len(union))
            raw.append((week_id, week_start, week_end, role, products, revenue, distance))
    baseline_revenues = [item[5] for item in raw if item[3] == "BASELINE"]
    reference = Decimal(str(median(baseline_revenues))) if baseline_revenues else None
    deviations = [item[5] - reference for item in raw] if reference is not None else []
    distances = [item[6] for item in raw] if reference is not None else []
    distance_ranks = average_ranks(distances); deviation_ranks = average_ranks(deviations)
    observations = tuple(
        WeeklyDiagnosticObservation(
            week_id=item[0], week_start=item[1], week_end=item[2], period_role=item[3],
            product_set_fingerprint=canonical_json_fingerprint(sorted(item[4])), active_product_count=len(item[4]),
            jaccard_distance=item[6], weekly_revenue=item[5], revenue_deviation=deviations[index],
            distance_rank=distance_ranks[index], revenue_deviation_rank=deviation_ranks[index],
        ) for index, item in enumerate(raw)
    )
    baseline_count = sum(item.period_role == "BASELINE" for item in observations)
    comparison_count = sum(item.period_role == "COMPARISON" for item in observations)
    reasons: list[str] = []
    if len(observations) < 8: reasons.append("MINIMUM_TOTAL_WEEKS_NOT_MET")
    if baseline_count < 4: reasons.append("MINIMUM_BASELINE_WEEKS_NOT_MET")
    if comparison_count < 4: reasons.append("MINIMUM_COMPARISON_WEEKS_NOT_MET")
    if observations and len(set(distances)) == 1: reasons.append("CONSTANT_JACCARD_VECTOR")
    if observations and len(set(deviations)) == 1: reasons.append("CONSTANT_REVENUE_DEVIATION_VECTOR")
    rho = None if reasons else spearman_rho(distances, deviations)
    if not reasons and rho is None: reasons.append("UNDEFINED_SPEARMAN_DENOMINATOR")
    material = dict(
        executed_result_id="pending", execution_event_id=execution_event_id,
        test_request_ref=request.test_request_id, request_fingerprint=request.request_fingerprint,
        method=request.method, support_criterion=request.support_criterion,
        validation_profile=request.validation_profile, implementation=request.implementation,
        baseline_product_set_fingerprint=baseline_fp, baseline_product_count=len(baseline_products),
        observations=observations, excluded_observations=tuple(excluded), baseline_week_count=baseline_count,
        comparison_week_count=comparison_count, baseline_weekly_revenue_reference=reference,
        spearman_rho=rho, inconclusive_reasons=tuple(reasons), result_fingerprint="0" * 64,
    )
    fp = executed_result_fingerprint(material)
    material.update(executed_result_id=stable_content_id("r7result", fp), result_fingerprint=fp)
    return ExecutedDiagnosticResult(**material)


def execute_r7_diagnostic(
    *, request: DiagnosticTestRequest, canonical_dataset: CanonicalDatasetReference,
    baseline_population: PopulationDefinition, comparison_population: PopulationDefinition,
    artifact_store: ArtifactStore,
) -> R7ExecutionOutcome:
    _authenticate_execution_inputs(request, canonical_dataset, baseline_population, comparison_population)
    started = utc_now(); event_id = generate_id("r7exec")
    try:
        path = _verified_path(canonical_dataset, artifact_store)
        transactions = _load_transactions(path, baseline_population, request.baseline_start, request.comparison_end)
        result = calculate_r7_result(request=request, transactions=transactions, execution_event_id=event_id)
        ended = utc_now()
        record = DiagnosticExecutionRecord(
            execution_event_id=event_id, test_request_ref=request.test_request_id,
            request_fingerprint=request.request_fingerprint, method=request.method, implementation=request.implementation,
            started_at=started, ended_at=ended, status=R7ExecutionStatus.COMPLETED, result_ref=result.executed_result_id,
        )
        return R7ExecutionOutcome(record, result)
    except Exception as exc:
        raise R7ExecutionError(f"R7 deterministic execution failed: {exc}") from exc


def _authenticate_execution_inputs(request, canonical, baseline, comparison) -> None:
    if request.canonical_dataset_ref != canonical.canonical_dataset_id or request.canonical_dataset_fingerprint != canonical.content_fingerprint:
        raise R7ExecutionError("canonical dataset binding mismatch")
    if (request.baseline_population_ref, request.baseline_population_fingerprint) != (baseline.population_id, baseline.population_fingerprint):
        raise R7ExecutionError("baseline population binding mismatch")
    if (request.comparison_population_ref, request.comparison_population_fingerprint) != (comparison.population_id, comparison.population_fingerprint):
        raise R7ExecutionError("comparison population binding mismatch")
    if baseline.scope.scope_id != request.scope_ref or comparison.scope.scope_id != request.scope_ref:
        raise R7ExecutionError("scope binding mismatch")
    if baseline.period.start_date != request.baseline_start or baseline.period.end_date != request.baseline_end:
        raise R7ExecutionError("baseline period binding mismatch")
    if comparison.period.start_date != request.comparison_start or comparison.period.end_date != request.comparison_end:
        raise R7ExecutionError("comparison period binding mismatch")


def _verified_path(canonical, store) -> Path:
    path = store.safe_path(canonical.artifact.path)
    if not path.is_file() or sha256_file(path) != canonical.content_fingerprint:
        raise R7ExecutionError("canonical artifact integrity failure")
    return path


def _load_transactions(path: Path, population: PopulationDefinition, start: date, end: date) -> tuple[R7Transaction, ...]:
    clauses = ["eligibility_status = ?", "order_date >= ?", "order_date <= ?"]
    params: list[object] = [str(path), EligibilityState.ELIGIBLE.value, start, end]
    for item in population.scope.filters:
        if item.field not in SUPPORTED_SCOPE_FILTER_FIELDS or item.operator != "equals":
            raise R7ExecutionError("unsupported governed scope filter")
        clauses.append(f'"{item.field}" = ?'); params.append(item.value)
    query = f"SELECT order_date, product_id, line_revenue FROM read_parquet(?) WHERE {' AND '.join(clauses)} ORDER BY order_date, product_id"
    rows = duckdb.connect(":memory:").execute(query, params).fetchall()
    return tuple(R7Transaction(row[0], row[1], row[2]) for row in rows)
