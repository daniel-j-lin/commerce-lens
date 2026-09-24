"""R6 proposal, provenance, governed wrapper, family, and R7 handoff contracts."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Mapping, Self

from pydantic import Field, field_validator, model_validator

from commerce_lens.contracts.common import ContractBase
from commerce_lens.contracts.diagnostic import EvidenceReadiness, TestEligibility
from commerce_lens.contracts.required_evidence import DependencyClassification
from commerce_lens.evidence.identifiers import canonical_json_fingerprint


SHA256_PATTERN = r"^[0-9a-f]{64}$"
CandidateScalar = str | int | float | bool | None


class CandidateSlot(ContractBase):
    slot: str = Field(min_length=1)
    value: CandidateScalar | tuple[CandidateScalar, ...]


class CandidateProposal(ContractBase):
    """Untrusted producer output. It contains no authority decisions."""

    family_id: str = Field(min_length=1)
    family_version: str = Field(min_length=1)
    structured_slot_values: tuple[CandidateSlot, ...] = Field(min_length=1)
    source_reference_proposals: tuple[str, ...] = ()
    display_template_id: str | None = None
    non_authoritative_wording: str | None = None

    @model_validator(mode="after")
    def unique_slots(self) -> Self:
        slots = [item.slot for item in self.structured_slot_values]
        if len(set(slots)) != len(slots):
            raise ValueError("structured_slot_values cannot contain duplicate slots")
        return self


class CandidateProposalBatch(ContractBase):
    batch_schema_version: str = Field(min_length=1)
    producer_ref: str = Field(min_length=1)
    generation_request_ref: str = Field(min_length=1)
    candidates: tuple[CandidateProposal, ...] = Field(min_length=1)


class GenerationParameters(ContractBase):
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    top_p: float | None = Field(default=None, gt=0.0, le=1.0)
    max_output_tokens: int | None = Field(default=None, ge=1, le=100_000)
    seed: int | None = Field(default=None, ge=0)


class GenerationProvenance(ContractBase):
    """Generation lineage only; never evidence supporting a hypothesis."""

    generation_provenance_id: str = Field(min_length=1)
    generator_id: str = Field(min_length=1)
    generator_version: str = Field(min_length=1)
    prompt_template_id: str = Field(min_length=1)
    prompt_template_version: str = Field(min_length=1)
    prompt_template_fingerprint: str = Field(pattern=SHA256_PATTERN)
    model_id: str | None = None
    generation_parameters: GenerationParameters
    raw_candidate_artifact_ref: str | None = None
    generated_at: datetime
    provenance_fingerprint: str = Field(pattern=SHA256_PATTERN)

    @field_validator("generated_at")
    @classmethod
    def generated_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_provenance_fingerprint(self) -> Self:
        if self.provenance_fingerprint != generation_provenance_semantic_fingerprint(self):
            raise ValueError("provenance_fingerprint does not match generation provenance")
        return self


class GovernedHypothesis(ContractBase):
    """Thin R6 aggregate containing references, never copied authority bodies."""

    governed_hypothesis_id: str = Field(min_length=1)
    governed_hypothesis_schema_version: str = Field(min_length=1)
    governed_hypothesis_fingerprint: str = Field(pattern=SHA256_PATTERN)
    diagnostic_proposition_ref: str = Field(min_length=1)
    diagnostic_proposition_fingerprint: str = Field(pattern=SHA256_PATTERN)
    pretest_evaluation_ref: str = Field(min_length=1)
    pretest_evaluation_fingerprint: str = Field(pattern=SHA256_PATTERN)
    resolved_profile_ref: str = Field(min_length=1)
    resolved_profile_fingerprint: str = Field(pattern=SHA256_PATTERN)
    generation_provenance_ref: str = Field(min_length=1)
    generation_provenance_fingerprint: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_wrapper_fingerprint(self) -> Self:
        if self.governed_hypothesis_fingerprint != governed_hypothesis_semantic_fingerprint(self):
            raise ValueError("governed_hypothesis_fingerprint does not match authority references")
        return self


class FamilyActivationPolicy(str, Enum):
    STANDARD = "STANDARD"
    EXPLICIT_USER_REQUEST_ONLY = "EXPLICIT_USER_REQUEST_ONLY"


class FamilyClassification(str, Enum):
    MVP = "MVP"
    MISSING_INTERNAL_EVIDENCE_ONLY = "MISSING_INTERNAL_EVIDENCE_ONLY"
    EXTERNAL_EVIDENCE_REQUIRED = "EXTERNAL_EVIDENCE_REQUIRED"


class HypothesisFamilyDefinition(ContractBase):
    family_id: str = Field(min_length=1)
    family_version: str = Field(min_length=1)
    family_fingerprint: str = Field(pattern=SHA256_PATTERN)
    classifications: tuple[FamilyClassification, ...] = Field(min_length=1)
    activation_policy: FamilyActivationPolicy
    requirement_template_ref: str = Field(min_length=1)
    requirement_template_version: str = Field(min_length=1)
    requirement_template_fingerprint: str = Field(pattern=SHA256_PATTERN)
    allowed_proposition_slots: tuple[str, ...] = Field(min_length=1)
    required_proposition_slots: tuple[str, ...] = Field(min_length=1)
    permitted_meanings: tuple[str, ...] = Field(min_length=1)
    prohibited_meanings: tuple[str, ...] = Field(min_length=1)
    dependency_classifications: tuple[DependencyClassification, ...] = Field(min_length=1)
    display_template_ids: tuple[str, ...] = Field(min_length=1)
    registry_can_establish_execution_eligibility: Literal[False] = False
    display_name: str | None = None

    @model_validator(mode="after")
    def validate_family(self) -> Self:
        if not set(self.required_proposition_slots).issubset(self.allowed_proposition_slots):
            raise ValueError("required proposition slots must be allowed")
        if self.family_fingerprint != hypothesis_family_semantic_fingerprint(self):
            raise ValueError("family_fingerprint does not match material family definition")
        return self


class R6ToR7Handoff(ContractBase):
    handoff_id: str = Field(min_length=1)
    handoff_schema_version: str = Field(min_length=1)
    handoff_fingerprint: str = Field(pattern=SHA256_PATTERN)
    diagnostic_proposition_ref: str = Field(min_length=1)
    diagnostic_proposition_fingerprint: str = Field(pattern=SHA256_PATTERN)
    pretest_evaluation_ref: str = Field(min_length=1)
    pretest_evaluation_fingerprint: str = Field(pattern=SHA256_PATTERN)
    family_id: str = Field(min_length=1)
    family_version: str = Field(min_length=1)
    family_fingerprint: str = Field(pattern=SHA256_PATTERN)
    resolved_profile_ref: str = Field(min_length=1)
    resolved_profile_version: str = Field(min_length=1)
    resolved_profile_fingerprint: str = Field(pattern=SHA256_PATTERN)
    scope_ref: str = Field(min_length=1)
    baseline_period_ref: str = Field(min_length=1)
    comparison_period_ref: str = Field(min_length=1)
    population_refs: tuple[str, ...] = Field(min_length=1)
    metric_refs: tuple[str, ...] = ()
    variable_refs: tuple[str, ...] = Field(min_length=1)
    source_observation_refs: tuple[str, ...] = Field(min_length=1)
    source_mechanical_result_refs: tuple[str, ...] = ()
    requirement_judgment_refs: tuple[str, ...] = Field(min_length=1)
    evidence_readiness: EvidenceReadiness
    missing_internal_requirement_refs: tuple[str, ...] = ()
    unmet_external_requirement_refs: tuple[str, ...] = ()
    method_ref: str | None = None
    method_version: str | None = None
    support_criterion_ref: str | None = None
    support_criterion_version: str | None = None
    validation_profile_ref: str | None = None
    validation_profile_version: str | None = None
    test_eligibility: TestEligibility
    first_controlling_blocker: str | None = None
    governed_hypothesis_ref: str = Field(min_length=1)
    governed_hypothesis_fingerprint: str = Field(pattern=SHA256_PATTERN)
    generation_provenance_ref: str = Field(min_length=1)

    @property
    def r7_execution_permitted(self) -> bool:
        return self.test_eligibility is TestEligibility.ELIGIBLE_NOT_EXECUTED

    @model_validator(mode="after")
    def validate_handoff(self) -> Self:
        _both_or_neither(self.method_ref, self.method_version, "method")
        _both_or_neither(self.support_criterion_ref, self.support_criterion_version, "support criterion")
        _both_or_neither(self.validation_profile_ref, self.validation_profile_version, "validation profile")
        if self.test_eligibility is TestEligibility.ELIGIBLE_NOT_EXECUTED:
            if self.evidence_readiness is not EvidenceReadiness.READY_FOR_TEST:
                raise ValueError("R7-eligible handoff requires READY_FOR_TEST")
            if self.first_controlling_blocker is not None:
                raise ValueError("R7-eligible handoff cannot contain a controlling blocker")
            if self.missing_internal_requirement_refs or self.unmet_external_requirement_refs:
                raise ValueError("R7-eligible handoff cannot contain unmet requirements")
        elif not self.first_controlling_blocker:
            raise ValueError("ineligible handoff requires first_controlling_blocker")
        if self.handoff_fingerprint != r6_to_r7_handoff_semantic_fingerprint(self):
            raise ValueError("handoff_fingerprint does not match handoff authority")
        return self


def generation_provenance_semantic_fingerprint(
    provenance: GenerationProvenance | Mapping[str, Any],
) -> str:
    data = _data(provenance)
    payload = {
        "generator_id": data["generator_id"],
        "generator_version": data["generator_version"],
        "prompt_template_id": data["prompt_template_id"],
        "prompt_template_version": data["prompt_template_version"],
        "prompt_template_fingerprint": data["prompt_template_fingerprint"],
        "model_id": data.get("model_id"),
        "generation_parameters": _json(data["generation_parameters"]),
        "raw_candidate_artifact_ref": data.get("raw_candidate_artifact_ref"),
        "generated_at": _datetime(data["generated_at"]),
    }
    return canonical_json_fingerprint(payload)


def governed_hypothesis_semantic_fingerprint(
    hypothesis: GovernedHypothesis | Mapping[str, Any],
) -> str:
    data = _data(hypothesis)
    payload = {
        "governed_hypothesis_schema_version": data["governed_hypothesis_schema_version"],
        "diagnostic_proposition_ref": data["diagnostic_proposition_ref"],
        "diagnostic_proposition_fingerprint": data["diagnostic_proposition_fingerprint"],
        "pretest_evaluation_ref": data["pretest_evaluation_ref"],
        "pretest_evaluation_fingerprint": data["pretest_evaluation_fingerprint"],
        "resolved_profile_ref": data["resolved_profile_ref"],
        "resolved_profile_fingerprint": data["resolved_profile_fingerprint"],
        "generation_provenance_ref": data["generation_provenance_ref"],
        "generation_provenance_fingerprint": data["generation_provenance_fingerprint"],
    }
    return canonical_json_fingerprint(payload)


def hypothesis_family_semantic_fingerprint(
    family: HypothesisFamilyDefinition | Mapping[str, Any],
) -> str:
    data = _data(family)
    payload = {
        "family_id": data["family_id"],
        "family_version": data["family_version"],
        "classifications": sorted(_enum(item) for item in data["classifications"]),
        "activation_policy": _enum(data["activation_policy"]),
        "requirement_template_ref": data["requirement_template_ref"],
        "requirement_template_version": data["requirement_template_version"],
        "requirement_template_fingerprint": data["requirement_template_fingerprint"],
        "allowed_proposition_slots": sorted(data["allowed_proposition_slots"]),
        "required_proposition_slots": sorted(data["required_proposition_slots"]),
        "permitted_meanings": sorted(data["permitted_meanings"]),
        "prohibited_meanings": sorted(data["prohibited_meanings"]),
        "dependency_classifications": sorted(_enum(item) for item in data["dependency_classifications"]),
        "display_template_ids": sorted(data["display_template_ids"]),
        "registry_can_establish_execution_eligibility": False,
    }
    return canonical_json_fingerprint(payload)


def r6_to_r7_handoff_semantic_fingerprint(
    handoff: R6ToR7Handoff | Mapping[str, Any],
) -> str:
    data = _data(handoff)
    ordered_fields = (
        "handoff_schema_version",
        "diagnostic_proposition_ref",
        "diagnostic_proposition_fingerprint",
        "pretest_evaluation_ref",
        "pretest_evaluation_fingerprint",
        "family_id",
        "family_version",
        "family_fingerprint",
        "resolved_profile_ref",
        "resolved_profile_version",
        "resolved_profile_fingerprint",
        "scope_ref",
        "baseline_period_ref",
        "comparison_period_ref",
        "evidence_readiness",
        "method_ref",
        "method_version",
        "support_criterion_ref",
        "support_criterion_version",
        "validation_profile_ref",
        "validation_profile_version",
        "test_eligibility",
        "first_controlling_blocker",
        "governed_hypothesis_ref",
        "governed_hypothesis_fingerprint",
        "generation_provenance_ref",
    )
    payload = {field: _enum(data.get(field)) for field in ordered_fields}
    for field in (
        "population_refs",
        "metric_refs",
        "variable_refs",
        "source_observation_refs",
        "source_mechanical_result_refs",
        "requirement_judgment_refs",
        "missing_internal_requirement_refs",
        "unmet_external_requirement_refs",
    ):
        payload[field] = sorted(data.get(field, ()))
    return canonical_json_fingerprint(payload)


def _both_or_neither(reference: str | None, version: str | None, label: str) -> None:
    if (reference is None) != (version is None):
        raise ValueError(f"{label} reference and version must be provided together")


def _data(value: ContractBase | Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(value, ContractBase):
        return value.model_dump(mode="python")
    return value


def _json(value: Any) -> Any:
    if isinstance(value, ContractBase):
        return value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return {key: _json(item) for key, item in value.items()}
    if isinstance(value, Enum):
        return value.value
    return value


def _enum(value: Any) -> Any:
    return value.value if isinstance(value, Enum) else value


def _datetime(value: datetime | str) -> str:
    return value.isoformat() if isinstance(value, datetime) else value


__all__ = [
    "CandidateProposal",
    "CandidateProposalBatch",
    "CandidateSlot",
    "FamilyActivationPolicy",
    "FamilyClassification",
    "GenerationParameters",
    "GenerationProvenance",
    "GovernedHypothesis",
    "HypothesisFamilyDefinition",
    "R6ToR7Handoff",
    "generation_provenance_semantic_fingerprint",
    "governed_hypothesis_semantic_fingerprint",
    "hypothesis_family_semantic_fingerprint",
    "r6_to_r7_handoff_semantic_fingerprint",
]
