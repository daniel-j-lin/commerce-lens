from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from commerce_lens.contracts.diagnostic import (
    AlternativeExplanationState,
    AnalyticalOutcome,
    AuthorityBinding,
    DiagnosticProposition,
    EvidenceReadiness,
    PreTestDiagnosticEvaluation,
    RelationshipDirection,
    RelationshipType,
    StructuredRelationship,
    TestEligibility as EligibilityState,
    diagnostic_proposition_semantic_fingerprint,
    pretest_evaluation_semantic_fingerprint,
)
from commerce_lens.contracts.hypotheses import (
    CandidateProposal,
    CandidateProposalBatch,
    CandidateSlot,
    GenerationParameters,
    GenerationProvenance,
    GovernedHypothesis,
    R6ToR7Handoff,
    generation_provenance_semantic_fingerprint,
    governed_hypothesis_semantic_fingerprint,
    r6_to_r7_handoff_semantic_fingerprint,
)
from commerce_lens.contracts.required_evidence import (
    ApplicabilityLevel,
    ApplicabilityState,
    DependencyClassification,
    DependencyRequirement,
    DimensionRequirement,
    EvidenceDimension,
    EvidenceRole,
    HypothesisFamilyRequirementTemplate,
    MeasurementClassification,
    MeasurementRequirement,
    RequirementConsequence,
    RequirementJudgment,
    RequirementOutcome,
    ResolvedRequiredEvidenceProfile,
    SlotBinding,
    requirement_template_semantic_fingerprint,
    resolved_profile_semantic_fingerprint,
    validate_profile_against_template,
)
from commerce_lens.diagnostic.family_registry import MVP_FAMILY_REGISTRY
from commerce_lens.evidence.identifiers import stable_content_id


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
NOW = datetime(2026, 9, 25, 1, 0, tzinfo=UTC)


def _proposition_data() -> dict[str, object]:
    family = MVP_FAMILY_REGISTRY.get_family("product_composition_association")
    data: dict[str, object] = {
        "proposition_id": "pending",
        "proposition_schema_version": "1.0.0",
        "family_id": family.family_id,
        "family_version": family.family_version,
        "family_fingerprint": family.family_fingerprint,
        "relationship": StructuredRelationship(
            relationship_type=RelationshipType.ASSOCIATION,
            direction=RelationshipDirection.UNSPECIFIED,
            comparison_basis="baseline versus comparison period",
            bounded_strength="non-causal association proposed for future testing",
        ),
        "outcome_ref": "metric:revenue_change@1.0.0",
        "scope_ref": "scope:all-eligible",
        "baseline_period_ref": "period:baseline",
        "comparison_period_ref": "period:comparison",
        "baseline_population_ref": "population:baseline",
        "comparison_population_ref": "population:comparison",
        "metric_refs": ("metric:revenue_change@1.0.0",),
        "variable_refs": ("field:product_id", "field:line_revenue"),
        "source_observation_refs": ("dataset:orders",),
        "source_mechanical_result_refs": ("r4:decomposition",),
        "intended_use": "diagnostic",
        "maximum_permitted_meaning": "untested bounded association hypothesis",
        "prohibited_meanings": ("causality", "support", "explanation"),
        "authority_bindings": (
            AuthorityBinding(
                authority_ref="R2_HYPOTHESIS_FINDING_STATE_MODEL",
                authority_version="1.0",
                authority_fingerprint=HASH_A,
            ),
        ),
        "display_wording": "Hypothesis—not tested.",
        "display_label": "Product composition",
    }
    data["proposition_id"] = stable_content_id(
        "diagprop", diagnostic_proposition_semantic_fingerprint(data)
    )
    return data


def _proposition(**updates: object) -> DiagnosticProposition:
    data = {**_proposition_data(), **updates}
    data["semantic_fingerprint"] = diagnostic_proposition_semantic_fingerprint(data)
    data["proposition_id"] = stable_content_id("diagprop", data["semantic_fingerprint"])
    return DiagnosticProposition(**data)


