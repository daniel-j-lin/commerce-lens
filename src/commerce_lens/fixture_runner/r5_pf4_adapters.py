"""PF4-0 harness boundary for the approved production R4 subject.

This module contains orchestration, material projection, and hostile-artifact
submission support only.  Product decomposition and validation semantics remain
owned by the production R4 service, executor, repository, and validator.
"""

from __future__ import annotations

import csv
import json
import tempfile
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path
from typing import Any, Callable, Literal

from pydantic import ValidationError

from commerce_lens.application.analysis_service import run_analysis
from commerce_lens.application.r4_service import (
    R4EligibilityError,
    R4ResultValidationFailure,
    R4RunOutcome,
    run_r4_decomposition,
)
from commerce_lens.canonical import (
    CanonicalizationRequest,
    EligibilityMode,
    EligibilityState,
    EligibilityValueMapping,
    identity_mapping,
)
from commerce_lens.canonical.models import PeriodCoverageEvidence
from commerce_lens.contracts.common import (
    AvailableEvidence,
    ClaimType,
    ContractBase,
    EvidenceRequirement,
    GroupingDimension,
    PeriodDefinition,
    ScopeDefinition,
    SourceType,
)
from commerce_lens.contracts.evidence import AdmissibleEvidence, EvidenceRole, MetricReference
from commerce_lens.contracts.populations import PopulationDefinition, PopulationPeriodRole
from commerce_lens.contracts.r4 import (
    R4AuthorityBinding,
    R4DecompositionRequest,
    R4ExecutionContext,
    R4ProductTraceRow,
)
from commerce_lens.contracts.requests import AnalysisRequest
from commerce_lens.contracts.validation import ValidatedResult
from commerce_lens.evidence.admissibility import retrieve_admissible_evidence_authority
from commerce_lens.evidence.identifiers import canonical_json_bytes, generate_id
from commerce_lens.fixture_runner.r5_adapters import AdapterRegistration, AdapterRegistry
from commerce_lens.fixture_runner.r5_manifest import (
    ActualProjection,
    ExecutionMode,
    LoadedR5Fixture,
)
from commerce_lens.intake.registry import DatasetRegistry
from commerce_lens.metrics import METRIC_DEFINITION_VERSION, METRIC_REGISTRY_VERSION
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.persistence.r4_repository import (
    R4ArtifactIntegrityError,
    _r4_result_fingerprint,
    _r4_trace_fingerprint,
    load_authenticated_scalar_validated_result,
)
from commerce_lens.validation.r4_validator import validate_r4_decomposition


PF4_R4_ACTUAL_OUTPUT_PRODUCER = "commerce_lens.application.r4_service.run_r4_decomposition"
PF4_R4_PREREQUISITE_OUTPUT_PRODUCER = "commerce_lens.production.r4_prerequisite_chain"
PF4_PRESENTATION_ROUNDING_DISPOSITION = (
    "VALIDATED_R4_MECHANICAL_RESULT__PRESENTATION_ROUNDING_DISCLOSED"
)
PF4_NON_MATERIAL_FIELDS = (
    "ExecutedR4DecompositionResult.result_id",
    "ExecutedR4DecompositionResult.execution_id",
    "ExecutedR4DecompositionResult.r4_request_id",
    "R4ProductTrace.trace_id",
    "R4ProductTrace.execution_id",
    "R4ProductTraceRow.execution_id",
    "R4ValidationRecord.validation_id",
    "execution and validation timestamps",
    "ArtifactReference.artifact_id/path/size_bytes",
)
_FORBIDDEN_HOSTILE_KEYS = frozenset(
    {
        "expected_failure",
        "should_pass",
        "should_fail",
        "expected_component",
        "first_blocker",
        "first_controlling_blocker",
        "final_disposition",
    }
)


class PF4HarnessSetupError(RuntimeError):
    """Low-level factual input could not produce authentic R4 prerequisites."""


class PF4UpstreamBlocked(RuntimeError):
    """Production analysis stopped before authentic R4 authority was available."""

    def __init__(self, analysis_result: object) -> None:
        super().__init__("production analysis blocked before R4 authority construction")
        self.analysis_result = analysis_result


class PF4MaterialTraceRow(ContractBase):
    product_id: str
    baseline_present: bool
    comparison_present: bool
    baseline_revenue: Decimal
    comparison_revenue: Decimal
    classification: str
    contribution: Decimal
    assigned_component: str
    currency: str
    baseline_period_ref: str
    comparison_period_ref: str
    baseline_population_ref: str
    comparison_population_ref: str
    scope_ref: str
    canonical_dataset_ref: str
    canonical_dataset_fingerprint: str
    method_id: str
    method_version: str
    precision_policy_ref: str
    precision_policy_version: str
    validation_policy_id: str
    validation_policy_version: str


class PF4R4MaterialProjection(ContractBase):
    authority: R4AuthorityBinding
    baseline_revenue: Decimal
    comparison_revenue: Decimal
    observed_revenue_change: Decimal
    entry_component: Decimal
    exit_component: Decimal
    continuing_component: Decimal
    component_sum: Decimal
    reconciliation_difference: Decimal
    product_count: int
    entry_product_count: int
    exit_product_count: int
    continuing_product_count: int
    trace_rows: tuple[PF4MaterialTraceRow, ...]
    product_trace_fingerprint: str
    result_fingerprint: str
    execution_status: str
    validation_status: str
    validation_checks: tuple[tuple[str, bool, str | None], ...]
    semantic_boundary: str


class PF4MaterialDifference(ContractBase):
    path: str
    left: Any = None
    right: Any = None


class PF4ConformanceComparison(ContractBase):
    conforming: bool
    failure_layer: Literal["METHOD_CONFORMANCE"] | None = None
    differences: tuple[PF4MaterialDifference, ...] = ()


class PF4FailureObservation(ContractBase):
    failure_layer: Literal[
        "ELIGIBILITY",
        "EXECUTION",
        "RESULT_VALIDATION_OR_INTEGRITY",
        "METHOD_CONFORMANCE",
    ]
    failure_code: str
    exception_type: str
    reason: str


class PF4IndependentChainObservation(ContractBase):
    scalar_metric_ref: str
    scalar_validated_result_ref: str
    scalar_validation_fingerprint: str
    scalar_value: Decimal
    r4_failure: PF4FailureObservation | None = None


@dataclass(frozen=True)
class PF4UpstreamAuthority:
    request: AnalysisRequest
    analysis_result: object
    canonical_dataset: object
    plan: object
    baseline_population: PopulationDefinition
    comparison_population: PopulationDefinition
    baseline_revenue: ValidatedResult
    comparison_revenue: ValidatedResult
    revenue_change: ValidatedResult
    baseline_evidence: AdmissibleEvidence
    comparison_evidence: AdmissibleEvidence
    revenue_change_evidence: AdmissibleEvidence
    r4_request: R4DecompositionRequest
    artifact_store: ArtifactStore
    metadata_store: MetadataStore


@dataclass(frozen=True)
class PF4HostileSubmission:
    result_artifact: object
    trace_artifact: object


