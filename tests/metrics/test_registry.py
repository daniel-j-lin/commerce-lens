import pytest
from pydantic import ValidationError

from commerce_lens.contracts.common import GroupingDimension
from commerce_lens.metrics import (
    EXECUTION_NOT_IMPLEMENTED_REF,
    METRIC_DEFINITION_VERSION,
    Additivity,
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
