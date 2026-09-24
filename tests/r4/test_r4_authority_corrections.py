from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import commerce_lens.application.r4_service as r4_service
from commerce_lens.application.r4_service import R4EligibilityError
from commerce_lens.contracts.common import ArtifactReference
from commerce_lens.evidence.identifiers import sha256_file, stable_content_id
from commerce_lens.metrics.registry import PRECISION_POLICY_REF, PRECISION_POLICY_VERSION
from tests.engine.test_execution import _row
from tests.r4.support import make_r4_fixture, run_r4


@pytest.mark.parametrize(
    "field",
    (
        "baseline_revenue_evidence_ref",
        "comparison_revenue_evidence_ref",
        "revenue_change_evidence_ref",
    ),
)
def test_missing_required_evidence_authority_fails_closed(tmp_path, field) -> None:
    fixture = make_r4_fixture(tmp_path, [_row(), _row(order_id="c", order_date="2026-01-03")])
    request = fixture.request.model_copy(update={field: "ev_missing_exact_authority"})

    with pytest.raises(R4EligibilityError) as exc:
        run_r4(fixture, request=request)

    assert exc.value.code == "admissible_evidence_authority_missing"


def test_evidence_bound_to_wrong_validated_result_run_and_population_is_rejected(tmp_path) -> None:
    fixture = make_r4_fixture(tmp_path, [_row(), _row(order_id="c", order_date="2026-01-03")])
    request = fixture.request.model_copy(
        update={
            "baseline_revenue_evidence_ref": fixture.comparison_evidence.evidence_id,
            "baseline_revenue_evidence_fingerprint": fixture.comparison_evidence.evidence_fingerprint,
        }
    )

    with pytest.raises(R4EligibilityError) as exc:
        run_r4(fixture, request=request)

    assert exc.value.code == "evidence_authority_lineage_mismatch"


@pytest.mark.parametrize(
    ("field", "wrong_value"),
    (
        ("request_id", "req_wrong"),
        ("execution_id", "exec_wrong"),
        ("population_ref", "pop_wrong"),
        ("period_ref", "period_wrong"),
        ("canonical_dataset_ref_id", "canon_wrong"),
    ),
)
def test_cross_request_run_population_period_or_canonical_evidence_is_rejected(
    tmp_path,
    monkeypatch,
    field,
    wrong_value,
) -> None:
    fixture = make_r4_fixture(tmp_path, [_row(), _row(order_id="c", order_date="2026-01-03")])
    original_retrieve = r4_service.retrieve_admissible_evidence_authority

    def hostile_retrieve(evidence_id, **kwargs):
        evidence = original_retrieve(evidence_id, **kwargs)
        if evidence_id == fixture.baseline_evidence.evidence_id:
            return evidence.model_copy(update={field: wrong_value})
        return evidence

    monkeypatch.setattr(r4_service, "retrieve_admissible_evidence_authority", hostile_retrieve)

    with pytest.raises(R4EligibilityError) as exc:
        run_r4(fixture)

    assert exc.value.code == "evidence_authority_lineage_mismatch"


def test_equivalent_numeric_result_cannot_borrow_another_results_evidence(tmp_path) -> None:
    fixture = make_r4_fixture(
        tmp_path,
        [
            _row(order_id="b", order_date="2026-01-01", line_revenue="10"),
            _row(order_id="c", order_date="2026-01-03", line_revenue="10"),
        ],
    )
    assert fixture.baseline.value == fixture.comparison.value
    request = fixture.request.model_copy(
        update={
            "baseline_revenue_evidence_ref": fixture.comparison_evidence.evidence_id,
            "baseline_revenue_evidence_fingerprint": fixture.comparison_evidence.evidence_fingerprint,
        }
    )

    with pytest.raises(R4EligibilityError) as exc:
        run_r4(fixture, request=request)

    assert exc.value.code == "evidence_authority_lineage_mismatch"


