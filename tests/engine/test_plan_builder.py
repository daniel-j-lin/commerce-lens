from datetime import date

import pytest

from commerce_lens.contracts.common import FailureDetail, FailureStage, GroupingDimension, MetricState, PeriodDefinition, ScopeDefinition, ScopeFilter
from commerce_lens.contracts.evidence import MetricReference
from commerce_lens.contracts.plans import ExecutionPlan, PlanMetricNode
from commerce_lens.contracts.requests import AnalysisRequest
from commerce_lens.contracts.sufficiency import DataSufficiencyResult, MetricEligibility, SufficiencyState
from commerce_lens.engine import PlanningError, build_execution_plan, validate_execution_plan_pre_execution
from commerce_lens.metrics import METRIC_DEFINITION_VERSION, METRIC_REGISTRY_VERSION, PRECISION_POLICY_REF, MetricRegistry, get_metric_registry


def test_valid_metric_request_builds_deterministic_plan_without_execution() -> None:
    request = _request(metrics=("revenue_change",))
    plan = build_execution_plan(request, _sufficiency(request))
    equivalent = _request(metrics=("revenue_change",))
    equivalent_plan = build_execution_plan(equivalent, _sufficiency(equivalent))

    assert plan.plan_fingerprint == equivalent_plan.plan_fingerprint
    assert plan.plan_id == equivalent_plan.plan_id
    assert all(node.execution_status == "not_executed" for node in plan.ordered_metrics)
    assert not hasattr(plan, "executed_result_refs")
    assert not hasattr(plan, "validated_result_refs")


def test_material_request_difference_changes_plan_fingerprint() -> None:
    revenue_change = _request(metrics=("revenue_change",))
    revenue_and_aov = _request(metrics=("revenue_change", "aov"))

    first = build_execution_plan(revenue_change, _sufficiency(revenue_change))
    second = build_execution_plan(revenue_and_aov, _sufficiency(revenue_and_aov))

    assert first.plan_fingerprint != second.plan_fingerprint


def test_equivalent_scope_filter_order_has_same_plan_fingerprint() -> None:
    first = _request(
        metrics=("revenue_change",),
        scope=ScopeDefinition(
            scope_id="filtered",
            filters=(
                ScopeFilter(field="product_id", operator="equals", value="p1"),
                ScopeFilter(field="currency", operator="equals", value="USD"),
            ),
            description="presentation text",
        ),
    )
    second = _request(
        metrics=("revenue_change",),
        scope=ScopeDefinition(
            scope_id="filtered",
            filters=(
                ScopeFilter(field="currency", operator="equals", value="USD"),
                ScopeFilter(field="product_id", operator="equals", value="p1"),
            ),
            description="different presentation text",
        ),
    )

    assert build_execution_plan(first, _sufficiency(first)).plan_fingerprint == build_execution_plan(
        second, _sufficiency(second)
    ).plan_fingerprint


def test_aov_nodes_depend_on_revenue_and_orders_for_identical_population() -> None:
    request = _request(metrics=("aov",))
    plan = build_execution_plan(request, _sufficiency(request))
    nodes = {node.node_id: node for node in plan.ordered_metrics}
    aov_nodes = [node for node in plan.ordered_metrics if node.metric_ref == "aov"]

    assert len(aov_nodes) == 2
    for node in aov_nodes:
        assert set(node.dependency_metric_refs) == {"revenue", "orders"}
        dependency_populations = {
            tuple(nodes[dependency_id].population_refs) for dependency_id in node.dependency_node_ids
        }
        assert dependency_populations == {tuple(node.population_refs)}


