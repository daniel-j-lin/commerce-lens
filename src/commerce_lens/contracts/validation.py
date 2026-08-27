"""Validation structural contracts."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from commerce_lens.contracts.common import ContractBase, FailureDetail, Qualification, Limitation, utc_now


class ValidationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"
    BLOCKED = "blocked"


class ValidationRecord(ContractBase):
    validation_id: str = Field(min_length=1)
    target_result_ref: str = Field(min_length=1)
    validation_rule_id: str = Field(min_length=1)
    validation_version: str = Field(min_length=1)
    status: ValidationStatus
    observed: Any = None
    expected_constraint: str | None = None
    authoritative_precision: str | None = None
    failure_reason: str | None = None
    metric_ref: str | None = None
    validated_at: datetime = Field(default_factory=utc_now)
    failure_details: tuple[FailureDetail, ...] = ()


class ValidatedResult(ContractBase):
    validated_result_id: str = Field(min_length=1)
    executed_result_id: str = Field(min_length=1)
    required_validation_record_ids: tuple[str, ...] = Field(min_length=1)
    intended_use: str = Field(min_length=1)
    qualifications: tuple[Qualification, ...] = ()
    limitations: tuple[Limitation, ...] = ()

    @model_validator(mode="after")
    def require_validation_records(self) -> "ValidatedResult":
        if not self.required_validation_record_ids:
            raise ValueError("ValidatedResult requires validation record references")
        return self

