from datetime import date

import pytest

from commerce_lens.contracts.common import FailureDetail, FailureStage, GroupingDimension, MetricState, PeriodDefinition, ScopeDefinition
from commerce_lens.contracts.evidence import MetricReference
from commerce_lens.contracts.plans import ExecutionPlan, PlanMetricNode
from commerce_lens.contracts.requests import AnalysisRequest
from commerce_lens.contracts.sufficiency import DataSufficiencyResult, MetricEligibility, SufficiencyState
from commerce_lens.engine import PlanningError, build_execution_plan, validate_execution_plan_pre_execution
from commerce_lens.metrics import METRIC_DEFINITION_VERSION, METRIC_REGISTRY_VERSION, PRECISION_POLICY_REF


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


def _request(
    *,
    metrics: tuple[str, ...],
    grouping: GroupingDimension = GroupingDimension.NONE,
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
        scope=ScopeDefinition(scope_id="all_eligible"),
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
