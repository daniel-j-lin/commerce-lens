from __future__ import annotations

import pytest

from commerce_lens.contracts.hypotheses import (
    CandidateProposal,
    CandidateProposalBatch,
    CandidateSlot,
    GenerationParameters,
)
from commerce_lens.contracts.required_evidence import DependencyClassification
from commerce_lens.diagnostic.family_registry import MVP_FAMILY_REGISTRY
from commerce_lens.diagnostic.generator import (
    AllowedSlotBinding,
    CandidateFamilyView,
    CandidateProducerDescriptor,
    FamilyActivation,
    GenerationBoundaryError,
    SourceAuthorityClass,
    SourceAuthorityView,
    build_candidate_generation_context,
    build_generation_request,
    validate_and_construct_propositions,
    validate_candidate_batch,
)
from commerce_lens.evidence.identifiers import canonical_json_fingerprint
from commerce_lens.metrics.registry import METRIC_DEFINITION_VERSION


HASH = "a" * 64
METRIC = f"metric:revenue_change@{METRIC_DEFINITION_VERSION}"
COMMON = {
    "outcome_ref": METRIC,
    "scope_ref": "scope:all",
    "baseline_period_ref": "period:baseline",
    "comparison_period_ref": "period:comparison",
    "baseline_population_ref": "population:baseline",
    "comparison_population_ref": "population:comparison",
}


def _descriptor() -> CandidateProducerDescriptor:
    return CandidateProducerDescriptor(
        producer_id="producer:test",
        producer_version="1.0.0",
        template_id="template:test",
        template_version="1.0.0",
        template_fingerprint=HASH,
        generation_parameters=GenerationParameters(temperature=0.0),
    )


def _context(*, external: bool = False, requested: tuple[str, ...] = ()):
    activation = (
        FamilyActivation(
            family_id="external_market_association",
            activation_ref="activation:external",
            external_factor_ref="external:sentiment",
            external_dependency_ref="dependency:external-evidence",
        ),
    ) if external else ()
    request = build_generation_request(
        analysis_request_ref="request:analysis",
        requested_family_ids=requested,
        family_activations=activation,
    )
    permitted = {"product_composition_association", "discounting_association"}
    if external:
        permitted.add("external_market_association")
    family_views = tuple(
        CandidateFamilyView(
            family_id=family.family_id,
            family_version=family.family_version,
            family_fingerprint=family.family_fingerprint,
            allowed_slots=tuple(sorted(family.allowed_proposition_slots)),
            required_slots=tuple(sorted(family.required_proposition_slots)),
            display_template_ids=family.display_template_ids,
        )
        for family in MVP_FAMILY_REGISTRY.active_families
        if family.family_id in permitted
    )
    bindings = []
    for family_id in permitted:
        bindings.extend(
            AllowedSlotBinding(family_id=family_id, slot=slot, allowed_refs=(value,))
            for slot, value in COMMON.items()
        )
    bindings.extend(
        (
            AllowedSlotBinding(family_id="product_composition_association", slot="product_identity_ref", allowed_refs=("field:product_id", "field:alternate_product_id")),
            AllowedSlotBinding(family_id="product_composition_association", slot="monetary_observation_ref", allowed_refs=("field:line_revenue",)),
            AllowedSlotBinding(family_id="product_composition_association", slot="source_observation_refs", allowed_refs=("source:orders", "source:catalog"), semantically_unordered=True),
            AllowedSlotBinding(family_id="discounting_association", slot="original_or_list_price_ref", allowed_refs=("requirement:original_or_list_price",)),
            AllowedSlotBinding(family_id="discounting_association", slot="discount_semantics_ref", allowed_refs=("requirement:discount_semantics",)),
            AllowedSlotBinding(family_id="discounting_association", slot="monetary_observation_ref", allowed_refs=("field:line_revenue",)),
            AllowedSlotBinding(family_id="discounting_association", slot="source_observation_refs", allowed_refs=("source:orders",), semantically_unordered=True),
        )
    )
    views = [
        _view(METRIC, SourceAuthorityClass.METRIC),
        _view("field:product_id", SourceAuthorityClass.VARIABLE),
        _view("field:alternate_product_id", SourceAuthorityClass.VARIABLE),
        _view("field:line_revenue", SourceAuthorityClass.VARIABLE),
        _view("requirement:original_or_list_price", SourceAuthorityClass.VARIABLE),
        _view("requirement:discount_semantics", SourceAuthorityClass.VARIABLE),
        _view("source:orders", SourceAuthorityClass.SOURCE_REFERENCE, uses=("diagnostic_candidate_source",)),
        _view("source:catalog", SourceAuthorityClass.SOURCE_REFERENCE, uses=("diagnostic_candidate_source",)),
    ]
    if external:
        bindings.extend(
            (
                AllowedSlotBinding(family_id="external_market_association", slot="external_factor_ref", allowed_refs=("external:sentiment",)),
                AllowedSlotBinding(family_id="external_market_association", slot="external_evidence_dependency_ref", allowed_refs=("dependency:external-evidence",)),
                AllowedSlotBinding(family_id="external_market_association", slot="source_observation_refs", allowed_refs=("dependency:external-evidence",), semantically_unordered=True),
                AllowedSlotBinding(family_id="external_market_association", slot="explicit_activation_ref", allowed_refs=("activation:external",)),
            )
        )
        views.extend(
            (
                _view("external:sentiment", SourceAuthorityClass.VARIABLE, classification=DependencyClassification.EXTERNAL),
                _view("dependency:external-evidence", SourceAuthorityClass.SOURCE_REFERENCE, classification=DependencyClassification.EXTERNAL, uses=("diagnostic_candidate_source", "non_evidentiary_dependency")),
                _view("activation:external", SourceAuthorityClass.ACTIVATION, classification=DependencyClassification.EXTERNAL, uses=("family_activation_only", "diagnostic")),
            )
        )
    return build_candidate_generation_context(
        generation_request_ref=request.generation_request_ref,
        analysis_request_ref=request.analysis_request_ref,
        outcome_metric_ref=METRIC,
        outcome_validated_result_ref="validated:revenue-change",
        scope_ref=COMMON["scope_ref"],
        baseline_period_ref=COMMON["baseline_period_ref"],
        comparison_period_ref=COMMON["comparison_period_ref"],
        baseline_population_ref=COMMON["baseline_population_ref"],
        comparison_population_ref=COMMON["comparison_population_ref"],
        permitted_family_views=family_views,
        allowed_slot_bindings=tuple(bindings),
        source_authority_views=tuple(views),
        requested_family_ids=requested,
        family_activations=activation,
        source_mechanical_result_ref=None,
    )