def test_comparison_metric_depends_on_baseline_and_comparison_revenue_nodes() -> None:
    request = _request(metrics=("revenue_change",))
    plan = build_execution_plan(request, _sufficiency(request))
    change_node = next(node for node in plan.ordered_metrics if node.metric_ref == "revenue_change")
    nodes = {node.node_id: node for node in plan.ordered_metrics}
    dependencies = [nodes[node_id] for node_id in change_node.dependency_node_ids]

    assert [node.metric_ref for node in dependencies] == ["revenue", "revenue"]
    assert {tuple(node.period_refs) for node in dependencies} == {("baseline",), ("comparison",)}


def test_unsupported_metric_fails_closed_before_planning() -> None:
    request = _request(metrics=("gross_margin",))

    with pytest.raises(PlanningError):
        build_execution_plan(request, _sufficiency(request))


def test_ineligible_chain_is_blocked_while_independent_chain_survives() -> None:
    request = _request(metrics=("revenue_change", "category_absolute_contribution"), grouping=GroupingDimension.CATEGORY)
    sufficiency = _sufficiency(
        request,
        ineligible={
            "category_absolute_contribution": (
                FailureDetail(
                    stage=FailureStage.SUFFICIENCY,
                    reason="category attribution evidence missing",
                    target_ref="category_id",
                    governing_ref="canonical_dictionary:20",
                    dependency_scope="category_absolute_contribution",
                    independent_chains_may_continue=True,
                ),
            )
        },
    )

    plan = build_execution_plan(request, sufficiency)

    assert "category_absolute_contribution" in plan.blocked_metric_refs
    assert any(
        node.metric_ref == "revenue_change" and node.planning_state == "executable"
        for node in plan.ordered_metrics
    )
    blocked = next(
        node for node in plan.ordered_metrics if node.metric_ref == "category_absolute_contribution"
    )
    assert blocked.planning_state == "blocked"
    assert blocked.failure_details[0].independent_chains_may_continue


def test_ineligible_single_period_aov_remains_structural_and_independent_change_survives() -> None:
    request = _request(metrics=("revenue_change", "aov"))
    sufficiency = _sufficiency(
        request,
        ineligible={
            "aov": (
                FailureDetail(
                    stage=FailureStage.SUFFICIENCY,
                    reason="orders evidence missing",
                    target_ref="orders",
                    governing_ref="canonical_dictionary:17",
                    dependency_scope="aov",
                    independent_chains_may_continue=True,
                ),
            )
        },
    )

    plan = build_execution_plan(request, sufficiency)

    assert any(node.metric_ref == "revenue_change" and node.planning_state == "executable" for node in plan.ordered_metrics)
    aov_nodes = [node for node in plan.ordered_metrics if node.metric_ref == "aov"]
    assert {tuple(node.period_refs) for node in aov_nodes} == {("baseline",), ("comparison",)}
    assert {node.planning_state for node in aov_nodes} == {"blocked"}
    assert "aov" in plan.blocked_metric_refs


def test_ineligible_single_period_product_revenue_remains_structural_and_independent_change_survives() -> None:
    request = _request(metrics=("revenue_change", "product_revenue"), grouping=GroupingDimension.PRODUCT)
    sufficiency = _sufficiency(
        request,
        ineligible={
            "product_revenue": (
                FailureDetail(
                    stage=FailureStage.SUFFICIENCY,
                    reason="product identity evidence missing",
                    target_ref="product_id",
                    governing_ref="canonical_dictionary:19",
                    dependency_scope="product_revenue",
                    independent_chains_may_continue=True,
                ),
            )
        },
    )

    plan = build_execution_plan(request, sufficiency)

    assert any(node.metric_ref == "revenue_change" and node.planning_state == "executable" for node in plan.ordered_metrics)
    product_nodes = [node for node in plan.ordered_metrics if node.metric_ref == "product_revenue"]
    assert {tuple(node.period_refs) for node in product_nodes} == {("baseline",), ("comparison",)}
    assert {node.grouping for node in product_nodes} == {GroupingDimension.PRODUCT}
    assert {node.planning_state for node in product_nodes} == {"blocked"}


