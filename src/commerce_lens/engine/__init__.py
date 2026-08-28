"""Deterministic engine pre-execution boundaries."""

from commerce_lens.engine.plan_builder import (
    EXECUTION_PLAN_VERSION,
    PlanningError,
    build_execution_plan,
    validate_execution_plan_pre_execution,
)
from commerce_lens.engine.execution import (
    APPROVED_EXECUTABLE_METRICS,
    REFERENCE_EXECUTOR_ID,
    REFERENCE_EXECUTOR_VERSION,
    MetricExecutionError,
    PlanExecutionOutcome,
    execute_plan,
)
from commerce_lens.engine.populations import PopulationDefinitionError, build_population_definitions

__all__ = [
    "APPROVED_EXECUTABLE_METRICS",
    "EXECUTION_PLAN_VERSION",
    "MetricExecutionError",
    "PlanExecutionOutcome",
    "PlanningError",
    "PopulationDefinitionError",
    "REFERENCE_EXECUTOR_ID",
    "REFERENCE_EXECUTOR_VERSION",
    "build_execution_plan",
    "build_population_definitions",
    "execute_plan",
    "validate_execution_plan_pre_execution",
]
