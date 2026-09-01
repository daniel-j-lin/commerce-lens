from __future__ import annotations

import json
import sqlite3
from decimal import Decimal

import pytest

from commerce_lens.contracts.common import ClaimState, ClaimType, MetricState, ScopeDefinition, ScopeFilter
from commerce_lens.contracts.evidence import ClaimCandidate, ClaimPropositionType, EvidenceRole, claim_candidate_semantic_fingerprint
from commerce_lens.evidence.claim_admissibility import (
    CLAIM_POLICY_ID,
    CLAIM_POLICY_VERSION,
    ClaimAdmissibilityError,
    evaluate_claim_admissibility,
    persist_claim_candidate,
    verify_claim_decision_artifact,
)
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, canonical_json_bytes, sha256_file, stable_content_id
from commerce_lens.persistence.metadata_store import MetadataStore, SCHEMA_VERSION
from commerce_lens.contracts.common import ArtifactReference
from tests.evidence.test_admissibility import (
    _admit,
    _delete_row,
    _fixture,
    _replace_evidence_artifact_content,
    _replace_request,
    _replace_sufficiency,
    _replace_validated_artifact_authority,
    _row,
    _set_admissibility_record_artifact_ref,
    _set_validation_record_status,
    _tamper_evidence_artifact,
    _tamper_executed_artifact,
    _tamper_validation_record,
    _validate,
    _validated_revenue_change_fixture,
)


def test_revenue_orders_and_numeric_aov_descriptive_claims_are_admissible(tmp_path) -> None:
    cases = (
        ("revenue", Decimal("10.00")),
        ("orders", 1),
        ("aov", Decimal("10.00")),
    )
    for metric_ref, expected_value in cases:
        fixture, result, evidence = _evidence_chain(tmp_path / metric_ref, metric_ref)
        candidate = _candidate_from_evidence(fixture, result, evidence)

        decision = _persist_and_decide(fixture, candidate)

        assert result.value == expected_value
        assert decision.claim_state is ClaimState.ADMISSIBLE
        assert decision.failure_code is None
        assert decision.policy_id == CLAIM_POLICY_ID
        assert decision.policy_version == CLAIM_POLICY_VERSION
        assert decision.supporting_evidence_refs == (evidence.evidence_id,)
        assert not fixture.metadata_store.list_claim_decisions()[-1].required_qualifications


def test_revenue_change_descriptive_claim_is_admissible_without_recomputing_formula(tmp_path) -> None:
    fixture, result, evidence = _evidence_chain(tmp_path, "revenue_change")
    candidate = _candidate_from_evidence(fixture, result, evidence)

    decision = _persist_and_decide(fixture, candidate)

    assert result.value == Decimal("20.00")
    assert decision.claim_state is ClaimState.ADMISSIBLE
    assert decision.baseline_period_ref == "baseline"
    assert decision.comparison_period_ref == "comparison"
    assert decision.period_role == "baseline_and_comparison"


def test_governed_aov_undefined_state_claim_is_admissible(tmp_path) -> None:
    fixture, result, evidence = _evidence_chain(tmp_path, "aov_undefined")
    candidate = _candidate_from_evidence(
        fixture,
        result,
        evidence,
        proposition_type=ClaimPropositionType.METRIC_STATE_IS,
        claimed_value=None,
        claimed_metric_state=MetricState.UNDEFINED,
        undefined_reason="orders_equals_zero",
    )

    decision = _persist_and_decide(fixture, candidate)

    assert evidence.evidence_role is EvidenceRole.METRIC_STATE
    assert decision.claim_state is ClaimState.ADMISSIBLE


def test_repeated_equivalent_evaluation_has_unique_events_and_stable_semantic_fingerprints(tmp_path) -> None:
    fixture, result, evidence = _evidence_chain(tmp_path, "revenue")
    candidate = persist_claim_candidate(_candidate_from_evidence(fixture, result, evidence), artifact_store=fixture.artifact_store, metadata_store=fixture.metadata_store)

    first = evaluate_claim_admissibility(claim_candidate_id=candidate.claim_candidate_id, artifact_store=fixture.artifact_store, metadata_store=fixture.metadata_store).claim_decision
    second = evaluate_claim_admissibility(claim_candidate_id=candidate.claim_candidate_id, artifact_store=fixture.artifact_store, metadata_store=fixture.metadata_store).claim_decision

    assert first.claim_decision_id != second.claim_decision_id
    assert first.decision_fingerprint == second.decision_fingerprint
    assert candidate.claim_candidate_fingerprint == claim_candidate_semantic_fingerprint(candidate)
    equivalent_new_event = candidate.model_copy(update={"claim_candidate_id": "clmcand_equivalent_new_event"})
    assert claim_candidate_semantic_fingerprint(equivalent_new_event) == candidate.claim_candidate_fingerprint


