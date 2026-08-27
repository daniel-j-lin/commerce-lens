"""Deterministic pre-execution ExecutionPlan builder."""

from __future__ import annotations

from commerce_lens.contracts.common import FailureDetail, FailureStage, GroupingDimension
from commerce_lens.contracts.plans import ExecutionPlan, PlanMetricNode
from commerce_lens.contracts.populations import PopulationDefinition, PopulationPeriodRole
from commerce_lens.contracts.requests import AnalysisRequest
from commerce_lens.contracts.sufficiency import DataSufficiencyResult, MetricEligibility
from commerce_lens.engine.populations import build_population_definitions, material_scope_payload
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, stable_content_id
from commerce_lens.metrics.registry import (
    PRECISION_POLICY_REF,
    DependencyPeriodRole,
    MetricDefinition,
    MetricDependency,
    MetricRegistry,
    PeriodRequirement,
    assert_registry_matches_approved_authority,
    get_metric_registry,
)


EXECUTION_PLAN_VERSION = "execution_plan_p3_001_v1"


class PlanningError(ValueError):
    """Raised when pre-execution planning must fail closed."""


def build_execution_plan(
    request: AnalysisRequest,
    sufficiency: DataSufficiencyResult,
    *,
    registry: MetricRegistry | None = None,
) -> ExecutionPlan:
    """Build a deterministic plan from governed request and sufficiency inputs.

    The plan references future execution implementations but does not execute
    Metrics and does not create execution, validation, result, or evidence records.
    """
    active_registry = registry or get_metric_registry()
    try:
        assert_registry_matches_approved_authority(active_registry)
    except ValueError as exc:
        raise PlanningError(str(exc)) from exc
    if request.metric_registry_version != active_registry.registry_version:
        raise PlanningError("AnalysisRequest metric_registry_version does not match the active Metric Registry")
    if sufficiency.request_id != request.request_id:
        raise PlanningError("AnalysisRequest and DataSufficiencyResult request IDs must match")

    requested_ids = tuple(metric.metric_id for metric in request.metrics)
    for metric in request.metrics:
        try:
            definition = active_registry.require(metric.metric_id)
        except KeyError as exc:
            raise PlanningError(str(exc)) from exc
        if metric.definition_version != definition.definition_version:
            raise PlanningError("AnalysisRequest MetricReference definition_version does not match Metric Registry")

    eligibility_by_metric = _requested_eligibility_by_metric(requested_ids, sufficiency.metric_eligibility)
    populations = build_population_definitions(
        request,
        sufficiency,
        groupings=(GroupingDimension.NONE, GroupingDimension.PRODUCT, GroupingDimension.CATEGORY),
    )
    nodes: list[PlanMetricNode] = []
    node_keys: dict[tuple[str, str | None, GroupingDimension], str] = {}

    def add_node(metric_id: str, period_role: PopulationPeriodRole | None, grouping: GroupingDimension) -> PlanMetricNode:
        key = (metric_id, period_role.value if period_role else None, grouping)
        existing_id = node_keys.get(key)
        if existing_id is not None:
            return next(node for node in nodes if node.node_id == existing_id)

        definition = active_registry.require(metric_id)
        dependency_nodes: list[PlanMetricNode] = []
        _validate_grouping_supported(definition, grouping)
        for dependency in _effective_dependencies(definition, grouping):
            dependency_periods = _dependency_period_roles(dependency, period_role)
            for dependency_period in dependency_periods:
                dependency_nodes.append(
                    add_node(
                        dependency.metric_id,
                        dependency_period,
                        _dependency_grouping(dependency, active_registry),
                    )
                )

        dependency_failures = tuple(
            FailureDetail(
                stage=FailureStage.PLANNING,
                reason="dependency node is blocked",
                target_ref=dependency.node_id,
                governing_ref="tasks:P3-001:28",
                dependency_scope=metric_id,
                independent_chains_may_continue=True,
            )
            for dependency in dependency_nodes
            if dependency.planning_state == "blocked"
        )
        eligibility = eligibility_by_metric.get(metric_id)
        eligibility_failures = _eligibility_failures(metric_id, eligibility)
        planning_state = "blocked" if eligibility_failures or dependency_failures else "executable"
        population_refs = _population_refs(definition, populations, period_role, grouping)
        period_refs = tuple(population.period.period_id for population in populations if population.population_id in population_refs)
        payload = {
            "plan_version": EXECUTION_PLAN_VERSION,
            "metric_id": metric_id,
            "metric_version": definition.definition_version,
            "period_role": period_role.value if period_role else None,
            "period_refs": period_refs,
            "population_refs": population_refs,
            "grouping": grouping.value,
            "dependency_node_ids": [node.node_id for node in dependency_nodes],
            "planning_state": planning_state,
        }
        node_fingerprint = canonical_json_fingerprint(payload)
        node = PlanMetricNode(
            node_id=stable_content_id("node", node_fingerprint),
            metric_ref=metric_id,
            metric_version=definition.definition_version,
            dependency_metric_refs=tuple(dict.fromkeys(dependency.metric_ref for dependency in dependency_nodes)),
            dependency_node_ids=tuple(node.node_id for node in dependency_nodes),
            period_refs=period_refs,
            population_refs=population_refs,
            grouping=grouping,
            required_canonical_inputs=definition.required_canonical_fields,
            required_validation_rule_refs=definition.required_validation_rule_refs,
            output_shape=definition.output_shape,
            precision_policy_ref=definition.precision_policy_ref,
            execution_implementation_ref=definition.execution_implementation_ref,
            planning_state=planning_state,
            failure_details=tuple((*eligibility_failures, *dependency_failures)),
        )
        nodes.append(node)
        node_keys[key] = node.node_id
        return node

    for metric_id in requested_ids:
        eligibility = eligibility_by_metric.get(metric_id)
        if eligibility is not None and not eligibility.eligible:
            add_node(metric_id, None, _effective_grouping(metric_id, request.grouping, active_registry))
            continue
        definition = active_registry.require(metric_id)
        period_roles = _root_period_roles(definition)
        for period_role in period_roles:
            add_node(metric_id, period_role, _effective_grouping(metric_id, request.grouping, active_registry))

    all_validation_refs = tuple(dict.fromkeys(ref for node in nodes for ref in node.required_validation_rule_refs))
    blocked_metric_refs = tuple(dict.fromkeys(node.metric_ref for node in nodes if node.planning_state == "blocked"))
    fingerprint = canonical_json_fingerprint(
        {
            "planner_version": EXECUTION_PLAN_VERSION,
            "registry_version": active_registry.registry_version,
            "canonical_schema_version": request.canonical_schema_version,
            "dataset_ref_id": request.dataset_ref_id,
            "canonical_dataset_ref_id": sufficiency.canonical_dataset_ref_id,
            "metrics": requested_ids,
            "periods": {
                "baseline": request.baseline_period.model_dump(mode="json"),
                "comparison": request.comparison_period.model_dump(mode="json"),
            },
            "scope": material_scope_payload(request.scope),
            "grouping": request.grouping.value,
            "population_fingerprints": [population.population_fingerprint for population in populations],
            "metric_eligibility": [_eligibility_payload(item) for item in sufficiency.metric_eligibility],
            "nodes": [node.model_dump(mode="json") for node in nodes],
        }
    )
    plan = ExecutionPlan(
        plan_id=stable_content_id("plan", fingerprint),
        plan_version=EXECUTION_PLAN_VERSION,
        request_id=request.request_id,
        sufficiency_id=sufficiency.sufficiency_id,
        ordered_metrics=tuple(nodes),
        population_definitions=populations,
        period_refs=(request.baseline_period.period_id, request.comparison_period.period_id),
        population_refs=tuple(population.population_id for population in populations),
        blocked_metric_refs=blocked_metric_refs,
        grouping=request.grouping,
        precision_policy_ref=PRECISION_POLICY_REF,
        required_validation_rule_refs=all_validation_refs,
        plan_fingerprint=fingerprint,
    )
    validate_execution_plan_pre_execution(plan, registry=active_registry)
    return plan