def test_ineligible_metric_with_empty_failure_details_cannot_become_executable() -> None:
    request = _request(metrics=("revenue_change", "aov"))
    sufficiency = _sufficiency(
        request,
        ineligible={"revenue_change": ()},
    )

    plan = build_execution_plan(request, sufficiency)

    blocked = next(node for node in plan.ordered_metrics if node.metric_ref == "revenue_change")
    assert blocked.planning_state == "blocked"
    assert blocked.failure_details
    assert "revenue_change" in plan.blocked_metric_refs
    assert any(node.metric_ref == "aov" and node.planning_state == "executable" for node in plan.ordered_metrics)


def test_ineligible_single_period_metric_with_empty_failure_details_cannot_become_executable() -> None:
    request = _request(metrics=("revenue_change", "aov"))
    sufficiency = _sufficiency(request, ineligible={"aov": ()})

    plan = build_execution_plan(request, sufficiency)

    blocked = [node for node in plan.ordered_metrics if node.metric_ref == "aov"]
    assert blocked
    assert all(node.planning_state == "blocked" for node in blocked)
    assert all(node.failure_details for node in blocked)
    assert "aov" in plan.blocked_metric_refs


def test_missing_requested_metric_eligibility_fails_closed() -> None:
    request = _request(metrics=("revenue_change", "aov"))
    sufficiency = _sufficiency(request).model_copy(
        update={
            "metric_eligibility": (
                MetricEligibility(metric_ref="revenue_change", eligible=True),
            )
        }
    )

    with pytest.raises(PlanningError):
        build_execution_plan(request, sufficiency)


def test_duplicate_requested_metric_eligibility_fails_closed() -> None:
    request = _request(metrics=("revenue_change",))
    sufficiency = _sufficiency(request).model_copy(
        update={
            "metric_eligibility": (
                MetricEligibility(metric_ref="revenue_change", eligible=True),
                MetricEligibility(metric_ref="revenue_change", eligible=True),
            )
        }
    )

    with pytest.raises(PlanningError):
        build_execution_plan(request, sufficiency)


def test_wrong_requested_metric_definition_version_fails_closed() -> None:
    request = _request(metrics=("revenue_change",)).model_copy(
        update={"metrics": (MetricReference(metric_id="revenue_change", definition_version="wrong_version"),)}
    )

    with pytest.raises(PlanningError):
        build_execution_plan(request, _sufficiency(request))


def test_custom_registry_with_unsupported_metric_cannot_be_planned() -> None:
    registry = get_metric_registry()
    gross_margin = registry.require("revenue").model_copy(
        update={
            "metric_id": "gross_margin",
            "display_name": "Gross Margin",
            "business_definition": "Unsupported injected Metric.",
            "prerequisite_metric_ids": (),
            "dependencies": (),
        }
    )
    custom_registry = MetricRegistry(definitions=(*registry.definitions, gross_margin))
    request = _request(metrics=("gross_margin",))

    with pytest.raises(PlanningError):
        build_execution_plan(request, _sufficiency(request), registry=custom_registry)


def test_pre_execution_validation_rejects_custom_registry_with_unsupported_metric() -> None:
    registry = get_metric_registry()
    gross_margin = registry.require("revenue").model_copy(
        update={
            "metric_id": "gross_margin",
            "display_name": "Gross Margin",
            "business_definition": "Unsupported injected Metric.",
            "prerequisite_metric_ids": (),
            "dependencies": (),
        }
    )
    custom_registry = MetricRegistry(definitions=(*registry.definitions, gross_margin))
    plan = ExecutionPlan(
        plan_id="plan_custom_registry",
        plan_version="execution_plan_p3_001_v1",
        request_id="req_1",
        ordered_metrics=(
            PlanMetricNode(
                node_id="node_gross_margin",
                metric_ref="gross_margin",
                metric_version=METRIC_DEFINITION_VERSION,
            ),
        ),
        precision_policy_ref=PRECISION_POLICY_REF,
        plan_fingerprint="a" * 64,
    )

    with pytest.raises(PlanningError):
        validate_execution_plan_pre_execution(plan, registry=custom_registry)