def build_r5_pf4_adapter_registry() -> AdapterRegistry:
    """Register only the production-R4 adapter boundaries authorized for PF4."""
    registry = AdapterRegistry()
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_repeat_material_conformance",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="production_r4_same_evaluator_material_comparison",
            capability_version="R4 v1.0",
            actual_output_producer="commerce_lens.production.r4_same_evaluator_comparison",
            producer=_produce_r4_repeat_material_conformance,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_row_order_conformance",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="production_r4_canonical_row_order_invariance",
            capability_version="R4 v1.0",
            actual_output_producer="commerce_lens.production.r4_same_evaluator_comparison",
            producer=_produce_r4_row_order_conformance,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_presentation_order_observation",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="production_r4_presentation_order_non_materiality",
            capability_version="R4 v1.0",
            actual_output_producer="commerce_lens.fixture_runner.r4_presentation_observation",
            producer=_produce_r4_presentation_order_observation,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_material_mutation_conformance",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="production_r4_same_evaluator_mutation_detection",
            capability_version="R4 v1.0",
            actual_output_producer="commerce_lens.fixture_runner.compare_r4_material",
            producer=_produce_r4_material_mutation_conformance,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_product_revenue_mismatch_gate",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="production_r4_validator_product_revenue",
            capability_version="r4_v1_0_validation_v1",
            actual_output_producer="commerce_lens.validation.r4_validator.validate_r4_decomposition",
            producer=_produce_r4_product_revenue_mismatch_gate,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_partition_incomplete_gate",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="production_r4_validator_partition",
            capability_version="r4_v1_0_validation_v1",
            actual_output_producer="commerce_lens.validation.r4_validator.validate_r4_decomposition",
            producer=_produce_r4_partition_incomplete_gate,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_partition_overlap_gate",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="production_r4_repository_trace_contract",
            capability_version="r4_v1_0_validation_v1",
            actual_output_producer="commerce_lens.persistence.r4_repository.load_r4_trace",
            producer=_produce_r4_partition_overlap_gate,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_component_sum_mismatch_gate",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="production_r4_validator_component_sum",
            capability_version="r4_v1_0_validation_v1",
            actual_output_producer="commerce_lens.validation.r4_validator.validate_r4_decomposition",
            producer=_produce_r4_component_sum_mismatch_gate,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_reconciliation_mismatch_gate",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="production_r4_validator_reconciliation",
            capability_version="r4_v1_0_validation_v1",
            actual_output_producer="commerce_lens.validation.r4_validator.validate_r4_decomposition",
            producer=_produce_r4_reconciliation_mismatch_gate,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_trace_incomplete_gate",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="production_r4_validator_trace_completeness",
            capability_version="r4_v1_0_validation_v1",
            actual_output_producer="commerce_lens.validation.r4_validator.validate_r4_decomposition",
            producer=_produce_r4_trace_incomplete_gate,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_trace_integrity_gate",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="production_r4_repository_trace_integrity",
            capability_version="r4_v1_0_validation_v1",
            actual_output_producer="commerce_lens.persistence.r4_repository.load_r4_trace",
            producer=_produce_r4_trace_integrity_gate,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_post_execution_method_binding_gate",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="production_r4_validator_method_binding",
            capability_version="r4_v1_0_validation_v1",
            actual_output_producer="commerce_lens.validation.r4_validator.validate_r4_decomposition",
            producer=_produce_r4_post_execution_method_binding_gate,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_runtime_dependency_gate",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="production_r4_executor_dependency_boundary",
            capability_version="R4 v1.0",
            actual_output_producer="commerce_lens.engine.r4_execution.execute_r4_decomposition",
            producer=_produce_r4_runtime_dependency_gate,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_independent_chain_projection",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="production_scalar_and_r4_independent_chains",
            capability_version="R4 v1.0",
            actual_output_producer="commerce_lens.production.scalar_and_r4_chains",
            producer=_produce_r4_independent_chain_projection,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_eligibility_projection",
            execution_mode=ExecutionMode.APPLICATION_SERVICE,
            capability_name="approved_production_r4_prerequisite_chain",
            capability_version="R4 v1.0",
            actual_output_producer=PF4_R4_PREREQUISITE_OUTPUT_PRODUCER,
            producer=_produce_r4_eligibility_projection,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_version_authority_projection",
            execution_mode=ExecutionMode.APPLICATION_SERVICE,
            capability_name="approved_production_r4_version_authority",
            capability_version="R4 v1.0",
            actual_output_producer=PF4_R4_PREREQUISITE_OUTPUT_PRODUCER,
            producer=_produce_r4_version_authority_projection,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_standalone_context_projection",
            execution_mode=ExecutionMode.APPLICATION_SERVICE,
            capability_name="approved_production_r4_standalone_context",
            capability_version="R4 v1.0",
            actual_output_producer=PF4_R4_ACTUAL_OUTPUT_PRODUCER,
            producer=_produce_r4_standalone_context_projection,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_artificial_diagnostic_authority_guard",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="r4_request_contract_context_guard",
            capability_version="R4 v1.0",
            actual_output_producer="commerce_lens.contracts.r4.R4DecompositionRequest",
            producer=_produce_r4_artificial_diagnostic_authority_guard,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_mechanical_semantic_boundary",
            execution_mode=ExecutionMode.APPLICATION_SERVICE,
            capability_name="approved_production_r4_mechanical_semantic_boundary",
            capability_version="R4 v1.0",
            actual_output_producer=PF4_R4_ACTUAL_OUTPUT_PRODUCER,
            producer=_produce_r4_mechanical_semantic_boundary,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_material_projection_with_presentation_observation",
            execution_mode=ExecutionMode.APPLICATION_SERVICE,
            capability_name="approved_production_r4_with_presentation_observation",
            capability_version="R4 v1.0 + R5 presentation observation v1",
            actual_output_producer=PF4_R4_ACTUAL_OUTPUT_PRODUCER,
            producer=_produce_r4_material_projection_with_presentation_observation,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_material_projection",
            execution_mode=ExecutionMode.APPLICATION_SERVICE,
            capability_name="approved_production_r4",
            capability_version="R4 v1.0",
            actual_output_producer=PF4_R4_ACTUAL_OUTPUT_PRODUCER,
            producer=_produce_r4_material_projection,
        )
    )
    registry.register(
        AdapterRegistration(
            adapter_id="production_r4_diagnostic_gate",
            execution_mode=ExecutionMode.APPLICATION_SERVICE,
            capability_name="approved_production_r4_diagnostic_negative_boundary",
            capability_version="R4 v1.0",
            actual_output_producer=PF4_R4_ACTUAL_OUTPUT_PRODUCER,
            producer=_produce_r4_diagnostic_gate,
        )
    )
    return registry


def build_pf4_upstream_authority(
    *,
    source_path: str | Path,
    baseline_period: PeriodDefinition,
    comparison_period: PeriodDefinition,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    scope: ScopeDefinition | None = None,
    coverage_start_date: date | None = None,
    coverage_end_date: date | None = None,
    coverage_note_ref: str = "r5_pf4_static_synthetic_fixture",
) -> PF4UpstreamAuthority:
    """Use production P1-P7 stages to build authentic R4 input authority."""
    source = Path(source_path).resolve()
    governed_scope = scope or ScopeDefinition(scope_id="all_eligible")
    dataset = DatasetRegistry(artifact_store, metadata_store).register_source(source, SourceType.CSV)
    required_evidence = (
        EvidenceRequirement(requirement_id="req_global", description="PF4 factual source authority"),
        EvidenceRequirement(
            requirement_id="req_revenue",
            description="PF4 Revenue authority",
            metric_ref="revenue",
        ),
        EvidenceRequirement(
            requirement_id="req_revenue_change",
            description="PF4 Revenue Change authority",
            metric_ref="revenue_change",
        ),
    )
    request = AnalysisRequest(
        canonical_business_question_id="r5_pf4_product_revenue_decomposition",
        original_question_text="PF4 governed Product-Level Revenue Decomposition conformance input",
        metrics=(
            MetricReference(metric_id="revenue_change", definition_version=METRIC_DEFINITION_VERSION),
            MetricReference(metric_id="revenue", definition_version=METRIC_DEFINITION_VERSION),
        ),
        baseline_period=baseline_period,
        comparison_period=comparison_period,
        scope=governed_scope,
        grouping=GroupingDimension.NONE,
        required_evidence=required_evidence,
        dataset_ref_id=dataset.dataset_id,
        canonical_schema_version="canonical_mvp_v1",
        metric_registry_version=METRIC_REGISTRY_VERSION,
    )
    result = run_analysis(
        request,
        canonicalization_request=_canonicalization_request(dataset.dataset_id, source),
        artifact_store=artifact_store,
        metadata_store=metadata_store,
        dataset=dataset,
        available_evidence=(
            AvailableEvidence(
                evidence_id="r5_pf4_factual_source",
                description="PF4 reviewed tiny factual source",
                source_ref=dataset.dataset_id,
                satisfies_requirement_ids=tuple(item.requirement_id for item in required_evidence),
            ),
        ),
        period_coverage_evidence=(
            PeriodCoverageEvidence(
                coverage_ref_id="r5_pf4_reviewed_coverage",
                dataset_ref_id=dataset.dataset_id,
                observed_start_date=coverage_start_date or baseline_period.start_date,
                observed_end_date=coverage_end_date or comparison_period.end_date,
                date_convention_ref=baseline_period.date_convention_ref,
                governing_note_ref=coverage_note_ref,
            ),
        ),
    )
    if (
        result.execution_plan is None
        or result.data_sufficiency_ref is None
        or result.blocked_metric_refs
    ):
        raise PF4UpstreamBlocked(result)
    sufficiency = metadata_store.get_data_sufficiency_result(result.data_sufficiency_ref, artifact_store)
    if sufficiency is None or sufficiency.canonical_dataset_ref_id is None:
        raise PF4HarnessSetupError("production analysis did not retain sufficiency/canonical authority")
    canonical = metadata_store.get_canonical_dataset(sufficiency.canonical_dataset_ref_id)
    if canonical is None:
        raise PF4HarnessSetupError("production canonical authority is missing")
    scalars = tuple(
        load_authenticated_scalar_validated_result(item, artifact_store, metadata_store)
        for item in result.validated_result_refs
    )
    baseline = _one_scalar(scalars, "revenue", "baseline")
    comparison = _one_scalar(scalars, "revenue", "comparison")
    change = _one_scalar(scalars, "revenue_change", "baseline_and_comparison")
    evidence = tuple(
        retrieve_admissible_evidence_authority(
            item,
            artifact_store=artifact_store,
            metadata_store=metadata_store,
        )
        for item in result.admissible_evidence_refs
    )
    baseline_evidence = _one_evidence(evidence, baseline)
    comparison_evidence = _one_evidence(evidence, comparison)
    change_evidence = _one_evidence(evidence, change)
    baseline_population = _one_population(result.execution_plan.population_definitions, PopulationPeriodRole.BASELINE)
    comparison_population = _one_population(
        result.execution_plan.population_definitions,
        PopulationPeriodRole.COMPARISON,
    )
    r4_request = R4DecompositionRequest(
        analysis_request_ref=request.request_id,
        sufficiency_ref=sufficiency.sufficiency_id,
        plan_ref=result.execution_plan.plan_id,
        plan_fingerprint=result.execution_plan.plan_fingerprint,
        canonical_dataset_ref=canonical.canonical_dataset_id,
        canonical_dataset_fingerprint=canonical.content_fingerprint,
        baseline_population_ref=baseline_population.population_id,
        baseline_population_fingerprint=baseline_population.population_fingerprint,
        comparison_population_ref=comparison_population.population_id,
        comparison_population_fingerprint=comparison_population.population_fingerprint,
        baseline_revenue_validated_result_ref=baseline.validated_result_id,
        comparison_revenue_validated_result_ref=comparison.validated_result_id,
        revenue_change_validated_result_ref=change.validated_result_id,
        baseline_revenue_evidence_ref=baseline_evidence.evidence_id,
        baseline_revenue_evidence_fingerprint=_required_evidence_fingerprint(baseline_evidence),
        comparison_revenue_evidence_ref=comparison_evidence.evidence_id,
        comparison_revenue_evidence_fingerprint=_required_evidence_fingerprint(comparison_evidence),
        revenue_change_evidence_ref=change_evidence.evidence_id,
        revenue_change_evidence_fingerprint=_required_evidence_fingerprint(change_evidence),
    )
    return PF4UpstreamAuthority(
        request=request,
        analysis_result=result,
        canonical_dataset=canonical,
        plan=result.execution_plan,
        baseline_population=baseline_population,
        comparison_population=comparison_population,
        baseline_revenue=baseline,
        comparison_revenue=comparison,
        revenue_change=change,
        baseline_evidence=baseline_evidence,
        comparison_evidence=comparison_evidence,
        revenue_change_evidence=change_evidence,
        r4_request=r4_request,
        artifact_store=artifact_store,
        metadata_store=metadata_store,
    )


