"""Deterministic R6-2 authority authentication and pre-test governance."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Self

from pydantic import Field, model_validator

from commerce_lens.contracts.common import ClaimType, ContractBase
from commerce_lens.contracts.diagnostic import (
    AlternativeExplanationState,
    AnalyticalOutcome,
    AuthorityBinding,
    DiagnosticProposition,
    EvidenceReadiness,
    PreTestDiagnosticEvaluation,
    TestEligibility,
    pretest_evaluation_semantic_fingerprint,
)
from commerce_lens.contracts.hypotheses import (
    CandidateProposal,
    CandidateSlot,
    FamilyClassification,
    HypothesisFamilyDefinition,
)
from commerce_lens.contracts.required_evidence import (
    ApplicabilityState,
    DependencyClassification,
    DimensionRequirement,
    EvidenceDimension,
    EvidenceRole,
    HypothesisFamilyRequirementTemplate,
    RequirementConsequence,
    RequirementJudgment,
    RequirementOutcome,
    ResolvedRequiredEvidenceProfile,
    SlotBinding,
    resolved_profile_semantic_fingerprint,
    validate_profile_against_template,
)
from commerce_lens.diagnostic.family_registry import MVP_FAMILY_REGISTRY
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, stable_content_id
from commerce_lens.metrics.registry import get_metric_registry


GOVERNANCE_VERSION = "1.0.0"
PROFILE_VERSION = "1.0.0"
PROFILE_SCHEMA_VERSION = "1.0.0"
EVALUATION_SCHEMA_VERSION = "1.0.0"
SHA256_PATTERN = r"^[0-9a-f]{64}$"


class GovernanceAuthenticationError(ValueError):
    """Fail-closed integrity or exact-authority mismatch."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class EvidenceAvailability(str, Enum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"
    UNRESOLVED = "UNRESOLVED"


class DiagnosticAdmissionState(str, Enum):
    DIAGNOSTIC_ADMITTED = "DIAGNOSTIC_ADMITTED"
    DESCRIPTIVE_ONLY = "DESCRIPTIVE_ONLY"
    INADMISSIBLE = "INADMISSIBLE"
    UNRESOLVED = "UNRESOLVED"


