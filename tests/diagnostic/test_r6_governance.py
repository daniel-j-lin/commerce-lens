from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from commerce_lens.contracts.common import ClaimType
from commerce_lens.contracts.diagnostic import (
    AlternativeExplanationState,
    AnalyticalOutcome,
    AuthorityBinding,
    DiagnosticProposition,
    RelationshipDirection,
    RelationshipType,
    StructuredRelationship,
    TestEligibility as DiagnosticTestEligibility,
    diagnostic_proposition_semantic_fingerprint,
)
from commerce_lens.contracts.hypotheses import CandidateProposal, CandidateSlot
from commerce_lens.contracts.required_evidence import (
    ApplicabilityState,
    DependencyClassification,
    DimensionRequirement,
    EvidenceDimension,
    HypothesisFamilyRequirementTemplate,
    ResolvedRequiredEvidenceProfile,
    requirement_template_semantic_fingerprint,
    resolved_profile_semantic_fingerprint,
    validate_profile_against_template,
)
from commerce_lens.diagnostic.family_registry import MVP_FAMILY_REGISTRY
from commerce_lens.diagnostic.governance import (
    AuthorityClass,
    DiagnosticAdmissionState,
    EvidenceAvailability,
    EvidenceConflictAssessment,
    EvidenceFitnessState,
    EvidenceOrigin,
    GovernanceAuthenticationError,
    PreTestDisposition,
    PreTestAuthorityRegistry,
    RegisteredAuthority,
    RequirementEvidenceAssessment,
    evidence_conflict_assessment_fingerprint,
    govern_pretest,
    pretest_authority_registry_fingerprint,
    requirement_evidence_assessment_fingerprint,
    resolve_dimension_applicability,
)
from commerce_lens.evidence.identifiers import stable_content_id
from commerce_lens.metrics.registry import METRIC_DEFINITION_VERSION


HASH_A = "a" * 64
HASH_B = "b" * 64
NOW = datetime(2026, 9, 25, 3, 0, tzinfo=UTC)


def _authority(reference: str = "authority:synthetic") -> AuthorityBinding:
    return AuthorityBinding(
        authority_ref=reference,
        authority_version="1.0.0",
        authority_fingerprint=HASH_A,
    )


def _registered(
    authority_class: AuthorityClass,
    binding: AuthorityBinding,
    *,
    subject_refs: tuple[str, ...] = (),
    intended_uses: tuple[str, ...] = (),
    classification: DependencyClassification | None = None,
) -> RegisteredAuthority:
    return RegisteredAuthority(
        authority_class=authority_class,
        binding=binding,
        subject_refs=subject_refs,
        intended_uses=intended_uses,
        dependency_classification=classification,
    )


def _template_binding(family_id: str) -> AuthorityBinding:
    template = MVP_FAMILY_REGISTRY.get_requirement_template(family_id)
    return AuthorityBinding(
        authority_ref=template.template_id,
        authority_version=template.template_version,
        authority_fingerprint=template.template_fingerprint,
    )


def _family_inputs(family_id: str) -> tuple[tuple[str, ...], tuple[str, ...], tuple[CandidateSlot, ...]]:
    common = (
        CandidateSlot(
            slot="outcome_ref",
            value=f"metric:revenue_change@{METRIC_DEFINITION_VERSION}",
        ),
        CandidateSlot(slot="baseline_period_ref", value="period:baseline"),
        CandidateSlot(slot="comparison_period_ref", value="period:comparison"),
        CandidateSlot(slot="baseline_population_ref", value="population:baseline"),
        CandidateSlot(slot="comparison_population_ref", value="population:comparison"),
        CandidateSlot(slot="scope_ref", value="scope:all-eligible"),
    )
    if family_id == "product_composition_association":
        variables = ("field:product_id", "field:line_revenue")
        sources = ("dataset:orders",)
        specific = (
            CandidateSlot(slot="product_identity_ref", value="field:product_id"),
            CandidateSlot(slot="monetary_observation_ref", value="field:line_revenue"),
            CandidateSlot(slot="source_observation_refs", value=sources),
        )
    elif family_id == "discounting_association":
        variables = (
            "field:original_list_price",
            "definition:governed_discount",
            "field:line_revenue",
        )
        sources = ("dataset:orders",)
        specific = (
            CandidateSlot(slot="original_or_list_price_ref", value="field:original_list_price"),
            CandidateSlot(slot="discount_semantics_ref", value="definition:governed_discount"),
            CandidateSlot(slot="monetary_observation_ref", value="field:line_revenue"),
            CandidateSlot(slot="source_observation_refs", value=sources),
        )
    else:
        variables = ("external:consumer_sentiment",)
        sources = ("source:governed_market_index",)
        specific = (
            CandidateSlot(slot="external_factor_ref", value="external:consumer_sentiment"),
            CandidateSlot(
                slot="external_evidence_dependency_ref",
                value="source:governed_market_index",
            ),
            CandidateSlot(slot="source_observation_refs", value=sources),
            CandidateSlot(slot="explicit_activation_ref", value="activation:user-request"),
        )
    return variables, sources, (*common, *specific)