def run_pf4_r4(
    authority: PF4UpstreamAuthority,
    *,
    request: R4DecompositionRequest | None = None,
) -> R4RunOutcome:
    return run_r4_decomposition(
        request=request or authority.r4_request,
        plan=authority.plan,
        canonical_dataset=authority.canonical_dataset,
        artifact_store=authority.artifact_store,
        metadata_store=authority.metadata_store,
    )


def project_r4_material(outcome: R4RunOutcome) -> PF4R4MaterialProjection:
    """Project every governed material value while excluding only event identity."""
    result = outcome.execution.executed_result
    rows = tuple(
        sorted(
            (_project_trace_row(item) for item in outcome.execution.product_trace.rows),
            key=lambda item: item.product_id,
        )
    )
    return PF4R4MaterialProjection(
        authority=result.authority,
        baseline_revenue=result.baseline_revenue,
        comparison_revenue=result.comparison_revenue,
        observed_revenue_change=result.observed_revenue_change,
        entry_component=result.entry_component,
        exit_component=result.exit_component,
        continuing_component=result.continuing_component,
        component_sum=result.component_sum,
        reconciliation_difference=result.reconciliation_difference,
        product_count=result.product_count,
        entry_product_count=result.entry_product_count,
        exit_product_count=result.exit_product_count,
        continuing_product_count=result.continuing_product_count,
        trace_rows=rows,
        product_trace_fingerprint=result.product_trace_fingerprint,
        result_fingerprint=result.result_fingerprint,
        execution_status=result.execution_status.value,
        validation_status=outcome.validation.validation_record.status.value,
        validation_checks=tuple(
            (item.check_id, item.passed, item.failure_code)
            for item in outcome.validation.validation_record.checks
        ),
        semantic_boundary=result.semantic_boundary,
    )


def compare_r4_material(
    left: PF4R4MaterialProjection,
    right: PF4R4MaterialProjection,
) -> PF4ConformanceComparison:
    differences: list[PF4MaterialDifference] = []
    _material_diff("r4", left.model_dump(mode="json"), right.model_dump(mode="json"), differences)
    return PF4ConformanceComparison(
        conforming=not differences,
        failure_layer=None if not differences else "METHOD_CONFORMANCE",
        differences=tuple(differences),
    )


def classify_r4_failure(exc: Exception) -> PF4FailureObservation:
    if isinstance(exc, R4EligibilityError):
        return PF4FailureObservation(
            failure_layer="ELIGIBILITY",
            failure_code=exc.code,
            exception_type=type(exc).__name__,
            reason=str(exc),
        )
    if isinstance(exc, R4ResultValidationFailure):
        failed = tuple(item.check_id for item in exc.outcome.validation_record.checks if not item.passed)
        return PF4FailureObservation(
            failure_layer="RESULT_VALIDATION_OR_INTEGRITY",
            failure_code=",".join(failed) or "r4_result_validation_failed",
            exception_type=type(exc).__name__,
            reason=str(exc),
        )
    if isinstance(exc, R4ArtifactIntegrityError):
        return PF4FailureObservation(
            failure_layer="RESULT_VALIDATION_OR_INTEGRITY",
            failure_code="R4ArtifactIntegrityError",
            exception_type=type(exc).__name__,
            reason=str(exc),
        )
    from commerce_lens.engine.r4_execution import R4ExecutionError

    if isinstance(exc, R4ExecutionError):
        return PF4FailureObservation(
            failure_layer="EXECUTION",
            failure_code="R4ExecutionError",
            exception_type=type(exc).__name__,
            reason=str(exc),
        )
    raise exc


def prepare_hostile_r4_submission(
    authority: PF4UpstreamAuthority,
    outcome: R4RunOutcome,
    *,
    trace_payload: dict[str, Any] | None = None,
    result_payload: dict[str, Any] | None = None,
    register_trace: bool = True,
    register_result: bool = True,
) -> PF4HostileSubmission:
    """Persist hostile actual artifacts without interpreting their expected outcome."""
    if trace_payload is not None:
        _reject_expected_oracle_keys(trace_payload)
        trace_artifact = authority.artifact_store.write_json_artifact(
            Path("temporary") / f"{generate_id('pf4trace')}.json",
            trace_payload,
        )
        if register_trace:
            authority.metadata_store.insert_artifact_reference(trace_artifact)
    else:
        trace_artifact = outcome.execution.executed_result.product_trace_ref

    if result_payload is None:
        hostile_result = outcome.execution.executed_result.model_copy(
            update={
                "product_trace_ref": trace_artifact,
                "product_trace_fingerprint": (
                    trace_payload.get("trace_fingerprint")
                    if trace_payload is not None
                    else outcome.execution.executed_result.product_trace_fingerprint
                ),
            }
        )
        hostile_result = hostile_result.model_copy(
            update={"result_fingerprint": _r4_result_fingerprint(hostile_result)}
        )
        result_payload = hostile_result.model_dump(mode="json")
    else:
        _reject_expected_oracle_keys(result_payload)
    result_artifact = authority.artifact_store.write_json_artifact(
        Path("temporary") / f"{generate_id('pf4result')}.json",
        result_payload,
    )
    if register_result:
        authority.metadata_store.insert_artifact_reference(result_artifact)
    return PF4HostileSubmission(result_artifact=result_artifact, trace_artifact=trace_artifact)


def validate_hostile_r4_submission(
    authority: PF4UpstreamAuthority,
    outcome: R4RunOutcome,
    submission: PF4HostileSubmission,
):
    """Submit hostile actual input to the genuine production R4 validator boundary."""
    return validate_r4_decomposition(
        executed_result_artifact=submission.result_artifact,
        execution_record=outcome.execution.execution_record,
        execution_record_artifact=outcome.execution.execution_record_artifact,
        canonical_dataset=authority.canonical_dataset,
        baseline_population=authority.baseline_population,
        comparison_population=authority.comparison_population,
        baseline_revenue_authority=authority.baseline_revenue,
        comparison_revenue_authority=authority.comparison_revenue,
        revenue_change_authority=authority.revenue_change,
        artifact_store=authority.artifact_store,
        metadata_store=authority.metadata_store,
    )


def observe_independent_scalar_and_r4(
    scalar_revenue: ValidatedResult,
    r4_operation: Callable[[], object],
) -> PF4IndependentChainObservation:
    """Observe two branches without allowing the R4 branch to mutate scalar authority."""
    before = scalar_revenue.model_dump(mode="json")
    failure: PF4FailureObservation | None = None
    try:
        r4_operation()
    except Exception as exc:
        failure = classify_r4_failure(exc)
    if scalar_revenue.model_dump(mode="json") != before:
        raise PF4HarnessSetupError("R4 branch mutated independent scalar Revenue authority")
    if not isinstance(scalar_revenue.value, Decimal):
        raise PF4HarnessSetupError("independent scalar Revenue authority is not Decimal")
    return PF4IndependentChainObservation(
        scalar_metric_ref=scalar_revenue.metric_ref,
        scalar_validated_result_ref=scalar_revenue.validated_result_id,
        scalar_validation_fingerprint=scalar_revenue.validation_fingerprint,
        scalar_value=scalar_revenue.value,
        r4_failure=failure,
    )


def _produce_r4_material_projection(fixture: LoadedR5Fixture) -> ActualProjection:
    material = _run_fixture_r4_material(fixture)
    return _material_actual_projection(material)


def _produce_r4_repeat_material_conformance(
    fixture: LoadedR5Fixture,
) -> ActualProjection:
    left, right = _run_fixture_r4_material_pair(fixture)
    comparison = compare_r4_material(left, right)
    if not comparison.conforming:
        raise PF4HarnessSetupError("repeated production R4 evaluation was not material-identical")
    return _conformance_projection(
        validation_outcome="material_outputs_identical",
        chain_disposition="same_evaluator_conforming",
        final_disposition="MATERIAL_OUTPUT_IDENTICAL__CONFORMING",
        trace_integrity_state={
            "failure_layer": None,
            "material_difference_count": 0,
        },
        actual_output_producer="commerce_lens.production.r4_same_evaluator_comparison",
    )


def _produce_r4_row_order_conformance(fixture: LoadedR5Fixture) -> ActualProjection:
    shuffled_source = _input_path_for_role(fixture, "orders_shuffled")
    if shuffled_source is None:
        raise PF4HarnessSetupError("row-order conformance requires a shuffled orders input")
    left = _run_fixture_r4_material(fixture)
    right = _run_fixture_r4_material_from_source(fixture, shuffled_source)
    differences: list[PF4MaterialDifference] = []
    _material_diff(
        "r4",
        _project_fixture_material(left),
        _project_fixture_material(right),
        differences,
    )
    if differences:
        raise PF4HarnessSetupError("canonical source-row order changed material R4 output")
    return _conformance_projection(
        validation_outcome="authoritative_result_unchanged",
        chain_disposition="canonical_row_order_conforming",
        final_disposition="AUTHORITATIVE_RESULT_UNCHANGED",
        trace_integrity_state={
            "material_difference_count": 0,
            "source_row_order_differed": True,
        },
        actual_output_producer="commerce_lens.production.r4_same_evaluator_comparison",
    )