def test_claim_decision_persists_immutable_verifiable_artifact(tmp_path) -> None:
    fixture, result, evidence = _evidence_chain(tmp_path, "orders")
    candidate = _candidate_from_evidence(fixture, result, evidence)
    decision = _persist_and_decide(fixture, candidate)
    artifact = _decision_artifact(fixture, decision.claim_decision_id)

    restored = verify_claim_decision_artifact(
        artifact,
        artifact_store=fixture.artifact_store,
        metadata_store=fixture.metadata_store,
        expected_decision=decision,
        claim_candidate_fingerprint=fixture.metadata_store.get_claim_candidate(decision.claim_candidate_ref, fixture.artifact_store).claim_candidate_fingerprint,
    )

    assert restored == decision
    _tamper_artifact(fixture, artifact, {"claim_state": ClaimState.INADMISSIBLE.value, "failure_code": "tampered"})
    with pytest.raises(ClaimAdmissibilityError) as exc_info:
        verify_claim_decision_artifact(artifact, artifact_store=fixture.artifact_store, metadata_store=fixture.metadata_store)
    assert exc_info.value.failure_code == "claim_decision_artifact_hash_mismatch"


@pytest.mark.parametrize("claim_type", [ClaimType.DIAGNOSTIC, ClaimType.PREDICTIVE, ClaimType.CAUSAL, ClaimType.PRESCRIPTIVE])
def test_unsupported_claim_types_fail_closed(tmp_path, claim_type) -> None:
    fixture, result, evidence = _evidence_chain(tmp_path, "revenue")
    candidate = _candidate_from_evidence(fixture, result, evidence, claim_type=claim_type)

    decision = _persist_and_decide(fixture, candidate)

    assert decision.claim_state is ClaimState.INADMISSIBLE
    assert decision.failure_code == "unsupported_claim_type"


@pytest.mark.parametrize(
    ("update", "expected_code"),
    [
        ({"claimed_value": Decimal("999.00")}, "wrong_claimed_value"),
        ({"metric_ref": "orders"}, "wrong_metric"),
        ({"metric_definition_version": "wrong"}, "wrong_metric_definition_version"),
        ({"period_ref": "outside"}, "wrong_period"),
        ({"period_role": "forecast"}, "wrong_period_role"),
        ({"population_ref": "pop_wrong"}, "wrong_population"),
        ({"population_fingerprint": "f" * 64}, "wrong_population_fingerprint"),
        ({"intended_scope": ScopeDefinition(scope_id="currency_eur", filters=(ScopeFilter(field="currency", operator="equals", value="EUR"),))}, "wrong_scope"),
        ({"currency": "EUR"}, "wrong_currency"),
        ({"unit": "wrong_unit"}, "wrong_unit"),
        ({"dataset_ref_id": "ds_wrong"}, "wrong_dataset"),
        ({"canonical_dataset_ref_id": "cds_wrong"}, "wrong_canonical_dataset"),
        ({"canonical_dataset_fingerprint": "e" * 64}, "wrong_canonical_dataset"),
    ],
)
def test_claim_evidence_semantic_mismatches_fail_closed(tmp_path, update, expected_code) -> None:
    fixture, result, evidence = _evidence_chain(tmp_path, "revenue")
    candidate = _candidate_from_evidence(fixture, result, evidence).model_copy(update=update)

    decision = _persist_and_decide(fixture, candidate)

    assert decision.claim_state is ClaimState.INADMISSIBLE
    assert decision.failure_code == expected_code


