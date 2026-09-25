from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

import commerce_lens.application.r6_service as service_module
from commerce_lens.application.r6_service import R6CompletionStatus, run_r6
from commerce_lens.contracts.diagnostic import EvidenceReadiness, TestEligibility as EligibilityState
from commerce_lens.contracts.hypotheses import CandidateProposal, CandidateProposalBatch, CandidateSlot, GenerationParameters
from commerce_lens.diagnostic.generator import CandidateProducerDescriptor, FamilyActivation, build_generation_request
from commerce_lens.diagnostic.governance import GovernanceAuthenticationError
from commerce_lens.evidence.identifiers import stable_content_id
from commerce_lens.persistence.r6_repository import R6ArtifactIntegrityError, R6ArtifactType, R6Repository
from tests.engine.test_execution import _row
from tests.r4.support import make_r4_fixture, run_r4


NOW = datetime(2026, 9, 25, 10, 0, tzinfo=UTC)
HASH = "a" * 64


class BoundedProducer:
    def __init__(self, families=("product_composition_association",), *, duplicate=False, wording="candidate"):
        self.families = families
        self.duplicate = duplicate
        self.wording = wording
        self.context = None

    def produce_candidates(self, context):
        self.context = context
        candidates = [_candidate(context, family, wording=self.wording) for family in self.families]
        if self.duplicate:
            candidates.append(_candidate(context, self.families[0], wording="duplicate wording"))
        return CandidateProposalBatch(
            batch_schema_version="1.0.0",
            producer_ref="producer:test",
            generation_request_ref=context.generation_request_ref,
            candidates=tuple(candidates),
        )


class RaisingProducer:
    def produce_candidates(self, context):
        raise RuntimeError("simulated producer failure")


class MalformedProducer:
    def __init__(self, payload):
        self.payload = payload

    def produce_candidates(self, context):
        return self.payload


def _descriptor():
    return CandidateProducerDescriptor(
        producer_id="producer:test",
        producer_version="1.0.0",
        template_id="template:r6-test",
        template_version="1.0.0",
        template_fingerprint=HASH,
        generation_parameters=GenerationParameters(temperature=0.0, max_output_tokens=500),
    )


def _fixture(tmp_path):
    return make_r4_fixture(
        tmp_path,
        [
            _row(order_id="o1", order_date="2026-01-01", product_id="p1", line_revenue="100.00"),
            _row(order_id="o2", order_date="2026-01-03", product_id="p2", line_revenue="120.00"),
        ],
    )


def _run(tmp_path, producer, *, requested=(), activations=(), handoff=False, with_r4=False):
    fixture = _fixture(tmp_path)
    request = build_generation_request(
        analysis_request_ref=fixture.scalar.request.request_id,
        requested_family_ids=requested,
        family_activations=activations,
    )
    r4_artifact = None
    if with_r4:
        r4_outcome = run_r4(fixture)
        r4_artifact = r4_outcome.validation.validated_result_artifact
    outcome = run_r6(
        generation_request=request,
        producer=producer,
        producer_descriptor=_descriptor(),
        analysis_request_ref=fixture.scalar.request.request_id,
        sufficiency_ref=fixture.scalar.sufficiency.sufficiency_id,
        plan=fixture.scalar.plan,
        revenue_change_validated_result_ref=fixture.change.validated_result_id,
        artifact_store=fixture.scalar.artifact_store,
        metadata_store=fixture.scalar.metadata_store,
        generated_at=NOW,
        finalized_at=NOW,
        r4_validated_result_artifact=r4_artifact,
        persist_handoff=handoff,
    )
    return fixture, request, outcome