def _produce_r4_presentation_order_observation(
    fixture: LoadedR5Fixture,
) -> ActualProjection:
    material = _run_fixture_r4_material(fixture)
    authoritative_order = tuple(row.product_id for row in material.trace_rows)
    presentation_order = tuple(reversed(authoritative_order))
    if len(authoritative_order) < 2 or presentation_order == authoritative_order:
        raise PF4HarnessSetupError("presentation-order observation requires distinct product order")
    return _conformance_projection(
        validation_outcome="authoritative_result_unchanged",
        chain_disposition="presentation_order_non_material",
        final_disposition="NON_MATERIAL_ORDER_DIFFERENCE__CONFORMING",
        trace_integrity_state={
            "authoritative_values_unchanged": True,
            "presentation_order_differed": True,
        },
        actual_output_producer="commerce_lens.fixture_runner.r4_presentation_observation",
    )


def _produce_r4_material_mutation_conformance(
    fixture: LoadedR5Fixture,
) -> ActualProjection:
    left, repeated = _run_fixture_r4_material_pair(fixture)
    right = repeated.model_copy(
        update={"reconciliation_difference": left.reconciliation_difference + Decimal("0.01")}
    )
    comparison = compare_r4_material(left, right)
    difference_paths = [item.path for item in comparison.differences]
    if (
        comparison.conforming
        or comparison.failure_layer != "METHOD_CONFORMANCE"
        or difference_paths != ["r4.reconciliation_difference"]
    ):
        raise PF4HarnessSetupError("harness material mutation was not detected exactly")
    return _conformance_projection(
        validation_outcome="material_mutation_detected",
        chain_disposition="same_evaluator_nonconforming",
        final_disposition="METHOD_OR_EVALUATOR_CONFORMANCE_FAILURE",
        trace_integrity_state={
            "failure_layer": comparison.failure_layer,
            "difference_paths": difference_paths,
        },
        actual_output_producer="commerce_lens.fixture_runner.compare_r4_material",
        validation_reachability="blocked",
        authority_ref="R4 v1.0 §§32–33",
    )


def _conformance_projection(
    *,
    validation_outcome: str,
    chain_disposition: str,
    final_disposition: str,
    trace_integrity_state: dict[str, Any],
    actual_output_producer: str,
    validation_reachability: str = "reached",
    authority_ref: str | None = None,
) -> ActualProjection:
    validation_step: dict[str, Any] = {
        "stage": "validation",
        "reachability": validation_reachability,
        "outcome": validation_outcome,
    }
    blocker: str | dict[str, Any] = "NONE"
    if validation_reachability == "blocked":
        validation_step.update(
            {
                "controlling_reason": validation_outcome,
                "authority_ref": authority_ref,
            }
        )
        blocker = {
            "blocker_id": validation_outcome,
            "stage": "validation",
            "reason": validation_outcome,
            "authority_ref": authority_ref,
        }
    return ActualProjection.model_validate(
        {
            "material_path": (
                {"stage": "execution", "reachability": "reached", "outcome": "repeated_same_evaluator"},
                validation_step,
            ),
            "chain_dispositions": {"main": chain_disposition},
            "first_controlling_blocker": blocker,
            "final_disposition": final_disposition,
            "trace_integrity_state": trace_integrity_state,
            "actual_output_producer": actual_output_producer,
        }
    )


def _produce_r4_eligibility_projection(fixture: LoadedR5Fixture) -> ActualProjection:
    failure_code = _observe_r4_eligibility_failure(fixture)
    dispositions = {
        "product_identity_missing": "R4_NOT_EXECUTED__PRODUCT_IDENTITY_MISSING",
        "product_identity_defect": "R4_NOT_EXECUTED__PRODUCT_IDENTITY_CORRUPT",
        "period_coverage_incomplete": "R4_NOT_EXECUTED__PERIOD_COVERAGE_INCOMPLETE",
        "mixed_currency": "R4_NOT_EXECUTED__MIXED_CURRENCY",
        "unknown_currency": "R4_NOT_EXECUTED__UNKNOWN_CURRENCY",
        "population_binding_mismatch": "R4_NOT_EXECUTED__POPULATION_MISMATCH",
        "r4_method_authority_mismatch": "R4_NOT_EXECUTED__METHOD_VERSION_UNRESOLVED",
    }
    try:
        final_disposition = dispositions[failure_code]
    except KeyError as exc:
        raise PF4HarnessSetupError(
            f"unsupported production R4 eligibility failure: {failure_code}"
        ) from exc
    return _eligibility_failure_projection(
        failure_code=failure_code,
        final_disposition=final_disposition,
        authority_ref=_eligibility_authority_ref(failure_code),
    )


def _produce_r4_version_authority_projection(
    fixture: LoadedR5Fixture,
) -> ActualProjection:
    failure_code = _observe_r4_eligibility_failure(fixture)
    if failure_code != "r4_method_authority_mismatch":
        raise PF4HarnessSetupError("version adapter observed a non-version failure")
    return _eligibility_failure_projection(
        failure_code=failure_code,
        final_disposition="METHOD_VERSION_MISMATCH__NOT_ELIGIBLE",
        authority_ref="R4 v1.0 §§6, 24, 36",
    )


def _observe_r4_eligibility_failure(fixture: LoadedR5Fixture) -> str:
    source, baseline, comparison, scope = _fixture_facts(fixture)
    identity_state_path = _input_path_for_role(fixture, "product_identity_state")
    coverage_state_path = _input_path_for_role(fixture, "period_coverage_state")
    population_state_path = _input_path_for_role(fixture, "population_authority_state")
    method_state_path = _input_path_for_role(fixture, "method_authority_state")
    coverage_kwargs: dict[str, Any] = {}
    if coverage_state_path is not None:
        coverage = _load_period_coverage_state(coverage_state_path)
        coverage_kwargs = {
            "coverage_start_date": date.fromisoformat(coverage["observed_start_date"]),
            "coverage_end_date": date.fromisoformat(coverage["observed_end_date"]),
            "coverage_note_ref": coverage["governing_note_ref"],
        }
    with tempfile.TemporaryDirectory(prefix="r5-pf4-r4-eligibility-") as temporary:
        root = Path(temporary)
        try:
            authority = build_pf4_upstream_authority(
                source_path=source,
                baseline_period=baseline,
                comparison_period=comparison,
                scope=scope,
                artifact_store=ArtifactStore(root / "artifacts"),
                metadata_store=MetadataStore(root / "metadata.sqlite"),
                **coverage_kwargs,
            )
        except PF4UpstreamBlocked as exc:
            return _classify_upstream_r4_blocker(exc.analysis_result)
        else:
            state_paths = tuple(
                item
                for item in (
                    identity_state_path,
                    population_state_path,
                    method_state_path,
                )
                if item is not None
            )
            if len(state_paths) != 1:
                raise PF4HarnessSetupError(
                    "R4 eligibility adapter requires exactly one factual authority state"
                )
            if identity_state_path is not None:
                state = _load_confirmed_product_identity_state(identity_state_path)
                update = {
                    "confirmed_product_identity_defect_refs": tuple(
                        state["confirmed_product_identity_defect_refs"]
                    )
                }
            elif population_state_path is not None:
                update = _load_factual_json(
                    population_state_path,
                    {"baseline_population_fingerprint"},
                )
            else:
                assert method_state_path is not None
                update = _load_factual_json(method_state_path, {"method_version"})
            _require_nonblank_string_values(update)
            request = authority.r4_request.model_copy(update=update)
            try:
                run_pf4_r4(authority, request=request)
            except R4EligibilityError as exc:
                return exc.code
            else:
                raise PF4HarnessSetupError(
                    "factual authority mismatch did not block production R4"
                )


def _produce_r4_standalone_context_projection(
    fixture: LoadedR5Fixture,
) -> ActualProjection:
    actual = _material_actual_projection(_run_fixture_r4_material(fixture))
    return actual.model_copy(
        update={
            "chain_dispositions": {"main": "standalone_r4_mechanical_result"},
            "final_disposition": "R4_MAY_EXECUTE_WITHOUT_DIAGNOSTIC_PROPOSITION",
        }
    )


def _produce_r4_mechanical_semantic_boundary(
    fixture: LoadedR5Fixture,
) -> ActualProjection:
    actual = _material_actual_projection(_run_fixture_r4_material(fixture))
    return actual.model_copy(
        update={
            "chain_dispositions": {"main": "mechanical_result_only"},
            "final_disposition": (
                "VALIDATED_R4_MECHANICAL_RESULT_ONLY__NO_DIAGNOSTIC_MEANING"
            ),
        }
    )


