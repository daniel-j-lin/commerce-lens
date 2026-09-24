from __future__ import annotations

import pytest
from pydantic import ValidationError

from commerce_lens.contracts.hypotheses import (
    CandidateProposal,
    CandidateSlot,
    FamilyActivationPolicy,
    FamilyClassification,
    hypothesis_family_semantic_fingerprint,
)
from commerce_lens.contracts.required_evidence import (
    ApplicabilityState,
    DependencyClassification,
    EvidenceDimension,
    HypothesisFamilyRequirementTemplate,
    requirement_template_semantic_fingerprint,
)
from commerce_lens.diagnostic.family_registry import (
    ACTIVE_FAMILY_IDS,
    MVP_FAMILY_REGISTRY,
    family_registry_semantic_fingerprint,
)


def _product_slots() -> tuple[CandidateSlot, ...]:
    return (
        CandidateSlot(slot="outcome_ref", value="metric:revenue-change"),
        CandidateSlot(slot="baseline_period_ref", value="period:baseline"),
        CandidateSlot(slot="comparison_period_ref", value="period:comparison"),
        CandidateSlot(slot="baseline_population_ref", value="population:baseline"),
        CandidateSlot(slot="comparison_population_ref", value="population:comparison"),
        CandidateSlot(slot="scope_ref", value="scope:all-eligible"),
        CandidateSlot(slot="product_identity_ref", value="product_id"),
        CandidateSlot(slot="monetary_observation_ref", value="line_revenue"),
        CandidateSlot(slot="source_observation_refs", value=("dataset:orders",)),
    )


def _candidate(family_id: str, slots: tuple[CandidateSlot, ...], **updates: object) -> CandidateProposal:
    return CandidateProposal(
        family_id=family_id,
        family_version=str(updates.pop("family_version", "1.0.0")),
        structured_slot_values=slots,
        source_reference_proposals=(),
        display_template_id=updates.pop("display_template_id", None),
        non_authoritative_wording=updates.pop("non_authoritative_wording", None),
        **updates,
    )


def test_registry_contains_exactly_three_approved_active_families() -> None:
    assert {family.family_id for family in MVP_FAMILY_REGISTRY.active_families} == ACTIVE_FAMILY_IDS
    assert len(MVP_FAMILY_REGISTRY.active_families) == 3


@pytest.mark.parametrize(
    "family_id",
    ["orders_change", "refund", "stockout", "other", "unrestricted_other"],
)
def test_explicitly_absent_family_lookup_fails_closed(family_id: str) -> None:
    with pytest.raises(ValueError, match="unknown hypothesis family"):
        MVP_FAMILY_REGISTRY.get_family(family_id)


def test_wrong_family_version_fails_closed() -> None:
    with pytest.raises(ValueError, match="unsupported family version"):
        MVP_FAMILY_REGISTRY.get_family("product_composition_association", "2.0.0")


def test_product_composition_candidate_with_exact_slots_is_accepted() -> None:
    candidate = _candidate(
        "product_composition_association",
        _product_slots(),
        display_template_id="r6-product-composition-untested-v1",
    )
    assert MVP_FAMILY_REGISTRY.validate_candidate(candidate) is candidate


def test_unknown_candidate_slot_is_rejected() -> None:
    candidate = _candidate(
        "product_composition_association",
        _product_slots() + (CandidateSlot(slot="confidence", value=0.9),),
    )
    with pytest.raises(ValueError, match="unsupported proposition slots"):
        MVP_FAMILY_REGISTRY.validate_candidate(candidate)


def test_product_name_cannot_substitute_for_product_identity() -> None:
    slots = tuple(
        CandidateSlot(slot=item.slot, value="field:product_name")
        if item.slot == "product_identity_ref"
        else item
        for item in _product_slots()
    )
    with pytest.raises(ValueError, match="product_name"):
        MVP_FAMILY_REGISTRY.validate_candidate(_candidate("product_composition_association", slots))


@pytest.mark.parametrize(
    "substitute",
    ["field:unit_price", "field:line_revenue", "metric:AOV", "metric:Revenue"],
)
def test_discount_family_rejects_unsupported_discount_authority(substitute: str) -> None:
    slots = (
        CandidateSlot(slot="outcome_ref", value="metric:revenue-change"),
        CandidateSlot(slot="baseline_period_ref", value="period:baseline"),
        CandidateSlot(slot="comparison_period_ref", value="period:comparison"),
        CandidateSlot(slot="baseline_population_ref", value="population:baseline"),
        CandidateSlot(slot="comparison_population_ref", value="population:comparison"),
        CandidateSlot(slot="scope_ref", value="scope:all-eligible"),
        CandidateSlot(slot="original_or_list_price_ref", value=substitute),
        CandidateSlot(slot="discount_semantics_ref", value="governed-discount-definition"),
        CandidateSlot(slot="monetary_observation_ref", value="line_revenue"),
        CandidateSlot(slot="source_observation_refs", value=("dataset:orders",)),
    )
    with pytest.raises(ValueError, match="discount authority"):
        MVP_FAMILY_REGISTRY.validate_candidate(_candidate("discounting_association", slots))


