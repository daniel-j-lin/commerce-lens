"""Private R6-4 governed candidate-generation application service."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import Field

from commerce_lens.canonical.schema import (
    CANONICAL_FIELD_DEFINITIONS,
    CANONICAL_SCHEMA_VERSION,
)
from commerce_lens.contracts.common import ArtifactReference, ContractBase, GroupingDimension, MetricState
from commerce_lens.contracts.diagnostic import AuthorityBinding, TestEligibility
from commerce_lens.contracts.hypotheses import (
    GenerationProvenance,
    GovernedHypothesis,
    R6ToR7Handoff,
    generation_provenance_semantic_fingerprint,
    governed_hypothesis_semantic_fingerprint,
    r6_to_r7_handoff_semantic_fingerprint,
)
from commerce_lens.contracts.plans import ExecutionPlan
from commerce_lens.contracts.populations import PopulationDefinition, PopulationPeriodRole
from commerce_lens.contracts.required_evidence import DependencyClassification, RequirementOutcome
from commerce_lens.contracts.r4 import ValidatedR4DecompositionResult
from commerce_lens.diagnostic.family_registry import MVP_FAMILY_REGISTRY
from commerce_lens.diagnostic.generator import (
    CANDIDATE_BATCH_SCHEMA_VERSION,
    INTENDED_USE_AUTHORITY_FINGERPRINT,
    INTENDED_USE_AUTHORITY_REF,
    INTENDED_USE_AUTHORITY_VERSION,
    AllowedSlotBinding,
    CandidateDiagnostic,
    CandidateFamilyView,
    CandidateGenerationContext,
    CandidateProducer,
    CandidateProducerDescriptor,
    FamilyActivation,
    GenerationBoundaryError,
    R6GenerationRequest,
    SourceAuthorityClass,
    SourceAuthorityView,
    build_candidate_generation_context,
    validate_and_construct_propositions,
    validate_candidate_batch,
)
from commerce_lens.diagnostic.governance import (
    AuthorityClass,
    GovernanceAuthenticationError,
    PreTestAuthorityRegistry,
    RegisteredAuthority,
    govern_pretest,
    pretest_authority_registry_fingerprint,
)
from commerce_lens.engine.plan_builder import build_execution_plan
from commerce_lens.engine.populations import population_fingerprint, population_id_for_fingerprint
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, stable_content_id
from commerce_lens.metrics.registry import METRIC_DEFINITION_VERSION, get_metric_registry
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.persistence.r4_repository import (
    R4ArtifactIntegrityError,
    load_authenticated_scalar_validated_result,
    load_validated_r4_result,
)
from commerce_lens.persistence.r6_repository import R6ArtifactIntegrityError, R6Repository


R6_APPLICATION_SCHEMA_VERSION = "1.0.0"


class R6CompletionStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL_FAILURE = "PARTIAL_FAILURE"
    GENERATION_FAILURE = "GENERATION_FAILURE"
    GOVERNANCE_FAILURE = "GOVERNANCE_FAILURE"
    PERSISTENCE_FAILURE = "PERSISTENCE_FAILURE"


class R6ApplicationDiagnostic(ContractBase):
    stage: str = Field(min_length=1)
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    candidate_fingerprint: str | None = None
    proposition_ref: str | None = None
    family_id: str | None = None


class R6ChainReferences(ContractBase):
    candidate_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    duplicate_candidate_fingerprints: tuple[str, ...] = ()
    diagnostic_proposition_ref: str = Field(min_length=1)
    resolved_profile_ref: str = Field(min_length=1)
    requirement_judgment_bundle_ref: str = Field(min_length=1)
    pretest_evaluation_ref: str = Field(min_length=1)
    generation_provenance_ref: str = Field(min_length=1)
    governed_hypothesis_ref: str = Field(min_length=1)
    handoff_ref: str | None = None
    test_eligibility: TestEligibility


class R6RunOutcome(ContractBase):
    result_schema_version: str = R6_APPLICATION_SCHEMA_VERSION
    generation_request_ref: str = Field(min_length=1)
    context_ref: str | None = None
    raw_candidate_artifact_ref: str | None = None
    accepted_candidate_fingerprints: tuple[str, ...] = ()
    chains: tuple[R6ChainReferences, ...] = ()
    diagnostics: tuple[R6ApplicationDiagnostic, ...] = ()
    partial_persisted_refs: tuple[str, ...] = ()
    completion_status: R6CompletionStatus


class R6ApplicationError(RuntimeError):
    """Unexpected private orchestration failure with preserved partial references."""

    def __init__(self, code: str, message: str, *, partial_refs: tuple[str, ...] = ()) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.partial_refs = partial_refs


def run_r6(
    *,
    generation_request: R6GenerationRequest,
    producer: CandidateProducer,
    producer_descriptor: CandidateProducerDescriptor,
    analysis_request_ref: str,
    sufficiency_ref: str,
    plan: ExecutionPlan,
    revenue_change_validated_result_ref: str,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    generated_at: datetime,
    finalized_at: datetime,
    r4_validated_result_artifact: ArtifactReference | None = None,
    persist_handoff: bool = False,
) -> R6RunOutcome:
    """Run private R6 orchestration without creating analytical authority itself."""

    if generated_at.tzinfo is None or generated_at.utcoffset() is None:
        raise R6ApplicationError("invalid_generation_time", "generated_at must be timezone-aware")
    if finalized_at.tzinfo is None or finalized_at.utcoffset() is None:
        raise R6ApplicationError("invalid_finalization_time", "finalized_at must be timezone-aware")

    try:
        context, source_views = _authenticate_and_build_context(
            generation_request=generation_request,
            analysis_request_ref=analysis_request_ref,
            sufficiency_ref=sufficiency_ref,
            supplied_plan=plan,
            revenue_change_validated_result_ref=revenue_change_validated_result_ref,
            artifact_store=artifact_store,
            metadata_store=metadata_store,
            r4_validated_result_artifact=r4_validated_result_artifact,
        )
    except (ValueError, RuntimeError, R4ArtifactIntegrityError) as exc:
        return _failure_outcome(
            generation_request.generation_request_ref,
            R6CompletionStatus.GENERATION_FAILURE,
            "authentication",
            getattr(exc, "code", "upstream_authority_failure"),
            str(exc),
        )

    try:
        raw_batch = producer.produce_candidates(context)
    except Exception as exc:
        return _failure_outcome(
            generation_request.generation_request_ref,
            R6CompletionStatus.GENERATION_FAILURE,
            "generation",
            "producer_exception",
            str(exc) or type(exc).__name__,
            context_ref=context.context_id,
        )
    try:
        batch = validate_candidate_batch(raw_batch, descriptor=producer_descriptor, context=context)
    except GenerationBoundaryError as exc:
        return _failure_outcome(
            generation_request.generation_request_ref,
            R6CompletionStatus.GENERATION_FAILURE,
            "generation",
            exc.code,
            str(exc),
            context_ref=context.context_id,
        )

    try:
        raw_reference = _persist_raw_candidate_batch(
            batch,
            generation_request_ref=generation_request.generation_request_ref,
            artifact_store=artifact_store,
            metadata_store=metadata_store,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        return _failure_outcome(
            generation_request.generation_request_ref,
            R6CompletionStatus.PERSISTENCE_FAILURE,
            "persistence",
            "raw_candidate_persistence_failure",
            str(exc),
            context_ref=context.context_id,
        )

    validation = validate_and_construct_propositions(batch, context)
    diagnostics = [_application_diagnostic(item) for item in validation.diagnostics]
    accepted_fingerprints = tuple(item.candidate_fingerprint for item in validation.accepted)
    if not validation.accepted:
        return R6RunOutcome(
            generation_request_ref=generation_request.generation_request_ref,
            context_ref=context.context_id,
            raw_candidate_artifact_ref=raw_reference.artifact_id,
            accepted_candidate_fingerprints=(),
            diagnostics=tuple(diagnostics),
            completion_status=R6CompletionStatus.GENERATION_FAILURE,
        )

    provenance = _build_generation_provenance(
        producer_descriptor,
        raw_candidate_artifact_ref=raw_reference.artifact_id,
        generated_at=generated_at,
    )
    repository = R6Repository(artifact_store, metadata_store)
    chains: list[R6ChainReferences] = []
    partial_refs: list[str] = []
    governance_failures = 0
    persistence_failed = False

    for item in validation.accepted:
        proposition = item.proposition
        try:
            authority_registry = _build_pretest_registry(proposition, source_views)
            template = MVP_FAMILY_REGISTRY.get_requirement_template(proposition.family_id)
            template_binding = AuthorityBinding(
                authority_ref=template.template_id,
                authority_version=template.template_version,
                authority_fingerprint=template.template_fingerprint,
            )
            governed = govern_pretest(
                proposition,
                item.candidate,
                template_binding,
                (),
                authority_registry=authority_registry,
                finalized_at=finalized_at,
            )
        except GovernanceAuthenticationError as exc:
            governance_failures += 1
            diagnostics.append(
                R6ApplicationDiagnostic(
                    stage="governance",
                    code=exc.code,
                    message=str(exc),
                    candidate_fingerprint=item.candidate_fingerprint,
                    proposition_ref=proposition.proposition_id,
                    family_id=proposition.family_id,
                )
            )
            continue

        try:
            repository.persist_diagnostic_proposition(proposition)
            partial_refs.append(proposition.proposition_id)
            repository.persist_resolved_required_evidence_profile(governed.resolved_profile)
            partial_refs.append(governed.resolved_profile.profile_id)
            repository.persist_requirement_judgment_bundle(
                governed.requirement_judgment_bundle_ref,
                governed.requirement_judgment_bundle_fingerprint,
                governed.requirement_judgments,
            )
            partial_refs.append(governed.requirement_judgment_bundle_ref)
            repository.persist_pretest_diagnostic_evaluation(governed.evaluation)
            partial_refs.append(governed.evaluation.evaluation_id)
            repository.persist_generation_provenance(provenance)
            partial_refs.append(provenance.generation_provenance_id)
            hypothesis = _build_governed_hypothesis(proposition, governed, provenance)
            repository.persist_governed_hypothesis(hypothesis)
            partial_refs.append(hypothesis.governed_hypothesis_id)
            repository.load_governed_hypothesis(
                hypothesis.governed_hypothesis_id,
                authority_registry=authority_registry,
            )
            handoff = None
            if persist_handoff:
                requested_handoff = _build_handoff(proposition, governed, hypothesis, provenance)
                try:
                    repository.persist_r6_to_r7_handoff(requested_handoff)
                    partial_refs.append(requested_handoff.handoff_id)
                    repository.load_r6_to_r7_handoff(
                        requested_handoff.handoff_id,
                        authority_registry=authority_registry,
                    )
                    handoff = requested_handoff
                except R6ArtifactIntegrityError as exc:
                    persistence_failed = True
                    diagnostics.append(
                        R6ApplicationDiagnostic(
                            stage="persistence",
                            code=exc.code,
                            message=str(exc),
                            candidate_fingerprint=item.candidate_fingerprint,
                            proposition_ref=proposition.proposition_id,
                            family_id=proposition.family_id,
                        )
                    )
            chains.append(
                R6ChainReferences(
                    candidate_fingerprint=item.candidate_fingerprint,
                    duplicate_candidate_fingerprints=item.duplicate_candidate_fingerprints,
                    diagnostic_proposition_ref=proposition.proposition_id,
                    resolved_profile_ref=governed.resolved_profile.profile_id,
                    requirement_judgment_bundle_ref=governed.requirement_judgment_bundle_ref,
                    pretest_evaluation_ref=governed.evaluation.evaluation_id,
                    generation_provenance_ref=provenance.generation_provenance_id,
                    governed_hypothesis_ref=hypothesis.governed_hypothesis_id,
                    handoff_ref=handoff.handoff_id if handoff is not None else None,
                    test_eligibility=governed.evaluation.test_eligibility,
                )
            )
            if persistence_failed:
                break
        except R6ArtifactIntegrityError as exc:
            persistence_failed = True
            diagnostics.append(
                R6ApplicationDiagnostic(
                    stage="persistence",
                    code=exc.code,
                    message=str(exc),
                    candidate_fingerprint=item.candidate_fingerprint,
                    proposition_ref=proposition.proposition_id,
                    family_id=proposition.family_id,
                )
            )
            break

    has_failure = bool(validation.requested_family_omissions or governance_failures or persistence_failed)
    if chains and has_failure:
        status = R6CompletionStatus.PARTIAL_FAILURE
    elif chains:
        status = R6CompletionStatus.COMPLETE
    elif persistence_failed:
        status = R6CompletionStatus.PERSISTENCE_FAILURE
    elif governance_failures:
        status = R6CompletionStatus.GOVERNANCE_FAILURE
    else:
        status = R6CompletionStatus.GENERATION_FAILURE
    return R6RunOutcome(
        generation_request_ref=generation_request.generation_request_ref,
        context_ref=context.context_id,
        raw_candidate_artifact_ref=raw_reference.artifact_id,
        accepted_candidate_fingerprints=accepted_fingerprints,
        chains=tuple(chains),
        diagnostics=tuple(diagnostics),
        partial_persisted_refs=tuple(dict.fromkeys(partial_refs)),
        completion_status=status,
    )


def _authenticate_and_build_context(
    *,
    generation_request: R6GenerationRequest,
    analysis_request_ref: str,
    sufficiency_ref: str,
    supplied_plan: ExecutionPlan,
    revenue_change_validated_result_ref: str,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    r4_validated_result_artifact: ArtifactReference | None,
) -> tuple[CandidateGenerationContext, tuple[SourceAuthorityView, ...]]:
    generation_request = R6GenerationRequest.model_validate(generation_request.model_dump(mode="python"))
    if generation_request.analysis_request_ref != analysis_request_ref:
        raise GenerationBoundaryError("generation_request_mismatch", "generation request analysis binding mismatches service input")
    requested = set(generation_request.requested_family_ids)
    active = {item.family_id for item in MVP_FAMILY_REGISTRY.active_families}
    unknown_requested = requested - active
    if unknown_requested:
        raise GenerationBoundaryError("disallowed_family", f"requested family is not active: {', '.join(sorted(unknown_requested))}")

    request = metadata_store.get_analysis_request(analysis_request_ref, artifact_store)
    sufficiency = metadata_store.get_data_sufficiency_result(sufficiency_ref, artifact_store)
    if request is None or sufficiency is None:
        raise GenerationBoundaryError("upstream_authority_failure", "analysis request or sufficiency authority is missing")
    if sufficiency.request_id != request.request_id:
        raise GenerationBoundaryError("upstream_authority_failure", "sufficiency does not belong to analysis request")
    expected_plan = build_execution_plan(request, sufficiency)
    if supplied_plan != expected_plan:
        raise GenerationBoundaryError("plan_authority_mismatch", "supplied plan is not the deterministic governed plan")
    baseline = _population(supplied_plan, PopulationPeriodRole.BASELINE)
    comparison = _population(supplied_plan, PopulationPeriodRole.COMPARISON)
    if baseline.scope.scope_id != comparison.scope.scope_id or baseline.scope != comparison.scope:
        raise GenerationBoundaryError("scope_mismatch", "baseline and comparison populations do not share exact scope")
    if baseline.canonical_dataset_ref_id != comparison.canonical_dataset_ref_id:
        raise GenerationBoundaryError("population_mismatch", "populations do not share canonical dataset")
    canonical = metadata_store.get_canonical_dataset(baseline.canonical_dataset_ref_id)
    if canonical is None or canonical.canonical_schema_version != CANONICAL_SCHEMA_VERSION:
        raise GenerationBoundaryError("stale_source_authority", "canonical dataset authority is missing or stale")

    revenue_change = load_authenticated_scalar_validated_result(
        revenue_change_validated_result_ref,
        artifact_store,
        metadata_store,
    )
    metric = get_metric_registry().require("revenue_change")
    if (
        revenue_change.metric_ref != "revenue_change"
        or revenue_change.metric_definition_version != metric.definition_version
        or revenue_change.metric_state is not MetricState.VALID
        or revenue_change.plan_id != supplied_plan.plan_id
        or revenue_change.canonical_dataset_ref_id != canonical.canonical_dataset_id
        or revenue_change.canonical_dataset_fingerprint != canonical.content_fingerprint
        or revenue_change.population_ref != comparison.population_id
        or revenue_change.period_role != "baseline_and_comparison"
    ):
        raise GenerationBoundaryError("invented_metric", "Revenue Change authority is invalid or misbound")

    validated_r4: ValidatedR4DecompositionResult | None = None
    if r4_validated_result_artifact is not None:
        validated_r4 = load_validated_r4_result(
            r4_validated_result_artifact,
            artifact_store,
            metadata_store,
        )
        authority = validated_r4.authority
        if (
            authority.analysis_request_ref != request.request_id
            or authority.plan_ref != supplied_plan.plan_id
            or authority.canonical_dataset_ref != canonical.canonical_dataset_id
            or authority.scope_ref != baseline.scope.scope_id
            or authority.baseline_period_ref != baseline.period.period_id
            or authority.comparison_period_ref != comparison.period.period_id
            or authority.baseline_population_ref != baseline.population_id
            or authority.comparison_population_ref != comparison.population_id
        ):
            raise GenerationBoundaryError("r4_support_claim_forbidden", "R4 authority does not match generation context")

    activations = {item.family_id: item for item in generation_request.family_activations}
    external_activation = activations.get("external_market_association")
    if external_activation is not None and "external_market_association" not in requested:
        raise GenerationBoundaryError("generation_request_mismatch", "external activation requires explicit requested family")

    metric_ref = f"metric:revenue_change@{METRIC_DEFINITION_VERSION}"
    source_views = _source_views(
        metric_ref=metric_ref,
        validated_result_ref=revenue_change.validated_result_id,
        canonical_ref=canonical.canonical_dataset_id,
        canonical_fingerprint=canonical.content_fingerprint,
        scope_ref=baseline.scope.scope_id,
        baseline=baseline,
        comparison=comparison,
        activations=tuple(generation_request.family_activations),
        validated_r4=validated_r4,
    )
    permitted_ids = {"product_composition_association", "discounting_association"}
    if external_activation is not None:
        permitted_ids.add("external_market_association")
    family_views = tuple(
        CandidateFamilyView(
            family_id=family.family_id,
            family_version=family.family_version,
            family_fingerprint=family.family_fingerprint,
            allowed_slots=tuple(sorted(family.allowed_proposition_slots)),
            required_slots=tuple(sorted(family.required_proposition_slots)),
            display_template_ids=tuple(sorted(family.display_template_ids)),
        )
        for family in sorted(MVP_FAMILY_REGISTRY.active_families, key=lambda item: item.family_id)
        if family.family_id in permitted_ids
    )
    slot_bindings = _slot_bindings(
        metric_ref=metric_ref,
        canonical_ref=canonical.canonical_dataset_id,
        scope_ref=baseline.scope.scope_id,
        baseline=baseline,
        comparison=comparison,
        external_activation=external_activation,
        validated_r4=validated_r4,
    )
    context = build_candidate_generation_context(
        generation_request_ref=generation_request.generation_request_ref,
        analysis_request_ref=request.request_id,
        outcome_metric_ref=metric_ref,
        outcome_validated_result_ref=revenue_change.validated_result_id,
        scope_ref=baseline.scope.scope_id,
        baseline_period_ref=baseline.period.period_id,
        comparison_period_ref=comparison.period.period_id,
        baseline_population_ref=baseline.population_id,
        comparison_population_ref=comparison.population_id,
        permitted_family_views=family_views,
        allowed_slot_bindings=slot_bindings,
        source_authority_views=source_views,
        requested_family_ids=tuple(sorted(requested)),
        family_activations=tuple(sorted(generation_request.family_activations, key=lambda item: item.family_id)),
        source_mechanical_result_ref=(validated_r4.validated_result_id if validated_r4 is not None else None),
    )
    return context, source_views


def _population(plan: ExecutionPlan, role: PopulationPeriodRole) -> PopulationDefinition:
    matches = [
        item for item in plan.population_definitions
        if item.period_role is role and item.grouping is GroupingDimension.NONE
    ]
    if len(matches) != 1:
        raise GenerationBoundaryError("population_mismatch", f"exact {role.value} population is missing or ambiguous")
    population = matches[0]
    fingerprint = population_fingerprint(population)
    if population.population_fingerprint != fingerprint or population.population_id != population_id_for_fingerprint(fingerprint):
        raise GenerationBoundaryError("population_mismatch", f"{role.value} population identity is invalid")
    return population


def _source_views(
    *,
    metric_ref: str,
    validated_result_ref: str,
    canonical_ref: str,
    canonical_fingerprint: str,
    scope_ref: str,
    baseline: PopulationDefinition,
    comparison: PopulationDefinition,
    activations: tuple[FamilyActivation, ...],
    validated_r4: ValidatedR4DecompositionResult | None,
) -> tuple[SourceAuthorityView, ...]:
    alignment = {
        "scope_ref": scope_ref,
        "baseline_period_ref": baseline.period.period_id,
        "comparison_period_ref": comparison.period.period_id,
        "baseline_population_ref": baseline.population_id,
        "comparison_population_ref": comparison.population_id,
    }
    views = [
        SourceAuthorityView(
            authority_ref=metric_ref,
            authority_version=METRIC_DEFINITION_VERSION,
            authority_fingerprint=canonical_json_fingerprint(
                {"metric_ref": metric_ref, "validated_result_ref": validated_result_ref}
            ),
            authority_class=SourceAuthorityClass.METRIC,
            dependency_classification=DependencyClassification.INTERNAL,
            intended_uses=("diagnostic_candidate_outcome",),
            **alignment,
        ),
        SourceAuthorityView(
            authority_ref=canonical_ref,
            authority_version=CANONICAL_SCHEMA_VERSION,
            authority_fingerprint=canonical_fingerprint,
            authority_class=SourceAuthorityClass.SOURCE_REFERENCE,
            dependency_classification=DependencyClassification.INTERNAL,
            intended_uses=("diagnostic_candidate_source",),
            **alignment,
        ),
    ]
    variable_refs = {
        "field:product_id": CANONICAL_FIELD_DEFINITIONS["product_id"].model_dump(mode="json"),
        "field:line_revenue": CANONICAL_FIELD_DEFINITIONS["line_revenue"].model_dump(mode="json"),
        "requirement:original_or_list_price": {"requirement": "original_or_list_price", "available": False},
        "requirement:governed_discount_semantics": {"requirement": "governed_discount_semantics", "available": False},
    }
    for reference, material in variable_refs.items():
        views.append(
            SourceAuthorityView(
                authority_ref=reference,
                authority_version="1.0.0",
                authority_fingerprint=canonical_json_fingerprint(material),
                authority_class=SourceAuthorityClass.VARIABLE,
                dependency_classification=DependencyClassification.INTERNAL,
                intended_uses=("diagnostic_candidate_variable",),
                **alignment,
            )
        )
    for activation in activations:
        activation_fingerprint = canonical_json_fingerprint(activation.model_dump(mode="json"))
        views.append(
            SourceAuthorityView(
                authority_ref=activation.activation_ref,
                authority_version="1.0.0",
                authority_fingerprint=activation_fingerprint,
                authority_class=SourceAuthorityClass.ACTIVATION,
                dependency_classification=DependencyClassification.EXTERNAL,
                intended_uses=("family_activation_only", "diagnostic"),
                **alignment,
            )
        )
        if activation.external_factor_ref is not None:
            views.append(
                SourceAuthorityView(
                    authority_ref=activation.external_factor_ref,
                    authority_version="1.0.0",
                    authority_fingerprint=canonical_json_fingerprint(
                        {"activation_ref": activation.activation_ref, "factor_ref": activation.external_factor_ref}
                    ),
                    authority_class=SourceAuthorityClass.VARIABLE,
                    dependency_classification=DependencyClassification.EXTERNAL,
                    intended_uses=("diagnostic_candidate_variable",),
                    **alignment,
                )
            )
        if activation.external_dependency_ref is not None:
            views.append(
                SourceAuthorityView(
                    authority_ref=activation.external_dependency_ref,
                    authority_version="1.0.0",
                    authority_fingerprint=canonical_json_fingerprint(
                        {"activation_ref": activation.activation_ref, "dependency_ref": activation.external_dependency_ref}
                    ),
                    authority_class=SourceAuthorityClass.SOURCE_REFERENCE,
                    dependency_classification=DependencyClassification.EXTERNAL,
                    intended_uses=("diagnostic_candidate_source", "non_evidentiary_dependency"),
                    **alignment,
                )
            )
    if validated_r4 is not None:
        views.append(
            SourceAuthorityView(
                authority_ref=validated_r4.validated_result_id,
                authority_version=validated_r4.authority.method_version,
                authority_fingerprint=validated_r4.validation_fingerprint,
                authority_class=SourceAuthorityClass.MECHANICAL_RESULT,
                dependency_classification=DependencyClassification.INTERNAL,
                intended_uses=("mechanical_reference_only",),
                **alignment,
            )
        )
    return tuple(sorted(views, key=lambda item: (item.authority_class.value, item.authority_ref)))


def _slot_bindings(
    *,
    metric_ref: str,
    canonical_ref: str,
    scope_ref: str,
    baseline: PopulationDefinition,
    comparison: PopulationDefinition,
    external_activation: FamilyActivation | None,
    validated_r4: ValidatedR4DecompositionResult | None,
) -> tuple[AllowedSlotBinding, ...]:
    common = {
        "outcome_ref": (metric_ref,),
        "scope_ref": (scope_ref,),
        "baseline_period_ref": (baseline.period.period_id,),
        "comparison_period_ref": (comparison.period.period_id,),
        "baseline_population_ref": (baseline.population_id,),
        "comparison_population_ref": (comparison.population_id,),
    }
    bindings: list[AllowedSlotBinding] = []
    for family_id in ("product_composition_association", "discounting_association", "external_market_association"):
        if family_id == "external_market_association" and external_activation is None:
            continue
        bindings.extend(
            AllowedSlotBinding(family_id=family_id, slot=slot, allowed_refs=refs)
            for slot, refs in common.items()
        )
    bindings.extend(
        (
            AllowedSlotBinding(family_id="product_composition_association", slot="product_identity_ref", allowed_refs=("field:product_id",)),
            AllowedSlotBinding(family_id="product_composition_association", slot="monetary_observation_ref", allowed_refs=("field:line_revenue",)),
            AllowedSlotBinding(family_id="product_composition_association", slot="source_observation_refs", allowed_refs=(canonical_ref,), semantically_unordered=True),
            AllowedSlotBinding(family_id="discounting_association", slot="original_or_list_price_ref", allowed_refs=("requirement:original_or_list_price",)),
            AllowedSlotBinding(family_id="discounting_association", slot="discount_semantics_ref", allowed_refs=("requirement:governed_discount_semantics",)),
            AllowedSlotBinding(family_id="discounting_association", slot="monetary_observation_ref", allowed_refs=("field:line_revenue",)),
            AllowedSlotBinding(family_id="discounting_association", slot="source_observation_refs", allowed_refs=(canonical_ref,), semantically_unordered=True),
        )
    )
    if validated_r4 is not None:
        bindings.append(
            AllowedSlotBinding(
                family_id="product_composition_association",
                slot="optional_r4_result_ref",
                allowed_refs=(validated_r4.validated_result_id,),
            )
        )
    if external_activation is not None:
        assert external_activation.external_factor_ref is not None
        assert external_activation.external_dependency_ref is not None
        bindings.extend(
            (
                AllowedSlotBinding(family_id="external_market_association", slot="external_factor_ref", allowed_refs=(external_activation.external_factor_ref,)),
                AllowedSlotBinding(family_id="external_market_association", slot="external_evidence_dependency_ref", allowed_refs=(external_activation.external_dependency_ref,)),
                AllowedSlotBinding(family_id="external_market_association", slot="source_observation_refs", allowed_refs=(external_activation.external_dependency_ref,), semantically_unordered=True),
                AllowedSlotBinding(family_id="external_market_association", slot="explicit_activation_ref", allowed_refs=(external_activation.activation_ref,)),
            )
        )
    return tuple(sorted(bindings, key=lambda item: (item.family_id, item.slot)))


def _build_pretest_registry(proposition, source_views: tuple[SourceAuthorityView, ...]) -> PreTestAuthorityRegistry:
    views = {item.authority_ref: item for item in source_views}
    records: list[RegisteredAuthority] = []
    for binding in proposition.authority_bindings:
        records.append(
            RegisteredAuthority(
                authority_class=AuthorityClass.INTENDED_USE,
                binding=binding,
                subject_refs=(proposition.proposition_id,),
                intended_uses=("diagnostic",),
                dependency_classification=(
                    views[binding.authority_ref].dependency_classification
                    if binding.authority_ref in views
                    else None
                ),
            )
        )
    context_refs = {
        AuthorityClass.SCOPE: (proposition.scope_ref,),
        AuthorityClass.PERIOD: (proposition.baseline_period_ref, proposition.comparison_period_ref),
        AuthorityClass.POPULATION: (proposition.baseline_population_ref, proposition.comparison_population_ref),
    }
    for authority_class, references in context_refs.items():
        for reference in references:
            records.append(
                RegisteredAuthority(
                    authority_class=authority_class,
                    binding=_context_binding(authority_class.value, reference),
                    subject_refs=(proposition.proposition_id,),
                )
            )
    for reference in proposition.variable_refs:
        view = views[reference]
        records.append(
            RegisteredAuthority(
                authority_class=AuthorityClass.VARIABLE,
                binding=_view_binding(view),
                subject_refs=(proposition.proposition_id,),
                intended_uses=view.intended_uses,
                dependency_classification=view.dependency_classification,
            )
        )
    for reference in (*proposition.source_observation_refs, *proposition.source_mechanical_result_refs):
        view = views[reference]
        records.append(
            RegisteredAuthority(
                authority_class=AuthorityClass.SOURCE_REFERENCE,
                binding=_view_binding(view),
                subject_refs=(proposition.proposition_id,),
                intended_uses=view.intended_uses,
                dependency_classification=view.dependency_classification,
            )
        )
    data: dict[str, Any] = {
        "registry_id": "commerce_lens_r6_pretest_authorities",
        "registry_version": "1.0.0",
        "authorities": tuple(records),
    }
    data["registry_fingerprint"] = pretest_authority_registry_fingerprint(data)
    return PreTestAuthorityRegistry(**data)


def _context_binding(kind: str, reference: str) -> AuthorityBinding:
    return AuthorityBinding(
        authority_ref=reference,
        authority_version="1.0.0",
        authority_fingerprint=canonical_json_fingerprint({"authority_class": kind, "authority_ref": reference}),
    )


def _view_binding(view: SourceAuthorityView) -> AuthorityBinding:
    return AuthorityBinding(
        authority_ref=view.authority_ref,
        authority_version=view.authority_version,
        authority_fingerprint=view.authority_fingerprint,
    )


def _persist_raw_candidate_batch(
    batch,
    *,
    generation_request_ref: str,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ArtifactReference:
    payload = batch.model_dump(mode="json")
    fingerprint = canonical_json_fingerprint(payload)
    reference = artifact_store.write_json_artifact(
        Path("runs") / generation_request_ref / "r6" / "raw_candidates" / f"{fingerprint}.json",
        payload,
    )
    return metadata_store.insert_artifact_reference(reference)


def _build_generation_provenance(
    descriptor: CandidateProducerDescriptor,
    *,
    raw_candidate_artifact_ref: str,
    generated_at: datetime,
) -> GenerationProvenance:
    data: dict[str, Any] = {
        "generation_provenance_id": "pending",
        "generator_id": descriptor.producer_id,
        "generator_version": descriptor.producer_version,
        "prompt_template_id": descriptor.template_id,
        "prompt_template_version": descriptor.template_version,
        "prompt_template_fingerprint": descriptor.template_fingerprint,
        "model_id": descriptor.model_id,
        "generation_parameters": descriptor.generation_parameters,
        "raw_candidate_artifact_ref": raw_candidate_artifact_ref,
        "generated_at": generated_at,
    }
    data["provenance_fingerprint"] = generation_provenance_semantic_fingerprint(data)
    data["generation_provenance_id"] = stable_content_id("genprov", data["provenance_fingerprint"])
    return GenerationProvenance(**data)


def _build_governed_hypothesis(proposition, governed, provenance) -> GovernedHypothesis:
    data = {
        "governed_hypothesis_id": "pending",
        "governed_hypothesis_schema_version": "1.0.0",
        "diagnostic_proposition_ref": proposition.proposition_id,
        "diagnostic_proposition_fingerprint": proposition.semantic_fingerprint,
        "pretest_evaluation_ref": governed.evaluation.evaluation_id,
        "pretest_evaluation_fingerprint": governed.evaluation.evaluation_fingerprint,
        "resolved_profile_ref": governed.resolved_profile.profile_id,
        "resolved_profile_fingerprint": governed.resolved_profile.profile_fingerprint,
        "generation_provenance_ref": provenance.generation_provenance_id,
        "generation_provenance_fingerprint": provenance.provenance_fingerprint,
    }
    data["governed_hypothesis_fingerprint"] = governed_hypothesis_semantic_fingerprint(data)
    data["governed_hypothesis_id"] = stable_content_id("govhyp", data["governed_hypothesis_fingerprint"])
    return GovernedHypothesis(**data)


def _build_handoff(proposition, governed, hypothesis, provenance) -> R6ToR7Handoff:
    judgments = governed.requirement_judgments
    blocking = {
        RequirementOutcome.FAILED,
        RequirementOutcome.MISSING,
        RequirementOutcome.UNRESOLVED,
        RequirementOutcome.PRESENT_BUT_INADMISSIBLE,
    }
    missing_internal = tuple(sorted(
        item.requirement_ref for item in judgments
        if item.dependency_classification is DependencyClassification.INTERNAL and item.outcome in blocking
    ))
    unmet_external = tuple(sorted(
        item.requirement_ref for item in judgments
        if item.dependency_classification is DependencyClassification.EXTERNAL
        and item.outcome in {*blocking, RequirementOutcome.EXTERNAL_UNMET}
    ))
    data = {
        "handoff_id": "pending",
        "handoff_schema_version": "1.0.0",
        "diagnostic_proposition_ref": proposition.proposition_id,
        "diagnostic_proposition_fingerprint": proposition.semantic_fingerprint,
        "pretest_evaluation_ref": governed.evaluation.evaluation_id,
        "pretest_evaluation_fingerprint": governed.evaluation.evaluation_fingerprint,
        "family_id": proposition.family_id,
        "family_version": proposition.family_version,
        "family_fingerprint": proposition.family_fingerprint,
        "resolved_profile_ref": governed.resolved_profile.profile_id,
        "resolved_profile_version": governed.resolved_profile.profile_version,
        "resolved_profile_fingerprint": governed.resolved_profile.profile_fingerprint,
        "scope_ref": proposition.scope_ref,
        "baseline_period_ref": proposition.baseline_period_ref,
        "comparison_period_ref": proposition.comparison_period_ref,
        "population_refs": tuple(sorted((proposition.baseline_population_ref, proposition.comparison_population_ref))),
        "metric_refs": proposition.metric_refs,
        "variable_refs": proposition.variable_refs,
        "source_observation_refs": proposition.source_observation_refs,
        "source_mechanical_result_refs": proposition.source_mechanical_result_refs,
        "requirement_judgment_refs": tuple(sorted(item.judgment_id for item in judgments)),
        "evidence_readiness": governed.evaluation.evidence_readiness,
        "missing_internal_requirement_refs": missing_internal,
        "unmet_external_requirement_refs": unmet_external,
        "method_ref": None,
        "method_version": None,
        "support_criterion_ref": None,
        "support_criterion_version": None,
        "validation_profile_ref": None,
        "validation_profile_version": None,
        "test_eligibility": governed.evaluation.test_eligibility,
        "first_controlling_blocker": governed.evaluation.first_controlling_blocker,
        "governed_hypothesis_ref": hypothesis.governed_hypothesis_id,
        "governed_hypothesis_fingerprint": hypothesis.governed_hypothesis_fingerprint,
        "generation_provenance_ref": provenance.generation_provenance_id,
    }
    data["handoff_fingerprint"] = r6_to_r7_handoff_semantic_fingerprint(data)
    data["handoff_id"] = stable_content_id("r6handoff", data["handoff_fingerprint"])
    return R6ToR7Handoff(**data)


def _application_diagnostic(item: CandidateDiagnostic) -> R6ApplicationDiagnostic:
    return R6ApplicationDiagnostic(
        stage="generation",
        code=item.code,
        message=item.message,
        candidate_fingerprint=item.candidate_fingerprint,
        family_id=item.family_id,
        proposition_ref=item.duplicate_of_proposition_ref,
    )


def _failure_outcome(
    generation_request_ref: str,
    status: R6CompletionStatus,
    stage: str,
    code: str,
    message: str,
    *,
    context_ref: str | None = None,
) -> R6RunOutcome:
    return R6RunOutcome(
        generation_request_ref=generation_request_ref,
        context_ref=context_ref,
        completion_status=status,
        diagnostics=(R6ApplicationDiagnostic(stage=stage, code=code, message=message),),
    )


__all__ = [
    "R6ApplicationDiagnostic",
    "R6ApplicationError",
    "R6ChainReferences",
    "R6CompletionStatus",
    "R6RunOutcome",
    "run_r6",
]
