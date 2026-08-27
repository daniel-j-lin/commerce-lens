"""Execution plan structural contracts."""

from __future__ import annotations

from pydantic import Field

from commerce_lens.contracts.common import ContractBase, GroupingDimension


class PlanMetricNode(ContractBase):
    metric_ref: str = Field(min_length=1)
    dependency_metric_refs: tuple[str, ...] = ()
    required_validation_rule_refs: tuple[str, ...] = ()


class ExecutionPlan(ContractBase):
    plan_id: str = Field(min_length=1)
    plan_version: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    ordered_metrics: tuple[PlanMetricNode, ...] = ()
    period_refs: tuple[str, ...] = ()
    population_refs: tuple[str, ...] = ()
    grouping: GroupingDimension = GroupingDimension.NONE
    precision_policy_ref: str = Field(min_length=1)
    required_validation_rule_refs: tuple[str, ...] = ()
    plan_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

