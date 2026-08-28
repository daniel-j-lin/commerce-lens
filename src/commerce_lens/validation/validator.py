"""P5-001 deterministic validation for Revenue, Orders, and AOV results."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

import duckdb

from commerce_lens.canonical.models import EligibilityState
from commerce_lens.contracts.common import ArtifactReference, FailureDetail, FailureStage, GroupingDimension, MetricState, ScopeFilter, utc_now
from commerce_lens.contracts.evidence import CanonicalDatasetReference
from commerce_lens.contracts.execution import ExecutedResult, ExecutionRecord, ExecutionStatus
from commerce_lens.contracts.plans import ExecutionPlan, PlanMetricNode
from commerce_lens.contracts.populations import PopulationDefinition
from commerce_lens.contracts.validation import ValidatedResult, ValidationRecord, ValidationStatus
from commerce_lens.engine.execution import (
    AOV_DECIMAL_CALCULATION_POLICY_ID,
    AOV_DECIMAL_PRECISION,
    AOV_DECIMAL_ROUNDING,
    _result_fingerprint,
)
from commerce_lens.engine.populations import population_fingerprint, population_id_for_fingerprint
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, generate_id, sha256_file
from commerce_lens.metrics.registry import get_metric_registry
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore


VALIDATOR_ID = "commerce_lens_p5_deterministic_validator"
VALIDATOR_VERSION = "p5_001_v1"
SUPPORTED_VALIDATION_METRICS = frozenset({"revenue", "orders", "aov"})
_CANONICAL_TABLE = "validation_canonical_lines"
_SUPPORTED_FILTER_OPERATORS = frozenset({"equals"})
_EXPLICIT_CURRENCY_BASIS_PREFIX = "currency:"
_PHASE2_SINGLE_GOVERNED_CURRENCY_BASIS = "currency_basis:phase2_single_governed_currency"


class MetricValidationError(ValueError):
    """Raised when a P5 validation check fails closed."""

    def __init__(
        self,
        failure_code: str,
        reason: str,
        *,
        checks_performed: tuple[str, ...] = (),
        operation: dict[str, Any] | None = None,
        expected_value: Decimal | int | float | bool | str | None = None,
        expected_state: MetricState | None = None,
    ) -> None:
        super().__init__(reason)
        self.failure_code = failure_code
        self.reason = reason
        self.checks_performed = checks_performed
        self.operation = operation or {"method": "fail_closed", "reason": failure_code}
        self.expected_value = expected_value
        self.expected_state = expected_state


@dataclass(frozen=True)
class ValidationOutcome:
    validation_record: ValidationRecord
    validated_result: ValidatedResult | None


@dataclass(frozen=True)
class _ValidationContext:
    execution_record: ExecutionRecord
    executed_result: ExecutedResult
    result_artifact: ArtifactReference
    node: PlanMetricNode
    population: PopulationDefinition
    canonical_dataset: CanonicalDatasetReference
    canonical_path: Path
    duckdb_version: str
    checks_performed: tuple[str, ...]


def validate_executed_result(
    *,
    execution_id: str,
    result_id: str,
    plan: ExecutionPlan,
    canonical_dataset: CanonicalDatasetReference,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    dependency_validated_results: tuple[ValidatedResult, ...] = (),
) -> ValidationOutcome:
    """Validate one persisted P4 ExecutedResult and persist the P5 outcome."""
    metadata_store.initialize()
    started_at = utc_now()
    execution_record = metadata_store.get_execution_record(execution_id)
    actual_value: Decimal | int | float | bool | str | None = None
    actual_state: MetricState | None = None
    metric_ref: str | None = None
    lineage: dict[str, Any] = {}
    try:
        if execution_record is None:
            raise MetricValidationError("missing_execution_record", "ExecutionRecord does not exist")
        context = _load_and_validate_context(
            execution_record,
            result_id,
            plan,
            canonical_dataset,
            artifact_store,
            metadata_store,
        )
        actual_value = context.executed_result.value
        actual_state = context.executed_result.metric_state
        metric_ref = context.executed_result.metric_ref
        lineage = _lineage_payload(context)
        expected_value, expected_state, operation, checks = _validate_metric_value(
            context,
            dependency_validated_results,
        )
        validation_fingerprint = _validation_fingerprint(
            context,
            expected_value=expected_value,
            expected_state=expected_state,
            status=ValidationStatus.PASSED,
            failure_code=None,
        )
        validated_result = _validated_result(
            context,
            validation_id="",
            validation_fingerprint=validation_fingerprint,
        )
        validation_id = generate_id("val")
        validated_result = validated_result.model_copy(
            update={
                "validation_record_id": validation_id,
                "required_validation_record_ids": (validation_id,),
            }
        )
        artifact = _persist_validated_result(validated_result, artifact_store, metadata_store)
        ended_at = utc_now()
        record = ValidationRecord(
            validation_id=validation_id,
            execution_id=context.execution_record.execution_id,
            target_result_ref=context.executed_result.result_id,
            validation_rule_id=_validation_rule_id(context.executed_result.metric_ref),
            validation_version=VALIDATOR_VERSION,
            result_fingerprint=context.executed_result.result_fingerprint,
            validator_id=VALIDATOR_ID,
            validator_version=VALIDATOR_VERSION,
            validation_operation=operation,
            checks_performed=checks,
            expected_value=expected_value,
            expected_state=expected_state,
            actual_value=context.executed_result.value,
            actual_state=context.executed_result.metric_state,
            status=ValidationStatus.PASSED,
            observed=context.executed_result.model_dump(mode="json"),
            expected_constraint="all P5-001 deterministic validation checks pass",
            authoritative_precision=context.executed_result.precision,
            metric_ref=context.executed_result.metric_ref,
            started_at=started_at,
            ended_at=ended_at,
            validated_at=ended_at,
            validated_result_ref=validated_result.validated_result_id,
            validated_result_artifact_ref=artifact,
            validation_fingerprint=validation_fingerprint,
            **lineage,
        )
        metadata_store.insert_validation_record(record)
        return ValidationOutcome(validation_record=record, validated_result=validated_result)
    except MetricValidationError as exc:
        ended_at = utc_now()
        record = ValidationRecord(
            validation_id=generate_id("val"),
            execution_id=execution_id,
            target_result_ref=result_id,
            validation_rule_id=_validation_rule_id(metric_ref),
            validation_version=VALIDATOR_VERSION,
            validator_id=VALIDATOR_ID,
            validator_version=VALIDATOR_VERSION,
            validation_operation=exc.operation,
            checks_performed=exc.checks_performed,
            expected_value=exc.expected_value,
            expected_state=exc.expected_state,
            actual_value=actual_value,
            actual_state=actual_state,
            status=ValidationStatus.FAILED,
            expected_constraint="all P5-001 deterministic validation checks pass",
            authoritative_precision=None,
            failure_code=exc.failure_code,
            failure_reason=exc.reason,
            metric_ref=metric_ref,
            started_at=started_at,
            ended_at=ended_at,
            validated_at=ended_at,
            failure_details=(
                FailureDetail(
                    stage=FailureStage.VALIDATION,
                    reason=exc.reason,
                    target_ref=result_id,
                    governing_ref="tasks:P5-001",
                    dependency_scope=metric_ref,
                    independent_chains_may_continue=True,
                ),
            ),
            **lineage,
        )
        metadata_store.insert_validation_record(record)
        return ValidationOutcome(validation_record=record, validated_result=None)


def _load_and_validate_context(
    execution_record: ExecutionRecord,
    result_id: str,
    plan: ExecutionPlan,
    canonical_dataset: CanonicalDatasetReference,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> _ValidationContext:
    checks: list[str] = []
    if execution_record.status is not ExecutionStatus.COMPLETED:
        raise MetricValidationError("execution_not_completed", "ExecutionRecord is not completed")
    checks.append("execution_record_completed")
    if execution_record.result_ref != result_id:
        raise MetricValidationError("execution_result_linkage_mismatch", "ExecutionRecord result_ref does not match target result")
    if len(execution_record.output_artifacts) != 1:
        raise MetricValidationError("result_artifact_missing", "ExecutionRecord must reference exactly one ExecutedResult artifact")
    result_artifact = execution_record.output_artifacts[0]
    persisted_artifact = metadata_store.get_artifact_reference(result_artifact.artifact_id)
    if persisted_artifact != result_artifact:
        raise MetricValidationError("result_artifact_metadata_mismatch", "result artifact reference does not match persisted metadata")
    artifact_path = artifact_store.safe_path(result_artifact.path)
    if not artifact_path.is_file():
        raise MetricValidationError("result_artifact_missing", "persisted ExecutedResult artifact is missing")
    if result_artifact.fingerprint is None or sha256_file(artifact_path) != result_artifact.fingerprint:
        raise MetricValidationError("result_artifact_hash_mismatch", "persisted ExecutedResult artifact hash does not match metadata")
    try:
        executed_result = ExecutedResult.model_validate_json(artifact_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise MetricValidationError("result_artifact_schema_invalid", f"persisted ExecutedResult artifact is schema-invalid: {exc}") from exc
    checks.extend(("result_artifact_metadata_matches", "result_artifact_hash_matches", "executed_result_schema_valid"))
    _validate_execution_result_linkage(execution_record, executed_result, result_id)
    checks.append("execution_result_linkage_matches")
    node = _plan_node(plan, execution_record.plan_node_id)
    population = _population(plan, executed_result.scope_ref)
    _validate_registry_authority(node, execution_record, executed_result)
    checks.append("metric_registry_authority_matches")
    _validate_plan_linkage(plan, node, execution_record, executed_result)
    checks.append("plan_node_linkage_matches")
    _validate_population_identity(population, execution_record, executed_result)
    checks.append("population_identity_matches")
    canonical_path = _verified_canonical_artifact_path(canonical_dataset, artifact_store)
    _validate_canonical_dataset_linkage(canonical_dataset, execution_record, population)
    checks.append("canonical_dataset_identity_matches")
    _validate_result_fingerprint(node, population, canonical_dataset, execution_record, executed_result)
    checks.append("result_fingerprint_matches")
    return _ValidationContext(
        execution_record=execution_record,
        executed_result=executed_result,
        result_artifact=result_artifact,
        node=node,
        population=population,
        canonical_dataset=canonical_dataset,
        canonical_path=canonical_path,
        duckdb_version=str(duckdb.__version__),
        checks_performed=tuple(checks),
    )


def _validate_execution_result_linkage(
    execution_record: ExecutionRecord,
    executed_result: ExecutedResult,
    result_id: str,
) -> None:
    if executed_result.result_id != result_id:
        raise MetricValidationError("result_id_mismatch", "ExecutedResult result_id does not match requested result_id")
    if executed_result.execution_id != execution_record.execution_id:
        raise MetricValidationError("execution_result_linkage_mismatch", "ExecutedResult execution_id does not match ExecutionRecord")
    if executed_result.execution_status is not ExecutionStatus.COMPLETED:
        raise MetricValidationError("executed_result_not_completed", "ExecutedResult execution_status is not completed")
    if execution_record.metric_refs != (executed_result.metric_ref,):
        raise MetricValidationError("metric_ref_mismatch", "ExecutionRecord Metric ref does not match ExecutedResult")


def _plan_node(plan: ExecutionPlan, node_id: str | None) -> PlanMetricNode:
    if node_id is None:
        raise MetricValidationError("plan_node_missing", "ExecutionRecord has no plan node identity")
    node = next((candidate for candidate in plan.ordered_metrics if candidate.node_id == node_id), None)
    if node is None:
        raise MetricValidationError("plan_node_missing", "ExecutionRecord plan node does not exist in supplied ExecutionPlan")
    return node


def _population(plan: ExecutionPlan, population_id: str) -> PopulationDefinition:
    population = next((candidate for candidate in plan.population_definitions if candidate.population_id == population_id), None)
    if population is None:
        raise MetricValidationError("population_missing", "ExecutedResult population does not exist in supplied ExecutionPlan")
    return population


def _validate_registry_authority(
    node: PlanMetricNode,
    execution_record: ExecutionRecord,
    executed_result: ExecutedResult,
) -> None:
    if executed_result.metric_ref not in SUPPORTED_VALIDATION_METRICS:
        raise MetricValidationError("unsupported_metric", f"unsupported P5-001 Metric validation: {executed_result.metric_ref}")
    definition = get_metric_registry().require(executed_result.metric_ref)
    if node.metric_ref != definition.metric_id:
        raise MetricValidationError("metric_ref_mismatch", "plan node Metric does not match Metric Registry authority")
    if node.metric_version != definition.definition_version:
        raise MetricValidationError("metric_definition_version_mismatch", "plan node Metric definition version does not match Registry")
    if execution_record.metric_definition_version != definition.definition_version:
        raise MetricValidationError("metric_definition_version_mismatch", "ExecutionRecord Metric definition version does not match Registry")
    if execution_record.metric_implementation_ref != definition.execution_implementation_ref:
        raise MetricValidationError("implementation_ref_mismatch", "ExecutionRecord implementation ref does not match Registry")
    if node.execution_implementation_ref != definition.execution_implementation_ref:
        raise MetricValidationError("implementation_ref_mismatch", "plan node implementation ref does not match Registry")
    expected_dependencies = tuple(dependency.metric_id for dependency in definition.dependencies)
    if tuple(node.dependency_metric_refs) != expected_dependencies:
        raise MetricValidationError("metric_dependency_mismatch", "plan node dependency Metric refs do not match Registry")
    if executed_result.metric_ref in {"revenue", "orders"} and node.dependency_node_ids:
        raise MetricValidationError("metric_dependency_mismatch", "base Metric validation expected no dependency nodes")
    if executed_result.metric_ref == "aov" and set(expected_dependencies) != {"revenue", "orders"}:
        raise MetricValidationError("metric_dependency_mismatch", "AOV Registry dependencies do not match Revenue and Orders")


def _validate_plan_linkage(
    plan: ExecutionPlan,
    node: PlanMetricNode,
    execution_record: ExecutionRecord,
    executed_result: ExecutedResult,
) -> None:
    if execution_record.plan_id != plan.plan_id or execution_record.plan_fingerprint != plan.plan_fingerprint:
        raise MetricValidationError("plan_identity_mismatch", "ExecutionRecord plan identity does not match supplied ExecutionPlan")
    if execution_record.plan_node_id != node.node_id:
        raise MetricValidationError("plan_node_mismatch", "ExecutionRecord plan node identity does not match")
    if node.metric_ref != executed_result.metric_ref:
        raise MetricValidationError("metric_ref_mismatch", "PlanMetricNode Metric ref does not match ExecutedResult")
    if node.population_refs != (executed_result.scope_ref,):
        raise MetricValidationError("population_mismatch", "PlanMetricNode population ref does not match ExecutedResult")


def _validate_population_identity(
    population: PopulationDefinition,
    execution_record: ExecutionRecord,
    executed_result: ExecutedResult,
) -> None:
    recomputed = population_fingerprint(population)
    if recomputed != population.population_fingerprint:
        raise MetricValidationError("population_fingerprint_mismatch", "population fingerprint does not match population semantics")
    if population_id_for_fingerprint(recomputed) != population.population_id:
        raise MetricValidationError("population_id_mismatch", "population ID does not correspond to population fingerprint")
    if execution_record.population_refs != (population.population_id,):
        raise MetricValidationError("population_mismatch", "ExecutionRecord population ref does not match governed population")
    if execution_record.population_fingerprints != (population.population_fingerprint,):
        raise MetricValidationError("population_fingerprint_mismatch", "ExecutionRecord population fingerprint does not match governed population")
    if executed_result.scope_ref != population.population_id:
        raise MetricValidationError("population_mismatch", "ExecutedResult scope_ref does not match governed population")
    if executed_result.period_ref != population.period.period_id:
        raise MetricValidationError("period_mismatch", "ExecutedResult period_ref does not match governed population")
    if execution_record.period_refs != (population.period.period_id,):
        raise MetricValidationError("period_mismatch", "ExecutionRecord period ref does not match governed population")
    if execution_record.period_role != population.period_role.value:
        raise MetricValidationError("period_mismatch", "ExecutionRecord period role does not match governed population")
    if execution_record.grouping != population.grouping.value or population.grouping is not GroupingDimension.NONE:
        raise MetricValidationError("population_grouping_mismatch", "P5-001 validates only governed total-population results")


def _verified_canonical_artifact_path(
    canonical_dataset: CanonicalDatasetReference,
    artifact_store: ArtifactStore,
) -> Path:
    path = artifact_store.safe_path(canonical_dataset.artifact.path)
    if not path.is_file():
        raise MetricValidationError("canonical_artifact_missing", "canonical dataset artifact is missing")
    if canonical_dataset.artifact.fingerprint is None:
        raise MetricValidationError("canonical_artifact_hash_mismatch", "canonical dataset artifact has no fingerprint")
    if sha256_file(path) != canonical_dataset.artifact.fingerprint:
        raise MetricValidationError("canonical_artifact_hash_mismatch", "canonical artifact hash does not match CanonicalDatasetReference")
    if canonical_dataset.content_fingerprint != canonical_dataset.artifact.fingerprint:
        raise MetricValidationError("canonical_fingerprint_mismatch", "canonical dataset fingerprint does not match artifact fingerprint")
    return path


def _validate_canonical_dataset_linkage(
    canonical_dataset: CanonicalDatasetReference,
    execution_record: ExecutionRecord,
    population: PopulationDefinition,
) -> None:
    if execution_record.canonical_dataset_ref_ids != (canonical_dataset.canonical_dataset_id,):
        raise MetricValidationError("canonical_dataset_mismatch", "ExecutionRecord canonical dataset ref does not match")
    if execution_record.canonical_dataset_fingerprints != (canonical_dataset.content_fingerprint,):
        raise MetricValidationError("canonical_fingerprint_mismatch", "ExecutionRecord canonical fingerprint does not match")
    if population.canonical_dataset_ref_id != canonical_dataset.canonical_dataset_id:
        raise MetricValidationError("canonical_dataset_mismatch", "Population canonical dataset ref does not match")
    if population.dataset_ref_id != canonical_dataset.source_dataset_id:
        raise MetricValidationError("dataset_mismatch", "Population source dataset ref does not match CanonicalDatasetReference")


def _validate_result_fingerprint(
    node: PlanMetricNode,
    population: PopulationDefinition,
    canonical_dataset: CanonicalDatasetReference,
    execution_record: ExecutionRecord,
    executed_result: ExecutedResult,
) -> None:
    expected = _result_fingerprint(
        node,
        population,
        canonical_dataset,
        executed_result.value,
        executed_result.metric_state,
        executed_result.undefined_reason,
        executed_result.precision or "",
        executed_result.unit or "",
        execution_record.resolved_currency if executed_result.unit != "orders" else None,
    )
    if executed_result.result_fingerprint != expected:
        raise MetricValidationError("result_fingerprint_mismatch", "ExecutedResult result fingerprint does not match authoritative P4 fingerprint")


def _validate_metric_value(
    context: _ValidationContext,
    dependency_validated_results: tuple[ValidatedResult, ...],
) -> tuple[Decimal | int | None, MetricState, dict[str, Any], tuple[str, ...]]:
    metric_ref = context.executed_result.metric_ref
    if metric_ref == "revenue":
        return _validate_revenue(context)
    if metric_ref == "orders":
        return _validate_orders(context)
    if metric_ref == "aov":
        return _validate_aov(context, dependency_validated_results)
    raise MetricValidationError("unsupported_metric", f"unsupported P5-001 Metric validation: {metric_ref}")


def _validate_revenue(context: _ValidationContext) -> tuple[Decimal, MetricState, dict[str, Any], tuple[str, ...]]:
    result = context.executed_result
    operation = _operation("revenue_sum", context, "SUM(line_revenue)")
    checks = (*context.checks_performed, "revenue_type_decimal", "revenue_currency_matches", "revenue_independent_sum_matches")
    if not isinstance(result.value, Decimal) or isinstance(result.value, bool):
        raise MetricValidationError("invalid_revenue_type", "Revenue value must be Decimal", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    if not result.value.is_finite():
        raise MetricValidationError("invalid_revenue_value", "Revenue value must be finite Decimal", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    expected_currency = _resolve_governed_currency(context.population, context.canonical_path)
    if result.metric_state is not MetricState.VALID:
        raise MetricValidationError("invalid_metric_state", "Revenue must use MetricState.VALID", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    if result.currency != expected_currency or context.execution_record.resolved_currency != expected_currency:
        raise MetricValidationError("currency_mismatch", "Revenue currency does not match governed currency", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    if result.precision != "exact_decimal" or result.precision_metadata != {"precision_policy": "exact_decimal"} or result.unit != "money":
        raise MetricValidationError("precision_policy_mismatch", "Revenue precision metadata does not match governed exact Decimal policy", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    sql, params = _aggregate_sql("SELECT SUM(line_revenue) AS expected_value", context.population, context.canonical_path)
    expected = _fetch_one(sql, params)[0]
    if expected is None:
        expected = Decimal("0")
    if not isinstance(expected, Decimal):
        raise MetricValidationError("validation_operation_failed", "Revenue validation query returned non-Decimal value", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    operation = _operation("revenue_sum", context, sql, params)
    if result.value != expected:
        raise MetricValidationError("value_mismatch", "Revenue value does not match independent validation sum", checks_performed=checks, operation=operation, expected_value=expected, expected_state=MetricState.VALID)
    return expected, MetricState.VALID, operation, checks


def _validate_orders(context: _ValidationContext) -> tuple[int, MetricState, dict[str, Any], tuple[str, ...]]:
    result = context.executed_result
    operation = _operation("orders_distinct_count", context, "COUNT(DISTINCT order_id)")
    checks = (*context.checks_performed, "orders_type_int_not_bool", "orders_non_negative", "orders_independent_distinct_count_matches")
    if not isinstance(result.value, int) or isinstance(result.value, bool):
        raise MetricValidationError("invalid_orders_type", "Orders value must be int and bool is not accepted", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    if result.value < 0:
        raise MetricValidationError("negative_orders", "Orders value must be non-negative", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    if result.metric_state is not MetricState.VALID:
        raise MetricValidationError("invalid_metric_state", "Orders must use MetricState.VALID", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    if result.currency is not None or result.precision != "exact_integer" or result.precision_metadata != {"precision_policy": "exact_integer"} or result.unit != "orders":
        raise MetricValidationError("precision_policy_mismatch", "Orders unit/precision metadata does not match governed integer count policy", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    sql, params = _aggregate_sql("SELECT COUNT(DISTINCT order_id) AS expected_value", context.population, context.canonical_path)
    expected = _fetch_one(sql, params)[0]
    if not isinstance(expected, int) or isinstance(expected, bool):
        raise MetricValidationError("validation_operation_failed", "Orders validation query returned non-integer value", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    operation = _operation("orders_distinct_count", context, sql, params)
    if result.value != expected:
        raise MetricValidationError("value_mismatch", "Orders value does not match independent validation distinct count", checks_performed=checks, operation=operation, expected_value=expected, expected_state=MetricState.VALID)
    return expected, MetricState.VALID, operation, checks


def _validate_aov(
    context: _ValidationContext,
    dependency_validated_results: tuple[ValidatedResult, ...],
) -> tuple[Decimal | None, MetricState, dict[str, Any], tuple[str, ...]]:
    result = context.executed_result
    operation = _operation("aov_from_validated_dependencies", context, "validated_revenue / validated_orders")
    checks = (
        *context.checks_performed,
        "aov_dependencies_validated",
        "aov_dependency_population_matches",
        "aov_dependency_period_matches",
        "aov_dependency_dataset_matches",
        "aov_currency_matches",
        "aov_calculation_policy_matches",
        "aov_value_matches_validated_dependencies",
    )
    dependencies = _aov_dependencies(context, dependency_validated_results, checks, operation)
    revenue = dependencies["revenue"]
    orders = dependencies["orders"]
    expected_currency = _resolve_governed_currency(context.population, context.canonical_path)
    if result.currency != expected_currency or context.execution_record.resolved_currency != expected_currency:
        raise MetricValidationError("currency_mismatch", "AOV currency does not match governed currency", checks_performed=checks, operation=operation)
    if result.precision != AOV_DECIMAL_CALCULATION_POLICY_ID or result.unit != "money_per_order":
        raise MetricValidationError("precision_policy_mismatch", "AOV precision/unit metadata does not match governed calculation policy", checks_performed=checks, operation=operation)
    if result.precision_metadata != _aov_calculation_policy_metadata():
        raise MetricValidationError("precision_policy_mismatch", "AOV calculation-policy metadata does not match governed policy", checks_performed=checks, operation=operation)
    if not isinstance(revenue.value, Decimal) or not isinstance(orders.value, int) or isinstance(orders.value, bool):
        raise MetricValidationError("dependency_type_mismatch", "AOV dependencies must be validated Decimal Revenue and integer Orders", checks_performed=checks, operation=operation)
    if orders.value == 0:
        if result.value is not None or result.metric_state is not MetricState.UNDEFINED or result.undefined_reason != "orders_equals_zero":
            raise MetricValidationError("aov_undefined_mismatch", "Orders=0 requires AOV Undefined with value None and orders_equals_zero", checks_performed=checks, operation=operation, expected_value=None, expected_state=MetricState.UNDEFINED)
        return None, MetricState.UNDEFINED, operation, checks
    if result.metric_state is not MetricState.VALID or result.undefined_reason is not None:
        raise MetricValidationError("invalid_metric_state", "Orders>0 requires Valid AOV with no undefined_reason", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    if not isinstance(result.value, Decimal) or isinstance(result.value, bool):
        raise MetricValidationError("invalid_aov_type", "AOV value must be Decimal when Orders > 0", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    if not result.value.is_finite():
        raise MetricValidationError("invalid_aov_value", "AOV value must be finite Decimal", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    with localcontext() as decimal_context:
        decimal_context.prec = AOV_DECIMAL_PRECISION
        decimal_context.rounding = AOV_DECIMAL_ROUNDING
        expected = revenue.value / Decimal(orders.value)
    operation = {
        **operation,
        "revenue_validated_result_ref": revenue.validated_result_id,
        "orders_validated_result_ref": orders.validated_result_id,
        "calculation_policy": _aov_calculation_policy_metadata(),
    }
    if result.value != expected:
        raise MetricValidationError("value_mismatch", "AOV value does not match validated Revenue / Orders", checks_performed=checks, operation=operation, expected_value=expected, expected_state=MetricState.VALID)
    return expected, MetricState.VALID, operation, checks


def _aov_dependencies(
    context: _ValidationContext,
    dependency_validated_results: tuple[ValidatedResult, ...],
    checks: tuple[str, ...],
    operation: dict[str, Any],
) -> dict[str, ValidatedResult]:
    dependencies = {result.metric_ref: result for result in dependency_validated_results}
    if set(dependencies) != {"revenue", "orders"}:
        raise MetricValidationError("missing_validated_dependency", "AOV validation requires successful validated Revenue and Orders dependencies", checks_performed=checks, operation=operation)
    for metric_ref in ("revenue", "orders"):
        dependency = dependencies[metric_ref]
        if dependency.metric_definition_version != get_metric_registry().require(metric_ref).definition_version:
            raise MetricValidationError("dependency_metric_version_mismatch", "AOV dependency Metric version does not match Registry", checks_performed=checks, operation=operation)
        if dependency.canonical_dataset_ref_id != context.canonical_dataset.canonical_dataset_id:
            raise MetricValidationError("dependency_dataset_mismatch", "AOV dependency canonical dataset does not match AOV result", checks_performed=checks, operation=operation)
        if dependency.canonical_dataset_fingerprint != context.canonical_dataset.content_fingerprint:
            raise MetricValidationError("dependency_dataset_mismatch", "AOV dependency canonical fingerprint does not match AOV result", checks_performed=checks, operation=operation)
        if dependency.population_ref != context.population.population_id:
            raise MetricValidationError("dependency_population_mismatch", "AOV dependency population does not match AOV result", checks_performed=checks, operation=operation)
        if dependency.population_fingerprint != context.population.population_fingerprint:
            raise MetricValidationError("dependency_population_mismatch", "AOV dependency population fingerprint does not match AOV result", checks_performed=checks, operation=operation)
        if dependency.period_ref != context.population.period.period_id:
            raise MetricValidationError("dependency_period_mismatch", "AOV dependency period does not match AOV result", checks_performed=checks, operation=operation)
        if metric_ref == "revenue" and dependency.currency != context.execution_record.resolved_currency:
            raise MetricValidationError("dependency_currency_mismatch", "AOV Revenue dependency currency does not match AOV currency", checks_performed=checks, operation=operation)
        if metric_ref == "orders" and dependency.currency is not None:
            raise MetricValidationError("dependency_currency_mismatch", "AOV Orders dependency must not carry currency", checks_performed=checks, operation=operation)
    return dependencies


def _aggregate_sql(
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
        where_clauses.append(_scope_filter_sql(scope_filter, population))
        params.append(scope_filter.value)
    sql = f"{select_clause} FROM read_parquet(?) AS {_CANONICAL_TABLE} WHERE {' AND '.join(where_clauses)}"
    return sql, (str(canonical_path), *params)


def _scope_filter_sql(scope_filter: ScopeFilter, population: PopulationDefinition) -> str:
    if scope_filter.operator not in _SUPPORTED_FILTER_OPERATORS or scope_filter.operator not in population.supported_filter_operators:
        raise MetricValidationError("unsupported_scope_filter", "unsupported governed scope filter operator")
    if scope_filter.field not in population.supported_filter_fields:
        raise MetricValidationError("unsupported_scope_filter", "scope filter is not supported by governed population")
    if not scope_filter.field.replace("_", "").isalnum():
        raise MetricValidationError("unsupported_scope_filter", "unsupported governed scope filter field")
    return f'"{scope_filter.field}" = ?'


def _fetch_one(sql: str, params: tuple[Any, ...]) -> tuple[Any, ...]:
    conn = duckdb.connect(database=":memory:")
    try:
        row = conn.execute(sql, params).fetchone()
    finally:
        conn.close()
    if row is None:
        raise MetricValidationError("validation_operation_failed", "validation query returned no result row")
    return row


def _resolve_governed_currency(population: PopulationDefinition, canonical_path: Path) -> str:
    if population.currency_basis_ref.startswith(_EXPLICIT_CURRENCY_BASIS_PREFIX):
        expected = population.currency_basis_ref.removeprefix(_EXPLICIT_CURRENCY_BASIS_PREFIX)
        if not expected:
            raise MetricValidationError("currency_mismatch", "explicit governed currency basis is empty")
        sql, params = _scope_period_sql(
            "SELECT COUNT(*) AS row_count, COUNT(DISTINCT currency) AS currency_count, MIN(currency) AS currency",
            population,
            canonical_path,
        )
        row_count, currency_count, currency = _fetch_one(sql, params)
        if row_count != 0 and (currency_count != 1 or currency != expected):
            raise MetricValidationError("currency_mismatch", "canonical population contradicts explicit governed currency authority")
        return expected
    if population.currency_basis_ref != _PHASE2_SINGLE_GOVERNED_CURRENCY_BASIS:
        raise MetricValidationError("currency_mismatch", "unsupported governed currency basis")
    sql, params = _scope_sql(
        "SELECT COUNT(*) AS row_count, COUNT(DISTINCT currency) AS currency_count, MIN(currency) AS currency",
        population,
        canonical_path,
    )
    row_count, currency_count, currency = _fetch_one(sql, params)
    if row_count == 0:
        raise MetricValidationError("currency_mismatch", "monetary validation cannot establish governed currency authority")
    if currency_count != 1 or not currency:
        raise MetricValidationError("currency_mismatch", "canonical population contradicts single-governed-currency authority")
    return str(currency)


def _scope_period_sql(
    select_clause: str,
    population: PopulationDefinition,
    canonical_path: Path,
) -> tuple[str, tuple[Any, ...]]:
    where_clauses = ["order_date >= ?", "order_date <= ?"]
    params: list[Any] = [population.period.start_date, population.period.end_date]
    for scope_filter in population.scope.filters:
        where_clauses.append(_scope_filter_sql(scope_filter, population))
        params.append(scope_filter.value)
    sql = f"{select_clause} FROM read_parquet(?) AS {_CANONICAL_TABLE} WHERE {' AND '.join(where_clauses)}"
    return sql, (str(canonical_path), *params)


def _scope_sql(
    select_clause: str,
    population: PopulationDefinition,
    canonical_path: Path,
) -> tuple[str, tuple[Any, ...]]:
    where_clauses: list[str] = []
    params: list[Any] = []
    for scope_filter in population.scope.filters:
        where_clauses.append(_scope_filter_sql(scope_filter, population))
        params.append(scope_filter.value)
    where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    sql = f"{select_clause} FROM read_parquet(?) AS {_CANONICAL_TABLE}{where_sql}"
    return sql, (str(canonical_path), *params)


def _operation(
    method: str,
    context: _ValidationContext,
    sql_or_representation: str,
    params: tuple[Any, ...] = (),
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "method": method,
        "duckdb_version": context.duckdb_version,
        "operation": sql_or_representation,
        "metric_ref": context.executed_result.metric_ref,
        "metric_definition_version": context.node.metric_version,
        "canonical_dataset_ref": context.canonical_dataset.canonical_dataset_id,
        "canonical_dataset_fingerprint": context.canonical_dataset.content_fingerprint,
        "population_ref": context.population.population_id,
        "population_fingerprint": context.population.population_fingerprint,
        "plan_id": context.execution_record.plan_id,
        "plan_node_id": context.execution_record.plan_node_id,
    }
    if params:
        payload["parameters"] = [param.isoformat() if hasattr(param, "isoformat") else param for param in params]
    return payload


def _validated_result(
    context: _ValidationContext,
    *,
    validation_id: str,
    validation_fingerprint: str,
) -> ValidatedResult:
    return ValidatedResult(
        validated_result_id=generate_id("valres"),
        validation_record_id=validation_id or "pending_validation_record_id",
        execution_id=context.execution_record.execution_id,
        executed_result_id=context.executed_result.result_id,
        required_validation_record_ids=(validation_id or "pending_validation_record_id",),
        intended_use="deterministic_metric_result_validation",
        metric_ref=context.executed_result.metric_ref,
        metric_definition_version=context.node.metric_version,
        plan_id=context.execution_record.plan_id,
        plan_node_id=context.execution_record.plan_node_id,
        canonical_dataset_ref_id=context.canonical_dataset.canonical_dataset_id,
        canonical_dataset_fingerprint=context.canonical_dataset.content_fingerprint,
        population_ref=context.population.population_id,
        population_fingerprint=context.population.population_fingerprint,
        period_ref=context.population.period.period_id,
        period_role=context.population.period_role.value,
        result_fingerprint=context.executed_result.result_fingerprint or "",
        validation_fingerprint=validation_fingerprint,
        value=context.executed_result.value,
        metric_state=context.executed_result.metric_state,
        undefined_reason=context.executed_result.undefined_reason,
        precision=context.executed_result.precision,
        precision_metadata=context.executed_result.precision_metadata,
        unit=context.executed_result.unit,
        currency=context.executed_result.currency,
        source_result_artifact_ref=context.result_artifact,
    )


def _persist_validated_result(
    result: ValidatedResult,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ArtifactReference:
    artifact = artifact_store.write_json_artifact(
        Path("runs") / result.execution_id / "validated_results" / f"{result.validated_result_id}.json",
        result.model_dump(mode="json"),
    )
    metadata_store.insert_artifact_reference(artifact)
    restored = ValidatedResult.model_validate_json(artifact_store.safe_path(artifact.path).read_text(encoding="utf-8"))
    if restored != result:
        raise MetricValidationError("validated_result_artifact_roundtrip_failed", "persisted ValidatedResult artifact did not round-trip")
    return artifact


def _validation_fingerprint(
    context: _ValidationContext,
    *,
    expected_value: Decimal | int | None,
    expected_state: MetricState,
    status: ValidationStatus,
    failure_code: str | None,
) -> str:
    return canonical_json_fingerprint(
        {
            "validator_id": VALIDATOR_ID,
            "validator_version": VALIDATOR_VERSION,
            "validation_rule_id": _validation_rule_id(context.executed_result.metric_ref),
            "status": status.value,
            "failure_code": failure_code,
            "metric_ref": context.executed_result.metric_ref,
            "metric_definition_version": context.node.metric_version,
            "result_fingerprint": context.executed_result.result_fingerprint,
            "canonical_dataset_ref": context.canonical_dataset.canonical_dataset_id,
            "canonical_dataset_fingerprint": context.canonical_dataset.content_fingerprint,
            "population_ref": context.population.population_id,
            "population_fingerprint": context.population.population_fingerprint,
            "expected_value": str(expected_value) if isinstance(expected_value, Decimal) else expected_value,
            "expected_state": expected_state.value,
            "actual_value": str(context.executed_result.value) if isinstance(context.executed_result.value, Decimal) else context.executed_result.value,
            "actual_state": context.executed_result.metric_state.value,
            "precision": context.executed_result.precision,
            "precision_metadata": context.executed_result.precision_metadata,
            "unit": context.executed_result.unit,
            "currency": context.executed_result.currency,
        }
    )


def _lineage_payload(context: _ValidationContext) -> dict[str, Any]:
    return {
        "metric_definition_version": context.node.metric_version,
        "plan_id": context.execution_record.plan_id,
        "plan_fingerprint": context.execution_record.plan_fingerprint,
        "plan_node_id": context.execution_record.plan_node_id,
        "canonical_dataset_ref_id": context.canonical_dataset.canonical_dataset_id,
        "canonical_dataset_fingerprint": context.canonical_dataset.content_fingerprint,
        "population_ref": context.population.population_id,
        "population_fingerprint": context.population.population_fingerprint,
        "period_ref": context.population.period.period_id,
        "period_role": context.population.period_role.value,
    }


def _validation_rule_id(metric_ref: str | None) -> str:
    if metric_ref == "revenue":
        return "validation:revenue_sum:p5_001"
    if metric_ref == "orders":
        return "validation:distinct_order_count:p5_001"
    if metric_ref == "aov":
        return "validation:aov_from_validated_revenue_orders:p5_001"
    return "validation:p5_001_fail_closed"


def _aov_calculation_policy_metadata() -> dict[str, str | int]:
    return {
        "calculation_policy_id": AOV_DECIMAL_CALCULATION_POLICY_ID,
        "precision": AOV_DECIMAL_PRECISION,
        "rounding": str(AOV_DECIMAL_ROUNDING),
    }