def validate_execution_plan_pre_execution(
    plan: ExecutionPlan,
    *,
    registry: MetricRegistry | None = None,
) -> None:
    """Fail closed when a structural plan violates governed pre-execution rules."""
    active_registry = registry or get_metric_registry()
    node_by_id = {node.node_id: node for node in plan.ordered_metrics}
    population_by_id = {population.population_id: population for population in plan.population_definitions}
    if plan.population_refs and not population_by_id:
        raise PlanningError("ExecutionPlan must include governed population definitions for pre-execution validation")
    if set(plan.population_refs) != set(population_by_id):
        raise PlanningError("ExecutionPlan population refs must match embedded governed population definitions")
    for node in plan.ordered_metrics:
        try:
            definition = active_registry.require(node.metric_ref)
        except KeyError as exc:
            raise PlanningError(str(exc)) from exc
        if node.metric_version != definition.definition_version:
            raise PlanningError(f"plan node {node.node_id} Metric definition version does not match the Metric Registry")
        _validate_grouping_supported(definition, node.grouping)
        for dependency_id in node.dependency_node_ids:
            if dependency_id not in node_by_id:
                raise PlanningError(f"plan node {node.node_id} references missing dependency node {dependency_id}")
        if any(population_ref not in population_by_id for population_ref in node.population_refs):
            raise PlanningError(f"plan node {node.node_id} references unknown governed population")
        if any(population_by_id[population_ref].grouping is not node.grouping for population_ref in node.population_refs):
            raise PlanningError(f"plan node {node.node_id} has incompatible node/population grouping")
        if node.period_refs:
            population_period_refs = tuple(
                population_by_id[population_ref].period.period_id
                for population_ref in node.population_refs
            )
            if population_period_refs != node.period_refs:
                raise PlanningError(f"plan node {node.node_id} has incompatible period/population refs")
        if node.metric_ref == "aov":
            dependency_populations = {
                tuple(node_by_id[dependency_id].population_refs)
                for dependency_id in node.dependency_node_ids
            }
            dependency_periods = {
                tuple(node_by_id[dependency_id].period_refs)
                for dependency_id in node.dependency_node_ids
            }
            if len(dependency_populations) != 1 or len(dependency_periods) != 1:
                raise PlanningError("AOV dependency nodes must use identical governed populations and periods")
    if any(node.execution_status != "not_executed" for node in plan.ordered_metrics):
        raise PlanningError("P3-001 ExecutionPlan nodes must remain not_executed")