def test_discount_family_is_declared_missing_internal_evidence_only() -> None:
    family = MVP_FAMILY_REGISTRY.get_family("discounting_association")
    assert FamilyClassification.MISSING_INTERNAL_EVIDENCE_ONLY in family.classifications
    assert family.dependency_classifications == (DependencyClassification.INTERNAL,)
    substitutions = " ".join(
        MVP_FAMILY_REGISTRY.get_requirement_template(family.family_id).prohibited_evidence_substitutions
    ).lower()
    assert all(value in substitutions for value in ("unit_price", "line_revenue", "aov"))


def test_external_family_requires_explicit_activation_metadata() -> None:
    family = MVP_FAMILY_REGISTRY.get_family("external_market_association")
    assert family.activation_policy is FamilyActivationPolicy.EXPLICIT_USER_REQUEST_ONLY
    slots = tuple(
        CandidateSlot(slot=slot, value=None if slot == "explicit_activation_ref" else f"ref:{slot}")
        for slot in family.required_proposition_slots
    )
    with pytest.raises(ValueError, match="explicit user-request"):
        MVP_FAMILY_REGISTRY.validate_candidate(_candidate(family.family_id, slots))


def test_external_family_requires_external_evidence_and_prohibits_model_knowledge() -> None:
    family = MVP_FAMILY_REGISTRY.get_family("external_market_association")
    template = MVP_FAMILY_REGISTRY.get_requirement_template(family.family_id)
    assert family.dependency_classifications == (DependencyClassification.EXTERNAL,)
    substitutions = " ".join(template.prohibited_evidence_substitutions).lower()
    assert "automatic browsing" in substitutions
    assert "model general knowledge as evidence" in substitutions


def test_every_template_explicitly_represents_all_twelve_dimensions() -> None:
    for template in MVP_FAMILY_REGISTRY.requirement_templates:
        assert len(template.dimension_requirements) == 12
        assert {item.dimension for item in template.dimension_requirements} == set(EvidenceDimension)


def test_every_family_template_preserves_conditional_exact_binding_dimensions() -> None:
    conditional_dimensions = {
        EvidenceDimension.METRIC_COMPATIBILITY,
        EvidenceDimension.UNIT_CURRENCY_COMPATIBILITY,
    }
    for family_id in ACTIVE_FAMILY_IDS:
        template = MVP_FAMILY_REGISTRY.get_requirement_template(family_id)
        by_dimension = {item.dimension: item for item in template.dimension_requirements}
        assert {
            dimension
            for dimension, requirement in by_dimension.items()
            if requirement.applicability is ApplicabilityState.CONDITIONAL
        } == conditional_dimensions
        assert all(by_dimension[dimension].applicability_condition_ref for dimension in conditional_dimensions)
        assert all(
            requirement.applicability is ApplicabilityState.REQUIRED
            for dimension, requirement in by_dimension.items()
            if dimension not in conditional_dimensions
        )


def test_template_rejects_duplicate_dimension_without_silent_replacement() -> None:
    template = MVP_FAMILY_REGISTRY.get_requirement_template("product_composition_association")
    data = template.model_dump(mode="python")
    requirements = list(data["dimension_requirements"])
    requirements[-1] = requirements[0]
    data["dimension_requirements"] = tuple(requirements)
    data["template_fingerprint"] = requirement_template_semantic_fingerprint(data)
    with pytest.raises(ValidationError, match="exactly once"):
        HypothesisFamilyRequirementTemplate(**data)


def test_product_composition_permitted_meaning_is_bounded_and_non_causal() -> None:
    family = MVP_FAMILY_REGISTRY.get_family("product_composition_association")
    permitted = " ".join(family.permitted_meanings).lower()
    assert "non-causal" in permitted
    assert "future" in permitted
    assert "not tested" in permitted
    assert "price effect" not in permitted
    assert "support" not in permitted


def test_registry_and_family_fingerprints_are_deterministic_and_order_independent() -> None:
    assert MVP_FAMILY_REGISTRY.registry_fingerprint == family_registry_semantic_fingerprint(MVP_FAMILY_REGISTRY)
    data = MVP_FAMILY_REGISTRY.model_dump(mode="python")
    data["active_families"] = tuple(reversed(data["active_families"]))
    assert family_registry_semantic_fingerprint(data) == MVP_FAMILY_REGISTRY.registry_fingerprint


def test_family_display_name_does_not_change_material_fingerprint() -> None:
    family = MVP_FAMILY_REGISTRY.get_family("product_composition_association")
    data = family.model_dump(mode="python")
    data["display_name"] = "Different presentation label"
    assert hypothesis_family_semantic_fingerprint(data) == family.family_fingerprint


def test_material_family_change_changes_fingerprint() -> None:
    family = MVP_FAMILY_REGISTRY.get_family("product_composition_association")
    data = family.model_dump(mode="python")
    data["required_proposition_slots"] = (*data["required_proposition_slots"], "new_material_slot")
    assert hypothesis_family_semantic_fingerprint(data) != family.family_fingerprint


def test_registry_metadata_never_claims_current_family_is_executable() -> None:
    assert all(not family.registry_can_establish_execution_eligibility for family in MVP_FAMILY_REGISTRY.active_families)


def test_candidate_top_level_authority_field_is_rejected_before_registry_validation() -> None:
    with pytest.raises(ValidationError):
        CandidateProposal.model_validate(
            {
                "family_id": "product_composition_association",
                "family_version": "1.0.0",
                "structured_slot_values": [item.model_dump() for item in _product_slots()],
                "claim_state": "Admissible",
            }
        )