def _evaluation_data() -> dict[str, object]:
    proposition = _proposition()
    return {
        "evaluation_id": "eval-001",
        "evaluation_schema_version": "1.0.0",
        "diagnostic_proposition_ref": proposition.proposition_id,
        "diagnostic_proposition_fingerprint": proposition.semantic_fingerprint,
        "resolved_profile_ref": "profile-001",
        "resolved_profile_version": "1.0.0",
        "resolved_profile_fingerprint": HASH_B,
        "requirement_judgment_bundle_ref": "judgments-001",
        "requirement_judgment_bundle_fingerprint": HASH_C,
        "evidence_readiness": EvidenceReadiness.MISSING_INTERNAL_EVIDENCE,
        "test_eligibility": EligibilityState.NOT_ELIGIBLE,
        "first_controlling_blocker": "missing governed method authority",
        "analytical_outcome": AnalyticalOutcome.NOT_EVALUATED,
        "alternative_explanation_state": AlternativeExplanationState.NOT_EVALUATED,
        "authority_bindings": (
            AuthorityBinding(
                authority_ref="R3_REQUIRED_EVIDENCE_MATRIX",
                authority_version="1.0",
                authority_fingerprint=HASH_B,
            ),
        ),
        "finalized_at": NOW,
    }


def _evaluation(**updates: object) -> PreTestDiagnosticEvaluation:
    data = {**_evaluation_data(), **updates}
    data["evaluation_fingerprint"] = pretest_evaluation_semantic_fingerprint(data)
    return PreTestDiagnosticEvaluation(**data)


def _dimension_decisions() -> tuple[DimensionRequirement, ...]:
    return tuple(
        DimensionRequirement(
            dimension=dimension,
            applicability=ApplicabilityState.REQUIRED,
            applicability_level=ApplicabilityLevel.PROPOSITION,
            requirement_ref=f"requirement:{dimension.value}",
            controlling_authority_refs=("R3",),
            failure_consequence="blocks eligibility",
        )
        for dimension in EvidenceDimension
    )


def _profile_data() -> dict[str, object]:
    proposition = _proposition()
    template = MVP_FAMILY_REGISTRY.get_requirement_template(proposition.family_id)
    return {
        "profile_id": "pending",
        "profile_version": "1.0.0",
        "profile_schema_version": "1.0.0",
        "template_id": template.template_id,
        "template_version": template.template_version,
        "template_fingerprint": template.template_fingerprint,
        "diagnostic_proposition_ref": proposition.proposition_id,
        "diagnostic_proposition_fingerprint": proposition.semantic_fingerprint,
        "exact_slot_bindings": (
            SlotBinding(slot="outcome_ref", bound_ref=proposition.outcome_ref),
            SlotBinding(slot="scope_ref", bound_ref=proposition.scope_ref),
        ),
        "resolved_evidence_roles": template.required_evidence_roles,
        "dimension_applicability_decisions": _dimension_decisions(),
        "dependency_classifications": (
            DependencyRequirement(
                requirement_ref="governed_product_id",
                classification=DependencyClassification.INTERNAL,
            ),
        ),
        "measurement_classifications": (
            MeasurementRequirement(
                requirement_ref="product_composition_measurement",
                role=EvidenceRole.EXPLANATORY_VARIABLE,
                classification=MeasurementClassification.GOVERNED_TRANSFORMED_MEASUREMENT,
                permitted_use="bounded future test",
            ),
        ),
        "method_requirement_refs": (),
        "blocking_rules": ("missing governed method blocks",),
        "qualification_rules": (),
        "narrowing_rules": (),
    }


def _profile(**updates: object) -> ResolvedRequiredEvidenceProfile:
    data = {**_profile_data(), **updates}
    data["profile_fingerprint"] = resolved_profile_semantic_fingerprint(data)
    data["profile_id"] = stable_content_id("reqprof", data["profile_fingerprint"])
    return ResolvedRequiredEvidenceProfile(**data)


def _provenance_data() -> dict[str, object]:
    return {
        "generation_provenance_id": "genprov-001",
        "generator_id": "bounded-candidate-producer",
        "generator_version": "1.0.0",
        "prompt_template_id": "prompt:r6-candidates",
        "prompt_template_version": "1.0.0",
        "prompt_template_fingerprint": HASH_A,
        "model_id": None,
        "generation_parameters": GenerationParameters(temperature=0.0, max_output_tokens=500),
        "raw_candidate_artifact_ref": None,
        "generated_at": NOW,
    }


