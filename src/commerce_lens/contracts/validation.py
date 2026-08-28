"""Validation structural contracts."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from commerce_lens.contracts.common import ArtifactReference, ContractBase, FailureDetail, MetricState, utc_now
from commerce_lens.contracts.execution import ScalarResultValue


class ValidationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"
    BLOCKED = "blocked"


class ValidationRecord(ContractBase):
    validation_id: str = Field(min_length=1)
    execution_id: str = Field(min_length=1)
    target_result_ref: str = Field(min_length=1)
    validation_rule_id: str = Field(min_length=1)
    validation_version: str = Field(min_length=1)
    result_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    metric_definition_version: str | None = None
    plan_id: str | None = None
    plan_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    plan_node_id: str | None = None
    canonical_dataset_ref_id: str | None = None
    canonical_dataset_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    population_ref: str | None = None
    population_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    period_ref: str | None = None
    period_role: str | None = None
    validator_id: str = Field(min_length=1)
    validator_version: str = Field(min_length=1)
    validation_operation: dict[str, Any] = Field(default_factory=dict)
    checks_performed: tuple[str, ...] = ()
    expected_value: ScalarResultValue | None = None
    expected_state: MetricState | None = None
    actual_value: ScalarResultValue | None = None
    actual_state: MetricState | None = None
    status: ValidationStatus
    observed: Any = None
    expected_constraint: str | None = None
    authoritative_precision: str | None = None
    failure_code: str | None = None
    failure_reason: str | None = None
    metric_ref: str | None = None
    started_at: datetime = Field(default_factory=utc_now)
    ended_at: datetime | None = None
    validated_at: datetime | None = None
    validated_result_ref: str | None = None
    validated_result_artifact_ref: ArtifactReference | None = None
    validation_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    failure_details: tuple[FailureDetail, ...] = ()

    @model_validator(mode="after")
    def validate_timestamp_order(self) -> "ValidationRecord":
        if self.ended_at is not None and self.started_at > self.ended_at:
            raise ValueError("ValidationRecord started_at must be before or equal to ended_at")
        if self.validated_at is not None and self.ended_at is not None and self.validated_at != self.ended_at:
            raise ValueError("ValidationRecord validated_at must match ended_at when both are present")
        return self


class ValidatedResult(ContractBase):
    validated_result_id: str = Field(min_length=1)
    validation_record_id: str = Field(min_length=1)
    execution_id: str = Field(min_length=1)
    executed_result_id: str = Field(min_length=1)
    required_validation_record_ids: tuple[str, ...] = Field(min_length=1)
    intended_use: str = Field(min_length=1)
    metric_ref: str = Field(min_length=1)
    metric_definition_version: str | None = None
    plan_id: str | None = None
    plan_node_id: str | None = None
    canonical_dataset_ref_id: str = Field(min_length=1)
    canonical_dataset_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    population_ref: str = Field(min_length=1)
    population_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    period_ref: str | None = None
    period_role: str | None = None
    result_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    validation_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    value: ScalarResultValue | None = None
    metric_state: MetricState
    undefined_reason: str | None = None
    precision: str | None = None
    precision_metadata: dict[str, Any] = Field(default_factory=dict)
    unit: str | None = None
    currency: str | None = None
    source_result_artifact_ref: ArtifactReference
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def require_validation_records(self) -> "ValidatedResult":
        if not self.required_validation_record_ids:
            raise ValueError("ValidatedResult requires validation record references")
        if self.validation_record_id not in self.required_validation_record_ids:
            raise ValueError("ValidatedResult must reference its governing ValidationRecord")
        if self.metric_state is MetricState.UNDEFINED and not self.undefined_reason:
            raise ValueError("Undefined ValidatedResult requires undefined_reason")
        return self
