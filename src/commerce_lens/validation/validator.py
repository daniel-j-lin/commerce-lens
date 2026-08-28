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
    REVENUE_CHANGE_DECIMAL_CALCULATION_POLICY_ID,
    REVENUE_CHANGE_DECIMAL_PRECISION,
    REVENUE_CHANGE_DECIMAL_ROUNDING,
    _result_fingerprint,
    _revenue_change_calculation_policy_metadata,
    _revenue_change_result_fingerprint,
)
from commerce_lens.engine.populations import material_scope_payload, population_fingerprint, population_id_for_fingerprint
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, generate_id, sha256_file
from commerce_lens.metrics.registry import get_metric_registry
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.validation.rules import ValidationRuleDefinition, require_p5_rule


VALIDATOR_ID = "commerce_lens_p5_deterministic_validator"
VALIDATOR_VERSION = "p5_001_v1"
SUPPORTED_VALIDATION_METRICS = frozenset({"revenue", "orders", "aov", "revenue_change"})
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
        validation_rule_id: str | None = None,
        validation_version: str | None = None,
    ) -> None:
        super().__init__(reason)
        self.failure_code = failure_code
        self.reason = reason
        self.checks_performed = checks_performed
        self.operation = operation or {"method": "fail_closed", "reason": failure_code}
        self.expected_value = expected_value
        self.expected_state = expected_state
        self.validation_rule_id = validation_rule_id
        self.validation_version = validation_version


@dataclass(frozen=True)
class ValidationOutcome:
    validation_record: ValidationRecord
    validation_records: tuple[ValidationRecord, ...]
    validated_result: ValidatedResult | None


@dataclass(frozen=True)
class _RuleEvaluation:
    rule: ValidationRuleDefinition
    operation: dict[str, Any]
    checks_performed: tuple[str, ...]
    expected_value: Decimal | int | float | bool | str | None = None
    expected_state: MetricState | None = None
    expected_constraint: str = "P5-001 required validation rule passed"


