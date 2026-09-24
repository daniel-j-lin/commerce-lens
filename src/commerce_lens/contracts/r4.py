"""R4 Product-Level Revenue Decomposition production contracts."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from commerce_lens.contracts.common import ArtifactReference, ContractBase, utc_now
from commerce_lens.contracts.execution import ExecutionStatus
from commerce_lens.evidence.identifiers import generate_id
from commerce_lens.metrics.registry import PRECISION_POLICY_REF, PRECISION_POLICY_VERSION


R4_METHOD_ID = "product_level_revenue_decomposition"
R4_METHOD_VERSION = "R4 v1.0"
R4_IMPLEMENTATION_ID = "commerce_lens_r4_product_revenue_decomposition"
R4_IMPLEMENTATION_VERSION = "r4_imp_v1"
R4_VALIDATION_POLICY_ID = "r4_product_revenue_decomposition_validation"
R4_VALIDATION_POLICY_VERSION = "r4_v1_0_validation_v1"


class R4ExecutionContext(str, Enum):
    STANDALONE_MECHANICAL = "standalone_mechanical"
    DIAGNOSTIC_WORKFLOW = "diagnostic_workflow"


class R4ProductClassification(str, Enum):
    COMPARISON_ONLY = "comparison_only"
    BASELINE_ONLY = "baseline_only"
    CONTINUING = "continuing"


class R4Component(str, Enum):
    ENTRY = "entry"
    EXIT = "exit"
    CONTINUING = "continuing_product_revenue_change"


class R4ValidationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"


class R4DecompositionRequest(ContractBase):
    r4_request_id: str = Field(default_factory=lambda: generate_id("r4req"), min_length=1)
    execution_context: R4ExecutionContext = R4ExecutionContext.STANDALONE_MECHANICAL
    analysis_request_ref: str = Field(min_length=1)
    sufficiency_ref: str = Field(min_length=1)
    plan_ref: str = Field(min_length=1)
    plan_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    canonical_dataset_ref: str = Field(min_length=1)
    canonical_dataset_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    baseline_population_ref: str = Field(min_length=1)
    baseline_population_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    comparison_population_ref: str = Field(min_length=1)
    comparison_population_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    baseline_revenue_validated_result_ref: str = Field(min_length=1)
    comparison_revenue_validated_result_ref: str = Field(min_length=1)
    revenue_change_validated_result_ref: str = Field(min_length=1)
    baseline_revenue_evidence_ref: str = Field(min_length=1)
    baseline_revenue_evidence_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    comparison_revenue_evidence_ref: str = Field(min_length=1)
    comparison_revenue_evidence_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    revenue_change_evidence_ref: str = Field(min_length=1)
    revenue_change_evidence_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    method_id: str = R4_METHOD_ID
    method_version: str = R4_METHOD_VERSION
    precision_policy_ref: str = PRECISION_POLICY_REF
    precision_policy_version: str = PRECISION_POLICY_VERSION
    validation_policy_id: str = R4_VALIDATION_POLICY_ID
    validation_policy_version: str = R4_VALIDATION_POLICY_VERSION
    confirmed_product_identity_defect_refs: tuple[str, ...] = ()
    diagnostic_proposition_ref: str | None = None
    diagnostic_r3_profile_ref: str | None = None
    diagnostic_r3_profile_version: str | None = None
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_context_shape(self) -> "R4DecompositionRequest":
        if self.execution_context is R4ExecutionContext.STANDALONE_MECHANICAL:
            if any(
                value is not None
                for value in (
                    self.diagnostic_proposition_ref,
                    self.diagnostic_r3_profile_ref,
                    self.diagnostic_r3_profile_version,
                )
            ):
                raise ValueError("standalone R4 requests cannot carry diagnostic authority")
        return self


class R4AuthorityBinding(ContractBase):
    analysis_request_ref: str = Field(min_length=1)
    sufficiency_ref: str = Field(min_length=1)
    plan_ref: str = Field(min_length=1)
    plan_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    canonical_dataset_ref: str = Field(min_length=1)
    canonical_dataset_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    baseline_period_ref: str = Field(min_length=1)
    comparison_period_ref: str = Field(min_length=1)
    baseline_population_ref: str = Field(min_length=1)
    baseline_population_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    comparison_population_ref: str = Field(min_length=1)
    comparison_population_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    scope_ref: str = Field(min_length=1)
    currency: str = Field(min_length=1)
    baseline_revenue_validated_result_ref: str = Field(min_length=1)
    baseline_revenue_validation_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    comparison_revenue_validated_result_ref: str = Field(min_length=1)
    comparison_revenue_validation_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    revenue_change_validated_result_ref: str = Field(min_length=1)
    revenue_change_validation_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    baseline_revenue_evidence_ref: str = Field(min_length=1)
    baseline_revenue_evidence_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    comparison_revenue_evidence_ref: str = Field(min_length=1)
    comparison_revenue_evidence_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    revenue_change_evidence_ref: str = Field(min_length=1)
    revenue_change_evidence_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    method_id: str = R4_METHOD_ID
    method_version: str = R4_METHOD_VERSION
    precision_policy_ref: str = PRECISION_POLICY_REF
    precision_policy_version: str = PRECISION_POLICY_VERSION
    validation_policy_id: str = R4_VALIDATION_POLICY_ID
    validation_policy_version: str = R4_VALIDATION_POLICY_VERSION


class R4ProductTraceRow(ContractBase):
    product_id: str = Field(min_length=1)
    baseline_present: bool
    comparison_present: bool
    baseline_revenue: Decimal
    comparison_revenue: Decimal
    classification: R4ProductClassification
    contribution: Decimal
    assigned_component: R4Component
    currency: str = Field(min_length=1)
    baseline_period_ref: str = Field(min_length=1)
    comparison_period_ref: str = Field(min_length=1)
    baseline_population_ref: str = Field(min_length=1)
    comparison_population_ref: str = Field(min_length=1)
    scope_ref: str = Field(min_length=1)
    canonical_dataset_ref: str = Field(min_length=1)
    canonical_dataset_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    method_id: str = R4_METHOD_ID
    method_version: str = R4_METHOD_VERSION
    execution_id: str = Field(min_length=1)
    precision_policy_ref: str = PRECISION_POLICY_REF
    precision_policy_version: str = PRECISION_POLICY_VERSION
    validation_policy_id: str = R4_VALIDATION_POLICY_ID
    validation_policy_version: str = R4_VALIDATION_POLICY_VERSION

    @model_validator(mode="after")
    def validate_presence_classification(self) -> "R4ProductTraceRow":
        expected = {
            (False, True): (R4ProductClassification.COMPARISON_ONLY, R4Component.ENTRY),
            (True, False): (R4ProductClassification.BASELINE_ONLY, R4Component.EXIT),
            (True, True): (R4ProductClassification.CONTINUING, R4Component.CONTINUING),
        }.get((self.baseline_present, self.comparison_present))
        if expected is None:
            raise ValueError("R4 trace rows must be present in at least one governed period")
        if (self.classification, self.assigned_component) != expected:
            raise ValueError("R4 trace classification contradicts governed presence")
        return self


class R4ProductTrace(ContractBase):
    trace_id: str = Field(min_length=1)
    trace_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    execution_id: str = Field(min_length=1)
    authority: R4AuthorityBinding
    rows: tuple[R4ProductTraceRow, ...]
    row_count: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_row_count_and_order(self) -> "R4ProductTrace":
        if self.row_count != len(self.rows):
            raise ValueError("R4 trace row_count does not match rows")
        product_ids = tuple(row.product_id for row in self.rows)
        if product_ids != tuple(sorted(product_ids)) or len(product_ids) != len(set(product_ids)):
            raise ValueError("R4 trace rows must contain unique product IDs in stable order")
        return self


class ExecutedR4DecompositionResult(ContractBase):
    result_id: str = Field(default_factory=lambda: generate_id("r4res"), min_length=1)
    execution_id: str = Field(min_length=1)
    r4_request_id: str = Field(min_length=1)
    authority: R4AuthorityBinding
    baseline_revenue: Decimal
    comparison_revenue: Decimal
    observed_revenue_change: Decimal
    entry_component: Decimal
    exit_component: Decimal
    continuing_component: Decimal
    component_sum: Decimal
    reconciliation_difference: Decimal
    product_count: int = Field(ge=0)
    entry_product_count: int = Field(ge=0)
    exit_product_count: int = Field(ge=0)
    continuing_product_count: int = Field(ge=0)
    product_trace_ref: ArtifactReference
    product_trace_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    result_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    execution_status: ExecutionStatus = ExecutionStatus.COMPLETED
    semantic_boundary: str = "mechanical contribution != diagnostic explanation != causal explanation"


class R4ExecutionRecord(ContractBase):
    execution_id: str = Field(min_length=1)
    r4_request_id: str = Field(min_length=1)
    execution_context: R4ExecutionContext
    authority: R4AuthorityBinding
    implementation_id: str = R4_IMPLEMENTATION_ID
    implementation_version: str = R4_IMPLEMENTATION_VERSION
    started_at: datetime
    ended_at: datetime
    status: ExecutionStatus
    operation: dict[str, Any] = Field(default_factory=dict)
    result_ref: str | None = None
    output_artifacts: tuple[ArtifactReference, ...] = ()
    failure_code: str | None = None
    failure_reason: str | None = None

    @model_validator(mode="after")
    def validate_record(self) -> "R4ExecutionRecord":
        if self.started_at > self.ended_at:
            raise ValueError("R4 execution timestamps are out of order")
        if self.status is ExecutionStatus.COMPLETED and self.result_ref is None:
            raise ValueError("completed R4 execution requires a result reference")
        if self.status is not ExecutionStatus.COMPLETED and self.failure_code is None:
            raise ValueError("non-completed R4 execution requires a failure code")
        return self


class R4ValidationCheck(ContractBase):
    check_id: str = Field(min_length=1)
    passed: bool
    observed: Any = None
    expected: Any = None
    failure_code: str | None = None
    failure_reason: str | None = None

    @model_validator(mode="after")
    def validate_failure_shape(self) -> "R4ValidationCheck":
        if self.passed and (self.failure_code is not None or self.failure_reason is not None):
            raise ValueError("passed R4 validation checks cannot carry failure data")
        if not self.passed and (self.failure_code is None or self.failure_reason is None):
            raise ValueError("failed R4 validation checks require failure data")
        return self


class R4ValidationRecord(ContractBase):
    validation_id: str = Field(default_factory=lambda: generate_id("r4val"), min_length=1)
    execution_id: str = Field(min_length=1)
    target_result_ref: str = Field(min_length=1)
    target_result_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    product_trace_ref: ArtifactReference
    product_trace_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    execution_record_ref: ArtifactReference
    source_result_ref: ArtifactReference
    authority: R4AuthorityBinding
    validator_id: str = "commerce_lens_r4_independent_validator"
    validator_version: str = R4_VALIDATION_POLICY_VERSION
    checks: tuple[R4ValidationCheck, ...] = Field(min_length=1)
    status: R4ValidationStatus
    started_at: datetime
    ended_at: datetime
    validation_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_status(self) -> "R4ValidationRecord":
        if self.started_at > self.ended_at:
            raise ValueError("R4 validation timestamps are out of order")
        expected = R4ValidationStatus.PASSED if all(check.passed for check in self.checks) else R4ValidationStatus.FAILED
        if self.status is not expected:
            raise ValueError("R4 validation status contradicts check outcomes")
        return self


class ValidatedR4DecompositionResult(ContractBase):
    validated_result_id: str = Field(default_factory=lambda: generate_id("r4valres"), min_length=1)
    execution_id: str = Field(min_length=1)
    executed_result_id: str = Field(min_length=1)
    validation_record_id: str = Field(min_length=1)
    authority: R4AuthorityBinding
    source_result_artifact_ref: ArtifactReference
    execution_record_artifact_ref: ArtifactReference
    validation_record_artifact_ref: ArtifactReference
    product_trace_ref: ArtifactReference
    result_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    validation_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    product_trace_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    baseline_revenue: Decimal
    comparison_revenue: Decimal
    observed_revenue_change: Decimal
    entry_component: Decimal
    exit_component: Decimal
    continuing_component: Decimal
    component_sum: Decimal
    reconciliation_difference: Decimal
    product_count: int = Field(ge=0)
    entry_product_count: int = Field(ge=0)
    exit_product_count: int = Field(ge=0)
    continuing_product_count: int = Field(ge=0)
    intended_use: str = "standalone_mechanical_decomposition"
    created_at: datetime = Field(default_factory=utc_now)
    semantic_boundary: str = "mechanical contribution != diagnostic explanation != causal explanation"