def test_tampered_evidence_artifact_fails_before_execution(tmp_path) -> None:
    fixture = make_r4_fixture(tmp_path, [_row(), _row(order_id="c", order_date="2026-01-03")])
    record = next(
        item
        for item in fixture.scalar.metadata_store.list_evidence_admissibility_records()
        if item.admissible_evidence_id == fixture.baseline_evidence.evidence_id
    )
    path = fixture.scalar.artifact_store.safe_path(record.admissible_evidence_artifact_ref.path)
    path.write_bytes(path.read_bytes() + b"\n")

    with pytest.raises(R4EligibilityError) as exc:
        run_r4(fixture)

    assert exc.value.code == "admissible_evidence_artifact_integrity_failure"


def test_unregistered_copied_evidence_artifact_fails_closed(tmp_path) -> None:
    fixture = make_r4_fixture(tmp_path, [_row(), _row(order_id="c", order_date="2026-01-03")])
    store = fixture.scalar.metadata_store
    record = next(
        item
        for item in store.list_evidence_admissibility_records()
        if item.admissible_evidence_id == fixture.baseline_evidence.evidence_id
    )
    original = record.admissible_evidence_artifact_ref
    source = fixture.scalar.artifact_store.safe_path(original.path)
    copied_path = fixture.scalar.artifact_store.safe_path("temporary", "unregistered_evidence_copy.json")
    copied_path.parent.mkdir(parents=True, exist_ok=True)
    copied_path.write_bytes(source.read_bytes())
    copied = ArtifactReference(
        artifact_id=stable_content_id("art", sha256_file(copied_path)),
        path=str(copied_path.relative_to(fixture.scalar.artifact_store.root)),
        fingerprint=sha256_file(copied_path),
        media_type="application/json",
        size_bytes=copied_path.stat().st_size,
    )
    hostile_record = record.model_copy(update={"admissible_evidence_artifact_ref": copied})
    with sqlite3.connect(store.db_path) as conn:
        conn.execute(
            "UPDATE evidence_admissibility_records SET admissible_evidence_artifact_id = ?, record_json = ? WHERE admissibility_id = ?",
            (copied.artifact_id, hostile_record.model_dump_json(), record.admissibility_id),
        )

    with pytest.raises(R4EligibilityError) as exc:
        run_r4(fixture)

    assert exc.value.code == "admissible_evidence_artifact_integrity_failure"


def test_caller_created_pseudo_evidence_record_is_not_authority(tmp_path) -> None:
    fixture = make_r4_fixture(tmp_path, [_row(), _row(order_id="c", order_date="2026-01-03")])
    store = fixture.scalar.metadata_store
    record = next(
        item
        for item in store.list_evidence_admissibility_records()
        if item.admissible_evidence_id == fixture.baseline_evidence.evidence_id
    )
    pseudo = record.model_copy(update={"evaluator_id": "caller_created_pseudo_evaluator"})
    with sqlite3.connect(store.db_path) as conn:
        conn.execute(
            "UPDATE evidence_admissibility_records SET record_json = ? WHERE admissibility_id = ?",
            (pseudo.model_dump_json(), record.admissibility_id),
        )

    with pytest.raises(R4EligibilityError) as exc:
        run_r4(fixture)

    assert exc.value.code == "admissible_evidence_authority_invalid"


def test_precision_policy_requires_exact_existing_versioned_authority(tmp_path) -> None:
    fixture = make_r4_fixture(tmp_path, [_row(), _row(order_id="c", order_date="2026-01-03")])
    assert fixture.request.precision_policy_ref == PRECISION_POLICY_REF
    assert fixture.request.precision_policy_version == PRECISION_POLICY_VERSION
    assert run_r4(fixture).validated_result.authority.precision_policy_version == PRECISION_POLICY_VERSION

    for unsupported in ("v0.9", ""):
        request = fixture.request.model_copy(update={"precision_policy_version": unsupported})
        with pytest.raises(R4EligibilityError) as exc:
            run_r4(fixture, request=request)
        assert exc.value.code == "r4_method_authority_mismatch"


def test_standalone_authority_contains_no_diagnostic_admission(tmp_path) -> None:
    fixture = make_r4_fixture(tmp_path, [_row(), _row(order_id="c", order_date="2026-01-03")])
    authority = run_r4(fixture).validated_result.authority.model_dump(mode="json")
    assert not any("diagnostic" in key or "r3" in key for key in authority)