def test_pre_execution_validation_rejects_modified_approved_metric_definition() -> None:
    registry = get_metric_registry()
    modified_revenue = registry.require("revenue").model_copy(update={"business_definition": "Tampered definition."})
    modified_registry = MetricRegistry(
        definitions=tuple(
            modified_revenue if definition.metric_id == "revenue" else definition
            for definition in registry.definitions
        )
    )
    request = _request(metrics=("revenue_change",))
    plan = build_execution_plan(request, _sufficiency(request))

    with pytest.raises(PlanningError):
        validate_execution_plan_pre_execution(plan, registry=modified_registry)


def test_pre_execution_validation_accepts_authoritative_registry_and_valid_plan() -> None:
    request = _request(metrics=("revenue_change",))
    plan = build_execution_plan(request, _sufficiency(request))

    validate_execution_plan_pre_execution(plan, registry=get_metric_registry())


@pytest.mark.parametrize(
    ("metric", "grouping", "root_dependencies"),
    (
        (
            "revenue_change",
            GroupingDimension.NONE,
            (("revenue", ("baseline",), GroupingDimension.NONE), ("revenue", ("comparison",), GroupingDimension.NONE)),
        ),
        (
            "revenue_change_pct",
            GroupingDimension.NONE,
            (("revenue", ("baseline",), GroupingDimension.NONE), ("revenue", ("comparison",), GroupingDimension.NONE)),
        ),
        (
            "product_revenue_change",
            GroupingDimension.PRODUCT,
            (
                ("product_revenue", ("baseline",), GroupingDimension.PRODUCT),
                ("product_revenue", ("comparison",), GroupingDimension.PRODUCT),
            ),
        ),
        (
            "category_revenue_change",
            GroupingDimension.CATEGORY,
            (
                ("category_revenue", ("baseline",), GroupingDimension.CATEGORY),
                ("category_revenue", ("comparison",), GroupingDimension.CATEGORY),
            ),
        ),
        (
            "product_absolute_contribution",
            GroupingDimension.PRODUCT,
            (
                ("product_revenue_change", ("baseline", "comparison"), GroupingDimension.PRODUCT),
                ("revenue_change", ("baseline", "comparison"), GroupingDimension.NONE),
            ),
        ),
        (
            "category_absolute_contribution",
            GroupingDimension.CATEGORY,
            (
                ("category_revenue_change", ("baseline", "comparison"), GroupingDimension.CATEGORY),
                ("revenue_change", ("baseline", "comparison"), GroupingDimension.NONE),
            ),
        ),
        (
            "product_contribution_share",
            GroupingDimension.PRODUCT,
            (
                ("product_absolute_contribution", ("baseline", "comparison"), GroupingDimension.PRODUCT),
                ("revenue_change", ("baseline", "comparison"), GroupingDimension.NONE),
            ),
        ),
        (
            "category_contribution_share",
            GroupingDimension.CATEGORY,
            (
                ("category_absolute_contribution", ("baseline", "comparison"), GroupingDimension.CATEGORY),
                ("revenue_change", ("baseline", "comparison"), GroupingDimension.NONE),
            ),
        ),
    ),
)
def test_two_period_dependency_graphs_are_exact_and_not_duplicated(
    metric: str,
    grouping: GroupingDimension,
    root_dependencies: tuple[tuple[str, tuple[str, ...], GroupingDimension], ...],
) -> None:
    request = _request(metrics=(metric,), grouping=grouping)
    plan = build_execution_plan(request, _sufficiency(request))
    nodes = {node.node_id: node for node in plan.ordered_metrics}
    root = next(node for node in plan.ordered_metrics if node.metric_ref == metric)

    assert tuple(
        (nodes[node_id].metric_ref, tuple(nodes[node_id].period_refs), nodes[node_id].grouping)
        for node_id in root.dependency_node_ids
    ) == root_dependencies
    assert _semantic_node_keys(plan) == tuple(dict.fromkeys(_semantic_node_keys(plan)))


