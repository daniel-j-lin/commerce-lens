"""P4-001 deterministic reference execution for approved scalar Metrics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from pathlib import Path
from typing import Any

import duckdb

from commerce_lens.canonical.models import EligibilityState
from commerce_lens.contracts.common import (
    FailureDetail,
    FailureStage,
    GroupingDimension,
    MetricState,
    ScopeFilter,
    utc_now,
)
from commerce_lens.contracts.evidence import CanonicalDatasetReference
from commerce_lens.contracts.execution import ExecutedResult, ExecutionRecord, ExecutionStatus
from commerce_lens.contracts.plans import ExecutionPlan, PlanMetricNode
from commerce_lens.contracts.populations import PopulationDefinition
from commerce_lens.engine.plan_builder import validate_execution_plan_pre_execution
from commerce_lens.engine.populations import population_fingerprint, population_id_for_fingerprint
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, generate_id, sha256_file
from commerce_lens.metrics.registry import get_metric_registry
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore


REFERENCE_EXECUTOR_ID = "commerce_lens_duckdb_reference_executor"
REFERENCE_EXECUTOR_VERSION = "p4_001_v1"
APPROVED_EXECUTABLE_METRICS = frozenset({"revenue", "orders", "aov", "revenue_change"})
AOV_DECIMAL_CALCULATION_POLICY_ID = "p4_aov_decimal_calculation_policy_v1"
AOV_DECIMAL_PRECISION = 38
AOV_DECIMAL_ROUNDING = ROUND_HALF_EVEN
REVENUE_CHANGE_DECIMAL_CALCULATION_POLICY_ID = "p7_revenue_change_decimal_calculation_policy_v1"
REVENUE_CHANGE_DECIMAL_PRECISION = 38
REVENUE_CHANGE_DECIMAL_ROUNDING = ROUND_HALF_EVEN
_CANONICAL_TABLE = "canonical_lines"
_SUPPORTED_FILTER_OPERATORS = frozenset({"equals"})
_EXPLICIT_CURRENCY_BASIS_PREFIX = "currency:"
_PHASE2_SINGLE_GOVERNED_CURRENCY_BASIS = "currency_basis:phase2_single_governed_currency"


class MetricExecutionError(ValueError):
    """Raised when P4 execution cannot safely proceed."""


@dataclass(frozen=True)
class PlanExecutionOutcome:
    execution_records: tuple[ExecutionRecord, ...]
    executed_results: tuple[ExecutedResult, ...]


@dataclass(frozen=True)
class PopulationRuntimeMetadata:
    resolved_currency: str | None
    eligible_input_row_count: int


def execute_plan(
    plan: ExecutionPlan,
    canonical_dataset: CanonicalDatasetReference,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore | None = None,
) -> PlanExecutionOutcome:
    """Execute authorized P4-001 Revenue, Orders, and AOV plan nodes.

    The function consumes the P3 ExecutionPlan as authority. Blocked nodes are
    skipped without records or results; malformed plans fail before DuckDB runs.
    """
    validate_execution_plan_pre_execution(plan)
    _validate_canonical_dataset_linkage(plan, canonical_dataset)
    canonical_path = _verified_canonical_artifact_path(canonical_dataset, artifact_store)
    active_metadata_store = _execution_metadata_store(artifact_store, metadata_store)
    duckdb_version = _duckdb_version()

    population_by_id = {population.population_id: population for population in plan.population_definitions}
    result_by_node_id: dict[str, ExecutedResult] = {}
    records: list[ExecutionRecord] = []
    results: list[ExecutedResult] = []

    for node in plan.ordered_metrics:
        if node.planning_state == "blocked":
            continue
        started_at = utc_now()
        if node.metric_ref not in APPROVED_EXECUTABLE_METRICS:
            record = _failed_record(
                plan,
                node,
                population_by_id,
                canonical_dataset,
                duckdb_version,
                _unsupported_metric_failure(node),
                operation={"method": "fail_closed", "reason": "unsupported_metric"},
                started_at=started_at,
            )
            active_metadata_store.insert_execution_record(record)
            records.append(record)
            continue
        try:
            _validate_metric_implementation_ref(node)
            if node.metric_ref == "revenue_change":
                record, result = _execute_revenue_change(
                    plan,
                    node,
                    population_by_id,
                    canonical_dataset,
                    canonical_path,
                    duckdb_version,
                    result_by_node_id,
                    active_metadata_store,
                    artifact_store,
                    started_at,
                )
            else:
                population = _single_total_population(node, population_by_id)
                _validate_population_identity(population)
                if node.metric_ref == "revenue":
                    record, result = _execute_revenue(
                        plan,
                        node,
                        population,
                        canonical_dataset,
                        canonical_path,
                        duckdb_version,
                        started_at,
                    )
                elif node.metric_ref == "orders":
                    record, result = _execute_orders(
                        plan,
                        node,
                        population,
                        canonical_dataset,
                        canonical_path,
                        duckdb_version,
                        started_at,
                    )
                else:
                    record, result = _execute_aov(
                        plan,
                        node,
                        population,
                        canonical_dataset,
                        canonical_path,
                        duckdb_version,
                        result_by_node_id,
                        started_at,
                    )
        except Exception as exc:
            failure = (
                exc
                if isinstance(exc, MetricExecutionError)
                else MetricExecutionError(f"DuckDB deterministic execution failed: {exc}")
            )
            record = _failed_record(
                plan,
                node,
                population_by_id,
                canonical_dataset,
                duckdb_version,
                FailureDetail(
                    stage=FailureStage.EXECUTION,
                    reason=str(failure),
                    target_ref=node.node_id,
                    governing_ref="tasks:P4-001:18",
                    dependency_scope=node.metric_ref,
                    independent_chains_may_continue=True,
                ),
                operation={"method": "execution_failed"},
                started_at=started_at,
            )
            active_metadata_store.insert_execution_record(record)
            records.append(record)
            continue
        result_artifact = _persist_executed_result(result, artifact_store, active_metadata_store)
        record = record.model_copy(update={"output_artifacts": (result_artifact,)})
        active_metadata_store.insert_execution_record(record)
        records.append(record)
        results.append(result)
        result_by_node_id[node.node_id] = result

    return PlanExecutionOutcome(execution_records=tuple(records), executed_results=tuple(results))


def _validate_canonical_dataset_linkage(plan: ExecutionPlan, canonical_dataset: CanonicalDatasetReference) -> None:
    if not plan.population_definitions:
        raise MetricExecutionError("ExecutionPlan must include governed PopulationDefinitions")
    canonical_ids = {population.canonical_dataset_ref_id for population in plan.population_definitions}
    if canonical_ids != {canonical_dataset.canonical_dataset_id}:
        raise MetricExecutionError("ExecutionPlan populations must reference the supplied canonical dataset")
    source_ids = {population.dataset_ref_id for population in plan.population_definitions}
    if source_ids != {canonical_dataset.source_dataset_id}:
        raise MetricExecutionError("ExecutionPlan populations must preserve canonical dataset source lineage")


def _execution_metadata_store(
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore | None,
) -> MetadataStore:
    active_store = metadata_store or MetadataStore(artifact_store.safe_path("metadata.sqlite"))
    active_store.initialize()
    return active_store


def _verified_canonical_artifact_path(
    canonical_dataset: CanonicalDatasetReference,
    artifact_store: ArtifactStore,
) -> Path:
    path = artifact_store.safe_path(canonical_dataset.artifact.path)
    if not path.is_file():
        raise MetricExecutionError("required canonical artifact is missing")
    if sha256_file(path) != canonical_dataset.content_fingerprint:
        raise MetricExecutionError("canonical artifact fingerprint does not match CanonicalDatasetReference")
    return path


def _single_total_population(
    node: PlanMetricNode,
    population_by_id: dict[str, PopulationDefinition],
) -> PopulationDefinition:
    if node.grouping is not GroupingDimension.NONE:
        raise MetricExecutionError("P4-001 executes only total-population nodes")
    if len(node.population_refs) != 1:
        raise MetricExecutionError("P4-001 executable nodes must reference exactly one governed population")
    population = population_by_id.get(node.population_refs[0])
    if population is None:
        raise MetricExecutionError("plan node references unknown governed population")
    if population.grouping is not GroupingDimension.NONE:
        raise MetricExecutionError("P4-001 populations must be total-population definitions")
    return population


def _validate_metric_implementation_ref(node: PlanMetricNode) -> None:
    definition = get_metric_registry().require(node.metric_ref)
    if node.execution_implementation_ref != definition.execution_implementation_ref:
        raise MetricExecutionError("plan Metric implementation ref does not match approved Metric Registry binding")


def _validate_population_identity(population: PopulationDefinition) -> None:
    recomputed = population_fingerprint(population)
    if recomputed != population.population_fingerprint:
        raise MetricExecutionError("governed population fingerprint does not match population semantics")
    if population_id_for_fingerprint(recomputed) != population.population_id:
        raise MetricExecutionError("governed population ID does not correspond to population fingerprint")


def _execute_revenue(
    plan: ExecutionPlan,
    node: PlanMetricNode,
    population: PopulationDefinition,
    canonical_dataset: CanonicalDatasetReference,
    canonical_path: Path,
    duckdb_version: str,
    started_at: datetime,
) -> tuple[ExecutionRecord, ExecutedResult]:
    runtime_metadata = _population_runtime_metadata(population, canonical_path, requires_currency=True)
    sql, params = _population_aggregate_sql(
        "SELECT SUM(line_revenue) AS value",
        population,
        canonical_path,
    )
    value = _fetch_one(sql, params)[0]
    if value is None:
        value = Decimal("0")
    if not isinstance(value, Decimal):
        raise MetricExecutionError("Revenue execution returned a non-Decimal authoritative value")
    operation = {"method": "duckdb_sql", "sql": sql, "parameters": _json_params(params)}
    return _completed_record_and_result(
        plan,
        node,
        population,
        canonical_dataset,
        duckdb_version,
        operation,
        started_at=started_at,
        resolved_currency=runtime_metadata.resolved_currency,
        eligible_input_row_count=runtime_metadata.eligible_input_row_count,
        value=value,
        metric_state=MetricState.VALID,
        precision="exact_decimal",
        unit="money",
    )


def _execute_orders(
    plan: ExecutionPlan,
    node: PlanMetricNode,
    population: PopulationDefinition,
    canonical_dataset: CanonicalDatasetReference,
    canonical_path: Path,
    duckdb_version: str,
    started_at: datetime,
) -> tuple[ExecutionRecord, ExecutedResult]:
    runtime_metadata = _population_runtime_metadata(population, canonical_path, requires_currency=False)
    sql, params = _population_aggregate_sql(
        "SELECT COUNT(DISTINCT order_id) AS value",
        population,
        canonical_path,
    )
    value = _fetch_one(sql, params)[0]
    if not isinstance(value, int):
        raise MetricExecutionError("Orders execution returned a non-integer authoritative value")
    operation = {"method": "duckdb_sql", "sql": sql, "parameters": _json_params(params)}
    return _completed_record_and_result(
        plan,
        node,
        population,
        canonical_dataset,
        duckdb_version,
        operation,
        started_at=started_at,
        resolved_currency=runtime_metadata.resolved_currency,
        eligible_input_row_count=runtime_metadata.eligible_input_row_count,
        value=value,
        metric_state=MetricState.VALID,
        precision="exact_integer",
        unit="orders",
    )


def _execute_aov(
    plan: ExecutionPlan,
    node: PlanMetricNode,
    population: PopulationDefinition,
    canonical_dataset: CanonicalDatasetReference,
    canonical_path: Path,
    duckdb_version: str,
    result_by_node_id: dict[str, ExecutedResult],
    started_at: datetime,
) -> tuple[ExecutionRecord, ExecutedResult]:
    runtime_metadata = _population_runtime_metadata(population, canonical_path, requires_currency=True)
    dependency_results = _aov_dependency_results(node, result_by_node_id)
    revenue = dependency_results["revenue"]
    orders = dependency_results["orders"]
    if not isinstance(revenue.value, Decimal):
        raise MetricExecutionError("AOV Revenue dependency did not return Decimal")
    if not isinstance(orders.value, int):
        raise MetricExecutionError("AOV Orders dependency did not return integer")
    operation = {
        "method": "python_decimal_dependency_arithmetic",
        "formula": "revenue / orders",
        "calculation_policy": _aov_calculation_policy_metadata(),
        "operation_representation": "Decimal(revenue.value) / Decimal(orders.value) under localcontext",
        "revenue_result_ref": revenue.result_id,
        "orders_result_ref": orders.result_id,
    }
    if orders.value == 0:
        return _completed_record_and_result(
            plan,
            node,
            population,
            canonical_dataset,
            duckdb_version,
            operation,
            started_at=started_at,
            resolved_currency=runtime_metadata.resolved_currency,
            eligible_input_row_count=runtime_metadata.eligible_input_row_count,
            value=None,
            metric_state=MetricState.UNDEFINED,
            undefined_reason="orders_equals_zero",
            precision=AOV_DECIMAL_CALCULATION_POLICY_ID,
            unit="money_per_order",
        )
    with localcontext() as context:
        context.prec = AOV_DECIMAL_PRECISION
        context.rounding = AOV_DECIMAL_ROUNDING
        aov_value = revenue.value / Decimal(orders.value)
    return _completed_record_and_result(
        plan,
        node,
        population,
        canonical_dataset,
        duckdb_version,
        operation,
        started_at=started_at,
        resolved_currency=runtime_metadata.resolved_currency,
        eligible_input_row_count=runtime_metadata.eligible_input_row_count,
        value=aov_value,
        metric_state=MetricState.VALID,
        precision=AOV_DECIMAL_CALCULATION_POLICY_ID,
        unit="money_per_order",
    )


def _aov_dependency_results(
    node: PlanMetricNode,
    result_by_node_id: dict[str, ExecutedResult],
) -> dict[str, ExecutedResult]:
    dependencies: dict[str, ExecutedResult] = {}
    for dependency_id in node.dependency_node_ids:
        result = result_by_node_id.get(dependency_id)
        if result is None:
            raise MetricExecutionError("AOV dependency result is missing or not executable")
        dependencies[result.metric_ref] = result
    if set(dependencies) != {"revenue", "orders"}:
        raise MetricExecutionError("AOV requires executed Revenue and Orders dependency results")
    if dependencies["revenue"].scope_ref != dependencies["orders"].scope_ref:
        raise MetricExecutionError("AOV dependencies must use the same governed population")
    if dependencies["revenue"].period_ref != dependencies["orders"].period_ref:
        raise MetricExecutionError("AOV dependencies must use the same governed period")
    return dependencies


def _execute_revenue_change(
    plan: ExecutionPlan,
    node: PlanMetricNode,
    population_by_id: dict[str, PopulationDefinition],
    canonical_dataset: CanonicalDatasetReference,
    canonical_path: Path,
    duckdb_version: str,
    result_by_node_id: dict[str, ExecutedResult],
    metadata_store: MetadataStore,
    artifact_store: ArtifactStore,
    started_at: datetime,
) -> tuple[ExecutionRecord, ExecutedResult]:
    baseline_population, comparison_population = _revenue_change_populations(node, population_by_id)
    runtime_metadata = _comparison_runtime_metadata(baseline_population, comparison_population, canonical_path)
    dependencies = _revenue_change_dependency_results(
        plan,
        node,
        result_by_node_id,
        population_by_id,
        metadata_store,
        artifact_store,
    )
    baseline = dependencies["baseline"]
    comparison = dependencies["comparison"]
    if not isinstance(baseline.value, Decimal) or isinstance(baseline.value, bool):
        raise MetricExecutionError("Revenue Change Baseline Revenue dependency did not return Decimal")
    if not isinstance(comparison.value, Decimal) or isinstance(comparison.value, bool):
        raise MetricExecutionError("Revenue Change Comparison Revenue dependency did not return Decimal")
    with localcontext() as context:
        context.prec = REVENUE_CHANGE_DECIMAL_PRECISION
        context.rounding = REVENUE_CHANGE_DECIMAL_ROUNDING
        value = comparison.value - baseline.value
    operation = {
        "method": "python_decimal_dependency_arithmetic",
        "formula": "comparison_revenue - baseline_revenue",
        "calculation_policy": _revenue_change_calculation_policy_metadata(),
        "operation_representation": "Decimal(comparison.value) - Decimal(baseline.value) under localcontext",
        "baseline_revenue_result_ref": baseline.result_id,
        "comparison_revenue_result_ref": comparison.result_id,
        "baseline_revenue_result_fingerprint": baseline.result_fingerprint,
        "comparison_revenue_result_fingerprint": comparison.result_fingerprint,
        "baseline_period_ref": baseline_population.period.period_id,
        "comparison_period_ref": comparison_population.period.period_id,
    }
    return _completed_comparison_record_and_result(
        plan,
        node,
        (baseline_population, comparison_population),
        canonical_dataset,
        duckdb_version,
        operation,
        started_at=started_at,
        resolved_currency=runtime_metadata.resolved_currency,
        eligible_input_row_count=runtime_metadata.eligible_input_row_count,
        value=value,
        baseline_result=baseline,
        comparison_result=comparison,
    )


def _revenue_change_populations(
    node: PlanMetricNode,
    population_by_id: dict[str, PopulationDefinition],
) -> tuple[PopulationDefinition, PopulationDefinition]:
    if node.grouping is not GroupingDimension.NONE:
        raise MetricExecutionError("Revenue Change executes only total-population nodes")
    if len(node.population_refs) != 2:
        raise MetricExecutionError("Revenue Change requires exactly Baseline and Comparison governed populations")
    populations = tuple(population_by_id.get(population_ref) for population_ref in node.population_refs)
    if any(population is None for population in populations):
        raise MetricExecutionError("Revenue Change plan node references unknown governed population")
    for population in populations:
        if population.grouping is not GroupingDimension.NONE:
            raise MetricExecutionError("Revenue Change populations must be total-population definitions")
        _validate_population_identity(population)
    by_role = {population.period_role.value: population for population in populations}
    if set(by_role) != {"baseline", "comparison"}:
        raise MetricExecutionError("Revenue Change populations must represent one Baseline and one Comparison")
    if node.period_refs != (by_role["baseline"].period.period_id, by_role["comparison"].period.period_id):
        raise MetricExecutionError("Revenue Change period refs must preserve Baseline then Comparison order")
    return by_role["baseline"], by_role["comparison"]


def _comparison_runtime_metadata(
    baseline_population: PopulationDefinition,
    comparison_population: PopulationDefinition,
    canonical_path: Path,
) -> PopulationRuntimeMetadata:
    baseline = _population_runtime_metadata(baseline_population, canonical_path, requires_currency=True)
    comparison = _population_runtime_metadata(comparison_population, canonical_path, requires_currency=True)
    if baseline.resolved_currency != comparison.resolved_currency:
        raise MetricExecutionError("Revenue Change Baseline and Comparison currency authority must match")
    return PopulationRuntimeMetadata(
        resolved_currency=baseline.resolved_currency,
        eligible_input_row_count=baseline.eligible_input_row_count + comparison.eligible_input_row_count,
    )


def _revenue_change_dependency_results(
    plan: ExecutionPlan,
    node: PlanMetricNode,
    result_by_node_id: dict[str, ExecutedResult],
    population_by_id: dict[str, PopulationDefinition],
    metadata_store: MetadataStore,
    artifact_store: ArtifactStore,
) -> dict[str, ExecutedResult]:
    if len(node.dependency_node_ids) != 2:
        raise MetricExecutionError("Revenue Change requires executed Baseline and Comparison Revenue dependency results")
    dependencies: dict[str, ExecutedResult] = {}
    for dependency_node_id in node.dependency_node_ids:
        result = result_by_node_id.get(dependency_node_id)
        if result is None:
            raise MetricExecutionError("Revenue Change dependency result is missing or not executable")
        if result.metric_ref != "revenue":
            raise MetricExecutionError("Revenue Change dependencies must be Revenue results")
        if result.metric_state is not MetricState.VALID:
            raise MetricExecutionError("Revenue Change requires valid Revenue dependency results")
        if result.result_fingerprint is None:
            raise MetricExecutionError("Revenue Change dependency result lacks semantic fingerprint")
        record = _verify_dependency_execution_record(result, metadata_store, artifact_store)
        population = population_by_id.get(result.scope_ref)
        if population is None:
            raise MetricExecutionError("Revenue Change dependency result references unknown governed population")
        if record.request_id != plan.request_id:
            raise MetricExecutionError("Revenue Change dependency ExecutionRecord request authority mismatches plan")
        if record.plan_id != plan.plan_id or record.plan_fingerprint != plan.plan_fingerprint:
            raise MetricExecutionError("Revenue Change dependency ExecutionRecord plan authority mismatches plan")
        if record.plan_node_id != dependency_node_id:
            raise MetricExecutionError("Revenue Change dependency result does not match governed dependency node")
        if result.period_ref != population.period.period_id:
            raise MetricExecutionError("Revenue Change dependency result period mismatches governed population")
        role = population.period_role.value
        if role in dependencies:
            raise MetricExecutionError("Revenue Change requires one Baseline and one Comparison Revenue dependency")
        dependencies[role] = result
    if set(dependencies) != {"baseline", "comparison"}:
        raise MetricExecutionError("Revenue Change requires one Baseline and one Comparison Revenue dependency")
    baseline = dependencies["baseline"]
    comparison = dependencies["comparison"]
    if baseline.currency != comparison.currency:
        raise MetricExecutionError("Revenue Change Revenue dependency currencies must match")
    return dependencies


def _verify_dependency_execution_record(
    result: ExecutedResult,
    metadata_store: MetadataStore,
    artifact_store: ArtifactStore,
) -> ExecutionRecord:
    record = metadata_store.get_execution_record(result.execution_id)
    if record is None:
        raise MetricExecutionError("Revenue Change dependency ExecutionRecord is missing")
    if record.status is not ExecutionStatus.COMPLETED:
        raise MetricExecutionError("Revenue Change dependency ExecutionRecord is not completed")
    if record.result_ref != result.result_id:
        raise MetricExecutionError("Revenue Change dependency ExecutionRecord result_ref mismatches result")
    if len(record.output_artifacts) != 1:
        raise MetricExecutionError("Revenue Change dependency ExecutedResult artifact is missing")
    artifact = record.output_artifacts[0]
    persisted = metadata_store.get_artifact_reference(artifact.artifact_id)
    if persisted != artifact:
        raise MetricExecutionError("Revenue Change dependency artifact metadata is missing or mismatched")
    artifact_path = artifact_store.safe_path(artifact.path)
    if not artifact_path.is_file() or artifact.fingerprint is None or sha256_file(artifact_path) != artifact.fingerprint:
        raise MetricExecutionError("Revenue Change dependency ExecutedResult artifact integrity check failed")
    restored = ExecutedResult.model_validate_json(artifact_path.read_text(encoding="utf-8"))
    if restored != result:
        raise MetricExecutionError("Revenue Change dependency result does not match persisted artifact authority")
    return record


def _population_aggregate_sql(
    select_clause: str,
    population: PopulationDefinition,
    canonical_path: Path,
) -> tuple[str, tuple[Any, ...]]:
    where_clauses = [
        "eligibility_status = ?",
        "order_date >= ?",
        "order_date <= ?",
    ]
    params: list[Any] = [
        EligibilityState.ELIGIBLE.value,
        population.period.start_date,
        population.period.end_date,
    ]
    for scope_filter in population.scope.filters:
        if scope_filter.field not in population.supported_filter_fields:
            raise MetricExecutionError("scope filter is not supported by the governed population")
        where_clauses.append(_scope_filter_sql(scope_filter))
        params.append(scope_filter.value)
    sql = (
        f"{select_clause} FROM read_parquet(?) AS {_CANONICAL_TABLE} "
        f"WHERE {' AND '.join(where_clauses)}"
    )
    return sql, (str(canonical_path), *params)


def _population_scope_period_sql(
    select_clause: str,
    population: PopulationDefinition,
    canonical_path: Path,
) -> tuple[str, tuple[Any, ...]]:
    where_clauses = [
        "order_date >= ?",
        "order_date <= ?",
    ]
    params: list[Any] = [
        population.period.start_date,
        population.period.end_date,
    ]
    for scope_filter in population.scope.filters:
        if scope_filter.field not in population.supported_filter_fields:
            raise MetricExecutionError("scope filter is not supported by the governed population")
        where_clauses.append(_scope_filter_sql(scope_filter))
        params.append(scope_filter.value)
    sql = (
        f"{select_clause} FROM read_parquet(?) AS {_CANONICAL_TABLE} "
        f"WHERE {' AND '.join(where_clauses)}"
    )
    return sql, (str(canonical_path), *params)


def _population_scope_sql(
    select_clause: str,
    population: PopulationDefinition,
    canonical_path: Path,
) -> tuple[str, tuple[Any, ...]]:
    where_clauses: list[str] = []
    params: list[Any] = []
    for scope_filter in population.scope.filters:
        if scope_filter.field not in population.supported_filter_fields:
            raise MetricExecutionError("scope filter is not supported by the governed population")
        where_clauses.append(_scope_filter_sql(scope_filter))
        params.append(scope_filter.value)
    where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    sql = f"{select_clause} FROM read_parquet(?) AS {_CANONICAL_TABLE}{where_sql}"
    return sql, (str(canonical_path), *params)


def _scope_filter_sql(scope_filter: ScopeFilter) -> str:
    if scope_filter.operator not in _SUPPORTED_FILTER_OPERATORS:
        raise MetricExecutionError("unsupported governed scope filter operator")
    return f"{_quote_identifier(scope_filter.field)} = ?"


def _quote_identifier(field_name: str) -> str:
    if not field_name.replace("_", "").isalnum():
        raise MetricExecutionError("unsupported governed scope filter field")
    return f'"{field_name}"'


def _fetch_one(sql: str, params: tuple[Any, ...]) -> tuple[Any, ...]:
    conn = duckdb.connect(database=":memory:")
    try:
        row = conn.execute(sql, params).fetchone()
    finally:
        conn.close()
    if row is None:
        raise MetricExecutionError("DuckDB execution returned no result row")
    return row


def _population_runtime_metadata(
    population: PopulationDefinition,
    canonical_path: Path,
    *,
    requires_currency: bool,
) -> PopulationRuntimeMetadata:
    eligible_sql, eligible_params = _population_aggregate_sql(
        "SELECT COUNT(*) AS eligible_input_row_count",
        population,
        canonical_path,
    )
    eligible_count = _fetch_one(eligible_sql, eligible_params)[0]
    if not isinstance(eligible_count, int):
        raise MetricExecutionError("eligible input row count returned a non-integer value")
    resolved_currency = _resolve_governed_currency(population, canonical_path) if requires_currency else None
    return PopulationRuntimeMetadata(
        resolved_currency=resolved_currency,
        eligible_input_row_count=eligible_count,
    )


def _resolve_governed_currency(population: PopulationDefinition, canonical_path: Path) -> str:
    if population.currency_basis_ref.startswith(_EXPLICIT_CURRENCY_BASIS_PREFIX):
        expected = population.currency_basis_ref.removeprefix(_EXPLICIT_CURRENCY_BASIS_PREFIX)
        if not expected:
            raise MetricExecutionError("explicit governed currency basis is empty")
        _validate_explicit_currency_period_evidence(population, canonical_path, expected)
        return expected
    if population.currency_basis_ref != _PHASE2_SINGLE_GOVERNED_CURRENCY_BASIS:
        raise MetricExecutionError("unsupported governed currency basis for P4-001 monetary execution")
    return _resolve_phase2_single_governed_currency(population, canonical_path)


def _validate_explicit_currency_period_evidence(
    population: PopulationDefinition,
    canonical_path: Path,
    expected_currency: str,
) -> None:
    sql, params = _population_scope_period_sql(
        """
        SELECT
            COUNT(*) AS row_count,
            COUNT(DISTINCT currency) AS currency_count,
            MIN(currency) AS currency
        """,
        population,
        canonical_path,
    )
    row_count, currency_count, currency = _fetch_one(sql, params)
    if row_count == 0:
        return
    if currency_count != 1 or not currency:
        raise MetricExecutionError("canonical population contradicts explicit governed currency authority")
    if currency != expected_currency:
        raise MetricExecutionError("resolved currency does not match governed currency scope filter")


def _resolve_phase2_single_governed_currency(population: PopulationDefinition, canonical_path: Path) -> str:
    sql, params = _population_scope_sql(
        """
        SELECT
            COUNT(*) AS row_count,
            COUNT(DISTINCT currency) AS currency_count,
            MIN(currency) AS currency
        """,
        population,
        canonical_path,
    )
    row_count, currency_count, currency = _fetch_one(sql, params)
    if row_count == 0:
        raise MetricExecutionError(
            "monetary Metric population has no canonical rows from which to establish phase2 single-governed currency authority"
        )
    if currency_count != 1 or not currency:
        raise MetricExecutionError("canonical population contradicts single-governed-currency authority")
    return str(currency)


def _completed_record_and_result(
    plan: ExecutionPlan,
    node: PlanMetricNode,
    population: PopulationDefinition,
    canonical_dataset: CanonicalDatasetReference,
    duckdb_version: str,
    operation: dict[str, Any],
    *,
    started_at: datetime,
    resolved_currency: str | None,
    eligible_input_row_count: int,
    value: Decimal | int | None,
    metric_state: MetricState,
    precision: str,
    unit: str,
    undefined_reason: str | None = None,
) -> tuple[ExecutionRecord, ExecutedResult]:
    execution_id = generate_id("exec")
    result_id = generate_id("exres")
    result_fingerprint = _result_fingerprint(
        node,
        population,
        canonical_dataset,
        value,
        metric_state,
        undefined_reason,
        precision,
        unit,
        resolved_currency,
    )
    result = ExecutedResult(
        result_id=result_id,
        execution_id=execution_id,
        metric_ref=node.metric_ref,
        scope_ref=population.population_id,
        period_ref=population.period.period_id,
        value=value,
        metric_state=metric_state,
        undefined_reason=undefined_reason,
        result_fingerprint=result_fingerprint,
        precision=precision,
        precision_metadata=_precision_metadata(node.metric_ref, precision),
        unit=unit,
        currency=resolved_currency if unit != "orders" else None,
        execution_status=ExecutionStatus.COMPLETED,
    )
    record = _record(
        plan,
        node,
        (population,),
        canonical_dataset,
        duckdb_version,
        operation,
        status=ExecutionStatus.COMPLETED,
        execution_id=execution_id,
        started_at=started_at,
        result_ref=result.result_id,
        resolved_currency=resolved_currency if unit != "orders" else None,
        eligible_input_row_count=eligible_input_row_count,
    )
    return record, result


def _completed_comparison_record_and_result(
    plan: ExecutionPlan,
    node: PlanMetricNode,
    populations: tuple[PopulationDefinition, PopulationDefinition],
    canonical_dataset: CanonicalDatasetReference,
    duckdb_version: str,
    operation: dict[str, Any],
    *,
    started_at: datetime,
    resolved_currency: str | None,
    eligible_input_row_count: int,
    value: Decimal,
    baseline_result: ExecutedResult,
    comparison_result: ExecutedResult,
) -> tuple[ExecutionRecord, ExecutedResult]:
    baseline_population, comparison_population = populations
    execution_id = generate_id("exec")
    result_id = generate_id("exres")
    result_fingerprint = _revenue_change_result_fingerprint(
        node=node,
        baseline_population=baseline_population,
        comparison_population=comparison_population,
        canonical_dataset=canonical_dataset,
        value=value,
        currency=resolved_currency,
        baseline_result=baseline_result,
        comparison_result=comparison_result,
    )
    result = ExecutedResult(
        result_id=result_id,
        execution_id=execution_id,
        metric_ref=node.metric_ref,
        scope_ref=comparison_population.population_id,
        period_ref=comparison_population.period.period_id,
        value=value,
        metric_state=MetricState.VALID,
        result_fingerprint=result_fingerprint,
        precision=REVENUE_CHANGE_DECIMAL_CALCULATION_POLICY_ID,
        precision_metadata=_precision_metadata(node.metric_ref, REVENUE_CHANGE_DECIMAL_CALCULATION_POLICY_ID),
        unit="money",
        currency=resolved_currency,
        execution_status=ExecutionStatus.COMPLETED,
    )
    record = _record(
        plan,
        node,
        populations,
        canonical_dataset,
        duckdb_version,
        operation,
        status=ExecutionStatus.COMPLETED,
        execution_id=execution_id,
        started_at=started_at,
        result_ref=result.result_id,
        resolved_currency=resolved_currency,
        eligible_input_row_count=eligible_input_row_count,
    )
    return record, result


def _failed_record(
    plan: ExecutionPlan,
    node: PlanMetricNode,
    population_by_id: dict[str, PopulationDefinition],
    canonical_dataset: CanonicalDatasetReference,
    duckdb_version: str,
    failure: FailureDetail,
    *,
    operation: dict[str, Any],
    started_at: datetime,
) -> ExecutionRecord:
    populations = tuple(
        population_by_id[population_ref]
        for population_ref in node.population_refs
        if population_ref in population_by_id
    )
    return _record(
        plan,
        node,
        populations,
        canonical_dataset,
        duckdb_version,
        operation,
        status=ExecutionStatus.FAILED,
        execution_id=generate_id("exec"),
        started_at=started_at,
        failure_details=(failure,),
    )


def _record(
    plan: ExecutionPlan,
    node: PlanMetricNode,
    populations: tuple[PopulationDefinition, ...],
    canonical_dataset: CanonicalDatasetReference,
    duckdb_version: str,
    operation: dict[str, Any],
    *,
    status: ExecutionStatus,
    execution_id: str,
    started_at: datetime,
    result_ref: str | None = None,
    resolved_currency: str | None = None,
    eligible_input_row_count: int | None = None,
    failure_details: tuple[FailureDetail, ...] = (),
) -> ExecutionRecord:
    return ExecutionRecord(
        execution_id=execution_id,
        request_id=plan.request_id,
        plan_id=plan.plan_id,
        plan_fingerprint=plan.plan_fingerprint,
        plan_node_id=node.node_id,
        dataset_ref_ids=tuple(dict.fromkeys(population.dataset_ref_id for population in populations)),
        canonical_dataset_ref_ids=(canonical_dataset.canonical_dataset_id,),
        canonical_dataset_fingerprints=(canonical_dataset.content_fingerprint,),
        engine_version=REFERENCE_EXECUTOR_VERSION,
        dependency_versions={"duckdb": duckdb_version},
        metric_refs=(node.metric_ref,),
        metric_definition_version=node.metric_version,
        metric_implementation_ref=node.execution_implementation_ref,
        period_refs=tuple(dict.fromkeys(population.period.period_id for population in populations)),
        period_role=populations[0].period_role.value if len(populations) == 1 else "baseline_and_comparison",
        periods=tuple(population.period.model_dump(mode="json") for population in populations),
        population_refs=tuple(population.population_id for population in populations),
        population_fingerprints=tuple(population.population_fingerprint for population in populations),
        scope_filters=tuple(
            scope_filter.model_dump(mode="json")
            for population in populations
            for scope_filter in population.scope.filters
        ),
        grouping=populations[0].grouping.value if len(populations) == 1 else node.grouping.value,
        resolved_currency=resolved_currency,
        eligible_input_row_count=eligible_input_row_count,
        executor_id=REFERENCE_EXECUTOR_ID,
        executor_version=REFERENCE_EXECUTOR_VERSION,
        duckdb_version=duckdb_version,
        operation=operation,
        started_at=started_at,
        ended_at=utc_now(),
        result_ref=result_ref,
        status=status,
        failure_details=failure_details,
    )


def _result_fingerprint(
    node: PlanMetricNode,
    population: PopulationDefinition,
    canonical_dataset: CanonicalDatasetReference,
    value: Decimal | int | None,
    metric_state: MetricState,
    undefined_reason: str | None,
    precision: str,
    unit: str,
    currency: str | None,
) -> str:
    return canonical_json_fingerprint(
        {
            "metric_ref": node.metric_ref,
            "metric_version": node.metric_version,
            "canonical_dataset_ref": canonical_dataset.canonical_dataset_id,
            "canonical_dataset_fingerprint": canonical_dataset.content_fingerprint,
            "population_ref": population.population_id,
            "population_fingerprint": population.population_fingerprint,
            "value": str(value) if isinstance(value, Decimal) else value,
            "metric_state": metric_state.value,
            "undefined_reason": undefined_reason,
            "precision": precision,
            "unit": unit,
            "currency": currency,
            "executor_id": REFERENCE_EXECUTOR_ID,
            "executor_version": REFERENCE_EXECUTOR_VERSION,
        }
    )


def _revenue_change_result_fingerprint(
    *,
    node: PlanMetricNode,
    baseline_population: PopulationDefinition,
    comparison_population: PopulationDefinition,
    canonical_dataset: CanonicalDatasetReference,
    value: Decimal,
    currency: str | None,
    baseline_result: ExecutedResult,
    comparison_result: ExecutedResult,
) -> str:
    return canonical_json_fingerprint(
        {
            "metric_ref": node.metric_ref,
            "metric_version": node.metric_version,
            "canonical_dataset_ref": canonical_dataset.canonical_dataset_id,
            "canonical_dataset_fingerprint": canonical_dataset.content_fingerprint,
            "baseline_population_ref": baseline_population.population_id,
            "baseline_population_fingerprint": baseline_population.population_fingerprint,
            "comparison_population_ref": comparison_population.population_id,
            "comparison_population_fingerprint": comparison_population.population_fingerprint,
            "baseline_period_ref": baseline_population.period.period_id,
            "comparison_period_ref": comparison_population.period.period_id,
            "baseline_revenue_result_fingerprint": baseline_result.result_fingerprint,
            "comparison_revenue_result_fingerprint": comparison_result.result_fingerprint,
            "value": str(value),
            "metric_state": MetricState.VALID.value,
            "undefined_reason": None,
            "precision": REVENUE_CHANGE_DECIMAL_CALCULATION_POLICY_ID,
            "precision_metadata": _revenue_change_calculation_policy_metadata(),
            "unit": "money",
            "currency": currency,
            "executor_id": REFERENCE_EXECUTOR_ID,
            "executor_version": REFERENCE_EXECUTOR_VERSION,
        }
    )


def _unsupported_metric_failure(node: PlanMetricNode) -> FailureDetail:
    return FailureDetail(
        stage=FailureStage.EXECUTION,
        reason=f"unsupported P4-001 Metric execution: {node.metric_ref}",
        target_ref=node.node_id,
        governing_ref="tasks:P4-001:15",
        dependency_scope=node.metric_ref,
        independent_chains_may_continue=True,
    )


def _json_params(params: tuple[Any, ...]) -> list[str | int | bool | None]:
    return [param.isoformat() if hasattr(param, "isoformat") else param for param in params]


def _aov_calculation_policy_metadata() -> dict[str, str | int]:
    return {
        "calculation_policy_id": AOV_DECIMAL_CALCULATION_POLICY_ID,
        "precision": AOV_DECIMAL_PRECISION,
        "rounding": str(AOV_DECIMAL_ROUNDING),
    }


def _precision_metadata(metric_ref: str, precision: str) -> dict[str, str | int]:
    if metric_ref == "aov":
        return _aov_calculation_policy_metadata()
    if metric_ref == "revenue_change":
        return _revenue_change_calculation_policy_metadata()
    return {"precision_policy": precision}


def _revenue_change_calculation_policy_metadata() -> dict[str, str | int]:
    return {
        "calculation_policy_id": REVENUE_CHANGE_DECIMAL_CALCULATION_POLICY_ID,
        "precision": REVENUE_CHANGE_DECIMAL_PRECISION,
        "rounding": str(REVENUE_CHANGE_DECIMAL_ROUNDING),
        "operation": "subtraction",
    }


def _persist_executed_result(
    result: ExecutedResult,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
):
    artifact = artifact_store.write_json_artifact(
        Path("runs") / result.execution_id / "results" / f"{result.result_id}.json",
        result.model_dump(mode="json"),
    )
    metadata_store.insert_artifact_reference(artifact)
    restored = ExecutedResult.model_validate_json(artifact_store.safe_path(artifact.path).read_text(encoding="utf-8"))
    if restored != result:
        raise MetricExecutionError("persisted ExecutedResult artifact did not round-trip")
    return artifact


def _duckdb_version() -> str:
    return str(duckdb.__version__)