def _governed_data() -> dict[str, object]:
    return {
        "governed_hypothesis_id": "hyp-001",
        "governed_hypothesis_schema_version": "1.0.0",
        "diagnostic_proposition_ref": "prop-001",
        "diagnostic_proposition_fingerprint": HASH_A,
        "pretest_evaluation_ref": "eval-001",
        "pretest_evaluation_fingerprint": HASH_B,
        "resolved_profile_ref": "profile-001",
        "resolved_profile_fingerprint": HASH_C,
        "generation_provenance_ref": "genprov-001",
        "generation_provenance_fingerprint": "d" * 64,
    }


def _handoff_data() -> dict[str, object]:
    family = MVP_FAMILY_REGISTRY.get_family("discounting_association")
    return {
        "handoff_id": "handoff-001",
        "handoff_schema_version": "1.0.0",
        "diagnostic_proposition_ref": "prop-001",
        "diagnostic_proposition_fingerprint": HASH_A,
        "pretest_evaluation_ref": "eval-001",
        "pretest_evaluation_fingerprint": HASH_B,
        "family_id": family.family_id,
        "family_version": family.family_version,
        "family_fingerprint": family.family_fingerprint,
        "resolved_profile_ref": "profile-001",
        "resolved_profile_version": "1.0.0",
        "resolved_profile_fingerprint": HASH_C,
        "scope_ref": "scope:all-eligible",
        "baseline_period_ref": "period:baseline",
        "comparison_period_ref": "period:comparison",
        "population_refs": ("population:baseline", "population:comparison"),
        "metric_refs": ("metric:revenue_change@1.0.0",),
        "variable_refs": ("variable:discount",),
        "source_observation_refs": ("dataset:orders",),
        "source_mechanical_result_refs": (),
        "requirement_judgment_refs": ("judgment:missing-list-price",),
        "evidence_readiness": EvidenceReadiness.MISSING_INTERNAL_EVIDENCE,
        "missing_internal_requirement_refs": ("requirement:original-list-price",),
        "unmet_external_requirement_refs": (),
        "method_ref": None,
        "method_version": None,
        "support_criterion_ref": None,
        "support_criterion_version": None,
        "validation_profile_ref": None,
        "validation_profile_version": None,
        "test_eligibility": EligibilityState.NOT_ELIGIBLE,
        "first_controlling_blocker": "missing original/list-price evidence",
        "governed_hypothesis_ref": "hyp-001",
        "governed_hypothesis_fingerprint": "d" * 64,
        "generation_provenance_ref": "genprov-001",
    }


def test_identical_material_proposition_has_identical_fingerprint() -> None:
    assert _proposition().semantic_fingerprint == _proposition().semantic_fingerprint


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("baseline_period_ref", "period:different"),
        ("comparison_population_ref", "population:different"),
        ("family_version", "2.0.0"),
        (
            "relationship",
            StructuredRelationship(
                relationship_type=RelationshipType.PATTERN,
                direction=RelationshipDirection.POSITIVE,
                comparison_basis="different basis",
                bounded_strength="bounded pattern",
            ),
        ),
    ],
)
def test_material_proposition_change_changes_fingerprint(field: str, value: object) -> None:
    original = _proposition()
    changed = _proposition(**{field: value})
    assert original.semantic_fingerprint != changed.semantic_fingerprint
    assert original.proposition_id != changed.proposition_id


def test_display_only_proposition_change_does_not_change_fingerprint() -> None:
    first = _proposition(display_wording="First wording", display_label="First label")
    second = _proposition(display_wording="Other wording", display_label="Other label")
    assert first.semantic_fingerprint == second.semantic_fingerprint


def test_semantically_unordered_proposition_refs_do_not_change_fingerprint() -> None:
    first = _proposition(variable_refs=("field:product_id", "field:line_revenue"))
    second = _proposition(variable_refs=("field:line_revenue", "field:product_id"))
    assert first.semantic_fingerprint == second.semantic_fingerprint


def test_missing_or_malformed_proposition_fingerprint_is_rejected() -> None:
    data = _proposition_data()
    with pytest.raises(ValidationError):
        DiagnosticProposition(**data)
    with pytest.raises(ValidationError):
        DiagnosticProposition(**data, semantic_fingerprint="not-a-fingerprint")


