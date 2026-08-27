"""Shared structural contract types."""

from __future__ import annotations

from datetime import UTC, date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


CONTRACT_VERSION = "1.0"


def utc_now() -> datetime:
    """Return a timezone-aware timestamp for contract records."""
    return datetime.now(UTC)


class ContractBase(BaseModel):
    """Base model for host-independent JSON-compatible contracts."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class SourceType(str, Enum):
    CSV = "csv"
    EXCEL_XLSX = "excel_xlsx"
    SQLITE = "sqlite"


class RunStatus(str, Enum):
    CLARIFICATION_REQUIRED = "clarification_required"
    READY_FOR_EXECUTION = "ready_for_execution"
    BLOCKED = "blocked"
    EXECUTING = "executing"
    EXECUTION_FAILED = "execution_failed"
    VALIDATION_FAILED = "validation_failed"
    PARTIALLY_COMPLETED = "partially_completed"
    COMPLETED = "completed"


class MetricState(str, Enum):
    VALID = "Valid"
    QUALIFIED = "Qualified"
    UNDEFINED = "Undefined"
    INADMISSIBLE = "Inadmissible"


class ClaimState(str, Enum):
    ADMISSIBLE = "Admissible"
    QUALIFIED_ADMISSIBLE = "Qualified Admissible"
    INADMISSIBLE = "Inadmissible"


class ClaimType(str, Enum):
    DESCRIPTIVE = "descriptive"
    DIAGNOSTIC = "diagnostic"
    PREDICTIVE = "predictive"
    CAUSAL = "causal"
    PRESCRIPTIVE = "prescriptive"


class FailureStage(str, Enum):
    REQUEST = "request"
    INTAKE = "intake"
    SUFFICIENCY = "sufficiency"
    PLANNING = "planning"
    EXECUTION = "execution"
    VALIDATION = "validation"
    EVIDENCE = "evidence"
    CLAIM_ADMISSIBILITY = "claim_admissibility"
    PERSISTENCE = "persistence"


class FailureDetail(ContractBase):
    stage: FailureStage
    reason: str = Field(min_length=1)
    target_ref: str | None = None
    governing_ref: str | None = None
    dependency_scope: str | None = None
    independent_chains_may_continue: bool = False


class ArtifactReference(ContractBase):
    artifact_id: str = Field(min_length=1)
    path: str = Field(min_length=1)
    fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    media_type: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)


class PeriodDefinition(ContractBase):
    period_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    start_date: date
    end_date: date
    date_convention_ref: str

    @field_validator("end_date")
    @classmethod
    def end_not_before_start(cls, value: date, info: Any) -> date:
        start = info.data.get("start_date")
        if start is not None and value < start:
            raise ValueError("end_date must be on or after start_date")
        return value


SUPPORTED_SCOPE_FILTER_FIELDS = frozenset(
    {
        "order_id",
        "order_line_id",
        "order_date",
        "product_id",
        "product_name",
        "category_id",
        "category_name",
        "currency",
        "eligibility_status",
    }
)
SUPPORTED_SCOPE_FILTER_OPERATORS = frozenset({"equals"})


class ScopeFilter(ContractBase):
    field: str = Field(min_length=1)
    operator: str = Field(min_length=1)
    value: str | int | float | bool

    @model_validator(mode="after")
    def validate_supported_scope_filter(self) -> "ScopeFilter":
        if self.field not in SUPPORTED_SCOPE_FILTER_FIELDS:
            raise ValueError(f"unsupported governed scope filter field: {self.field}")
        if self.operator not in SUPPORTED_SCOPE_FILTER_OPERATORS:
            raise ValueError(f"unsupported governed scope filter operator: {self.operator}")
        return self


class ScopeDefinition(ContractBase):
    scope_id: str = Field(min_length=1)
    population_ref: str | None = None
    filters: tuple[ScopeFilter, ...] = ()
    description: str | None = None


class GroupingDimension(str, Enum):
    NONE = "none"
    PRODUCT = "product"
    CATEGORY = "category"
    PRODUCT_AND_CATEGORY = "product_and_category"


class Assumption(ContractBase):
    assumption_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    authorized_by: str | None = None


class Qualification(ContractBase):
    qualification_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    affected_ref: str | None = None


class Limitation(ContractBase):
    limitation_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    affected_ref: str | None = None
    blocking: bool = False


class EvidenceRequirement(ContractBase):
    requirement_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    metric_ref: str | None = None
    claim_type: ClaimType | None = None


class AvailableEvidence(ContractBase):
    evidence_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    source_ref: str | None = None
    satisfies_requirement_ids: tuple[str, ...] = ()
