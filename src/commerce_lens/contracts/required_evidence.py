"""R3 requirement templates, exact profiles, and requirement judgments."""

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping, Self

from pydantic import Field, model_validator

from commerce_lens.contracts.common import ContractBase
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, stable_content_id


SHA256_PATTERN = r"^[0-9a-f]{64}$"


class EvidenceDimension(str, Enum):
    RELEVANCE = "relevance"
    SEMANTIC_VALIDITY = "semantic_validity"
    SOURCE_AUTHORITY = "source_authority"
    COMPLETENESS = "completeness"
    TEMPORAL_ALIGNMENT = "temporal_alignment"
    POPULATION_ALIGNMENT = "population_alignment"
    METRIC_COMPATIBILITY = "metric_compatibility"
    UNIT_CURRENCY_COMPATIBILITY = "unit_currency_compatibility"
    MEASUREMENT_VALIDITY = "measurement_validity"
    MISSINGNESS = "missingness"
    PROVENANCE = "provenance"
    VALIDATION_STATUS = "validation_status"


class ApplicabilityState(str, Enum):
    REQUIRED = "REQUIRED"
    CONDITIONAL = "CONDITIONAL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ApplicabilityLevel(str, Enum):
    PROPOSITION = "PROPOSITION"
    ROLE = "ROLE"
    CROSS_ROLE_RELATIONSHIP = "CROSS_ROLE_RELATIONSHIP"
    SHARED_AUTHORITY = "SHARED_AUTHORITY"
    METHOD_SPECIFIC = "METHOD_SPECIFIC"


class EvidenceRole(str, Enum):
    OBSERVED_OUTCOME = "observed_outcome"
    EXPLANATORY_VARIABLE = "explanatory_variable"
    POPULATION_ELIGIBILITY = "population_eligibility"
    COMPLETENESS_COVERAGE = "completeness_coverage"
    SOURCE_AUTHORITY_PROVENANCE = "source_authority_provenance"
    NORMALIZATION_DENOMINATOR = "normalization_denominator"
    IDENTITY_JOIN = "identity_join"
    UNIT_CURRENCY = "unit_currency"


class DependencyClassification(str, Enum):
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"
    EITHER = "EITHER"


class MeasurementClassification(str, Enum):
    DIRECT_MEASUREMENT = "DIRECT_MEASUREMENT"
    GOVERNED_TRANSFORMED_MEASUREMENT = "GOVERNED_TRANSFORMED_MEASUREMENT"
    GOVERNED_PROXY = "GOVERNED_PROXY"
    INFERRED_CONSTRUCT = "INFERRED_CONSTRUCT"
    UNSUPPORTED_PROXY = "UNSUPPORTED_PROXY"


class RequirementOutcome(str, Enum):
    SATISFIED = "SATISFIED"
    FAILED = "FAILED"
    MISSING = "MISSING"
    UNRESOLVED = "UNRESOLVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    EXTERNAL_UNMET = "EXTERNAL_UNMET"
    PRESENT_BUT_INADMISSIBLE = "PRESENT_BUT_INADMISSIBLE"


class RequirementConsequence(str, Enum):
    BLOCKING = "BLOCKING"
    QUALIFYING = "QUALIFYING"
    NONE = "NONE"


class DimensionRequirement(ContractBase):
    dimension: EvidenceDimension
    applicability: ApplicabilityState
    applicability_level: ApplicabilityLevel
    requirement_ref: str | None = None
    applicability_condition_ref: str | None = None
    controlling_authority_refs: tuple[str, ...] = ()
    failure_consequence: str | None = None
    governed_reason: str | None = None

    @model_validator(mode="after")
    def validate_resolution(self) -> Self:
        if self.applicability is ApplicabilityState.NOT_APPLICABLE:
            if not self.governed_reason:
                raise ValueError("NOT_APPLICABLE dimension requires a governed reason")
        elif not self.requirement_ref or not self.failure_consequence:
            raise ValueError("applicable dimension requires requirement_ref and failure_consequence")
        if self.applicability is ApplicabilityState.CONDITIONAL:
            if not self.applicability_condition_ref:
                raise ValueError("CONDITIONAL dimension requires an applicability condition reference")
        elif self.applicability_condition_ref is not None:
            raise ValueError("applicability condition reference is only valid for CONDITIONAL dimensions")
        return self


class DependencyRequirement(ContractBase):
    requirement_ref: str = Field(min_length=1)
    classification: DependencyClassification


class MeasurementRequirement(ContractBase):
    requirement_ref: str = Field(min_length=1)
    role: EvidenceRole
    classification: MeasurementClassification
    permitted_use: str = Field(min_length=1)


class SlotBinding(ContractBase):
    slot: str = Field(min_length=1)
    bound_ref: str = Field(min_length=1)
    bound_fingerprint: str | None = Field(default=None, pattern=SHA256_PATTERN)