def _proposition(family_id: str = "product_composition_association", **updates: object) -> DiagnosticProposition:
    family = MVP_FAMILY_REGISTRY.get_family(family_id)
    variables, sources, _ = _family_inputs(family_id)
    bindings = [_authority("R2_HYPOTHESIS_FINDING_STATE_MODEL")]
    if family_id == "external_market_association":
        bindings.append(_authority("activation:user-request"))
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
        "outcome_ref": f"metric:revenue_change@{METRIC_DEFINITION_VERSION}",
        "scope_ref": "scope:all-eligible",
        "baseline_period_ref": "period:baseline",
        "comparison_period_ref": "period:comparison",
        "baseline_population_ref": "population:baseline",
        "comparison_population_ref": "population:comparison",
        "metric_refs": (f"metric:revenue_change@{METRIC_DEFINITION_VERSION}",),
        "variable_refs": variables,
        "source_observation_refs": sources,
        "source_mechanical_result_refs": (),
        "intended_use": "diagnostic",
        "maximum_permitted_meaning": "untested bounded association hypothesis",
        "prohibited_meanings": ("causality", "support", "explanation"),
        "authority_bindings": tuple(bindings),
    }
    data.update(updates)
    data["semantic_fingerprint"] = diagnostic_proposition_semantic_fingerprint(data)
    data["proposition_id"] = stable_content_id("diagprop", data["semantic_fingerprint"])
    return DiagnosticProposition(**data)


def _candidate(family_id: str = "product_composition_association", **updates: object) -> CandidateProposal:
    _, _, slots = _family_inputs(family_id)
    return CandidateProposal(
        family_id=family_id,
        family_version="1.0.0",
        structured_slot_values=tuple(updates.pop("slots", slots)),
        source_reference_proposals=(),
        **updates,
    )


def _assessment(
    proposition: DiagnosticProposition,
    requirement_ref: str,
    classification: DependencyClassification,
    **updates: object,
) -> RequirementEvidenceAssessment:
    availability = updates.pop("availability", EvidenceAvailability.PRESENT)
    if availability is EvidenceAvailability.PRESENT:
        admission = updates.pop("admission_state", DiagnosticAdmissionState.DIAGNOSTIC_ADMITTED)
        evidence_refs = updates.pop("evidence_refs", (f"evidence:{requirement_ref}",))
        fitness = updates.pop("fitness_state", EvidenceFitnessState.PASSED)
    else:
        admission = updates.pop("admission_state", DiagnosticAdmissionState.UNRESOLVED)
        evidence_refs = updates.pop("evidence_refs", ())
        fitness = updates.pop("fitness_state", EvidenceFitnessState.UNRESOLVED)
    origin = updates.pop(
        "origin",
        (
            EvidenceOrigin.GOVERNED_EXTERNAL
            if classification is DependencyClassification.EXTERNAL
            else EvidenceOrigin.GOVERNED_INTERNAL
        ),
    )
    data: dict[str, object] = {
        "assessment_id": "pending",
        "assessment_version": "1.0.0",
        "requirement_ref": requirement_ref,
        "availability": availability,
        "admission_state": admission,
        "fitness_state": fitness,
        "origin": origin,
        "dependency_classification": classification,
        "evidence_refs": evidence_refs,
        "diagnostic_proposition_ref": proposition.proposition_id,
        "diagnostic_proposition_fingerprint": proposition.semantic_fingerprint,
        "scope_ref": proposition.scope_ref,
        "baseline_period_ref": proposition.baseline_period_ref,
        "comparison_period_ref": proposition.comparison_period_ref,
        "baseline_population_ref": proposition.baseline_population_ref,
        "comparison_population_ref": proposition.comparison_population_ref,
        "metric_refs": proposition.metric_refs,
        "variable_refs": proposition.variable_refs,
        "source_observation_refs": proposition.source_observation_refs,
        "authority_bindings": (_authority(f"assessment-authority:{requirement_ref}"),),
        "diagnostic_admission_authority": (
            _authority(f"diagnostic-admission:{requirement_ref}")
            if admission is DiagnosticAdmissionState.DIAGNOSTIC_ADMITTED
            else None
        ),
        "failure_reason": None,
    }
    data.update(updates)
    data["assessment_fingerprint"] = requirement_evidence_assessment_fingerprint(data)
    data["assessment_id"] = stable_content_id("reqevid", data["assessment_fingerprint"])
    return RequirementEvidenceAssessment(**data)


def _all_assessments(
    proposition: DiagnosticProposition,
    *,
    omit: tuple[str, ...] = (),
) -> tuple[RequirementEvidenceAssessment, ...]:
    template = MVP_FAMILY_REGISTRY.get_requirement_template(proposition.family_id)
    family_class = template.dependency_source_classifications[0].classification
    requirements = [
        (item.requirement_ref, family_class)
        for item in template.dimension_requirements
        if item.requirement_ref is not None
    ]
    requirements.extend(
        (item.requirement_ref, item.classification)
        for item in template.dependency_source_classifications
    )
    return tuple(
        _assessment(proposition, reference, classification)
        for reference, classification in requirements
        if reference not in omit
    )