def _root_period_roles(definition: MetricDefinition) -> tuple[PopulationPeriodRole | None, ...]:
    if definition.period_requirement is PeriodRequirement.SINGLE_PERIOD:
        return (PopulationPeriodRole.BASELINE, PopulationPeriodRole.COMPARISON)
    return (None,)


def _dependency_period_roles(
    dependency: MetricDependency,
    parent_period_role: PopulationPeriodRole | None,
) -> tuple[PopulationPeriodRole | None, ...]:
    if dependency.period_role is DependencyPeriodRole.SAME_AS_PARENT:
        if parent_period_role is None:
            raise PlanningError("same-period dependency requires a parent period role")
        return (parent_period_role,)
    if dependency.period_role is DependencyPeriodRole.BASELINE:
        return (PopulationPeriodRole.BASELINE,)
    if dependency.period_role is DependencyPeriodRole.COMPARISON:
        return (PopulationPeriodRole.COMPARISON,)
    if dependency.period_role is DependencyPeriodRole.BASELINE_AND_COMPARISON:
        return (PopulationPeriodRole.BASELINE, PopulationPeriodRole.COMPARISON)
    return (None,)


def _population_refs(
    definition: MetricDefinition,
    populations: tuple[PopulationDefinition, ...],
    period_role: PopulationPeriodRole | None,
    grouping: GroupingDimension,
) -> tuple[str, ...]:
    if definition.period_requirement is PeriodRequirement.SINGLE_PERIOD and period_role is not None:
        return tuple(pop.population_id for pop in populations if pop.period_role is period_role and pop.grouping is grouping)
    return tuple(pop.population_id for pop in populations if pop.grouping is grouping)


