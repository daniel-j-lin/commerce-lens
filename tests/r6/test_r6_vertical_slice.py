from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

import commerce_lens.application.r6_service as service_module
from commerce_lens.contracts.diagnostic import DiagnosticProposition
from commerce_lens.contracts.hypotheses import GovernedHypothesis
from commerce_lens.evidence.identifiers import canonical_json_bytes, canonical_json_fingerprint, stable_content_id
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.persistence.r6_repository import R6ArtifactIntegrityError, R6ArtifactType, R6Repository
from tests.persistence.test_r6_repository import _index, _rewrite_bytes
from tests.r6.support import case, metric_values, raw_artifact_payload, run_service_case


ALL_R6_ARTIFACT_TYPES = {item.value for item in R6ArtifactType}


def test_complete_product_vertical_persists_reloads_and_matches_independent_identity(tmp_path: Path) -> None:
    fixture = case("FX-R6-PROD-001A")
    run = run_service_case(tmp_path, fixture, handoff=True)

    assert metric_values(run.analysis) == {
        "revenue": (200, 120),
        "orders": (2, 2),
        "aov": (100, 60),
    }
    assert run.analysis.scalar.request.original_question_text == (
        "Why did Revenue decrease from the baseline period to the comparison period?"
    )
    assert run.outcome.completion_status.value == fixture.expected.completion_status
    assert len(run.outcome.chains) == 1
    chain = run.outcome.chains[0]
    assert chain.handoff_ref is not None

    proposition_payload = raw_artifact_payload(
        run,
        R6ArtifactType.DIAGNOSTIC_PROPOSITION.value,
        chain.diagnostic_proposition_ref,
    )
    assert fixture.expected.proposition_material is not None
    independently_computed = canonical_json_fingerprint(fixture.expected.proposition_material)
    independently_derived_id = stable_content_id("diagprop", independently_computed)
    assert independently_computed == fixture.expected.proposition_fingerprint
    assert independently_derived_id == fixture.expected.proposition_id
    assert proposition_payload["semantic_fingerprint"] == independently_computed
    assert proposition_payload["proposition_id"] == independently_derived_id

    proposition = DiagnosticProposition.model_validate(proposition_payload)
    registry = service_module._build_pretest_registry(
        proposition,
        run.producer.context.source_authority_views,
    )
    reopened = R6Repository(
        ArtifactStore(run.analysis.scalar.artifact_store.root),
        MetadataStore(run.analysis.scalar.metadata_store.db_path),
    )
    loaded_proposition = reopened.load_diagnostic_proposition(
        chain.diagnostic_proposition_ref,
        authority_registry=registry,
    )
    loaded_profile = reopened.load_resolved_required_evidence_profile(
        chain.resolved_profile_ref,
        authority_registry=registry,
    )
    loaded_judgments = reopened.load_requirement_judgment_bundle(
        chain.requirement_judgment_bundle_ref,
        profile=loaded_profile,
    )
    loaded_evaluation = reopened.load_pretest_diagnostic_evaluation(
        chain.pretest_evaluation_ref,
        authority_registry=registry,
    )
    loaded_provenance = reopened.load_generation_provenance(chain.generation_provenance_ref)
    loaded_hypothesis = reopened.load_governed_hypothesis(
        chain.governed_hypothesis_ref,
        authority_registry=registry,
    )
    loaded_handoff = reopened.load_r6_to_r7_handoff(
        chain.handoff_ref,
        authority_registry=registry,
    )

    assert loaded_proposition == proposition
    assert len(loaded_profile.dimension_applicability_decisions) == 12
    assert len({item.dimension for item in loaded_profile.dimension_applicability_decisions}) == 12
    assert loaded_judgments
    assert fixture.expected.profile_dimension_expectations is not None
    applicability = {
        item.dimension.value: item.applicability.value
        for item in loaded_profile.dimension_applicability_decisions
    }
    outcomes = {
        item.dimension.value: item.outcome.value
        for item in loaded_judgments if item.dimension is not None
    }
    assert {
        dimension: f"{applicability[dimension]}/{outcomes[dimension]}"
        for dimension in applicability
    } == fixture.expected.profile_dimension_expectations
    assert fixture.expected.requirement_judgments is not None
    assert {
        item.requirement_ref: item.outcome.value
        for item in loaded_judgments if item.dimension is None
    } == fixture.expected.requirement_judgments
    assert loaded_evaluation.test_eligibility.value == fixture.expected.test_eligibility
    assert loaded_evaluation.first_controlling_blocker == fixture.expected.first_controlling_blocker
    assert loaded_evaluation.analytical_outcome.value == fixture.expected.analytical_outcome
    assert loaded_evaluation.alternative_explanation_state.value == fixture.expected.alternative_explanation_state
    assert loaded_provenance.raw_candidate_artifact_ref == run.outcome.raw_candidate_artifact_ref
    assert loaded_hypothesis.diagnostic_proposition_ref == loaded_proposition.proposition_id
    assert loaded_handoff.governed_hypothesis_ref == loaded_hypothesis.governed_hypothesis_id
    assert loaded_handoff.r7_execution_permitted is False

    indexes = run.analysis.scalar.metadata_store.list_r6_artifact_indexes()
    assert {item.artifact_type for item in indexes} == ALL_R6_ARTIFACT_TYPES
    assert len(indexes) == 7