def _authority_registry(
    proposition: DiagnosticProposition,
    assessments: tuple[RequirementEvidenceAssessment, ...],
    *,
    methods: tuple[AuthorityBinding, ...] = (),
    conflict: EvidenceConflictAssessment | None = None,
) -> PreTestAuthorityRegistry:
    family = MVP_FAMILY_REGISTRY.get_family(proposition.family_id)
    family_class = family.dependency_classifications[0]
    records: list[RegisteredAuthority] = []
    records.extend(
        _registered(
            AuthorityClass.INTENDED_USE,
            binding,
            subject_refs=(proposition.proposition_id,),
            intended_uses=("diagnostic",),
        )
        for binding in proposition.authority_bindings
    )
    context = {
        AuthorityClass.SCOPE: (proposition.scope_ref,),
        AuthorityClass.PERIOD: (
            proposition.baseline_period_ref,
            proposition.comparison_period_ref,
        ),
        AuthorityClass.POPULATION: (
            proposition.baseline_population_ref,
            proposition.comparison_population_ref,
        ),
        AuthorityClass.VARIABLE: proposition.variable_refs,
        AuthorityClass.SOURCE_REFERENCE: (
            *proposition.source_observation_refs,
            *proposition.source_mechanical_result_refs,
        ),
    }
    for authority_class, references in context.items():
        records.extend(
            _registered(
                authority_class,
                _authority(reference),
                subject_refs=(proposition.proposition_id,),
                classification=(
                    family_class
                    if authority_class
                    in {AuthorityClass.VARIABLE, AuthorityClass.SOURCE_REFERENCE}
                    else None
                ),
            )
            for reference in references
        )
    for assessment in assessments:
        subjects = (proposition.proposition_id, assessment.requirement_ref)
        records.extend(
            _registered(
                AuthorityClass.EVIDENCE_ASSESSMENT,
                binding,
                subject_refs=subjects,
                classification=assessment.dependency_classification,
            )
            for binding in assessment.authority_bindings
        )
        records.extend(
            _registered(
                AuthorityClass.EVIDENCE,
                _authority(evidence_ref),
                subject_refs=subjects,
                classification=assessment.dependency_classification,
            )
            for evidence_ref in assessment.evidence_refs
        )
        if assessment.diagnostic_admission_authority is not None:
            records.append(
                _registered(
                    AuthorityClass.DIAGNOSTIC_ADMISSION,
                    assessment.diagnostic_admission_authority,
                    subject_refs=(*subjects, *assessment.evidence_refs),
                    intended_uses=("diagnostic",),
                    classification=assessment.dependency_classification,
                )
            )
    records.extend(_registered(AuthorityClass.METHOD, method) for method in methods)
    if conflict is not None:
        records.extend(
            _registered(
                AuthorityClass.EVIDENCE_CONFLICT,
                binding,
                subject_refs=(proposition.proposition_id, *conflict.evidence_refs),
            )
            for binding in conflict.authority_bindings
        )
        known_evidence_refs = {
            record.binding.authority_ref
            for record in records
            if record.authority_class is AuthorityClass.EVIDENCE
        }
        records.extend(
            _registered(
                AuthorityClass.EVIDENCE,
                _authority(evidence_ref),
                subject_refs=(proposition.proposition_id,),
                classification=family_class,
            )
            for evidence_ref in conflict.evidence_refs
            if evidence_ref not in known_evidence_refs
        )
    return _registry_from_records(tuple(records))


def _registry_from_records(
    records: tuple[RegisteredAuthority, ...],
) -> PreTestAuthorityRegistry:
    data: dict[str, object] = {
        "registry_id": "commerce_lens_r6_pretest_authorities",
        "registry_version": "1.0.0",
        "authorities": records,
    }
    data["registry_fingerprint"] = pretest_authority_registry_fingerprint(data)
    return PreTestAuthorityRegistry(**data)


def _run(
    family_id: str = "product_composition_association",
    *,
    proposition: DiagnosticProposition | None = None,
    candidate: CandidateProposal | None = None,
    assessments: tuple[RequirementEvidenceAssessment, ...] | None = None,
    template_binding: AuthorityBinding | None | object = ...,
    authority_registry: PreTestAuthorityRegistry | None = None,
    **kwargs: object,
):
    proposition = proposition or _proposition(family_id)
    candidate = candidate or _candidate(family_id)
    if assessments is None:
        assessments = _all_assessments(proposition)
    binding = _template_binding(family_id) if template_binding is ... else template_binding
    methods = kwargs.get("proposed_method_refs", ())
    conflict = kwargs.get("conflict_assessment")
    if authority_registry is None:
        authority_registry = _authority_registry(
            proposition,
            assessments,
            methods=methods,
            conflict=conflict,
        )
    return govern_pretest(
        proposition,
        candidate,
        binding,
        assessments,
        authority_registry=authority_registry,
        finalized_at=NOW,
        **kwargs,
    )