def _candidate(context, family, *, wording="candidate"):
    values = {
        "outcome_ref": context.outcome_metric_ref,
        "scope_ref": context.scope_ref,
        "baseline_period_ref": context.baseline_period_ref,
        "comparison_period_ref": context.comparison_period_ref,
        "baseline_population_ref": context.baseline_population_ref,
        "comparison_population_ref": context.comparison_population_ref,
    }
    source_refs = ()
    if family == "product_composition_association":
        source = next(
            item.authority_ref for item in context.source_authority_views
            if item.authority_class.value == "SOURCE_REFERENCE"
            and item.dependency_classification.value == "INTERNAL"
        )
        values.update(
            product_identity_ref="field:product_id",
            monetary_observation_ref="field:line_revenue",
            source_observation_refs=(source,),
        )
        if context.source_mechanical_result_ref is not None:
            values["optional_r4_result_ref"] = context.source_mechanical_result_ref
        source_refs = (source,) + ((context.source_mechanical_result_ref,) if context.source_mechanical_result_ref else ())
        template = "r6-product-composition-untested-v1"
    elif family == "discounting_association":
        source = next(
            item.authority_ref for item in context.source_authority_views
            if item.authority_class.value == "SOURCE_REFERENCE"
            and item.dependency_classification.value == "INTERNAL"
        )
        values.update(
            original_or_list_price_ref="requirement:original_or_list_price",
            discount_semantics_ref="requirement:governed_discount_semantics",
            monetary_observation_ref="field:line_revenue",
            source_observation_refs=(source,),
        )
        source_refs = (source,)
        template = "r6-discounting-untested-v1"
    else:
        activation = next(item for item in context.family_activations if item.family_id == family)
        values.update(
            external_factor_ref=activation.external_factor_ref,
            external_evidence_dependency_ref=activation.external_dependency_ref,
            source_observation_refs=(activation.external_dependency_ref,),
            explicit_activation_ref=activation.activation_ref,
        )
        source_refs = (activation.external_dependency_ref,)
        template = "r6-external-market-untested-v1"
    return CandidateProposal(
        family_id=family,
        family_version="1.0.0",
        structured_slot_values=tuple(CandidateSlot(slot=slot, value=value) for slot, value in values.items()),
        source_reference_proposals=source_refs,
        display_template_id=template,
        non_authoritative_wording=wording,
    )


def _artifact_payload(fixture, artifact_type, artifact_id):
    index = fixture.scalar.metadata_store.get_r6_artifact_index(artifact_type.value, artifact_id)
    assert index is not None
    reference = fixture.scalar.metadata_store.get_artifact_reference(index.artifact_reference_id)
    assert reference is not None
    return json.loads(fixture.scalar.artifact_store.safe_path(reference.path).read_text(encoding="utf-8"))


def test_complete_product_chain_persists_missing_evidence_without_upgrade(tmp_path) -> None:
    fixture, _, outcome = _run(tmp_path, BoundedProducer())
    assert outcome.completion_status is R6CompletionStatus.COMPLETE
    assert len(outcome.chains) == 1
    chain = outcome.chains[0]
    assert chain.test_eligibility is EligibilityState.NOT_ELIGIBLE
    evaluation = _artifact_payload(fixture, R6ArtifactType.PRETEST_DIAGNOSTIC_EVALUATION, chain.pretest_evaluation_ref)
    assert evaluation["evidence_readiness"] == EvidenceReadiness.MISSING_INTERNAL_EVIDENCE.value
    assert evaluation["test_eligibility"] == EligibilityState.NOT_ELIGIBLE.value


def test_hypothesis_only_not_eligible_from_r6_2_is_persisted_unchanged(tmp_path, monkeypatch) -> None:
    from commerce_lens.diagnostic.governance import PreTestDisposition
    from tests.diagnostic.test_r6_governance import _all_assessments, _authority_registry

    original = service_module.govern_pretest
    derived_dispositions = []

    def governed_with_authenticated_evidence(
        proposition,
        candidate,
        template_binding,
        evidence_assessments,
        *,
        authority_registry,
        finalized_at,
        **kwargs,
    ):
        assessments = _all_assessments(proposition)
        result = original(
            proposition,
            candidate,
            template_binding,
            assessments,
            authority_registry=_authority_registry(proposition, assessments),
            finalized_at=finalized_at,
            **kwargs,
        )
        derived_dispositions.append(result.derived_disposition)
        return result

    monkeypatch.setattr(service_module, "govern_pretest", governed_with_authenticated_evidence)
    fixture, _, outcome = _run(tmp_path, BoundedProducer())

    assert outcome.completion_status is R6CompletionStatus.COMPLETE
    chain = outcome.chains[0]
    evaluation = _artifact_payload(
        fixture,
        R6ArtifactType.PRETEST_DIAGNOSTIC_EVALUATION,
        chain.pretest_evaluation_ref,
    )
    assert derived_dispositions == [PreTestDisposition.HYPOTHESIS_ONLY]
    assert evaluation["evidence_readiness"] == EvidenceReadiness.READY_FOR_TEST.value
    assert evaluation["test_eligibility"] == EligibilityState.NOT_ELIGIBLE.value
    assert chain.test_eligibility is EligibilityState.NOT_ELIGIBLE