def _view(ref, authority_class, *, classification=DependencyClassification.INTERNAL, uses=("diagnostic_candidate_variable",)):
    return SourceAuthorityView(
        authority_ref=ref,
        authority_version="1.0.0",
        authority_fingerprint=canonical_json_fingerprint({"ref": ref}),
        authority_class=authority_class,
        dependency_classification=classification,
        intended_uses=uses,
        **{
            "scope_ref": COMMON["scope_ref"],
            "baseline_period_ref": COMMON["baseline_period_ref"],
            "comparison_period_ref": COMMON["comparison_period_ref"],
            "baseline_population_ref": COMMON["baseline_population_ref"],
            "comparison_population_ref": COMMON["comparison_population_ref"],
        },
    )


def _product(*, wording="wording", product_ref="field:product_id", sources=("source:orders",), slot_order=None):
    values = {
        **COMMON,
        "product_identity_ref": product_ref,
        "monetary_observation_ref": "field:line_revenue",
        "source_observation_refs": sources,
    }
    order = slot_order or tuple(values)
    return CandidateProposal(
        family_id="product_composition_association",
        family_version="1.0.0",
        structured_slot_values=tuple(CandidateSlot(slot=slot, value=values[slot]) for slot in order),
        source_reference_proposals=sources,
        display_template_id="r6-product-composition-untested-v1",
        non_authoritative_wording=wording,
    )


def _discount(**updates):
    values = {
        **COMMON,
        "original_or_list_price_ref": "requirement:original_or_list_price",
        "discount_semantics_ref": "requirement:discount_semantics",
        "monetary_observation_ref": "field:line_revenue",
        "source_observation_refs": ("source:orders",),
    }
    values.update(updates)
    return CandidateProposal(
        family_id="discounting_association",
        family_version="1.0.0",
        structured_slot_values=tuple(CandidateSlot(slot=slot, value=value) for slot, value in values.items()),
        source_reference_proposals=("source:orders",),
    )


def _external():
    values = {
        **COMMON,
        "external_factor_ref": "external:sentiment",
        "external_evidence_dependency_ref": "dependency:external-evidence",
        "source_observation_refs": ("dependency:external-evidence",),
        "explicit_activation_ref": "activation:external",
    }
    return CandidateProposal(
        family_id="external_market_association",
        family_version="1.0.0",
        structured_slot_values=tuple(CandidateSlot(slot=slot, value=value) for slot, value in values.items()),
        source_reference_proposals=("dependency:external-evidence",),
    )


def _batch(context, *candidates):
    return CandidateProposalBatch(
        batch_schema_version="1.0.0",
        producer_ref="producer:test",
        generation_request_ref=context.generation_request_ref,
        candidates=candidates,
    )