class HypothesisFamilyRequirementTemplate(ContractBase):
    """Static family requirement authority, not a resolved profile."""

    template_id: str = Field(min_length=1)
    template_version: str = Field(min_length=1)
    template_fingerprint: str = Field(pattern=SHA256_PATTERN)
    family_id: str = Field(min_length=1)
    family_version: str = Field(min_length=1)
    allowed_proposition_slots: tuple[str, ...] = Field(min_length=1)
    required_evidence_roles: tuple[EvidenceRole, ...] = Field(min_length=1)
    dimension_requirements: tuple[DimensionRequirement, ...] = Field(min_length=12, max_length=12)
    dependency_source_classifications: tuple[DependencyRequirement, ...] = Field(min_length=1)
    measurement_classifications: tuple[MeasurementRequirement, ...] = Field(min_length=1)
    method_specific_requirement_slots: tuple[str, ...] = ()
    known_blocking_conditions: tuple[str, ...] = Field(min_length=1)
    maximum_evidence_use: str = Field(min_length=1)
    prohibited_evidence_substitutions: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_template(self) -> Self:
        _require_all_dimensions(self.dimension_requirements)
        expected = requirement_template_semantic_fingerprint(self)
        if self.template_fingerprint != expected:
            raise ValueError("template_fingerprint does not match material template authority")
        return self


class ResolvedRequiredEvidenceProfile(ContractBase):
    """Immutable R3 requirement authority exactly bound to one proposition."""

    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    profile_schema_version: str = Field(min_length=1)
    profile_fingerprint: str = Field(pattern=SHA256_PATTERN)
    template_id: str = Field(min_length=1)
    template_version: str = Field(min_length=1)
    template_fingerprint: str = Field(pattern=SHA256_PATTERN)
    diagnostic_proposition_ref: str = Field(min_length=1)
    diagnostic_proposition_fingerprint: str = Field(pattern=SHA256_PATTERN)
    exact_slot_bindings: tuple[SlotBinding, ...] = Field(min_length=1)
    resolved_evidence_roles: tuple[EvidenceRole, ...] = Field(min_length=1)
    dimension_applicability_decisions: tuple[DimensionRequirement, ...] = Field(min_length=12, max_length=12)
    dependency_classifications: tuple[DependencyRequirement, ...] = Field(min_length=1)
    measurement_classifications: tuple[MeasurementRequirement, ...] = Field(min_length=1)
    method_requirement_refs: tuple[str, ...] = ()
    blocking_rules: tuple[str, ...] = Field(min_length=1)
    qualification_rules: tuple[str, ...] = ()
    narrowing_rules: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_profile(self) -> Self:
        _require_all_dimensions(self.dimension_applicability_decisions)
        if any(
            decision.applicability is ApplicabilityState.CONDITIONAL
            for decision in self.dimension_applicability_decisions
        ):
            raise ValueError("exact profile must resolve CONDITIONAL dimensions")
        if len({binding.slot for binding in self.exact_slot_bindings}) != len(self.exact_slot_bindings):
            raise ValueError("exact_slot_bindings cannot contain duplicate slots")
        expected = resolved_profile_semantic_fingerprint(self)
        if self.profile_fingerprint != expected:
            raise ValueError("profile_fingerprint does not match exact proposition binding")
        if self.profile_id != stable_content_id("reqprof", expected):
            raise ValueError("profile_id must be the stable ID for exact profile identity")
        return self


def validate_profile_against_template(
    profile: ResolvedRequiredEvidenceProfile,
    template: HypothesisFamilyRequirementTemplate,
) -> None:
    """Validate exact-binding decisions without resolving or evaluating evidence."""

    if (
        profile.template_id != template.template_id
        or profile.template_version != template.template_version
        or profile.template_fingerprint != template.template_fingerprint
    ):
        raise ValueError("resolved profile does not reference the supplied requirement template")

    template_by_dimension = {item.dimension: item for item in template.dimension_requirements}
    profile_by_dimension = {
        item.dimension: item for item in profile.dimension_applicability_decisions
    }
    for dimension, template_requirement in template_by_dimension.items():
        decision = profile_by_dimension[dimension]
        if (
            template_requirement.applicability is ApplicabilityState.REQUIRED
            and decision.applicability is not ApplicabilityState.REQUIRED
        ):
            raise ValueError(
                f"exact profile cannot weaken REQUIRED template dimension: {dimension.value}"
            )


