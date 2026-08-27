"""Execution plan structural contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from commerce_lens.contracts.common import ContractBase, FailureDetail, GroupingDimension
from commerce_lens.contracts.populations import PopulationDefinition


class PlanMetricNode(ContractBase):
    node_id: str = Field(min_length=1)
    metric_ref: str = Field(min_length=1)
    metric_version: str | None = None
    dependency_metric_refs: tuple[str, ...] = ()
    dependency_node_ids: tuple[str, ...] = ()
    period_refs: tuple[str, ...] = ()
    population_refs: tuple[str, ...] = ()
    grouping: GroupingDimension = GroupingDimension.NONE
    required_canonical_inputs: tuple[str, ...] = ()
    required_validation_rule_refs: tuple[str, ...] = ()
    output_shape: str | None = None
    precision_policy_ref: str | None = None
    execution_implementation_ref: str | None = None
    execution_status: Literal["not_executed"] = "not_executed"
    planning_state: Literal["executable", "blocked"] = "executable"
    failure_details: tuple[FailureDetail, ...] = ()


class ExecutionPlan(ContractBase):
    plan_id: str = Field(min_length=1)
    plan_version: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    sufficiency_id: str | None = None
    ordered_metrics: tuple[PlanMetricNode, ...] = ()
    population_definitions: tuple[PopulationDefinition, ...] = ()
    period_refs: tuple[str, ...] = ()
    population_refs: tuple[str, ...] = ()
    blocked_metric_refs: tuple[str, ...] = ()
    grouping: GroupingDimension = GroupingDimension.NONE
    precision_policy_ref: str = Field(min_length=1)
    required_validation_rule_refs: tuple[str, ...] = ()
    plan_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