def test_product_composition_is_hypothesis_only_and_not_eligible() -> None:
    result = _run()
    assert result.derived_disposition is PreTestDisposition.HYPOTHESIS_ONLY
    assert result.evaluation.test_eligibility is DiagnosticTestEligibility.NOT_ELIGIBLE
    assert result.evaluation.first_controlling_blocker == "method_authority_unavailable"
    assert result.evaluation.analytical_outcome is AnalyticalOutcome.NOT_EVALUATED
    assert result.evaluation.alternative_explanation_state is AlternativeExplanationState.NOT_COMPLETED


def test_discount_is_missing_internal_evidence_and_not_eligible() -> None:
    proposition = _proposition("discounting_association")
    result = _run(
        "discounting_association",
        proposition=proposition,
        assessments=_all_assessments(proposition),
    )
    assert result.derived_disposition is PreTestDisposition.MISSING_EVIDENCE
    assert result.evaluation.evidence_readiness.value == "MISSING_INTERNAL_EVIDENCE"
    assert result.evaluation.test_eligibility is DiagnosticTestEligibility.NOT_ELIGIBLE


def test_external_market_requires_external_evidence_and_is_not_eligible() -> None:
    proposition = _proposition("external_market_association")
    template = MVP_FAMILY_REGISTRY.get_requirement_template(proposition.family_id)
    missing = tuple(
        item.requirement_ref for item in template.dependency_source_classifications
    )
    result = _run(
        "external_market_association",
        proposition=proposition,
        assessments=_all_assessments(proposition, omit=missing),
    )
    assert result.derived_disposition is PreTestDisposition.EXTERNAL_EVIDENCE_REQUIRED
    assert result.evaluation.evidence_readiness.value == "EXTERNAL_EVIDENCE_REQUIRED"
    assert result.evaluation.test_eligibility is DiagnosticTestEligibility.NOT_ELIGIBLE


def test_authenticated_admitted_external_evidence_can_satisfy_requirement() -> None:
    proposition = _proposition("external_market_association")
    result = _run(
        "external_market_association",
        proposition=proposition,
        assessments=_all_assessments(proposition),
    )
    dependency = MVP_FAMILY_REGISTRY.get_requirement_template(
        proposition.family_id
    ).dependency_source_classifications[0]
    judgment = next(
        item
        for item in result.requirement_judgments
        if item.requirement_ref == dependency.requirement_ref
    )
    assert judgment.outcome.value == "SATISFIED"
    assert result.derived_disposition is PreTestDisposition.HYPOTHESIS_ONLY
    assert result.evaluation.test_eligibility is DiagnosticTestEligibility.NOT_ELIGIBLE
    assert result.evaluation.first_controlling_blocker == "method_authority_unavailable"


@pytest.mark.parametrize(
    ("family_id", "family_version", "code"),
    [
        ("unknown_family", "1.0.0", "unknown_family"),
        ("product_composition_association", "2.0.0", "wrong_family_version"),
    ],
)
def test_unknown_or_wrong_version_family_fails_closed(
    family_id: str,
    family_version: str,
    code: str,
) -> None:
    base = _proposition()
    data = base.model_dump(mode="python")
    data.update(family_id=family_id, family_version=family_version, family_fingerprint=HASH_B)
    data["semantic_fingerprint"] = diagnostic_proposition_semantic_fingerprint(data)
    data["proposition_id"] = stable_content_id("diagprop", data["semantic_fingerprint"])
    proposition = DiagnosticProposition(**data)
    candidate = _candidate()
    with pytest.raises(GovernanceAuthenticationError, match=code):
        _run(
            proposition=proposition,
            candidate=candidate,
            assessments=(),
            authority_registry=_authority_registry(base, ()),
        )


def test_wrong_family_fingerprint_fails_closed() -> None:
    base = _proposition()
    data = base.model_dump(mode="python")
    data["family_fingerprint"] = HASH_B
    data["semantic_fingerprint"] = diagnostic_proposition_semantic_fingerprint(data)
    data["proposition_id"] = stable_content_id("diagprop", data["semantic_fingerprint"])
    with pytest.raises(GovernanceAuthenticationError, match="wrong_family_fingerprint"):
        _run(proposition=DiagnosticProposition(**data), assessments=())


def test_missing_or_wrong_template_authority_fails_closed() -> None:
    with pytest.raises(GovernanceAuthenticationError, match="missing_template_authority"):
        _run(template_binding=None)
    wrong = AuthorityBinding(
        authority_ref="r3-template:wrong",
        authority_version="1.0.0",
        authority_fingerprint=HASH_B,
    )
    with pytest.raises(GovernanceAuthenticationError, match="template_authority_mismatch"):
        _run(template_binding=wrong)


def test_proposition_fingerprint_tamper_is_integrity_failure_not_missing_evidence() -> None:
    proposition = _proposition().model_copy(update={"scope_ref": "scope:tampered"})
    with pytest.raises(GovernanceAuthenticationError, match="proposition_authentication_failed"):
        _run(proposition=proposition, assessments=())