def _rebuild_context(context, **updates):
    data = context.model_dump(mode="python")
    data.pop("context_id")
    data.pop("context_fingerprint")
    data.update(updates)
    return build_candidate_generation_context(**data)


def test_generation_request_is_stable_structured_and_has_no_authority_fields() -> None:
    request = build_generation_request(analysis_request_ref="request:analysis", requested_family_ids=("discounting_association",))
    assert request.generation_request_ref.startswith("r6genreq_")
    forbidden = {"evidence", "support", "confidence", "probability", "finding", "claim_decision"}
    assert not forbidden & set(type(request).model_fields)


@pytest.mark.parametrize("field", ["confidence", "probability", "status", "Finding", "blocker", "eligibility", "family_fingerprint", "ClaimDecision"])
def test_strict_runtime_batch_revalidation_rejects_forbidden_fields(field) -> None:
    context = _context()
    raw = _batch(context, _product()).model_dump(mode="python")
    raw["candidates"][0][field] = "forbidden"
    with pytest.raises(GenerationBoundaryError) as error:
        validate_candidate_batch(raw, descriptor=_descriptor(), context=context)
    assert error.value.code == "malformed_batch"


def test_batch_identity_cannot_override_descriptor_or_request() -> None:
    context = _context()
    raw = _batch(context, _product()).model_dump(mode="python")
    raw["producer_ref"] = "producer:spoofed"
    with pytest.raises(GenerationBoundaryError, match="producer_identity_mismatch"):
        validate_candidate_batch(raw, descriptor=_descriptor(), context=context)
    raw["producer_ref"] = "producer:test"
    raw["generation_request_ref"] = "r6genreq_wrong"
    with pytest.raises(GenerationBoundaryError, match="generation_request_mismatch"):
        validate_candidate_batch(raw, descriptor=_descriptor(), context=context)


def test_same_semantics_different_wording_has_same_proposition_identity() -> None:
    context = _context()
    result = validate_and_construct_propositions(_batch(context, _product(wording="one"), _product(wording="two")), context)
    assert len(result.accepted) == 1
    assert len(result.accepted[0].duplicate_candidate_fingerprints) == 1
    assert result.accepted[0].proposition.display_wording is None


def test_different_semantics_same_wording_has_different_identity() -> None:
    context = _context()
    result = validate_and_construct_propositions(
        _batch(context, _product(wording="same"), _product(wording="same", product_ref="field:alternate_product_id")),
        context,
    )
    assert len(result.accepted) == 2
    assert len({item.proposition.proposition_id for item in result.accepted}) == 2


def test_slot_and_unordered_source_reordering_preserve_identity() -> None:
    context = _context()
    first = _product(sources=("source:orders", "source:catalog"))
    values = tuple(reversed(tuple(slot.slot for slot in first.structured_slot_values)))
    second = _product(sources=("source:catalog", "source:orders"), slot_order=values)
    result = validate_and_construct_propositions(_batch(context, first, second), context)
    assert len(result.accepted) == 1
    assert len(result.accepted[0].duplicate_candidate_fingerprints) == 1


@pytest.mark.parametrize(
    ("candidate", "code"),
    [
        (_product(product_ref="field:invented"), "invented_variable"),
        (_product(product_ref="product_name"), "forbidden_product_name_identity"),
        (_discount(original_or_list_price_ref="unit_price"), "forbidden_discount_substitution"),
    ],
)
def test_invented_and_forbidden_variable_bindings_reject(candidate, code) -> None:
    context = _context()
    result = validate_and_construct_propositions(_batch(context, candidate), context)
    assert result.accepted == ()
    assert result.diagnostics[0].code == code


def test_invented_metric_source_scope_period_population_and_source_mismatch_reject() -> None:
    mutations = (
        ("outcome_ref", "metric:orders@wrong", "invented_metric"),
        ("scope_ref", "scope:wrong", "scope_mismatch"),
        ("baseline_period_ref", "period:wrong", "period_mismatch"),
        ("comparison_population_ref", "population:wrong", "population_mismatch"),
        ("source_observation_refs", ("source:invented",), "invented_source_reference"),
    )
    context = _context()
    for slot, value, code in mutations:
        candidate = _product()
        slots = tuple(item.model_copy(update={"value": value}) if item.slot == slot else item for item in candidate.structured_slot_values)
        source_proposals = value if slot == "source_observation_refs" else candidate.source_reference_proposals
        candidate = candidate.model_copy(update={"structured_slot_values": slots, "source_reference_proposals": source_proposals})
        result = validate_and_construct_propositions(_batch(context, candidate), context)
        assert result.diagnostics[0].code == code


