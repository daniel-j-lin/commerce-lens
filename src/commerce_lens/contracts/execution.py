"""Execution record and executed-result contracts."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from commerce_lens.contracts.common import ArtifactReference, ContractBase, FailureDetail, MetricState, utc_now


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class ExecutionRecord(ContractBase):
    execution_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    plan_id: str | None = None
    plan_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    plan_node_id: str | None = None
    dataset_ref_ids: tuple[str, ...] = ()
    canonical_dataset_ref_ids: tuple[str, ...] = ()
    canonical_dataset_fingerprints: tuple[str, ...] = ()
    engine_version: str = Field(min_length=1)
    dependency_versions: dict[str, str] = Field(default_factory=dict)
    metric_refs: tuple[str, ...] = ()
    metric_definition_version: str | None = None
    period_refs: tuple[str, ...] = ()
    period_role: str | None = None
    population_refs: tuple[str, ...] = ()
    population_fingerprints: tuple[str, ...] = ()
    executor_id: str | None = None
    executor_version: str | None = None
    duckdb_version: str | None = None
    operation: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=utc_now)
    ended_at: datetime | None = None
    output_artifacts: tuple[ArtifactReference, ...] = ()
    result_ref: str | None = None
    status: ExecutionStatus
    failure_details: tuple[FailureDetail, ...] = ()


ScalarResultValue = str | int | float | Decimal | bool


class ExecutedResult(ContractBase):
    result_id: str = Field(min_length=1)
    execution_id: str = Field(min_length=1)
    metric_ref: str = Field(min_length=1)
    scope_ref: str = Field(min_length=1)
    period_ref: str | None = None
    value: ScalarResultValue | None = None
    metric_state: MetricState
    undefined_reason: str | None = None
    precision: str | None = None
    unit: str | None = None
    currency: str | None = None
    grouping_keys: dict[str, str] = Field(default_factory=dict)
    execution_status: ExecutionStatus
    failure_details: tuple[FailureDetail, ...] = ()

    @model_validator(mode="after")
    def validate_undefined_state(self) -> "ExecutedResult":
        if self.metric_state is MetricState.UNDEFINED and not self.undefined_reason:
            raise ValueError("Undefined metric state requires undefined_reason")
        return self
