from __future__ import annotations

import json
import sqlite3
from decimal import Decimal
from pathlib import Path

import pytest

from commerce_lens.canonical import canonicalize_dataset
from commerce_lens.contracts.common import (
    AvailableEvidence,
    ArtifactReference,
    ClaimType,
    EvidenceRequirement,
    FailureDetail,
    FailureStage,
    MetricState,
    ScopeDefinition,
)
from commerce_lens.contracts.evidence import AdmissibleEvidence, EvidenceAdmissibilityStatus, EvidenceRole
from commerce_lens.contracts.sufficiency import MetricEligibility, SufficiencyState
from commerce_lens.contracts.validation import ValidatedResult, ValidationStatus
from commerce_lens.engine import execute_plan
from commerce_lens.engine.plan_builder import build_execution_plan
from commerce_lens.evidence.admissibility import evaluate_evidence_admissibility
from commerce_lens.evidence.identifiers import canonical_json_bytes, sha256_file, stable_content_id
from commerce_lens.persistence.metadata_store import MetadataStore, SCHEMA_VERSION
from commerce_lens.validation import validate_executed_result
from tests.engine.test_execution import (
    _canonicalization_request,
    _record,
    _registered_source,
    _request,
    _result,
    _row,
    _sufficiency,
)
from tests.persistence.test_metadata_store import _create_supported_v1_tables, _create_supported_v2_tables


def test_valid_revenue_orders_and_aov_become_metric_value_evidence(tmp_path) -> None:
    for metric_ref, expected_value in (
        ("revenue", Decimal("10.00")),
        ("orders", 1),
        ("aov", Decimal("10.00")),
    ):
        fixture = _fixture(tmp_path / metric_ref, (metric_ref,), [_row()])
        if metric_ref == "aov":
            revenue = _validate(fixture, "revenue").validated_result
            orders = _validate(fixture, "orders").validated_result
            validation = _validate(fixture, "aov", dependencies=(revenue, orders))
        else:
            validation = _validate(fixture, metric_ref)

        outcome = _admit(fixture, validation.validated_result)

        assert outcome.admissibility_record.status is EvidenceAdmissibilityStatus.PASSED
        assert outcome.admissible_evidence is not None
        assert outcome.admissible_evidence.validated_result_ids == (
            validation.validated_result.validated_result_id,
        )
        assert outcome.admissible_evidence.evidence_role is EvidenceRole.METRIC_VALUE
        assert outcome.admissible_evidence.metric_ref == metric_ref
        assert validation.validated_result.value == expected_value
        assert _restored_evidence(fixture, outcome).evidence_fingerprint == outcome.admissible_evidence.evidence_fingerprint


def test_governed_aov_undefined_becomes_metric_state_evidence(tmp_path) -> None:
    fixture = _fixture(tmp_path, ("aov",), [_row(eligibility_status="cancelled")])
    revenue = _validate(fixture, "revenue").validated_result
    orders = _validate(fixture, "orders").validated_result
    aov = _validate(fixture, "aov", dependencies=(revenue, orders)).validated_result

    outcome = _admit(fixture, aov)

    assert outcome.admissibility_record.status is EvidenceAdmissibilityStatus.PASSED
    assert outcome.admissible_evidence.evidence_role is EvidenceRole.METRIC_STATE
    assert outcome.admissible_evidence.metric_ref == "aov"
    assert aov.value is None
    assert aov.metric_state is MetricState.UNDEFINED
    assert aov.undefined_reason == "orders_equals_zero"


def test_partial_overall_sufficiency_allows_independently_eligible_metric(tmp_path) -> None:
    fixture = _fixture(
        tmp_path,
        ("revenue", "orders"),
        [_row()],
        ineligible={
            "orders": (
                FailureDetail(
                    stage=FailureStage.SUFFICIENCY,
                    reason="orders chain blocked",
                    dependency_scope="orders",
                    independent_chains_may_continue=True,
                ),
            )
        },
    )
    validation = _validate(fixture, "revenue")

    outcome = _admit(fixture, validation.validated_result)

    assert fixture.sufficiency.state is SufficiencyState.PARTIAL
    assert outcome.admissibility_record.status is EvidenceAdmissibilityStatus.PASSED