@pytest.mark.parametrize("metric", ("leading_positive_contributors", "leading_negative_contributors"))
@pytest.mark.parametrize(
    ("grouping", "dependency_metric"),
    (
        (GroupingDimension.PRODUCT, "product_absolute_contribution"),
        (GroupingDimension.CATEGORY, "category_absolute_contribution"),
    ),
)
def test_ranking_plan_uses_one_grouping_dependent_contributor_chain(
    metric: str,
    grouping: GroupingDimension,
    dependency_metric: str,
) -> None:
    request = _request(metrics=(metric,), grouping=grouping)
    plan = build_execution_plan(request, _sufficiency(request))
    nodes = {node.node_id: node for node in plan.ordered_metrics}
    ranking = next(node for node in plan.ordered_metrics if node.metric_ref == metric)

    assert ranking.grouping is grouping
    assert ranking.dependency_metric_refs == (dependency_metric,)
    assert {node.metric_ref for node in plan.ordered_metrics if node.grouping is grouping} >= {dependency_metric, metric}
    assert not any(
        node.metric_ref in {"product_absolute_contribution", "category_absolute_contribution"} and node.metric_ref != dependency_metric
        for node in plan.ordered_metrics
    )


@pytest.mark.parametrize("metric", ("leading_positive_contributors", "leading_negative_contributors"))
@pytest.mark.parametrize("grouping", (GroupingDimension.NONE, GroupingDimension.PRODUCT_AND_CATEGORY))
def test_unsupported_ranking_grouping_fails_closed(metric: str, grouping: GroupingDimension) -> None:
    request = _request(metrics=(metric,), grouping=grouping)

    with pytest.raises(PlanningError):
        build_execution_plan(request, _sufficiency(request))


@pytest.mark.parametrize("metric", ("leading_positive_contributors", "leading_negative_contributors"))
def test_product_ranking_inputs_do_not_require_category_id(metric: str) -> None:
    request = _request(metrics=(metric,), grouping=GroupingDimension.PRODUCT)
    plan = build_execution_plan(request, _sufficiency(request))
    ranking = next(node for node in plan.ordered_metrics if node.metric_ref == metric)

    assert "product_id" in ranking.required_canonical_inputs
    assert "category_id" not in ranking.required_canonical_inputs


@pytest.mark.parametrize("metric", ("leading_positive_contributors", "leading_negative_contributors"))
def test_category_ranking_inputs_do_not_require_product_id(metric: str) -> None:
    request = _request(metrics=(metric,), grouping=GroupingDimension.CATEGORY)
    plan = build_execution_plan(request, _sufficiency(request))
    ranking = next(node for node in plan.ordered_metrics if node.metric_ref == metric)

    assert "category_id" in ranking.required_canonical_inputs
    assert "product_id" not in ranking.required_canonical_inputs


def test_exact_duplicate_equals_filters_do_not_change_plan_fingerprint() -> None:
    plain = _request(
        metrics=("revenue_change",),
        scope=ScopeDefinition(
            scope_id="filtered",
            filters=(ScopeFilter(field="currency", operator="equals", value="USD"),),
        ),
    )
    duplicate = _request(
        metrics=("revenue_change",),
        scope=ScopeDefinition(
            scope_id="filtered",
            filters=(
                ScopeFilter(field="currency", operator="equals", value="USD"),
                ScopeFilter(field="currency", operator="equals", value="USD"),
            ),
        ),
    )

    assert build_execution_plan(plain, _sufficiency(plain)).plan_fingerprint == build_execution_plan(
        duplicate, _sufficiency(duplicate)
    ).plan_fingerprint


