"""Narrow P5-001 deterministic validation-rule authority."""

from __future__ import annotations

from dataclasses import dataclass


P5_VALIDATION_RULE_VERSION = "p5_001_rule_v1"


@dataclass(frozen=True)
class ValidationRuleDefinition:
    rule_id: str
    rule_version: str
    applicable_metric_refs: tuple[str, ...]
    evaluator: str


P5_VALIDATION_RULES: dict[str, ValidationRuleDefinition] = {
    "validation:revenue_sum": ValidationRuleDefinition(
        rule_id="validation:revenue_sum",
        rule_version=P5_VALIDATION_RULE_VERSION,
        applicable_metric_refs=("revenue",),
        evaluator="_evaluate_revenue_sum",
    ),
    "validation:currency_consistency": ValidationRuleDefinition(
        rule_id="validation:currency_consistency",
        rule_version=P5_VALIDATION_RULE_VERSION,
        applicable_metric_refs=("revenue",),
        evaluator="_evaluate_revenue_currency_consistency",
    ),
    "validation:population_consistency": ValidationRuleDefinition(
        rule_id="validation:population_consistency",
        rule_version=P5_VALIDATION_RULE_VERSION,
        applicable_metric_refs=("revenue", "orders", "aov"),
        evaluator="_evaluate_population_consistency",
    ),
    "validation:distinct_order_count": ValidationRuleDefinition(
        rule_id="validation:distinct_order_count",
        rule_version=P5_VALIDATION_RULE_VERSION,
        applicable_metric_refs=("orders",),
        evaluator="_evaluate_distinct_order_count",
    ),
    "validation:aov_from_revenue_orders": ValidationRuleDefinition(
        rule_id="validation:aov_from_revenue_orders",
        rule_version=P5_VALIDATION_RULE_VERSION,
        applicable_metric_refs=("aov",),
        evaluator="_evaluate_aov_from_revenue_orders",
    ),
}


def require_p5_rule(rule_id: str, metric_ref: str) -> ValidationRuleDefinition:
    rule = P5_VALIDATION_RULES.get(rule_id)
    if rule is None:
        raise KeyError(f"unsupported P5-001 validation rule: {rule_id}")
    if metric_ref not in rule.applicable_metric_refs:
        raise KeyError(f"P5-001 validation rule {rule_id} does not apply to {metric_ref}")
    return rule