def test_not_evaluated_pretest_evaluation_is_valid_and_immutable() -> None:
    evaluation = _evaluation()
    assert evaluation.analytical_outcome is AnalyticalOutcome.NOT_EVALUATED
    with pytest.raises(ValidationError):
        evaluation.test_eligibility = EligibilityState.ELIGIBLE_NOT_EXECUTED


@pytest.mark.parametrize(
    "outcome",
    [AnalyticalOutcome.CRITERION_MET, AnalyticalOutcome.CRITERION_NOT_MET, AnalyticalOutcome.PROPOSITION_CONTRADICTED],
)
def test_pretest_evaluation_rejects_tested_outcomes(outcome: AnalyticalOutcome) -> None:
    data = _evaluation_data()
    data["analytical_outcome"] = outcome
    data["evaluation_fingerprint"] = pretest_evaluation_semantic_fingerprint(data)
    with pytest.raises(ValidationError, match="pre-test evaluation"):
        PreTestDiagnosticEvaluation(**data)


def test_pretest_evaluation_requires_exact_proposition_and_profile_refs() -> None:
    data = _evaluation_data()
    data.pop("resolved_profile_ref")
    with pytest.raises(ValidationError):
        PreTestDiagnosticEvaluation(**data, evaluation_fingerprint=HASH_A)


def test_cached_derived_disposition_cannot_become_evaluation_authority() -> None:
    data = _evaluation_data()
    data["evaluation_fingerprint"] = pretest_evaluation_semantic_fingerprint(data)
    data["derived_disposition"] = "SUPPORTED_DIAGNOSTIC_FINDING"
    with pytest.raises(ValidationError, match="derived_disposition"):
        PreTestDiagnosticEvaluation(**data)


def test_profile_requires_all_twelve_dimensions_exactly_once() -> None:
    profile = _profile()
    assert {item.dimension for item in profile.dimension_applicability_decisions} == set(EvidenceDimension)
    data = _profile_data()
    data["dimension_applicability_decisions"] = data["dimension_applicability_decisions"][:-1]
    data["profile_fingerprint"] = resolved_profile_semantic_fingerprint(data)
    data["profile_id"] = stable_content_id("reqprof", data["profile_fingerprint"])
    with pytest.raises(ValidationError):
        ResolvedRequiredEvidenceProfile(**data)


def test_profile_rejects_duplicate_dimension_even_when_all_twelve_entries_exist() -> None:
    data = _profile_data()
    decisions = list(data["dimension_applicability_decisions"])
    decisions[-1] = decisions[0]
    data["dimension_applicability_decisions"] = tuple(decisions)
    data["profile_fingerprint"] = resolved_profile_semantic_fingerprint(data)
    data["profile_id"] = stable_content_id("reqprof", data["profile_fingerprint"])
    with pytest.raises(ValidationError, match="exactly once"):
        ResolvedRequiredEvidenceProfile(**data)


def test_conditional_dimension_requires_reviewable_condition_reference() -> None:
    with pytest.raises(ValidationError, match="condition reference"):
        DimensionRequirement(
            dimension=EvidenceDimension.METRIC_COMPATIBILITY,
            applicability=ApplicabilityState.CONDITIONAL,
            applicability_level=ApplicabilityLevel.CROSS_ROLE_RELATIONSHIP,
            requirement_ref="requirement:metric-compatibility",
            controlling_authority_refs=("R3",),
            failure_consequence="blocks eligibility when triggered",
        )


def test_not_applicable_dimension_requires_governed_reason() -> None:
    with pytest.raises(ValidationError, match="governed reason"):
        DimensionRequirement(
            dimension=EvidenceDimension.METRIC_COMPATIBILITY,
            applicability=ApplicabilityState.NOT_APPLICABLE,
            applicability_level=ApplicabilityLevel.PROPOSITION,
        )


