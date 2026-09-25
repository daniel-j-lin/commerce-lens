from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

import commerce_lens.application.r6_service as service_module
from commerce_lens.application.r6_service import R6CompletionStatus
from commerce_lens.contracts.diagnostic import EvidenceReadiness
from commerce_lens.contracts.diagnostic import (
    RelationshipDirection,
    RelationshipType,
    StructuredRelationship,
)
from commerce_lens.contracts.required_evidence import EvidenceDimension
from commerce_lens.diagnostic.family_registry import MVP_FAMILY_REGISTRY
from commerce_lens.diagnostic.governance import (
    GovernanceAuthenticationError,
    _build_judgments,
    resolve_dimension_applicability,
)
from commerce_lens.persistence.r6_repository import R6ArtifactType
from tests.diagnostic.test_r6_generator import (
    _batch as generator_batch,
    _context as generator_context,
    _product as generator_product,
)
from tests.diagnostic.test_r6_governance import (
    _all_assessments,
    _assessment,
    _authority,
    _authority_registry,
    _proposition,
    _run,
)
from tests.r6.support import (
    CASES_PATH,
    EXPECTED_FIXTURE_IDS,
    R6FixtureSuite,
    case,
    load_cases,
    raw_artifact_payload,
    run_service_case,
)
from commerce_lens.diagnostic.generator import validate_and_construct_propositions


FAIL_CLOSED_SERVICE_IDS = (
    "FX-R6-DESC-001A",
    "FX-R6-DISC-002A",
    "FX-R6-DISC-002B",
    "FX-R6-DISC-002C",
    "FX-R6-DISC-002D",
    "FX-R6-EXT-001B",
    "FX-R6-CLOSED-001A",
    "FX-R6-CLOSED-001B",
    "FX-R6-CLOSED-001C",
    "FX-R6-CLOSED-001D",
    "FX-R6-CLOSED-001E",
    "FX-R6-CLOSED-001F",
    "FX-R6-CLOSED-001G",
    "FX-R6-NONDET-001D",
)

ACCEPTED_SERVICE_IDS = (
    "FX-R6-DISC-001A",
    "FX-R6-EXT-001A",
    "FX-R6-PEER-001A",
    "FX-R6-R4-001A",
    "FX-R6-NONDET-001A",
    "FX-R6-NONDET-001B",
    "FX-R6-NONDET-001C",
)


def test_fixture_authority_is_strict_complete_unique_and_sorted() -> None:
    fixtures = load_cases()
    assert {item.fixture_id for item in fixtures} == EXPECTED_FIXTURE_IDS
    assert [item.fixture_id for item in fixtures] == sorted(EXPECTED_FIXTURE_IDS)
    assert len(fixtures) == len(EXPECTED_FIXTURE_IDS) == 34
    assert all(len(item.expected.diagnostic_code.split(",")) == 1 for item in fixtures if item.expected.diagnostic_code)


@pytest.mark.parametrize("mutation", ["unknown", "missing", "duplicate"])
def test_fixture_loader_rejects_unknown_missing_and_duplicate_authority(tmp_path: Path, mutation: str) -> None:
    payload = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    if mutation == "unknown":
        payload["fixtures"][0]["unapproved"] = True
    elif mutation == "missing":
        payload["fixtures"][0].pop("scenario")
    else:
        payload["fixtures"].append(payload["fixtures"][0])
    path = tmp_path / "cases.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValidationError):
        R6FixtureSuite.model_validate_json(path.read_text(encoding="utf-8"))


def test_compound_hostile_cases_are_split_into_one_outcome_variants() -> None:
    closed = [item for item in load_cases() if item.fixture_id.startswith("FX-R6-CLOSED-001")]
    discount = [item for item in load_cases() if item.fixture_id.startswith("FX-R6-DISC-002")]
    assert [item.expected.diagnostic_code for item in closed] == [
        "unknown_family",
        "invented_metric",
        "invented_variable",
        "invented_source_reference",
        "period_mismatch",
        "population_mismatch",
        "malformed_batch",
        "unregistered_authority",
        "unregistered_authority",
    ]
    assert len(discount) == 4
    assert {item.producer_recipe for item in discount} == {
        "discount_substitute_unit_price",
        "discount_substitute_line_revenue",
        "discount_substitute_revenue",
        "discount_substitute_aov",
    }
    assert {item.expected.diagnostic_code for item in discount} == {"forbidden_discount_substitution"}