def test_zero_executable_hypotheses_is_valid_complete(tmp_path) -> None:
    _, _, outcome = _run(tmp_path, BoundedProducer(("product_composition_association", "discounting_association")))
    assert outcome.completion_status is R6CompletionStatus.COMPLETE
    assert len(outcome.chains) == 2
    assert not any(chain.test_eligibility is EligibilityState.ELIGIBLE_NOT_EXECUTED for chain in outcome.chains)


def test_duplicate_proposals_make_one_chain_and_retain_all_audit_fingerprints(tmp_path) -> None:
    _, _, outcome = _run(tmp_path, BoundedProducer(duplicate=True))
    assert outcome.completion_status is R6CompletionStatus.COMPLETE
    assert len(outcome.chains) == 1
    assert len(outcome.chains[0].duplicate_candidate_fingerprints) == 1
    assert len(outcome.accepted_candidate_fingerprints) == 1
    assert any(item.code == "duplicate_candidate" for item in outcome.diagnostics)


def test_multiple_distinct_peers_are_all_retained_without_ranking(tmp_path) -> None:
    _, _, outcome = _run(tmp_path, BoundedProducer(("discounting_association", "product_composition_association")))
    assert outcome.completion_status is R6CompletionStatus.COMPLETE
    assert len(outcome.chains) == 2
    assert not {"rank", "score", "primary", "best", "most_likely"} & set(type(outcome.chains[0]).model_fields)


def test_external_activation_allows_consideration_but_is_not_evidence(tmp_path) -> None:
    activation = FamilyActivation(
        family_id="external_market_association",
        activation_ref="activation:external",
        external_factor_ref="external:consumer_sentiment",
        external_dependency_ref="dependency:external-evidence",
    )
    fixture, _, outcome = _run(
        tmp_path,
        BoundedProducer(("external_market_association",)),
        requested=("external_market_association",),
        activations=(activation,),
    )
    assert outcome.completion_status is R6CompletionStatus.COMPLETE
    evaluation = _artifact_payload(fixture, R6ArtifactType.PRETEST_DIAGNOSTIC_EVALUATION, outcome.chains[0].pretest_evaluation_ref)
    assert evaluation["evidence_readiness"] == EvidenceReadiness.EXTERNAL_EVIDENCE_REQUIRED.value
    judgments = _artifact_payload(fixture, R6ArtifactType.REQUIREMENT_JUDGMENT_BUNDLE, outcome.chains[0].requirement_judgment_bundle_ref)
    assert not any("activation:external" in item["evidence_refs"] for item in judgments["judgments"])


def test_external_without_activation_is_rejected(tmp_path) -> None:
    class UnactivatedExternalProducer:
        def produce_candidates(self, context):
            values = {
                "outcome_ref": context.outcome_metric_ref,
                "scope_ref": context.scope_ref,
                "baseline_period_ref": context.baseline_period_ref,
                "comparison_period_ref": context.comparison_period_ref,
                "baseline_population_ref": context.baseline_population_ref,
                "comparison_population_ref": context.comparison_population_ref,
                "external_factor_ref": "external:sentiment",
                "external_evidence_dependency_ref": "dependency:external",
                "source_observation_refs": ("dependency:external",),
                "explicit_activation_ref": "activation:missing",
            }
            candidate = CandidateProposal(
                family_id="external_market_association",
                family_version="1.0.0",
                structured_slot_values=tuple(CandidateSlot(slot=slot, value=value) for slot, value in values.items()),
                source_reference_proposals=("dependency:external",),
            )
            return CandidateProposalBatch(
                batch_schema_version="1.0.0",
                producer_ref="producer:test",
                generation_request_ref=context.generation_request_ref,
                candidates=(candidate,),
            )

    _, _, outcome = _run(tmp_path, UnactivatedExternalProducer())
    assert outcome.completion_status is R6CompletionStatus.GENERATION_FAILURE
    assert outcome.chains == ()
    assert any(item.code == "disallowed_family" for item in outcome.diagnostics)