def test_revenue_change_wrong_baseline_comparison_context_fails_closed(tmp_path) -> None:
    fixture, result, evidence = _evidence_chain(tmp_path, "revenue_change")
    candidate = _candidate_from_evidence(fixture, result, evidence).model_copy(update={"baseline_period_ref": "comparison"})

    decision = _persist_and_decide(fixture, candidate)

    assert decision.claim_state is ClaimState.INADMISSIBLE
    assert decision.failure_code == "wrong_baseline_comparison_context"


@pytest.mark.parametrize(
    ("metric_ref", "expected_code"),
    [
        ("revenue_change_pct", "unsupported_metric"),
        ("product_revenue", "unsupported_metric"),
    ],
)
def test_unsupported_metrics_fail_closed(tmp_path, metric_ref, expected_code) -> None:
    fixture, result, evidence = _evidence_chain(tmp_path, "revenue")
    candidate = _candidate_from_evidence(fixture, result, evidence).model_copy(update={"metric_ref": metric_ref})

    decision = _persist_and_decide(fixture, candidate)

    assert decision.claim_state is ClaimState.INADMISSIBLE
    assert decision.failure_code == expected_code


def test_unrepresentable_material_claim_and_wrong_policy_fail_closed(tmp_path) -> None:
    fixture, result, evidence = _evidence_chain(tmp_path, "orders")
    candidate = _candidate_from_evidence(fixture, result, evidence).model_copy(update={"metric_definition_version": None})
    persisted = persist_claim_candidate(candidate, artifact_store=fixture.artifact_store, metadata_store=fixture.metadata_store)

    decision = evaluate_claim_admissibility(claim_candidate_id=persisted.claim_candidate_id, artifact_store=fixture.artifact_store, metadata_store=fixture.metadata_store).claim_decision
    wrong_policy = evaluate_claim_admissibility(claim_candidate_id=persisted.claim_candidate_id, artifact_store=fixture.artifact_store, metadata_store=fixture.metadata_store, policy_version="wrong").claim_decision

    assert decision.failure_code == "unrepresentable_material_claim"
    assert wrong_policy.failure_code == "policy_version_mismatch"


@pytest.mark.parametrize(
    ("tamper", "expected_code"),
    [
        ("missing_evidence_ref", "missing_supporting_evidence"),
        ("ambiguous_evidence_ref", "duplicate_or_ambiguous_supporting_evidence"),
        ("missing_persisted_evidence", "missing_persisted_evidence_authority"),
        ("forged_evidence_object", "forged_evidence_object"),
        ("tampered_evidence_artifact", "tampered_evidence_artifact"),
        ("forged_evidence_fingerprint", "tampered_evidence_artifact"),
        ("wrong_validated_result", "wrong_validated_result"),
    ],
)
def test_evidence_authority_failures_are_inadmissible(tmp_path, tamper, expected_code) -> None:
    fixture, result, evidence = _evidence_chain(tmp_path, "revenue")
    candidate = _candidate_from_evidence(fixture, result, evidence)
    supplied_evidence = None
    if tamper == "missing_evidence_ref":
        candidate = candidate.model_copy(update={"supporting_evidence_refs": ()})
    elif tamper == "ambiguous_evidence_ref":
        candidate = candidate.model_copy(update={"supporting_evidence_refs": (evidence.evidence_id, evidence.evidence_id)})
    elif tamper == "missing_persisted_evidence":
        candidate = candidate.model_copy(update={"supporting_evidence_refs": ("ev_missing",)})
    elif tamper == "forged_evidence_object":
        supplied_evidence = evidence.model_copy(update={"dataset_ref_id": "ds_wrong"})
    elif tamper == "tampered_evidence_artifact":
        artifact = _latest_evidence_artifact(fixture, evidence.evidence_id)
        _tamper_evidence_artifact(fixture, artifact, {"dataset_ref_id": "ds_wrong"})
    elif tamper == "forged_evidence_fingerprint":
        artifact = _latest_evidence_artifact(fixture, evidence.evidence_id)
        _tamper_evidence_artifact(fixture, artifact, {"evidence_fingerprint": "f" * 64})
    elif tamper == "wrong_validated_result":
        candidate = candidate.model_copy(update={"supporting_validated_result_refs": ("valres_wrong",)})

    persisted = persist_claim_candidate(candidate, artifact_store=fixture.artifact_store, metadata_store=fixture.metadata_store)
    decision = evaluate_claim_admissibility(
        claim_candidate_id=persisted.claim_candidate_id,
        artifact_store=fixture.artifact_store,
        metadata_store=fixture.metadata_store,
        supplied_evidence=supplied_evidence,
    ).claim_decision

    assert decision.claim_state is ClaimState.INADMISSIBLE
    assert decision.failure_code == expected_code