@pytest.mark.parametrize("fixture_id", FAIL_CLOSED_SERVICE_IDS)
def test_service_hostile_variants_have_one_exact_failure_and_no_chain(tmp_path: Path, fixture_id: str) -> None:
    fixture = case(fixture_id)
    run = run_service_case(tmp_path, fixture)
    assert run.outcome.completion_status.value == fixture.expected.completion_status
    assert run.outcome.chains == ()
    assert tuple(item.code for item in run.outcome.diagnostics) == (fixture.expected.diagnostic_code,)
    assert not run.analysis.scalar.metadata_store.list_r6_artifact_indexes()


@pytest.mark.parametrize("fixture_id", ACCEPTED_SERVICE_IDS)
def test_accepted_cases_pin_governance_states_and_all_dimensions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fixture_id: str,
) -> None:
    fixture = case(fixture_id)
    assert fixture.expected.profile_dimension_expectations is not None
    captured = []
    original = service_module.govern_pretest

    def capture(*args, **kwargs):
        result = original(*args, **kwargs)
        captured.append(result)
        return result

    monkeypatch.setattr(service_module, "govern_pretest", capture)
    run = run_service_case(tmp_path, fixture)

    assert run.outcome.completion_status.value == fixture.expected.completion_status
    actual_families = []
    actual_dependencies: dict[str, str] = {}
    for chain in run.outcome.chains:
        proposition = raw_artifact_payload(
            run,
            R6ArtifactType.DIAGNOSTIC_PROPOSITION.value,
            chain.diagnostic_proposition_ref,
        )
        actual_families.append(proposition["family_id"])
        profile = raw_artifact_payload(
            run,
            R6ArtifactType.RESOLVED_REQUIRED_EVIDENCE_PROFILE.value,
            chain.resolved_profile_ref,
        )
        decisions = profile["dimension_applicability_decisions"]
        assert len(decisions) == 12
        assert {item["dimension"] for item in decisions} == {item.value for item in EvidenceDimension}
        assert len({item["dimension"] for item in decisions}) == 12
        conditional = {
            item["dimension"]: item["applicability"]
            for item in decisions
            if item["dimension"] in {"metric_compatibility", "unit_currency_compatibility"}
        }
        assert conditional == {
            "metric_compatibility": "REQUIRED",
            "unit_currency_compatibility": "REQUIRED",
        }

        judgments = raw_artifact_payload(
            run,
            R6ArtifactType.REQUIREMENT_JUDGMENT_BUNDLE.value,
            chain.requirement_judgment_bundle_ref,
        )["judgments"]
        dimension_judgments = [item for item in judgments if item["dimension"] is not None]
        dependency_judgments = [item for item in judgments if item["dimension"] is None]
        assert len(dimension_judgments) == 12
        expected_dimension_outcome = "EXTERNAL_UNMET" if proposition["family_id"] == "external_market_association" else "MISSING"
        assert {item["outcome"] for item in dimension_judgments} == {expected_dimension_outcome}
        decision_by_dimension = {item["dimension"]: item["applicability"] for item in decisions}
        outcome_by_dimension = {item["dimension"]: item["outcome"] for item in dimension_judgments}
        assert {
            dimension: f"{decision_by_dimension[dimension]}/{outcome_by_dimension[dimension]}"
            for dimension in decision_by_dimension
        } == fixture.expected.profile_dimension_expectations
        for judgment in dependency_judgments:
            key = (
                f"{proposition['family_id']}:{judgment['requirement_ref']}"
                if len(fixture.expected.accepted_families) > 1
                else judgment["requirement_ref"]
            )
            actual_dependencies[key] = judgment["outcome"]

        evaluation = raw_artifact_payload(
            run,
            R6ArtifactType.PRETEST_DIAGNOSTIC_EVALUATION.value,
            chain.pretest_evaluation_ref,
        )
        assert evaluation["test_eligibility"] == "NOT_ELIGIBLE"
        assert evaluation["analytical_outcome"] == "NOT_EVALUATED"
        assert evaluation["alternative_explanation_state"] == "NOT_COMPLETED"
        assert evaluation["first_controlling_blocker"]

    assert sorted(actual_families) == sorted(fixture.expected.accepted_families)
    assert fixture.expected.requirement_judgments is not None
    assert actual_dependencies == fixture.expected.requirement_judgments
    expected_disposition = fixture.expected.pretest_disposition
    if expected_disposition is not None:
        assert {item.derived_disposition.value for item in captured} == {expected_disposition}