def test_requested_family_omission_prevents_complete_and_does_not_substitute(tmp_path) -> None:
    activation = FamilyActivation(
        family_id="external_market_association",
        activation_ref="activation:external",
        external_factor_ref="external:consumer_sentiment",
        external_dependency_ref="dependency:external-evidence",
    )
    _, _, outcome = _run(
        tmp_path,
        BoundedProducer(),
        requested=("external_market_association",),
        activations=(activation,),
    )
    assert outcome.completion_status is R6CompletionStatus.PARTIAL_FAILURE
    assert len(outcome.chains) == 1
    assert any(item.code == "requested_family_omitted" for item in outcome.diagnostics)


def test_producer_exception_and_malformed_or_empty_batch_create_no_r6_artifacts(tmp_path) -> None:
    for index, producer in enumerate((RaisingProducer(), MalformedProducer({}), MalformedProducer({
        "batch_schema_version": "1.0.0",
        "producer_ref": "producer:test",
        "generation_request_ref": "wrong",
        "candidates": [],
    }))):
        fixture, _, outcome = _run(tmp_path / str(index), producer)
        assert outcome.completion_status is R6CompletionStatus.GENERATION_FAILURE
        assert outcome.chains == ()
        assert fixture.scalar.metadata_store.list_r6_artifact_indexes() == []


def test_producer_identity_cannot_override_trusted_descriptor(tmp_path) -> None:
    class Spoofed(BoundedProducer):
        def produce_candidates(self, context):
            batch = super().produce_candidates(context)
            return batch.model_copy(update={"producer_ref": "producer:spoofed"})

    _, _, outcome = _run(tmp_path, Spoofed())
    assert outcome.completion_status is R6CompletionStatus.GENERATION_FAILURE
    assert outcome.diagnostics[0].code == "producer_identity_mismatch"


def test_raw_batch_is_generic_audit_only_and_provenance_uses_existing_identity(tmp_path) -> None:
    fixture, _, outcome = _run(tmp_path, BoundedProducer())
    raw_ref = fixture.scalar.metadata_store.get_artifact_reference(outcome.raw_candidate_artifact_ref)
    assert raw_ref is not None
    assert "/raw_candidates/" in f"/{raw_ref.path}"
    assert outcome.raw_candidate_artifact_ref not in {
        item.artifact_id for item in fixture.scalar.metadata_store.list_r6_artifact_indexes()
    }
    provenance_id = outcome.chains[0].generation_provenance_ref
    provenance = R6Repository(fixture.scalar.artifact_store, fixture.scalar.metadata_store).load_generation_provenance(provenance_id)
    assert provenance.raw_candidate_artifact_ref == outcome.raw_candidate_artifact_ref
    assert provenance.generation_provenance_id == stable_content_id("genprov", provenance.provenance_fingerprint)


def test_optional_handoff_is_persisted_but_never_executes_r7(tmp_path) -> None:
    fixture, _, outcome = _run(tmp_path, BoundedProducer(), handoff=True)
    assert outcome.completion_status is R6CompletionStatus.COMPLETE
    assert outcome.chains[0].handoff_ref is not None
    handoff = _artifact_payload(fixture, R6ArtifactType.R6_TO_R7_HANDOFF, outcome.chains[0].handoff_ref)
    assert handoff["test_eligibility"] == EligibilityState.NOT_ELIGIBLE.value
    assert "execute" not in handoff


def test_authenticated_r4_is_retained_as_mechanical_reference_only(tmp_path) -> None:
    fixture, _, outcome = _run(tmp_path, BoundedProducer(), with_r4=True)
    assert outcome.completion_status is R6CompletionStatus.COMPLETE
    proposition = _artifact_payload(fixture, R6ArtifactType.DIAGNOSTIC_PROPOSITION, outcome.chains[0].diagnostic_proposition_ref)
    assert len(proposition["source_mechanical_result_refs"]) == 1
    assert proposition["relationship"]["relationship_type"] == "association"
    assert "support" not in proposition["maximum_permitted_meaning"].lower()


def test_late_persistence_failure_reports_partial_refs_and_no_completed_chain(tmp_path, monkeypatch) -> None:
    def fail(self, artifact):
        raise R6ArtifactIntegrityError("simulated_late_failure", artifact.governed_hypothesis_id, "late failure")

    monkeypatch.setattr(service_module.R6Repository, "persist_governed_hypothesis", fail)
    _, _, outcome = _run(tmp_path, BoundedProducer())
    assert outcome.completion_status is R6CompletionStatus.PERSISTENCE_FAILURE
    assert outcome.chains == ()
    assert outcome.partial_persisted_refs
    assert any(item.code == "simulated_late_failure" for item in outcome.diagnostics)


