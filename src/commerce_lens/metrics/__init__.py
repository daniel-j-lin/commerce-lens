"""Metric Registry authority for approved CommerceLens MVP metrics."""

from commerce_lens.metrics.registry import (
    EXECUTION_NOT_IMPLEMENTED_REF,
    METRIC_DEFINITION_VERSION,
    METRIC_REGISTRY_VERSION,
    PRECISION_POLICY_REF,
    Additivity,
    DependencyPeriodRole,
    MetricCategory,
    MetricDependency,
    MetricDefinition,
    MetricRegistry,
    PeriodRequirement,
    assert_registry_matches_approved_authority,
    approved_metric_ids,
    get_metric_registry,
)

__all__ = [
    "EXECUTION_NOT_IMPLEMENTED_REF",
    "METRIC_DEFINITION_VERSION",
    "METRIC_REGISTRY_VERSION",
    "PRECISION_POLICY_REF",
    "Additivity",
    "DependencyPeriodRole",
    "MetricCategory",
    "MetricDependency",
    "MetricDefinition",
    "MetricRegistry",
    "PeriodRequirement",
    "assert_registry_matches_approved_authority",
    "approved_metric_ids",
    "get_metric_registry",
]