def _effective_grouping(
    metric_id: str,
    requested_grouping: GroupingDimension,
    registry: MetricRegistry,
) -> GroupingDimension:
    definition = registry.require(metric_id)
    if definition.supported_groupings and requested_grouping in definition.supported_groupings:
        return requested_grouping
    if definition.supported_groupings and requested_grouping not in definition.supported_groupings:
        raise PlanningError(f"Metric {metric_id} does not support requested grouping {requested_grouping.value}")
    return definition.grouping_requirement


def _effective_dependencies(
    definition: MetricDefinition,
    grouping: GroupingDimension,
) -> tuple[MetricDependency, ...]:
    return tuple(
        dependency
        for dependency in definition.dependencies
        if not dependency.applies_to_groupings or grouping in dependency.applies_to_groupings
    )


def _dependency_grouping(dependency: MetricDependency, registry: MetricRegistry) -> GroupingDimension:
    if dependency.grouping is not None:
        return dependency.grouping
    return registry.require(dependency.metric_id).grouping_requirement


def _validate_grouping_supported(definition: MetricDefinition, grouping: GroupingDimension) -> None:
    if definition.supported_groupings and grouping not in definition.supported_groupings:
        raise PlanningError(f"Metric {definition.metric_id} does not support grouping {grouping.value}")
    if not definition.supported_groupings and grouping is not definition.grouping_requirement:
        raise PlanningError(f"Metric {definition.metric_id} requires grouping {definition.grouping_requirement.value}")


def _requested_eligibility_by_metric(
    requested_ids: tuple[str, ...],
    metric_eligibility: tuple[MetricEligibility, ...],
) -> dict[str, MetricEligibility]:
    requested = set(requested_ids)
    seen: dict[str, list[MetricEligibility]] = {metric_id: [] for metric_id in requested}
    for item in metric_eligibility:
        if item.metric_ref in requested:
            seen[item.metric_ref].append(item)
    missing = [metric_id for metric_id in requested_ids if len(seen[metric_id]) == 0]
    duplicates = [metric_id for metric_id in requested_ids if len(seen[metric_id]) > 1]
    if missing:
        raise PlanningError(f"DataSufficiencyResult is missing MetricEligibility for requested Metric(s): {missing}")
    if duplicates:
        raise PlanningError(f"DataSufficiencyResult has duplicate MetricEligibility for requested Metric(s): {duplicates}")
    return {metric_id: items[0] for metric_id, items in seen.items()}


def _eligibility_failures(metric_id: str, eligibility: MetricEligibility | None) -> tuple[FailureDetail, ...]:
    if eligibility is None or eligibility.eligible:
        return ()
    if eligibility.failure_details:
        return eligibility.failure_details
    return (
        FailureDetail(
            stage=FailureStage.PLANNING,
            reason="Data Sufficiency marked requested Metric ineligible",
            target_ref=metric_id,
            governing_ref="tasks:P3-001:28",
            dependency_scope=metric_id,
            independent_chains_may_continue=True,
        ),
    )


def _eligibility_payload(item: MetricEligibility) -> dict[str, object]:
    return {
        "metric_ref": item.metric_ref,
        "eligible": item.eligible,
        "metric_state": item.metric_state.value if item.metric_state is not None else None,
        "failure_details": [failure.model_dump(mode="json") for failure in item.failure_details],
    }