def test_repeated_equivalent_evaluations_have_distinct_events_and_same_fingerprint(tmp_path) -> None:
    fixture = _fixture(tmp_path, ("revenue",), [_row()])
    validation = _validate(fixture, "revenue")

    first = _admit(fixture, validation.validated_result)
    second = _admit(fixture, validation.validated_result)

    assert first.admissibility_record.admissibility_id != second.admissibility_record.admissibility_id
    assert first.admissibility_record.evidence_fingerprint == second.admissibility_record.evidence_fingerprint
    assert first.admissibility_record.started_at <= first.admissibility_record.ended_at
    assert len(fixture.metadata_store.list_evidence_admissibility_records()) == 2


def test_applicable_required_evidence_selection_is_retained(tmp_path) -> None:
    fixture = _fixture(tmp_path, ("revenue", "orders"), [_row()])
    validation = _validate(fixture, "revenue")

    outcome = _admit(fixture, validation.validated_result)

    assert outcome.admissible_evidence.applicable_required_evidence_requirement_ids == (
        "req_global",
        "req_revenue",
    )
    assert "req_orders" not in outcome.admissible_evidence.applicable_required_evidence_requirement_ids
    assert "req_revenue_diagnostic" not in outcome.admissible_evidence.applicable_required_evidence_requirement_ids


@pytest.mark.parametrize(
    ("claim_type", "expected_code"),
    [
        (ClaimType.DIAGNOSTIC, "unsupported_claim_type_for_p6_001"),
        (ClaimType.PREDICTIVE, "unsupported_claim_type_for_p6_001"),
        (ClaimType.CAUSAL, "unsupported_claim_type_for_p6_001"),
        (ClaimType.PRESCRIPTIVE, "unsupported_claim_type_for_p6_001"),
    ],
)
def test_unsupported_claim_types_fail_closed(tmp_path, claim_type, expected_code) -> None:
    fixture = _fixture(tmp_path, ("revenue",), [_row()])
    validation = _validate(fixture, "revenue")

    outcome = _admit(fixture, validation.validated_result, claim_type=claim_type)

    assert outcome.admissible_evidence is None
    assert outcome.admissibility_record.status is EvidenceAdmissibilityStatus.FAILED
    assert outcome.admissibility_record.failure_code == expected_code