def test_second_peer_persistence_failure_preserves_first_complete_chain(tmp_path, monkeypatch) -> None:
    original = service_module.R6Repository.persist_governed_hypothesis
    calls = 0

    def fail_second(self, artifact):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise R6ArtifactIntegrityError("simulated_second_failure", artifact.governed_hypothesis_id, "second failed")
        return original(self, artifact)

    monkeypatch.setattr(service_module.R6Repository, "persist_governed_hypothesis", fail_second)
    _, _, outcome = _run(tmp_path, BoundedProducer(("product_composition_association", "discounting_association")))
    assert outcome.completion_status is R6CompletionStatus.PARTIAL_FAILURE
    assert len(outcome.chains) == 1
    assert any(item.code == "simulated_second_failure" for item in outcome.diagnostics)


def test_governance_authentication_failure_is_not_missing_evidence(tmp_path, monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise GovernanceAuthenticationError("simulated_governance_failure", "governance failed")

    monkeypatch.setattr(service_module, "govern_pretest", fail)
    _, _, outcome = _run(tmp_path, BoundedProducer())
    assert outcome.completion_status is R6CompletionStatus.GOVERNANCE_FAILURE
    assert outcome.chains == ()
    assert outcome.diagnostics[0].code == "simulated_governance_failure"
    assert outcome.diagnostics[0].code not in {"MISSING_EVIDENCE", "EXTERNAL_EVIDENCE_REQUIRED"}


def test_requested_handoff_failure_preserves_hypothesis_but_prevents_complete(tmp_path, monkeypatch) -> None:
    def fail(self, artifact):
        raise R6ArtifactIntegrityError("handoff_failure", artifact.handoff_id, "handoff failed")

    monkeypatch.setattr(service_module.R6Repository, "persist_r6_to_r7_handoff", fail)
    _, _, outcome = _run(tmp_path, BoundedProducer(), handoff=True)
    assert outcome.completion_status is R6CompletionStatus.PARTIAL_FAILURE
    assert len(outcome.chains) == 1
    assert outcome.chains[0].handoff_ref is None
    assert any(ref.startswith("govhyp_") for ref in outcome.partial_persisted_refs)


def test_candidate_context_is_minimized_and_public_contracts_unchanged(tmp_path) -> None:
    producer = BoundedProducer()
    _, _, outcome = _run(tmp_path, producer)
    assert outcome.completion_status is R6CompletionStatus.COMPLETE
    context_fields = set(type(producer.context).model_fields)
    forbidden = {
        "raw_rows", "original_question_text", "product_name", "unit_price", "orders", "aov",
        "r4_components", "required_evidence_profile", "requirement_judgments", "evidence_readiness",
        "first_blocker", "test_eligibility", "analytical_outcome", "disposition", "finding",
        "claim_decision", "confidence", "probability", "ranking",
    }
    assert not forbidden & context_fields
    from commerce_lens.contracts.results import AnalysisResult
    assert not {"hypotheses", "diagnostic_families", "r6_handoffs"} & set(AnalysisResult.model_fields)


def test_wording_and_batch_order_nondeterminism_do_not_change_governance_material(tmp_path) -> None:
    fixture_one, _, one = _run(tmp_path / "one", BoundedProducer(("product_composition_association", "discounting_association"), wording="one"))
    fixture_two, _, two = _run(tmp_path / "two", BoundedProducer(("discounting_association", "product_composition_association"), wording="two"))
    one_refs = sorted(chain.diagnostic_proposition_ref for chain in one.chains)
    two_refs = sorted(chain.diagnostic_proposition_ref for chain in two.chains)
    assert one_refs == two_refs
    one_eval = sorted(
        _artifact_payload(fixture_one, R6ArtifactType.PRETEST_DIAGNOSTIC_EVALUATION, chain.pretest_evaluation_ref)["evidence_readiness"]
        for chain in one.chains
    )
    two_eval = sorted(
        _artifact_payload(fixture_two, R6ArtifactType.PRETEST_DIAGNOSTIC_EVALUATION, chain.pretest_evaluation_ref)["evidence_readiness"]
        for chain in two.chains
    )
    assert one_eval == two_eval


def test_no_finding_claimdecision_or_ranking_construction_exists() -> None:
    source = open(service_module.__file__, encoding="utf-8").read()
    assert "ClaimDecision(" not in source
    assert "Finding(" not in source
    assert "most_likely" not in source