@pytest.mark.parametrize(
    ("authority_class", "authority_ref"),
    [
        (AuthorityClass.INTENDED_USE, "R2_HYPOTHESIS_FINDING_STATE_MODEL"),
        (AuthorityClass.SCOPE, "scope:all-eligible"),
        (AuthorityClass.PERIOD, "period:baseline"),
        (AuthorityClass.POPULATION, "population:baseline"),
        (AuthorityClass.VARIABLE, "field:product_id"),
        (AuthorityClass.SOURCE_REFERENCE, "dataset:orders"),
    ],
)
def test_unregistered_proposition_context_authority_fails_closed(
    authority_class: AuthorityClass,
    authority_ref: str,
) -> None:
    proposition = _proposition()
    assessments = _all_assessments(proposition)
    registry = _authority_registry(proposition, assessments)
    filtered = tuple(
        item
        for item in registry.authorities
        if not (
            item.authority_class is authority_class
            and item.binding.authority_ref == authority_ref
        )
    )
    with pytest.raises(GovernanceAuthenticationError, match="unregistered_authority"):
        _run(
            proposition=proposition,
            assessments=assessments,
            authority_registry=_registry_from_records(filtered),
        )


def test_stale_metric_definition_version_fails_closed() -> None:
    proposition = _proposition(
        outcome_ref="metric:revenue_change@stale",
        metric_refs=("metric:revenue_change@stale",),
    )
    candidate = _candidate()
    slots = tuple(
        CandidateSlot(slot=item.slot, value=proposition.outcome_ref)
        if item.slot == "outcome_ref"
        else item
        for item in candidate.structured_slot_values
    )
    with pytest.raises(GovernanceAuthenticationError, match="stale_metric_authority"):
        _run(
            proposition=proposition,
            candidate=_candidate(slots=slots),
            assessments=(),
        )


@pytest.mark.parametrize(
    ("slot", "value", "code"),
    [
        ("scope_ref", "scope:wrong", "scope_mismatch"),
        ("baseline_period_ref", "period:wrong", "period_mismatch"),
        ("comparison_population_ref", "population:wrong", "population_mismatch"),
        (
            "outcome_ref",
            f"metric:orders@{METRIC_DEFINITION_VERSION}",
            "metric_mismatch",
        ),
    ],
)
def test_exact_candidate_context_mismatch_fails_authentication(
    slot: str,
    value: str,
    code: str,
) -> None:
    candidate = _candidate()
    slots = tuple(
        CandidateSlot(slot=item.slot, value=value) if item.slot == slot else item
        for item in candidate.structured_slot_values
    )
    with pytest.raises(GovernanceAuthenticationError, match=code):
        _run(candidate=_candidate(slots=slots), assessments=())


def test_metric_reference_mismatch_fails_authentication() -> None:
    proposition = _proposition(
        metric_refs=(f"metric:orders@{METRIC_DEFINITION_VERSION}",)
    )
    with pytest.raises(GovernanceAuthenticationError, match="metric_mismatch"):
        _run(proposition=proposition, assessments=())


def test_template_silent_dimension_omission_still_fails() -> None:
    template = MVP_FAMILY_REGISTRY.get_requirement_template("product_composition_association")
    data = template.model_dump(mode="python")
    data["dimension_requirements"] = data["dimension_requirements"][:-1]
    data["template_fingerprint"] = requirement_template_semantic_fingerprint(data)
    with pytest.raises(ValidationError):
        HypothesisFamilyRequirementTemplate(**data)


def test_unapproved_conditional_dimension_rule_fails_closed() -> None:
    template = MVP_FAMILY_REGISTRY.get_requirement_template("product_composition_association")
    data = template.model_dump(mode="python")
    requirements = list(template.dimension_requirements)
    relevance = requirements[0]
    requirements[0] = DimensionRequirement(
        dimension=relevance.dimension,
        applicability=ApplicabilityState.CONDITIONAL,
        applicability_level=relevance.applicability_level,
        requirement_ref=relevance.requirement_ref,
        applicability_condition_ref="R3:unapproved_condition",
        controlling_authority_refs=relevance.controlling_authority_refs,
        failure_consequence=relevance.failure_consequence,
    )
    data["dimension_requirements"] = tuple(requirements)
    data["template_fingerprint"] = requirement_template_semantic_fingerprint(data)
    changed = HypothesisFamilyRequirementTemplate(**data)
    with pytest.raises(GovernanceAuthenticationError, match="conditional_applicability_unresolved"):
        resolve_dimension_applicability(changed, _proposition())


def test_required_template_dimension_cannot_become_not_applicable() -> None:
    result = _run()
    template = MVP_FAMILY_REGISTRY.get_requirement_template("product_composition_association")
    data = result.resolved_profile.model_dump(mode="python")
    decisions = list(result.resolved_profile.dimension_applicability_decisions)
    required = decisions[0]
    decisions[0] = DimensionRequirement(
        dimension=required.dimension,
        applicability=ApplicabilityState.NOT_APPLICABLE,
        applicability_level=required.applicability_level,
        governed_reason="attempted waiver",
    )
    data["dimension_applicability_decisions"] = tuple(decisions)
    data["profile_fingerprint"] = resolved_profile_semantic_fingerprint(data)
    data["profile_id"] = stable_content_id("reqprof", data["profile_fingerprint"])
    profile = ResolvedRequiredEvidenceProfile(**data)
    with pytest.raises(ValueError, match="cannot weaken REQUIRED"):
        validate_profile_against_template(profile, template)


