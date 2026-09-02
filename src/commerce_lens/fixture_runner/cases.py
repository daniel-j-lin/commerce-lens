"""Strict P9 physical fixture case loading."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


EXPECTED_CASE_IDS = (
    "P9-CONF-POS-001",
    "P9-CONF-REVCHG-001",
    "P9-CONF-SUFF-MISSING-REVENUE-001",
    "P9-CONF-SUFF-MIXED-CURRENCY-001",
    "P9-CONF-AOV-UNDEFINED-001",
    "P9-CONF-VAL-REVCHG-WRONG-VALUE-001",
    "P9-CONF-CLAIM-DIAGNOSTIC-REFUSAL-001",
    "P9-CONF-TAMPER-CROSS-REQUEST-001",
)

DEFAULT_CASES_ROOT = Path("tests/fixtures/p9/cases")


class FixtureCaseError(ValueError):
    """Raised when P9 fixture case authority fails closed."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PeriodSpec(StrictModel):
    period_id: Literal["baseline", "comparison"]
    label: str = Field(min_length=1)
    start_date: date
    end_date: date
    date_convention_ref: str = Field(min_length=1)


class RequestSpec(StrictModel):
    canonical_business_question_id: str = Field(min_length=1)
    analytical_request_class: str = Field(min_length=1)
    metrics: tuple[str, ...] = Field(min_length=1)
    baseline_period: PeriodSpec
    comparison_period: PeriodSpec

    @model_validator(mode="after")
    def validate_distinct_periods(self) -> "RequestSpec":
        if self.baseline_period.period_id != "baseline":
            raise ValueError("baseline_period must use period_id=baseline")
        if self.comparison_period.period_id != "comparison":
            raise ValueError("comparison_period must use period_id=comparison")
        return self


class SetupContextSpec(StrictModel):
    name: str = Field(min_length=1)
    rows: tuple[dict[str, str], ...] = Field(min_length=1)


class ExpectedValidatedResult(StrictModel):
    metric_ref: str = Field(min_length=1)
    period_ref: str | None = None
    period_role: str | None = None
    metric_state: str = Field(min_length=1)
    value: Decimal | int | None = None
    undefined_reason: str | None = None
    evidence_status: str | None = None
    evidence_role: str | None = None


class ExpectedClaim(StrictModel):
    metric_ref: str = Field(min_length=1)
    claim_type: str = Field(min_length=1)
    claim_state: str = Field(min_length=1)
    failure_code: str | None = None
    period_ref: str | None = None
    period_role: str | None = None


class ExpectedCaseOutcome(StrictModel):
    data_sufficiency_state: str = Field(min_length=1)
    run_status: str | None = None
    execution_disposition: Literal["completed", "not_started", "hostile_submitted"]
    validation_disposition: Literal["passed", "failed", "not_started"]
    expected_validated_results: tuple[ExpectedValidatedResult, ...] = ()
    expected_claims: tuple[ExpectedClaim, ...] = ()
    failure_code: str | None = None
    no_executed_results: bool = False
    no_validated_results: bool = False
    no_admissible_evidence: bool = False
    no_claim_decision: bool = False


class CaseManifest(StrictModel):
    case_id: str = Field(min_length=1)
    case_class: Literal["current-authority conformance"]
    case_level: Literal["physical-input", "harness-level"]
    frozen_fixture_id: Literal["NONE"]
    authority_reference: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    source_input_path: str | None
    public_operation: str = Field(min_length=1)
    request: RequestSpec
    expected: ExpectedCaseOutcome
    setup_contexts: tuple[SetupContextSpec, ...] = ()
    prohibited_material_output: tuple[str, ...] = ()
    governing_authority: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_case_contract(self) -> "CaseManifest":
        if tuple(self.request.metrics) != tuple(dict.fromkeys(self.request.metrics)):
            raise ValueError("request metrics must be unique and deterministic")
        if self.case_level == "physical-input":
            if self.source_input_path != "input.csv":
                raise ValueError("physical-input cases must declare source_input_path=input.csv")
            if self.setup_contexts:
                raise ValueError("physical-input cases must not declare harness setup_contexts")
        if self.case_level == "harness-level":
            if self.source_input_path is not None:
                raise ValueError("harness-level cases must declare source_input_path: null")
            if not self.setup_contexts and self.case_id != "P9-CONF-VAL-REVCHG-WRONG-VALUE-001":
                raise ValueError("harness-level claim cases require deterministic setup_contexts")
        return self


class FixtureCase(StrictModel):
    case_dir: Path
    manifest: CaseManifest

    @property
    def case_id(self) -> str:
        return self.manifest.case_id

    @property
    def input_path(self) -> Path | None:
        if self.manifest.source_input_path is None:
            return None
        return self.case_dir / self.manifest.source_input_path


def load_case(case_dir: str | Path) -> FixtureCase:
    """Load one P9 fixture case from a strict safe-YAML manifest."""
    case_path = Path(case_dir)
    manifest_path = case_path / "manifest.yaml"
    if not manifest_path.is_file():
        raise FixtureCaseError(f"missing P9 manifest: {manifest_path}")
    try:
        payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise FixtureCaseError(f"P9 manifest is not safe-loadable YAML: {manifest_path}") from exc
    if not isinstance(payload, dict):
        raise FixtureCaseError(f"P9 manifest must be a mapping: {manifest_path}")
    try:
        manifest = CaseManifest.model_validate(payload)
    except Exception as exc:
        raise FixtureCaseError(f"P9 manifest schema invalid for {manifest_path}: {exc}") from exc
    if manifest.case_id != case_path.name:
        raise FixtureCaseError(f"P9 manifest case_id {manifest.case_id!r} does not match directory {case_path.name!r}")
    if manifest.case_id not in EXPECTED_CASE_IDS:
        raise FixtureCaseError(f"unknown P9 case_id: {manifest.case_id}")
    case = FixtureCase(case_dir=case_path, manifest=manifest)
    if manifest.case_level == "physical-input":
        input_path = case.input_path
        if input_path is None or not input_path.is_file():
            raise FixtureCaseError(f"missing physical P9 input.csv for {manifest.case_id}")
    return case


def discover_cases(cases_root: str | Path = DEFAULT_CASES_ROOT) -> tuple[FixtureCase, ...]:
    """Discover exactly the approved P9 initial case inventory."""
    root = Path(cases_root)
    if not root.is_dir():
        raise FixtureCaseError(f"P9 cases root does not exist: {root}")
    case_dirs = tuple(path for path in root.iterdir() if path.is_dir())
    unknown_dirs = sorted(path.name for path in case_dirs if path.name not in EXPECTED_CASE_IDS)
    if unknown_dirs:
        raise FixtureCaseError(f"unknown P9 case directorie(s): {', '.join(unknown_dirs)}")
    missing_dirs = [case_id for case_id in EXPECTED_CASE_IDS if not (root / case_id).is_dir()]
    if missing_dirs:
        raise FixtureCaseError(f"missing P9 case directorie(s): {', '.join(missing_dirs)}")
    loaded = tuple(load_case(root / case_id) for case_id in EXPECTED_CASE_IDS)
    ids = [case.case_id for case in loaded]
    duplicates = sorted(case_id for case_id in set(ids) if ids.count(case_id) > 1)
    if duplicates:
        raise FixtureCaseError(f"duplicate P9 case ID(s): {', '.join(duplicates)}")
    if tuple(ids) != EXPECTED_CASE_IDS:
        raise FixtureCaseError("P9 case inventory order or identity diverges from approved authority")
    return loaded