def _produce_r4_artificial_diagnostic_authority_guard(
    fixture: LoadedR5Fixture,
) -> ActualProjection:
    source, baseline, comparison, scope = _fixture_facts(fixture)
    state_path = _input_path_for_role(fixture, "diagnostic_authority_state")
    if state_path is None:
        raise PF4HarnessSetupError("artificial diagnostic guard requires factual state")
    state = _load_factual_json(
        state_path,
        {
            "execution_context",
            "diagnostic_proposition_ref",
            "diagnostic_r3_profile_ref",
            "diagnostic_r3_profile_version",
        },
    )
    _require_nonblank_string_values(state)
    with tempfile.TemporaryDirectory(prefix="r5-pf4-r4-context-") as temporary:
        root = Path(temporary)
        authority = build_pf4_upstream_authority(
            source_path=source,
            baseline_period=baseline,
            comparison_period=comparison,
            scope=scope,
            artifact_store=ArtifactStore(root / "artifacts"),
            metadata_store=MetadataStore(root / "metadata.sqlite"),
        )
        payload = authority.r4_request.model_dump(mode="python")
        payload.update(state)
        try:
            R4DecompositionRequest.model_validate(payload)
        except ValidationError:
            pass
        else:
            raise PF4HarnessSetupError(
                "standalone request accepted fabricated diagnostic authority"
            )
    return ActualProjection.model_validate(
        {
            "material_path": (
                {
                    "stage": "r4_method_eligibility",
                    "reachability": "blocked",
                    "outcome": "artificial_diagnostic_authority",
                    "controlling_reason": "artificial_diagnostic_authority",
                    "authority_ref": "R4 v1.0 §§7–8, 23",
                },
                {
                    "stage": "execution",
                    "reachability": "not_reached",
                    "not_reached_due_to": "r4_method_eligibility",
                },
            ),
            "chain_dispositions": {"main": "non_conforming_orchestration"},
            "first_controlling_blocker": {
                "blocker_id": "execution_context_classification",
                "stage": "r4_method_eligibility",
                "reason": "artificial_diagnostic_authority",
                "authority_ref": "R4 v1.0 §§7–8, 23",
            },
            "final_disposition": (
                "NON_CONFORMING_ORCHESTRATION__ARTIFICIAL_DIAGNOSTIC_AUTHORITY"
            ),
            "trace_integrity_state": {
                "request_contract_rejected": True,
                "production_r4_entered": False,
            },
            "actual_output_producer": (
                "commerce_lens.contracts.r4.R4DecompositionRequest"
            ),
        }
    )


def _produce_r4_product_revenue_mismatch_gate(
    fixture: LoadedR5Fixture,
) -> ActualProjection:
    def mutate(authority, outcome):
        hostile = outcome.execution.executed_result.model_copy(
            update={"baseline_revenue": outcome.execution.executed_result.baseline_revenue + Decimal("1")}
        )
        hostile = hostile.model_copy(update={"result_fingerprint": _r4_result_fingerprint(hostile)})
        submission = prepare_hostile_r4_submission(
            authority,
            outcome,
            result_payload=hostile.model_dump(mode="json"),
        )
        return validate_hostile_r4_submission(authority, outcome, submission)

    observed = _observe_hostile_validation(fixture, mutate)
    return _hostile_validation_projection(
        observed,
        required_check="baseline_product_revenue_sum",
        outcome_code="product_revenue_sum_mismatch",
        final_disposition="EXECUTED_R4_RESULT_REJECTED__PRODUCT_REVENUE_SUM_MISMATCH",
    )


def _produce_r4_partition_incomplete_gate(fixture: LoadedR5Fixture) -> ActualProjection:
    def mutate(authority, outcome):
        trace = outcome.execution.product_trace
        first = trace.rows[0].model_copy(
            update={
                "classification": type(trace.rows[0].classification).COMPARISON_ONLY,
                "assigned_component": type(trace.rows[0].assigned_component).ENTRY,
            }
        )
        hostile_trace = trace.model_copy(update={"rows": (first, *trace.rows[1:])})
        hostile_trace = hostile_trace.model_copy(
            update={"trace_fingerprint": _r4_trace_fingerprint(hostile_trace)}
        )
        submission = prepare_hostile_r4_submission(
            authority,
            outcome,
            trace_payload=hostile_trace.model_dump(mode="json"),
        )
        return validate_hostile_r4_submission(authority, outcome, submission)

    observed = _observe_hostile_validation(fixture, mutate)
    return _hostile_validation_projection(
        observed,
        required_check="R4ArtifactIntegrityError",
        outcome_code="partition_incomplete",
        final_disposition="EXECUTED_R4_RESULT_REJECTED__PARTITION_INCOMPLETE",
    )


def _produce_r4_partition_overlap_gate(fixture: LoadedR5Fixture) -> ActualProjection:
    def mutate(authority, outcome):
        payload = outcome.execution.product_trace.model_dump(mode="json")
        payload["rows"].append(dict(payload["rows"][0]))
        payload["row_count"] += 1
        submission = prepare_hostile_r4_submission(
            authority,
            outcome,
            trace_payload=payload,
        )
        return validate_hostile_r4_submission(authority, outcome, submission)

    observed = _observe_hostile_validation(fixture, mutate)
    return _hostile_validation_projection(
        observed,
        required_check="R4ArtifactIntegrityError",
        outcome_code="partition_overlap",
        final_disposition="EXECUTED_R4_RESULT_REJECTED__PARTITION_OVERLAP",
    )


def _produce_r4_component_sum_mismatch_gate(fixture: LoadedR5Fixture) -> ActualProjection:
    def mutate(authority, outcome):
        hostile = outcome.execution.executed_result.model_copy(
            update={"component_sum": outcome.execution.executed_result.component_sum + Decimal("1")}
        )
        hostile = hostile.model_copy(update={"result_fingerprint": _r4_result_fingerprint(hostile)})
        submission = prepare_hostile_r4_submission(
            authority,
            outcome,
            result_payload=hostile.model_dump(mode="json"),
        )
        return validate_hostile_r4_submission(authority, outcome, submission)

    observed = _observe_hostile_validation(fixture, mutate)
    return _hostile_validation_projection(
        observed,
        required_check="component_sum",
        outcome_code="component_sum_mismatch",
        final_disposition="EXECUTED_R4_RESULT_REJECTED__COMPONENT_SUM_MISMATCH",
    )


def _produce_r4_reconciliation_mismatch_gate(fixture: LoadedR5Fixture) -> ActualProjection:
    def mutate(authority, outcome):
        hostile = outcome.execution.executed_result.model_copy(
            update={"reconciliation_difference": Decimal("1")}
        )
        hostile = hostile.model_copy(update={"result_fingerprint": _r4_result_fingerprint(hostile)})
        submission = prepare_hostile_r4_submission(
            authority,
            outcome,
            result_payload=hostile.model_dump(mode="json"),
        )
        return validate_hostile_r4_submission(authority, outcome, submission)

    observed = _observe_hostile_validation(fixture, mutate)
    return _hostile_validation_projection(
        observed,
        required_check="exact_zero_reconciliation",
        outcome_code="nonzero_reconciliation_difference",
        final_disposition=(
            "EXECUTED_R4_RESULT_REJECTED__NONZERO_RECONCILIATION_DIFFERENCE"
        ),
    )


def _produce_r4_trace_incomplete_gate(fixture: LoadedR5Fixture) -> ActualProjection:
    observed = _observe_hostile_validation(fixture, _incomplete_trace_validation)
    return _hostile_validation_projection(
        observed,
        required_check="complete_product_universe",
        outcome_code="trace_incomplete",
        final_disposition="EXECUTED_R4_RESULT_REJECTED__TRACE_INCOMPLETE",
    )


