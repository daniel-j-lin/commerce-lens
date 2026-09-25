"""Private R6-4 candidate-generation boundary and deterministic proposition builder."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from pydantic import Field, model_validator

from commerce_lens.contracts.common import ContractBase
from commerce_lens.contracts.diagnostic import (
    AuthorityBinding,
    DiagnosticProposition,
    RelationshipDirection,
    RelationshipType,
    StructuredRelationship,
    diagnostic_proposition_semantic_fingerprint,
)
from commerce_lens.contracts.hypotheses import (
    CandidateProposal,
    CandidateProposalBatch,
    GenerationParameters,
)
from commerce_lens.contracts.required_evidence import DependencyClassification
from commerce_lens.diagnostic.family_registry import MVP_FAMILY_REGISTRY
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, stable_content_id


GENERATION_REQUEST_SCHEMA_VERSION = "1.0.0"
GENERATION_CONTEXT_SCHEMA_VERSION = "1.0.0"
CANDIDATE_BATCH_SCHEMA_VERSION = "1.0.0"
PROPOSITION_SCHEMA_VERSION = "1.0.0"
INTENDED_USE_AUTHORITY_REF = "R2_HYPOTHESIS_FINDING_STATE_MODEL"
INTENDED_USE_AUTHORITY_VERSION = "1.0.0"
INTENDED_USE_AUTHORITY_FINGERPRINT = canonical_json_fingerprint(
    {
        "authority_ref": INTENDED_USE_AUTHORITY_REF,
        "authority_version": INTENDED_USE_AUTHORITY_VERSION,
        "intended_use": "diagnostic",
    }
)


class GenerationBoundaryError(ValueError):
    """Deterministic generation-boundary failure; never an analytical state."""

    def __init__(self, code: str, message: str, *, candidate_fingerprint: str | None = None) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.candidate_fingerprint = candidate_fingerprint


class SourceAuthorityClass(str, Enum):
    METRIC = "METRIC"
    VARIABLE = "VARIABLE"
    SOURCE_REFERENCE = "SOURCE_REFERENCE"
    ACTIVATION = "ACTIVATION"
    MECHANICAL_RESULT = "MECHANICAL_RESULT"


class FamilyActivation(ContractBase):
    """Structured orchestration activation. It is not Evidence."""

    family_id: str = Field(min_length=1)
    activation_ref: str = Field(min_length=1)
    external_factor_ref: str | None = Field(default=None, min_length=1)
    external_dependency_ref: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_external_shape(self) -> "FamilyActivation":
        if self.family_id == "external_market_association":
            if self.external_factor_ref is None or self.external_dependency_ref is None:
                raise ValueError("external activation requires structured factor and dependency references")
        elif self.external_factor_ref is not None or self.external_dependency_ref is not None:
            raise ValueError("external activation fields are reserved for external_market_association")
        return self


class R6GenerationRequest(ContractBase):
    """Private orchestration/activation request; never evidence or analytical authority."""

    generation_request_ref: str = Field(min_length=1)
    generation_request_schema_version: str = GENERATION_REQUEST_SCHEMA_VERSION
    analysis_request_ref: str = Field(min_length=1)
    requested_family_ids: tuple[str, ...] = ()
    family_activations: tuple[FamilyActivation, ...] = ()
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_identity(self) -> "R6GenerationRequest":
        if len(self.requested_family_ids) != len(set(self.requested_family_ids)):
            raise ValueError("requested_family_ids must be unique")
        activation_ids = [item.family_id for item in self.family_activations]
        if len(activation_ids) != len(set(activation_ids)):
            raise ValueError("family activations must be unique by family")
        expected = generation_request_fingerprint(self)
        if self.request_fingerprint != expected:
            raise ValueError("request_fingerprint does not match R6 generation request")
        if self.generation_request_ref != stable_content_id("r6genreq", expected):
            raise ValueError("generation_request_ref must be the stable request identity")
        return self


class CandidateProducerDescriptor(ContractBase):
    """Trusted adapter metadata used only for identity checks and generation provenance."""

    producer_id: str = Field(min_length=1)
    producer_version: str = Field(min_length=1)
    template_id: str = Field(min_length=1)
    template_version: str = Field(min_length=1)
    template_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    model_id: str | None = None
    generation_parameters: GenerationParameters = Field(default_factory=GenerationParameters)


class CandidateFamilyView(ContractBase):
    family_id: str = Field(min_length=1)
    family_version: str = Field(min_length=1)
    family_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    allowed_slots: tuple[str, ...] = Field(min_length=1)
    required_slots: tuple[str, ...] = Field(min_length=1)
    display_template_ids: tuple[str, ...] = Field(min_length=1)


class AllowedSlotBinding(ContractBase):
    family_id: str = Field(min_length=1)
    slot: str = Field(min_length=1)
    allowed_refs: tuple[str, ...] = Field(min_length=1)
    semantically_unordered: bool = False


class SourceAuthorityView(ContractBase):
    authority_ref: str = Field(min_length=1)
    authority_version: str = Field(min_length=1)
    authority_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    authority_class: SourceAuthorityClass
    dependency_classification: DependencyClassification | None = None
    intended_uses: tuple[str, ...] = ()
    scope_ref: str | None = None
    baseline_period_ref: str | None = None
    comparison_period_ref: str | None = None
    baseline_population_ref: str | None = None
    comparison_population_ref: str | None = None


class CandidateGenerationContext(ContractBase):
    """Minimal immutable producer view containing only closed, authenticated references."""

    context_id: str = Field(min_length=1)
    context_schema_version: str = GENERATION_CONTEXT_SCHEMA_VERSION
    context_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    generation_request_ref: str = Field(min_length=1)
    analysis_request_ref: str = Field(min_length=1)
    outcome_metric_ref: str = Field(min_length=1)
    outcome_validated_result_ref: str = Field(min_length=1)
    scope_ref: str = Field(min_length=1)
    baseline_period_ref: str = Field(min_length=1)
    comparison_period_ref: str = Field(min_length=1)
    baseline_population_ref: str = Field(min_length=1)
    comparison_population_ref: str = Field(min_length=1)
    permitted_family_views: tuple[CandidateFamilyView, ...] = Field(min_length=1)
    allowed_slot_bindings: tuple[AllowedSlotBinding, ...] = Field(min_length=1)
    source_authority_views: tuple[SourceAuthorityView, ...] = Field(min_length=1)
    requested_family_ids: tuple[str, ...] = ()
    family_activations: tuple[FamilyActivation, ...] = ()
    source_mechanical_result_ref: str | None = None

    @model_validator(mode="after")
    def validate_identity(self) -> "CandidateGenerationContext":
        expected = candidate_generation_context_fingerprint(self)
        if self.context_fingerprint != expected:
            raise ValueError("context_fingerprint does not match candidate generation context")
        if self.context_id != stable_content_id("r6ctx", expected):
            raise ValueError("context_id must be the stable context identity")
        if len(self.requested_family_ids) != len(set(self.requested_family_ids)):
            raise ValueError("requested family IDs must be unique")
        return self


@runtime_checkable
class CandidateProducer(Protocol):
    def produce_candidates(self, context: CandidateGenerationContext) -> CandidateProposalBatch:
        """Return untrusted bounded proposal material."""


class CandidateDiagnostic(ContractBase):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    candidate_fingerprint: str | None = None
    family_id: str | None = None
    duplicate_of_proposition_ref: str | None = None


@dataclass(frozen=True)
class ConstructedCandidate:
    candidate: CandidateProposal
    candidate_fingerprint: str
    proposition: DiagnosticProposition
    duplicate_candidate_fingerprints: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProposalValidationResult:
    accepted: tuple[ConstructedCandidate, ...]
    diagnostics: tuple[CandidateDiagnostic, ...]
    requested_family_omissions: tuple[str, ...]


def generation_request_fingerprint(request: R6GenerationRequest | dict[str, Any]) -> str:
    data = request.model_dump(mode="json") if isinstance(request, R6GenerationRequest) else _jsonable(request)
    return canonical_json_fingerprint(
        {
            "generation_request_schema_version": data["generation_request_schema_version"],
            "analysis_request_ref": data["analysis_request_ref"],
            "requested_family_ids": sorted(data.get("requested_family_ids", ())),
            "family_activations": sorted(
                data.get("family_activations", ()),
                key=lambda item: item["family_id"],
            ),
        }
    )


def build_generation_request(
    *,
    analysis_request_ref: str,
    requested_family_ids: tuple[str, ...] = (),
    family_activations: tuple[FamilyActivation, ...] = (),
) -> R6GenerationRequest:
    data: dict[str, Any] = {
        "generation_request_ref": "pending",
        "generation_request_schema_version": GENERATION_REQUEST_SCHEMA_VERSION,
        "analysis_request_ref": analysis_request_ref,
        "requested_family_ids": tuple(sorted(requested_family_ids)),
        "family_activations": tuple(sorted(family_activations, key=lambda item: item.family_id)),
    }
    data["request_fingerprint"] = generation_request_fingerprint(data)
    data["generation_request_ref"] = stable_content_id("r6genreq", data["request_fingerprint"])
    return R6GenerationRequest(**data)


def candidate_generation_context_fingerprint(
    context: CandidateGenerationContext | dict[str, Any],
) -> str:
    data = context.model_dump(mode="json") if isinstance(context, CandidateGenerationContext) else _jsonable(context)
    payload = {
        key: data.get(key)
        for key in (
            "context_schema_version",
            "generation_request_ref",
            "analysis_request_ref",
            "outcome_metric_ref",
            "outcome_validated_result_ref",
            "scope_ref",
            "baseline_period_ref",
            "comparison_period_ref",
            "baseline_population_ref",
            "comparison_population_ref",
            "source_mechanical_result_ref",
        )
    }
    payload["permitted_family_views"] = sorted(
        data["permitted_family_views"], key=lambda item: item["family_id"]
    )
    payload["allowed_slot_bindings"] = sorted(
        data["allowed_slot_bindings"], key=lambda item: (item["family_id"], item["slot"])
    )
    payload["source_authority_views"] = sorted(
        data["source_authority_views"], key=lambda item: (item["authority_class"], item["authority_ref"])
    )
    payload["requested_family_ids"] = sorted(data.get("requested_family_ids", ()))
    payload["family_activations"] = sorted(
        data.get("family_activations", ()), key=lambda item: item["family_id"]
    )
    return canonical_json_fingerprint(payload)


def build_candidate_generation_context(**fields: Any) -> CandidateGenerationContext:
    data = {
        "context_id": "pending",
        "context_schema_version": GENERATION_CONTEXT_SCHEMA_VERSION,
        **fields,
    }
    data["context_fingerprint"] = candidate_generation_context_fingerprint(data)
    data["context_id"] = stable_content_id("r6ctx", data["context_fingerprint"])
    return CandidateGenerationContext(**data)


def validate_candidate_batch(
    raw_batch: Any,
    *,
    descriptor: CandidateProducerDescriptor,
    context: CandidateGenerationContext,
) -> CandidateProposalBatch:
    if isinstance(raw_batch, dict) and raw_batch.get("candidates") in ((), []):
        raise GenerationBoundaryError("empty_batch", "candidate batch cannot be empty")
    try:
        if isinstance(raw_batch, CandidateProposalBatch):
            batch = CandidateProposalBatch.model_validate(raw_batch.model_dump(mode="python"))
        else:
            batch = CandidateProposalBatch.model_validate(raw_batch)
    except Exception as exc:
        raise GenerationBoundaryError("malformed_batch", "producer returned an invalid candidate batch") from exc
    if batch.batch_schema_version != CANDIDATE_BATCH_SCHEMA_VERSION:
        raise GenerationBoundaryError("batch_schema_version_mismatch", "candidate batch schema version is unsupported")
    if batch.producer_ref != descriptor.producer_id:
        raise GenerationBoundaryError("producer_identity_mismatch", "batch producer identity does not match trusted descriptor")
    if batch.generation_request_ref != context.generation_request_ref:
        raise GenerationBoundaryError("generation_request_mismatch", "batch generation request does not match context")
    return batch


def candidate_fingerprint(candidate: CandidateProposal) -> str:
    """Raw proposal identity for audit, not proposition identity or rank."""

    return canonical_json_fingerprint(candidate.model_dump(mode="json"))


def validate_and_construct_propositions(
    batch: CandidateProposalBatch,
    context: CandidateGenerationContext,
) -> ProposalValidationResult:
    accepted_by_id: dict[str, list[ConstructedCandidate]] = {}
    diagnostics: list[CandidateDiagnostic] = []
    for candidate in batch.candidates:
        raw_fingerprint = candidate_fingerprint(candidate)
        try:
            normalized = _normalize_and_validate_candidate(candidate, context, raw_fingerprint)
            proposition = _construct_proposition(normalized, context)
        except GenerationBoundaryError as exc:
            diagnostics.append(
                CandidateDiagnostic(
                    code=exc.code,
                    message=str(exc),
                    candidate_fingerprint=raw_fingerprint,
                    family_id=candidate.family_id,
                )
            )
            continue
        accepted_by_id.setdefault(proposition.proposition_id, []).append(
            ConstructedCandidate(normalized, raw_fingerprint, proposition)
        )

    accepted: list[ConstructedCandidate] = []
    for proposition_id in sorted(accepted_by_id):
        group = sorted(accepted_by_id[proposition_id], key=lambda item: item.candidate_fingerprint)
        representative = group[0]
        duplicates = tuple(item.candidate_fingerprint for item in group[1:])
        accepted.append(
            ConstructedCandidate(
                representative.candidate,
                representative.candidate_fingerprint,
                representative.proposition,
                duplicates,
            )
        )
        diagnostics.extend(
            CandidateDiagnostic(
                code="duplicate_candidate",
                message="raw proposal maps to an already retained governed proposition",
                candidate_fingerprint=item.candidate_fingerprint,
                family_id=item.candidate.family_id,
                duplicate_of_proposition_ref=proposition_id,
            )
            for item in group[1:]
        )

    accepted_families = {item.proposition.family_id for item in accepted}
    omissions = tuple(sorted(set(context.requested_family_ids) - accepted_families))
    diagnostics.extend(
        CandidateDiagnostic(
            code="requested_family_omitted",
            message=f"requested family has no accepted proposition: {family_id}",
            family_id=family_id,
        )
        for family_id in omissions
    )
    return ProposalValidationResult(tuple(accepted), tuple(diagnostics), omissions)


def _normalize_and_validate_candidate(
    candidate: CandidateProposal,
    context: CandidateGenerationContext,
    raw_fingerprint: str,
) -> CandidateProposal:
    family_views = {item.family_id: item for item in context.permitted_family_views}
    family_view = family_views.get(candidate.family_id)
    if family_view is None:
        known = {item.family_id for item in MVP_FAMILY_REGISTRY.active_families}
        code = "disallowed_family" if candidate.family_id in known else "unknown_family"
        raise GenerationBoundaryError(code, f"family is not permitted: {candidate.family_id}", candidate_fingerprint=raw_fingerprint)
    if candidate.family_version != family_view.family_version:
        raise GenerationBoundaryError("wrong_family_version", "candidate family version is not current")
    current_family = MVP_FAMILY_REGISTRY.get_family(candidate.family_id, candidate.family_version)
    if (
        family_view.family_fingerprint != current_family.family_fingerprint
        or set(family_view.allowed_slots) != set(current_family.allowed_proposition_slots)
        or set(family_view.required_slots) != set(current_family.required_proposition_slots)
        or set(family_view.display_template_ids) != set(current_family.display_template_ids)
    ):
        raise GenerationBoundaryError("stale_family_authority", "candidate context family authority is not current")
    try:
        MVP_FAMILY_REGISTRY.validate_candidate(candidate)
    except ValueError as exc:
        message = str(exc)
        code = "invented_slot" if "unsupported proposition slots" in message else "missing_required_slot"
        if "product_name" in message:
            code = "forbidden_product_name_identity"
        elif "discount authority" in message:
            code = "forbidden_discount_substitution"
        elif "explicit user-request" in message:
            code = "external_activation_missing"
        raise GenerationBoundaryError(code, message) from exc

    values = {item.slot: item.value for item in candidate.structured_slot_values}
    expected_common = {
        "outcome_ref": context.outcome_metric_ref,
        "scope_ref": context.scope_ref,
        "baseline_period_ref": context.baseline_period_ref,
        "comparison_period_ref": context.comparison_period_ref,
        "baseline_population_ref": context.baseline_population_ref,
        "comparison_population_ref": context.comparison_population_ref,
    }
    mismatch_codes = {
        "outcome_ref": "invented_metric",
        "scope_ref": "scope_mismatch",
        "baseline_period_ref": "period_mismatch",
        "comparison_period_ref": "period_mismatch",
        "baseline_population_ref": "population_mismatch",
        "comparison_population_ref": "population_mismatch",
    }
    for slot, expected in expected_common.items():
        if not _equivalent(values.get(slot), expected):
            raise GenerationBoundaryError(mismatch_codes[slot], f"candidate {slot} does not match context")

    options = {
        (item.family_id, item.slot): item
        for item in context.allowed_slot_bindings
    }
    for slot, value in values.items():
        option = options.get((candidate.family_id, slot))
        if option is None:
            raise GenerationBoundaryError("invented_slot", f"slot is not available in context: {slot}")
        proposed = _as_refs(value)
        if not set(proposed).issubset(option.allowed_refs):
            if slot == "source_observation_refs" and context.source_mechanical_result_ref in proposed:
                raise GenerationBoundaryError(
                    "r4_support_claim_forbidden",
                    "R4 mechanical result cannot be proposed as observation support",
                )
            code = _reference_failure_code(slot, proposed)
            raise GenerationBoundaryError(code, f"slot contains an untrusted reference: {slot}")

    activations = {item.family_id: item for item in context.family_activations}
    if candidate.family_id == "external_market_association":
        activation = activations.get(candidate.family_id)
        if activation is None or values.get("explicit_activation_ref") != activation.activation_ref:
            raise GenerationBoundaryError("external_activation_missing", "external proposal lacks exact structured activation")

    observation_refs = tuple(sorted(_as_refs(values["source_observation_refs"])))
    proposed_refs = tuple(sorted(set(candidate.source_reference_proposals)))
    expected_source_proposals = set(observation_refs)
    if "optional_r4_result_ref" in values:
        expected_source_proposals.add(str(values["optional_r4_result_ref"]))
    if set(proposed_refs) != expected_source_proposals:
        raise GenerationBoundaryError("source_proposal_mismatch", "source-reference proposals do not match material source slots")

    authority_by_ref = {item.authority_ref: item for item in context.source_authority_views}
    for reference in observation_refs:
        authority = authority_by_ref.get(reference)
        if authority is None:
            raise GenerationBoundaryError("invented_source_reference", f"source is not authenticated: {reference}")
        if authority.authority_class is not SourceAuthorityClass.SOURCE_REFERENCE:
            raise GenerationBoundaryError("wrong_source_class", f"reference is not an observation source: {reference}")
        if "diagnostic_candidate_source" not in authority.intended_uses:
            raise GenerationBoundaryError("stale_source_authority", f"source is not current for candidate use: {reference}")
        _require_context_alignment(authority, context)

    if "optional_r4_result_ref" in values:
        r4_ref = str(values["optional_r4_result_ref"])
        authority = authority_by_ref.get(r4_ref)
        if (
            context.source_mechanical_result_ref != r4_ref
            or authority is None
            or authority.authority_class is not SourceAuthorityClass.MECHANICAL_RESULT
            or "mechanical_reference_only" not in authority.intended_uses
        ):
            raise GenerationBoundaryError("r4_support_claim_forbidden", "R4 may only be an authenticated mechanical reference")

    normalized_slots = []
    for item in sorted(candidate.structured_slot_values, key=lambda entry: entry.slot):
        option = options[(candidate.family_id, item.slot)]
        value = item.value
        if option.semantically_unordered and isinstance(value, tuple):
            value = tuple(sorted(set(value), key=lambda entry: str(entry)))
        normalized_slots.append(item.model_copy(update={"value": value}))
    return candidate.model_copy(
        update={
            "structured_slot_values": tuple(normalized_slots),
            "source_reference_proposals": proposed_refs,
        }
    )


def _construct_proposition(
    candidate: CandidateProposal,
    context: CandidateGenerationContext,
) -> DiagnosticProposition:
    family = MVP_FAMILY_REGISTRY.get_family(candidate.family_id, candidate.family_version)
    template = MVP_FAMILY_REGISTRY.get_requirement_template(candidate.family_id)
    values = {item.slot: item.value for item in candidate.structured_slot_values}
    variable_slots = {
        "product_identity_ref",
        "monetary_observation_ref",
        "original_or_list_price_ref",
        "discount_semantics_ref",
        "external_factor_ref",
    }
    variables = tuple(sorted({str(values[slot]) for slot in variable_slots & values.keys()}))
    observations = tuple(sorted(_as_refs(values["source_observation_refs"])))
    mechanical = (
        (str(values["optional_r4_result_ref"]),)
        if "optional_r4_result_ref" in values
        else ()
    )
    authority_bindings = [
        AuthorityBinding(
            authority_ref=INTENDED_USE_AUTHORITY_REF,
            authority_version=INTENDED_USE_AUTHORITY_VERSION,
            authority_fingerprint=INTENDED_USE_AUTHORITY_FINGERPRINT,
        )
    ]
    if candidate.family_id == "external_market_association":
        activation_ref = str(values["explicit_activation_ref"])
        activation_view = next(
            item for item in context.source_authority_views if item.authority_ref == activation_ref
        )
        authority_bindings.append(
            AuthorityBinding(
                authority_ref=activation_view.authority_ref,
                authority_version=activation_view.authority_version,
                authority_fingerprint=activation_view.authority_fingerprint,
            )
        )
    data: dict[str, Any] = {
        "proposition_id": "pending",
        "proposition_schema_version": PROPOSITION_SCHEMA_VERSION,
        "family_id": family.family_id,
        "family_version": family.family_version,
        "family_fingerprint": family.family_fingerprint,
        "relationship": StructuredRelationship(
            relationship_type=RelationshipType.ASSOCIATION,
            direction=RelationshipDirection.UNSPECIFIED,
            comparison_basis="governed baseline period versus governed comparison period",
            bounded_strength="bounded non-causal association proposed for future testing",
        ),
        "outcome_ref": context.outcome_metric_ref,
        "scope_ref": context.scope_ref,
        "baseline_period_ref": context.baseline_period_ref,
        "comparison_period_ref": context.comparison_period_ref,
        "baseline_population_ref": context.baseline_population_ref,
        "comparison_population_ref": context.comparison_population_ref,
        "metric_refs": (context.outcome_metric_ref,),
        "variable_refs": variables,
        "source_observation_refs": observations,
        "source_mechanical_result_refs": mechanical,
        "intended_use": "diagnostic",
        "maximum_permitted_meaning": template.maximum_evidence_use,
        "prohibited_meanings": tuple(sorted(family.prohibited_meanings)),
        "authority_bindings": tuple(sorted(authority_bindings, key=lambda item: item.authority_ref)),
        "display_wording": None,
        "display_label": None,
    }
    data["semantic_fingerprint"] = diagnostic_proposition_semantic_fingerprint(data)
    data["proposition_id"] = stable_content_id("diagprop", data["semantic_fingerprint"])
    return DiagnosticProposition(**data)


def _as_refs(value: Any) -> tuple[str, ...]:
    values = value if isinstance(value, tuple) else (value,)
    if any(not isinstance(item, str) or not item for item in values):
        raise GenerationBoundaryError("invented_variable", "candidate references must be non-empty strings")
    return tuple(values)


def _equivalent(actual: Any, expected: str) -> bool:
    return actual == expected or (isinstance(actual, tuple) and actual == (expected,))


def _reference_failure_code(slot: str, proposed: tuple[str, ...]) -> str:
    if slot == "outcome_ref":
        return "invented_metric"
    if slot in {"scope_ref"}:
        return "scope_mismatch"
    if "period_ref" in slot:
        return "period_mismatch"
    if "population_ref" in slot:
        return "population_mismatch"
    if slot in {"source_observation_refs", "external_evidence_dependency_ref"}:
        return "invented_source_reference"
    if slot == "explicit_activation_ref":
        return "external_activation_missing"
    if slot == "optional_r4_result_ref":
        return "r4_support_claim_forbidden"
    if slot == "product_identity_ref":
        return (
            "forbidden_product_name_identity"
            if any("product_name" in item.lower() for item in proposed)
            else "invented_variable"
        )
    if slot in {"original_or_list_price_ref", "discount_semantics_ref"}:
        forbidden = {"unit_price", "line_revenue", "revenue", "aov"}
        return (
            "forbidden_discount_substitution"
            if any(item.lower() in forbidden for item in proposed)
            else "invented_variable"
        )
    return "invented_variable"


def _require_context_alignment(
    authority: SourceAuthorityView,
    context: CandidateGenerationContext,
) -> None:
    expected = {
        "scope_ref": context.scope_ref,
        "baseline_period_ref": context.baseline_period_ref,
        "comparison_period_ref": context.comparison_period_ref,
        "baseline_population_ref": context.baseline_population_ref,
        "comparison_population_ref": context.comparison_population_ref,
    }
    for field, value in expected.items():
        actual = getattr(authority, field)
        if actual is not None and actual != value:
            code = "scope_mismatch" if field == "scope_ref" else (
                "period_mismatch" if "period" in field else "population_mismatch"
            )
            raise GenerationBoundaryError(code, f"source authority {field} is misaligned")


def _jsonable(value: Any) -> Any:
    if isinstance(value, ContractBase):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    return value


__all__ = [
    "AllowedSlotBinding",
    "CandidateDiagnostic",
    "CandidateFamilyView",
    "CandidateGenerationContext",
    "CandidateProducer",
    "CandidateProducerDescriptor",
    "ConstructedCandidate",
    "FamilyActivation",
    "GenerationBoundaryError",
    "ProposalValidationResult",
    "R6GenerationRequest",
    "SourceAuthorityClass",
    "SourceAuthorityView",
    "build_candidate_generation_context",
    "build_generation_request",
    "candidate_fingerprint",
    "validate_and_construct_propositions",
    "validate_candidate_batch",
]