def test_descriptive_admissible_evidence_is_not_diagnostic_admission() -> None:
    proposition = _proposition()
    assessments = list(_all_assessments(proposition))
    first = assessments[0]
    assessments[0] = _assessment(
        proposition,
        first.requirement_ref,
        first.dependency_classification,
        origin=EvidenceOrigin.DESCRIPTIVE_ADMISSIBLE_EVIDENCE,
        admission_state=DiagnosticAdmissionState.DESCRIPTIVE_ONLY,
    )
    result = _run(proposition=proposition, assessments=tuple(assessments))
    judgment = next(item for item in result.requirement_judgments if item.requirement_ref == first.requirement_ref)
    assert judgment.outcome.value == "PRESENT_BUT_INADMISSIBLE"
    assert result.derived_disposition is PreTestDisposition.MISSING_EVIDENCE


def test_present_but_inadmissible_evidence_remains_distinct_from_missing() -> None:
    proposition = _proposition()
    assessments = list(_all_assessments(proposition))
    first = assessments[0]
    assessments[0] = _assessment(
        proposition,
        first.requirement_ref,
        first.dependency_classification,
        admission_state=DiagnosticAdmissionState.INADMISSIBLE,
    )
    result = _run(proposition=proposition, assessments=tuple(assessments))
    judgment = next(item for item in result.requirement_judgments if item.requirement_ref == first.requirement_ref)
    assert judgment.outcome.value == "PRESENT_BUT_INADMISSIBLE"
    assert judgment.evidence_refs


def test_fitness_failure_precedes_inadmissibility_for_same_evidence() -> None:
    proposition = _proposition()
    assessments = list(_all_assessments(proposition))
    target = assessments[0]
    assessments[0] = _assessment(
        proposition,
        target.requirement_ref,
        target.dependency_classification,
        admission_state=DiagnosticAdmissionState.INADMISSIBLE,
        fitness_state=EvidenceFitnessState.FAILED,
        failure_reason="governed fitness failure",
    )
    result = _run(proposition=proposition, assessments=tuple(assessments))
    judgment = next(
        item
        for item in result.requirement_judgments
        if item.requirement_ref == target.requirement_ref
    )
    assert judgment.outcome.value == "FAILED"
    assert judgment.reason_code == "evidence_fitness_failed"
    assert result.evaluation.first_controlling_blocker.startswith(
        "evidence_fitness_failed:"
    )


def test_fitness_failure_precedes_later_missing_state_under_permutation() -> None:
    proposition = _proposition()
    assessments = list(_all_assessments(proposition))
    failed = assessments[0]
    missing = assessments[1]
    assessments[0] = _assessment(
        proposition,
        failed.requirement_ref,
        failed.dependency_classification,
        fitness_state=EvidenceFitnessState.FAILED,
        failure_reason="governed fitness failure",
    )
    assessments[1] = _assessment(
        proposition,
        missing.requirement_ref,
        missing.dependency_classification,
        availability=EvidenceAvailability.MISSING,
    )
    first = _run(proposition=proposition, assessments=tuple(assessments))
    second = _run(
        proposition=proposition,
        assessments=tuple(reversed(assessments)),
    )
    assert first == second
    assert first.evaluation.first_controlling_blocker.startswith(
        "evidence_fitness_failed:"
    )


def test_stale_evidence_authority_is_integrity_failure_not_missing() -> None:
    proposition = _proposition()
    assessments = list(_all_assessments(proposition))
    assessments[0] = assessments[0].model_copy(update={"scope_ref": "scope:stale"})
    with pytest.raises(GovernanceAuthenticationError, match="stale_or_tampered_evidence_authority"):
        _run(proposition=proposition, assessments=tuple(assessments))


def test_unregistered_diagnostic_admission_authority_fails_closed() -> None:
    proposition = _proposition()
    trusted = _all_assessments(proposition)
    supplied = list(trusted)
    target = supplied[0]
    supplied[0] = _assessment(
        proposition,
        target.requirement_ref,
        target.dependency_classification,
        diagnostic_admission_authority=_authority("diagnostic-admission:unregistered"),
    )
    with pytest.raises(GovernanceAuthenticationError, match="unregistered_authority"):
        _run(
            proposition=proposition,
            assessments=tuple(supplied),
            authority_registry=_authority_registry(proposition, trusted),
        )


