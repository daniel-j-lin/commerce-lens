"""P4-001 deterministic reference execution for approved scalar Metrics."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
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
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, sha256_file, stable_content_id
from commerce_lens.persistence.artifact_store import ArtifactStore


REFERENCE_EXECUTOR_ID = "commerce_lens_duckdb_reference_executor"
REFERENCE_EXECUTOR_VERSION = "p4_001_v1"
APPROVED_EXECUTABLE_METRICS = frozenset({"revenue", "orders", "aov"})
_CANONICAL_TABLE = "canonical_lines"
_SUPPORTED_FILTER_OPERATORS = frozenset({"equals"})


class MetricExecutionError(ValueError):
    """Raised when P4 execution cannot safely proceed."""


@dataclass(frozen=True)
class PlanExecutionOutcome:
    execution_records: tuple[ExecutionRecord, ...]
    executed_results: tuple[ExecutedResult, ...]


def execute_plan(
    plan: ExecutionPlan,
    canonical_dataset: CanonicalDatasetReference,
    artifact_store: ArtifactStore,
) -> PlanExecutionOutcome:
    """Execute authorized P4-001 Revenue, Orders, and AOV plan nodes.

    The function consumes the P3 ExecutionPlan as authority. Blocked nodes are
    skipped without records or results; malformed plans fail before DuckDB runs.
    """
    validate_execution_plan_pre_execution(plan)
    _validate_canonical_dataset_linkage(plan, canonical_dataset)
    canonical_path = _verified_canonical_artifact_path(canonical_dataset, artifact_store)
    duckdb_version = _duckdb_version()

    population_by_id = {population.population_id: population for population in plan.population_definitions}
    result_by_node_id: dict[str, ExecutedResult] = {}
    records: list[ExecutionRecord] = []
    results: list[ExecutedResult] = []

    for node in plan.ordered_metrics:
        if node.planning_state == "blocked":
            continue
        if node.metric_ref not in APPROVED_EXECUTABLE_METRICS:
            record = _failed_record(
                plan,
                node,
                population_by_id,
                canonical_dataset,
                duckdb_version,
                _unsupported_metric_failure(node),
                operation={"method": "fail_closed", "reason": "unsupported_metric"},
            )
            records.append(record)
            continue
        try:
            population = _single_total_population(node, population_by_id)
            if node.metric_ref == "revenue":
                record, result = _execute_revenue(
                    plan,
                    node,
                    population,
                    canonical_dataset,
                    canonical_path,
                    duckdb_version,
                )
            elif node.metric_ref == "orders":
                record, result = _execute_orders(
                    plan,
                    node,
                    population,
                    canonical_dataset,
                    canonical_path,
                    duckdb_version,
                )
            else:
                record, result = _execute_aov(
                    plan,
                    node,
                    population,
                    canonical_dataset,
                    duckdb_version,
                    result_by_node_id,
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
            )
            records.append(record)
            continue
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


def _execute_revenue(
    plan: ExecutionPlan,
    node: PlanMetricNode,
    population: PopulationDefinition,
    canonical_dataset: CanonicalDatasetReference,
    canonical_path: Path,
    duckdb_version: str,
) -> tuple[ExecutionRecord, ExecutedResult]:
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
) -> tuple[ExecutionRecord, ExecutedResult]:
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
    duckdb_version: str,
    result_by_node_id: dict[str, ExecutedResult],
) -> tuple[ExecutionRecord, ExecutedResult]:
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
            value=None,
            metric_state=MetricState.UNDEFINED,
            undefined_reason="orders_equals_zero",
            precision="exact_decimal",
            unit="money_per_order",
        )
    return _completed_record_and_result(
        plan,
        node,
        population,
        canonical_dataset,
        duckdb_version,
        operation,
        value=revenue.value / Decimal(orders.value),
        metric_state=MetricState.VALID,
        precision="exact_decimal",
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


def _completed_record_and_result(
    plan: ExecutionPlan,
    node: PlanMetricNode,
    population: PopulationDefinition,
    canonical_dataset: CanonicalDatasetReference,
    duckdb_version: str,
    operation: dict[str, Any],
    *,
    value: Decimal | int | None,
    metric_state: MetricState,
    precision: str,
    unit: str,
    undefined_reason: str | None = None,
) -> tuple[ExecutionRecord, ExecutedResult]:
    execution_id = _execution_id(plan, node, population, canonical_dataset, duckdb_version, operation, "completed")
    result_id = _result_id(node, population, canonical_dataset, value, metric_state, undefined_reason)
    result = ExecutedResult(
        result_id=result_id,
        execution_id=execution_id,
        metric_ref=node.metric_ref,
        scope_ref=population.population_id,
        period_ref=population.period.period_id,
        value=value,
        metric_state=metric_state,
        undefined_reason=undefined_reason,
        precision=precision,
        unit=unit,
        currency=_result_currency(population),
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
        result_ref=result.result_id,
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
    result_ref: str | None = None,
    failure_details: tuple[FailureDetail, ...] = (),
) -> ExecutionRecord:
    execution_id = _execution_id(
        plan,
        node,
        populations[0] if populations else None,
        canonical_dataset,
        duckdb_version,
        operation,
        status.value,
        failure_details=failure_details,
    )
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
        period_refs=tuple(dict.fromkeys(population.period.period_id for population in populations)),
        period_role=populations[0].period_role.value if len(populations) == 1 else None,
        population_refs=tuple(population.population_id for population in populations),
        population_fingerprints=tuple(population.population_fingerprint for population in populations),
        executor_id=REFERENCE_EXECUTOR_ID,
        executor_version=REFERENCE_EXECUTOR_VERSION,
        duckdb_version=duckdb_version,
        operation=operation,
        ended_at=utc_now(),
        result_ref=result_ref,
        status=status,
        failure_details=failure_details,
    )


def _execution_id(
    plan: ExecutionPlan,
    node: PlanMetricNode,
    population: PopulationDefinition | None,
    canonical_dataset: CanonicalDatasetReference,
    duckdb_version: str,
    operation: dict[str, Any],
    status: str,
    *,
    failure_details: tuple[FailureDetail, ...] = (),
) -> str:
    fingerprint = canonical_json_fingerprint(
        {
            "plan_id": plan.plan_id,
            "plan_fingerprint": plan.plan_fingerprint,
            "node_id": node.node_id,
            "metric_ref": node.metric_ref,
            "metric_version": node.metric_version,
            "canonical_dataset_ref": canonical_dataset.canonical_dataset_id,
            "canonical_dataset_fingerprint": canonical_dataset.content_fingerprint,
            "population_ref": population.population_id if population else None,
            "population_fingerprint": population.population_fingerprint if population else None,
            "executor_id": REFERENCE_EXECUTOR_ID,
            "executor_version": REFERENCE_EXECUTOR_VERSION,
            "duckdb_version": duckdb_version,
            "operation": operation,
            "status": status,
            "failure_details": [failure.model_dump(mode="json") for failure in failure_details],
        }
    )
    return stable_content_id("exec", fingerprint)


def _result_id(
    node: PlanMetricNode,
    population: PopulationDefinition,
    canonical_dataset: CanonicalDatasetReference,
    value: Decimal | int | None,
    metric_state: MetricState,
    undefined_reason: str | None,
) -> str:
    fingerprint = canonical_json_fingerprint(
        {
            "node_id": node.node_id,
            "metric_ref": node.metric_ref,
            "metric_version": node.metric_version,
            "canonical_dataset_ref": canonical_dataset.canonical_dataset_id,
            "canonical_dataset_fingerprint": canonical_dataset.content_fingerprint,
            "population_ref": population.population_id,
            "population_fingerprint": population.population_fingerprint,
            "value": str(value) if isinstance(value, Decimal) else value,
            "metric_state": metric_state.value,
            "undefined_reason": undefined_reason,
            "executor_id": REFERENCE_EXECUTOR_ID,
            "executor_version": REFERENCE_EXECUTOR_VERSION,
        }
    )
    return stable_content_id("exres", fingerprint)


def _unsupported_metric_failure(node: PlanMetricNode) -> FailureDetail:
    return FailureDetail(
        stage=FailureStage.EXECUTION,
        reason=f"unsupported P4-001 Metric execution: {node.metric_ref}",
        target_ref=node.node_id,
        governing_ref="tasks:P4-001:15",
        dependency_scope=node.metric_ref,
        independent_chains_may_continue=True,
    )


def _json_params(params: tuple[Any, ...]) -> tuple[str | int | bool | None, ...]:
    return tuple(param.isoformat() if hasattr(param, "isoformat") else param for param in params)


def _result_currency(population: PopulationDefinition) -> str | None:
    if population.currency_basis_ref.startswith("currency:"):
        return population.currency_basis_ref.removeprefix("currency:")
    return None


def _duckdb_version() -> str:
    return str(duckdb.__version__)
