"""Bounded internal application service for standalone R4 execution."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from commerce_lens.contracts.common import ClaimType, GroupingDimension, MetricState
from commerce_lens.contracts.evidence import AdmissibleEvidence, CanonicalDatasetReference, EvidenceRole
from commerce_lens.contracts.plans import ExecutionPlan
from commerce_lens.contracts.populations import PopulationDefinition, PopulationPeriodRole
from commerce_lens.contracts.r4 import (
    R4_METHOD_ID,
    R4_METHOD_VERSION,
    R4_VALIDATION_POLICY_ID,
    R4_VALIDATION_POLICY_VERSION,
    R4AuthorityBinding,
    R4DecompositionRequest,
    R4ExecutionContext,
    ValidatedR4DecompositionResult,
)
from commerce_lens.contracts.sufficiency import SufficiencyState
from commerce_lens.engine.plan_builder import build_execution_plan
from commerce_lens.engine.populations import material_scope_payload, population_fingerprint, population_id_for_fingerprint
from commerce_lens.engine.r4_execution import R4ExecutionOutcome, execute_r4_decomposition
from commerce_lens.evidence.admissibility import (
    EvidenceAdmissibilityError,
    retrieve_admissible_evidence_authority,
)
from commerce_lens.metrics.registry import PRECISION_POLICY_REF, PRECISION_POLICY_VERSION
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.persistence.r4_repository import (
    R4ArtifactIntegrityError,
    load_authenticated_scalar_validated_result,
    persist_r4_request,
)
from commerce_lens.validation.r4_validator import R4ValidationOutcome, validate_r4_decomposition


class R4EligibilityError(RuntimeError):
    """A request or governed prerequisite failed before R4 execution."""

    def __init__(self, code: str, reason: str) -> None:
        super().__init__(reason)
        self.code = code


class R4ResultValidationFailure(RuntimeError):
    """Execution produced an R4 result but independent validation rejected it."""

    def __init__(self, outcome: R4ValidationOutcome) -> None:
        super().__init__("R4 executed result failed independent validation")
        self.outcome = outcome


@dataclass(frozen=True)
class R4RunOutcome:
    execution: R4ExecutionOutcome
    validation: R4ValidationOutcome
    validated_result: ValidatedR4DecompositionResult


def run_r4_decomposition(
    *,
    request: R4DecompositionRequest,
    plan: ExecutionPlan,
    canonical_dataset: CanonicalDatasetReference,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> R4RunOutcome:
    """Run the non-public standalone R4 method against authenticated authorities."""
    metadata_store.initialize()
    if request.execution_context is R4ExecutionContext.DIAGNOSTIC_WORKFLOW:
        raise R4EligibilityError(
            "diagnostic_r3_authority_unavailable",
            "R4 diagnostic execution is not eligible because exact authenticated R3 profile authority is unavailable",
        )
    if (
        request.method_id != R4_METHOD_ID
        or request.method_version != R4_METHOD_VERSION
        or request.precision_policy_ref != PRECISION_POLICY_REF
        or request.precision_policy_version != PRECISION_POLICY_VERSION
        or request.validation_policy_id != R4_VALIDATION_POLICY_ID
        or request.validation_policy_version != R4_VALIDATION_POLICY_VERSION
    ):
        raise R4EligibilityError(
            "r4_method_authority_mismatch",
            "R4 request method, precision, or validation authority is unsupported or stale",
        )
    if request.confirmed_product_identity_defect_refs:
        raise R4EligibilityError(
            "product_identity_defect",
            "R4 execution is blocked by confirmed unresolved product identity defects",
        )
    persist_r4_request(request, artifact_store, metadata_store)
    try:
        analysis_request = metadata_store.get_analysis_request(request.analysis_request_ref, artifact_store)
        sufficiency = metadata_store.get_data_sufficiency_result(request.sufficiency_ref, artifact_store)
    except RuntimeError as exc:
        raise R4ArtifactIntegrityError(f"R4 upstream authority authentication failed: {exc}") from exc
    if analysis_request is None or sufficiency is None:
        raise R4EligibilityError("missing_governed_authority", "R4 request or sufficiency authority is missing")
    if sufficiency.state is not SufficiencyState.SUFFICIENT:
        raise R4EligibilityError("insufficient_governed_evidence", "R4 requires sufficient governed evidence authority")
    revenue_change_eligibility = [
        item for item in sufficiency.metric_eligibility if item.metric_ref == "revenue_change"
    ]
    if len(revenue_change_eligibility) != 1 or not revenue_change_eligibility[0].eligible:
        raise R4EligibilityError("revenue_change_not_eligible", "authoritative Revenue Change chain is not eligible")
    if "revenue_change" not in {metric.metric_id for metric in analysis_request.metrics}:
        raise R4EligibilityError("missing_revenue_change_authority", "analysis authority does not request Revenue Change")
    expected_plan = build_execution_plan(analysis_request, sufficiency)
    if plan != expected_plan:
        raise R4EligibilityError("plan_authority_mismatch", "supplied plan is not the deterministic governed plan")
    if request.plan_ref != plan.plan_id or request.plan_fingerprint != plan.plan_fingerprint:
        raise R4EligibilityError("plan_binding_mismatch", "R4 request plan binding is stale or mismatched")
    stored_canonical = metadata_store.get_canonical_dataset(canonical_dataset.canonical_dataset_id)
    if stored_canonical != canonical_dataset:
        raise R4ArtifactIntegrityError("canonical dataset reference is not exact MetadataStore authority")
    if (
        request.canonical_dataset_ref != canonical_dataset.canonical_dataset_id
        or request.canonical_dataset_fingerprint != canonical_dataset.content_fingerprint
        or sufficiency.canonical_dataset_ref_id != canonical_dataset.canonical_dataset_id
    ):
        raise R4EligibilityError("canonical_dataset_binding_mismatch", "R4 canonical dataset binding is mismatched")
    baseline_population = _population(plan, request.baseline_population_ref, PopulationPeriodRole.BASELINE)
    comparison_population = _population(plan, request.comparison_population_ref, PopulationPeriodRole.COMPARISON)
    _validate_population_authority(request, baseline_population, comparison_population)
    _validate_periods(baseline_population, comparison_population)

    baseline_revenue = load_authenticated_scalar_validated_result(
        request.baseline_revenue_validated_result_ref,
        artifact_store,
        metadata_store,
    )
    comparison_revenue = load_authenticated_scalar_validated_result(
        request.comparison_revenue_validated_result_ref,
        artifact_store,
        metadata_store,
    )
    revenue_change = load_authenticated_scalar_validated_result(
        request.revenue_change_validated_result_ref,
        artifact_store,
        metadata_store,
    )
    _validate_scalar_authorities(
        plan,
        canonical_dataset,
        baseline_population,
        comparison_population,
        baseline_revenue,
        comparison_revenue,
        revenue_change,
    )
    baseline_evidence = _load_evidence(request.baseline_revenue_evidence_ref, artifact_store, metadata_store)
    comparison_evidence = _load_evidence(request.comparison_revenue_evidence_ref, artifact_store, metadata_store)
    change_evidence = _load_evidence(request.revenue_change_evidence_ref, artifact_store, metadata_store)
    _validate_evidence_authorities(
        request,
        analysis_request,
        sufficiency,
        canonical_dataset,
        baseline_population,
        comparison_population,
        baseline_revenue,
        comparison_revenue,
        revenue_change,
        baseline_evidence,
        comparison_evidence,
        change_evidence,
    )
    currency = baseline_revenue.currency
    assert currency is not None
    authority = R4AuthorityBinding(
        analysis_request_ref=analysis_request.request_id,
        sufficiency_ref=sufficiency.sufficiency_id,
        plan_ref=plan.plan_id,
        plan_fingerprint=plan.plan_fingerprint,
        canonical_dataset_ref=canonical_dataset.canonical_dataset_id,
        canonical_dataset_fingerprint=canonical_dataset.content_fingerprint,
        baseline_period_ref=baseline_population.period.period_id,
        comparison_period_ref=comparison_population.period.period_id,
        baseline_population_ref=baseline_population.population_id,
        baseline_population_fingerprint=baseline_population.population_fingerprint,
        comparison_population_ref=comparison_population.population_id,
        comparison_population_fingerprint=comparison_population.population_fingerprint,
        scope_ref=baseline_population.scope.scope_id,
        currency=currency,
        baseline_revenue_validated_result_ref=baseline_revenue.validated_result_id,
        baseline_revenue_validation_fingerprint=baseline_revenue.validation_fingerprint,
        comparison_revenue_validated_result_ref=comparison_revenue.validated_result_id,
        comparison_revenue_validation_fingerprint=comparison_revenue.validation_fingerprint,
        revenue_change_validated_result_ref=revenue_change.validated_result_id,
        revenue_change_validation_fingerprint=revenue_change.validation_fingerprint,
        baseline_revenue_evidence_ref=baseline_evidence.evidence_id,
        baseline_revenue_evidence_fingerprint=baseline_evidence.evidence_fingerprint,
        comparison_revenue_evidence_ref=comparison_evidence.evidence_id,
        comparison_revenue_evidence_fingerprint=comparison_evidence.evidence_fingerprint,
        revenue_change_evidence_ref=change_evidence.evidence_id,
        revenue_change_evidence_fingerprint=change_evidence.evidence_fingerprint,
        precision_policy_ref=PRECISION_POLICY_REF,
        precision_policy_version=PRECISION_POLICY_VERSION,
    )
    execution = execute_r4_decomposition(
        request=request,
        authority=authority,
        canonical_dataset=canonical_dataset,
        baseline_population=baseline_population,
        comparison_population=comparison_population,
        baseline_revenue=baseline_revenue.value,
        comparison_revenue=comparison_revenue.value,
        observed_revenue_change=revenue_change.value,
        artifact_store=artifact_store,
        metadata_store=metadata_store,
    )
    validation = validate_r4_decomposition(
        executed_result_artifact=execution.executed_result_artifact,
        execution_record=execution.execution_record,
        execution_record_artifact=execution.execution_record_artifact,
        canonical_dataset=canonical_dataset,
        baseline_population=baseline_population,
        comparison_population=comparison_population,
        baseline_revenue_authority=baseline_revenue,
        comparison_revenue_authority=comparison_revenue,
        revenue_change_authority=revenue_change,
        artifact_store=artifact_store,
        metadata_store=metadata_store,
    )
    if validation.validated_result is None:
        raise R4ResultValidationFailure(validation)
    return R4RunOutcome(execution, validation, validation.validated_result)


def _population(
    plan: ExecutionPlan,
    population_ref: str,
    expected_role: PopulationPeriodRole,
) -> PopulationDefinition:
    matches = [item for item in plan.population_definitions if item.population_id == population_ref]
    if len(matches) != 1:
        raise R4EligibilityError("population_authority_missing", "R4 population authority is missing or ambiguous")
    population = matches[0]
    if population.period_role is not expected_role or population.grouping is not GroupingDimension.NONE:
        raise R4EligibilityError("population_authority_mismatch", "R4 requires total governed Baseline and Comparison populations")
    recomputed = population_fingerprint(population)
    if recomputed != population.population_fingerprint or population_id_for_fingerprint(recomputed) != population.population_id:
        raise R4EligibilityError("population_integrity_failure", "R4 population fingerprint authority is invalid")
    return population


def _validate_population_authority(request, baseline, comparison) -> None:
    if (
        request.baseline_population_fingerprint != baseline.population_fingerprint
        or request.comparison_population_fingerprint != comparison.population_fingerprint
    ):
        raise R4EligibilityError("population_binding_mismatch", "R4 request population binding is stale or mismatched")
    if baseline.canonical_dataset_ref_id != comparison.canonical_dataset_ref_id:
        raise R4EligibilityError("population_dataset_mismatch", "R4 populations use different canonical datasets")
    if baseline.dataset_ref_id != comparison.dataset_ref_id:
        raise R4EligibilityError("population_dataset_mismatch", "R4 populations use different source datasets")
    if material_scope_payload(baseline.scope) != material_scope_payload(comparison.scope):
        raise R4EligibilityError("scope_mismatch", "R4 populations do not share one governed material scope")
    if baseline.eligibility_rule_ref != comparison.eligibility_rule_ref:
        raise R4EligibilityError("eligibility_mismatch", "R4 populations use different eligibility rules")
    if baseline.currency_basis_ref != comparison.currency_basis_ref:
        raise R4EligibilityError("currency_basis_mismatch", "R4 populations use different currency bases")


def _validate_periods(baseline, comparison) -> None:
    if baseline.period.end_date >= comparison.period.start_date:
        raise R4EligibilityError("period_overlap_or_direction", "R4 Baseline must precede and not overlap Comparison")
    baseline_days = (baseline.period.end_date - baseline.period.start_date).days + 1
    comparison_days = (comparison.period.end_date - comparison.period.start_date).days + 1
    if baseline_days != comparison_days:
        raise R4EligibilityError("period_duration_mismatch", "R4 governed comparison periods must have equal duration")
    if baseline.period.date_convention_ref != comparison.period.date_convention_ref:
        raise R4EligibilityError("period_convention_mismatch", "R4 periods use different date conventions")


def _validate_scalar_authorities(
    plan,
    canonical_dataset,
    baseline_population,
    comparison_population,
    baseline,
    comparison,
    change,
) -> None:
    authorities = (baseline, comparison, change)
    if any(item.metric_state is not MetricState.VALID for item in authorities):
        raise R4EligibilityError("invalid_metric_authority", "R4 requires Valid Revenue and Revenue Change authorities")
    if (baseline.metric_ref, comparison.metric_ref, change.metric_ref) != ("revenue", "revenue", "revenue_change"):
        raise R4EligibilityError("metric_authority_mismatch", "R4 scalar authorities have wrong Metric identities")
    if baseline.period_role != "baseline" or comparison.period_role != "comparison" or change.period_role != "baseline_and_comparison":
        raise R4EligibilityError("metric_period_role_mismatch", "R4 scalar authorities have wrong period roles")
    if baseline.population_ref != baseline_population.population_id or comparison.population_ref != comparison_population.population_id:
        raise R4EligibilityError("metric_population_mismatch", "R4 Revenue authorities do not match governed populations")
    if change.population_ref != comparison_population.population_id:
        raise R4EligibilityError("metric_population_mismatch", "R4 Revenue Change authority does not retain comparison population binding")
    if any(item.plan_id != plan.plan_id for item in authorities):
        raise R4EligibilityError("metric_plan_mismatch", "R4 scalar authorities do not share the governed plan")
    if any(
        item.canonical_dataset_ref_id != canonical_dataset.canonical_dataset_id
        or item.canonical_dataset_fingerprint != canonical_dataset.content_fingerprint
        for item in authorities
    ):
        raise R4EligibilityError("metric_dataset_mismatch", "R4 scalar authorities do not share canonical authority")
    if any(not isinstance(item.value, Decimal) or not item.value.is_finite() for item in authorities):
        raise R4EligibilityError("metric_value_invalid", "R4 scalar authorities require finite Decimal values")
    if baseline.currency is None or baseline.currency != comparison.currency or baseline.currency != change.currency:
        raise R4EligibilityError("currency_mismatch", "R4 scalar authorities do not share one governed currency")
    if change.value != comparison.value - baseline.value:
        raise R4EligibilityError("revenue_change_authority_mismatch", "Revenue Change authority does not bind exact Revenue anchors")


def _load_evidence(evidence_id, artifact_store, metadata_store) -> AdmissibleEvidence:
    try:
        return retrieve_admissible_evidence_authority(
            evidence_id,
            artifact_store=artifact_store,
            metadata_store=metadata_store,
        )
    except EvidenceAdmissibilityError as exc:
        raise R4EligibilityError(exc.failure_code, exc.reason) from exc


def _validate_evidence_authorities(
    request,
    analysis_request,
    sufficiency,
    canonical_dataset,
    baseline_population,
    comparison_population,
    baseline,
    comparison,
    change,
    baseline_evidence,
    comparison_evidence,
    change_evidence,
) -> None:
    bindings = (
        (
            baseline_evidence,
            request.baseline_revenue_evidence_fingerprint,
            baseline,
            baseline_population,
        ),
        (
            comparison_evidence,
            request.comparison_revenue_evidence_fingerprint,
            comparison,
            comparison_population,
        ),
        (
            change_evidence,
            request.revenue_change_evidence_fingerprint,
            change,
            comparison_population,
        ),
    )
    for evidence, requested_fingerprint, scalar, population in bindings:
        if evidence.evidence_fingerprint != requested_fingerprint:
            raise R4EligibilityError("evidence_fingerprint_mismatch", "R4 Evidence fingerprint binding is stale or mismatched")
        exact_lineage = (
            evidence.supported_claim_type is ClaimType.DESCRIPTIVE
            and evidence.evidence_role is EvidenceRole.METRIC_VALUE
            and evidence.request_id == analysis_request.request_id
            and evidence.sufficiency_id == sufficiency.sufficiency_id
            and evidence.validated_result_ids == (scalar.validated_result_id,)
            and evidence.validation_record_ids == scalar.required_validation_record_ids
            and evidence.executed_result_id == scalar.executed_result_id
            and evidence.execution_id == scalar.execution_id
            and evidence.metric_ref == scalar.metric_ref
            and evidence.metric_definition_version == scalar.metric_definition_version
            and evidence.dataset_ref_id == analysis_request.dataset_ref_id
            and evidence.canonical_dataset_ref_id == canonical_dataset.canonical_dataset_id
            and evidence.canonical_dataset_fingerprint == canonical_dataset.content_fingerprint
            and evidence.population_ref == scalar.population_ref == population.population_id
            and evidence.population_fingerprint == scalar.population_fingerprint == population.population_fingerprint
            and evidence.period_ref == scalar.period_ref
            and evidence.period_role == scalar.period_role
            and evidence.scope == analysis_request.scope
        )
        if not exact_lineage:
            raise R4EligibilityError(
                "evidence_authority_lineage_mismatch",
                "R4 requires exact descriptive AdmissibleEvidence lineage for each scalar authority",
            )
