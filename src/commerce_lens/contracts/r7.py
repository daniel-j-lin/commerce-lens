"""Immutable private R7 diagnostic execution contracts."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Literal, Mapping, Self

from pydantic import Field, field_validator, model_validator

from commerce_lens.contracts.common import ContractBase
from commerce_lens.contracts.diagnostic import AlternativeExplanationState, AnalyticalOutcome, AuthorityBinding
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, stable_content_id


SHA256_PATTERN = r"^[0-9a-f]{64}$"


class R7AuthorityReference(ContractBase):
    authority_id: str = Field(min_length=1)
    authority_version: str = Field(min_length=1)
    authority_fingerprint: str = Field(pattern=SHA256_PATTERN)


class DiagnosticMethodDefinition(ContractBase):
    method_id: str
    method_version: str
    method_fingerprint: str = Field(pattern=SHA256_PATTERN)
    family_id: Literal["product_composition_association"]
    family_version: str
    family_fingerprint: str = Field(pattern=SHA256_PATTERN)
    intended_use: Literal["diagnostic"] = "diagnostic"
    observation_unit: Literal["full_iso_calendar_week"] = "full_iso_calendar_week"
    predictor: str
    outcome: str
    association_measure: Literal["spearman_average_rank"] = "spearman_average_rank"
    required_variables: tuple[str, ...]
    required_source_class: Literal["GOVERNED_INTERNAL"] = "GOVERNED_INTERNAL"
    fixed_parameters: Mapping[str, Any]
    maximum_permitted_meaning: str
    prohibited_meanings: tuple[str, ...]
    limitations: tuple[str, ...]
    support_criterion_ref: R7AuthorityReference
    validation_profile_ref: R7AuthorityReference
    implementation_ref: R7AuthorityReference

    @model_validator(mode="after")
    def authenticate(self) -> Self:
        if self.method_fingerprint != method_definition_fingerprint(self):
            raise ValueError("method_fingerprint mismatch")
        return self


class DiagnosticSupportCriterionDefinition(ContractBase):
    criterion_id: str
    criterion_version: str
    criterion_fingerprint: str = Field(pattern=SHA256_PATTERN)
    support_maximum: float = -0.5
    contradiction_minimum: float = 0.5
    inconclusive_reasons: tuple[str, ...]

    @model_validator(mode="after")
    def authenticate(self) -> Self:
        if self.criterion_fingerprint != support_criterion_fingerprint(self):
            raise ValueError("criterion_fingerprint mismatch")
        return self


class DiagnosticValidationProfile(ContractBase):
    profile_id: str
    profile_version: str
    profile_fingerprint: str = Field(pattern=SHA256_PATTERN)
    required_checks: tuple[str, ...]

    @model_validator(mode="after")
    def authenticate(self) -> Self:
        if self.profile_fingerprint != validation_profile_fingerprint(self):
            raise ValueError("profile_fingerprint mismatch")
        return self


class DiagnosticMethodImplementationBinding(ContractBase):
    implementation_id: str
    implementation_version: str
    implementation_fingerprint: str = Field(pattern=SHA256_PATTERN)
    runtime: str
    week_convention: str
    numeric_convention: str
    dependencies: tuple[str, ...]

    @model_validator(mode="after")
    def authenticate(self) -> Self:
        if self.implementation_fingerprint != implementation_binding_fingerprint(self):
            raise ValueError("implementation_fingerprint mismatch")
        return self


class DiagnosticEvidenceInputBinding(ContractBase):
    requirement_judgment_ref: str
    evidence_ref: str
    evidence_fingerprint: str = Field(pattern=SHA256_PATTERN)
    evidence_assessment_ref: str
    evidence_assessment_fingerprint: str = Field(pattern=SHA256_PATTERN)
    diagnostic_admission_authority: AuthorityBinding
    admission_state: Literal["DIAGNOSTIC_ADMITTED"]
    fitness_state: Literal["PASSED"]
    source_class: Literal["GOVERNED_INTERNAL"]
    scope_ref: str
    period_refs: tuple[str, ...]
    population_refs: tuple[str, ...]
    metric_refs: tuple[str, ...]
    variable_refs: tuple[str, ...]


class DiagnosticEvidenceInputSet(ContractBase):
    evidence_input_set_id: str
    schema_version: str = "1.0.0"
    evidence_input_set_fingerprint: str = Field(pattern=SHA256_PATTERN)
    diagnostic_proposition_ref: str
    diagnostic_proposition_fingerprint: str = Field(pattern=SHA256_PATTERN)
    bindings: tuple[DiagnosticEvidenceInputBinding, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def authenticate(self) -> Self:
        expected = evidence_input_set_fingerprint(self)
        if self.evidence_input_set_fingerprint != expected:
            raise ValueError("evidence_input_set_fingerprint mismatch")
        if self.evidence_input_set_id != stable_content_id("r7evid", expected):
            raise ValueError("evidence_input_set_id mismatch")
        return self


class DiagnosticTestRequest(ContractBase):
    test_request_id: str
    schema_version: str = "1.0.0"
    request_fingerprint: str = Field(pattern=SHA256_PATTERN)
    handoff_ref: str
    handoff_fingerprint: str = Field(pattern=SHA256_PATTERN)
    governed_hypothesis_ref: str
    governed_hypothesis_fingerprint: str = Field(pattern=SHA256_PATTERN)
    diagnostic_proposition_ref: str
    diagnostic_proposition_fingerprint: str = Field(pattern=SHA256_PATTERN)
    pretest_evaluation_ref: str
    pretest_evaluation_fingerprint: str = Field(pattern=SHA256_PATTERN)
    resolved_profile_ref: str
    resolved_profile_fingerprint: str = Field(pattern=SHA256_PATTERN)
    requirement_judgment_bundle_ref: str
    requirement_judgment_bundle_fingerprint: str = Field(pattern=SHA256_PATTERN)
    method: R7AuthorityReference
    support_criterion: R7AuthorityReference
    validation_profile: R7AuthorityReference
    implementation: R7AuthorityReference
    evidence_input_set_ref: str
    evidence_input_set_fingerprint: str = Field(pattern=SHA256_PATTERN)
    canonical_dataset_ref: str
    canonical_dataset_fingerprint: str = Field(pattern=SHA256_PATTERN)
    scope_ref: str
    baseline_period_ref: str
    comparison_period_ref: str
    baseline_start: date
    baseline_end: date
    comparison_start: date
    comparison_end: date
    baseline_population_ref: str
    baseline_population_fingerprint: str = Field(pattern=SHA256_PATTERN)
    comparison_population_ref: str
    comparison_population_fingerprint: str = Field(pattern=SHA256_PATTERN)
    metric_refs: tuple[str, ...]
    variable_refs: tuple[str, ...]
    normalized_parameters: Mapping[str, Any]
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        return value

    @model_validator(mode="after")
    def authenticate(self) -> Self:
        expected = diagnostic_test_request_fingerprint(self)
        if self.request_fingerprint != expected:
            raise ValueError("request_fingerprint mismatch")
        if self.test_request_id != stable_content_id("r7req", expected):
            raise ValueError("test_request_id mismatch")
        return self


class R7ExecutionStatus(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class R7ValidationStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"


class R7EvaluationState(str, Enum):
    VALIDATED_OUTCOME = "VALIDATED_OUTCOME"
    INCONCLUSIVE = "INCONCLUSIVE"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"


class ExcludedWeeklyObservation(ContractBase):
    week_id: str
    period_role: Literal["BASELINE", "COMPARISON"]
    reason: str


class WeeklyDiagnosticObservation(ContractBase):
    week_id: str
    week_start: date
    week_end: date
    period_role: Literal["BASELINE", "COMPARISON"]
    product_set_fingerprint: str = Field(pattern=SHA256_PATTERN)
    active_product_count: int = Field(gt=0)
    jaccard_distance: float = Field(ge=0.0, le=1.0)
    weekly_revenue: Decimal
    revenue_deviation: Decimal
    distance_rank: float = Field(gt=0.0)
    revenue_deviation_rank: float = Field(gt=0.0)


class DiagnosticExecutionRecord(ContractBase):
    execution_event_id: str
    test_request_ref: str
    request_fingerprint: str = Field(pattern=SHA256_PATTERN)
    method: R7AuthorityReference
    implementation: R7AuthorityReference
    started_at: datetime
    ended_at: datetime
    status: R7ExecutionStatus
    result_ref: str | None = None
    failure_code: str | None = None
    failure_reason: str | None = None

    @model_validator(mode="after")
    def valid_status(self) -> Self:
        if self.started_at > self.ended_at:
            raise ValueError("execution timestamps out of order")
        if self.status is R7ExecutionStatus.COMPLETED and not self.result_ref:
            raise ValueError("completed execution requires result_ref")
        if self.status is R7ExecutionStatus.FAILED and not self.failure_code:
            raise ValueError("failed execution requires failure_code")
        return self


class ExecutedDiagnosticResult(ContractBase):
    executed_result_id: str
    execution_event_id: str
    test_request_ref: str
    request_fingerprint: str = Field(pattern=SHA256_PATTERN)
    method: R7AuthorityReference
    support_criterion: R7AuthorityReference
    validation_profile: R7AuthorityReference
    implementation: R7AuthorityReference
    baseline_product_set_fingerprint: str = Field(pattern=SHA256_PATTERN)
    baseline_product_count: int = Field(gt=0)
    observations: tuple[WeeklyDiagnosticObservation, ...]
    excluded_observations: tuple[ExcludedWeeklyObservation, ...] = ()
    baseline_week_count: int = Field(ge=0)
    comparison_week_count: int = Field(ge=0)
    baseline_weekly_revenue_reference: Decimal | None
    spearman_rho: float | None
    inconclusive_reasons: tuple[str, ...] = ()
    result_fingerprint: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def authenticate(self) -> Self:
        if self.result_fingerprint != executed_result_fingerprint(self):
            raise ValueError("result_fingerprint mismatch")
        return self


class DiagnosticValidationCheck(ContractBase):
    check_id: str
    passed: bool
    failure_code: str | None = None


class DiagnosticValidationRecord(ContractBase):
    validation_event_id: str
    executed_result_ref: str
    executed_result_fingerprint: str = Field(pattern=SHA256_PATTERN)
    validation_profile: R7AuthorityReference
    checks: tuple[DiagnosticValidationCheck, ...] = Field(min_length=1)
    status: R7ValidationStatus
    validated_result_ref: str | None = None
    started_at: datetime
    ended_at: datetime
    validation_fingerprint: str = Field(pattern=SHA256_PATTERN)


class ValidatedDiagnosticResult(ContractBase):
    validated_result_id: str
    validation_event_id: str
    execution_event_id: str
    executed_result_ref: str
    result_fingerprint: str = Field(pattern=SHA256_PATTERN)
    validation_fingerprint: str = Field(pattern=SHA256_PATTERN)
    test_request_ref: str
    method: R7AuthorityReference
    support_criterion: R7AuthorityReference
    validation_profile: R7AuthorityReference
    baseline_week_count: int
    comparison_week_count: int
    spearman_rho: float | None
    inconclusive_reasons: tuple[str, ...]


class PostTestDiagnosticEvaluation(ContractBase):
    evaluation_event_id: str
    schema_version: str = "1.0.0"
    evaluation_fingerprint: str = Field(pattern=SHA256_PATTERN)
    diagnostic_proposition_ref: str
    diagnostic_proposition_fingerprint: str = Field(pattern=SHA256_PATTERN)
    pretest_evaluation_ref: str
    pretest_evaluation_fingerprint: str = Field(pattern=SHA256_PATTERN)
    handoff_ref: str
    handoff_fingerprint: str = Field(pattern=SHA256_PATTERN)
    test_request_ref: str
    request_fingerprint: str = Field(pattern=SHA256_PATTERN)
    execution_event_ref: str
    validation_event_ref: str
    validated_result_ref: str | None
    method: R7AuthorityReference
    support_criterion: R7AuthorityReference
    evaluation_state: R7EvaluationState
    controlling_reason: str
    analytical_outcome: AnalyticalOutcome
    alternative_explanation_state: Literal[AlternativeExplanationState.NOT_COMPLETED] = AlternativeExplanationState.NOT_COMPLETED
    finalized_at: datetime

    @model_validator(mode="after")
    def authenticate(self) -> Self:
        if self.alternative_explanation_state is not AlternativeExplanationState.NOT_COMPLETED:
            raise ValueError("R7 cannot complete alternative explanations")
        if self.evaluation_state is not R7EvaluationState.VALIDATED_OUTCOME and self.analytical_outcome is not AnalyticalOutcome.NOT_EVALUATED:
            raise ValueError("non-validated R7 state must remain NOT_EVALUATED")
        if self.evaluation_fingerprint != posttest_evaluation_fingerprint(self):
            raise ValueError("evaluation_fingerprint mismatch")
        return self


def _json(value: Any) -> Any:
    if isinstance(value, ContractBase):
        return value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return {key: _json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def _data(value: ContractBase | Mapping[str, Any]) -> dict[str, Any]:
    return dict(_json(value))


def method_definition_fingerprint(value: DiagnosticMethodDefinition | Mapping[str, Any]) -> str:
    data = _data(value); data.pop("method_fingerprint", None)
    return canonical_json_fingerprint(data)


def support_criterion_fingerprint(value: DiagnosticSupportCriterionDefinition | Mapping[str, Any]) -> str:
    data = _data(value); data.pop("criterion_fingerprint", None)
    return canonical_json_fingerprint(data)


def validation_profile_fingerprint(value: DiagnosticValidationProfile | Mapping[str, Any]) -> str:
    data = _data(value); data.pop("profile_fingerprint", None)
    return canonical_json_fingerprint(data)


def implementation_binding_fingerprint(value: DiagnosticMethodImplementationBinding | Mapping[str, Any]) -> str:
    data = _data(value); data.pop("implementation_fingerprint", None)
    return canonical_json_fingerprint(data)


def evidence_input_set_fingerprint(value: DiagnosticEvidenceInputSet | Mapping[str, Any]) -> str:
    data = _data(value)
    data.setdefault("schema_version", "1.0.0")
    for key in ("evidence_input_set_id", "evidence_input_set_fingerprint"):
        data.pop(key, None)
    data["bindings"] = sorted(data["bindings"], key=lambda item: (item["requirement_judgment_ref"], item["evidence_ref"]))
    return canonical_json_fingerprint(data)


def diagnostic_test_request_fingerprint(value: DiagnosticTestRequest | Mapping[str, Any]) -> str:
    data = _data(value)
    data.setdefault("schema_version", "1.0.0")
    for key in ("test_request_id", "request_fingerprint", "created_at"):
        data.pop(key, None)
    for key in ("metric_refs", "variable_refs"):
        data[key] = sorted(data[key])
    return canonical_json_fingerprint(data)


def executed_result_fingerprint(value: ExecutedDiagnosticResult | Mapping[str, Any]) -> str:
    data = _data(value)
    for key in ("executed_result_id", "execution_event_id", "result_fingerprint"):
        data.pop(key, None)
    return canonical_json_fingerprint(data)


def posttest_evaluation_fingerprint(value: PostTestDiagnosticEvaluation | Mapping[str, Any]) -> str:
    data = _data(value)
    for key in ("evaluation_event_id", "evaluation_fingerprint", "finalized_at"):
        data.pop(key, None)
    return canonical_json_fingerprint(data)