def test_exact_profile_preserves_governed_not_applicable_when_template_is_conditional() -> None:
    source_template = MVP_FAMILY_REGISTRY.get_requirement_template("product_composition_association")
    template_data = source_template.model_dump(mode="python")
    template_data.update(
        template_id="r3-template:test-non-metric-association",
        family_id="test_non_metric_association",
    )
    template_data["template_fingerprint"] = requirement_template_semantic_fingerprint(template_data)
    template = HypothesisFamilyRequirementTemplate(**template_data)

    data = _profile_data()
    data.update(
        template_id=template.template_id,
        template_version=template.template_version,
        template_fingerprint=template.template_fingerprint,
        diagnostic_proposition_ref="diagprop:test-non-metric-association",
        diagnostic_proposition_fingerprint=HASH_A,
        exact_slot_bindings=(
            SlotBinding(slot="outcome_ref", bound_ref="observation:non-metric-outcome"),
            SlotBinding(slot="scope_ref", bound_ref="scope:test"),
        ),
    )
    data["dimension_applicability_decisions"] = tuple(
        DimensionRequirement(
            dimension=item.dimension,
            applicability=ApplicabilityState.NOT_APPLICABLE,
            applicability_level=item.applicability_level,
            controlling_authority_refs=item.controlling_authority_refs,
            governed_reason="exact binding establishes that no governed Metric participates",
        )
        if item.dimension is EvidenceDimension.METRIC_COMPATIBILITY
        else item
        for item in data["dimension_applicability_decisions"]
    )
    data["profile_fingerprint"] = resolved_profile_semantic_fingerprint(data)
    data["profile_id"] = stable_content_id("reqprof", data["profile_fingerprint"])
    profile = ResolvedRequiredEvidenceProfile(**data)

    validate_profile_against_template(profile, template)
    metric_decision = next(
        item
        for item in profile.dimension_applicability_decisions
        if item.dimension is EvidenceDimension.METRIC_COMPATIBILITY
    )
    assert metric_decision.applicability is ApplicabilityState.NOT_APPLICABLE


def test_exact_profile_cannot_waive_required_template_dimension() -> None:
    template = MVP_FAMILY_REGISTRY.get_requirement_template("product_composition_association")
    data = _profile_data()
    data["dimension_applicability_decisions"] = tuple(
        DimensionRequirement(
            dimension=item.dimension,
            applicability=ApplicabilityState.NOT_APPLICABLE,
            applicability_level=item.applicability_level,
            controlling_authority_refs=item.controlling_authority_refs,
            governed_reason="attempted exact-binding waiver",
        )
        if item.dimension is EvidenceDimension.RELEVANCE
        else item
        for item in data["dimension_applicability_decisions"]
    )
    data["profile_fingerprint"] = resolved_profile_semantic_fingerprint(data)
    data["profile_id"] = stable_content_id("reqprof", data["profile_fingerprint"])
    profile = ResolvedRequiredEvidenceProfile(**data)

    with pytest.raises(ValueError, match="cannot weaken REQUIRED.*relevance"):
        validate_profile_against_template(profile, template)


def test_changed_proposition_invalidates_existing_profile_fingerprint() -> None:
    profile = _profile()
    with pytest.raises(ValidationError, match="exact proposition binding"):
        ResolvedRequiredEvidenceProfile(
            **{
                **profile.model_dump(mode="python"),
                "diagnostic_proposition_fingerprint": "f" * 64,
            }
        )


def test_template_cannot_masquerade_as_resolved_profile() -> None:
    template = MVP_FAMILY_REGISTRY.get_requirement_template("product_composition_association")
    with pytest.raises(ValidationError):
        ResolvedRequiredEvidenceProfile.model_validate(template.model_dump(mode="python"))


@pytest.mark.parametrize("outcome", list(RequirementOutcome))
def test_requirement_judgment_preserves_all_governed_outcomes(outcome: RequirementOutcome) -> None:
    dependency = DependencyClassification.EXTERNAL if outcome is RequirementOutcome.EXTERNAL_UNMET else None
    judgment = RequirementJudgment(
        judgment_id=f"judgment:{outcome.value}",
        requirement_ref="requirement:source",
        requirement_version="1.0.0",
        outcome=outcome,
        reason_code=f"reason:{outcome.value}",
        evidence_refs=(),
        authority_refs=("authority:R3",),
        role=EvidenceRole.SOURCE_AUTHORITY_PROVENANCE,
        dimension=EvidenceDimension.SOURCE_AUTHORITY,
        context="exact proposition source authority",
        dependency_classification=dependency,
        consequence=(
            RequirementConsequence.NONE
            if outcome is RequirementOutcome.NOT_APPLICABLE
            else RequirementConsequence.BLOCKING
        ),
        authority_version="1.0.0",
    )
    assert judgment.outcome is outcome