def test_external_activation_is_not_evidence(tmp_path: Path) -> None:
    run = run_service_case(tmp_path, case("FX-R6-EXT-001A"))
    chain = run.outcome.chains[0]
    judgments = raw_artifact_payload(
        run,
        R6ArtifactType.REQUIREMENT_JUDGMENT_BUNDLE.value,
        chain.requirement_judgment_bundle_ref,
    )["judgments"]
    assert all("activation:explicit-economy-request" not in item["evidence_refs"] for item in judgments)
    evaluation = raw_artifact_payload(
        run,
        R6ArtifactType.PRETEST_DIAGNOSTIC_EVALUATION.value,
        chain.pretest_evaluation_ref,
    )
    assert evaluation["evidence_readiness"] == EvidenceReadiness.EXTERNAL_EVIDENCE_REQUIRED.value


def test_unknown_method_authority_is_authentication_failure_not_missing_evidence() -> None:
    fixture = case("FX-R6-CLOSED-001H")
    proposition = _proposition()
    assessments = _all_assessments(proposition)
    with pytest.raises(GovernanceAuthenticationError) as error:
        _run(
            proposition=proposition,
            assessments=assessments,
            proposed_method_refs=(_authority("method:unregistered"),),
            authority_registry=_authority_registry(proposition, assessments),
        )
    assert error.value.code == fixture.expected.diagnostic_code


def test_unregistered_admission_authority_is_authentication_failure_not_missing_evidence() -> None:
    fixture = case("FX-R6-CLOSED-001I")
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
    with pytest.raises(GovernanceAuthenticationError) as error:
        _run(
            proposition=proposition,
            assessments=tuple(supplied),
            authority_registry=_authority_registry(proposition, trusted),
        )
    assert error.value.code == fixture.expected.diagnostic_code


def test_absent_conditional_triggers_are_governed_not_applicable_not_missing() -> None:
    fixture = case("FX-R6-IDENT-003A")
    proposition = _proposition(
        "external_market_association",
        outcome_ref="outcome:validated_revenue_change",
        metric_refs=(),
    )
    family = MVP_FAMILY_REGISTRY.get_family("external_market_association")
    template = MVP_FAMILY_REGISTRY.get_requirement_template("external_market_association")
    resolved = resolve_dimension_applicability(template, proposition)
    decisions = {item.dimension.value: item for item in resolved}
    judgments = {
        item.dimension.value: item
        for item in _build_judgments(family, template, resolved, {})
        if item.dimension is not None
    }
    for dimension in ("metric_compatibility", "unit_currency_compatibility"):
        assert decisions[dimension].applicability.value == "NOT_APPLICABLE"
        assert judgments[dimension].outcome.value == "NOT_APPLICABLE"
        assert judgments[dimension].reason_code == "governed_not_applicable"
    required = set(decisions) - {"metric_compatibility", "unit_currency_compatibility"}
    assert len(required) == 10
    assert all(decisions[item].applicability.value == "REQUIRED" for item in required)
    assert fixture.expected.diagnostic_code == "conditional_not_applicable"


def test_proposition_authority_tamper_is_authentication_failure_not_missing_evidence() -> None:
    fixture = case("FX-R6-TAMPER-001A")
    proposition = _proposition().model_copy(update={"scope_ref": "scope:tampered"})
    with pytest.raises(GovernanceAuthenticationError) as error:
        _run(proposition=proposition, assessments=())
    assert error.value.code == fixture.expected.diagnostic_code


def test_presentation_order_and_wording_deduplicate_to_one_material_identity() -> None:
    fixture = case("FX-R6-IDENT-001A")
    context = generator_context()
    first = generator_product(wording="one", sources=("source:orders", "source:catalog"))
    order = tuple(reversed(tuple(item.slot for item in first.structured_slot_values)))
    second = generator_product(
        wording="materially irrelevant wording",
        sources=("source:catalog", "source:orders"),
        slot_order=order,
    )
    result = validate_and_construct_propositions(generator_batch(context, first, second), context)
    assert len(result.accepted) == 1
    assert len(result.accepted[0].duplicate_candidate_fingerprints) == 1
    assert tuple(item.code for item in result.diagnostics) == (fixture.expected.diagnostic_code,)


