"""R2 diagnostic proposition and finalized pre-test evaluation contracts."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Mapping, Self

from pydantic import Field, field_validator, model_validator

from commerce_lens.contracts.common import ContractBase
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, stable_content_id


SHA256_PATTERN = r"^[0-9a-f]{64}$"


class RelationshipType(str, Enum):
    ASSOCIATION = "association"
    PATTERN = "pattern"
    SEGMENT_DIFFERENCE = "segment_difference"
    INTERPRETATION = "interpretation"


class RelationshipDirection(str, Enum):
    UNSPECIFIED = "unspecified"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    DIFFERENT = "different"


class StructuredRelationship(ContractBase):
    """Structured material relationship semantics; never free-form identity."""

    relationship_type: RelationshipType
    direction: RelationshipDirection = RelationshipDirection.UNSPECIFIED
    comparison_basis: str = Field(min_length=1)
    bounded_strength: str = Field(min_length=1)


class AuthorityBinding(ContractBase):
    authority_ref: str = Field(min_length=1)
    authority_version: str = Field(min_length=1)
    authority_fingerprint: str = Field(pattern=SHA256_PATTERN)


class EvidenceReadiness(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    MISSING_INTERNAL_EVIDENCE = "MISSING_INTERNAL_EVIDENCE"
    EXTERNAL_EVIDENCE_REQUIRED = "EXTERNAL_EVIDENCE_REQUIRED"
    READY_FOR_TEST = "READY_FOR_TEST"


class TestEligibility(str, Enum):
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    ELIGIBLE_NOT_EXECUTED = "ELIGIBLE_NOT_EXECUTED"


class AnalyticalOutcome(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"
    CRITERION_MET = "CRITERION_MET"
    CRITERION_NOT_MET = "CRITERION_NOT_MET"
    PROPOSITION_CONTRADICTED = "PROPOSITION_CONTRADICTED"


class AlternativeExplanationState(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"


class DiagnosticProposition(ContractBase):
    """Exact, immutable R2 proposition identity."""

    proposition_id: str = Field(min_length=1)
    proposition_schema_version: str = Field(min_length=1)
    semantic_fingerprint: str = Field(pattern=SHA256_PATTERN)

    family_id: str = Field(min_length=1)
    family_version: str = Field(min_length=1)
    family_fingerprint: str = Field(pattern=SHA256_PATTERN)

    relationship: StructuredRelationship
    outcome_ref: str = Field(min_length=1)
    scope_ref: str = Field(min_length=1)
    baseline_period_ref: str = Field(min_length=1)
    comparison_period_ref: str = Field(min_length=1)
    baseline_population_ref: str = Field(min_length=1)
    comparison_population_ref: str = Field(min_length=1)
    metric_refs: tuple[str, ...] = ()
    variable_refs: tuple[str, ...] = Field(min_length=1)
    source_observation_refs: tuple[str, ...] = Field(min_length=1)
    source_mechanical_result_refs: tuple[str, ...] = ()
    intended_use: Literal["diagnostic"] = "diagnostic"
    maximum_permitted_meaning: str = Field(min_length=1)
    prohibited_meanings: tuple[str, ...] = Field(min_length=1)
    authority_bindings: tuple[AuthorityBinding, ...] = Field(min_length=1)

    # Non-material metadata. It is deliberately excluded from identity.
    display_wording: str | None = None
    display_label: str | None = None

    @model_validator(mode="after")
    def validate_semantic_fingerprint(self) -> Self:
        expected = diagnostic_proposition_semantic_fingerprint(self)
        if self.semantic_fingerprint != expected:
            raise ValueError("semantic_fingerprint does not match material proposition identity")
        if self.proposition_id != stable_content_id("diagprop", expected):
            raise ValueError("proposition_id must be the stable ID for material proposition identity")
        return self


class PreTestDiagnosticEvaluation(ContractBase):
    """Finalized R2 pre-test judgment bound to exact R2/R3 authorities."""

    evaluation_id: str = Field(min_length=1)
    evaluation_schema_version: str = Field(min_length=1)
    evaluation_fingerprint: str = Field(pattern=SHA256_PATTERN)

    diagnostic_proposition_ref: str = Field(min_length=1)
    diagnostic_proposition_fingerprint: str = Field(pattern=SHA256_PATTERN)
    resolved_profile_ref: str = Field(min_length=1)
    resolved_profile_version: str = Field(min_length=1)
    resolved_profile_fingerprint: str = Field(pattern=SHA256_PATTERN)
    requirement_judgment_bundle_ref: str = Field(min_length=1)
    requirement_judgment_bundle_fingerprint: str = Field(pattern=SHA256_PATTERN)

    evidence_readiness: EvidenceReadiness
    test_eligibility: TestEligibility
    first_controlling_blocker: str | None = None
    analytical_outcome: AnalyticalOutcome = AnalyticalOutcome.NOT_EVALUATED
    alternative_explanation_state: AlternativeExplanationState = AlternativeExplanationState.NOT_EVALUATED
    authority_bindings: tuple[AuthorityBinding, ...] = Field(min_length=1)
    finalized_at: datetime

    @field_validator("finalized_at")
    @classmethod
    def finalized_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("finalized_at must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_pretest_boundary(self) -> Self:
        if self.analytical_outcome is not AnalyticalOutcome.NOT_EVALUATED:
            raise ValueError("pre-test evaluation cannot contain a tested analytical outcome")
        if self.alternative_explanation_state is not AlternativeExplanationState.NOT_EVALUATED:
            raise ValueError("pre-test evaluation cannot contain a tested alternative-explanation state")
        if self.test_eligibility is TestEligibility.ELIGIBLE_NOT_EXECUTED:
            if self.evidence_readiness is not EvidenceReadiness.READY_FOR_TEST:
                raise ValueError("eligible pre-test evaluation requires READY_FOR_TEST evidence readiness")
            if self.first_controlling_blocker is not None:
                raise ValueError("eligible pre-test evaluation cannot contain a controlling blocker")
        elif not self.first_controlling_blocker:
            raise ValueError("ineligible pre-test evaluation requires first_controlling_blocker")
        expected = pretest_evaluation_semantic_fingerprint(self)
        if self.evaluation_fingerprint != expected:
            raise ValueError("evaluation_fingerprint does not match material pre-test authority")
        return self


def diagnostic_proposition_semantic_fingerprint(
    proposition: DiagnosticProposition | Mapping[str, Any],
) -> str:
    data = _data(proposition)
    relationship = _json(data["relationship"])
    authority_bindings = sorted(
        (_json(binding) for binding in data["authority_bindings"]),
        key=lambda item: (
            item["authority_ref"],
            item["authority_version"],
            item["authority_fingerprint"],
        ),
    )
    payload = {
        "proposition_schema_version": data["proposition_schema_version"],
        "family_id": data["family_id"],
        "family_version": data["family_version"],
        "family_fingerprint": data["family_fingerprint"],
        "relationship": relationship,
        "outcome_ref": data["outcome_ref"],
        "scope_ref": data["scope_ref"],
        "baseline_period_ref": data["baseline_period_ref"],
        "comparison_period_ref": data["comparison_period_ref"],
        "baseline_population_ref": data["baseline_population_ref"],
        "comparison_population_ref": data["comparison_population_ref"],
        "metric_refs": sorted(data.get("metric_refs", ())),
        "variable_refs": sorted(data["variable_refs"]),
        "source_observation_refs": sorted(data["source_observation_refs"]),
        "source_mechanical_result_refs": sorted(data.get("source_mechanical_result_refs", ())),
        "intended_use": _enum(data.get("intended_use", "diagnostic")),
        "maximum_permitted_meaning": data["maximum_permitted_meaning"],
        "prohibited_meanings": sorted(data["prohibited_meanings"]),
        "authority_bindings": authority_bindings,
    }
    return canonical_json_fingerprint(payload)


def pretest_evaluation_semantic_fingerprint(
    evaluation: PreTestDiagnosticEvaluation | Mapping[str, Any],
) -> str:
    data = _data(evaluation)
    payload = {
        "evaluation_schema_version": data["evaluation_schema_version"],
        "diagnostic_proposition_ref": data["diagnostic_proposition_ref"],
        "diagnostic_proposition_fingerprint": data["diagnostic_proposition_fingerprint"],
        "resolved_profile_ref": data["resolved_profile_ref"],
        "resolved_profile_version": data["resolved_profile_version"],
        "resolved_profile_fingerprint": data["resolved_profile_fingerprint"],
        "requirement_judgment_bundle_ref": data["requirement_judgment_bundle_ref"],
        "requirement_judgment_bundle_fingerprint": data["requirement_judgment_bundle_fingerprint"],
        "evidence_readiness": _enum(data["evidence_readiness"]),
        "test_eligibility": _enum(data["test_eligibility"]),
        "first_controlling_blocker": data.get("first_controlling_blocker"),
        "analytical_outcome": _enum(data.get("analytical_outcome", AnalyticalOutcome.NOT_EVALUATED)),
        "alternative_explanation_state": _enum(
            data.get("alternative_explanation_state", AlternativeExplanationState.NOT_EVALUATED)
        ),
        "authority_bindings": sorted(
            (_json(binding) for binding in data["authority_bindings"]),
            key=lambda item: (
                item["authority_ref"],
                item["authority_version"],
                item["authority_fingerprint"],
            ),
        ),
        "finalized_at": _datetime(data["finalized_at"]),
    }
    return canonical_json_fingerprint(payload)


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
    "AlternativeExplanationState",
    "AnalyticalOutcome",
    "AuthorityBinding",
    "DiagnosticProposition",
    "EvidenceReadiness",
    "PreTestDiagnosticEvaluation",
    "RelationshipDirection",
    "RelationshipType",
    "StructuredRelationship",
    "TestEligibility",
    "diagnostic_proposition_semantic_fingerprint",
    "pretest_evaluation_semantic_fingerprint",
]