@pytest.mark.parametrize(
    ("tamper", "expected_code"),
    [
        ("missing_validation_record", "missing_validation_record"),
        ("failed_validation_record", "tampered_validation_record"),
        ("tampered_validation_record", "tampered_validation_record"),
        ("executed_result_lineage", "mismatched_executed_result_lineage"),
    ],
)
def test_upstream_validation_and_execution_authority_failures_are_inadmissible(tmp_path, tamper, expected_code) -> None:
    fixture, result, evidence = _evidence_chain(tmp_path, "revenue")
    candidate = _candidate_from_evidence(fixture, result, evidence)
    if tamper == "missing_validation_record":
        _delete_row(fixture.metadata_store, "validation_records", "validation_id", result.required_validation_record_ids[0])
    elif tamper == "failed_validation_record":
        _set_validation_record_status(fixture, result.required_validation_record_ids[0], "failed")
    elif tamper == "tampered_validation_record":
        _tamper_validation_record(fixture, result.required_validation_record_ids[0], {"validation_fingerprint": "f" * 64})
    elif tamper == "executed_result_lineage":
        _tamper_executed_artifact(fixture, result, "result_id", "result_wrong")

    decision = _persist_and_decide(fixture, candidate)

    assert decision.claim_state is ClaimState.INADMISSIBLE
    assert decision.failure_code == expected_code


def test_cross_request_and_cross_run_equal_value_substitution_fail_closed(tmp_path) -> None:
    fixture, result, evidence = _evidence_chain(tmp_path / "original", "revenue")
    foreign, _, foreign_evidence = _evidence_chain(tmp_path / "foreign", "revenue")
    candidate = _candidate_from_evidence(fixture, result, evidence).model_copy(
        update={
            "supporting_evidence_refs": (foreign_evidence.evidence_id,),
            "supporting_validated_result_refs": foreign_evidence.validated_result_ids,
        }
    )
    foreign.metadata_store.insert_claim_candidate(candidate, foreign.artifact_store)

    decision = evaluate_claim_admissibility(claim_candidate_id=candidate.claim_candidate_id, artifact_store=foreign.artifact_store, metadata_store=foreign.metadata_store).claim_decision

    assert evidence.evidence_id != foreign_evidence.evidence_id
    assert result.value == Decimal("10.00")
    assert decision.claim_state is ClaimState.INADMISSIBLE
    assert decision.failure_code == "cross_request_substitution"


def test_candidate_persistence_and_tamper_failures(tmp_path) -> None:
    fixture, result, evidence = _evidence_chain(tmp_path, "revenue")
    candidate = _candidate_from_evidence(fixture, result, evidence)

    missing = evaluate_claim_admissibility(claim_candidate_id=candidate.claim_candidate_id, artifact_store=fixture.artifact_store, metadata_store=fixture.metadata_store).claim_decision
    persisted = persist_claim_candidate(candidate, artifact_store=fixture.artifact_store, metadata_store=fixture.metadata_store)
    supplied_differs = evaluate_claim_admissibility(
        claim_candidate_id=persisted.claim_candidate_id,
        artifact_store=fixture.artifact_store,
        metadata_store=fixture.metadata_store,
        supplied_candidate=persisted.model_copy(update={"period_ref": "wrong"}),
    ).claim_decision

    assert missing.failure_code == "claim_candidate_not_persisted"
    assert supplied_differs.failure_code == "claim_candidate_fingerprint_mismatch"

    artifact = _candidate_artifact(fixture, persisted.claim_candidate_id)
    _tamper_artifact(fixture, artifact, {"period_ref": "wrong"})
    tampered = evaluate_claim_admissibility(claim_candidate_id=persisted.claim_candidate_id, artifact_store=fixture.artifact_store, metadata_store=fixture.metadata_store).claim_decision
    assert tampered.failure_code == "claim_candidate_artifact_hash_mismatch"