class RequirementJudgment(ContractBase):
    judgment_id: str = Field(min_length=1)
    requirement_ref: str = Field(min_length=1)
    requirement_version: str = Field(min_length=1)
    outcome: RequirementOutcome
    reason_code: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = ()
    authority_refs: tuple[str, ...] = Field(min_length=1)
    role: EvidenceRole | None = None
    dimension: EvidenceDimension | None = None
    context: str = Field(min_length=1)
    dependency_classification: DependencyClassification | None = None
    consequence: RequirementConsequence
    authority_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_judgment(self) -> Self:
        if self.outcome is RequirementOutcome.NOT_APPLICABLE and self.consequence is RequirementConsequence.BLOCKING:
            raise ValueError("NOT_APPLICABLE judgment cannot be blocking")
        if self.outcome is RequirementOutcome.EXTERNAL_UNMET:
            if self.dependency_classification is not DependencyClassification.EXTERNAL:
                raise ValueError("EXTERNAL_UNMET requires EXTERNAL dependency classification")
        return self


def requirement_template_semantic_fingerprint(
    template: HypothesisFamilyRequirementTemplate | Mapping[str, Any],
) -> str:
    data = _data(template)
    payload = {
        "template_version": data["template_version"],
        "family_id": data["family_id"],
        "family_version": data["family_version"],
        "allowed_proposition_slots": sorted(data["allowed_proposition_slots"]),
        "required_evidence_roles": sorted(_enum(value) for value in data["required_evidence_roles"]),
        "dimension_requirements": _sorted_models(data["dimension_requirements"], "dimension"),
        "dependency_source_classifications": _sorted_models(
            data["dependency_source_classifications"], "requirement_ref"
        ),
        "measurement_classifications": _sorted_models(data["measurement_classifications"], "requirement_ref"),
        "method_specific_requirement_slots": sorted(data.get("method_specific_requirement_slots", ())),
        "known_blocking_conditions": sorted(data["known_blocking_conditions"]),
        "maximum_evidence_use": data["maximum_evidence_use"],
        "prohibited_evidence_substitutions": sorted(data["prohibited_evidence_substitutions"]),
    }
    return canonical_json_fingerprint(payload)


def resolved_profile_semantic_fingerprint(
    profile: ResolvedRequiredEvidenceProfile | Mapping[str, Any],
) -> str:
    data = _data(profile)
    payload = {
        "profile_version": data["profile_version"],
        "profile_schema_version": data["profile_schema_version"],
        "template_id": data["template_id"],
        "template_version": data["template_version"],
        "template_fingerprint": data["template_fingerprint"],
        "diagnostic_proposition_ref": data["diagnostic_proposition_ref"],
        "diagnostic_proposition_fingerprint": data["diagnostic_proposition_fingerprint"],
        "exact_slot_bindings": _sorted_models(data["exact_slot_bindings"], "slot"),
        "resolved_evidence_roles": sorted(_enum(value) for value in data["resolved_evidence_roles"]),
        "dimension_applicability_decisions": _sorted_models(
            data["dimension_applicability_decisions"], "dimension"
        ),
        "dependency_classifications": _sorted_models(data["dependency_classifications"], "requirement_ref"),
        "measurement_classifications": _sorted_models(data["measurement_classifications"], "requirement_ref"),
        "method_requirement_refs": sorted(data.get("method_requirement_refs", ())),
        "blocking_rules": sorted(data["blocking_rules"]),
        "qualification_rules": sorted(data.get("qualification_rules", ())),
        "narrowing_rules": sorted(data.get("narrowing_rules", ())),
    }
    return canonical_json_fingerprint(payload)


def _require_all_dimensions(requirements: tuple[DimensionRequirement, ...]) -> None:
    dimensions = [requirement.dimension for requirement in requirements]
    if len(set(dimensions)) != len(dimensions):
        raise ValueError("evidence dimensions must appear exactly once")
    missing = set(EvidenceDimension) - set(dimensions)
    if missing:
        names = ", ".join(sorted(item.value for item in missing))
        raise ValueError(f"all twelve evidence dimensions must be represented; missing: {names}")


def _data(value: ContractBase | Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(value, ContractBase):
        return value.model_dump(mode="python")
    return value


def _enum(value: Any) -> Any:
    return value.value if isinstance(value, Enum) else value


def _json(value: Any) -> Any:
    if isinstance(value, ContractBase):
        return value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return {key: _json(item) for key, item in value.items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_json(item) for item in value]
    return value


def _sorted_models(values: tuple[Any, ...] | list[Any], key: str) -> list[dict[str, Any]]:
    payloads = [_json(value) for value in values]
    return sorted(payloads, key=lambda item: _enum(item[key]))


__all__ = [
    "ApplicabilityLevel",
    "ApplicabilityState",
    "DependencyClassification",
    "DependencyRequirement",
    "DimensionRequirement",
    "EvidenceDimension",
    "EvidenceRole",
    "HypothesisFamilyRequirementTemplate",
    "MeasurementClassification",
    "MeasurementRequirement",
    "RequirementConsequence",
    "RequirementJudgment",
    "RequirementOutcome",
    "ResolvedRequiredEvidenceProfile",
    "SlotBinding",
    "requirement_template_semantic_fingerprint",
    "resolved_profile_semantic_fingerprint",
    "validate_profile_against_template",
]