def test_authoritative_product_graph_is_noncausal_nonpromotional_and_unranked(tmp_path: Path) -> None:
    run = run_service_case(tmp_path, case("FX-R6-PROD-001A"), handoff=True)
    chain = run.outcome.chains[0]
    proposition = raw_artifact_payload(run, R6ArtifactType.DIAGNOSTIC_PROPOSITION.value, chain.diagnostic_proposition_ref)
    evaluation = raw_artifact_payload(run, R6ArtifactType.PRETEST_DIAGNOSTIC_EVALUATION.value, chain.pretest_evaluation_ref)
    hypothesis = raw_artifact_payload(run, R6ArtifactType.GOVERNED_HYPOTHESIS.value, chain.governed_hypothesis_ref)
    handoff = raw_artifact_payload(run, R6ArtifactType.R6_TO_R7_HANDOFF.value, chain.handoff_ref)

    assert proposition["relationship"]["relationship_type"] == "association"
    assert proposition["maximum_permitted_meaning"] == "proposal for a future bounded non-causal association test"
    assert {"explanation or causality", "primacy or support"}.issubset(proposition["prohibited_meanings"])
    assert evaluation["analytical_outcome"] == "NOT_EVALUATED"
    assert evaluation["alternative_explanation_state"] == "NOT_COMPLETED"
    assert set(hypothesis) == set(GovernedHypothesis.model_fields)
    assert handoff["test_eligibility"] == "NOT_ELIGIBLE"
    assert not {"finding", "claim_decision", "rank", "score", "primary", "probability", "confidence"} & {
        key.lower() for artifact in (proposition, evaluation, hypothesis, handoff) for key in artifact
    }


def test_large_r4_entry_is_mechanical_only_and_hostile_wording_stays_raw(tmp_path: Path) -> None:
    run = run_service_case(tmp_path, case("FX-R6-R4-001A"))
    chain = run.outcome.chains[0]
    proposition = raw_artifact_payload(run, R6ArtifactType.DIAGNOSTIC_PROPOSITION.value, chain.diagnostic_proposition_ref)
    judgments = raw_artifact_payload(run, R6ArtifactType.REQUIREMENT_JUDGMENT_BUNDLE.value, chain.requirement_judgment_bundle_ref)["judgments"]
    raw_ref = run.analysis.scalar.metadata_store.get_artifact_reference(run.outcome.raw_candidate_artifact_ref)
    assert raw_ref is not None
    raw_batch = json.loads(run.analysis.scalar.artifact_store.safe_path(raw_ref.path).read_text(encoding="utf-8"))

    assert proposition["source_mechanical_result_refs"] == [
        run.analysis.r4_outcome.validation.validated_result.validated_result_id
    ]
    assert proposition["relationship"]["relationship_type"] == "association"
    assert "new products caused growth" in raw_batch["candidates"][0]["non_authoritative_wording"]
    assert proposition["display_wording"] is None
    assert all(
        run.analysis.r4_outcome.validation.validated_result.validated_result_id not in item["evidence_refs"]
        for item in judgments
    )


def test_persisted_handoff_lineage_tamper_fails_after_superficial_hash_recomputation(tmp_path: Path) -> None:
    fixture = case("FX-R6-TAMPER-001B")
    run = run_service_case(tmp_path, fixture, handoff=True)
    chain = run.outcome.chains[0]
    assert chain.handoff_ref is not None
    proposition_payload = raw_artifact_payload(
        run,
        R6ArtifactType.DIAGNOSTIC_PROPOSITION.value,
        chain.diagnostic_proposition_ref,
    )
    proposition = DiagnosticProposition.model_validate(proposition_payload)
    registry = service_module._build_pretest_registry(proposition, run.producer.context.source_authority_views)
    graph = SimpleNamespace(repo=run.repository)
    index, _, path = _index(graph, R6ArtifactType.R6_TO_R7_HANDOFF, chain.handoff_ref)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["evidence_readiness"] = "READY_FOR_TEST"
    payload["handoff_fingerprint"] = service_module.r6_to_r7_handoff_semantic_fingerprint(payload)
    raw = canonical_json_bytes(run.repository._normalize_payload(R6ArtifactType.R6_TO_R7_HANDOFF, payload))
    _rewrite_bytes(graph, R6ArtifactType.R6_TO_R7_HANDOFF, chain.handoff_ref, raw)
    changed = index.model_copy(update={"semantic_fingerprint": payload["handoff_fingerprint"]})
    with sqlite3.connect(run.repository.metadata_store.db_path) as conn:
        conn.execute(
            "UPDATE r6_artifact_index SET semantic_fingerprint = ?, record_json = ? "
            "WHERE artifact_type = ? AND artifact_id = ?",
            (
                changed.semantic_fingerprint,
                changed.model_dump_json(),
                R6ArtifactType.R6_TO_R7_HANDOFF.value,
                chain.handoff_ref,
            ),
        )
    with pytest.raises(R6ArtifactIntegrityError) as error:
        run.repository.load_r6_to_r7_handoff(chain.handoff_ref, authority_registry=registry)
    assert error.value.code == fixture.expected.diagnostic_code == "lineage_mismatch"