def test_candidate_contract_accepts_only_untrusted_proposal_fields() -> None:
    candidate = CandidateProposal(
        family_id="product_composition_association",
        family_version="1.0.0",
        structured_slot_values=(CandidateSlot(slot="outcome_ref", value="metric:revenue-change"),),
        source_reference_proposals=("dataset:orders",),
        display_template_id="r6-product-composition-untested-v1",
        non_authoritative_wording="Hypothesis—not tested.",
    )
    batch = CandidateProposalBatch(
        batch_schema_version="1.0.0",
        producer_ref="producer:test",
        generation_request_ref="request:test",
        candidates=(candidate,),
    )
    assert batch.candidates == (candidate,)


@pytest.mark.parametrize(
    "forbidden",
    ["status", "first_blocker", "evidence_sufficiency", "test_eligibility", "confidence", "probability"],
)
def test_candidate_contract_rejects_authority_and_scoring_fields(forbidden: str) -> None:
    data = {
        "family_id": "product_composition_association",
        "family_version": "1.0.0",
        "structured_slot_values": ({"slot": "outcome_ref", "value": "metric:revenue-change"},),
        forbidden: "forbidden",
    }
    with pytest.raises(ValidationError):
        CandidateProposal.model_validate(data)


def test_generation_provenance_is_separate_from_supporting_evidence() -> None:
    data = _provenance_data()
    data["provenance_fingerprint"] = generation_provenance_semantic_fingerprint(data)
    provenance = GenerationProvenance(**data)
    assert "evidence_refs" not in GenerationProvenance.model_fields
    with pytest.raises(ValidationError):
        GenerationProvenance(**data, evidence_refs=("evidence:fake",))


def test_governed_hypothesis_is_thin_reference_wrapper() -> None:
    data = _governed_data()
    data["governed_hypothesis_fingerprint"] = governed_hypothesis_semantic_fingerprint(data)
    hypothesis = GovernedHypothesis(**data)
    assert set(GovernedHypothesis.model_fields) == {
        "governed_hypothesis_id",
        "governed_hypothesis_schema_version",
        "governed_hypothesis_fingerprint",
        "diagnostic_proposition_ref",
        "diagnostic_proposition_fingerprint",
        "pretest_evaluation_ref",
        "pretest_evaluation_fingerprint",
        "resolved_profile_ref",
        "resolved_profile_fingerprint",
        "generation_provenance_ref",
        "generation_provenance_fingerprint",
    }
    with pytest.raises(ValidationError):
        GovernedHypothesis(**data, proposition_body={"not": "allowed"})


def test_r6_to_r7_handoff_preserves_required_authority_references() -> None:
    data = _handoff_data()
    data["handoff_fingerprint"] = r6_to_r7_handoff_semantic_fingerprint(data)
    handoff = R6ToR7Handoff(**data)
    assert handoff.diagnostic_proposition_ref == "prop-001"
    assert handoff.resolved_profile_ref == "profile-001"
    assert handoff.requirement_judgment_refs == ("judgment:missing-list-price",)
    assert handoff.r7_execution_permitted is False


def test_r7_execution_gate_only_accepts_eligible_not_executed() -> None:
    data = _handoff_data()
    data.update(
        evidence_readiness=EvidenceReadiness.READY_FOR_TEST,
        missing_internal_requirement_refs=(),
        test_eligibility=EligibilityState.ELIGIBLE_NOT_EXECUTED,
        first_controlling_blocker=None,
    )
    data["handoff_fingerprint"] = r6_to_r7_handoff_semantic_fingerprint(data)
    assert R6ToR7Handoff(**data).r7_execution_permitted is True


def test_handoff_rejects_malformed_fingerprint() -> None:
    with pytest.raises(ValidationError):
        R6ToR7Handoff(**_handoff_data(), handoff_fingerprint=HASH_A)