def test_candidate_missing_artifact_and_semantic_fingerprint_mismatch_fail_closed(tmp_path) -> None:
    fixture, result, evidence = _evidence_chain(tmp_path / "missing", "orders")
    persisted = persist_claim_candidate(_candidate_from_evidence(fixture, result, evidence), artifact_store=fixture.artifact_store, metadata_store=fixture.metadata_store)
    artifact = _candidate_artifact(fixture, persisted.claim_candidate_id)
    fixture.artifact_store.safe_path(artifact.path).unlink()

    missing_artifact = evaluate_claim_admissibility(claim_candidate_id=persisted.claim_candidate_id, artifact_store=fixture.artifact_store, metadata_store=fixture.metadata_store).claim_decision

    fixture2, result2, evidence2 = _evidence_chain(tmp_path / "fingerprint", "orders")
    persisted2 = persist_claim_candidate(_candidate_from_evidence(fixture2, result2, evidence2), artifact_store=fixture2.artifact_store, metadata_store=fixture2.metadata_store)
    _rewrite_candidate_authority(fixture2, persisted2.claim_candidate_id, {"claim_candidate_fingerprint": "f" * 64})
    mismatch = evaluate_claim_admissibility(claim_candidate_id=persisted2.claim_candidate_id, artifact_store=fixture2.artifact_store, metadata_store=fixture2.metadata_store).claim_decision

    assert missing_artifact.failure_code == "claim_candidate_artifact_missing"
    assert mismatch.failure_code == "claim_candidate_fingerprint_mismatch"


def test_aov_undefined_negative_cases_do_not_invalidate_unrelated_evidence(tmp_path) -> None:
    fixture, result, evidence = _evidence_chain(tmp_path, "aov_undefined")
    numeric_candidate = _candidate_from_evidence(
        fixture,
        result,
        evidence,
        proposition_type=ClaimPropositionType.METRIC_VALUE_EQUALS,
        claimed_value=Decimal("0"),
    )
    wrong_reason = _candidate_from_evidence(
        fixture,
        result,
        evidence,
        proposition_type=ClaimPropositionType.METRIC_STATE_IS,
        claimed_value=None,
        claimed_metric_state=MetricState.UNDEFINED,
        undefined_reason="other_reason",
    )
    non_aov = _candidate_from_evidence(
        fixture,
        result,
        evidence,
        metric_ref="revenue",
        proposition_type=ClaimPropositionType.METRIC_STATE_IS,
        claimed_value=None,
        claimed_metric_state=MetricState.UNDEFINED,
        undefined_reason="orders_equals_zero",
    )

    assert _persist_and_decide(fixture, numeric_candidate).failure_code == "wrong_evidence_role"
    assert _persist_and_decide(fixture, wrong_reason).failure_code == "wrong_undefined_reason"
    assert _persist_and_decide(fixture, non_aov).failure_code == "wrong_metric"
    assert fixture.metadata_store.get_evidence_admissibility_record(_latest_evidence_record_id(fixture, evidence.evidence_id)).status.value == "passed"


def test_wrong_aov_evidence_role_fails_closed(tmp_path) -> None:
    fixture, result, evidence = _evidence_chain(tmp_path, "aov")
    candidate = _candidate_from_evidence(
        fixture,
        result,
        evidence,
        proposition_type=ClaimPropositionType.METRIC_STATE_IS,
        claimed_value=None,
        claimed_metric_state=MetricState.UNDEFINED,
        undefined_reason="orders_equals_zero",
    )

    decision = _persist_and_decide(fixture, candidate)

    assert decision.failure_code == "wrong_evidence_role"