@pytest.mark.parametrize(
    ("fixture_id", "updates"),
    [
        ("FX-R6-IDENT-002A", {"baseline_period_ref": "period:different"}),
        ("FX-R6-IDENT-002B", {"comparison_population_ref": "population:different"}),
        ("FX-R6-IDENT-002D", {"relationship": StructuredRelationship(
            relationship_type=RelationshipType.PATTERN,
            direction=RelationshipDirection.DIFFERENT,
            comparison_basis="governed baseline versus comparison",
            bounded_strength="bounded non-causal pattern",
        )}),
        ("FX-R6-IDENT-002E", {"source_observation_refs": ("dataset:different",)}),
        ("FX-R6-IDENT-002F", {"variable_refs": ("field:different_product_id", "field:line_revenue")}),
    ],
)
def test_each_material_mutation_has_one_distinct_identity(fixture_id: str, updates: dict[str, object]) -> None:
    fixture = case(fixture_id)
    original = _proposition()
    changed = _proposition(**updates)
    assert changed.proposition_id != original.proposition_id
    assert changed.semantic_fingerprint != original.semantic_fingerprint
    assert fixture.expected.diagnostic_code == "distinct_identity"


def test_material_family_change_has_distinct_identity() -> None:
    fixture = case("FX-R6-IDENT-002C")
    product = _proposition("product_composition_association")
    discount = _proposition("discounting_association")
    assert discount.proposition_id != product.proposition_id
    assert discount.semantic_fingerprint != product.semantic_fingerprint
    assert fixture.expected.diagnostic_code == "distinct_identity"


def test_peer_families_are_retained_without_ranking_fields(tmp_path: Path) -> None:
    run = run_service_case(tmp_path, case("FX-R6-PEER-001A"))
    assert len(run.outcome.chains) == 2
    assert tuple(item.diagnostic_proposition_ref for item in run.outcome.chains) == tuple(
        sorted(item.diagnostic_proposition_ref for item in run.outcome.chains)
    )
    assert not {"rank", "score", "primary", "best", "most_likely", "probability"} & set(
        type(run.outcome.chains[0]).model_fields
    )


def test_candidate_nondeterminism_preserves_proposition_and_governance_material(tmp_path: Path) -> None:
    fixture = case("FX-R6-NONDET-001A")
    first = run_service_case(tmp_path / "first", fixture)
    second_case = fixture.model_copy(update={"producer_recipe": "valid_discount_then_product"})
    second = run_service_case(tmp_path / "second", second_case, analysis=first.analysis)
    assert first.outcome.completion_status is R6CompletionStatus.COMPLETE
    assert second.outcome.completion_status is R6CompletionStatus.COMPLETE
    assert {item.diagnostic_proposition_ref for item in first.outcome.chains} == {
        item.diagnostic_proposition_ref for item in second.outcome.chains
    }
    assert len(first.outcome.chains) == len(second.outcome.chains) == 2
    assert any(item.code == "duplicate_candidate" for item in first.outcome.diagnostics)
    assert len(next(item for item in first.outcome.chains if item.duplicate_candidate_fingerprints).duplicate_candidate_fingerprints) == 1
    first_material = {
        item.diagnostic_proposition_ref: (item.resolved_profile_ref, item.requirement_judgment_bundle_ref)
        for item in first.outcome.chains
    }
    second_material = {
        item.diagnostic_proposition_ref: (item.resolved_profile_ref, item.requirement_judgment_bundle_ref)
        for item in second.outcome.chains
    }
    assert first_material == second_material


def test_requested_omission_and_disallowed_peer_remain_explicit(tmp_path: Path) -> None:
    omitted = run_service_case(tmp_path / "omitted", case("FX-R6-NONDET-001B"))
    disallowed = run_service_case(tmp_path / "disallowed", case("FX-R6-NONDET-001C"))
    assert omitted.outcome.completion_status is R6CompletionStatus.PARTIAL_FAILURE
    assert any(item.code == "requested_family_omitted" for item in omitted.outcome.diagnostics)
    assert disallowed.outcome.completion_status is R6CompletionStatus.COMPLETE
    assert any(item.code == "disallowed_family" for item in disallowed.outcome.diagnostics)
    assert len(disallowed.outcome.chains) == 1