@pytest.mark.parametrize(
    ("tamper", "expected_code"),
    [
        ("missing_request", "analysis_request_missing"),
        ("caller_request_differs", "analysis_request_tamper_or_mismatch"),
        ("tampered_request", "analysis_request_tamper_or_mismatch"),
        ("missing_sufficiency", "sufficiency_record_missing"),
        ("caller_sufficiency_differs", "sufficiency_tamper_or_mismatch"),
        ("tampered_sufficiency", "sufficiency_tamper_or_mismatch"),
        ("missing_eligibility", "sufficiency_metric_eligibility_absent"),
        ("duplicate_eligibility", "sufficiency_metric_eligibility_duplicate"),
        ("ineligible", "sufficiency_not_eligible"),
        ("missing_applicable_requirement", "required_evidence_context_missing"),
        ("wrong_metric", "required_evidence_metric_mismatch"),
        ("wrong_metric_version", "metric_definition_mismatch"),
        ("wrong_period", "period_mismatch"),
        ("wrong_population", "population_mismatch"),
        ("wrong_scope", "population_mismatch"),
        ("wrong_dataset", "dataset_mismatch"),
        ("wrong_canonical_dataset", "dataset_mismatch"),
        ("missing_validated_result", "validated_result_metadata_missing"),
        ("tampered_validated_artifact", "validated_result_artifact_hash_mismatch"),
        ("schema_invalid_validated_artifact", "validated_result_schema_invalid"),
        ("incomplete_validation_bundle", "validation_bundle_incomplete"),
        ("failed_validation_record", "validation_record_failed"),
        ("forged_rule_fingerprint", "validation_fingerprint_mismatch"),
        ("forged_bundle_fingerprint", "validation_fingerprint_mismatch"),
        ("missing_execution_record", "execution_record_lineage_missing"),
        ("wrong_executed_result_lineage", "executed_result_lineage_missing"),
        ("qualified_state", "qualified_metric_state_not_supported_p6_001"),
        ("inadmissible_state", "metric_state_not_admissible"),
        ("undefined_revenue", "undefined_state_context_mismatch"),
        ("undefined_orders", "undefined_state_context_mismatch"),
        ("aov_wrong_reason", "undefined_state_context_mismatch"),
        ("aov_numeric_undefined", "undefined_state_context_mismatch"),
        ("aov_undefined_metric_value", "undefined_aov_metric_value_not_supported_p6_001"),
    ],
)
def test_admissibility_fail_closed_cases(tmp_path, tamper, expected_code) -> None:
    metric = "aov" if tamper.startswith("aov_") else "revenue"
    rows = [_row(eligibility_status="cancelled")] if metric == "aov" else [_row()]
    fixture = _fixture(tmp_path, (metric,), rows)
    if metric == "aov":
        revenue = _validate(fixture, "revenue").validated_result
        orders = _validate(fixture, "orders").validated_result
        validation = _validate(fixture, "aov", dependencies=(revenue, orders))
    else:
        validation = _validate(fixture, "revenue")
    result = validation.validated_result
    supplied_request = None
    supplied_sufficiency = None
    supplied_validated_result = result
    requested_role = EvidenceRole.METRIC_VALUE if tamper == "aov_undefined_metric_value" else None
    if tamper == "missing_request":
        _delete_row(fixture.metadata_store, "analysis_requests", "request_id", fixture.request.request_id)
    elif tamper == "caller_request_differs":
        supplied_request = fixture.request.model_copy(update={"dataset_ref_id": "ds_wrong"})
    elif tamper == "tampered_request":
        _tamper_json(fixture.metadata_store, "analysis_requests", "request_id", fixture.request.request_id, "dataset_ref_id", "ds_wrong")
    elif tamper == "missing_sufficiency":
        _delete_row(fixture.metadata_store, "data_sufficiency_results", "sufficiency_id", fixture.sufficiency.sufficiency_id)
    elif tamper == "caller_sufficiency_differs":
        supplied_sufficiency = fixture.sufficiency.model_copy(update={"dataset_ref_id": "ds_wrong"})
    elif tamper == "tampered_sufficiency":
        _tamper_json(fixture.metadata_store, "data_sufficiency_results", "sufficiency_id", fixture.sufficiency.sufficiency_id, "dataset_ref_id", "ds_wrong")
    elif tamper == "missing_eligibility":
        _replace_sufficiency(fixture, metric_eligibility=())
    elif tamper == "duplicate_eligibility":
        _replace_sufficiency(fixture, metric_eligibility=fixture.sufficiency.metric_eligibility * 2)
    elif tamper == "ineligible":
        _replace_sufficiency(
            fixture,
            metric_eligibility=(MetricEligibility(metric_ref=metric, eligible=False, metric_state=MetricState.INADMISSIBLE),),
        )
    elif tamper == "missing_applicable_requirement":
        _replace_request(fixture, required_evidence=())
    elif tamper == "wrong_metric":
        _replace_request(
            fixture,
            metrics=(fixture.request.metrics[0].model_copy(update={"metric_id": "orders"}),),
        )
    elif tamper == "wrong_metric_version":
        _replace_request(
            fixture,
            metrics=tuple(metric.model_copy(update={"definition_version": "wrong"}) for metric in fixture.request.metrics),
        )
    elif tamper == "wrong_period":
        _set_execution_record_period_refs(fixture, result.execution_id, ("outside",))
    elif tamper == "wrong_population":
        _set_execution_record_population_refs(fixture, result.execution_id, ("pop_wrong",))
    elif tamper == "wrong_scope":
        _set_execution_record_grouping(fixture, result.execution_id, "product")
    elif tamper == "wrong_dataset":
        _set_execution_record_dataset_ids(fixture, result.execution_id, ("ds_wrong",))
    elif tamper == "wrong_canonical_dataset":
        _replace_sufficiency(fixture, canonical_dataset_ref_id="cds_wrong")
    elif tamper == "missing_validated_result":
        result = result.model_copy(update={"validated_result_id": "valres_missing"})
    elif tamper == "tampered_validated_artifact":
        _tamper_validated_artifact(fixture, result, "value", "999.00")
    elif tamper == "schema_invalid_validated_artifact":
        _validated_artifact_path(fixture, result).write_text('{"validated_result_id": 1}', encoding="utf-8")
        _refresh_validated_artifact_reference(fixture, result)
    elif tamper == "incomplete_validation_bundle":
        _replace_validated_artifact_authority(fixture, result, {"required_validation_record_ids": result.required_validation_record_ids[:1]})
        supplied_validated_result = None
    elif tamper == "failed_validation_record":
        _set_validation_record_status(fixture, result.required_validation_record_ids[0], "failed")
    elif tamper == "forged_rule_fingerprint":
        _tamper_validation_record(fixture, result.required_validation_record_ids[0], {"validation_fingerprint": "f" * 64})
    elif tamper == "forged_bundle_fingerprint":
        _replace_validated_artifact_authority(fixture, result, {"validation_fingerprint": "f" * 64})
        supplied_validated_result = None
    elif tamper == "missing_execution_record":
        _delete_row(fixture.metadata_store, "execution_records", "execution_id", result.execution_id)
    elif tamper == "wrong_executed_result_lineage":
        _tamper_executed_artifact(fixture, result, "result_id", "result_wrong")
    elif tamper == "qualified_state":
        _replace_validated_artifact_authority(fixture, result, {"metric_state": MetricState.QUALIFIED})
        supplied_validated_result = None
    elif tamper == "inadmissible_state":
        _replace_validated_artifact_authority(fixture, result, {"metric_state": MetricState.INADMISSIBLE})
        supplied_validated_result = None
    elif tamper == "undefined_revenue":
        _replace_validated_artifact_authority(
            fixture,
            result,
            {"metric_state": MetricState.UNDEFINED, "value": None, "undefined_reason": "orders_equals_zero"},
        )
        supplied_validated_result = None
    elif tamper == "undefined_orders":
        _replace_validated_artifact_authority(
            fixture,
            result,
            {"metric_ref": "orders", "metric_state": MetricState.UNDEFINED, "value": None, "undefined_reason": "orders_equals_zero"},
        )
        supplied_validated_result = None
    elif tamper == "aov_wrong_reason":
        _replace_validated_artifact_authority(fixture, result, {"undefined_reason": "other_reason"})
        supplied_validated_result = None
    elif tamper == "aov_numeric_undefined":
        _replace_validated_artifact_authority(fixture, result, {"value": Decimal("0")})
        supplied_validated_result = None

    outcome = _admit(
        fixture,
        result,
        supplied_request=supplied_request,
        supplied_sufficiency=supplied_sufficiency,
        supplied_validated_result=supplied_validated_result,
        evidence_role=requested_role,
    )

    assert outcome.admissible_evidence is None
    assert outcome.admissibility_record.status is EvidenceAdmissibilityStatus.FAILED
    assert outcome.admissibility_record.failure_code == expected_code
    assert outcome.admissibility_record.admissible_evidence_id is None