def test_schema_v5_to_v6_migration_and_claim_rows_round_trip(tmp_path) -> None:
    db_path = tmp_path / "legacy_v5.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE schema_version (id INTEGER PRIMARY KEY CHECK (id = 1), version INTEGER NOT NULL)")
    conn.execute("INSERT INTO schema_version (id, version) VALUES (1, 5)")
    from tests.evidence.test_admissibility import _create_supported_v4_tables

    _create_supported_v4_tables(conn)
    conn.execute("CREATE TABLE analysis_requests (request_id TEXT PRIMARY KEY, canonical_business_question_id TEXT NOT NULL, dataset_ref_id TEXT NOT NULL, request_artifact_id TEXT NOT NULL, record_fingerprint TEXT NOT NULL, created_at TEXT NOT NULL, record_json TEXT NOT NULL)")
    conn.execute("CREATE TABLE data_sufficiency_results (sufficiency_id TEXT PRIMARY KEY, request_id TEXT NOT NULL, dataset_ref_id TEXT NOT NULL, canonical_dataset_ref_id TEXT, sufficiency_artifact_id TEXT NOT NULL, state TEXT NOT NULL, record_fingerprint TEXT NOT NULL, record_json TEXT NOT NULL)")
    conn.execute("CREATE TABLE evidence_admissibility_records (admissibility_id TEXT PRIMARY KEY, request_id TEXT, sufficiency_id TEXT, validated_result_id TEXT, metric_ref TEXT, status TEXT NOT NULL, failure_code TEXT, admissible_evidence_id TEXT, admissible_evidence_artifact_id TEXT, evidence_fingerprint TEXT, started_at TEXT NOT NULL, ended_at TEXT NOT NULL, record_json TEXT NOT NULL)")
    conn.commit()
    conn.close()

    store = MetadataStore(db_path)
    store.initialize()

    assert store.schema_version() == 6 == SCHEMA_VERSION
    with sqlite3.connect(db_path) as reopened:
        tables = {row[0] for row in reopened.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()}
    assert {"claim_candidates", "claim_decisions"}.issubset(tables)

    fixture, result, evidence = _evidence_chain(tmp_path / "rows", "revenue")
    decision = _persist_and_decide(fixture, _candidate_from_evidence(fixture, result, evidence))
    candidate = fixture.metadata_store.get_claim_candidate(decision.claim_candidate_ref, fixture.artifact_store)
    restored = fixture.metadata_store.get_claim_decision(decision.claim_decision_id, fixture.artifact_store, claim_candidate_fingerprint=candidate.claim_candidate_fingerprint)

    assert candidate.claim_candidate_fingerprint
    assert restored.policy_id == CLAIM_POLICY_ID
    assert restored.policy_version == CLAIM_POLICY_VERSION
    assert restored.claim_state is ClaimState.ADMISSIBLE
    assert restored.decision_fingerprint


def _evidence_chain(tmp_path, metric_ref: str):
    if metric_ref == "revenue_change":
        fixture, result = _validated_revenue_change_fixture(tmp_path)
    elif metric_ref == "aov":
        fixture = _fixture(tmp_path, ("aov",), [_row()])
        revenue = _validate(fixture, "revenue").validated_result
        orders = _validate(fixture, "orders").validated_result
        result = _validate(fixture, "aov", dependencies=(revenue, orders)).validated_result
    elif metric_ref == "aov_undefined":
        fixture = _fixture(tmp_path, ("aov",), [_row(eligibility_status="cancelled")])
        revenue = _validate(fixture, "revenue").validated_result
        orders = _validate(fixture, "orders").validated_result
        result = _validate(fixture, "aov", dependencies=(revenue, orders)).validated_result
    else:
        fixture = _fixture(tmp_path, (metric_ref,), [_row()])
        result = _validate(fixture, metric_ref).validated_result
    outcome = _admit(fixture, result)
    assert outcome.admissible_evidence is not None
    return fixture, result, outcome.admissible_evidence


