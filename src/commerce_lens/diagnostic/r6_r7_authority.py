"""Production-only bridge from current R7 authority into R6 pre-test governance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from commerce_lens.contracts.diagnostic import AuthorityBinding, DiagnosticProposition
from commerce_lens.contracts.required_evidence import DependencyClassification
from commerce_lens.contracts.r7 import R7AuthorityReference
from commerce_lens.diagnostic.family_registry import MVP_FAMILY_REGISTRY
from commerce_lens.diagnostic.generator import SourceAuthorityClass, SourceAuthorityView
from commerce_lens.diagnostic.governance import (
    AuthorityClass,
    DiagnosticAdmissionState,
    EvidenceAvailability,
    EvidenceFitnessState,
    EvidenceOrigin,
    GovernanceAuthenticationError,
    PreTestExecutionAuthority,
    RegisteredAuthority,
    RequirementEvidenceAssessment,
    requirement_evidence_assessment_fingerprint,
)
from commerce_lens.diagnostic.r7_method_registry import (
    IMPLEMENTATION_BINDING,
    METHOD_DEFINITION,
    R7_METHOD_REGISTRY,
    R7MethodAuthorityRegistry,
    SUPPORT_CRITERION,
    VALIDATION_PROFILE,
    authority_ref,
)
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, stable_content_id


@dataclass(frozen=True)
class ProductionPreTestAuthorityResolution:
    """Trusted production inputs added to the ordinary R6 pre-test registry."""

    execution_authority: PreTestExecutionAuthority
    evidence_assessments: tuple[RequirementEvidenceAssessment, ...]
    registered_authorities: tuple[RegisteredAuthority, ...]


def resolve_production_pretest_authority(
    proposition: DiagnosticProposition,
    source_views: tuple[SourceAuthorityView, ...],
    *,
    method_registry: R7MethodAuthorityRegistry,
) -> ProductionPreTestAuthorityResolution | None:
    """Resolve current authority for the sole approved executable R7 family.

    Non-product families deliberately receive no execution authority. References
    on a candidate or proposition are never consulted as method authority.
    """

    if proposition.family_id != METHOD_DEFINITION.family_id:
        return None
    if method_registry is not R7_METHOD_REGISTRY:
        raise GovernanceAuthenticationError(
            "stale_or_untrusted_r7_method_registry",
            "production R6 accepts only the current approved R7 method registry",
        )

    execution_authority = _current_execution_authority(proposition, method_registry)
    evidence_assessments, evidence_authorities = _resolve_evidence_authority(
        proposition,
        source_views,
        execution_authority,
    )
    method_authorities = tuple(
        RegisteredAuthority(
            authority_class=AuthorityClass.METHOD,
            binding=binding,
            subject_refs=(
                proposition.proposition_id,
                proposition.family_id,
                proposition.family_fingerprint,
            ),
            intended_uses=("diagnostic_execution",),
            dependency_classification=DependencyClassification.INTERNAL,
        )
        for binding in execution_authority.bindings
    )
    return ProductionPreTestAuthorityResolution(
        execution_authority=execution_authority,
        evidence_assessments=evidence_assessments,
        registered_authorities=(*method_authorities, *evidence_authorities),
    )


def _current_execution_authority(
    proposition: DiagnosticProposition,
    method_registry: R7MethodAuthorityRegistry,
) -> PreTestExecutionAuthority:
    method_ref = authority_ref(METHOD_DEFINITION)
    support_ref = authority_ref(SUPPORT_CRITERION)
    validation_ref = authority_ref(VALIDATION_PROFILE)
    implementation_ref = authority_ref(IMPLEMENTATION_BINDING)
    try:
        method_registry.authenticate_bundle(
            method=method_ref,
            support_criterion=support_ref,
            validation_profile=validation_ref,
            implementation=implementation_ref,
            family_id=proposition.family_id,
            family_version=proposition.family_version,
            family_fingerprint=proposition.family_fingerprint,
        )
    except ValueError as exc:
        raise GovernanceAuthenticationError(
            str(exc),
            "current R7 execution authority does not authenticate for the exact family",
        ) from exc
    return PreTestExecutionAuthority(
        family_id=proposition.family_id,
        family_version=proposition.family_version,
        family_fingerprint=proposition.family_fingerprint,
        method=_binding(method_ref),
        support_criterion=_binding(support_ref),
        validation_profile=_binding(validation_ref),
        implementation=_binding(implementation_ref),
    )


def _resolve_evidence_authority(
    proposition: DiagnosticProposition,
    source_views: tuple[SourceAuthorityView, ...],
    execution_authority: PreTestExecutionAuthority,
) -> tuple[
    tuple[RequirementEvidenceAssessment, ...],
    tuple[RegisteredAuthority, ...],
]:
    if set(METHOD_DEFINITION.required_variables) != set(proposition.variable_refs):
        raise GovernanceAuthenticationError(
            "method_variable_mismatch",
            "R7 method variables do not match the exact proposition",
        )
    by_ref = {view.authority_ref: view for view in source_views}
    source_matches = [
        by_ref[reference]
        for reference in proposition.source_observation_refs
        if reference in by_ref
        and by_ref[reference].authority_class is SourceAuthorityClass.SOURCE_REFERENCE
        and by_ref[reference].dependency_classification is DependencyClassification.INTERNAL
    ]
    if len(source_matches) != 1:
        raise GovernanceAuthenticationError(
            "method_evidence_source_unavailable",
            "approved R7 method requires one exact governed internal canonical source",
        )
    source = source_matches[0]
    required_views = [source]
    for reference, expected_class in (
        *((reference, SourceAuthorityClass.VARIABLE) for reference in proposition.variable_refs),
        *((reference, SourceAuthorityClass.METRIC) for reference in proposition.metric_refs),
    ):
        view = by_ref.get(reference)
        if view is None:
            raise GovernanceAuthenticationError(
                "method_evidence_source_unavailable",
                f"approved R7 method input authority is unavailable: {reference}",
            )
        if view.authority_class is not expected_class:
            raise GovernanceAuthenticationError(
                "method_evidence_authority_class_mismatch",
                f"approved R7 method input authority has the wrong class: {reference}",
            )
        required_views.append(view)
    for view in required_views:
        _authenticate_alignment(proposition, view)

    template = MVP_FAMILY_REGISTRY.get_requirement_template(proposition.family_id)
    requirements = [
        (item.requirement_ref, DependencyClassification.INTERNAL)
        for item in template.dimension_requirements
        if item.requirement_ref is not None
    ]
    requirements.extend(
        (item.requirement_ref, item.classification)
        for item in template.dependency_source_classifications
    )
    evidence_binding = AuthorityBinding(
        authority_ref=source.authority_ref,
        authority_version=source.authority_version,
        authority_fingerprint=source.authority_fingerprint,
    )
    basis = {
        "proposition_fingerprint": proposition.semantic_fingerprint,
        "source_views": sorted(
            (view.model_dump(mode="json") for view in required_views),
            key=lambda item: (item["authority_class"], item["authority_ref"]),
        ),
        "execution_authority": execution_authority.model_dump(mode="json"),
    }
    assessments: list[RequirementEvidenceAssessment] = []
    authorities: list[RegisteredAuthority] = [
        RegisteredAuthority(
            authority_class=AuthorityClass.EVIDENCE,
            binding=evidence_binding,
            subject_refs=(
                proposition.proposition_id,
                *(reference for reference, _ in requirements),
            ),
            intended_uses=("diagnostic",),
            dependency_classification=DependencyClassification.INTERNAL,
        )
    ]
    for requirement_ref, classification in requirements:
        if classification is not DependencyClassification.INTERNAL:
            raise GovernanceAuthenticationError(
                "method_evidence_source_class_mismatch",
                "approved product-composition method requires governed internal evidence",
            )
        assessment_binding = _derived_binding(
            "r6-pretest-evidence-assessment",
            requirement_ref,
            basis,
        )
        admission_binding = _derived_binding(
            "r6-diagnostic-admission",
            requirement_ref,
            basis,
        )
        data: dict[str, Any] = {
            "assessment_id": "pending",
            "assessment_version": "1.0.0",
            "requirement_ref": requirement_ref,
            "availability": EvidenceAvailability.PRESENT,
            "admission_state": DiagnosticAdmissionState.DIAGNOSTIC_ADMITTED,
            "fitness_state": EvidenceFitnessState.PASSED,
            "origin": EvidenceOrigin.GOVERNED_INTERNAL,
            "dependency_classification": classification,
            "evidence_refs": (source.authority_ref,),
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
            "authority_bindings": (assessment_binding,),
            "diagnostic_admission_authority": admission_binding,
            "failure_reason": None,
        }
        data["assessment_fingerprint"] = requirement_evidence_assessment_fingerprint(data)
        data["assessment_id"] = stable_content_id("reqevid", data["assessment_fingerprint"])
        assessment = RequirementEvidenceAssessment(**data)
        assessments.append(assessment)
        subjects = (proposition.proposition_id, requirement_ref)
        authorities.extend(
            (
                RegisteredAuthority(
                    authority_class=AuthorityClass.EVIDENCE_ASSESSMENT,
                    binding=assessment_binding,
                    subject_refs=subjects,
                    intended_uses=("diagnostic_pretest",),
                    dependency_classification=classification,
                ),
                RegisteredAuthority(
                    authority_class=AuthorityClass.DIAGNOSTIC_ADMISSION,
                    binding=admission_binding,
                    subject_refs=(*subjects, source.authority_ref),
                    intended_uses=("diagnostic",),
                    dependency_classification=classification,
                ),
            )
        )
    return tuple(assessments), tuple(authorities)


def _authenticate_alignment(
    proposition: DiagnosticProposition,
    view: SourceAuthorityView,
) -> None:
    expected = (
        proposition.scope_ref,
        proposition.baseline_period_ref,
        proposition.comparison_period_ref,
        proposition.baseline_population_ref,
        proposition.comparison_population_ref,
    )
    actual = (
        view.scope_ref,
        view.baseline_period_ref,
        view.comparison_period_ref,
        view.baseline_population_ref,
        view.comparison_population_ref,
    )
    if actual != expected:
        raise GovernanceAuthenticationError(
            "method_evidence_alignment_mismatch",
            f"R7 method input authority is misaligned: {view.authority_ref}",
        )
    if view.dependency_classification is not DependencyClassification.INTERNAL:
        raise GovernanceAuthenticationError(
            "method_evidence_source_class_mismatch",
            f"R7 method input is not governed internal authority: {view.authority_ref}",
        )


def _binding(reference: R7AuthorityReference) -> AuthorityBinding:
    return AuthorityBinding(
        authority_ref=reference.authority_id,
        authority_version=reference.authority_version,
        authority_fingerprint=reference.authority_fingerprint,
    )


def _derived_binding(
    authority_kind: str,
    requirement_ref: str,
    basis: dict[str, Any],
) -> AuthorityBinding:
    fingerprint = canonical_json_fingerprint(
        {
            "authority_kind": authority_kind,
            "authority_version": "1.0.0",
            "requirement_ref": requirement_ref,
            "basis": basis,
        }
    )
    return AuthorityBinding(
        authority_ref=f"{authority_kind}:{requirement_ref}",
        authority_version="1.0.0",
        authority_fingerprint=fingerprint,
    )


__all__ = [
    "ProductionPreTestAuthorityResolution",
    "resolve_production_pretest_authority",
]