class EvidenceFitnessState(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    UNRESOLVED = "UNRESOLVED"


class EvidenceOrigin(str, Enum):
    GOVERNED_INTERNAL = "GOVERNED_INTERNAL"
    GOVERNED_EXTERNAL = "GOVERNED_EXTERNAL"
    DESCRIPTIVE_ADMISSIBLE_EVIDENCE = "DESCRIPTIVE_ADMISSIBLE_EVIDENCE"
    R4_MECHANICAL_RESULT = "R4_MECHANICAL_RESULT"
    MODEL_GENERAL_KNOWLEDGE = "MODEL_GENERAL_KNOWLEDGE"


class PreTestDisposition(str, Enum):
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    HYPOTHESIS_ONLY = "HYPOTHESIS_ONLY"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    EXTERNAL_EVIDENCE_REQUIRED = "EXTERNAL_EVIDENCE_REQUIRED"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"


class RequirementEvidenceAssessment(ContractBase):
    """Authenticated input view; it does not itself admit or create Evidence."""

    assessment_id: str = Field(min_length=1)
    assessment_version: str = GOVERNANCE_VERSION
    assessment_fingerprint: str = Field(pattern=SHA256_PATTERN)
    requirement_ref: str = Field(min_length=1)
    availability: EvidenceAvailability
    admission_state: DiagnosticAdmissionState
    fitness_state: EvidenceFitnessState
    origin: EvidenceOrigin
    dependency_classification: DependencyClassification
    evidence_refs: tuple[str, ...] = ()
    diagnostic_proposition_ref: str = Field(min_length=1)
    diagnostic_proposition_fingerprint: str = Field(pattern=SHA256_PATTERN)
    scope_ref: str = Field(min_length=1)
    baseline_period_ref: str = Field(min_length=1)
    comparison_period_ref: str = Field(min_length=1)
    baseline_population_ref: str = Field(min_length=1)
    comparison_population_ref: str = Field(min_length=1)
    metric_refs: tuple[str, ...] = ()
    variable_refs: tuple[str, ...] = Field(min_length=1)
    source_observation_refs: tuple[str, ...] = Field(min_length=1)
    authority_bindings: tuple[AuthorityBinding, ...] = Field(min_length=1)
    diagnostic_admission_authority: AuthorityBinding | None = None
    failure_reason: str | None = None

    @model_validator(mode="after")
    def validate_assessment(self) -> Self:
        if self.availability is EvidenceAvailability.PRESENT:
            if not self.evidence_refs:
                raise ValueError("present evidence assessment requires evidence_refs")
        elif self.evidence_refs:
            raise ValueError("non-present evidence assessment cannot carry evidence_refs")
        if self.availability is not EvidenceAvailability.PRESENT:
            if self.admission_state is not DiagnosticAdmissionState.UNRESOLVED:
                raise ValueError("non-present evidence cannot carry an admission decision")
        if self.admission_state is DiagnosticAdmissionState.DIAGNOSTIC_ADMITTED:
            if self.diagnostic_admission_authority is None:
                raise ValueError("diagnostic admission requires exact admission authority")
        if self.fitness_state is EvidenceFitnessState.FAILED and not self.failure_reason:
            raise ValueError("failed evidence fitness requires a reason")
        expected = requirement_evidence_assessment_fingerprint(self)
        if self.assessment_fingerprint != expected:
            raise ValueError("assessment_fingerprint does not match requirement evidence authority")
        if self.assessment_id != stable_content_id("reqevid", expected):
            raise ValueError("assessment_id must be the stable ID for requirement evidence authority")
        return self


class EvidenceConflictAssessment(ContractBase):
    conflict_id: str = Field(min_length=1)
    conflict_fingerprint: str = Field(pattern=SHA256_PATTERN)
    diagnostic_proposition_ref: str = Field(min_length=1)
    diagnostic_proposition_fingerprint: str = Field(pattern=SHA256_PATTERN)
    unresolved_material_conflict: bool
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    authority_bindings: tuple[AuthorityBinding, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_conflict(self) -> Self:
        expected = evidence_conflict_assessment_fingerprint(self)
        if self.conflict_fingerprint != expected:
            raise ValueError("conflict_fingerprint does not match conflict authority")
        if self.conflict_id != stable_content_id("evconf", expected):
            raise ValueError("conflict_id must be the stable ID for conflict authority")
        return self


class PreTestGovernanceResult(ContractBase):
    resolved_profile: ResolvedRequiredEvidenceProfile
    requirement_judgments: tuple[RequirementJudgment, ...] = Field(min_length=1)
    requirement_judgment_bundle_ref: str = Field(min_length=1)
    requirement_judgment_bundle_fingerprint: str = Field(pattern=SHA256_PATTERN)
    evaluation: PreTestDiagnosticEvaluation
    derived_disposition: PreTestDisposition


def govern_pretest(
    proposition: DiagnosticProposition,
    candidate: CandidateProposal,
    template_binding: AuthorityBinding | None,
    evidence_assessments: tuple[RequirementEvidenceAssessment, ...],
    *,
    finalized_at: datetime,
    requested_claim_type: ClaimType = ClaimType.DIAGNOSTIC,
    conflict_assessment: EvidenceConflictAssessment | None = None,
    proposed_method_refs: tuple[str, ...] = (),
) -> PreTestGovernanceResult:
    """Authenticate exact R2/R3 authority and derive immutable pre-test state."""

    proposition = _authenticate_proposition(proposition)
    family, template = _authenticate_family_and_template(proposition, template_binding)
    slot_bindings = _authenticate_exact_binding(proposition, candidate, family.required_proposition_slots)
    decisions = resolve_dimension_applicability(template, proposition)
    profile = _build_profile(proposition, template, slot_bindings, decisions)
    assessments = _authenticate_assessments(proposition, template, evidence_assessments)
    judgments = _build_judgments(family, template, decisions, assessments)

    if conflict_assessment is not None:
        _authenticate_conflict(proposition, conflict_assessment)

    disposition, readiness, blocker = _derive_first_blocker(
        requested_claim_type=requested_claim_type,
        judgments=judgments,
        conflict_assessment=conflict_assessment,
        proposed_method_refs=proposed_method_refs,
    )
    bundle_fingerprint = requirement_judgment_bundle_fingerprint(judgments)
    bundle_ref = stable_content_id("reqbundle", bundle_fingerprint)
    evaluation = _build_evaluation(
        proposition=proposition,
        profile=profile,
        bundle_ref=bundle_ref,
        bundle_fingerprint=bundle_fingerprint,
        readiness=readiness,
        blocker=blocker,
        finalized_at=finalized_at,
    )
    return PreTestGovernanceResult(
        resolved_profile=profile,
        requirement_judgments=judgments,
        requirement_judgment_bundle_ref=bundle_ref,
        requirement_judgment_bundle_fingerprint=bundle_fingerprint,
        evaluation=evaluation,
        derived_disposition=disposition,
    )


def resolve_dimension_applicability(
    template: HypothesisFamilyRequirementTemplate,
    proposition: DiagnosticProposition,
) -> tuple[DimensionRequirement, ...]:
    """Resolve every template conditional against exact proposition semantics."""

    metric_ids = _authenticated_metric_ids(proposition.metric_refs)
    decisions: list[DimensionRequirement] = []
    for requirement in template.dimension_requirements:
        if requirement.applicability is ApplicabilityState.REQUIRED:
            decisions.append(requirement)
            continue
        if requirement.applicability is ApplicabilityState.NOT_APPLICABLE:
            decisions.append(requirement)
            continue
        if requirement.dimension is EvidenceDimension.METRIC_COMPATIBILITY:
            applicable = bool(metric_ids)
            reason = "exact proposition contains no governed Metric or Metric-derived construct"
        elif requirement.dimension is EvidenceDimension.UNIT_CURRENCY_COMPATIBILITY:
            applicable = bool(metric_ids) or EvidenceRole.UNIT_CURRENCY in template.required_evidence_roles
            reason = "exact proposition contains no material unit-bearing or monetary evidence role"
        else:
            raise GovernanceAuthenticationError(
                "conditional_applicability_unresolved",
                f"no approved exact-binding rule for {requirement.dimension.value}",
            )
        if applicable:
            decisions.append(
                DimensionRequirement(
                    dimension=requirement.dimension,
                    applicability=ApplicabilityState.REQUIRED,
                    applicability_level=requirement.applicability_level,
                    requirement_ref=requirement.requirement_ref,
                    controlling_authority_refs=(
                        *requirement.controlling_authority_refs,
                        proposition.proposition_id,
                    ),
                    failure_consequence=requirement.failure_consequence,
                )
            )
        else:
            decisions.append(
                DimensionRequirement(
                    dimension=requirement.dimension,
                    applicability=ApplicabilityState.NOT_APPLICABLE,
                    applicability_level=requirement.applicability_level,
                    controlling_authority_refs=(
                        *requirement.controlling_authority_refs,
                        proposition.proposition_id,
                    ),
                    governed_reason=reason,
                )
            )
    return tuple(decisions)


def requirement_evidence_assessment_fingerprint(
    assessment: RequirementEvidenceAssessment | Mapping[str, Any],
) -> str:
    data = _data(assessment)
    payload = {
        "assessment_version": data.get("assessment_version", GOVERNANCE_VERSION),
        "requirement_ref": data["requirement_ref"],
        "availability": _enum(data["availability"]),
        "admission_state": _enum(data["admission_state"]),
        "fitness_state": _enum(data["fitness_state"]),
        "origin": _enum(data["origin"]),
        "dependency_classification": _enum(data["dependency_classification"]),
        "evidence_refs": sorted(data.get("evidence_refs", ())),
        "diagnostic_proposition_ref": data["diagnostic_proposition_ref"],
        "diagnostic_proposition_fingerprint": data["diagnostic_proposition_fingerprint"],
        "scope_ref": data["scope_ref"],
        "baseline_period_ref": data["baseline_period_ref"],
        "comparison_period_ref": data["comparison_period_ref"],
        "baseline_population_ref": data["baseline_population_ref"],
        "comparison_population_ref": data["comparison_population_ref"],
        "metric_refs": sorted(data.get("metric_refs", ())),
        "variable_refs": sorted(data["variable_refs"]),
        "source_observation_refs": sorted(data["source_observation_refs"]),
        "authority_bindings": _sorted_authority_bindings(data["authority_bindings"]),
        "diagnostic_admission_authority": _json(data.get("diagnostic_admission_authority")),
        "failure_reason": data.get("failure_reason"),
    }
    return canonical_json_fingerprint(payload)


def evidence_conflict_assessment_fingerprint(
    assessment: EvidenceConflictAssessment | Mapping[str, Any],
) -> str:
    data = _data(assessment)
    return canonical_json_fingerprint(
        {
            "diagnostic_proposition_ref": data["diagnostic_proposition_ref"],
            "diagnostic_proposition_fingerprint": data["diagnostic_proposition_fingerprint"],
            "unresolved_material_conflict": data["unresolved_material_conflict"],
            "evidence_refs": sorted(data["evidence_refs"]),
            "authority_bindings": _sorted_authority_bindings(data["authority_bindings"]),
        }
    )


def requirement_judgment_bundle_fingerprint(
    judgments: tuple[RequirementJudgment, ...],
) -> str:
    payload = sorted(
        (judgment.model_dump(mode="json") for judgment in judgments),
        key=lambda item: item["requirement_ref"],
    )
    return canonical_json_fingerprint(payload)


def _authenticate_proposition(proposition: DiagnosticProposition) -> DiagnosticProposition:
    try:
        authenticated = DiagnosticProposition.model_validate(proposition.model_dump(mode="python"))
    except ValueError as exc:
        raise GovernanceAuthenticationError(
            "proposition_authentication_failed",
            "DiagnosticProposition identity or semantic fingerprint is invalid",
        ) from exc
    bindings = [
        (binding.authority_ref, binding.authority_version, binding.authority_fingerprint)
        for binding in authenticated.authority_bindings
    ]
    if len(bindings) != len(set(bindings)):
        raise GovernanceAuthenticationError(
            "proposition_authority_binding_duplicate",
            "DiagnosticProposition authority bindings must be unique",
        )
    return authenticated


def _authenticate_family_and_template(
    proposition: DiagnosticProposition,
    template_binding: AuthorityBinding | None,
) -> tuple[Any, HypothesisFamilyRequirementTemplate]:
    try:
        family = MVP_FAMILY_REGISTRY.get_family(proposition.family_id, proposition.family_version)
    except ValueError as exc:
        code = "unknown_family" if "unknown" in str(exc) else "wrong_family_version"
        raise GovernanceAuthenticationError(code, str(exc)) from exc
    if proposition.family_fingerprint != family.family_fingerprint:
        raise GovernanceAuthenticationError(
            "wrong_family_fingerprint",
            "DiagnosticProposition family fingerprint does not match approved registry authority",
        )
    template = MVP_FAMILY_REGISTRY.get_requirement_template(proposition.family_id)
    if template_binding is None:
        raise GovernanceAuthenticationError("missing_template_authority", "exact template binding is required")
    if (
        template_binding.authority_ref != template.template_id
        or template_binding.authority_version != template.template_version
        or template_binding.authority_fingerprint != template.template_fingerprint
    ):
        raise GovernanceAuthenticationError(
            "template_authority_mismatch",
            "template ID, version, or fingerprint does not match approved static registry",
        )
    return family, template


def _authenticate_exact_binding(
    proposition: DiagnosticProposition,
    candidate: CandidateProposal,
    required_slots: tuple[str, ...],
) -> tuple[SlotBinding, ...]:
    if candidate.family_id != proposition.family_id or candidate.family_version != proposition.family_version:
        raise GovernanceAuthenticationError(
            "candidate_family_mismatch",
            "candidate family authority does not match DiagnosticProposition",
        )
    try:
        MVP_FAMILY_REGISTRY.validate_candidate(candidate)
    except ValueError as exc:
        raise GovernanceAuthenticationError("proposition_not_representable", str(exc)) from exc

    values = {item.slot: item.value for item in candidate.structured_slot_values}
    expected_common: dict[str, Any] = {
        "outcome_ref": proposition.outcome_ref,
        "baseline_period_ref": proposition.baseline_period_ref,
        "comparison_period_ref": proposition.comparison_period_ref,
        "baseline_population_ref": proposition.baseline_population_ref,
        "comparison_population_ref": proposition.comparison_population_ref,
        "scope_ref": proposition.scope_ref,
        "source_observation_refs": proposition.source_observation_refs,
    }
    mismatch_codes = {
        "outcome_ref": "metric_mismatch",
        "scope_ref": "scope_mismatch",
        "baseline_period_ref": "period_mismatch",
        "comparison_period_ref": "period_mismatch",
        "baseline_population_ref": "population_mismatch",
        "comparison_population_ref": "population_mismatch",
        "source_observation_refs": "source_authority_mismatch",
    }
    for slot, expected in expected_common.items():
        if slot in values and not _equivalent_slot_value(values[slot], expected):
            raise GovernanceAuthenticationError(mismatch_codes[slot], f"candidate {slot} mismatches proposition")

    if set(proposition.metric_refs) != {proposition.outcome_ref}:
        raise GovernanceAuthenticationError(
            "metric_mismatch",
            "exact proposition outcome must match its sole governed Metric reference",
        )
    metric_ids = _authenticated_metric_ids(proposition.metric_refs)
    if metric_ids != ("revenue_change",):
        raise GovernanceAuthenticationError(
            "metric_mismatch",
            "approved R6 MVP families require authenticated Revenue Change outcome",
        )

    variable_slots = {
        "product_identity_ref",
        "monetary_observation_ref",
        "original_or_list_price_ref",
        "discount_semantics_ref",
        "external_factor_ref",
    }
    for slot in variable_slots & values.keys():
        if str(values[slot]) not in proposition.variable_refs:
            raise GovernanceAuthenticationError(
                "variable_mismatch",
                f"candidate {slot} is not bound to an exact proposition variable",
            )
    if "external_evidence_dependency_ref" in values:
        if str(values["external_evidence_dependency_ref"]) not in proposition.source_observation_refs:
            raise GovernanceAuthenticationError(
                "source_authority_mismatch",
                "external evidence dependency is not an exact proposition source",
            )
    if "explicit_activation_ref" in values:
        activation_ref = str(values["explicit_activation_ref"])
        if activation_ref not in {binding.authority_ref for binding in proposition.authority_bindings}:
            raise GovernanceAuthenticationError(
                "external_activation_missing",
                "external-family activation is not authenticated by proposition authority",
            )
    if "optional_r4_result_ref" in values:
        r4_ref = str(values["optional_r4_result_ref"])
        if r4_ref not in proposition.source_mechanical_result_refs:
            raise GovernanceAuthenticationError(
                "mechanical_result_mismatch",
                "optional R4 result is not bound to the exact proposition",
            )

    missing = set(required_slots) - set(values)
    if missing:
        raise GovernanceAuthenticationError(
            "proposition_not_representable",
            "missing exact proposition slots: " + ", ".join(sorted(missing)),
        )
    return tuple(
        SlotBinding(slot=slot, bound_ref=_slot_binding_ref(values[slot]))
        for slot in sorted(values)
    )


def _build_profile(
    proposition: DiagnosticProposition,
    template: HypothesisFamilyRequirementTemplate,
    slot_bindings: tuple[SlotBinding, ...],
    decisions: tuple[DimensionRequirement, ...],
) -> ResolvedRequiredEvidenceProfile:
    data: dict[str, Any] = {
        "profile_id": "pending",
        "profile_version": PROFILE_VERSION,
        "profile_schema_version": PROFILE_SCHEMA_VERSION,
        "template_id": template.template_id,
        "template_version": template.template_version,
        "template_fingerprint": template.template_fingerprint,
        "diagnostic_proposition_ref": proposition.proposition_id,
        "diagnostic_proposition_fingerprint": proposition.semantic_fingerprint,
        "exact_slot_bindings": slot_bindings,
        "resolved_evidence_roles": template.required_evidence_roles,
        "dimension_applicability_decisions": decisions,
        "dependency_classifications": template.dependency_source_classifications,
        "measurement_classifications": template.measurement_classifications,
        "method_requirement_refs": (),
        "blocking_rules": template.known_blocking_conditions,
        "qualification_rules": (),
        "narrowing_rules": (),
    }
    fingerprint = resolved_profile_semantic_fingerprint(data)
    data["profile_fingerprint"] = fingerprint
    data["profile_id"] = stable_content_id("reqprof", fingerprint)
    profile = ResolvedRequiredEvidenceProfile(**data)
    validate_profile_against_template(profile, template)
    return profile


def _authenticate_assessments(
    proposition: DiagnosticProposition,
    template: HypothesisFamilyRequirementTemplate,
    assessments: tuple[RequirementEvidenceAssessment, ...],
) -> dict[str, RequirementEvidenceAssessment]:
    expected_classification = _expected_requirement_classifications(template)
    by_ref: dict[str, RequirementEvidenceAssessment] = {}
    for supplied in assessments:
        try:
            assessment = RequirementEvidenceAssessment.model_validate(supplied.model_dump(mode="python"))
        except ValueError as exc:
            raise GovernanceAuthenticationError(
                "stale_or_tampered_evidence_authority",
                "requirement evidence assessment failed fingerprint authentication",
            ) from exc
        if assessment.requirement_ref in by_ref:
            raise GovernanceAuthenticationError(
                "duplicate_requirement_evidence",
                f"duplicate evidence assessment for {assessment.requirement_ref}",
            )
        if assessment.requirement_ref not in expected_classification:
            raise GovernanceAuthenticationError(
                "unknown_requirement_evidence",
                f"assessment targets unknown requirement {assessment.requirement_ref}",
            )
        _authenticate_assessment_context(proposition, assessment)
        expected = expected_classification[assessment.requirement_ref]
        if assessment.dependency_classification is not expected:
            raise GovernanceAuthenticationError(
                "source_class_mismatch",
                f"assessment source class mismatches {assessment.requirement_ref}",
            )
        if expected is DependencyClassification.EXTERNAL:
            permitted = {
                EvidenceOrigin.GOVERNED_EXTERNAL,
                EvidenceOrigin.DESCRIPTIVE_ADMISSIBLE_EVIDENCE,
                EvidenceOrigin.MODEL_GENERAL_KNOWLEDGE,
            }
        else:
            permitted = {
                EvidenceOrigin.GOVERNED_INTERNAL,
                EvidenceOrigin.DESCRIPTIVE_ADMISSIBLE_EVIDENCE,
                EvidenceOrigin.R4_MECHANICAL_RESULT,
            }
        if assessment.origin not in permitted:
            raise GovernanceAuthenticationError(
                "source_class_mismatch",
                f"evidence origin mismatches {assessment.requirement_ref}",
            )
        by_ref[assessment.requirement_ref] = assessment
    return by_ref


def _authenticate_assessment_context(
    proposition: DiagnosticProposition,
    assessment: RequirementEvidenceAssessment,
) -> None:
    exact = {
        "diagnostic_proposition_ref": proposition.proposition_id,
        "diagnostic_proposition_fingerprint": proposition.semantic_fingerprint,
        "scope_ref": proposition.scope_ref,
        "baseline_period_ref": proposition.baseline_period_ref,
        "comparison_period_ref": proposition.comparison_period_ref,
        "baseline_population_ref": proposition.baseline_population_ref,
        "comparison_population_ref": proposition.comparison_population_ref,
    }
    for field, expected in exact.items():
        if getattr(assessment, field) != expected:
            code = {
                "scope_ref": "scope_mismatch",
                "baseline_period_ref": "period_mismatch",
                "comparison_period_ref": "period_mismatch",
                "baseline_population_ref": "population_mismatch",
                "comparison_population_ref": "population_mismatch",
            }.get(field, "proposition_authority_mismatch")
            raise GovernanceAuthenticationError(code, f"evidence assessment {field} mismatches proposition")
    unordered = {
        "metric_refs": proposition.metric_refs,
        "variable_refs": proposition.variable_refs,
        "source_observation_refs": proposition.source_observation_refs,
    }
    for field, expected in unordered.items():
        if set(getattr(assessment, field)) != set(expected):
            code = "metric_mismatch" if field == "metric_refs" else "proposition_authority_mismatch"
            raise GovernanceAuthenticationError(code, f"evidence assessment {field} mismatches proposition")


def _build_judgments(
    family: HypothesisFamilyDefinition,
    template: HypothesisFamilyRequirementTemplate,
    decisions: tuple[DimensionRequirement, ...],
    assessments: dict[str, RequirementEvidenceAssessment],
) -> tuple[RequirementJudgment, ...]:
    family_class = template.dependency_source_classifications[0].classification
    judgments: list[RequirementJudgment] = []
    for decision in decisions:
        if decision.applicability is ApplicabilityState.NOT_APPLICABLE:
            judgments.append(
                _judgment(
                    requirement_ref=f"{template.family_id}:{decision.dimension.value}",
                    outcome=RequirementOutcome.NOT_APPLICABLE,
                    reason_code="governed_not_applicable",
                    evidence_refs=(),
                    authority_refs=decision.controlling_authority_refs,
                    dimension=decision.dimension,
                    context=decision.governed_reason or "governed non-applicability",
                    dependency_classification=family_class,
                    consequence=RequirementConsequence.NONE,
                )
            )
            continue
        requirement_ref = decision.requirement_ref or f"{template.family_id}:{decision.dimension.value}"
        judgments.append(
            _judgment_from_assessment(
                requirement_ref=requirement_ref,
                assessment=assessments.get(requirement_ref),
                dimension=decision.dimension,
                default_classification=family_class,
                template=template,
            )
        )
    for dependency in sorted(
        template.dependency_source_classifications,
        key=lambda item: item.requirement_ref,
    ):
        assessment = assessments.get(dependency.requirement_ref)
        family_policy_blocks_satisfaction = (
            FamilyClassification.MISSING_INTERNAL_EVIDENCE_ONLY in family.classifications
            or FamilyClassification.EXTERNAL_EVIDENCE_REQUIRED in family.classifications
        )
        if (
            family_policy_blocks_satisfaction
            and assessment is not None
            and _assessment_outcome(assessment)[0] is RequirementOutcome.SATISFIED
        ):
            assessment = None
        judgments.append(
            _judgment_from_assessment(
                requirement_ref=dependency.requirement_ref,
                assessment=assessment,
                dimension=None,
                default_classification=dependency.classification,
                template=template,
            )
        )
    return tuple(sorted(judgments, key=lambda item: item.requirement_ref))


def _judgment_from_assessment(
    *,
    requirement_ref: str,
    assessment: RequirementEvidenceAssessment | None,
    dimension: EvidenceDimension | None,
    default_classification: DependencyClassification,
    template: HypothesisFamilyRequirementTemplate,
) -> RequirementJudgment:
    if assessment is None:
        outcome = (
            RequirementOutcome.EXTERNAL_UNMET
            if default_classification is DependencyClassification.EXTERNAL
            else RequirementOutcome.MISSING
        )
        reason = "external_evidence_unmet" if outcome is RequirementOutcome.EXTERNAL_UNMET else "evidence_missing"
        return _judgment(
            requirement_ref=requirement_ref,
            outcome=outcome,
            reason_code=reason,
            evidence_refs=(),
            authority_refs=(template.template_id,),
            dimension=dimension,
            context=f"exact proposition requirement {requirement_ref}",
            dependency_classification=default_classification,
            consequence=RequirementConsequence.BLOCKING,
        )

    outcome, reason = _assessment_outcome(assessment)
    authority_refs = tuple(
        sorted(
            {
                template.template_id,
                assessment.assessment_id,
                *(binding.authority_ref for binding in assessment.authority_bindings),
                *(
                    (assessment.diagnostic_admission_authority.authority_ref,)
                    if assessment.diagnostic_admission_authority is not None
                    else ()
                ),
            }
        )
    )
    return _judgment(
        requirement_ref=requirement_ref,
        outcome=outcome,
        reason_code=reason,
        evidence_refs=assessment.evidence_refs,
        authority_refs=authority_refs,
        dimension=dimension,
        context=f"exact proposition requirement {requirement_ref}",
        dependency_classification=assessment.dependency_classification,
        consequence=RequirementConsequence.BLOCKING,
    )


def _assessment_outcome(
    assessment: RequirementEvidenceAssessment,
) -> tuple[RequirementOutcome, str]:
    if assessment.availability is EvidenceAvailability.MISSING:
        if assessment.dependency_classification is DependencyClassification.EXTERNAL:
            return RequirementOutcome.EXTERNAL_UNMET, "external_evidence_unmet"
        return RequirementOutcome.MISSING, "evidence_missing"
    if assessment.availability is EvidenceAvailability.UNRESOLVED:
        return RequirementOutcome.UNRESOLVED, "evidence_availability_unresolved"
    if assessment.origin is EvidenceOrigin.R4_MECHANICAL_RESULT:
        return RequirementOutcome.PRESENT_BUT_INADMISSIBLE, "r4_mechanical_result_not_diagnostic_support"
    if assessment.origin is EvidenceOrigin.MODEL_GENERAL_KNOWLEDGE:
        return RequirementOutcome.PRESENT_BUT_INADMISSIBLE, "model_general_knowledge_not_evidence"
    if (
        assessment.origin is EvidenceOrigin.DESCRIPTIVE_ADMISSIBLE_EVIDENCE
        or assessment.admission_state is DiagnosticAdmissionState.DESCRIPTIVE_ONLY
    ):
        return RequirementOutcome.PRESENT_BUT_INADMISSIBLE, "descriptive_admission_not_diagnostic_admission"
    if assessment.admission_state is DiagnosticAdmissionState.INADMISSIBLE:
        return RequirementOutcome.PRESENT_BUT_INADMISSIBLE, "diagnostic_evidence_inadmissible"
    if assessment.admission_state is DiagnosticAdmissionState.UNRESOLVED:
        return RequirementOutcome.UNRESOLVED, "diagnostic_admission_unresolved"
    if assessment.fitness_state is EvidenceFitnessState.FAILED:
        return RequirementOutcome.FAILED, "evidence_fitness_failed"
    if assessment.fitness_state is EvidenceFitnessState.UNRESOLVED:
        return RequirementOutcome.UNRESOLVED, "evidence_fitness_unresolved"
    return RequirementOutcome.SATISFIED, "authenticated_requirement_satisfied"


def _judgment(
    *,
    requirement_ref: str,
    outcome: RequirementOutcome,
    reason_code: str,
    evidence_refs: tuple[str, ...],
    authority_refs: tuple[str, ...],
    dimension: EvidenceDimension | None,
    context: str,
    dependency_classification: DependencyClassification,
    consequence: RequirementConsequence,
) -> RequirementJudgment:
    payload = {
        "requirement_ref": requirement_ref,
        "requirement_version": GOVERNANCE_VERSION,
        "outcome": outcome.value,
        "reason_code": reason_code,
        "evidence_refs": sorted(evidence_refs),
        "authority_refs": sorted(authority_refs),
        "dimension": dimension.value if dimension else None,
        "context": context,
        "dependency_classification": dependency_classification.value,
        "consequence": consequence.value,
        "authority_version": GOVERNANCE_VERSION,
    }
    return RequirementJudgment(
        judgment_id=stable_content_id("reqjud", canonical_json_fingerprint(payload)),
        requirement_ref=requirement_ref,
        requirement_version=GOVERNANCE_VERSION,
        outcome=outcome,
        reason_code=reason_code,
        evidence_refs=tuple(sorted(evidence_refs)),
        authority_refs=tuple(sorted(authority_refs)),
        dimension=dimension,
        context=context,
        dependency_classification=dependency_classification,
        consequence=consequence,
        authority_version=GOVERNANCE_VERSION,
    )


def _derive_first_blocker(
    *,
    requested_claim_type: ClaimType,
    judgments: tuple[RequirementJudgment, ...],
    conflict_assessment: EvidenceConflictAssessment | None,
    proposed_method_refs: tuple[str, ...],
) -> tuple[PreTestDisposition, EvidenceReadiness, str]:
    if requested_claim_type is not ClaimType.DIAGNOSTIC:
        return (
            PreTestDisposition.CLARIFICATION_REQUIRED,
            EvidenceReadiness.UNRESOLVED,
            "claim_class_restricted",
        )

    external_blocking_outcomes = {
        RequirementOutcome.EXTERNAL_UNMET,
        RequirementOutcome.FAILED,
        RequirementOutcome.MISSING,
        RequirementOutcome.UNRESOLVED,
        RequirementOutcome.PRESENT_BUT_INADMISSIBLE,
    }
    external = [
        item
        for item in judgments
        if item.dependency_classification is DependencyClassification.EXTERNAL
        and item.outcome in external_blocking_outcomes
    ]
    if external:
        return (
            PreTestDisposition.EXTERNAL_EVIDENCE_REQUIRED,
            EvidenceReadiness.EXTERNAL_EVIDENCE_REQUIRED,
            f"external_evidence_unmet:{external[0].requirement_ref}",
        )

    blocking_outcomes = {
        RequirementOutcome.FAILED,
        RequirementOutcome.MISSING,
        RequirementOutcome.UNRESOLVED,
        RequirementOutcome.PRESENT_BUT_INADMISSIBLE,
    }
    defective = [item for item in judgments if item.outcome in blocking_outcomes]
    if defective:
        first = defective[0]
        return (
            PreTestDisposition.MISSING_EVIDENCE,
            EvidenceReadiness.MISSING_INTERNAL_EVIDENCE,
            f"{first.reason_code}:{first.requirement_ref}",
        )

    if conflict_assessment is not None and conflict_assessment.unresolved_material_conflict:
        return (
            PreTestDisposition.CONFLICTING_EVIDENCE,
            EvidenceReadiness.UNRESOLVED,
            f"unresolved_evidence_conflict:{conflict_assessment.conflict_id}",
        )

    _ = proposed_method_refs
    return (
        PreTestDisposition.HYPOTHESIS_ONLY,
        EvidenceReadiness.READY_FOR_TEST,
        "method_authority_unavailable",
    )


def _build_evaluation(
    *,
    proposition: DiagnosticProposition,
    profile: ResolvedRequiredEvidenceProfile,
    bundle_ref: str,
    bundle_fingerprint: str,
    readiness: EvidenceReadiness,
    blocker: str,
    finalized_at: datetime,
) -> PreTestDiagnosticEvaluation:
    governance_fingerprint = canonical_json_fingerprint(
        {"governance": "R6-2", "version": GOVERNANCE_VERSION}
    )
    data: dict[str, Any] = {
        "evaluation_id": "pending",
        "evaluation_schema_version": EVALUATION_SCHEMA_VERSION,
        "diagnostic_proposition_ref": proposition.proposition_id,
        "diagnostic_proposition_fingerprint": proposition.semantic_fingerprint,
        "resolved_profile_ref": profile.profile_id,
        "resolved_profile_version": profile.profile_version,
        "resolved_profile_fingerprint": profile.profile_fingerprint,
        "requirement_judgment_bundle_ref": bundle_ref,
        "requirement_judgment_bundle_fingerprint": bundle_fingerprint,
        "evidence_readiness": readiness,
        "test_eligibility": TestEligibility.NOT_ELIGIBLE,
        "first_controlling_blocker": blocker,
        "analytical_outcome": AnalyticalOutcome.NOT_EVALUATED,
        "alternative_explanation_state": AlternativeExplanationState.NOT_COMPLETED,
        "authority_bindings": (
            AuthorityBinding(
                authority_ref=proposition.proposition_id,
                authority_version=proposition.proposition_schema_version,
                authority_fingerprint=proposition.semantic_fingerprint,
            ),
            AuthorityBinding(
                authority_ref=profile.profile_id,
                authority_version=profile.profile_version,
                authority_fingerprint=profile.profile_fingerprint,
            ),
            AuthorityBinding(
                authority_ref="R6_2_DETERMINISTIC_PRETEST_GOVERNANCE",
                authority_version=GOVERNANCE_VERSION,
                authority_fingerprint=governance_fingerprint,
            ),
        ),
        "finalized_at": finalized_at,
    }
    fingerprint = pretest_evaluation_semantic_fingerprint(data)
    data["evaluation_fingerprint"] = fingerprint
    data["evaluation_id"] = stable_content_id("pretest", fingerprint)
    return PreTestDiagnosticEvaluation(**data)


def _expected_requirement_classifications(
    template: HypothesisFamilyRequirementTemplate,
) -> dict[str, DependencyClassification]:
    family_class = template.dependency_source_classifications[0].classification
    expected = {
        item.requirement_ref: item.classification
        for item in template.dependency_source_classifications
    }
    expected.update(
        {
            item.requirement_ref: family_class
            for item in template.dimension_requirements
            if item.requirement_ref is not None
        }
    )
    return expected


def _authenticated_metric_ids(metric_refs: tuple[str, ...]) -> tuple[str, ...]:
    registry = get_metric_registry()
    ids: list[str] = []
    for reference in metric_refs:
        if not reference.startswith("metric:"):
            raise GovernanceAuthenticationError("metric_mismatch", f"invalid governed Metric reference: {reference}")
        metric_id = reference.removeprefix("metric:").split("@", maxsplit=1)[0]
        if registry.get(metric_id) is None:
            raise GovernanceAuthenticationError("metric_mismatch", f"unknown governed Metric: {metric_id}")
        ids.append(metric_id)
    return tuple(sorted(ids))


def _authenticate_conflict(
    proposition: DiagnosticProposition,
    supplied: EvidenceConflictAssessment,
) -> None:
    try:
        assessment = EvidenceConflictAssessment.model_validate(supplied.model_dump(mode="python"))
    except ValueError as exc:
        raise GovernanceAuthenticationError(
            "stale_or_tampered_conflict_authority",
            "evidence conflict assessment failed fingerprint authentication",
        ) from exc
    if (
        assessment.diagnostic_proposition_ref != proposition.proposition_id
        or assessment.diagnostic_proposition_fingerprint != proposition.semantic_fingerprint
    ):
        raise GovernanceAuthenticationError(
            "proposition_authority_mismatch",
            "evidence conflict authority does not bind the exact proposition",
        )


def _equivalent_slot_value(actual: Any, expected: Any) -> bool:
    if isinstance(expected, tuple):
        actual_tuple = actual if isinstance(actual, tuple) else (actual,)
        return tuple(sorted(str(item) for item in actual_tuple)) == tuple(
            sorted(str(item) for item in expected)
        )
    return actual == expected


def _slot_binding_ref(value: Any) -> str:
    if isinstance(value, tuple):
        return "refs_sha256:" + canonical_json_fingerprint(sorted(value, key=str))
    return str(value)


def _sorted_authority_bindings(values: Any) -> list[dict[str, Any]]:
    return sorted(
        (_json(value) for value in values),
        key=lambda item: (
            item["authority_ref"],
            item["authority_version"],
            item["authority_fingerprint"],
        ),
    )


def _data(value: ContractBase | Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(value, ContractBase):
        return value.model_dump(mode="python")
    return value


def _json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, ContractBase):
        return value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return {key: _json(item) for key, item in value.items()}
    if isinstance(value, Enum):
        return value.value
    return value


def _enum(value: Any) -> Any:
    return value.value if isinstance(value, Enum) else value


__all__ = [
    "DiagnosticAdmissionState",
    "EvidenceAvailability",
    "EvidenceConflictAssessment",
    "EvidenceFitnessState",
    "EvidenceOrigin",
    "GovernanceAuthenticationError",
    "PreTestDisposition",
    "PreTestGovernanceResult",
    "RequirementEvidenceAssessment",
    "evidence_conflict_assessment_fingerprint",
    "govern_pretest",
    "requirement_evidence_assessment_fingerprint",
    "requirement_judgment_bundle_fingerprint",
    "resolve_dimension_applicability",
]