def _produce_r4_trace_integrity_gate(fixture: LoadedR5Fixture) -> ActualProjection:
    def mutate(authority, outcome):
        trace_payload = outcome.execution.product_trace.model_dump(mode="json")
        trace_payload["trace_id"] = generate_id("pf4tamper")
        submission = prepare_hostile_r4_submission(
            authority,
            outcome,
            trace_payload=trace_payload,
        )
        path = authority.artifact_store.safe_path(submission.trace_artifact.path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["rows"][0]["contribution"] = "999.00"
        path.write_bytes(canonical_json_bytes(payload))
        return validate_hostile_r4_submission(authority, outcome, submission)

    observed = _observe_hostile_validation(fixture, mutate)
    return _hostile_validation_projection(
        observed,
        required_check="R4ArtifactIntegrityError",
        outcome_code="trace_integrity_failure",
        final_disposition="EXECUTED_R4_RESULT_REJECTED__TRACE_INTEGRITY_FAILURE",
    )


def _produce_r4_post_execution_method_binding_gate(
    fixture: LoadedR5Fixture,
) -> ActualProjection:
    def mutate(authority, outcome):
        result = outcome.execution.executed_result
        hostile_authority = result.authority.model_copy(update={"method_version": "R4 v0.9"})
        hostile = result.model_copy(update={"authority": hostile_authority})
        hostile = hostile.model_copy(update={"result_fingerprint": _r4_result_fingerprint(hostile)})
        submission = prepare_hostile_r4_submission(
            authority,
            outcome,
            result_payload=hostile.model_dump(mode="json"),
        )
        return validate_hostile_r4_submission(authority, outcome, submission)

    observed = _observe_hostile_validation(fixture, mutate)
    return _hostile_validation_projection(
        observed,
        required_check="method_version_binding",
        outcome_code="method_authority_binding_mismatch",
        final_disposition=(
            "EXECUTED_R4_RESULT_REJECTED__METHOD_AUTHORITY_BINDING_MISMATCH"
        ),
    )


def _produce_r4_runtime_dependency_gate(fixture: LoadedR5Fixture) -> ActualProjection:
    import commerce_lens.engine.r4_execution as production_executor

    state_path = _input_path_for_role(fixture, "runtime_dependency_state")
    if state_path is None:
        raise PF4HarnessSetupError("runtime dependency gate requires factual state")
    state = _load_factual_json(state_path, {"dependency", "availability"})
    if state != {"dependency": "duckdb", "availability": "unavailable"}:
        raise PF4HarnessSetupError("unsupported runtime dependency state")
    source, baseline, comparison, scope = _fixture_facts(fixture)
    with tempfile.TemporaryDirectory(prefix="r5-pf4-r4-runtime-") as temporary:
        root = Path(temporary)
        authority = build_pf4_upstream_authority(
            source_path=source,
            baseline_period=baseline,
            comparison_period=comparison,
            scope=scope,
            artifact_store=ArtifactStore(root / "artifacts"),
            metadata_store=MetadataStore(root / "metadata.sqlite"),
        )
        original = production_executor.duckdb.connect

        def unavailable(*_args, **_kwargs):
            raise RuntimeError("PF4 factual runtime dependency unavailable: duckdb")

        production_executor.duckdb.connect = unavailable
        try:
            run_pf4_r4(authority)
        except Exception as exc:
            failure = classify_r4_failure(exc)
        else:
            raise PF4HarnessSetupError("R4 unexpectedly executed without runtime dependency")
        finally:
            production_executor.duckdb.connect = original
    if failure.failure_layer != "EXECUTION":
        raise PF4HarnessSetupError("runtime dependency loss did not fail in execution")
    return ActualProjection.model_validate(
        {
            "material_path": (
                {"stage": "r4_method_eligibility", "reachability": "reached", "outcome": "eligible"},
                {
                    "stage": "execution",
                    "reachability": "blocked",
                    "outcome": failure.failure_code,
                    "controlling_reason": failure.failure_code,
                    "authority_ref": "R4 v1.0 §30.2",
                },
                {
                    "stage": "validation",
                    "reachability": "not_reached",
                    "not_reached_due_to": "execution",
                },
            ),
            "chain_dispositions": {"main": "r4_execution_failed"},
            "first_controlling_blocker": {
                "blocker_id": "runtime_dependency_unavailable",
                "stage": "execution",
                "reason": failure.failure_code,
                "authority_ref": "R4 v1.0 §30.2",
            },
            "final_disposition": "R4_EXECUTION_FAILED__NO_USABLE_RESULT",
            "trace_integrity_state": {"failure_layer": "EXECUTION"},
            "actual_output_producer": "commerce_lens.engine.r4_execution.execute_r4_decomposition",
        }
    )


def _produce_r4_independent_chain_projection(fixture: LoadedR5Fixture) -> ActualProjection:
    source, baseline, comparison, scope = _fixture_facts(fixture)
    with tempfile.TemporaryDirectory(prefix="r5-pf4-r4-chain-") as temporary:
        root = Path(temporary)
        authority = build_pf4_upstream_authority(
            source_path=source,
            baseline_period=baseline,
            comparison_period=comparison,
            scope=scope,
            artifact_store=ArtifactStore(root / "artifacts"),
            metadata_store=MetadataStore(root / "metadata.sqlite"),
        )
        outcome = run_pf4_r4(authority)

        def rejected_r4():
            validation = _incomplete_trace_validation(authority, outcome)
            if validation.validated_result is None:
                raise R4ResultValidationFailure(validation)

        observation = observe_independent_scalar_and_r4(
            authority.baseline_revenue,
            rejected_r4,
        )
    if observation.r4_failure is None:
        raise PF4HarnessSetupError("independent R4 branch unexpectedly validated")
    return ActualProjection.model_validate(
        {
            "material_path": (
                {
                    "stage": "validation",
                    "chain_id": "scalar",
                    "reachability": "reached",
                    "outcome": {
                        "metric_ref": observation.scalar_metric_ref,
                        "value": str(observation.scalar_value),
                        "authority_unchanged": True,
                    },
                },
                {"stage": "execution", "chain_id": "r4", "reachability": "reached", "outcome": "completed"},
                {
                    "stage": "validation",
                    "chain_id": "r4",
                    "reachability": "blocked",
                    "outcome": "trace_incomplete",
                    "controlling_reason": "trace_incomplete",
                    "authority_ref": "R4 v1.0 §§25–26, 30.3",
                },
            ),
            "chain_dispositions": {
                "scalar": "revenue_valid",
                "r4": "r4_withheld",
            },
            "first_controlling_blocker": {
                "blocker_id": "trace_incomplete",
                "stage": "validation",
                "chain_id": "r4",
                "reason": "trace_incomplete",
                "authority_ref": "R4 v1.0 §§25–26, 30.3",
            },
            "final_disposition": "PARTIAL_MATERIAL_RESULT__REVENUE_VALID__R4_WITHHELD",
            "trace_integrity_state": {
                "scalar_authority_unchanged": True,
                "r4_failure_layer": observation.r4_failure.failure_layer,
            },
            "actual_output_producer": "commerce_lens.production.scalar_and_r4_chains",
        }
    )


def _produce_r4_material_projection_with_presentation_observation(
    fixture: LoadedR5Fixture,
) -> ActualProjection:
    material = _run_fixture_r4_material(fixture)
    if material.validation_status != "passed":
        raise PF4HarnessSetupError(
            "presentation observation requires a successfully validated R4 result"
        )
    presentation = _whole_unit_presentation_observation(material)
    return _material_actual_projection(material, presentation=presentation)


def _run_fixture_r4_material(fixture: LoadedR5Fixture) -> PF4R4MaterialProjection:
    source, baseline, comparison, scope = _fixture_facts(fixture)
    return _run_fixture_r4_material_from_source(fixture, source)


def _run_fixture_r4_material_from_source(
    fixture: LoadedR5Fixture,
    source: Path,
) -> PF4R4MaterialProjection:
    _, baseline, comparison, scope = _fixture_facts(fixture)
    with tempfile.TemporaryDirectory(prefix="r5-pf4-r4-") as temporary:
        root = Path(temporary)
        authority = build_pf4_upstream_authority(
            source_path=source,
            baseline_period=baseline,
            comparison_period=comparison,
            scope=scope,
            artifact_store=ArtifactStore(root / "artifacts"),
            metadata_store=MetadataStore(root / "metadata.sqlite"),
        )
        return project_r4_material(run_pf4_r4(authority))


def _run_fixture_r4_material_pair(
    fixture: LoadedR5Fixture,
) -> tuple[PF4R4MaterialProjection, PF4R4MaterialProjection]:
    source, baseline, comparison, scope = _fixture_facts(fixture)
    with tempfile.TemporaryDirectory(prefix="r5-pf4-r4-pair-") as temporary:
        root = Path(temporary)
        authority = build_pf4_upstream_authority(
            source_path=source,
            baseline_period=baseline,
            comparison_period=comparison,
            scope=scope,
            artifact_store=ArtifactStore(root / "artifacts"),
            metadata_store=MetadataStore(root / "metadata.sqlite"),
        )
        return (
            project_r4_material(run_pf4_r4(authority)),
            project_r4_material(run_pf4_r4(authority)),
        )


def _material_actual_projection(
    material: PF4R4MaterialProjection,
    *,
    presentation: dict[str, Any] | None = None,
) -> ActualProjection:
    fixture_material = _project_fixture_material(material)
    trace_integrity_state: dict[str, Any] = {
        "validation_status": material.validation_status,
        "all_validation_checks_passed": all(
            passed for _, passed, _ in material.validation_checks
        ),
        "trace_fingerprint_integrity": _validation_check_passed(
            material, "trace_fingerprint_integrity"
        ),
        "result_fingerprint_integrity": _validation_check_passed(
            material, "result_fingerprint_integrity"
        ),
        "exact_decimal_no_presentation_repair": _validation_check_passed(
            material, "exact_decimal_no_presentation_repair"
        ),
    }
    if presentation is not None:
        trace_integrity_state["whole_unit_presentation"] = presentation
    final_disposition = (
        PF4_PRESENTATION_ROUNDING_DISPOSITION
        if presentation is not None and presentation["appears_non_additive"]
        else "VALIDATED_R4_MECHANICAL_RESULT"
    )
    return ActualProjection.model_validate(
        {
            "material_path": (
                {"stage": "r4_method_eligibility", "reachability": "reached", "outcome": "eligible"},
                {"stage": "execution", "reachability": "reached", "outcome": "completed"},
                {
                    "stage": "validation",
                    "reachability": "reached",
                    "outcome": fixture_material,
                },
            ),
            "chain_dispositions": {"main": "validated_r4_mechanical_result"},
            "first_controlling_blocker": "NONE",
            "final_disposition": final_disposition,
            "trace_integrity_state": trace_integrity_state,
            "actual_output_producer": PF4_R4_ACTUAL_OUTPUT_PRODUCER,
        }
    )


def _eligibility_failure_projection(
    *,
    failure_code: str,
    final_disposition: str,
    authority_ref: str,
) -> ActualProjection:
    return ActualProjection.model_validate(
        {
            "material_path": (
                {
                    "stage": "r4_method_eligibility",
                    "reachability": "blocked",
                    "outcome": failure_code,
                    "controlling_reason": failure_code,
                    "authority_ref": authority_ref,
                },
                {
                    "stage": "execution",
                    "reachability": "not_reached",
                    "not_reached_due_to": "r4_method_eligibility",
                },
            ),
            "chain_dispositions": {"main": "r4_not_executed"},
            "first_controlling_blocker": {
                "blocker_id": failure_code,
                "stage": "r4_method_eligibility",
                "reason": failure_code,
                "authority_ref": authority_ref,
            },
            "final_disposition": final_disposition,
            "trace_integrity_state": {
                "failure_layer": "ELIGIBILITY",
                "production_failure_code": failure_code,
            },
            "actual_output_producer": PF4_R4_PREREQUISITE_OUTPUT_PRODUCER,
        }
    )


def _observe_hostile_validation(
    fixture: LoadedR5Fixture,
    mutation: Callable[[PF4UpstreamAuthority, R4RunOutcome], object],
) -> dict[str, Any]:
    source, baseline, comparison, scope = _fixture_facts(fixture)
    with tempfile.TemporaryDirectory(prefix="r5-pf4-r4-hostile-") as temporary:
        root = Path(temporary)
        authority = build_pf4_upstream_authority(
            source_path=source,
            baseline_period=baseline,
            comparison_period=comparison,
            scope=scope,
            artifact_store=ArtifactStore(root / "artifacts"),
            metadata_store=MetadataStore(root / "metadata.sqlite"),
        )
        outcome = run_pf4_r4(authority)
        try:
            validation = mutation(authority, outcome)
        except Exception as exc:
            failure = classify_r4_failure(exc)
            return {
                "failure_layer": failure.failure_layer,
                "failure_code": failure.failure_code,
                "failed_checks": (),
            }
    record = getattr(validation, "validation_record", None)
    if record is None or getattr(validation, "validated_result", None) is not None:
        raise PF4HarnessSetupError("hostile R4 actual was not rejected")
    return {
        "failure_layer": "RESULT_VALIDATION_OR_INTEGRITY",
        "failure_code": "r4_result_validation_failed",
        "failed_checks": tuple(
            item.check_id for item in record.checks if not item.passed
        ),
    }


def _hostile_validation_projection(
    observed: dict[str, Any],
    *,
    required_check: str,
    outcome_code: str,
    final_disposition: str,
) -> ActualProjection:
    if observed["failure_layer"] != "RESULT_VALIDATION_OR_INTEGRITY":
        raise PF4HarnessSetupError("hostile actual failed outside validation/integrity")
    if (
        required_check != observed["failure_code"]
        and required_check not in observed["failed_checks"]
    ):
        raise PF4HarnessSetupError(
            f"production validator did not observe required failure: {required_check}"
        )
    authority_ref = "R4 v1.0 §§25–26, 29, 30.3"
    return ActualProjection.model_validate(
        {
            "material_path": (
                {"stage": "r4_method_eligibility", "reachability": "reached", "outcome": "eligible"},
                {"stage": "execution", "reachability": "reached", "outcome": "completed"},
                {
                    "stage": "validation",
                    "reachability": "blocked",
                    "outcome": outcome_code,
                    "controlling_reason": outcome_code,
                    "authority_ref": authority_ref,
                },
            ),
            "chain_dispositions": {"main": "executed_r4_result_rejected"},
            "first_controlling_blocker": {
                "blocker_id": outcome_code,
                "stage": "validation",
                "reason": outcome_code,
                "authority_ref": authority_ref,
            },
            "final_disposition": final_disposition,
            "trace_integrity_state": {
                "failure_layer": "RESULT_VALIDATION_OR_INTEGRITY",
                "controlling_validation_check": required_check,
            },
            "actual_output_producer": (
                "commerce_lens.validation.r4_validator.validate_r4_decomposition"
                if required_check != "R4ArtifactIntegrityError"
                else "commerce_lens.persistence.r4_repository.load_r4_trace"
            ),
        }
    )


def _incomplete_trace_validation(
    authority: PF4UpstreamAuthority,
    outcome: R4RunOutcome,
):
    trace = outcome.execution.product_trace
    hostile_trace = trace.model_copy(
        update={"rows": trace.rows[:-1], "row_count": len(trace.rows) - 1}
    )
    hostile_trace = hostile_trace.model_copy(
        update={"trace_fingerprint": _r4_trace_fingerprint(hostile_trace)}
    )
    submission = prepare_hostile_r4_submission(
        authority,
        outcome,
        trace_payload=hostile_trace.model_dump(mode="json"),
    )
    return validate_hostile_r4_submission(authority, outcome, submission)


def _produce_r4_diagnostic_gate(fixture: LoadedR5Fixture) -> ActualProjection:
    source, baseline, comparison, scope = _fixture_facts(fixture)
    method_state_path = _input_path_for_role(fixture, "method_authority_state")
    with tempfile.TemporaryDirectory(prefix="r5-pf4-r4-diagnostic-") as temporary:
        root = Path(temporary)
        authority = build_pf4_upstream_authority(
            source_path=source,
            baseline_period=baseline,
            comparison_period=comparison,
            scope=scope,
            artifact_store=ArtifactStore(root / "artifacts"),
            metadata_store=MetadataStore(root / "metadata.sqlite"),
        )
        update = {
            "execution_context": R4ExecutionContext.DIAGNOSTIC_WORKFLOW,
            "diagnostic_proposition_ref": "pf4_unresolved_diagnostic_proposition",
            "diagnostic_r3_profile_ref": "pf4_missing_exact_r3_profile",
            "diagnostic_r3_profile_version": "unresolved",
        }
        if method_state_path is not None:
            method_state = _load_factual_json(method_state_path, {"method_version"})
            _require_nonblank_string_values(method_state)
            update.update(method_state)
        diagnostic = authority.r4_request.model_copy(update=update)
        try:
            run_pf4_r4(authority, request=diagnostic)
        except R4EligibilityError as exc:
            failure = classify_r4_failure(exc)
        else:
            raise PF4HarnessSetupError("diagnostic R4 unexpectedly executed without exact R3 authority")
    return ActualProjection.model_validate(
        {
            "material_path": (
                {
                    "stage": "r4_method_eligibility",
                    "reachability": "blocked",
                    "outcome": failure.failure_code,
                    "controlling_reason": failure.failure_code,
                    "authority_ref": "R4 v1.0 §§8.2, 23.2",
                },
                {
                    "stage": "execution",
                    "reachability": "not_reached",
                    "not_reached_due_to": "r4_method_eligibility",
                },
            ),
            "chain_dispositions": {"main": "diagnostic_r4_not_eligible"},
            "first_controlling_blocker": {
                "blocker_id": "exact_r3_profile_resolution",
                "stage": "r4_method_eligibility",
                "reason": failure.failure_code,
                "authority_ref": "R4 v1.0 §§8.2, 23.2",
            },
            "final_disposition": "R4_DIAGNOSTIC_WORKFLOW_NOT_ELIGIBLE__PROFILE_MISSING",
            "trace_integrity_state": {"failure_layer": failure.failure_layer},
            "actual_output_producer": PF4_R4_ACTUAL_OUTPUT_PRODUCER,
        }
    )


def _canonicalization_request(dataset_id: str, source: Path) -> CanonicalizationRequest:
    with source.open("r", encoding="utf-8-sig", newline="") as file_obj:
        headers = tuple(next(csv.reader(file_obj)))
    return CanonicalizationRequest(
        source_dataset_id=dataset_id,
        mapping=identity_mapping(headers, require_eligibility=True),
        eligibility_mode=EligibilityMode.EXPLICIT_STATUS_MAPPING,
        eligibility_value_mapping=(
            EligibilityValueMapping(source_value="paid", normalized_status=EligibilityState.ELIGIBLE),
            EligibilityValueMapping(source_value="cancelled", normalized_status=EligibilityState.EXCLUDED),
        ),
    )


def _one_scalar(results: tuple[ValidatedResult, ...], metric: str, period_role: str) -> ValidatedResult:
    matches = tuple(item for item in results if item.metric_ref == metric and item.period_role == period_role)
    if len(matches) != 1:
        raise PF4HarnessSetupError(f"production did not produce exactly one {metric}/{period_role} authority")
    return matches[0]


def _one_evidence(items: tuple[AdmissibleEvidence, ...], result: ValidatedResult) -> AdmissibleEvidence:
    matches = tuple(item for item in items if item.validated_result_ids == (result.validated_result_id,))
    if len(matches) != 1:
        raise PF4HarnessSetupError("production did not produce exact scalar AdmissibleEvidence")
    evidence = matches[0]
    if evidence.supported_claim_type is not ClaimType.DESCRIPTIVE or evidence.evidence_role is not EvidenceRole.METRIC_VALUE:
        raise PF4HarnessSetupError("production Evidence is not descriptive metric-value authority")
    return evidence


def _one_population(
    populations: tuple[PopulationDefinition, ...],
    role: PopulationPeriodRole,
) -> PopulationDefinition:
    matches = tuple(
        item
        for item in populations
        if item.period_role is role and item.grouping is GroupingDimension.NONE
    )
    if len(matches) != 1:
        raise PF4HarnessSetupError(f"production did not produce one governed {role.value} population")
    return matches[0]


def _required_evidence_fingerprint(evidence: AdmissibleEvidence) -> str:
    if evidence.evidence_fingerprint is None:
        raise PF4HarnessSetupError("production AdmissibleEvidence lacks its semantic fingerprint")
    return evidence.evidence_fingerprint


def _project_trace_row(row: R4ProductTraceRow) -> PF4MaterialTraceRow:
    return PF4MaterialTraceRow(
        product_id=row.product_id,
        baseline_present=row.baseline_present,
        comparison_present=row.comparison_present,
        baseline_revenue=row.baseline_revenue,
        comparison_revenue=row.comparison_revenue,
        classification=row.classification.value,
        contribution=row.contribution,
        assigned_component=row.assigned_component.value,
        currency=row.currency,
        baseline_period_ref=row.baseline_period_ref,
        comparison_period_ref=row.comparison_period_ref,
        baseline_population_ref=row.baseline_population_ref,
        comparison_population_ref=row.comparison_population_ref,
        scope_ref=row.scope_ref,
        canonical_dataset_ref=row.canonical_dataset_ref,
        canonical_dataset_fingerprint=row.canonical_dataset_fingerprint,
        method_id=row.method_id,
        method_version=row.method_version,
        precision_policy_ref=row.precision_policy_ref,
        precision_policy_version=row.precision_policy_version,
        validation_policy_id=row.validation_policy_id,
        validation_policy_version=row.validation_policy_version,
    )


def _project_fixture_material(material: PF4R4MaterialProjection) -> dict[str, Any]:
    """Expose Frozen-comparable material while retaining binding validation.

    Generated authority identifiers and fingerprints remain available in the
    full PF4 projection used by same-evaluator conformance.  Physical Frozen
    fixtures instead compare stable governed identities plus the production
    validator's exact binding checks; no expected fixture data is consulted.
    """
    authority = material.authority
    return {
        "authority": {
            "baseline_period_ref": authority.baseline_period_ref,
            "comparison_period_ref": authority.comparison_period_ref,
            "scope_ref": authority.scope_ref,
            "currency": authority.currency,
            "method_id": authority.method_id,
            "method_version": authority.method_version,
            "precision_policy_ref": authority.precision_policy_ref,
            "precision_policy_version": authority.precision_policy_version,
            "validation_policy_id": authority.validation_policy_id,
            "validation_policy_version": authority.validation_policy_version,
        },
        "authority_bindings_validated": all(
            _validation_check_passed(material, check_id)
            for check_id in (
                "execution_record_binding",
                "authority_binding",
                "method_version_binding",
                "period_binding",
                "population_binding",
                "scope_binding",
                "currency_binding",
                "canonical_dataset_binding",
                "baseline_revenue_authority",
                "comparison_revenue_authority",
                "observed_revenue_change_authority",
            )
        ),
        "baseline_revenue": str(material.baseline_revenue),
        "comparison_revenue": str(material.comparison_revenue),
        "observed_revenue_change": str(material.observed_revenue_change),
        "entry_component": str(material.entry_component),
        "exit_component": str(material.exit_component),
        "continuing_component": str(material.continuing_component),
        "component_sum": str(material.component_sum),
        "reconciliation_difference": str(material.reconciliation_difference),
        "product_count": material.product_count,
        "entry_product_count": material.entry_product_count,
        "exit_product_count": material.exit_product_count,
        "continuing_product_count": material.continuing_product_count,
        "trace_rows": [
            {
                "product_id": row.product_id,
                "baseline_present": row.baseline_present,
                "comparison_present": row.comparison_present,
                "baseline_revenue": str(row.baseline_revenue),
                "comparison_revenue": str(row.comparison_revenue),
                "classification": row.classification,
                "contribution": str(row.contribution),
                "assigned_component": row.assigned_component,
                "currency": row.currency,
                "baseline_period_ref": row.baseline_period_ref,
                "comparison_period_ref": row.comparison_period_ref,
                "scope_ref": row.scope_ref,
                "method_id": row.method_id,
                "method_version": row.method_version,
                "precision_policy_ref": row.precision_policy_ref,
                "precision_policy_version": row.precision_policy_version,
                "validation_policy_id": row.validation_policy_id,
                "validation_policy_version": row.validation_policy_version,
            }
            for row in material.trace_rows
        ],
        "execution_status": material.execution_status,
        "validation_status": material.validation_status,
        "semantic_boundary": material.semantic_boundary,
    }


def _validation_check_passed(material: PF4R4MaterialProjection, check_id: str) -> bool:
    matches = tuple(
        passed
        for observed_id, passed, _ in material.validation_checks
        if observed_id == check_id
    )
    if len(matches) != 1:
        raise PF4HarnessSetupError(f"production R4 validation check is missing or ambiguous: {check_id}")
    return matches[0]


def _whole_unit_presentation_observation(
    material: PF4R4MaterialProjection,
) -> dict[str, Any]:
    """Observe display-only rounding after validation; never alter authority."""
    unit = Decimal("1")
    entry = material.entry_component.quantize(unit, rounding=ROUND_HALF_EVEN)
    exit_value = material.exit_component.quantize(unit, rounding=ROUND_HALF_EVEN)
    continuing = material.continuing_component.quantize(unit, rounding=ROUND_HALF_EVEN)
    component_sum = material.component_sum.quantize(unit, rounding=ROUND_HALF_EVEN)
    observed_change = material.observed_revenue_change.quantize(unit, rounding=ROUND_HALF_EVEN)
    displayed_component_total = entry + exit_value + continuing
    return {
        "display_precision": "whole_unit",
        "rounding": "ROUND_HALF_EVEN",
        "entry": str(entry),
        "exit": str(exit_value),
        "continuing": str(continuing),
        "displayed_component_total": str(displayed_component_total),
        "component_sum": str(component_sum),
        "observed_revenue_change": str(observed_change),
        "appears_non_additive": displayed_component_total != observed_change,
        "authoritative_values_unchanged": True,
    }


def _material_diff(path: str, left: Any, right: Any, output: list[PF4MaterialDifference]) -> None:
    if isinstance(left, dict) and isinstance(right, dict):
        for key in sorted(set(left) | set(right)):
            _material_diff(f"{path}.{key}", left.get(key), right.get(key), output)
        return
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            output.append(PF4MaterialDifference(path=f"{path}.length", left=len(left), right=len(right)))
        for index, (left_item, right_item) in enumerate(zip(left, right, strict=False)):
            _material_diff(f"{path}[{index}]", left_item, right_item, output)
        return
    if left != right:
        output.append(PF4MaterialDifference(path=path, left=left, right=right))


def _reject_expected_oracle_keys(value: Any) -> None:
    if isinstance(value, dict):
        forbidden = _FORBIDDEN_HOSTILE_KEYS.intersection(value)
        if forbidden:
            raise PF4HarnessSetupError(f"hostile actual artifact contains expected-output key: {sorted(forbidden)[0]}")
        for item in value.values():
            _reject_expected_oracle_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_expected_oracle_keys(item)


def _fixture_facts(
    fixture: LoadedR5Fixture,
) -> tuple[Path, PeriodDefinition, PeriodDefinition, ScopeDefinition]:
    source = next(
        (path for spec, path in zip(fixture.manifest.inputs, fixture.input_paths, strict=True) if spec.role == "orders"),
        None,
    )
    if source is None:
        raise PF4HarnessSetupError("PF4 production adapter requires one verified orders input")
    periods = fixture.manifest.context.periods
    if len(periods) != 2:
        raise PF4HarnessSetupError("PF4 production adapter requires Baseline and Comparison periods")
    converted = tuple(
        PeriodDefinition(
            period_id=item.period_id,
            label=item.label,
            start_date=date.fromisoformat(item.start_date),
            end_date=date.fromisoformat(item.end_date),
            date_convention_ref=item.date_convention_ref,
        )
        for item in periods
    )
    scope_payload = fixture.manifest.context.scope or {"scope_id": "all_eligible"}
    return source, converted[0], converted[1], ScopeDefinition.model_validate(scope_payload)


def _input_path_for_role(fixture: LoadedR5Fixture, role: str) -> Path | None:
    matches = tuple(
        path
        for spec, path in zip(fixture.manifest.inputs, fixture.input_paths, strict=True)
        if spec.role == role
    )
    if len(matches) > 1:
        raise PF4HarnessSetupError(f"PF4 fixture has ambiguous {role} factual input")
    return matches[0] if matches else None


def _classify_upstream_r4_blocker(analysis_result: object) -> str:
    details = getattr(analysis_result, "failure_details", ())
    reasons = tuple(getattr(item, "reason", "") for item in details)
    if any("product_id is required and must not be null" in reason for reason in reasons):
        return "product_identity_missing"
    if any(
        "coverage evidence does not span" in reason
        or "coverage does not fully include requested period" in reason
        for reason in reasons
    ):
        return "period_coverage_incomplete"
    if any("multiple unnormalized currencies" in reason for reason in reasons):
        return "mixed_currency"
    if any("currency is required and must not be null" in reason for reason in reasons):
        return "unknown_currency"
    raise PF4HarnessSetupError(
        "production analysis blocked for an unsupported R4 prerequisite reason"
    )


def _load_confirmed_product_identity_state(path: Path) -> dict[str, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PF4HarnessSetupError("product identity state is not valid factual JSON") from exc
    if not isinstance(payload, dict) or set(payload) != {"confirmed_product_identity_defect_refs"}:
        raise PF4HarnessSetupError("product identity state has unsupported fields")
    refs = payload["confirmed_product_identity_defect_refs"]
    if (
        not isinstance(refs, list)
        or not refs
        or any(not isinstance(item, str) or not item.strip() for item in refs)
    ):
        raise PF4HarnessSetupError("confirmed product identity defect refs are invalid")
    return payload


def _load_factual_json(path: Path, allowed_keys: set[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PF4HarnessSetupError("PF4 factual state is not valid JSON") from exc
    if not isinstance(payload, dict) or set(payload) != allowed_keys:
        raise PF4HarnessSetupError("PF4 factual state has unsupported fields")
    _reject_expected_oracle_keys(payload)
    return payload


def _require_nonblank_string_values(payload: dict[str, Any]) -> None:
    def valid(value: Any) -> bool:
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, tuple):
            return bool(value) and all(isinstance(item, str) and item.strip() for item in value)
        return False

    if any(not valid(value) for value in payload.values()):
        raise PF4HarnessSetupError("PF4 factual authority values must be nonblank strings")


def _load_period_coverage_state(path: Path) -> dict[str, str]:
    payload = _load_factual_json(path, {"dataset_coverage"})
    coverage = payload["dataset_coverage"]
    required = {
        "observed_start_date",
        "observed_end_date",
        "date_convention_ref",
        "governing_note_ref",
    }
    if not isinstance(coverage, dict) or set(coverage) != required:
        raise PF4HarnessSetupError("period coverage state has unsupported fields")
    if any(not isinstance(value, str) or not value.strip() for value in coverage.values()):
        raise PF4HarnessSetupError("period coverage state values must be nonblank strings")
    try:
        date.fromisoformat(coverage["observed_start_date"])
        date.fromisoformat(coverage["observed_end_date"])
    except ValueError as exc:
        raise PF4HarnessSetupError("period coverage dates are invalid") from exc
    return coverage


def _eligibility_authority_ref(failure_code: str) -> str:
    if failure_code.startswith("product_identity"):
        return "R4 v1.0 §§22.4, 24, 30.1"
    if failure_code == "period_coverage_incomplete":
        return "R4 v1.0 §§9, 24, 30.1"
    if failure_code in {"mixed_currency", "unknown_currency"}:
        return "R4 v1.0 §§11, 24, 30.1"
    if failure_code == "population_binding_mismatch":
        return "R4 v1.0 §§10, 24, 30.1"
    if failure_code == "r4_method_authority_mismatch":
        return "R4 v1.0 §§6, 24, 36"
    raise PF4HarnessSetupError(f"no Frozen authority mapping for {failure_code}")
