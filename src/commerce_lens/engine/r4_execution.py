"""Deterministic R4 Product-Level Revenue Decomposition execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import duckdb

from commerce_lens.canonical.models import EligibilityState
from commerce_lens.contracts.common import SUPPORTED_SCOPE_FILTER_FIELDS, utc_now
from commerce_lens.contracts.evidence import CanonicalDatasetReference
from commerce_lens.contracts.execution import ExecutionStatus
from commerce_lens.contracts.populations import PopulationDefinition
from commerce_lens.contracts.r4 import (
    ExecutedR4DecompositionResult,
    R4AuthorityBinding,
    R4Component,
    R4DecompositionRequest,
    R4ExecutionRecord,
    R4ProductClassification,
    R4ProductTrace,
    R4ProductTraceRow,
)
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, generate_id, sha256_file, stable_content_id
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.persistence.r4_repository import (
    persist_r4_executed_result,
    persist_r4_execution_record,
    persist_r4_trace,
)


class R4ExecutionError(RuntimeError):
    """Raised when an eligible R4 execution fails to produce a usable result."""


@dataclass(frozen=True)
class R4ExecutionOutcome:
    execution_record: R4ExecutionRecord
    executed_result: ExecutedR4DecompositionResult
    execution_record_artifact: Any
    executed_result_artifact: Any
    product_trace: R4ProductTrace


def execute_r4_decomposition(
    *,
    request: R4DecompositionRequest,
    authority: R4AuthorityBinding,
    canonical_dataset: CanonicalDatasetReference,
    baseline_population: PopulationDefinition,
    comparison_population: PopulationDefinition,
    baseline_revenue: Decimal,
    comparison_revenue: Decimal,
    observed_revenue_change: Decimal,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> R4ExecutionOutcome:
    started_at = utc_now()
    execution_id = generate_id("r4exec")
    try:
        canonical_path = _verified_canonical_path(canonical_dataset, artifact_store)
        baseline_values = _product_revenues(baseline_population, canonical_path, authority.currency)
        comparison_values = _product_revenues(comparison_population, canonical_path, authority.currency)
        rows = _trace_rows(
            execution_id,
            authority,
            baseline_values,
            comparison_values,
        )
        trace_fingerprint = _trace_fingerprint(authority, rows)
        trace = R4ProductTrace(
            trace_id=stable_content_id("r4trace", trace_fingerprint),
            trace_fingerprint=trace_fingerprint,
            execution_id=execution_id,
            authority=authority,
            rows=rows,
            row_count=len(rows),
        )
        trace_artifact = persist_r4_trace(trace, artifact_store, metadata_store)
        entry = sum((row.contribution for row in rows if row.assigned_component is R4Component.ENTRY), Decimal("0"))
        exit_value = sum((row.contribution for row in rows if row.assigned_component is R4Component.EXIT), Decimal("0"))
        continuing = sum(
            (row.contribution for row in rows if row.assigned_component is R4Component.CONTINUING),
            Decimal("0"),
        )
        component_sum = entry + exit_value + continuing
        reconciliation = observed_revenue_change - component_sum
        material = {
            "authority": authority.model_dump(mode="json"),
            "baseline_revenue": str(baseline_revenue),
            "comparison_revenue": str(comparison_revenue),
            "observed_revenue_change": str(observed_revenue_change),
            "entry_component": str(entry),
            "exit_component": str(exit_value),
            "continuing_component": str(continuing),
            "component_sum": str(component_sum),
            "reconciliation_difference": str(reconciliation),
            "product_trace_fingerprint": trace_fingerprint,
            "product_count": len(rows),
            "entry_product_count": sum(row.classification is R4ProductClassification.COMPARISON_ONLY for row in rows),
            "exit_product_count": sum(row.classification is R4ProductClassification.BASELINE_ONLY for row in rows),
            "continuing_product_count": sum(row.classification is R4ProductClassification.CONTINUING for row in rows),
        }
        result = ExecutedR4DecompositionResult(
            execution_id=execution_id,
            r4_request_id=request.r4_request_id,
            authority=authority,
            baseline_revenue=baseline_revenue,
            comparison_revenue=comparison_revenue,
            observed_revenue_change=observed_revenue_change,
            entry_component=entry,
            exit_component=exit_value,
            continuing_component=continuing,
            component_sum=component_sum,
            reconciliation_difference=reconciliation,
            product_count=len(rows),
            entry_product_count=material["entry_product_count"],
            exit_product_count=material["exit_product_count"],
            continuing_product_count=material["continuing_product_count"],
            product_trace_ref=trace_artifact,
            product_trace_fingerprint=trace_fingerprint,
            result_fingerprint=canonical_json_fingerprint(material),
        )
        result_artifact = persist_r4_executed_result(result, artifact_store, metadata_store)
        ended_at = utc_now()
        record = R4ExecutionRecord(
            execution_id=execution_id,
            r4_request_id=request.r4_request_id,
            execution_context=request.execution_context,
            authority=authority,
            started_at=started_at,
            ended_at=ended_at,
            status=ExecutionStatus.COMPLETED,
            operation={
                "method": "deterministic_product_union_and_decimal_aggregation",
                "product_identity": "product_id",
                "presence_semantics": "eligible_line_presence_in_period",
                "component_identity": "entry + exit + continuing = observed_revenue_change",
                "binary_float_used": False,
                "duckdb_version": str(duckdb.__version__),
            },
            result_ref=result.result_id,
            output_artifacts=(trace_artifact, result_artifact),
        )
        record_artifact = persist_r4_execution_record(record, artifact_store, metadata_store)
        return R4ExecutionOutcome(record, result, record_artifact, result_artifact, trace)
    except Exception as exc:
        if isinstance(exc, R4ExecutionError):
            raise
        raise R4ExecutionError(f"R4 deterministic execution failed: {exc}") from exc


def _verified_canonical_path(
    canonical_dataset: CanonicalDatasetReference,
    artifact_store: ArtifactStore,
) -> Path:
    path = artifact_store.safe_path(canonical_dataset.artifact.path)
    if not path.is_file():
        raise R4ExecutionError("canonical dataset artifact is missing")
    if canonical_dataset.artifact.fingerprint is None:
        raise R4ExecutionError("canonical dataset artifact lacks a fingerprint")
    fingerprint = sha256_file(path)
    if fingerprint != canonical_dataset.artifact.fingerprint or fingerprint != canonical_dataset.content_fingerprint:
        raise R4ExecutionError("canonical dataset artifact integrity check failed")
    return path


def _product_revenues(
    population: PopulationDefinition,
    canonical_path: Path,
    expected_currency: str,
) -> dict[str, Decimal]:
    where_sql, params = _population_where(population, canonical_path)
    currency_rows = duckdb.connect(":memory:").execute(
        f"SELECT DISTINCT currency FROM read_parquet(?) WHERE {where_sql} ORDER BY currency",
        params,
    ).fetchall()
    currencies = tuple(row[0] for row in currency_rows)
    if currencies and currencies != (expected_currency,):
        raise R4ExecutionError("R4 population currency does not match authenticated Revenue authority")
    rows = duckdb.connect(":memory:").execute(
        f"SELECT product_id, SUM(line_revenue) FROM read_parquet(?) WHERE {where_sql} GROUP BY product_id ORDER BY product_id",
        params,
    ).fetchall()
    values: dict[str, Decimal] = {}
    for product_id, value in rows:
        if not isinstance(product_id, str) or not product_id.strip():
            raise R4ExecutionError("R4 encountered missing or malformed product identity")
        if product_id in values:
            raise R4ExecutionError("R4 product identity aggregation produced a duplicate identity")
        if not isinstance(value, Decimal) or not value.is_finite():
            raise R4ExecutionError("R4 product Revenue is not a finite Decimal")
        values[product_id] = value
    return values


def _population_where(population: PopulationDefinition, canonical_path: Path) -> tuple[str, tuple[Any, ...]]:
    clauses = ["eligibility_status = ?", "order_date >= ?", "order_date <= ?"]
    params: list[Any] = [
        str(canonical_path),
        EligibilityState.ELIGIBLE.value,
        population.period.start_date,
        population.period.end_date,
    ]
    for item in population.scope.filters:
        if item.field not in SUPPORTED_SCOPE_FILTER_FIELDS or item.operator != "equals":
            raise R4ExecutionError("R4 population contains an unsupported governed scope filter")
        clauses.append(f'"{item.field}" = ?')
        params.append(item.value)
    return " AND ".join(clauses), tuple(params)


def _trace_rows(
    execution_id: str,
    authority: R4AuthorityBinding,
    baseline: dict[str, Decimal],
    comparison: dict[str, Decimal],
) -> tuple[R4ProductTraceRow, ...]:
    rows: list[R4ProductTraceRow] = []
    for product_id in sorted(set(baseline) | set(comparison)):
        baseline_present = product_id in baseline
        comparison_present = product_id in comparison
        baseline_revenue = baseline.get(product_id, Decimal("0"))
        comparison_revenue = comparison.get(product_id, Decimal("0"))
        if baseline_present and comparison_present:
            classification = R4ProductClassification.CONTINUING
            component = R4Component.CONTINUING
        elif comparison_present:
            classification = R4ProductClassification.COMPARISON_ONLY
            component = R4Component.ENTRY
        else:
            classification = R4ProductClassification.BASELINE_ONLY
            component = R4Component.EXIT
        rows.append(
            R4ProductTraceRow(
                product_id=product_id,
                baseline_present=baseline_present,
                comparison_present=comparison_present,
                baseline_revenue=baseline_revenue,
                comparison_revenue=comparison_revenue,
                classification=classification,
                contribution=comparison_revenue - baseline_revenue,
                assigned_component=component,
                currency=authority.currency,
                baseline_period_ref=authority.baseline_period_ref,
                comparison_period_ref=authority.comparison_period_ref,
                baseline_population_ref=authority.baseline_population_ref,
                comparison_population_ref=authority.comparison_population_ref,
                scope_ref=authority.scope_ref,
                canonical_dataset_ref=authority.canonical_dataset_ref,
                canonical_dataset_fingerprint=authority.canonical_dataset_fingerprint,
                execution_id=execution_id,
                precision_policy_ref=authority.precision_policy_ref,
                precision_policy_version=authority.precision_policy_version,
                validation_policy_id=authority.validation_policy_id,
                validation_policy_version=authority.validation_policy_version,
            )
        )
    return tuple(rows)


def _trace_fingerprint(authority: R4AuthorityBinding, rows: tuple[R4ProductTraceRow, ...]) -> str:
    return canonical_json_fingerprint(
        {
            "authority": authority.model_dump(mode="json"),
            "rows": [
                {key: value for key, value in row.model_dump(mode="json").items() if key != "execution_id"}
                for row in rows
            ],
        }
    )