def test_self_consistent_but_untrusted_assessment_authority_fails_closed() -> None:
    proposition = _proposition()
    trusted = _all_assessments(proposition)
    supplied = list(trusted)
    target = supplied[0]
    supplied[0] = _assessment(
        proposition,
        target.requirement_ref,
        target.dependency_classification,
        authority_bindings=(_authority("assessment-authority:untrusted"),),
    )
    with pytest.raises(GovernanceAuthenticationError, match="unregistered_authority"):
        _run(
            proposition=proposition,
            assessments=tuple(supplied),
            authority_registry=_authority_registry(proposition, trusted),
        )


def test_stale_diagnostic_admission_version_fails_closed() -> None:
    proposition = _proposition()
    trusted = _all_assessments(proposition)
    supplied = list(trusted)
    target = supplied[0]
    current = target.diagnostic_admission_authority
    assert current is not None
    supplied[0] = _assessment(
        proposition,
        target.requirement_ref,
        target.dependency_classification,
        diagnostic_admission_authority=current.model_copy(
            update={"authority_version": "0.9.0"}
        ),
    )
    with pytest.raises(GovernanceAuthenticationError, match="stale_or_untrusted_authority"):
        _run(
            proposition=proposition,
            assessments=tuple(supplied),
            authority_registry=_authority_registry(proposition, trusted),
        )


def test_equal_looking_admission_for_another_requirement_is_rejected() -> None:
    proposition = _proposition()
    trusted = _all_assessments(proposition)
    supplied = list(trusted)
    target = supplied[0]
    substitute = supplied[1].diagnostic_admission_authority
    assert substitute is not None
    supplied[0] = _assessment(
        proposition,
        target.requirement_ref,
        target.dependency_classification,
        diagnostic_admission_authority=substitute,
    )
    with pytest.raises(GovernanceAuthenticationError, match="authority_subject_substitution"):
        _run(
            proposition=proposition,
            assessments=tuple(supplied),
            authority_registry=_authority_registry(proposition, trusted),
        )


def test_r4_mechanical_result_cannot_be_used_as_diagnostic_support() -> None:
    proposition = _proposition(source_mechanical_result_refs=("r4:decomposition",))
    assessments = list(_all_assessments(proposition))
    first = assessments[0]
    assessments[0] = _assessment(
        proposition,
        first.requirement_ref,
        first.dependency_classification,
        origin=EvidenceOrigin.R4_MECHANICAL_RESULT,
        evidence_refs=("r4:decomposition",),
    )
    result = _run(proposition=proposition, assessments=tuple(assessments))
    judgment = next(item for item in result.requirement_judgments if item.requirement_ref == first.requirement_ref)
    assert judgment.reason_code == "r4_mechanical_result_not_diagnostic_support"


@pytest.mark.parametrize("substitute", ["field:unit_price", "field:line_revenue", "metric:AOV"])
def test_forbidden_discount_substitute_fails_representability(substitute: str) -> None:
    candidate = _candidate("discounting_association")
    slots = tuple(
        CandidateSlot(slot=item.slot, value=substitute)
        if item.slot == "original_or_list_price_ref"
        else item
        for item in candidate.structured_slot_values
    )
    with pytest.raises(GovernanceAuthenticationError, match="proposition_not_representable"):
        _run(
            "discounting_association",
            proposition=_proposition("discounting_association"),
            candidate=_candidate("discounting_association", slots=slots),
            assessments=(),
        )


def test_external_family_without_explicit_activation_fails_closed() -> None:
    candidate = _candidate("external_market_association")
    slots = tuple(
        CandidateSlot(slot=item.slot, value=None) if item.slot == "explicit_activation_ref" else item
        for item in candidate.structured_slot_values
    )
    with pytest.raises(GovernanceAuthenticationError, match="proposition_not_representable"):
        _run(
            "external_market_association",
            proposition=_proposition("external_market_association"),
            candidate=_candidate("external_market_association", slots=slots),
            assessments=(),
        )


def test_external_model_general_knowledge_is_present_but_inadmissible() -> None:
    proposition = _proposition("external_market_association")
    assessments = list(_all_assessments(proposition))
    dependency = MVP_FAMILY_REGISTRY.get_requirement_template(
        proposition.family_id
    ).dependency_source_classifications[0]
    assessments = [
        item for item in assessments if item.requirement_ref != dependency.requirement_ref
    ]
    assessments.append(
        _assessment(
            proposition,
            dependency.requirement_ref,
            DependencyClassification.EXTERNAL,
            origin=EvidenceOrigin.MODEL_GENERAL_KNOWLEDGE,
        )
    )
    result = _run(
        "external_market_association",
        proposition=proposition,
        assessments=tuple(assessments),
    )
    judgment = next(
        item for item in result.requirement_judgments if item.requirement_ref == dependency.requirement_ref
    )
    assert judgment.reason_code == "model_general_knowledge_not_evidence"
    assert result.derived_disposition is PreTestDisposition.EXTERNAL_EVIDENCE_REQUIRED