@dataclass(frozen=True)
class _ValidationContext:
    plan: ExecutionPlan
    execution_record: ExecutionRecord
    executed_result: ExecutedResult
    result_artifact: ArtifactReference
    node: PlanMetricNode
    population: PopulationDefinition
    canonical_dataset: CanonicalDatasetReference
    canonical_path: Path
    artifact_store: ArtifactStore
    metadata_store: MetadataStore
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
        evaluations = _evaluate_required_rules(
            context,
            dependency_validated_results,
        )
        validation_ids = tuple(generate_id("val") for _ in evaluations)
        rule_fingerprints = tuple(
            _rule_validation_fingerprint(
                context=context,
                rule=evaluation.rule,
                operation=evaluation.operation,
                checks=evaluation.checks_performed,
                expected_value=evaluation.expected_value,
                expected_state=evaluation.expected_state,
                status=ValidationStatus.PASSED,
                failure_code=None,
            )
            for evaluation in evaluations
        )
        bundle_fingerprint = _bundle_validation_fingerprint(
            context,
            required_rule_ids=tuple(evaluation.rule.rule_id for evaluation in evaluations),
            rule_validation_fingerprints=rule_fingerprints,
            intended_use="deterministic_metric_result_validation",
        )
        validated_result = _validated_result(
            context,
            validation_record_ids=validation_ids,
            validation_fingerprint=bundle_fingerprint,
        )
        artifact = _persist_validated_result(validated_result, artifact_store, metadata_store)
        ended_at = utc_now()
        records = tuple(
            ValidationRecord(
                validation_id=validation_id,
                execution_id=context.execution_record.execution_id,
                target_result_ref=context.executed_result.result_id,
                validation_rule_id=evaluation.rule.rule_id,
                validation_version=evaluation.rule.rule_version,
                result_fingerprint=context.executed_result.result_fingerprint,
                validator_id=VALIDATOR_ID,
                validator_version=VALIDATOR_VERSION,
                validation_operation=evaluation.operation,
                checks_performed=evaluation.checks_performed,
                expected_value=evaluation.expected_value,
                expected_state=evaluation.expected_state,
                actual_value=context.executed_result.value,
                actual_state=context.executed_result.metric_state,
                status=ValidationStatus.PASSED,
                observed=context.executed_result.model_dump(mode="json"),
                expected_constraint=evaluation.expected_constraint,
                authoritative_precision=context.executed_result.precision,
                metric_ref=context.executed_result.metric_ref,
                started_at=started_at,
                ended_at=ended_at,
                validated_at=ended_at,
                validated_result_ref=validated_result.validated_result_id,
                validated_result_artifact_ref=artifact,
                validation_fingerprint=rule_fingerprint,
                **lineage,
            )
            for validation_id, evaluation, rule_fingerprint in zip(validation_ids, evaluations, rule_fingerprints)
        )
        for record in records:
            metadata_store.insert_validation_record(record)
        return ValidationOutcome(validation_record=records[0], validation_records=records, validated_result=validated_result)
    except MetricValidationError as exc:
        ended_at = utc_now()
        rule_id = exc.validation_rule_id or _validation_rule_id(metric_ref)
        validation_version = exc.validation_version or VALIDATOR_VERSION
        record = ValidationRecord(
            validation_id=generate_id("val"),
            execution_id=execution_id,
            target_result_ref=result_id,
            validation_rule_id=rule_id,
            validation_version=validation_version,
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
        return ValidationOutcome(validation_record=record, validation_records=(record,), validated_result=None)


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
    _validate_result_fingerprint(plan, node, population, canonical_dataset, execution_record, executed_result)
    checks.append("result_fingerprint_matches")
    return _ValidationContext(
        plan=plan,
        execution_record=execution_record,
        executed_result=executed_result,
        result_artifact=result_artifact,
        node=node,
        population=population,
        canonical_dataset=canonical_dataset,
        canonical_path=canonical_path,
        artifact_store=artifact_store,
        metadata_store=metadata_store,
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
    if tuple(node.dependency_metric_refs) != tuple(dict.fromkeys(expected_dependencies)):
        raise MetricValidationError("metric_dependency_mismatch", "plan node dependency Metric refs do not match Registry")
    if tuple(node.required_validation_rule_refs) != tuple(definition.required_validation_rule_refs):
        raise MetricValidationError(
            "required_validation_rule_refs_mismatch",
            "PlanMetricNode required validation rule refs do not match Metric Registry authority",
        )
    for rule_id in definition.required_validation_rule_refs:
        try:
            require_p5_rule(rule_id, executed_result.metric_ref)
        except KeyError as exc:
            raise MetricValidationError("unknown_required_validation_rule", str(exc)) from exc
    if executed_result.metric_ref in {"revenue", "orders"} and node.dependency_node_ids:
        raise MetricValidationError("metric_dependency_mismatch", "base Metric validation expected no dependency nodes")
    if executed_result.metric_ref == "aov" and set(expected_dependencies) != {"revenue", "orders"}:
        raise MetricValidationError("metric_dependency_mismatch", "AOV Registry dependencies do not match Revenue and Orders")
    if executed_result.metric_ref == "revenue_change" and expected_dependencies != ("revenue", "revenue"):
        raise MetricValidationError("metric_dependency_mismatch", "Revenue Change Registry dependencies do not match Baseline and Comparison Revenue")


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
    if node.metric_ref == "revenue_change":
        if executed_result.scope_ref not in node.population_refs:
            raise MetricValidationError("population_mismatch", "Revenue Change ExecutedResult scope_ref is outside governed plan populations")
        return
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
    if executed_result.metric_ref == "revenue_change":
        if population.population_id not in execution_record.population_refs:
            raise MetricValidationError("population_mismatch", "Revenue Change ExecutionRecord does not include ExecutedResult population")
        if population.population_fingerprint not in execution_record.population_fingerprints:
            raise MetricValidationError("population_fingerprint_mismatch", "Revenue Change ExecutionRecord does not include ExecutedResult population fingerprint")
        if executed_result.scope_ref != population.population_id:
            raise MetricValidationError("population_mismatch", "ExecutedResult scope_ref does not match governed population")
        if executed_result.period_ref != population.period.period_id:
            raise MetricValidationError("period_mismatch", "ExecutedResult period_ref does not match governed population")
        if population.period.period_id not in execution_record.period_refs:
            raise MetricValidationError("period_mismatch", "Revenue Change ExecutionRecord does not include ExecutedResult period ref")
        if execution_record.period_role != "baseline_and_comparison":
            raise MetricValidationError("period_mismatch", "Revenue Change ExecutionRecord period role must retain two-period context")
        if execution_record.grouping != population.grouping.value or population.grouping is not GroupingDimension.NONE:
            raise MetricValidationError("population_grouping_mismatch", "P7-001 validates only governed total-population Revenue Change")
        return
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
    plan: ExecutionPlan,
    node: PlanMetricNode,
    population: PopulationDefinition,
    canonical_dataset: CanonicalDatasetReference,
    execution_record: ExecutionRecord,
    executed_result: ExecutedResult,
) -> None:
    if executed_result.metric_ref == "revenue_change":
        baseline_population, comparison_population = _revenue_change_plan_populations(plan, node)
        baseline_result = ExecutedResult.model_construct(
            result_id=execution_record.operation.get("baseline_revenue_result_ref"),
            execution_id="validated_at_dependency_stage",
            metric_ref="revenue",
            scope_ref=baseline_population.population_id,
            period_ref=baseline_population.period.period_id,
            value=Decimal("0"),
            metric_state=MetricState.VALID,
            result_fingerprint=execution_record.operation.get("baseline_revenue_result_fingerprint"),
            execution_status=ExecutionStatus.COMPLETED,
        )
        comparison_result = ExecutedResult.model_construct(
            result_id=execution_record.operation.get("comparison_revenue_result_ref"),
            execution_id="validated_at_dependency_stage",
            metric_ref="revenue",
            scope_ref=comparison_population.population_id,
            period_ref=comparison_population.period.period_id,
            value=Decimal("0"),
            metric_state=MetricState.VALID,
            result_fingerprint=execution_record.operation.get("comparison_revenue_result_fingerprint"),
            execution_status=ExecutionStatus.COMPLETED,
        )
        expected = _revenue_change_result_fingerprint(
            node=node,
            baseline_population=baseline_population,
            comparison_population=comparison_population,
            canonical_dataset=canonical_dataset,
            value=executed_result.value,
            currency=execution_record.resolved_currency,
            baseline_result=baseline_result,
            comparison_result=comparison_result,
        )
    else:
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


def _evaluate_required_rules(
    context: _ValidationContext,
    dependency_validated_results: tuple[ValidatedResult, ...],
) -> tuple[_RuleEvaluation, ...]:
    definition = get_metric_registry().require(context.executed_result.metric_ref)
    evaluations: list[_RuleEvaluation] = []
    for rule_id in definition.required_validation_rule_refs:
        rule = require_p5_rule(rule_id, context.executed_result.metric_ref)
        try:
            if rule.evaluator == "_evaluate_revenue_sum":
                evaluations.append(_evaluate_revenue_sum(context, rule))
            elif rule.evaluator == "_evaluate_revenue_currency_consistency":
                evaluations.append(_evaluate_revenue_currency_consistency(context, rule))
            elif rule.evaluator == "_evaluate_population_consistency":
                evaluations.append(_evaluate_population_consistency(context, rule))
            elif rule.evaluator == "_evaluate_distinct_order_count":
                evaluations.append(_evaluate_distinct_order_count(context, rule))
            elif rule.evaluator == "_evaluate_aov_from_revenue_orders":
                evaluations.append(_evaluate_aov_from_revenue_orders(context, rule, dependency_validated_results))
            elif rule.evaluator == "_evaluate_revenue_change_from_validated_revenues":
                evaluations.append(_evaluate_revenue_change_from_validated_revenues(context, rule, dependency_validated_results))
            elif rule.evaluator == "_evaluate_revenue_change_dependency_context":
                evaluations.append(_evaluate_revenue_change_dependency_context(context, rule, dependency_validated_results))
            elif rule.evaluator == "_evaluate_revenue_change_currency_consistency":
                evaluations.append(_evaluate_revenue_change_currency_consistency(context, rule, dependency_validated_results))
            else:
                raise MetricValidationError("unknown_required_validation_rule", f"unsupported P5-001 evaluator: {rule.evaluator}")
        except MetricValidationError as exc:
            if exc.validation_rule_id is None:
                exc.validation_rule_id = rule.rule_id
            if exc.validation_version is None:
                exc.validation_version = rule.rule_version
            raise
    return tuple(evaluations)


def _evaluate_revenue_sum(context: _ValidationContext, rule: ValidationRuleDefinition) -> _RuleEvaluation:
    result = context.executed_result
    operation = _operation("revenue_sum", context, "SUM(line_revenue)")
    checks = (*context.checks_performed, "revenue_type_decimal", "revenue_state_valid", "revenue_precision_policy_matches", "revenue_independent_sum_matches")
    if not isinstance(result.value, Decimal) or isinstance(result.value, bool):
        raise MetricValidationError("invalid_revenue_type", "Revenue value must be Decimal", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    if not result.value.is_finite():
        raise MetricValidationError("invalid_revenue_value", "Revenue value must be finite Decimal", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    if result.metric_state is not MetricState.VALID:
        raise MetricValidationError("invalid_metric_state", "Revenue must use MetricState.VALID", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
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
    return _RuleEvaluation(rule=rule, operation=operation, checks_performed=checks, expected_value=expected, expected_state=MetricState.VALID)


def _evaluate_revenue_currency_consistency(context: _ValidationContext, rule: ValidationRuleDefinition) -> _RuleEvaluation:
    operation = _operation("currency_consistency", context, "governed currency basis matches result currency")
    checks = (*context.checks_performed, "governed_currency_resolved", "revenue_currency_matches")
    expected_currency = _resolve_governed_currency(context.population, context.canonical_path)
    if context.executed_result.currency != expected_currency or context.execution_record.resolved_currency != expected_currency:
        raise MetricValidationError(
            "currency_mismatch",
            "Revenue currency does not match governed currency",
            checks_performed=checks,
            operation=operation,
            expected_value=expected_currency,
            expected_state=MetricState.VALID,
        )
    operation = {**operation, "expected_currency": expected_currency}
    return _RuleEvaluation(
        rule=rule,
        operation=operation,
        checks_performed=checks,
        expected_value=expected_currency,
        expected_state=MetricState.VALID,
        expected_constraint="Revenue currency matches governed currency authority",
    )


def _evaluate_population_consistency(context: _ValidationContext, rule: ValidationRuleDefinition) -> _RuleEvaluation:
    operation = _operation("population_consistency", context, "P3/P5 population, period, dataset, and result fingerprint integrity")
    checks = tuple(
        check
        for check in context.checks_performed
        if check
        in {
            "metric_registry_authority_matches",
            "plan_node_linkage_matches",
            "population_identity_matches",
            "canonical_dataset_identity_matches",
            "result_fingerprint_matches",
        }
    )
    return _RuleEvaluation(
        rule=rule,
        operation=operation,
        checks_performed=checks,
        expected_state=context.executed_result.metric_state,
        expected_constraint="governed population and canonical dataset lineage match the ExecutedResult",
    )


def _evaluate_distinct_order_count(context: _ValidationContext, rule: ValidationRuleDefinition) -> _RuleEvaluation:
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
    return _RuleEvaluation(rule=rule, operation=operation, checks_performed=checks, expected_value=expected, expected_state=MetricState.VALID)


def _evaluate_aov_from_revenue_orders(
    context: _ValidationContext,
    rule: ValidationRuleDefinition,
    dependency_validated_results: tuple[ValidatedResult, ...],
) -> _RuleEvaluation:
    result = context.executed_result
    operation = _operation("aov_from_revenue_orders", context, "validated_revenue / validated_orders")
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
    operation = {
        **operation,
        "revenue_validated_result_ref": revenue.validated_result_id,
        "orders_validated_result_ref": orders.validated_result_id,
        "calculation_policy": _aov_calculation_policy_metadata(),
    }
    if orders.value == 0:
        if result.value is not None or result.metric_state is not MetricState.UNDEFINED or result.undefined_reason != "orders_equals_zero":
            raise MetricValidationError("aov_undefined_mismatch", "Orders=0 requires AOV Undefined with value None and orders_equals_zero", checks_performed=checks, operation=operation, expected_value=None, expected_state=MetricState.UNDEFINED)
        return _RuleEvaluation(rule=rule, operation=operation, checks_performed=checks, expected_value=None, expected_state=MetricState.UNDEFINED)
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
    if result.value != expected:
        raise MetricValidationError("value_mismatch", "AOV value does not match validated Revenue / Orders", checks_performed=checks, operation=operation, expected_value=expected, expected_state=MetricState.VALID)
    return _RuleEvaluation(rule=rule, operation=operation, checks_performed=checks, expected_value=expected, expected_state=MetricState.VALID)


def _aov_dependencies(
    context: _ValidationContext,
    dependency_validated_results: tuple[ValidatedResult, ...],
    checks: tuple[str, ...],
    operation: dict[str, Any],
) -> dict[str, ValidatedResult]:
    dependency_nodes = _aov_dependency_nodes(context)
    dependencies = {result.metric_ref: result for result in dependency_validated_results}
    if set(dependencies) != {"revenue", "orders"}:
        raise MetricValidationError("missing_validated_dependency", "AOV validation requires successful validated Revenue and Orders dependencies", checks_performed=checks, operation=operation)
    for metric_ref in ("revenue", "orders"):
        dependency = dependencies[metric_ref]
        governed_node = dependency_nodes[metric_ref]
        if dependency.plan_id != context.plan.plan_id:
            raise MetricValidationError("dependency_plan_mismatch", "AOV dependency plan_id does not match governed ExecutionPlan", checks_performed=checks, operation=operation)
        if dependency.plan_node_id != governed_node.node_id:
            raise MetricValidationError("dependency_plan_node_mismatch", "AOV dependency plan_node_id does not match the governed dependency node", checks_performed=checks, operation=operation)
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
        _verify_dependency_validation_bundle(context, dependency, checks, operation)
    return dependencies


def _aov_dependency_nodes(context: _ValidationContext) -> dict[str, PlanMetricNode]:
    if len(context.node.dependency_node_ids) != 2:
        raise MetricValidationError("metric_dependency_mismatch", "AOV requires exactly two governed dependency nodes")
    node_by_id = {node.node_id: node for node in context.plan.ordered_metrics}
    dependencies: dict[str, PlanMetricNode] = {}
    for dependency_node_id in context.node.dependency_node_ids:
        node = node_by_id.get(dependency_node_id)
        if node is None:
            raise MetricValidationError("metric_dependency_mismatch", "AOV dependency node does not exist in supplied ExecutionPlan")
        if node.metric_ref in dependencies:
            raise MetricValidationError("metric_dependency_mismatch", "AOV dependency nodes must contain one Revenue node and one Orders node")
        dependencies[node.metric_ref] = node
    if set(dependencies) != {"revenue", "orders"}:
        raise MetricValidationError("metric_dependency_mismatch", "AOV dependency nodes must contain one Revenue node and one Orders node")
    return dependencies


def _evaluate_revenue_change_from_validated_revenues(
    context: _ValidationContext,
    rule: ValidationRuleDefinition,
    dependency_validated_results: tuple[ValidatedResult, ...],
) -> _RuleEvaluation:
    result = context.executed_result
    operation = _operation("revenue_change_from_validated_revenues", context, "comparison_revenue - baseline_revenue")
    checks = (
        *context.checks_performed,
        "revenue_change_dependencies_validated",
        "revenue_change_calculation_policy_matches",
        "revenue_change_value_matches_validated_dependencies",
    )
    dependencies = _revenue_change_dependencies(context, dependency_validated_results, checks, operation)
    baseline = dependencies["baseline"]
    comparison = dependencies["comparison"]
    if result.metric_state is not MetricState.VALID or result.undefined_reason is not None:
        raise MetricValidationError("invalid_metric_state", "Revenue Change requires MetricState.VALID with no undefined_reason", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    if not isinstance(result.value, Decimal) or isinstance(result.value, bool):
        raise MetricValidationError("invalid_revenue_change_type", "Revenue Change value must be Decimal", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    if not result.value.is_finite():
        raise MetricValidationError("invalid_revenue_change_value", "Revenue Change value must be finite Decimal", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    if result.precision != REVENUE_CHANGE_DECIMAL_CALCULATION_POLICY_ID or result.unit != "money":
        raise MetricValidationError("precision_policy_mismatch", "Revenue Change precision/unit metadata does not match governed calculation policy", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    if result.precision_metadata != _revenue_change_calculation_policy_metadata():
        raise MetricValidationError("precision_policy_mismatch", "Revenue Change calculation-policy metadata does not match governed policy", checks_performed=checks, operation=operation, expected_state=MetricState.VALID)
    if not isinstance(baseline.value, Decimal) or not isinstance(comparison.value, Decimal):
        raise MetricValidationError("dependency_type_mismatch", "Revenue Change dependencies must be validated Decimal Revenue values", checks_performed=checks, operation=operation)
    with localcontext() as decimal_context:
        decimal_context.prec = REVENUE_CHANGE_DECIMAL_PRECISION
        decimal_context.rounding = REVENUE_CHANGE_DECIMAL_ROUNDING
        expected = comparison.value - baseline.value
    operation = {
        **operation,
        "baseline_revenue_validated_result_ref": baseline.validated_result_id,
        "comparison_revenue_validated_result_ref": comparison.validated_result_id,
        "baseline_revenue_validation_fingerprint": baseline.validation_fingerprint,
        "comparison_revenue_validation_fingerprint": comparison.validation_fingerprint,
        "calculation_policy": _revenue_change_calculation_policy_metadata(),
    }
    if result.value != expected:
        raise MetricValidationError("value_mismatch", "Revenue Change value does not match Comparison Revenue minus Baseline Revenue", checks_performed=checks, operation=operation, expected_value=expected, expected_state=MetricState.VALID)
    return _RuleEvaluation(rule=rule, operation=operation, checks_performed=checks, expected_value=expected, expected_state=MetricState.VALID)


def _evaluate_revenue_change_dependency_context(
    context: _ValidationContext,
    rule: ValidationRuleDefinition,
    dependency_validated_results: tuple[ValidatedResult, ...],
) -> _RuleEvaluation:
    operation = _operation("revenue_change_dependency_context", context, "authenticated Baseline and Comparison Revenue ValidatedResults")
    checks = (
        *context.checks_performed,
        "revenue_change_dependency_plan_nodes_match",
        "revenue_change_dependency_period_roles_match",
        "revenue_change_dependency_population_scope_matches",
        "revenue_change_dependency_validation_bundles_authentic",
    )
    _revenue_change_dependencies(context, dependency_validated_results, checks, operation)
    return _RuleEvaluation(
        rule=rule,
        operation=operation,
        checks_performed=checks,
        expected_state=MetricState.VALID,
        expected_constraint="Revenue Change dependencies are authentic Baseline and Comparison Revenue ValidatedResults",
    )


def _evaluate_revenue_change_currency_consistency(
    context: _ValidationContext,
    rule: ValidationRuleDefinition,
    dependency_validated_results: tuple[ValidatedResult, ...],
) -> _RuleEvaluation:
    operation = _operation("revenue_change_currency_consistency", context, "one governed currency across dependency and result context")
    checks = (
        *context.checks_performed,
        "revenue_change_dependency_currency_matches",
        "revenue_change_record_currency_matches",
        "revenue_change_no_fx_conversion",
    )
    dependencies = _revenue_change_dependencies(context, dependency_validated_results, checks, operation)
    baseline = dependencies["baseline"]
    comparison = dependencies["comparison"]
    if baseline.currency != comparison.currency:
        raise MetricValidationError("dependency_currency_mismatch", "Revenue Change dependency currencies do not match", checks_performed=checks, operation=operation)
    if context.executed_result.currency != baseline.currency:
        raise MetricValidationError("currency_mismatch", "Revenue Change currency does not match dependency currency", checks_performed=checks, operation=operation)
    if context.execution_record.resolved_currency != baseline.currency:
        raise MetricValidationError("currency_mismatch", "Revenue Change ExecutionRecord resolved currency does not match dependency currency", checks_performed=checks, operation=operation)
    if context.execution_record.operation.get("method") != "python_decimal_dependency_arithmetic":
        raise MetricValidationError("currency_mismatch", "Revenue Change must not perform FX conversion or alternate execution", checks_performed=checks, operation=operation)
    operation = {**operation, "expected_currency": baseline.currency}
    return _RuleEvaluation(
        rule=rule,
        operation=operation,
        checks_performed=checks,
        expected_value=baseline.currency,
        expected_state=MetricState.VALID,
        expected_constraint="Revenue Change currency matches Baseline and Comparison Revenue currency authority",
    )


def _revenue_change_dependencies(
    context: _ValidationContext,
    dependency_validated_results: tuple[ValidatedResult, ...],
    checks: tuple[str, ...],
    operation: dict[str, Any],
) -> dict[str, ValidatedResult]:
    dependency_nodes = _revenue_change_dependency_nodes(context)
    dependencies: dict[str, ValidatedResult] = {}
    for dependency in dependency_validated_results:
        if dependency.metric_ref != "revenue":
            raise MetricValidationError("dependency_metric_mismatch", "Revenue Change dependencies must be Revenue ValidatedResults", checks_performed=checks, operation=operation)
        role = dependency.period_role
        if role not in {"baseline", "comparison"}:
            raise MetricValidationError("dependency_period_mismatch", "Revenue Change dependency has invalid period role", checks_performed=checks, operation=operation)
        if role in dependencies:
            raise MetricValidationError("duplicate_validated_dependency", "Revenue Change requires exactly one Baseline and one Comparison Revenue dependency", checks_performed=checks, operation=operation)
        dependencies[role] = dependency
    if set(dependencies) != {"baseline", "comparison"}:
        raise MetricValidationError("missing_validated_dependency", "Revenue Change validation requires Baseline and Comparison Revenue ValidatedResults", checks_performed=checks, operation=operation)
    for role in ("baseline", "comparison"):
        dependency = dependencies[role]
        governed_node = dependency_nodes[role]
        governed_population = _population(context.plan, governed_node.population_refs[0])
        if dependency.plan_id != context.plan.plan_id:
            raise MetricValidationError("dependency_plan_mismatch", "Revenue Change dependency plan_id does not match governed ExecutionPlan", checks_performed=checks, operation=operation)
        if dependency.plan_node_id != governed_node.node_id:
            raise MetricValidationError("dependency_plan_node_mismatch", "Revenue Change dependency plan_node_id does not match governed dependency node", checks_performed=checks, operation=operation)
        if dependency.metric_definition_version != get_metric_registry().require("revenue").definition_version:
            raise MetricValidationError("dependency_metric_version_mismatch", "Revenue Change dependency Metric version does not match Registry", checks_performed=checks, operation=operation)
        if dependency.metric_state is not MetricState.VALID:
            raise MetricValidationError("dependency_metric_state_mismatch", "Revenue Change dependency must be Valid Revenue", checks_performed=checks, operation=operation)
        if dependency.canonical_dataset_ref_id != context.canonical_dataset.canonical_dataset_id:
            raise MetricValidationError("dependency_dataset_mismatch", "Revenue Change dependency canonical dataset does not match target result", checks_performed=checks, operation=operation)
        if dependency.canonical_dataset_fingerprint != context.canonical_dataset.content_fingerprint:
            raise MetricValidationError("dependency_dataset_mismatch", "Revenue Change dependency canonical fingerprint does not match target result", checks_performed=checks, operation=operation)
        if dependency.population_ref != governed_population.population_id:
            raise MetricValidationError("dependency_population_mismatch", "Revenue Change dependency population does not match governed role population", checks_performed=checks, operation=operation)
        if dependency.population_fingerprint != governed_population.population_fingerprint:
            raise MetricValidationError("dependency_population_mismatch", "Revenue Change dependency population fingerprint does not match governed role population", checks_performed=checks, operation=operation)
        if material_scope_payload(governed_population.scope) != material_scope_payload(context.population.scope):
            raise MetricValidationError("dependency_population_mismatch", "Revenue Change dependency scope does not match Revenue Change scope", checks_performed=checks, operation=operation)
        if dependency.period_ref != governed_population.period.period_id or dependency.period_role != role:
            raise MetricValidationError("dependency_period_mismatch", "Revenue Change dependency period role does not match governed dependency node", checks_performed=checks, operation=operation)
        _verify_dependency_validation_bundle(context, dependency, checks, operation)
        _verify_dependency_executed_artifact(context, dependency, checks, operation)
    return dependencies


def _revenue_change_dependency_nodes(context: _ValidationContext) -> dict[str, PlanMetricNode]:
    if len(context.node.dependency_node_ids) != 2:
        raise MetricValidationError("metric_dependency_mismatch", "Revenue Change requires exactly two governed dependency nodes")
    node_by_id = {node.node_id: node for node in context.plan.ordered_metrics}
    dependencies: dict[str, PlanMetricNode] = {}
    for dependency_node_id in context.node.dependency_node_ids:
        node = node_by_id.get(dependency_node_id)
        if node is None:
            raise MetricValidationError("metric_dependency_mismatch", "Revenue Change dependency node does not exist in supplied ExecutionPlan")
        if node.metric_ref != "revenue":
            raise MetricValidationError("metric_dependency_mismatch", "Revenue Change dependency nodes must be Revenue nodes")
        if len(node.period_refs) != 1 or len(node.population_refs) != 1:
            raise MetricValidationError("metric_dependency_mismatch", "Revenue Change dependency Revenue nodes must be single-period nodes")
        population = _population(context.plan, node.population_refs[0])
        role = population.period_role.value
        if role in dependencies:
            raise MetricValidationError("metric_dependency_mismatch", "Revenue Change dependency nodes must contain one Baseline and one Comparison Revenue")
        dependencies[role] = node
    if set(dependencies) != {"baseline", "comparison"}:
        raise MetricValidationError("metric_dependency_mismatch", "Revenue Change dependency nodes must contain one Baseline and one Comparison Revenue")
    return dependencies


def _revenue_change_plan_populations(
    plan: ExecutionPlan,
    node: PlanMetricNode,
) -> tuple[PopulationDefinition, PopulationDefinition]:
    if len(node.population_refs) != 2:
        raise MetricValidationError("population_mismatch", "Revenue Change node must reference Baseline and Comparison populations")
    populations = tuple(_population(plan, population_ref) for population_ref in node.population_refs)
    by_role = {population.period_role.value: population for population in populations}
    if set(by_role) != {"baseline", "comparison"}:
        raise MetricValidationError("period_mismatch", "Revenue Change populations must represent Baseline and Comparison")
    return by_role["baseline"], by_role["comparison"]


def _verify_dependency_executed_artifact(
    context: _ValidationContext,
    dependency: ValidatedResult,
    checks: tuple[str, ...],
    operation: dict[str, Any],
) -> None:
    execution_record = context.metadata_store.get_execution_record(dependency.execution_id)
    if execution_record is None:
        raise MetricValidationError("dependency_execution_record_missing", "Revenue dependency ExecutionRecord is missing", checks_performed=checks, operation=operation)
    if execution_record.request_id != context.execution_record.request_id:
        raise MetricValidationError("dependency_request_mismatch", "Revenue dependency ExecutionRecord request does not match Revenue Change", checks_performed=checks, operation=operation)
    if execution_record.plan_id != context.plan.plan_id or execution_record.plan_fingerprint != context.plan.plan_fingerprint:
        raise MetricValidationError("dependency_plan_mismatch", "Revenue dependency ExecutionRecord plan does not match Revenue Change", checks_performed=checks, operation=operation)
    if execution_record.status is not ExecutionStatus.COMPLETED:
        raise MetricValidationError("dependency_execution_record_missing", "Revenue dependency ExecutionRecord is not completed", checks_performed=checks, operation=operation)
    if not execution_record.output_artifacts or execution_record.output_artifacts[0] != dependency.source_result_artifact_ref:
        raise MetricValidationError("dependency_executed_result_artifact_missing", "Revenue dependency ExecutedResult artifact authority is missing", checks_performed=checks, operation=operation)
    artifact = dependency.source_result_artifact_ref
    persisted = context.metadata_store.get_artifact_reference(artifact.artifact_id)
    if persisted != artifact:
        raise MetricValidationError("dependency_executed_result_artifact_missing", "Revenue dependency ExecutedResult artifact metadata is missing", checks_performed=checks, operation=operation)
    path = context.artifact_store.safe_path(artifact.path)
    if not path.is_file() or artifact.fingerprint is None or sha256_file(path) != artifact.fingerprint:
        raise MetricValidationError("dependency_executed_result_artifact_hash_mismatch", "Revenue dependency ExecutedResult artifact hash does not match metadata", checks_performed=checks, operation=operation)
    restored = ExecutedResult.model_validate_json(path.read_text(encoding="utf-8"))
    if restored.result_id != dependency.executed_result_id or restored.result_fingerprint != dependency.result_fingerprint:
        raise MetricValidationError("dependency_executed_result_artifact_mismatch", "Revenue dependency ExecutedResult artifact content mismatches ValidatedResult", checks_performed=checks, operation=operation)


def _verify_dependency_validation_bundle(
    context: _ValidationContext,
    dependency: ValidatedResult,
    checks: tuple[str, ...],
    operation: dict[str, Any],
) -> None:
    definition = get_metric_registry().require(dependency.metric_ref)
    required_rule_ids = definition.required_validation_rule_refs
    if len(dependency.required_validation_record_ids) != len(required_rule_ids):
        raise MetricValidationError("dependency_required_validation_incomplete", "dependency does not reference every required ValidationRecord", checks_performed=checks, operation=operation)
    records: list[ValidationRecord] = []
    artifact: ArtifactReference | None = None
    for record_id, rule_id in zip(dependency.required_validation_record_ids, required_rule_ids):
        record = context.metadata_store.get_validation_record(record_id)
        if record is None:
            raise MetricValidationError("dependency_validation_record_missing", "dependency required ValidationRecord does not exist", checks_performed=checks, operation=operation)
        records.append(record)
        _verify_dependency_validation_record(dependency, record, rule_id, checks, operation)
        if artifact is None:
            artifact = record.validated_result_artifact_ref
        elif artifact != record.validated_result_artifact_ref:
            raise MetricValidationError("dependency_validated_result_artifact_mismatch", "dependency ValidationRecords do not reference one persisted ValidatedResult artifact", checks_performed=checks, operation=operation)
    if tuple(record.validation_rule_id for record in records) != required_rule_ids:
        raise MetricValidationError("dependency_required_validation_wrong_rules", "dependency ValidationRecords do not match required Metric Registry rule IDs", checks_performed=checks, operation=operation)
    if dependency.validation_record_id != dependency.required_validation_record_ids[0]:
        raise MetricValidationError("dependency_validation_bundle_mismatch", "dependency primary ValidationRecord is not the deterministic governing record", checks_performed=checks, operation=operation)
    if artifact is None:
        raise MetricValidationError("dependency_validated_result_artifact_missing", "dependency has no persisted ValidatedResult artifact authority", checks_performed=checks, operation=operation)
    restored = _load_persisted_dependency_validated_result(artifact, context.artifact_store, context.metadata_store, checks, operation)
    if restored != dependency:
        if (
            restored.validation_fingerprint != dependency.validation_fingerprint
            and restored.model_copy(update={"validation_fingerprint": dependency.validation_fingerprint}) == dependency
        ):
            raise MetricValidationError("dependency_validation_fingerprint_mismatch", "supplied dependency validation fingerprint does not match persisted artifact authority", checks_performed=checks, operation=operation)
        raise MetricValidationError("dependency_validated_result_artifact_mismatch", "supplied dependency ValidatedResult does not equal persisted artifact content", checks_performed=checks, operation=operation)
    expected_bundle = _bundle_validation_fingerprint_from_validated_result(
        dependency,
        required_rule_ids=required_rule_ids,
        rule_validation_fingerprints=tuple(record.validation_fingerprint or "" for record in records),
    )
    if dependency.validation_fingerprint != expected_bundle:
        raise MetricValidationError("dependency_validation_fingerprint_mismatch", "dependency ValidatedResult validation fingerprint is not authentic", checks_performed=checks, operation=operation)


def _verify_dependency_validation_record(
    dependency: ValidatedResult,
    record: ValidationRecord,
    expected_rule_id: str,
    checks: tuple[str, ...],
    operation: dict[str, Any],
) -> None:
    rule = require_p5_rule(expected_rule_id, dependency.metric_ref)
    if record.status is not ValidationStatus.PASSED:
        raise MetricValidationError("dependency_validation_record_failed", "dependency required ValidationRecord did not pass", checks_performed=checks, operation=operation)
    if record.validation_rule_id != expected_rule_id:
        raise MetricValidationError("dependency_required_validation_wrong_rules", "dependency ValidationRecord rule ID does not match required rule", checks_performed=checks, operation=operation)
    if record.validation_version != rule.rule_version:
        raise MetricValidationError("dependency_validation_record_version_mismatch", "dependency ValidationRecord version does not match rule authority", checks_performed=checks, operation=operation)
    expected_fields = {
        "execution_id": dependency.execution_id,
        "target_result_ref": dependency.executed_result_id,
        "metric_ref": dependency.metric_ref,
        "metric_definition_version": dependency.metric_definition_version,
        "plan_id": dependency.plan_id,
        "plan_node_id": dependency.plan_node_id,
        "canonical_dataset_ref_id": dependency.canonical_dataset_ref_id,
        "canonical_dataset_fingerprint": dependency.canonical_dataset_fingerprint,
        "population_ref": dependency.population_ref,
        "population_fingerprint": dependency.population_fingerprint,
        "period_ref": dependency.period_ref,
        "period_role": dependency.period_role,
        "result_fingerprint": dependency.result_fingerprint,
        "validated_result_ref": dependency.validated_result_id,
    }
    for field_name, expected in expected_fields.items():
        if getattr(record, field_name) != expected:
            raise MetricValidationError("dependency_validation_record_lineage_mismatch", "dependency ValidationRecord lineage does not match ValidatedResult", checks_performed=checks, operation=operation)
    if record.validated_result_artifact_ref is None:
        raise MetricValidationError("dependency_validated_result_artifact_missing", "dependency ValidationRecord does not reference a ValidatedResult artifact", checks_performed=checks, operation=operation)
    expected_fingerprint = _rule_validation_fingerprint_from_record(record)
    if record.validation_fingerprint != expected_fingerprint:
        raise MetricValidationError("dependency_validation_record_fingerprint_mismatch", "dependency ValidationRecord rule fingerprint is not authentic", checks_performed=checks, operation=operation)


def _load_persisted_dependency_validated_result(
    artifact: ArtifactReference,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    checks: tuple[str, ...],
    operation: dict[str, Any],
) -> ValidatedResult:
    persisted_artifact = metadata_store.get_artifact_reference(artifact.artifact_id)
    if persisted_artifact != artifact:
        raise MetricValidationError("dependency_validated_result_artifact_missing", "dependency ValidatedResult artifact reference is missing or mismatched", checks_performed=checks, operation=operation)
    path = artifact_store.safe_path(artifact.path)
    if not path.is_file():
        raise MetricValidationError("dependency_validated_result_artifact_missing", "dependency ValidatedResult artifact is missing", checks_performed=checks, operation=operation)
    if artifact.fingerprint is None or sha256_file(path) != artifact.fingerprint:
        raise MetricValidationError("dependency_validated_result_artifact_hash_mismatch", "dependency ValidatedResult artifact hash does not match metadata", checks_performed=checks, operation=operation)
    try:
        return ValidatedResult.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise MetricValidationError("dependency_validated_result_artifact_schema_invalid", f"dependency ValidatedResult artifact is schema-invalid: {exc}", checks_performed=checks, operation=operation) from exc


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
    validation_record_ids: tuple[str, ...],
    validation_fingerprint: str,
) -> ValidatedResult:
    return ValidatedResult(
        validated_result_id=generate_id("valres"),
        validation_record_id=validation_record_ids[0],
        execution_id=context.execution_record.execution_id,
        executed_result_id=context.executed_result.result_id,
        required_validation_record_ids=validation_record_ids,
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
        period_role="baseline_and_comparison"
        if context.executed_result.metric_ref == "revenue_change"
        else context.population.period_role.value,
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


def _rule_validation_fingerprint(
    context: _ValidationContext,
    *,
    rule: ValidationRuleDefinition,
    operation: dict[str, Any],
    checks: tuple[str, ...],
    expected_value: Decimal | int | None,
    expected_state: MetricState | None,
    status: ValidationStatus,
    failure_code: str | None,
) -> str:
    return canonical_json_fingerprint(
        {
            "validator_id": VALIDATOR_ID,
            "validator_version": VALIDATOR_VERSION,
            "validation_rule_id": rule.rule_id,
            "validation_rule_version": rule.rule_version,
            "status": status.value,
            "failure_code": failure_code,
            "metric_ref": context.executed_result.metric_ref,
            "metric_definition_version": context.node.metric_version,
            "result_fingerprint": context.executed_result.result_fingerprint,
            "canonical_dataset_ref": context.canonical_dataset.canonical_dataset_id,
            "canonical_dataset_fingerprint": context.canonical_dataset.content_fingerprint,
            "population_ref": context.population.population_id,
            "population_fingerprint": context.population.population_fingerprint,
            "checks_performed": checks,
            "operation": operation,
            "expected_value": _json_scalar(expected_value),
            "expected_state": expected_state.value if expected_state else None,
            "actual_value": _json_scalar(context.executed_result.value),
            "actual_state": context.executed_result.metric_state.value,
            "precision": context.executed_result.precision,
            "precision_metadata": context.executed_result.precision_metadata,
            "unit": context.executed_result.unit,
            "currency": context.executed_result.currency,
        }
    )


def _rule_validation_fingerprint_from_record(record: ValidationRecord) -> str:
    return canonical_json_fingerprint(
        {
            "validator_id": record.validator_id,
            "validator_version": record.validator_version,
            "validation_rule_id": record.validation_rule_id,
            "validation_rule_version": record.validation_version,
            "status": record.status.value,
            "failure_code": record.failure_code,
            "metric_ref": record.metric_ref,
            "metric_definition_version": record.metric_definition_version,
            "result_fingerprint": record.result_fingerprint,
            "canonical_dataset_ref": record.canonical_dataset_ref_id,
            "canonical_dataset_fingerprint": record.canonical_dataset_fingerprint,
            "population_ref": record.population_ref,
            "population_fingerprint": record.population_fingerprint,
            "checks_performed": record.checks_performed,
            "operation": record.validation_operation,
            "expected_value": _json_scalar(record.expected_value),
            "expected_state": record.expected_state.value if record.expected_state else None,
            "actual_value": _json_scalar(record.actual_value),
            "actual_state": record.actual_state.value if record.actual_state else None,
            "precision": record.authoritative_precision,
            "precision_metadata": (record.observed or {}).get("precision_metadata") if isinstance(record.observed, dict) else None,
            "unit": (record.observed or {}).get("unit") if isinstance(record.observed, dict) else None,
            "currency": (record.observed or {}).get("currency") if isinstance(record.observed, dict) else None,
        }
    )


def _bundle_validation_fingerprint(
    context: _ValidationContext,
    *,
    required_rule_ids: tuple[str, ...],
    rule_validation_fingerprints: tuple[str, ...],
    intended_use: str,
) -> str:
    return canonical_json_fingerprint(
        {
            "validator_id": VALIDATOR_ID,
            "validator_version": VALIDATOR_VERSION,
            "intended_use": intended_use,
            "metric_ref": context.executed_result.metric_ref,
            "metric_definition_version": context.node.metric_version,
            "result_fingerprint": context.executed_result.result_fingerprint,
            "canonical_dataset_ref": context.canonical_dataset.canonical_dataset_id,
            "canonical_dataset_fingerprint": context.canonical_dataset.content_fingerprint,
            "population_ref": context.population.population_id,
            "population_fingerprint": context.population.population_fingerprint,
            "required_validation_rule_ids": required_rule_ids,
            "rule_validation_fingerprints": rule_validation_fingerprints,
            "metric_state": context.executed_result.metric_state.value,
            "value": _json_scalar(context.executed_result.value),
            "undefined_reason": context.executed_result.undefined_reason,
            "precision": context.executed_result.precision,
            "precision_metadata": context.executed_result.precision_metadata,
            "unit": context.executed_result.unit,
            "currency": context.executed_result.currency,
        }
    )


def _bundle_validation_fingerprint_from_validated_result(
    result: ValidatedResult,
    *,
    required_rule_ids: tuple[str, ...],
    rule_validation_fingerprints: tuple[str, ...],
) -> str:
    return canonical_json_fingerprint(
        {
            "validator_id": VALIDATOR_ID,
            "validator_version": VALIDATOR_VERSION,
            "intended_use": result.intended_use,
            "metric_ref": result.metric_ref,
            "metric_definition_version": result.metric_definition_version,
            "result_fingerprint": result.result_fingerprint,
            "canonical_dataset_ref": result.canonical_dataset_ref_id,
            "canonical_dataset_fingerprint": result.canonical_dataset_fingerprint,
            "population_ref": result.population_ref,
            "population_fingerprint": result.population_fingerprint,
            "required_validation_rule_ids": required_rule_ids,
            "rule_validation_fingerprints": rule_validation_fingerprints,
            "metric_state": result.metric_state.value,
            "value": _json_scalar(result.value),
            "undefined_reason": result.undefined_reason,
            "precision": result.precision,
            "precision_metadata": result.precision_metadata,
            "unit": result.unit,
            "currency": result.currency,
        }
    )


def _json_scalar(value: Decimal | int | float | bool | str | None) -> int | float | bool | str | None:
    if isinstance(value, Decimal):
        return str(value)
    return value


def _lineage_payload(context: _ValidationContext) -> dict[str, Any]:
    period_role = (
        "baseline_and_comparison"
        if context.executed_result.metric_ref == "revenue_change"
        else context.population.period_role.value
    )
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
        "period_role": period_role,
    }


def _validation_rule_id(metric_ref: str | None) -> str:
    if metric_ref == "revenue":
        return "validation:revenue_sum"
    if metric_ref == "orders":
        return "validation:distinct_order_count"
    if metric_ref == "aov":
        return "validation:aov_from_revenue_orders"
    if metric_ref == "revenue_change":
        return "validation:revenue_change_from_validated_revenues"
    return "validation:p5_001_fail_closed"


def _aov_calculation_policy_metadata() -> dict[str, str | int]:
    return {
        "calculation_policy_id": AOV_DECIMAL_CALCULATION_POLICY_ID,
        "precision": AOV_DECIMAL_PRECISION,
        "rounding": str(AOV_DECIMAL_ROUNDING),
    }