def test_different_equals_filter_values_remain_material_to_plan_fingerprint() -> None:
    usd = _request(
        metrics=("revenue_change",),
        scope=ScopeDefinition(
            scope_id="filtered",
            filters=(ScopeFilter(field="currency", operator="equals", value="USD"),),
        ),
    )
    mixed = _request(
        metrics=("revenue_change",),
        scope=ScopeDefinition(
            scope_id="filtered",
            filters=(
                ScopeFilter(field="currency", operator="equals", value="USD"),
                ScopeFilter(field="currency", operator="equals", value="EUR"),
            ),
        ),
    )

    assert build_execution_plan(usd, _sufficiency(usd)).plan_fingerprint != build_execution_plan(
        mixed, _sufficiency(mixed)
    ).plan_fingerprint


def test_pre_execution_validation_rejects_incompatible_aov_populations() -> None:
    revenue = PlanMetricNode(
        node_id="node_revenue",
        metric_ref="revenue",
        metric_version=METRIC_DEFINITION_VERSION,
        period_refs=("baseline",),
        population_refs=("pop_baseline",),
    )
    orders = PlanMetricNode(
        node_id="node_orders",
        metric_ref="orders",
        metric_version=METRIC_DEFINITION_VERSION,
        period_refs=("comparison",),
        population_refs=("pop_comparison",),
    )
    aov = PlanMetricNode(
        node_id="node_aov",
        metric_ref="aov",
        metric_version=METRIC_DEFINITION_VERSION,
        dependency_node_ids=("node_revenue", "node_orders"),
        dependency_metric_refs=("revenue", "orders"),
        period_refs=("baseline",),
        population_refs=("pop_baseline",),
    )
    plan = ExecutionPlan(
        plan_id="plan_bad",
        plan_version="execution_plan_p3_001_v1",
        request_id="req_1",
        ordered_metrics=(revenue, orders, aov),
        period_refs=("baseline", "comparison"),
        population_refs=("pop_baseline", "pop_comparison"),
        grouping=GroupingDimension.NONE,
        precision_policy_ref=PRECISION_POLICY_REF,
        plan_fingerprint="a" * 64,
    )

    with pytest.raises(PlanningError):
        validate_execution_plan_pre_execution(plan)


def test_pre_execution_validation_rejects_wrong_metric_definition_version() -> None:
    request = _request(metrics=("revenue_change",))
    plan = build_execution_plan(request, _sufficiency(request))
    bad_node = plan.ordered_metrics[0].model_copy(update={"metric_version": "wrong_version"})
    bad_plan = plan.model_copy(update={"ordered_metrics": (bad_node, *plan.ordered_metrics[1:])})

    with pytest.raises(PlanningError):
        validate_execution_plan_pre_execution(bad_plan)


def test_pre_execution_validation_rejects_missing_dependency_node() -> None:
    request = _request(metrics=("aov",))
    plan = build_execution_plan(request, _sufficiency(request))
    aov = next(node for node in plan.ordered_metrics if node.metric_ref == "aov")
    bad_aov = aov.model_copy(update={"dependency_node_ids": ("missing_node",)})
    bad_plan = plan.model_copy(
        update={
            "ordered_metrics": tuple(bad_aov if node.node_id == aov.node_id else node for node in plan.ordered_metrics),
        }
    )

    with pytest.raises(PlanningError):
        validate_execution_plan_pre_execution(bad_plan)


def test_pre_execution_validation_rejects_non_not_executed_node() -> None:
    request = _request(metrics=("revenue_change",))
    plan = build_execution_plan(request, _sufficiency(request))
    payload = plan.ordered_metrics[0].model_dump()
    payload["execution_status"] = "executed"
    bad_node = PlanMetricNode.model_construct(**payload)
    bad_plan = plan.model_copy(update={"ordered_metrics": (bad_node, *plan.ordered_metrics[1:])})

    with pytest.raises(PlanningError):
        validate_execution_plan_pre_execution(bad_plan)