def test_metadata_store_v5_persistence_and_migrations(tmp_path) -> None:
    store = MetadataStore(tmp_path / "new.sqlite")
    store.initialize()
    assert store.schema_version() == 5 == SCHEMA_VERSION
    _assert_v5_tables(store)

    fixture = _fixture(tmp_path / "roundtrip", ("revenue",), [_row()])
    assert fixture.metadata_store.get_analysis_request(fixture.request.request_id) == fixture.request
    assert fixture.metadata_store.get_data_sufficiency_result(fixture.sufficiency.sufficiency_id) == fixture.sufficiency
    with pytest.raises(RuntimeError, match="stable provenance record conflict"):
        fixture.metadata_store.insert_analysis_request(fixture.request.model_copy(update={"dataset_ref_id": "ds_conflict"}))
    with pytest.raises(RuntimeError, match="stable provenance record conflict"):
        fixture.metadata_store.insert_data_sufficiency_result(fixture.sufficiency.model_copy(update={"dataset_ref_id": "ds_conflict"}))

    for version, creator in ((1, _create_supported_v1_tables), (2, _create_supported_v2_tables), (3, _create_supported_v3_tables), (4, _create_supported_v4_tables)):
        db_path = tmp_path / f"legacy_{version}.sqlite"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE schema_version (id INTEGER PRIMARY KEY CHECK (id = 1), version INTEGER NOT NULL)")
        conn.execute("INSERT INTO schema_version (id, version) VALUES (1, ?)", (version,))
        creator(conn)
        conn.commit()
        conn.close()
        legacy = MetadataStore(db_path)
        legacy.initialize()
        assert legacy.schema_version() == SCHEMA_VERSION
        _assert_v5_tables(legacy)

    malformed = tmp_path / "malformed_v4.sqlite"
    conn = sqlite3.connect(malformed)
    conn.execute("CREATE TABLE schema_version (id INTEGER PRIMARY KEY CHECK (id = 1), version INTEGER NOT NULL)")
    conn.execute("INSERT INTO schema_version (id, version) VALUES (1, 4)")
    _create_supported_v3_tables(conn)
    conn.execute("CREATE TABLE validation_records (validation_id TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()
    with pytest.raises(RuntimeError, match="version 4 is incompatible"):
        MetadataStore(malformed).initialize()


class _Fixture:
    def __init__(self, request, sufficiency, plan, canonical, artifact_store, metadata_store, outcome) -> None:
        self.request = request
        self.sufficiency = sufficiency
        self.plan = plan
        self.canonical = canonical
        self.artifact_store = artifact_store
        self.metadata_store = metadata_store
        self.outcome = outcome


def _fixture(
    tmp_path: Path,
    metrics: tuple[str, ...],
    rows: list[dict[str, str]],
    *,
    ineligible: dict[str, tuple[FailureDetail, ...]] | None = None,
) -> _Fixture:
    tmp_path.mkdir(parents=True, exist_ok=True)
    source_metrics = tuple(dict.fromkeys((*metrics, "revenue", "orders"))) if "aov" in metrics else metrics
    dataset, artifact_store = _registered_source(tmp_path, rows, filename="orders.csv", source_type="csv")
    canonicalization = canonicalize_dataset(dataset, _canonicalization_request(dataset), artifact_store)
    request = _request(source_metrics, dataset.dataset_id, scope=ScopeDefinition(scope_id="all_eligible"))
    request = request.model_copy(
        update={
            "required_evidence": (
                EvidenceRequirement(requirement_id="req_global", description="global dataset authority"),
                EvidenceRequirement(requirement_id=f"req_{metrics[0]}", description="target metric authority", metric_ref=metrics[0]),
                EvidenceRequirement(requirement_id="req_orders", description="orders authority", metric_ref="orders"),
                EvidenceRequirement(
                    requirement_id=f"req_{metrics[0]}_diagnostic",
                    description="diagnostic-only authority",
                    metric_ref=metrics[0],
                    claim_type=ClaimType.DIAGNOSTIC,
                ),
            )
        }
    )
    sufficiency = _sufficiency(
        request,
        canonicalization.canonical_dataset.canonical_dataset_id,
        ineligible=ineligible,
    ).model_copy(
        update={
            "required_evidence": request.required_evidence,
            "available_evidence": (
                AvailableEvidence(
                    evidence_id="avail_target",
                    description="available target evidence",
                    source_ref=dataset.dataset_id,
                    satisfies_requirement_ids=("req_global", f"req_{metrics[0]}"),
                ),
            ),
        }
    )
    plan = build_execution_plan(request, sufficiency)
    metadata_store = MetadataStore(tmp_path / "registry.sqlite")
    metadata_store.initialize()
    metadata_store.insert_analysis_request(request)
    metadata_store.insert_data_sufficiency_result(sufficiency)
    outcome = execute_plan(plan, canonicalization.canonical_dataset, artifact_store, metadata_store)
    return _Fixture(request, sufficiency, plan, canonicalization.canonical_dataset, artifact_store, metadata_store, outcome)


def _validate(fixture: _Fixture, metric_ref: str, dependencies: tuple[ValidatedResult, ...] = ()):
    record = _record(fixture.outcome, metric_ref, "baseline")
    result = _result(fixture.outcome, metric_ref, "baseline")
    return validate_executed_result(
        execution_id=record.execution_id,
        result_id=result.result_id,
        plan=fixture.plan,
        canonical_dataset=fixture.canonical,
        artifact_store=fixture.artifact_store,
        metadata_store=fixture.metadata_store,
        dependency_validated_results=dependencies,
    )


def _admit(
    fixture: _Fixture,
    result: ValidatedResult,
    *,
    claim_type: ClaimType = ClaimType.DESCRIPTIVE,
    supplied_request=None,
    supplied_sufficiency=None,
    supplied_validated_result=Ellipsis,
    evidence_role=None,
):
    if supplied_validated_result is Ellipsis:
        supplied_validated_result = result
    return evaluate_evidence_admissibility(
        request_id=fixture.request.request_id,
        sufficiency_id=fixture.sufficiency.sufficiency_id,
        validated_result_id=result.validated_result_id,
        claim_type=claim_type,
        artifact_store=fixture.artifact_store,
        metadata_store=fixture.metadata_store,
        supplied_request=supplied_request,
        supplied_sufficiency=supplied_sufficiency,
        supplied_validated_result=supplied_validated_result,
        evidence_role=evidence_role,
    )


def _restored_evidence(fixture: _Fixture, outcome) -> AdmissibleEvidence:
    artifact = outcome.admissibility_record.admissible_evidence_artifact_ref
    return AdmissibleEvidence.model_validate_json(
        fixture.artifact_store.safe_path(artifact.path).read_text(encoding="utf-8")
    )


def _validated_artifact_path(fixture: _Fixture, result: ValidatedResult) -> Path:
    record = fixture.metadata_store.get_validation_record(result.validation_record_id)
    return fixture.artifact_store.safe_path(record.validated_result_artifact_ref.path)


def _tamper_validated_artifact(fixture: _Fixture, result: ValidatedResult, key: str, value) -> None:
    path = _validated_artifact_path(fixture, result)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload[key] = value
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _replace_validated_artifact_authority(fixture: _Fixture, result: ValidatedResult, updates: dict) -> None:
    updated = result.model_copy(update=updates)
    path = _validated_artifact_path(fixture, result)
    path.write_bytes(canonical_json_bytes(updated.model_dump(mode="json")))
    _refresh_validated_artifact_reference(fixture, result)


def _refresh_validated_artifact_reference(fixture: _Fixture, result: ValidatedResult) -> None:
    old_record = fixture.metadata_store.get_validation_record(result.validation_record_id)
    old_artifact = old_record.validated_result_artifact_ref
    path = fixture.artifact_store.safe_path(old_artifact.path)
    fingerprint = sha256_file(path)
    artifact = ArtifactReference(
        artifact_id=stable_content_id("art", fingerprint),
        path=old_artifact.path,
        fingerprint=fingerprint,
        media_type=old_artifact.media_type,
        size_bytes=path.stat().st_size,
    )
    fixture.metadata_store.insert_artifact_reference(artifact)
    for validation_id in result.required_validation_record_ids:
        record = fixture.metadata_store.get_validation_record(validation_id)
        if record is None:
            continue
        payload = record.model_dump(mode="json")
        payload["validated_result_artifact_ref"] = artifact.model_dump(mode="json")
        with sqlite3.connect(fixture.metadata_store.db_path) as conn:
            conn.execute(
                """
                UPDATE validation_records
                SET validated_result_artifact_id = ?, record_json = ?
                WHERE validation_id = ?
                """,
                (artifact.artifact_id, json.dumps(payload, sort_keys=True), validation_id),
            )


def _tamper_executed_artifact(fixture: _Fixture, result: ValidatedResult, key: str, value) -> None:
    execution_record = fixture.metadata_store.get_execution_record(result.execution_id)
    path = fixture.artifact_store.safe_path(execution_record.output_artifacts[0].path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload[key] = value
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _delete_row(metadata_store: MetadataStore, table: str, id_column: str, value: str) -> None:
    with sqlite3.connect(metadata_store.db_path) as conn:
        conn.execute(f"DELETE FROM {table} WHERE {id_column} = ?", (value,))


def _tamper_json(metadata_store: MetadataStore, table: str, id_column: str, value: str, key: str, new_value: str) -> None:
    with sqlite3.connect(metadata_store.db_path) as conn:
        row = conn.execute(f"SELECT record_json FROM {table} WHERE {id_column} = ?", (value,)).fetchone()
        payload = json.loads(row[0])
        payload[key] = new_value
        conn.execute(f"UPDATE {table} SET record_json = ? WHERE {id_column} = ?", (json.dumps(payload, sort_keys=True), value))


def _replace_request(fixture: _Fixture, **updates) -> None:
    request = fixture.request.model_copy(update=updates)
    payload = request.model_dump_json()
    with sqlite3.connect(fixture.metadata_store.db_path) as conn:
        conn.execute(
            "UPDATE analysis_requests SET record_json = ?, record_fingerprint = ? WHERE request_id = ?",
            (payload, _fingerprint(payload), request.request_id),
        )


def _replace_sufficiency(fixture: _Fixture, **updates) -> None:
    sufficiency = fixture.sufficiency.model_copy(update=updates)
    payload = sufficiency.model_dump_json()
    with sqlite3.connect(fixture.metadata_store.db_path) as conn:
        conn.execute(
            "UPDATE data_sufficiency_results SET record_json = ?, record_fingerprint = ? WHERE sufficiency_id = ?",
            (payload, _fingerprint(payload), sufficiency.sufficiency_id),
        )


def _fingerprint(payload: str) -> str:
    from commerce_lens.evidence.identifiers import canonical_json_fingerprint

    return canonical_json_fingerprint(json.loads(payload))


def _set_validation_record_status(fixture: _Fixture, validation_id: str, status: str) -> None:
    _tamper_validation_record(fixture, validation_id, {"status": status})


def _tamper_validation_record(fixture: _Fixture, validation_id: str, updates: dict) -> None:
    record = fixture.metadata_store.get_validation_record(validation_id)
    payload = record.model_dump(mode="json")
    payload.update(updates)
    with sqlite3.connect(fixture.metadata_store.db_path) as conn:
        conn.execute(
            "UPDATE validation_records SET status = ?, record_json = ? WHERE validation_id = ?",
            (payload["status"], json.dumps(payload, sort_keys=True), validation_id),
        )


def _set_execution_record_grouping(fixture: _Fixture, execution_id: str, grouping: str) -> None:
    record = fixture.metadata_store.get_execution_record(execution_id)
    payload = record.model_dump(mode="json")
    payload["grouping"] = grouping
    with sqlite3.connect(fixture.metadata_store.db_path) as conn:
        conn.execute("UPDATE execution_records SET record_json = ? WHERE execution_id = ?", (json.dumps(payload, sort_keys=True), execution_id))


def _set_execution_record_dataset_ids(fixture: _Fixture, execution_id: str, dataset_ids: tuple[str, ...]) -> None:
    record = fixture.metadata_store.get_execution_record(execution_id)
    payload = record.model_dump(mode="json")
    payload["dataset_ref_ids"] = list(dataset_ids)
    with sqlite3.connect(fixture.metadata_store.db_path) as conn:
        conn.execute("UPDATE execution_records SET record_json = ? WHERE execution_id = ?", (json.dumps(payload, sort_keys=True), execution_id))


def _set_execution_record_period_refs(fixture: _Fixture, execution_id: str, period_refs: tuple[str, ...]) -> None:
    record = fixture.metadata_store.get_execution_record(execution_id)
    payload = record.model_dump(mode="json")
    payload["period_refs"] = list(period_refs)
    with sqlite3.connect(fixture.metadata_store.db_path) as conn:
        conn.execute("UPDATE execution_records SET record_json = ? WHERE execution_id = ?", (json.dumps(payload, sort_keys=True), execution_id))


def _set_execution_record_population_refs(fixture: _Fixture, execution_id: str, population_refs: tuple[str, ...]) -> None:
    record = fixture.metadata_store.get_execution_record(execution_id)
    payload = record.model_dump(mode="json")
    payload["population_refs"] = list(population_refs)
    with sqlite3.connect(fixture.metadata_store.db_path) as conn:
        conn.execute("UPDATE execution_records SET record_json = ? WHERE execution_id = ?", (json.dumps(payload, sort_keys=True), execution_id))


def _assert_v5_tables(store: MetadataStore) -> None:
    with sqlite3.connect(store.db_path) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()}
    assert {"analysis_requests", "data_sufficiency_results", "evidence_admissibility_records"}.issubset(tables)


def _create_supported_v3_tables(conn: sqlite3.Connection) -> None:
    _create_supported_v2_tables(conn)
    conn.execute(
        """
        CREATE TABLE execution_records (
            execution_id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL,
            plan_id TEXT,
            plan_node_id TEXT,
            metric_ref TEXT,
            status TEXT NOT NULL,
            result_ref TEXT,
            result_artifact_id TEXT,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            record_json TEXT NOT NULL
        )
        """
    )


def _create_supported_v4_tables(conn: sqlite3.Connection) -> None:
    _create_supported_v3_tables(conn)
    conn.execute(
        """
        CREATE TABLE validation_records (
            validation_id TEXT PRIMARY KEY,
            execution_id TEXT NOT NULL,
            result_ref TEXT NOT NULL,
            metric_ref TEXT,
            status TEXT NOT NULL,
            failure_code TEXT,
            validated_result_ref TEXT,
            validated_result_artifact_id TEXT,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            record_json TEXT NOT NULL
        )
        """
    )