def test_source_slot_and_proposal_mismatch_rejects() -> None:
    context = _context()
    candidate = _product().model_copy(update={"source_reference_proposals": ("source:catalog",)})
    result = validate_and_construct_propositions(_batch(context, candidate), context)
    assert result.diagnostics[0].code == "source_proposal_mismatch"


def test_wrong_source_class_and_stale_source_authority_reject() -> None:
    for mutation, code in (("class", "wrong_source_class"), ("use", "stale_source_authority")):
        context = _context()
        views = []
        for view in context.source_authority_views:
            if view.authority_ref != "source:orders":
                views.append(view)
            elif mutation == "class":
                views.append(view.model_copy(update={"authority_class": SourceAuthorityClass.VARIABLE}))
            else:
                views.append(view.model_copy(update={"intended_uses": ()}))
        context = _rebuild_context(context, source_authority_views=tuple(views))
        result = validate_and_construct_propositions(_batch(context, _product()), context)
        assert result.diagnostics[0].code == code


def test_stale_family_view_fails_closed() -> None:
    context = _context()
    views = tuple(
        item.model_copy(update={"family_fingerprint": "f" * 64})
        if item.family_id == "product_composition_association" else item
        for item in context.permitted_family_views
    )
    context = _rebuild_context(context, permitted_family_views=views)
    result = validate_and_construct_propositions(_batch(context, _product()), context)
    assert result.diagnostics[0].code == "stale_family_authority"


def test_invented_and_missing_slots_fail_closed() -> None:
    context = _context()
    candidate = _product()
    invented = candidate.model_copy(
        update={
            "structured_slot_values": (*candidate.structured_slot_values, CandidateSlot(slot="invented", value="x")),
        }
    )
    missing = candidate.model_copy(
        update={
            "structured_slot_values": tuple(item for item in candidate.structured_slot_values if item.slot != "product_identity_ref"),
        }
    )
    result = validate_and_construct_propositions(_batch(context, invented, missing), context)
    assert {item.code for item in result.diagnostics} == {"invented_slot", "missing_required_slot"}


def test_r4_mechanical_reference_cannot_be_used_as_observation_support() -> None:
    context = _context()
    mechanical = _view("r4:validated", SourceAuthorityClass.MECHANICAL_RESULT, uses=("mechanical_reference_only",))
    bindings = (*context.allowed_slot_bindings, AllowedSlotBinding(
        family_id="product_composition_association",
        slot="optional_r4_result_ref",
        allowed_refs=("r4:validated",),
    ))
    context = _rebuild_context(
        context,
        source_authority_views=(*context.source_authority_views, mechanical),
        allowed_slot_bindings=bindings,
        source_mechanical_result_ref="r4:validated",
    )
    candidate = _product(sources=("r4:validated",))
    result = validate_and_construct_propositions(_batch(context, candidate), context)
    assert result.diagnostics[0].code == "r4_support_claim_forbidden"


def test_unknown_wrong_version_and_disallowed_external_reject() -> None:
    context = _context()
    unknown = _product().model_copy(update={"family_id": "orders_change"})
    wrong = _product().model_copy(update={"family_version": "9.9.9"})
    result = validate_and_construct_propositions(_batch(context, unknown, wrong), context)
    assert {item.code for item in result.diagnostics} == {"unknown_family", "wrong_family_version"}
    external = validate_and_construct_propositions(_batch(context, _external()), context)
    assert external.diagnostics[0].code == "disallowed_family"


def test_external_requires_and_preserves_exact_structured_activation() -> None:
    context = _context(external=True, requested=("external_market_association",))
    result = validate_and_construct_propositions(_batch(context, _external()), context)
    assert len(result.accepted) == 1
    proposition = result.accepted[0].proposition
    assert proposition.family_id == "external_market_association"
    assert "activation:external" in {item.authority_ref for item in proposition.authority_bindings}


def test_requested_family_omission_is_explicit_and_not_substituted() -> None:
    context = _context(external=True, requested=("external_market_association",))
    result = validate_and_construct_propositions(_batch(context, _product()), context)
    assert result.requested_family_omissions == ("external_market_association",)
    assert any(item.code == "requested_family_omitted" for item in result.diagnostics)
    assert {item.proposition.family_id for item in result.accepted} == {"product_composition_association"}


def test_distinct_peers_are_sorted_by_identity_not_rank() -> None:
    context = _context()
    result = validate_and_construct_propositions(_batch(context, _discount(), _product()), context)
    ids = tuple(item.proposition.proposition_id for item in result.accepted)
    assert ids == tuple(sorted(ids))
    assert {item.proposition.family_id for item in result.accepted} == {"product_composition_association", "discounting_association"}
    assert not {"rank", "score", "primary", "confidence", "probability"} & set(type(result.accepted[0].proposition).model_fields)
