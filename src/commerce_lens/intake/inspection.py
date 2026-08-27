"""Shared source inspection result structures."""

from __future__ import annotations

from enum import Enum

from pydantic import Field

from commerce_lens.contracts.common import ContractBase, FailureDetail, SourceType


class InspectionStatus(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    AMBIGUOUS = "ambiguous"
    FAILED = "failed"


class ColumnInspection(ContractBase):
    name: str = Field(min_length=1)
    position: int = Field(ge=0)
    declared_type: str | None = None
    observed_type: str | None = None
    nullable_observed: bool | None = None


class IntakeInspectionResult(ContractBase):
    source_type: SourceType
    status: InspectionStatus
    dataset_ref_id: str | None = None
    selected_sheet: str | None = None
    selected_table: str | None = None
    available_sheets: tuple[str, ...] = ()
    available_tables: tuple[str, ...] = ()
    columns: tuple[ColumnInspection, ...] = ()
    row_count: int | None = Field(default=None, ge=0)
    warnings: tuple[str, ...] = ()
    ambiguities: tuple[str, ...] = ()
    failure_detail: FailureDetail | None = None


def infer_observed_type(values: list[object]) -> tuple[str, bool]:
    """Return a conservative observed type hint and null observation."""
    non_empty: list[object] = []
    saw_null = False
    for value in values:
        if value is None or value == "":
            saw_null = True
        else:
            non_empty.append(value)
    if not non_empty:
        return "empty", saw_null
    hints = {_hint(value) for value in non_empty}
    if len(hints) == 1:
        return hints.pop(), saw_null
    numeric = {"integer", "decimal"}
    if hints <= numeric:
        return "decimal", saw_null
    return "mixed", saw_null


def _hint(value: object) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "decimal"
    text = str(value).strip()
    if text == "":
        return "empty"
    lowered = text.lower()
    if lowered in {"true", "false"}:
        return "boolean"
    try:
        int(text)
        return "integer"
    except ValueError:
        pass
    try:
        float(text)
        return "decimal"
    except ValueError:
        return "text"

