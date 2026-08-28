import pytest
from pydantic import ValidationError

from commerce_lens.contracts.common import GroupingDimension
from commerce_lens.metrics import (
    DependencyPeriodRole,
    EXECUTION_NOT_IMPLEMENTED_REF,
    METRIC_DEFINITION_VERSION,
    Additivity,
    MetricDependency,
    MetricRegistry,
    approved_metric_ids,
    get_metric_registry,
)


APPROVED_IDS = {
    "revenue",
    "orders",
    "aov",
    "revenue_change",
    "revenue_change_pct",
    "product_revenue",
    "product_orders",
    "product_revenue_change",
    "product_revenue_change_pct",
    "product_absolute_contribution",
    "product_contribution_share",
    "category_revenue",
    "category_orders",
    "category_revenue_change",
    "category_revenue_change_pct",
    "category_absolute_contribution",
    "category_contribution_share",
    "leading_positive_contributors",
    "leading_negative_contributors",
}


def test_all_and_only_approved_metric_ids_are_registered() -> None:
    assert set(approved_metric_ids()) == APPROVED_IDS
    assert len(approved_metric_ids()) == len(APPROVED_IDS)


def test_unsupported_metric_id_is_rejected() -> None:
    with pytest.raises(KeyError):
        get_metric_registry().require("gross_margin")


def test_metric_definitions_are_versioned_and_do_not_execute() -> None:
    registry = get_metric_registry()

    assert {definition.definition_version for definition in registry.definitions} == {
        METRIC_DEFINITION_VERSION
    }
    assert {
        definition.execution_implementation_ref for definition in registry.definitions
    } == {EXECUTION_NOT_IMPLEMENTED_REF}


def test_required_inputs_dependencies_and_additivity_are_governed() -> None:
    registry = get_metric_registry()

    revenue = registry.require("revenue")
    orders = registry.require("orders")
    aov = registry.require("aov")
    share = registry.require("product_contribution_share")

    assert "line_revenue" in revenue.required_canonical_fields
    assert "order_id" in orders.required_canonical_fields
    assert aov.prerequisite_metric_ids == ("revenue", "orders")
    assert tuple(dependency.period_role for dependency in aov.dependencies) == (
        DependencyPeriodRole.SAME_AS_PARENT,
        DependencyPeriodRole.SAME_AS_PARENT,
    )
    assert aov.additivity is Additivity.DERIVED_NON_ADDITIVE
    assert "orders_equals_zero" in aov.undefined_conditions
    assert "total_revenue_change_equals_zero" in share.undefined_conditions
    assert share.grouping_requirement is GroupingDimension.PRODUCT


def test_dependency_references_resolve_and_registry_is_acyclic() -> None:
    registry = get_metric_registry()
    ids = set(registry.metric_ids)

    for definition in registry.definitions:
        assert set(definition.prerequisite_metric_ids) <= ids


def test_registry_cannot_silently_redefine_metric_id() -> None:
    revenue = get_metric_registry().require("revenue")

    with pytest.raises(ValidationError):
        MetricRegistry(definitions=(revenue, revenue))


def test_registry_rejects_cyclic_dependency_metadata() -> None:
    registry = get_metric_registry()
    revenue = registry.require("revenue").model_copy(
        update={
            "prerequisite_metric_ids": ("orders",),
            "dependencies": (MetricDependency(metric_id="orders", period_role=DependencyPeriodRole.SAME_AS_PARENT),),
        }
    )
    orders = registry.require("orders").model_copy(
        update={
            "prerequisite_metric_ids": ("revenue",),
            "dependencies": (MetricDependency(metric_id="revenue", period_role=DependencyPeriodRole.SAME_AS_PARENT),),
        }
    )
    definitions = tuple(
        revenue if definition.metric_id == "revenue" else orders if definition.metric_id == "orders" else definition
        for definition in registry.definitions
    )

    with pytest.raises(ValidationError):
        MetricRegistry(definitions=definitions)


@pytest.mark.parametrize("metric", ("leading_positive_contributors", "leading_negative_contributors"))
def test_ranking_registry_declares_grouping_dependent_dependencies(metric: str) -> None:
    ranking = get_metric_registry().require(metric)

    assert ranking.grouping_requirement is None
    assert ranking.supported_groupings == (GroupingDimension.PRODUCT, GroupingDimension.CATEGORY)
    assert GroupingDimension.PRODUCT_AND_CATEGORY not in ranking.supported_groupings
    assert "category_id" not in ranking.required_canonical_fields_by_grouping[GroupingDimension.PRODUCT]
    assert "product_id" not in ranking.required_canonical_fields_by_grouping[GroupingDimension.CATEGORY]
    assert {
        (dependency.metric_id, dependency.grouping, dependency.applies_to_groupings)
        for dependency in ranking.dependencies
    } == {
        ("product_absolute_contribution", GroupingDimension.PRODUCT, (GroupingDimension.PRODUCT,)),
        ("category_absolute_contribution", GroupingDimension.CATEGORY, (GroupingDimension.CATEGORY,)),
    }