def test_total_and_grouped_nodes_reference_compatible_populations() -> None:
    request = _request(metrics=("product_absolute_contribution",), grouping=GroupingDimension.PRODUCT)
    plan = build_execution_plan(request, _sufficiency(request))
    populations = {population.population_id: population for population in plan.population_definitions}

    for node in plan.ordered_metrics:
        assert {populations[population_ref].grouping for population_ref in node.population_refs} == {node.grouping}
    assert all(
        populations[population_ref].grouping is GroupingDimension.NONE
        for node in plan.ordered_metrics
        if node.metric_ref == "revenue"
        for population_ref in node.population_refs
    )
    assert all(
        populations[population_ref].grouping is GroupingDimension.PRODUCT
        for node in plan.ordered_metrics
        if node.metric_ref.startswith("product_")
        for population_ref in node.population_refs
    )


def test_category_nodes_reference_category_populations() -> None:
    request = _request(metrics=("category_absolute_contribution",), grouping=GroupingDimension.CATEGORY)
    plan = build_execution_plan(request, _sufficiency(request))
    populations = {population.population_id: population for population in plan.population_definitions}

    assert all(
        populations[population_ref].grouping is GroupingDimension.CATEGORY
        for node in plan.ordered_metrics
        if node.metric_ref.startswith("category_")
        for population_ref in node.population_refs
    )
    assert all(
        populations[population_ref].preserves_unclassified_category
        for node in plan.ordered_metrics
        if node.metric_ref.startswith("category_")
        for population_ref in node.population_refs
    )


def _request(
    *,
    metrics: tuple[str, ...],
    grouping: GroupingDimension = GroupingDimension.NONE,
    scope: ScopeDefinition = ScopeDefinition(scope_id="all_eligible"),
) -> AnalysisRequest:
    return AnalysisRequest(
        canonical_business_question_id="canonical_revenue_change",
        metrics=tuple(
            MetricReference(metric_id=metric_id, definition_version=METRIC_DEFINITION_VERSION)
            for metric_id in metrics
        ),
        baseline_period=PeriodDefinition(
            period_id="baseline",
            label="Baseline",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
            date_convention_ref="order_date_utc",
        ),
        comparison_period=PeriodDefinition(
            period_id="comparison",
            label="Comparison",
            start_date=date(2026, 1, 3),
            end_date=date(2026, 1, 4),
            date_convention_ref="order_date_utc",
        ),
        scope=scope,
        grouping=grouping,
        dataset_ref_id="ds_1",
        canonical_schema_version="canonical_mvp_v1",
        metric_registry_version=METRIC_REGISTRY_VERSION,
    )


def _sufficiency(
    request: AnalysisRequest,
    *,
    ineligible: dict[str, tuple[FailureDetail, ...]] | None = None,
) -> DataSufficiencyResult:
    ineligible = ineligible or {}
    return DataSufficiencyResult(
        sufficiency_id=f"suff_{request.request_id}",
        request_id=request.request_id,
        dataset_ref_id=request.dataset_ref_id,
        canonical_dataset_ref_id="cds_1",
        metric_eligibility=tuple(
            MetricEligibility(
                metric_ref=metric.metric_id,
                eligible=metric.metric_id not in ineligible,
                metric_state=MetricState.INADMISSIBLE if metric.metric_id in ineligible else None,
                failure_details=ineligible.get(metric.metric_id, ()),
            )
            for metric in request.metrics
        ),
        state=SufficiencyState.PARTIAL if ineligible else SufficiencyState.SUFFICIENT,
    )


def _semantic_node_keys(plan: ExecutionPlan) -> tuple[tuple[str, tuple[str, ...], GroupingDimension, tuple[str, ...]], ...]:
    return tuple(
        (node.metric_ref, tuple(node.period_refs), node.grouping, tuple(node.population_refs))
        for node in plan.ordered_metrics
    )