def test_valid_method_authority_is_bound_without_implying_execution_or_support() -> None:
    method = _authority("method:bounded-association-v1")
    result = _run(proposed_method_refs=(method,))
    assert result.resolved_profile.method_requirement_refs == (
        method.model_dump_json(),
    )
    assert result.derived_disposition is PreTestDisposition.HYPOTHESIS_ONLY
    assert result.evaluation.test_eligibility is DiagnosticTestEligibility.NOT_ELIGIBLE
    assert result.evaluation.analytical_outcome is AnalyticalOutcome.NOT_EVALUATED
    assert (
        result.evaluation.first_controlling_blocker
        == "method_execution_authority_unavailable"
    )


def test_unknown_method_authority_fails_closed() -> None:
    proposition = _proposition()
    assessments = _all_assessments(proposition)
    method = _authority("method:unregistered")
    with pytest.raises(GovernanceAuthenticationError, match="unregistered_authority"):
        _run(
            proposition=proposition,
            assessments=assessments,
            proposed_method_refs=(method,),
            authority_registry=_authority_registry(proposition, assessments),
        )


def test_stale_method_authority_fails_closed() -> None:
    proposition = _proposition()
    assessments = _all_assessments(proposition)
    current = _authority("method:bounded-association-v1")
    stale = current.model_copy(update={"authority_version": "0.9.0"})
    with pytest.raises(GovernanceAuthenticationError, match="stale_or_untrusted_authority"):
        _run(
            proposition=proposition,
            assessments=assessments,
            proposed_method_refs=(stale,),
            authority_registry=_authority_registry(
                proposition,
                assessments,
                methods=(current,),
            ),
        )


def test_later_method_claim_cannot_override_earlier_evidence_blocker() -> None:
    proposition = _proposition()
    assessments = _all_assessments(proposition)
    result = _run(
        proposition=proposition,
        assessments=assessments[1:],
        proposed_method_refs=(_authority("method:claimed-ready"),),
    )
    assert result.derived_disposition is PreTestDisposition.MISSING_EVIDENCE
    assert "method" not in result.evaluation.first_controlling_blocker
    assert result.resolved_profile.method_requirement_refs


def test_claim_class_restriction_precedes_evidence_and_method_states() -> None:
    proposition = _proposition()
    result = _run(
        proposition=proposition,
        assessments=(),
        requested_claim_type=ClaimType.CAUSAL,
        proposed_method_refs=(_authority("method:claimed-ready"),),
    )
    assert result.derived_disposition is PreTestDisposition.CLARIFICATION_REQUIRED
    assert result.evaluation.first_controlling_blocker == "claim_class_restricted"


def test_claim_class_restriction_precedes_later_scope_mismatch() -> None:
    proposition = _proposition()
    candidate = _candidate()
    slots = tuple(
        CandidateSlot(slot=item.slot, value="scope:wrong")
        if item.slot == "scope_ref"
        else item
        for item in candidate.structured_slot_values
    )
    result = _run(
        proposition=proposition,
        candidate=_candidate(slots=slots),
        assessments=(),
        requested_claim_type=ClaimType.CAUSAL,
    )
    assert result.derived_disposition is PreTestDisposition.CLARIFICATION_REQUIRED
    assert result.evaluation.first_controlling_blocker == "claim_class_restricted"
    scope_binding = next(
        binding
        for binding in result.resolved_profile.exact_slot_bindings
        if binding.slot == "scope_ref"
    )
    assert scope_binding.bound_ref == proposition.scope_ref


def test_internal_evidence_defect_precedes_authenticated_conflict() -> None:
    proposition = _proposition()
    conflict_data: dict[str, object] = {
        "conflict_id": "pending",
        "diagnostic_proposition_ref": proposition.proposition_id,
        "diagnostic_proposition_fingerprint": proposition.semantic_fingerprint,
        "unresolved_material_conflict": True,
        "evidence_refs": ("evidence:a", "evidence:b"),
        "authority_bindings": (_authority("conflict:evaluator"),),
    }
    conflict_data["conflict_fingerprint"] = evidence_conflict_assessment_fingerprint(conflict_data)
    conflict_data["conflict_id"] = stable_content_id("evconf", conflict_data["conflict_fingerprint"])
    conflict = EvidenceConflictAssessment(**conflict_data)
    result = _run(proposition=proposition, assessments=(), conflict_assessment=conflict)
    assert result.derived_disposition is PreTestDisposition.MISSING_EVIDENCE


def test_semantically_unordered_inputs_produce_identical_result() -> None:
    proposition = _proposition()
    candidate = _candidate()
    assessments = _all_assessments(proposition)
    methods = (
        _authority("method:bounded-association-v1"),
        _authority("method:robustness-check-v1"),
    )
    registry = _authority_registry(
        proposition,
        assessments,
        methods=methods,
    )
    reversed_registry = _registry_from_records(
        tuple(reversed(registry.authorities))
    )
    first = _run(
        proposition=proposition,
        candidate=candidate,
        assessments=assessments,
        proposed_method_refs=methods,
        authority_registry=registry,
    )
    second = _run(
        proposition=proposition,
        candidate=_candidate(slots=tuple(reversed(candidate.structured_slot_values))),
        assessments=tuple(reversed(assessments)),
        proposed_method_refs=tuple(reversed(methods)),
        authority_registry=reversed_registry,
    )
    assert first == second
