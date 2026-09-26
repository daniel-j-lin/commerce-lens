"""Production public orchestration for the single approved R7 diagnostic path.

This module constructs and binds existing R6/R7 contracts. Analytical execution,
thresholds, validation, evidence admission, and lineage authentication remain in
their owning services.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from commerce_lens.application.r6_service import (
    R6RunOutcome,
    build_pretest_authority_registry,
    run_r6,
)
from commerce_lens.application.r7_service import run_r7_diagnostic
from commerce_lens.contracts.common import utc_now
from commerce_lens.contracts.diagnostic import TestEligibility
from commerce_lens.contracts.hypotheses import (
    CandidateProposal,
    CandidateProposalBatch,
    CandidateSlot,
    GenerationParameters,
)
from commerce_lens.contracts.required_evidence import (
    DependencyClassification,
    EvidenceRole,
)
from commerce_lens.contracts.results import AnalysisResult
from commerce_lens.contracts.r7 import (
    DiagnosticEvidenceInputBinding,
    DiagnosticEvidenceInputSet,
    DiagnosticTestRequest,
    diagnostic_test_request_fingerprint,
    evidence_input_set_fingerprint,
)
from commerce_lens.diagnostic.generator import (
    CandidateGenerationContext,
    CandidateProducerDescriptor,
    SourceAuthorityClass,
    build_generation_request,
    validate_and_construct_propositions,
    validate_candidate_batch,
)
from commerce_lens.diagnostic.governance import AuthorityClass
from commerce_lens.diagnostic.r6_r7_authority import resolve_production_pretest_authority
from commerce_lens.diagnostic.r7_evidence_authentication import (
    TrustedR7EvidenceAuthority,
    TrustedR7EvidenceRole,
    requirement_judgment_fingerprint,
)
from commerce_lens.diagnostic.r7_method_registry import (
    IMPLEMENTATION_BINDING,
    METHOD_DEFINITION,
    R7_METHOD_REGISTRY,
    SUPPORT_CRITERION,
    VALIDATION_PROFILE,
    authority_ref,
)
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, stable_content_id
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.persistence.r6_repository import R6Repository
from commerce_lens.persistence.r7_repository import CompleteR7Lineage, R7Repository


PUBLIC_R7_FAMILY_ID = "product_composition_association"
PUBLIC_R7_PRODUCER_ID = "producer:public-approved-product-composition"
_PUBLIC_TEMPLATE_MATERIAL = {
    "producer_id": PUBLIC_R7_PRODUCER_ID,
    "producer_version": "1.0.0",
    "family_id": PUBLIC_R7_FAMILY_ID,
    "method_id": METHOD_DEFINITION.method_id,
    "method_version": METHOD_DEFINITION.method_version,
}


@dataclass(frozen=True)
class PublicR7ServiceOutcome:
    r6_outcome: R6RunOutcome | None
    authenticated_lineage: CompleteR7Lineage | None
    blocker: str | None
    r7_executed: bool = False


class _ApprovedProductCompositionProducer:
    """Fixed public adapter for the sole explicitly requested approved family."""

    context: CandidateGenerationContext | None = None
    batch: CandidateProposalBatch | None = None

    def produce_candidates(self, context: CandidateGenerationContext) -> CandidateProposalBatch:
        self.context = context
        family = next(
            item for item in context.permitted_family_views
            if item.family_id == PUBLIC_R7_FAMILY_ID
        )
        source = next(
            item.authority_ref for item in context.source_authority_views
            if item.authority_class is SourceAuthorityClass.SOURCE_REFERENCE
            and item.dependency_classification is DependencyClassification.INTERNAL
        )
        values: dict[str, Any] = {
            "outcome_ref": context.outcome_metric_ref,
            "scope_ref": context.scope_ref,
            "baseline_period_ref": context.baseline_period_ref,
            "comparison_period_ref": context.comparison_period_ref,
            "baseline_population_ref": context.baseline_population_ref,
            "comparison_population_ref": context.comparison_population_ref,
            "product_identity_ref": "field:product_id",
            "monetary_observation_ref": "field:line_revenue",
            "source_observation_refs": (source,),
        }
        if context.source_mechanical_result_ref is not None:
            values["optional_r4_result_ref"] = context.source_mechanical_result_ref
        candidate = CandidateProposal(
            family_id=family.family_id,
            family_version=family.family_version,
            structured_slot_values=tuple(
                CandidateSlot(slot=slot, value=value) for slot, value in values.items()
            ),
            source_reference_proposals=(source,),
            display_template_id="r6-product-composition-untested-v1",
            non_authoritative_wording=(
                "Evaluate the approved bounded non-causal product-composition association."
            ),
        )
        self.batch = CandidateProposalBatch(
            batch_schema_version="1.0.0",
            producer_ref=PUBLIC_R7_PRODUCER_ID,
            generation_request_ref=context.generation_request_ref,
            candidates=(candidate,),
        )
        return self.batch


def _producer_descriptor() -> CandidateProducerDescriptor:
    return CandidateProducerDescriptor(
        producer_id=PUBLIC_R7_PRODUCER_ID,
        producer_version="1.0.0",
        template_id="template:public-approved-product-composition",
        template_version="1.0.0",
        template_fingerprint=canonical_json_fingerprint(_PUBLIC_TEMPLATE_MATERIAL),
        generation_parameters=GenerationParameters(temperature=0.0, max_output_tokens=1),
    )


def run_public_r7_flow(
    *,
    analysis_result: AnalysisResult,
    revenue_change_validated_result_ref: str,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    now: datetime | None = None,
) -> PublicR7ServiceOutcome:
    """Run the approved production R6→R7 path and return authenticated lineage only."""

    if analysis_result.execution_plan is None or analysis_result.data_sufficiency_ref is None:
        return PublicR7ServiceOutcome(
            None,
            None,
            "governed execution plan or sufficiency authority is unavailable",
        )
    timestamp = now or utc_now()
    generation_request = build_generation_request(
        analysis_request_ref=analysis_result.request_id,
        requested_family_ids=(PUBLIC_R7_FAMILY_ID,),
    )
    producer = _ApprovedProductCompositionProducer()
    r6_outcome = run_r6(
        generation_request=generation_request,
        producer=producer,
        producer_descriptor=_producer_descriptor(),
        analysis_request_ref=analysis_result.request_id,
        sufficiency_ref=analysis_result.data_sufficiency_ref,
        plan=analysis_result.execution_plan,
        revenue_change_validated_result_ref=revenue_change_validated_result_ref,
        artifact_store=artifact_store,
        metadata_store=metadata_store,
        generated_at=timestamp,
        finalized_at=timestamp,
        persist_handoff=True,
        r7_method_registry=R7_METHOD_REGISTRY,
    )
    eligible = tuple(
        chain for chain in r6_outcome.chains
        if chain.test_eligibility is TestEligibility.ELIGIBLE_NOT_EXECUTED
        and chain.handoff_ref is not None
    )
    if len(eligible) != 1 or producer.context is None:
        blocker = _r6_blocker(r6_outcome)
        return PublicR7ServiceOutcome(r6_outcome, None, blocker)

    r6_repository = R6Repository(artifact_store, metadata_store)
    r7_repository = R7Repository(artifact_store, metadata_store)
    chain = eligible[0]
    if producer.batch is None:
        return PublicR7ServiceOutcome(
            r6_outcome, None, "approved R6 candidate material is unavailable"
        )
    authenticated_batch = validate_candidate_batch(
        producer.batch,
        descriptor=_producer_descriptor(),
        context=producer.context,
    )
    constructed = validate_and_construct_propositions(authenticated_batch, producer.context)
    if len(constructed.accepted) != 1:
        return PublicR7ServiceOutcome(r6_outcome, None, "approved R6 proposition is unavailable")
    expected_proposition = constructed.accepted[0].proposition
    if expected_proposition.proposition_id != chain.diagnostic_proposition_ref:
        return PublicR7ServiceOutcome(r6_outcome, None, "persisted R6 proposition identity mismatch")
    production_authority = resolve_production_pretest_authority(
        expected_proposition,
        producer.context.source_authority_views,
        method_registry=R7_METHOD_REGISTRY,
    )
    if production_authority is None:
        return PublicR7ServiceOutcome(r6_outcome, None, "approved R7 execution authority is unavailable")
    authority_registry = build_pretest_authority_registry(
        expected_proposition,
        producer.context.source_authority_views,
        production_authority=production_authority,
    )
    proposition = r6_repository.load_diagnostic_proposition(
        chain.diagnostic_proposition_ref,
        authority_registry=authority_registry,
    )
    handoff = r6_repository.load_r6_to_r7_handoff(
        chain.handoff_ref,
        authority_registry=authority_registry,
    )
    evidence_inputs, trusted_evidence = _build_evidence_inputs(
        handoff=handoff,
        proposition=proposition,
        production_authority=production_authority,
        r6_repository=r6_repository,
        authority_registry=authority_registry,
    )
    baseline, comparison = _period_populations(analysis_result)
    canonical = metadata_store.get_canonical_dataset(baseline.canonical_dataset_ref_id)
    if canonical is None:
        return PublicR7ServiceOutcome(r6_outcome, None, "canonical dataset authority is unavailable")
    request = _build_test_request(
        handoff=handoff,
        evidence_inputs=evidence_inputs,
        canonical=canonical,
        baseline=baseline,
        comparison=comparison,
        r6_repository=r6_repository,
        authority_registry=authority_registry,
        created_at=timestamp,
    )
    service_outcome = run_r7_diagnostic(
        request=request,
        evidence_inputs=evidence_inputs,
        canonical_dataset=canonical,
        baseline_population=baseline,
        comparison_population=comparison,
        r6_repository=r6_repository,
        r7_repository=r7_repository,
        authority_registry=authority_registry,
        trusted_evidence_authority=trusted_evidence,
    )
    lineage = r7_repository.load_complete_posttest_evaluation(
        service_outcome.evaluation.evaluation_event_id,
        r6_repository=r6_repository,
        authority_registry=authority_registry,
        trusted_evidence_authority=trusted_evidence,
    )
    return PublicR7ServiceOutcome(r6_outcome, lineage, None, r7_executed=True)


def _build_evidence_inputs(
    *, handoff, proposition, production_authority, r6_repository, authority_registry
):
    profile = r6_repository.load_resolved_required_evidence_profile(
        handoff.resolved_profile_ref, authority_registry=authority_registry
    )
    pretest = r6_repository.load_pretest_diagnostic_evaluation(
        handoff.pretest_evaluation_ref, authority_registry=authority_registry
    )
    judgments = r6_repository.load_requirement_judgment_bundle(
        pretest.requirement_judgment_bundle_ref, profile=profile
    )
    judgment = next(item for item in judgments if item.requirement_ref == "governed_product_id")
    assessment = next(
        item for item in production_authority.evidence_assessments
        if item.requirement_ref == judgment.requirement_ref
    )
    evidence_ref = assessment.evidence_refs[0]
    evidence_authority = authority_registry.require_reference(
        AuthorityClass.EVIDENCE, evidence_ref
    )
    binding = DiagnosticEvidenceInputBinding(
        requirement_judgment_ref=judgment.judgment_id,
        requirement_judgment_fingerprint=requirement_judgment_fingerprint(judgment),
        evidence_ref=evidence_ref,
        evidence_fingerprint=evidence_authority.binding.authority_fingerprint,
        evidence_assessment_ref=assessment.assessment_id,
        evidence_assessment_fingerprint=assessment.assessment_fingerprint,
        diagnostic_admission_authority=assessment.diagnostic_admission_authority,
        admission_state="DIAGNOSTIC_ADMITTED",
        fitness_state="PASSED",
        source_class="GOVERNED_INTERNAL",
        evidence_role=EvidenceRole.EXPLANATORY_VARIABLE,
        scope_ref=assessment.scope_ref,
        period_refs=(assessment.baseline_period_ref, assessment.comparison_period_ref),
        population_refs=(assessment.baseline_population_ref, assessment.comparison_population_ref),
        metric_refs=assessment.metric_refs,
        variable_refs=assessment.variable_refs,
    )
    data = {
        "evidence_input_set_id": "pending",
        "evidence_input_set_fingerprint": "0" * 64,
        "diagnostic_proposition_ref": proposition.proposition_id,
        "diagnostic_proposition_fingerprint": proposition.semantic_fingerprint,
        "bindings": (binding,),
    }
    fingerprint = evidence_input_set_fingerprint(data)
    data.update(
        evidence_input_set_fingerprint=fingerprint,
        evidence_input_set_id=stable_content_id("r7evid", fingerprint),
    )
    evidence_inputs = DiagnosticEvidenceInputSet(**data)
    trusted = TrustedR7EvidenceAuthority(
        authority_label="production R6 pre-test evidence authority",
        assessments=production_authority.evidence_assessments,
        roles=(
            TrustedR7EvidenceRole(
                requirement_ref=judgment.requirement_ref,
                evidence_role=EvidenceRole.EXPLANATORY_VARIABLE,
                authority_binding=assessment.authority_bindings[0],
            ),
        ),
    )
    return evidence_inputs, trusted


def _period_populations(analysis_result: AnalysisResult):
    from commerce_lens.contracts.populations import PopulationPeriodRole

    populations = analysis_result.execution_plan.population_definitions
    baseline = next(item for item in populations if item.period_role is PopulationPeriodRole.BASELINE)
    comparison = next(item for item in populations if item.period_role is PopulationPeriodRole.COMPARISON)
    return baseline, comparison


def _build_test_request(*, handoff, evidence_inputs, canonical, baseline, comparison,
                        r6_repository, authority_registry, created_at):
    pretest = r6_repository.load_pretest_diagnostic_evaluation(
        handoff.pretest_evaluation_ref, authority_registry=authority_registry
    )
    data = {
        "test_request_id": "pending",
        "request_fingerprint": "0" * 64,
        "handoff_ref": handoff.handoff_id,
        "handoff_fingerprint": handoff.handoff_fingerprint,
        "governed_hypothesis_ref": handoff.governed_hypothesis_ref,
        "governed_hypothesis_fingerprint": handoff.governed_hypothesis_fingerprint,
        "diagnostic_proposition_ref": handoff.diagnostic_proposition_ref,
        "diagnostic_proposition_fingerprint": handoff.diagnostic_proposition_fingerprint,
        "pretest_evaluation_ref": handoff.pretest_evaluation_ref,
        "pretest_evaluation_fingerprint": handoff.pretest_evaluation_fingerprint,
        "resolved_profile_ref": handoff.resolved_profile_ref,
        "resolved_profile_fingerprint": handoff.resolved_profile_fingerprint,
        "requirement_judgment_bundle_ref": pretest.requirement_judgment_bundle_ref,
        "requirement_judgment_bundle_fingerprint": pretest.requirement_judgment_bundle_fingerprint,
        "method": authority_ref(METHOD_DEFINITION),
        "support_criterion": authority_ref(SUPPORT_CRITERION),
        "validation_profile": authority_ref(VALIDATION_PROFILE),
        "implementation": authority_ref(IMPLEMENTATION_BINDING),
        "evidence_input_set_ref": evidence_inputs.evidence_input_set_id,
        "evidence_input_set_fingerprint": evidence_inputs.evidence_input_set_fingerprint,
        "canonical_dataset_ref": canonical.canonical_dataset_id,
        "canonical_dataset_fingerprint": canonical.content_fingerprint,
        "scope_ref": handoff.scope_ref,
        "baseline_period_ref": baseline.period.period_id,
        "comparison_period_ref": comparison.period.period_id,
        "baseline_start": baseline.period.start_date,
        "baseline_end": baseline.period.end_date,
        "comparison_start": comparison.period.start_date,
        "comparison_end": comparison.period.end_date,
        "baseline_population_ref": baseline.population_id,
        "baseline_population_fingerprint": baseline.population_fingerprint,
        "comparison_population_ref": comparison.population_id,
        "comparison_population_fingerprint": comparison.population_fingerprint,
        "metric_refs": handoff.metric_refs,
        "variable_refs": handoff.variable_refs,
        "normalized_parameters": METHOD_DEFINITION.fixed_parameters,
        "created_at": created_at,
    }
    fingerprint = diagnostic_test_request_fingerprint(data)
    data.update(
        request_fingerprint=fingerprint,
        test_request_id=stable_content_id("r7req", fingerprint),
    )
    return DiagnosticTestRequest(**data)


def _r6_blocker(outcome: R6RunOutcome) -> str:
    if outcome.chains:
        repository_blockers = tuple(
            item for item in outcome.diagnostics if item.stage in {"governance", "persistence"}
        )
        if repository_blockers:
            return repository_blockers[0].message
        return "R6 did not return an eligible product-composition handoff"
    if outcome.diagnostics:
        return outcome.diagnostics[0].message
    return "R6 did not return an eligible product-composition handoff"


__all__ = ["PublicR7ServiceOutcome", "run_public_r7_flow"]
