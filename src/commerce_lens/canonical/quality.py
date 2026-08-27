"""Structured canonical Data Quality results."""

from __future__ import annotations

from enum import Enum

from pydantic import Field

from commerce_lens.contracts.common import ContractBase


class DataQualityStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"


class DataQualityConsequence(str, Enum):
    PASS = "pass"
    QUALIFICATION = "qualification"
    BLOCKING = "blocking"


class DataQualityCheckResult(ContractBase):
    check_id: str = Field(min_length=1)
    target: str = Field(min_length=1)
    status: DataQualityStatus
    governing_ref: str = Field(min_length=1)
    consequence: DataQualityConsequence
    affected_metric_refs: tuple[str, ...] = ()
    reason: str = Field(min_length=1)


def passed(check_id: str, target: str, governing_ref: str, reason: str) -> DataQualityCheckResult:
    return DataQualityCheckResult(
        check_id=check_id,
        target=target,
        status=DataQualityStatus.PASS,
        governing_ref=governing_ref,
        consequence=DataQualityConsequence.PASS,
        reason=reason,
    )


def blocking(
    check_id: str,
    target: str,
    governing_ref: str,
    reason: str,
    *,
    affected_metric_refs: tuple[str, ...] = (),
) -> DataQualityCheckResult:
    return DataQualityCheckResult(
        check_id=check_id,
        target=target,
        status=DataQualityStatus.FAIL,
        governing_ref=governing_ref,
        consequence=DataQualityConsequence.BLOCKING,
        affected_metric_refs=affected_metric_refs,
        reason=reason,
    )


def qualification(
    check_id: str,
    target: str,
    governing_ref: str,
    reason: str,
    *,
    affected_metric_refs: tuple[str, ...] = (),
) -> DataQualityCheckResult:
    return DataQualityCheckResult(
        check_id=check_id,
        target=target,
        status=DataQualityStatus.FAIL,
        governing_ref=governing_ref,
        consequence=DataQualityConsequence.QUALIFICATION,
        affected_metric_refs=affected_metric_refs,
        reason=reason,
    )
