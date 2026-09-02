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

DataSufficiencyValue = Literal["sufficient", "data_quality_failure"]
RunStatusValue = Literal["completed", "blocked", "partially_completed"]
MetricStateValue = Literal["Valid", "Undefined", "Inadmissible"]
EvidenceStatusValue = Literal["passed", "failed"]
EvidenceRoleValue = Literal["metric_value", "metric_state"]
ClaimTypeValue = Literal["descriptive", "diagnostic"]
ClaimStateValue = Literal["Admissible", "Inadmissible"]
PublicOperationValue = Literal[
    "run_analysis(...)",
    "run_analysis(...), then evaluate_claim(...)",
    "evaluate_claim(...)",
    "ONE hostile direct-validator harness exception",
]
FinalDispositionValue = Literal[
    "completed_admissible",
    "blocked_insufficient",
    "validation_failed",
    "claim_inadmissible",
]

_FIXED_HOSTILE_DECIMALS = {
    "baseline_revenue": Decimal("100.00"),
    "comparison_revenue": Decimal("120.00"),
    "authoritative_revenue_change": Decimal("20.00"),
    "submitted_revenue_change": Decimal("21.00"),
}


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


class SetupRow(StrictModel):
    order_id: str = ""
    order_line_id: str = ""
    order_date: str = ""
    product_id: str = ""
    product_name: str = ""
    category_id: str = ""
    category_name: str = ""
    quantity: str = ""
    line_revenue: str = ""
    currency: str = ""
    unit_price: str = ""
    eligibility_status: str = ""


class SetupContextSpec(StrictModel):
    name: str = Field(min_length=1)
    rows: tuple[SetupRow, ...] = Field(min_length=1)


class ExpectedMetricResult(StrictModel):
    metric_ref: str = Field(min_length=1)
    metric_state: MetricStateValue


class ExpectedValidatedResult(StrictModel):
    metric_ref: str = Field(min_length=1)
    period_ref: str | None = None
    period_role: str | None = None
    metric_state: MetricStateValue
    value: Decimal | int | None = None
    undefined_reason: str | None = None
    evidence_status: EvidenceStatusValue | None = None
    evidence_role: EvidenceRoleValue | None = None


class ExpectedClaim(StrictModel):
    metric_ref: str = Field(min_length=1)
    claim_type: ClaimTypeValue
    claim_state: ClaimStateValue
    failure_code: str | None = None
    period_ref: str | None = None
    period_role: str | None = None


class HostileRevenueChangeAuthority(StrictModel):
    baseline_revenue: Decimal
    comparison_revenue: Decimal
    authoritative_revenue_change: Decimal
    submitted_revenue_change: Decimal
    validation_rule_id: Literal["validation:revenue_change_from_validated_revenues"]
    expected_metric_state: Literal["Inadmissible"]
    failure_code: Literal["value_mismatch"]

    @model_validator(mode="after")
    def validate_fixed_hostile_values(self) -> "HostileRevenueChangeAuthority":
        for field_name, expected in _FIXED_HOSTILE_DECIMALS.items():
            value = getattr(self, field_name)
            if value != expected or value.as_tuple().exponent != expected.as_tuple().exponent:
                raise ValueError(f"{field_name} must be fixed P9 hostile authority {expected}")
        return self


def validate_fixed_hostile_authority(authority: HostileRevenueChangeAuthority) -> HostileRevenueChangeAuthority:
    """Revalidate the single fixed P9 hostile authority before use."""
    return HostileRevenueChangeAuthority.model_validate(authority.model_dump())


class ExpectedCaseOutcome(StrictModel):
    data_sufficiency_state: DataSufficiencyValue
    run_status: RunStatusValue | None = None
    execution_disposition: Literal["completed", "not_started", "hostile_submitted"]
    validation_disposition: Literal["passed", "failed", "not_started"]
    final_disposition: FinalDispositionValue
    expected_metric_results: tuple[ExpectedMetricResult, ...] = ()
    expected_validated_results: tuple[ExpectedValidatedResult, ...] = ()
    expected_claims: tuple[ExpectedClaim, ...] = ()
    hostile_revenue_change: HostileRevenueChangeAuthority | None = None
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
    public_operation: PublicOperationValue
    request: RequestSpec
    expected: ExpectedCaseOutcome
    setup_contexts: tuple[SetupContextSpec, ...] = ()
    prohibited_material_output: tuple[str, ...] = ()
    governing_authority: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_case_contract(self) -> "CaseManifest":
        if tuple(self.request.metrics) != tuple(dict.fromkeys(self.request.metrics)):
            raise ValueError("request metrics must be unique and deterministic")
        expected_operation = {
            "P9-CONF-POS-001": "run_analysis(...), then evaluate_claim(...)",
            "P9-CONF-REVCHG-001": "run_analysis(...), then evaluate_claim(...)",
            "P9-CONF-SUFF-MISSING-REVENUE-001": "run_analysis(...)",
            "P9-CONF-SUFF-MIXED-CURRENCY-001": "run_analysis(...)",
            "P9-CONF-AOV-UNDEFINED-001": "run_analysis(...), then evaluate_claim(...)",
            "P9-CONF-VAL-REVCHG-WRONG-VALUE-001": "ONE hostile direct-validator harness exception",
            "P9-CONF-CLAIM-DIAGNOSTIC-REFUSAL-001": "evaluate_claim(...)",
            "P9-CONF-TAMPER-CROSS-REQUEST-001": "evaluate_claim(...)",
        }.get(self.case_id)
        if expected_operation is not None and self.public_operation != expected_operation:
            raise ValueError(f"public_operation for {self.case_id} must be {expected_operation}")
        if self.case_id == "P9-CONF-VAL-REVCHG-WRONG-VALUE-001":
            if self.expected.hostile_revenue_change is None:
                raise ValueError("hostile Revenue Change case requires hostile_revenue_change authority")
            if self.request.metrics != ("revenue_change",):
                raise ValueError("hostile Revenue Change case must remain fixed to revenue_change")
        elif self.expected.hostile_revenue_change is not None:
            raise ValueError("hostile_revenue_change authority is only valid for the hostile Revenue Change case")
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
