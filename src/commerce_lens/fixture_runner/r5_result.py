"""Single structured source for R5 machine- and human-readable reports."""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from commerce_lens.fixture_runner.r5_manifest import ExecutionMode, StrictModel


class HarnessResultStatus(str, Enum):
    PASS = "PASS"
    NON_CONFORMING = "NON_CONFORMING"
    FIXTURE_INVALID = "FIXTURE_INVALID"
    DEPENDENCY_BLOCKED = "DEPENDENCY_BLOCKED"


class CapabilityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_CHECKED = "NOT_CHECKED"
    EXECUTION_FAILED = "EXECUTION_FAILED"


class MaterialMismatch(StrictModel):
    field: str = Field(min_length=1)
    expected: Any = None
    actual: Any = None


class HarnessResult(StrictModel):
    fixture_id: str = Field(min_length=1)
    semantic_family: str | None = None
    execution_mode: ExecutionMode | None = None
    adapter_id: str | None = None
    capability_status: CapabilityStatus
    status: HarnessResultStatus
    expected_final_disposition: str | None = None
    actual_final_disposition: str | None = None
    expected_first_blocker: Any = None
    actual_first_blocker: Any = None
    expected_reached_stages: tuple[str, ...] = ()
    actual_reached_stages: tuple[str, ...] = ()
    mismatches: tuple[MaterialMismatch, ...] = ()
    artifact_evidence_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_status(self) -> "HarnessResult":
        if self.status is HarnessResultStatus.PASS:
            if self.capability_status is not CapabilityStatus.AVAILABLE or self.mismatches:
                raise ValueError("PASS requires available subject-under-test and zero mismatches")
            if self.actual_final_disposition is None:
                raise ValueError("PASS requires an actual subject-under-test result")
        if self.status is HarnessResultStatus.DEPENDENCY_BLOCKED:
            if self.capability_status is not CapabilityStatus.UNAVAILABLE:
                raise ValueError("DEPENDENCY_BLOCKED requires unavailable capability")
            if self.actual_final_disposition is not None:
                raise ValueError("DEPENDENCY_BLOCKED cannot carry fabricated actual disposition")
        return self

    def to_json(self) -> str:
        return json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def to_text(self) -> str:
        lines = [
            f"fixture: {self.fixture_id}",
            f"family: {self.semantic_family or '-'}",
            f"mode: {self.execution_mode.value if self.execution_mode else '-'}",
            f"adapter: {self.adapter_id or '-'}",
            f"capability: {self.capability_status.value}",
            f"result: {self.status.value}",
            f"expected disposition: {self.expected_final_disposition or '-'}",
            f"actual disposition: {self.actual_final_disposition or '-'}",
            f"expected first blocker: {_display(self.expected_first_blocker)}",
            f"actual first blocker: {_display(self.actual_first_blocker)}",
        ]
        for mismatch in self.mismatches:
            lines.append(
                f"mismatch {mismatch.field}: expected={_display(mismatch.expected)} actual={_display(mismatch.actual)}"
            )
        return "\n".join(lines)


class HarnessSuiteReport(StrictModel):
    semantic_active: int = Field(ge=0)
    semantic_deferred: int = Field(ge=0)
    physical_implemented: int = Field(ge=0)
    executable: int = Field(ge=0)
    dependency_blocked: int = Field(ge=0)
    passed: int = Field(ge=0)
    non_conforming: int = Field(ge=0)
    fixture_invalid: int = Field(ge=0)
    results: tuple[HarnessResult, ...] = ()

    @model_validator(mode="after")
    def deterministic_order(self) -> "HarnessSuiteReport":
        ids = [item.fixture_id for item in self.results]
        if ids != sorted(ids):
            raise ValueError("suite results must be sorted by fixture_id")
        return self

    def to_json(self) -> str:
        return json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _display(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