def _candidate_from_evidence(
    fixture,
    result,
    evidence,
    *,
    claim_type=ClaimType.DESCRIPTIVE,
    metric_ref: str | None = None,
    proposition_type=ClaimPropositionType.METRIC_VALUE_EQUALS,
    claimed_value=Ellipsis,
    claimed_metric_state=None,
    undefined_reason=None,
):
    execution_record = fixture.metadata_store.get_execution_record(result.execution_id)
    if claimed_value is Ellipsis:
        claimed_value = result.value
    update = {}
    if result.metric_ref == "revenue_change":
        update = {
            "baseline_period_ref": execution_record.period_refs[0],
            "comparison_period_ref": execution_record.period_refs[1],
            "baseline_population_ref": execution_record.population_refs[0],
            "comparison_population_ref": execution_record.population_refs[1],
            "baseline_population_fingerprint": execution_record.population_fingerprints[0],
            "comparison_population_fingerprint": execution_record.population_fingerprints[1],
        }
    return ClaimCandidate(
        claim_id="claim_presentational_compat",
        claim_type=claim_type,
        metric_ref=metric_ref or result.metric_ref,
        metric_definition_version=result.metric_definition_version,
        request_id=evidence.request_id,
        dataset_ref_id=evidence.dataset_ref_id,
        canonical_dataset_ref_id=evidence.canonical_dataset_ref_id,
        canonical_dataset_fingerprint=evidence.canonical_dataset_fingerprint,
        intended_scope=evidence.scope,
        population_ref=evidence.population_ref,
        population_fingerprint=evidence.population_fingerprint,
        period_ref=evidence.period_ref,
        period_role=evidence.period_role,
        proposition_type=proposition_type,
        claimed_value=claimed_value,
        claimed_metric_state=claimed_metric_state,
        undefined_reason=undefined_reason,
        unit=result.unit,
        currency=result.currency,
        supporting_evidence_refs=(evidence.evidence_id,),
        supporting_validated_result_refs=evidence.validated_result_ids,
        proposed_meaning="non-authoritative presentation text",
        metadata={"presentation_only": True},
        **update,
    )


def _persist_and_decide(fixture, candidate):
    persisted = persist_claim_candidate(candidate, artifact_store=fixture.artifact_store, metadata_store=fixture.metadata_store)
    return evaluate_claim_admissibility(claim_candidate_id=persisted.claim_candidate_id, artifact_store=fixture.artifact_store, metadata_store=fixture.metadata_store).claim_decision


def _latest_evidence_record_id(fixture, evidence_id: str) -> str:
    return next(record.admissibility_id for record in fixture.metadata_store.list_evidence_admissibility_records() if record.admissible_evidence_id == evidence_id)


def _latest_evidence_artifact(fixture, evidence_id: str):
    record = fixture.metadata_store.get_evidence_admissibility_record(_latest_evidence_record_id(fixture, evidence_id))
    return record.admissible_evidence_artifact_ref


def _candidate_artifact(fixture, claim_candidate_id: str):
    with sqlite3.connect(fixture.metadata_store.db_path) as conn:
        artifact_id = conn.execute("SELECT claim_candidate_artifact_id FROM claim_candidates WHERE claim_candidate_id = ?", (claim_candidate_id,)).fetchone()[0]
    return fixture.metadata_store.get_artifact_reference(artifact_id)


def _decision_artifact(fixture, claim_decision_id: str):
    with sqlite3.connect(fixture.metadata_store.db_path) as conn:
        artifact_id = conn.execute("SELECT claim_decision_artifact_id FROM claim_decisions WHERE claim_decision_id = ?", (claim_decision_id,)).fetchone()[0]
    return fixture.metadata_store.get_artifact_reference(artifact_id)


def _tamper_artifact(fixture, artifact, updates: dict) -> None:
    path = fixture.artifact_store.safe_path(artifact.path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(updates)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _rewrite_candidate_authority(fixture, claim_candidate_id: str, updates: dict) -> None:
    artifact = _candidate_artifact(fixture, claim_candidate_id)
    path = fixture.artifact_store.safe_path(artifact.path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(updates)
    path.write_bytes(canonical_json_bytes(payload))
    fingerprint = sha256_file(path)
    refreshed = ArtifactReference(
        artifact_id=stable_content_id("art", fingerprint),
        path=artifact.path,
        fingerprint=fingerprint,
        media_type=artifact.media_type,
        size_bytes=path.stat().st_size,
    )
    fixture.metadata_store.insert_artifact_reference(refreshed)
    with sqlite3.connect(fixture.metadata_store.db_path) as conn:
        conn.execute(
            """
            UPDATE claim_candidates
            SET claim_candidate_artifact_id = ?, claim_candidate_fingerprint = ?,
                record_fingerprint = ?, record_json = ?
            WHERE claim_candidate_id = ?
            """,
            (
                refreshed.artifact_id,
                payload["claim_candidate_fingerprint"],
                canonical_json_fingerprint(payload),
                json.dumps(payload, sort_keys=True),
                claim_candidate_id,
            ),
        )
