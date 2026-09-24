"""Independent deterministic validation for R4 decomposition results."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import duckdb

from commerce_lens.canonical.models import EligibilityState
from commerce_lens.contracts.common import SUPPORTED_SCOPE_FILTER_FIELDS, ArtifactReference, utc_now
from commerce_lens.contracts.evidence import CanonicalDatasetReference
from commerce_lens.contracts.populations import PopulationDefinition
from commerce_lens.contracts.r4 import (
    ExecutedR4DecompositionResult,
    R4Component,
    R4ExecutionRecord,
    R4ProductClassification,
    R4ProductTrace,
    R4ValidationCheck,
    R4ValidationRecord,
    R4ValidationStatus,
    ValidatedR4DecompositionResult,
)
from commerce_lens.contracts.validation import ValidatedResult
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, sha256_file
from commerce_lens.metrics.registry import PRECISION_POLICY_REF, PRECISION_POLICY_VERSION
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.persistence.r4_repository import (
    load_r4_executed_result,
    load_r4_trace,
    persist_r4_validation_record,
    persist_validated_r4_result,
)


class R4ValidationError(RuntimeError):
    """Raised when R4 result validation cannot safely be completed."""


@dataclass(frozen=True)
class R4ValidationOutcome:
    validation_record: R4ValidationRecord
    validation_record_artifact: ArtifactReference
    validated_result: ValidatedR4DecompositionResult | None
    validated_result_artifact: ArtifactReference | None


def validate_r4_decomposition(
    *,
    executed_result_artifact: ArtifactReference,
    execution_record: R4ExecutionRecord,
    execution_record_artifact: ArtifactReference,
    canonical_dataset: CanonicalDatasetReference,
    baseline_population: PopulationDefinition,
    comparison_population: PopulationDefinition,
    baseline_revenue_authority: ValidatedResult,
    comparison_revenue_authority: ValidatedResult,
    revenue_change_authority: ValidatedResult,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> R4ValidationOutcome:
    started_at = utc_now()
    result = load_r4_executed_result(executed_result_artifact, artifact_store, metadata_store)
    trace = load_r4_trace(result.product_trace_ref, artifact_store, metadata_store)
    checks: list[R4ValidationCheck] = []

    _check(checks, "execution_record_binding", execution_record.execution_id == result.execution_id and execution_record.result_ref == result.result_id)
    _check(checks, "authority_binding", result.authority == execution_record.authority == trace.authority)
    _check(
        checks,
        "method_version_binding",
        result.authority.method_id == "product_level_revenue_decomposition"
        and result.authority.method_version == "R4 v1.0",
    )
    _check(
        checks,
        "period_binding",
        result.authority.baseline_period_ref == baseline_population.period.period_id
        and result.authority.comparison_period_ref == comparison_population.period.period_id,
    )
    _check(
        checks,
        "population_binding",
        result.authority.baseline_population_ref == baseline_population.population_id
        and result.authority.baseline_population_fingerprint == baseline_population.population_fingerprint
        and result.authority.comparison_population_ref == comparison_population.population_id
        and result.authority.comparison_population_fingerprint == comparison_population.population_fingerprint,
    )
    _check(
        checks,
        "scope_binding",
        baseline_population.scope == comparison_population.scope
        and result.authority.scope_ref == baseline_population.scope.scope_id,
    )
    _check(
        checks,
        "currency_binding",
        result.authority.currency
        == baseline_revenue_authority.currency
        == comparison_revenue_authority.currency
        == revenue_change_authority.currency,
    )
    _check(
        checks,
        "canonical_dataset_binding",
        result.authority.canonical_dataset_ref == canonical_dataset.canonical_dataset_id
        and result.authority.canonical_dataset_fingerprint == canonical_dataset.content_fingerprint,
    )
    _check(
        checks,
        "baseline_revenue_authority",
        result.baseline_revenue == baseline_revenue_authority.value,
        observed=result.baseline_revenue,
        expected=baseline_revenue_authority.value,
    )
    _check(
        checks,
        "comparison_revenue_authority",
        result.comparison_revenue == comparison_revenue_authority.value,
        observed=result.comparison_revenue,
        expected=comparison_revenue_authority.value,
    )
    _check(
        checks,
        "observed_revenue_change_authority",
        result.observed_revenue_change == revenue_change_authority.value
        and result.observed_revenue_change == result.comparison_revenue - result.baseline_revenue,
        observed=result.observed_revenue_change,
        expected=revenue_change_authority.value,
    )

    canonical_path = _verified_canonical_path(canonical_dataset, artifact_store)
    baseline = _independent_product_revenues(baseline_population, canonical_path)
    comparison = _independent_product_revenues(comparison_population, canonical_path)
    _check(
        checks,
        "baseline_product_revenue_sum",
        sum(baseline.values(), Decimal("0")) == result.baseline_revenue,
        observed=sum(baseline.values(), Decimal("0")),
        expected=result.baseline_revenue,
    )
    _check(
        checks,
        "comparison_product_revenue_sum",
        sum(comparison.values(), Decimal("0")) == result.comparison_revenue,
        observed=sum(comparison.values(), Decimal("0")),
        expected=result.comparison_revenue,
    )
    expected_ids = tuple(sorted(set(baseline) | set(comparison)))
    trace_ids = tuple(row.product_id for row in trace.rows)
    _check(checks, "complete_product_universe", trace_ids == expected_ids, observed=trace_ids, expected=expected_ids)
    trace_by_id = {row.product_id: row for row in trace.rows}
    partition_valid = True
    value_valid = True
    contribution_valid = True
    context_valid = True
    for product_id in expected_ids:
        row = trace_by_id.get(product_id)
        if row is None:
            partition_valid = value_valid = contribution_valid = context_valid = False
            continue
        baseline_present = product_id in baseline
        comparison_present = product_id in comparison
        expected_classification, expected_component = _expected_classification(baseline_present, comparison_present)
        partition_valid &= (
            row.baseline_present == baseline_present
            and row.comparison_present == comparison_present
            and row.classification is expected_classification
            and row.assigned_component is expected_component
        )
        baseline_value = baseline.get(product_id, Decimal("0"))
        comparison_value = comparison.get(product_id, Decimal("0"))
        value_valid &= row.baseline_revenue == baseline_value and row.comparison_revenue == comparison_value
        contribution_valid &= row.contribution == comparison_value - baseline_value
        context_valid &= (
            row.currency == result.authority.currency
            and row.baseline_period_ref == result.authority.baseline_period_ref
            and row.comparison_period_ref == result.authority.comparison_period_ref
            and row.baseline_population_ref == result.authority.baseline_population_ref
            and row.comparison_population_ref == result.authority.comparison_population_ref
            and row.scope_ref == result.authority.scope_ref
            and row.canonical_dataset_ref == result.authority.canonical_dataset_ref
            and row.canonical_dataset_fingerprint == result.authority.canonical_dataset_fingerprint
            and row.method_id == result.authority.method_id
            and row.method_version == result.authority.method_version
            and row.execution_id == result.execution_id
            and row.precision_policy_ref == result.authority.precision_policy_ref
            and row.precision_policy_version == result.authority.precision_policy_version
            and row.validation_policy_id == result.authority.validation_policy_id
            and row.validation_policy_version == result.authority.validation_policy_version
        )
    _check(checks, "exclusive_exhaustive_partition", partition_valid)
    _check(checks, "product_level_value_integrity", value_valid)
    _check(checks, "per_product_contribution_arithmetic", contribution_valid)
    _check(checks, "trace_context_completeness", context_valid and trace.row_count == len(expected_ids))

    expected_entry = sum(
        (row.contribution for row in trace.rows if row.classification is R4ProductClassification.COMPARISON_ONLY),
        Decimal("0"),
    )
    expected_exit = sum(
        (row.contribution for row in trace.rows if row.classification is R4ProductClassification.BASELINE_ONLY),
        Decimal("0"),
    )
    expected_continuing = sum(
        (row.contribution for row in trace.rows if row.classification is R4ProductClassification.CONTINUING),
        Decimal("0"),
    )
    _check(checks, "entry_component_aggregation", result.entry_component == expected_entry, observed=result.entry_component, expected=expected_entry)
    _check(checks, "exit_component_aggregation", result.exit_component == expected_exit, observed=result.exit_component, expected=expected_exit)
    _check(
        checks,
        "continuing_component_aggregation",
        result.continuing_component == expected_continuing,
        observed=result.continuing_component,
        expected=expected_continuing,
    )
    expected_component_sum = expected_entry + expected_exit + expected_continuing
    _check(checks, "component_sum", result.component_sum == expected_component_sum, observed=result.component_sum, expected=expected_component_sum)
    _check(
        checks,
        "all_product_contributions_sum",
        result.component_sum == sum((row.contribution for row in trace.rows), Decimal("0")),
    )
    _check(
        checks,
        "observed_change_reconciliation",
        result.component_sum == result.observed_revenue_change,
        observed=result.component_sum,
        expected=result.observed_revenue_change,
    )
    _check(
        checks,
        "exact_zero_reconciliation",
        result.reconciliation_difference == Decimal("0")
        and result.observed_revenue_change - result.component_sum == Decimal("0"),
        observed=result.reconciliation_difference,
        expected=Decimal("0"),
    )
    _check(
        checks,
        "trace_fingerprint_integrity",
        trace.trace_fingerprint == _independent_trace_fingerprint(trace),
    )
    _check(
        checks,
        "result_fingerprint_integrity",
        result.result_fingerprint == _independent_result_fingerprint(result),
    )
    _check(
        checks,
        "exact_decimal_no_presentation_repair",
        all(
            isinstance(value, Decimal) and value.is_finite()
            for value in (
                result.baseline_revenue,
                result.comparison_revenue,
                result.observed_revenue_change,
                result.entry_component,
                result.exit_component,
                result.continuing_component,
                result.component_sum,
                result.reconciliation_difference,
            )
        )
        and result.authority.precision_policy_ref == PRECISION_POLICY_REF
        and result.authority.precision_policy_version == PRECISION_POLICY_VERSION,
    )
    ended_at = utc_now()
    status = R4ValidationStatus.PASSED if all(check.passed for check in checks) else R4ValidationStatus.FAILED
    validation_fingerprint = canonical_json_fingerprint(
        {
            "validator_id": "commerce_lens_r4_independent_validator",
            "validator_version": result.authority.validation_policy_version,
            "target_result_ref": result.result_id,
            "target_result_fingerprint": result.result_fingerprint,
            "product_trace_fingerprint": result.product_trace_fingerprint,
            "authority": result.authority.model_dump(mode="json"),
            "checks": [check.model_dump(mode="json") for check in checks],
            "status": status.value,
        }
    )
    record = R4ValidationRecord(
        execution_id=result.execution_id,
        target_result_ref=result.result_id,
        target_result_fingerprint=result.result_fingerprint,
        product_trace_ref=result.product_trace_ref,
        product_trace_fingerprint=result.product_trace_fingerprint,
        execution_record_ref=execution_record_artifact,
        source_result_ref=executed_result_artifact,
        authority=result.authority,
        checks=tuple(checks),
        status=status,
        started_at=started_at,
        ended_at=ended_at,
        validation_fingerprint=validation_fingerprint,
    )
    record_artifact = persist_r4_validation_record(record, artifact_store, metadata_store)
    if status is R4ValidationStatus.FAILED:
        return R4ValidationOutcome(record, record_artifact, None, None)
    validated = ValidatedR4DecompositionResult(
        execution_id=result.execution_id,
        executed_result_id=result.result_id,
        validation_record_id=record.validation_id,
        authority=result.authority,
        source_result_artifact_ref=executed_result_artifact,
        execution_record_artifact_ref=execution_record_artifact,
        validation_record_artifact_ref=record_artifact,
        product_trace_ref=result.product_trace_ref,
        result_fingerprint=result.result_fingerprint,
        validation_fingerprint=record.validation_fingerprint,
        product_trace_fingerprint=result.product_trace_fingerprint,
        baseline_revenue=result.baseline_revenue,
        comparison_revenue=result.comparison_revenue,
        observed_revenue_change=result.observed_revenue_change,
        entry_component=result.entry_component,
        exit_component=result.exit_component,
        continuing_component=result.continuing_component,
        component_sum=result.component_sum,
        reconciliation_difference=result.reconciliation_difference,
        product_count=result.product_count,
        entry_product_count=result.entry_product_count,
        exit_product_count=result.exit_product_count,
        continuing_product_count=result.continuing_product_count,
    )
    validated_artifact = persist_validated_r4_result(validated, artifact_store, metadata_store)
    return R4ValidationOutcome(record, record_artifact, validated, validated_artifact)


def _check(
    checks: list[R4ValidationCheck],
    check_id: str,
    passed: bool,
    *,
    observed: Any = None,
    expected: Any = None,
) -> None:
    checks.append(
        R4ValidationCheck(
            check_id=check_id,
            passed=bool(passed),
            observed=_json_value(observed),
            expected=_json_value(expected),
            failure_code=None if passed else f"r4_validation_{check_id}_failed",
            failure_reason=None if passed else f"R4 required validation failed: {check_id}",
        )
    )


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    return value


def _verified_canonical_path(canonical_dataset: CanonicalDatasetReference, artifact_store: ArtifactStore) -> Path:
    path = artifact_store.safe_path(canonical_dataset.artifact.path)
    if not path.is_file() or canonical_dataset.artifact.fingerprint is None:
        raise R4ValidationError("canonical authority artifact is missing")
    fingerprint = sha256_file(path)
    if fingerprint != canonical_dataset.artifact.fingerprint or fingerprint != canonical_dataset.content_fingerprint:
        raise R4ValidationError("canonical authority artifact integrity failure")
    return path


def _independent_product_revenues(population: PopulationDefinition, canonical_path: Path) -> dict[str, Decimal]:
    clauses = ["eligibility_status = ?", "order_date BETWEEN ? AND ?"]
    params: list[Any] = [
        str(canonical_path),
        EligibilityState.ELIGIBLE.value,
        population.period.start_date,
        population.period.end_date,
    ]
    for item in population.scope.filters:
        if item.field not in SUPPORTED_SCOPE_FILTER_FIELDS or item.operator != "equals":
            raise R4ValidationError("validator encountered unsupported scope authority")
        clauses.append(f'"{item.field}" = ?')
        params.append(item.value)
    sql = (
        "SELECT product_id, SUM(line_revenue) AS revenue "
        f"FROM read_parquet(?) WHERE {' AND '.join(clauses)} GROUP BY product_id ORDER BY product_id"
    )
    rows = duckdb.connect(":memory:").execute(sql, tuple(params)).fetchall()
    result: dict[str, Decimal] = {}
    for product_id, revenue in rows:
        if not isinstance(product_id, str) or not product_id.strip() or product_id in result:
            raise R4ValidationError("validator found invalid product identity")
        if not isinstance(revenue, Decimal) or not revenue.is_finite():
            raise R4ValidationError("validator found invalid Product Revenue")
        result[product_id] = revenue
    return result


def _expected_classification(baseline_present: bool, comparison_present: bool):
    if baseline_present and comparison_present:
        return R4ProductClassification.CONTINUING, R4Component.CONTINUING
    if comparison_present:
        return R4ProductClassification.COMPARISON_ONLY, R4Component.ENTRY
    return R4ProductClassification.BASELINE_ONLY, R4Component.EXIT


def _independent_trace_fingerprint(trace: R4ProductTrace) -> str:
    return canonical_json_fingerprint(
        {
            "authority": trace.authority.model_dump(mode="json"),
            "rows": [
                {key: value for key, value in row.model_dump(mode="json").items() if key != "execution_id"}
                for row in trace.rows
            ],
        }
    )


def _independent_result_fingerprint(result: ExecutedR4DecompositionResult) -> str:
    return canonical_json_fingerprint(
        {
            "authority": result.authority.model_dump(mode="json"),
            "baseline_revenue": str(result.baseline_revenue),
            "comparison_revenue": str(result.comparison_revenue),
            "observed_revenue_change": str(result.observed_revenue_change),
            "entry_component": str(result.entry_component),
            "exit_component": str(result.exit_component),
            "continuing_component": str(result.continuing_component),
            "component_sum": str(result.component_sum),
            "reconciliation_difference": str(result.reconciliation_difference),
            "product_trace_fingerprint": result.product_trace_fingerprint,
            "product_count": result.product_count,
            "entry_product_count": result.entry_product_count,
            "exit_product_count": result.exit_product_count,
            "continuing_product_count": result.continuing_product_count,
        }
    )
