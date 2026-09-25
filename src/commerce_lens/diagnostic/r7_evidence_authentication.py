"""Authenticate R7 evidence manifests against independent R3/R6 authority."""

from __future__ import annotations

from dataclasses import dataclass

from commerce_lens.contracts.required_evidence import (
    DependencyClassification, EvidenceRole,
    RequirementJudgment,
)
from commerce_lens.contracts.diagnostic import AuthorityBinding
from commerce_lens.contracts.r7 import DiagnosticEvidenceInputSet
from commerce_lens.diagnostic.governance import (
    AuthorityClass,
    DiagnosticAdmissionState,
    EvidenceFitnessState,
    EvidenceOrigin,
    PreTestAuthorityRegistry,
    RequirementEvidenceAssessment,
)
from commerce_lens.evidence.identifiers import canonical_json_fingerprint


class R7EvidenceAuthenticationError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class TrustedR7EvidenceRole:
    requirement_ref: str
    evidence_role: EvidenceRole
    authority_binding: AuthorityBinding


@dataclass(frozen=True)
class TrustedR7EvidenceAuthority:
    """Out-of-manifest upstream assessments supplied by trusted orchestration."""

    authority_label: str
    assessments: tuple[RequirementEvidenceAssessment, ...]
    roles: tuple[TrustedR7EvidenceRole, ...]


def requirement_judgment_fingerprint(judgment: RequirementJudgment) -> str:
    return canonical_json_fingerprint(judgment.model_dump(mode="json"))


def authenticate_evidence_input_set(
    evidence_inputs: DiagnosticEvidenceInputSet,
    *,
    judgments: tuple[RequirementJudgment, ...],
    trusted_authority: TrustedR7EvidenceAuthority,
    authority_registry: PreTestAuthorityRegistry,
) -> None:
    judgments_by_id = {item.judgment_id: item for item in judgments}
    assessments_by_id = {item.assessment_id: item for item in trusted_authority.assessments}
    roles_by_requirement = {item.requirement_ref: item for item in trusted_authority.roles}
    if len(assessments_by_id) != len(trusted_authority.assessments):
        _fail("R7_EVIDENCE_DUPLICATE_ASSESSMENT")
    for binding in evidence_inputs.bindings:
        judgment = judgments_by_id.get(binding.requirement_judgment_ref)
        if judgment is None or requirement_judgment_fingerprint(judgment) != binding.requirement_judgment_fingerprint:
            _fail("R7_EVIDENCE_JUDGMENT_MISMATCH")
        assessment = assessments_by_id.get(binding.evidence_assessment_ref)
        if assessment is None or assessment.assessment_fingerprint != binding.evidence_assessment_fingerprint:
            _fail("R7_EVIDENCE_ASSESSMENT_MISMATCH")
        if assessment.requirement_ref != judgment.requirement_ref:
            _fail("R7_EVIDENCE_REQUIREMENT_MISMATCH")
        trusted_role = roles_by_requirement.get(judgment.requirement_ref)
        if trusted_role is None or trusted_role.evidence_role != binding.evidence_role:
            _fail("R7_EVIDENCE_ROLE_MISMATCH")
        if trusted_role.authority_binding not in assessment.authority_bindings:
            _fail("R7_EVIDENCE_ROLE_AUTHORITY_MISMATCH")
        if assessment.admission_state is not DiagnosticAdmissionState.DIAGNOSTIC_ADMITTED:
            _fail("R7_EVIDENCE_NOT_DIAGNOSTICALLY_ADMITTED")
        if assessment.fitness_state is not EvidenceFitnessState.PASSED:
            _fail("R7_EVIDENCE_FITNESS_NOT_PASSED")
        if assessment.diagnostic_admission_authority != binding.diagnostic_admission_authority:
            _fail("R7_EVIDENCE_ADMISSION_AUTHORITY_MISMATCH")
        try:
            admission = authority_registry.authenticate_binding(
                AuthorityClass.DIAGNOSTIC_ADMISSION,
                assessment.diagnostic_admission_authority,
            )
            for authority in assessment.authority_bindings:
                authority_registry.authenticate_binding(AuthorityClass.EVIDENCE_ASSESSMENT, authority)
            registered_evidence = authority_registry.require_reference(AuthorityClass.EVIDENCE, binding.evidence_ref)
        except ValueError as exc:
            raise R7EvidenceAuthenticationError("R7_EVIDENCE_UPSTREAM_AUTHORITY_INVALID") from exc
        if "diagnostic" not in admission.intended_uses:
            _fail("R7_EVIDENCE_ADMISSION_USE_MISMATCH")
        if binding.evidence_ref not in assessment.evidence_refs:
            _fail("R7_EVIDENCE_ARTIFACT_MISMATCH")
        if registered_evidence.binding.authority_fingerprint != binding.evidence_fingerprint:
            _fail("R7_EVIDENCE_ARTIFACT_FINGERPRINT_MISMATCH")
        if (
            assessment.dependency_classification is not DependencyClassification.INTERNAL
            or assessment.origin not in {
                EvidenceOrigin.GOVERNED_INTERNAL,
                EvidenceOrigin.DESCRIPTIVE_ADMISSIBLE_EVIDENCE,
                EvidenceOrigin.R4_MECHANICAL_RESULT,
            }
            or binding.source_class != "GOVERNED_INTERNAL"
        ):
            _fail("R7_EVIDENCE_SOURCE_CLASS_MISMATCH")
        if assessment.diagnostic_proposition_ref != evidence_inputs.diagnostic_proposition_ref or assessment.diagnostic_proposition_fingerprint != evidence_inputs.diagnostic_proposition_fingerprint:
            _fail("R7_EVIDENCE_PROPOSITION_MISMATCH")
        if assessment.scope_ref != binding.scope_ref:
            _fail("R7_EVIDENCE_SCOPE_MISMATCH")
        if set(binding.period_refs) != {assessment.baseline_period_ref, assessment.comparison_period_ref}:
            _fail("R7_EVIDENCE_PERIOD_MISMATCH")
        if set(binding.population_refs) != {assessment.baseline_population_ref, assessment.comparison_population_ref}:
            _fail("R7_EVIDENCE_POPULATION_MISMATCH")
        if tuple(sorted(binding.metric_refs)) != tuple(sorted(assessment.metric_refs)):
            _fail("R7_EVIDENCE_METRIC_MISMATCH")
        if tuple(sorted(binding.variable_refs)) != tuple(sorted(assessment.variable_refs)):
            _fail("R7_EVIDENCE_VARIABLE_MISMATCH")


def _fail(code: str) -> None:
    raise R7EvidenceAuthenticationError(code)
