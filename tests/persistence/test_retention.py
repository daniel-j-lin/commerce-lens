from datetime import date
import json
import sqlite3

import pytest

from commerce_lens.canonical.models import PeriodCoverageEvidence
from commerce_lens.contracts.common import AvailableEvidence, PeriodDefinition, SourceType
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore, SCHEMA_VERSION
from commerce_lens.persistence.retention import RetainedRunSession, RetentionStore
from commerce_lens.skill.integration import (
    PublicAnalysisIntent,
    PublicQuestionClass,
    PublicSourceSelection,
    run_public_analysis,
)
from commerce_lens.intake.registry import DatasetRegistry
from commerce_lens.skill import coverage_intake
from commerce_lens.skill.integration import prepare_public_coverage


def _intent(source):
    return PublicAnalysisIntent(
        question_class=PublicQuestionClass.REVENUE_CHANGE,
        metric_id="revenue_change",
        baseline_period=PeriodDefinition(
            period_id="baseline", label="Q3 2026", start_date=date(2026, 7, 1),
            end_date=date(2026, 9, 30), date_convention_ref="order_date_utc",
        ),
        comparison_period=PeriodDefinition(
            period_id="comparison", label="Q4 2026", start_date=date(2026, 10, 1),
            end_date=date(2026, 12, 31), date_convention_ref="order_date_utc",
        ),
        source=PublicSourceSelection(source, SourceType.CSV),
    )


def _declared_authority(source, artifact_store):
    dataset = DatasetRegistry(artifact_store).register_source(source, SourceType.CSV)
    return {
        "available_evidence": (
            AvailableEvidence(
                evidence_id="retention_test_authority",
                description="Test-authored complete synthetic export",
                source_ref=dataset.dataset_id,
                satisfies_requirement_ids=("req_global", "req_revenue", "req_orders", "req_aov", "req_revenue_change"),
            ),
        ),
        "period_coverage_evidence": (
            PeriodCoverageEvidence(
                coverage_ref_id="retention_test_coverage",
                dataset_ref_id=dataset.dataset_id,
                observed_start_date=date(2026, 7, 1),
                observed_end_date=date(2026, 12, 31),
                date_convention_ref="order_date_utc",
                governing_note_ref="test_author_declares_complete_synthetic_export",
            ),
        ),
    }


def test_retained_run_is_self_contained_and_verifiable_across_store_instances(tmp_path):
    source = tmp_path / "orders.csv"
    source.write_text(
        "order_id,order_line_id,order_date,product_id,quantity,line_revenue,currency,eligibility_status\n"
        "o1,l1,2026-07-15,p1,1,120.00,USD,paid\n"
        "o2,l2,2026-10-15,p1,1,100.00,USD,paid\n",
        encoding="utf-8",
    )
    retention_root = tmp_path / "retention"
    session = RetainedRunSession.begin(retention_root)
    outcome = run_public_analysis(
        _intent(source),
        artifact_store=session.artifact_store,
        metadata_store=session.metadata_store,
        run_id=session.run_id,
        retention_session=session,
        **_declared_authority(source, session.artifact_store),
    )

    manifest = session.finalize(outcome, public_payload={"rendered_text": outcome.response.render_text()})
    reopened = RetentionStore(retention_root)
    assert manifest.retention_status.value == "retained_complete"
    assert (session.run_root / "complete.marker").is_file()
    assert reopened.list_runs()[0]["retention_status"] == "retained_complete"
    checks, errors = reopened.verify_run(session.run_id)
    assert not errors, (checks, errors)
    inspected = reopened.inspect_run(session.run_id)
    assert inspected["run_id"] == session.run_id
    assert inspected["analysis_result_artifact"]
    assert inspected["public_response_artifact"]

    result_path = session.artifact_store.safe_path(manifest.analysis_result_artifact.path)
    result_path.write_text("tampered", encoding="utf-8")
    _, corruption_errors = reopened.verify_run(session.run_id)
    assert any("hash mismatch" in error for error in corruption_errors)

    reopened.delete_run(session.run_id)
    assert not session.run_root.exists()


def test_retained_run_corruption_fails_verification_and_delete_is_path_safe(tmp_path):
    session = RetainedRunSession.begin(tmp_path / "retention")
    (session.run_root / "artifacts" / "sentinel.txt").write_text("x", encoding="utf-8")
    store = RetentionStore(tmp_path / "retention")
    assert store.list_runs()[0]["retention_status"] == "retained_incomplete"
    with pytest.raises(ValueError):
        store.inspect_run("../outside")
    with pytest.raises(ValueError):
        store.delete_run("../outside")
    session.fail("test interruption")
    assert store.list_runs()[0]["retention_status"] == "retention_failed"


def test_v6_component_store_migrates_additively_to_current_metadata_schema(tmp_path):
    db_path = tmp_path / "legacy.sqlite"
    store = MetadataStore(db_path)
    store.initialize()
    with sqlite3.connect(db_path) as conn:
        conn.execute("DROP TABLE retained_runs")
        conn.execute("UPDATE schema_version SET version = 6 WHERE id = 1")
    reopened = MetadataStore(db_path)
    reopened.initialize()
    assert reopened.schema_version() == SCHEMA_VERSION == 9
    assert reopened.list_retained_runs() == []


def test_legacy_component_root_is_listed_as_incomplete(tmp_path):
    legacy_root = tmp_path / "legacy"
    ArtifactStore(legacy_root / "artifacts").ensure_layout()
    MetadataStore(legacy_root / "metadata.sqlite").initialize()
    summaries = RetentionStore(legacy_root).list_runs()
    assert summaries == [
        {
            "run_id": "legacy",
            "retention_status": "legacy_incomplete",
            "reason": "legacy component store; no self-contained retained-run manifest",
        }
    ]


def test_internal_and_external_symlink_entries_are_never_deleted(tmp_path):
    retention_root = tmp_path / "retention"
    retention_root.mkdir()
    first = retention_root / "run-first"
    second = retention_root / "run-second"
    first.mkdir()
    second.mkdir()
    (second / "sentinel").write_text("keep", encoding="utf-8")
    external = tmp_path / "external"
    external.mkdir()
    (external / "sentinel").write_text("keep", encoding="utf-8")
    (retention_root / "link-to-run").symlink_to(second, target_is_directory=True)
    (retention_root / "link-outside").symlink_to(external, target_is_directory=True)
    store = RetentionStore(retention_root)

    with pytest.raises(ValueError):
        store.delete_run("link-to-run")
    with pytest.raises(ValueError):
        store.delete_run("link-outside")
    with pytest.raises(ValueError):
        store.inspect_run("link-to-run")
    assert (second / "sentinel").read_text(encoding="utf-8") == "keep"
    assert (external / "sentinel").read_text(encoding="utf-8") == "keep"
    assert store.list_runs() == [
        {"run_id": "link-outside", "retention_status": "retention_failed", "error": "retained run entry must not be a symlink"},
        {"run_id": "link-to-run", "retention_status": "retention_failed", "error": "retained run entry must not be a symlink"},
        {"run_id": "run-first", "retention_status": "legacy_incomplete"},
        {"run_id": "run-second", "retention_status": "legacy_incomplete"},
    ]


def test_original_source_survives_retained_run_deletion(tmp_path):
    source = tmp_path / "orders.csv"
    source_bytes = (
        b"order_id,order_line_id,order_date,product_id,quantity,line_revenue,currency,eligibility_status\n"
        b"o1,l1,2026-07-15,p1,1,120.00,USD,paid\n"
        b"o2,l2,2026-10-15,p1,1,100.00,USD,paid\n"
    )
    source.write_bytes(source_bytes)
    session = RetainedRunSession.begin(tmp_path / "retention")
    outcome = run_public_analysis(
        _intent(source),
        artifact_store=session.artifact_store,
        metadata_store=session.metadata_store,
        run_id=session.run_id,
        retention_session=session,
        **_declared_authority(source, session.artifact_store),
    )
    session.finalize(outcome, public_payload={"rendered_text": outcome.response.render_text()})
    RetentionStore(tmp_path / "retention").delete_run(session.run_id)
    assert source.exists()
    assert source.read_bytes() == source_bytes


def _retained_user_declared_case(tmp_path, monkeypatch):
    from datetime import UTC, datetime

    now = datetime(2027, 1, 3, tzinfo=UTC)
    cutoff = datetime(2027, 1, 1, tzinfo=UTC)
    monkeypatch.setattr(coverage_intake, "utc_now", lambda: now)
    source = tmp_path / "orders.csv"
    source.write_text(
        "order_id,order_line_id,order_date,product_id,quantity,line_revenue,currency,eligibility_status\n"
        "o1,l1,2026-07-15,p1,1,120.00,USD,paid\n"
        "o2,l2,2026-10-15,p1,1,100.00,USD,paid\n",
        encoding="utf-8",
    )
    session = RetainedRunSession.begin(tmp_path / "retention")
    intent = _intent(source)
    template = prepare_public_coverage(intent, artifact_store=session.artifact_store)["declaration_template"]
    declaration = coverage_intake.confirm_declaration(
        template,
        response="Confirm",
        proposal_fingerprint=coverage_intake.coverage_proposal_fingerprint(
            template, requested_periods=(intent.baseline_period, intent.comparison_period),
            data_availability_cutoff=cutoff,
        ),
        requested_periods=(intent.baseline_period, intent.comparison_period),
        recorded_at=now,
        declaration_id="retained-declaration",
        data_availability_cutoff=cutoff,
        source_basis_detail=coverage_intake.SOURCE_BASIS_ASSERTION,
    ).model_dump(mode="json")
    outcome = run_public_analysis(
        intent,
        artifact_store=session.artifact_store,
        metadata_store=session.metadata_store,
        coverage_declarations=declaration,
        run_id=session.run_id,
        retention_session=session,
    )
    manifest = session.finalize(outcome, public_payload={"response": outcome.response.__dict__})
    return session, manifest, RetentionStore(tmp_path / "retention")


def test_user_declared_bundle_reloads_and_detects_required_field_corruption(tmp_path, monkeypatch):
    session, manifest, store = _retained_user_declared_case(tmp_path, monkeypatch)
    checks, errors = store.verify_run(session.run_id)
    assert not errors, (checks, errors)
    declaration_path = session.artifact_store.safe_path(manifest.declaration_artifact.path)
    original = json.loads(declaration_path.read_text(encoding="utf-8"))
    for field, value in (
        ("declaration_id", "mutated"),
        ("policy_version", "wrong_policy"),
        ("dataset_id", "wrong_dataset"),
        ("content_fingerprint", "0" * 64),
        ("selected_sheet", "wrong_sheet"),
        ("selected_table", "wrong_table"),
        ("context_fingerprint", "0" * 64),
        ("covered_end", "2026-12-30"),
        ("data_availability_cutoff", "2026-12-31T00:00:00Z"),
        ("authority_type", "SOURCE_DECLARED"),
    ):
        declaration_path.write_text(json.dumps({**original, field: value}), encoding="utf-8")
        _, corruption_errors = store.verify_run(session.run_id)
        assert corruption_errors, field
    response_path = session.artifact_store.safe_path(manifest.public_response_artifact.path)
    response = json.loads(response_path.read_text(encoding="utf-8"))
    response["response"]["limitations"] = []
    response_path.write_text(json.dumps(response), encoding="utf-8")
    _, disclosure_errors = store.verify_run(session.run_id)
    assert disclosure_errors


def test_finalization_failure_never_reports_complete(tmp_path, monkeypatch):
    source = tmp_path / "orders.csv"
    source.write_text(
        "order_id,order_line_id,order_date,product_id,quantity,line_revenue,currency,eligibility_status\n"
        "o1,l1,2026-07-15,p1,1,120.00,USD,paid\n"
        "o2,l2,2026-10-15,p1,1,100.00,USD,paid\n",
        encoding="utf-8",
    )
    session = RetainedRunSession.begin(tmp_path / "retention")
    outcome = run_public_analysis(
        _intent(source),
        artifact_store=session.artifact_store,
        metadata_store=session.metadata_store,
        run_id=session.run_id,
        retention_session=session,
        **_declared_authority(source, session.artifact_store),
    )
    monkeypatch.setattr(session, "_write_complete_marker", lambda manifest: (_ for _ in ()).throw(OSError("injected marker failure")))
    with pytest.raises(Exception):
        session.finalize(outcome, public_payload={"rendered_text": outcome.response.render_text()})
    summary = RetentionStore(tmp_path / "retention").list_runs()[0]
    assert summary["retention_status"] != "retained_complete"
    assert not (session.run_root / "complete.marker").exists()


def test_complete_manifest_without_marker_is_visible_as_incomplete_and_fails_verify(tmp_path):
    source = tmp_path / "orders.csv"
    source.write_text(
        "order_id,order_line_id,order_date,product_id,quantity,line_revenue,currency,eligibility_status\n"
        "o1,l1,2026-07-15,p1,1,120.00,USD,paid\n"
        "o2,l2,2026-10-15,p1,1,100.00,USD,paid\n",
        encoding="utf-8",
    )
    session = RetainedRunSession.begin(tmp_path / "retention")
    outcome = run_public_analysis(
        _intent(source), artifact_store=session.artifact_store, metadata_store=session.metadata_store,
        run_id=session.run_id, retention_session=session,
        **_declared_authority(source, session.artifact_store),
    )
    session.finalize(outcome, public_payload={"rendered_text": outcome.response.render_text()})
    (session.run_root / "complete.marker").unlink()
    summary = RetentionStore(tmp_path / "retention").list_runs()[0]
    assert summary["retention_status"] == "retained_incomplete"
    assert RetentionStore(tmp_path / "retention").inspect_run(session.run_id)["retention_status"] == "retained_incomplete"
    _, errors = RetentionStore(tmp_path / "retention").verify_run(session.run_id)
    assert any("complete marker" in error for error in errors)


def test_canonical_artifact_missing_is_a_deterministic_verification_failure(tmp_path):
    source = tmp_path / "orders.csv"
    source.write_text(
        "order_id,order_line_id,order_date,product_id,quantity,line_revenue,currency,eligibility_status\n"
        "o1,l1,2026-07-15,p1,1,120.00,USD,paid\n"
        "o2,l2,2026-10-15,p1,1,100.00,USD,paid\n",
        encoding="utf-8",
    )
    session = RetainedRunSession.begin(tmp_path / "retention")
    outcome = run_public_analysis(
        _intent(source), artifact_store=session.artifact_store, metadata_store=session.metadata_store,
        run_id=session.run_id, retention_session=session,
        **_declared_authority(source, session.artifact_store),
    )
    manifest = session.finalize(outcome, public_payload={"rendered_text": outcome.response.render_text()})
    canonical_path = session.artifact_store.safe_path(manifest.canonical["artifact"]["path"])
    canonical_path.unlink()
    _, errors = RetentionStore(tmp_path / "retention").verify_run(session.run_id)
    assert any("artifact missing or hash mismatch" in error for error in errors)


def test_manifest_initialization_failure_leaves_no_complete_run(tmp_path, monkeypatch):
    monkeypatch.setattr(MetadataStore, "initialize", lambda self: (_ for _ in ()).throw(OSError("metadata init")))
    with pytest.raises(OSError):
        RetainedRunSession.begin(tmp_path / "retention")
    children = list((tmp_path / "retention").iterdir())
    assert children and all(not (child / "complete.marker").exists() for child in children)


@pytest.mark.parametrize("failure_point", ["source", "canonical", "declaration"])
def test_early_artifact_failures_leave_no_complete_run(tmp_path, monkeypatch, failure_point):
    source = tmp_path / "orders.csv"
    source.write_text(
        "order_id,order_line_id,order_date,product_id,quantity,line_revenue,currency,eligibility_status\n"
        "o1,l1,2026-07-15,p1,1,120.00,USD,paid\n"
        "o2,l2,2026-10-15,p1,1,100.00,USD,paid\n",
        encoding="utf-8",
    )
    session = RetainedRunSession.begin(tmp_path / "retention")
    if failure_point == "source":
        monkeypatch.setattr(ArtifactStore, "snapshot_source", lambda self, path: (_ for _ in ()).throw(OSError("source write")))
        with pytest.raises(OSError):
            run_public_analysis(
                _intent(source), artifact_store=session.artifact_store, metadata_store=session.metadata_store,
                run_id=session.run_id, retention_session=session,
                **_declared_authority(source, session.artifact_store),
            )
    elif failure_point == "canonical":
        monkeypatch.setattr("commerce_lens.canonical.service._write_parquet", lambda rows, path: (_ for _ in ()).throw(OSError("canonical write")))
        with pytest.raises(OSError):
            run_public_analysis(
                _intent(source), artifact_store=session.artifact_store, metadata_store=session.metadata_store,
                run_id=session.run_id, retention_session=session,
                **_declared_authority(source, session.artifact_store),
            )
    else:
        from datetime import UTC, datetime

        now = datetime(2027, 1, 3, tzinfo=UTC)
        monkeypatch.setattr(coverage_intake, "utc_now", lambda: now)
        intent = _intent(source)
        template = prepare_public_coverage(intent, artifact_store=session.artifact_store)["declaration_template"]
        declaration = coverage_intake.confirm_declaration(
            template, response="Confirm", recorded_at=now, declaration_id="decl-failure",
            proposal_fingerprint=coverage_intake.coverage_proposal_fingerprint(
                template, requested_periods=(intent.baseline_period, intent.comparison_period),
                data_availability_cutoff=datetime(2027, 1, 1, tzinfo=UTC),
            ),
            requested_periods=(intent.baseline_period, intent.comparison_period),
            data_availability_cutoff=datetime(2027, 1, 1, tzinfo=UTC),
            source_basis_detail=coverage_intake.SOURCE_BASIS_ASSERTION,
        ).model_dump(mode="json")
        original_write = session.artifact_store.write_json_artifact
        def fail_declaration(path, payload, **kwargs):
            if "coverage_declarations" in str(path):
                raise OSError("declaration write")
            return original_write(path, payload, **kwargs)
        monkeypatch.setattr(session.artifact_store, "write_json_artifact", fail_declaration)
        with pytest.raises(OSError):
            run_public_analysis(
                intent, artifact_store=session.artifact_store, metadata_store=session.metadata_store,
                coverage_declarations=declaration, run_id=session.run_id, retention_session=session,
            )
        session.fail("declaration persistence failure")
    assert RetentionStore(tmp_path / "retention").list_runs()[0]["retention_status"] != "retained_complete"


@pytest.mark.parametrize("failure_point", ["metadata", "analysis_result", "public_response", "final_verification"])
def test_late_persistence_failures_leave_no_complete_run(tmp_path, monkeypatch, failure_point):
    source = tmp_path / "orders.csv"
    source.write_text(
        "order_id,order_line_id,order_date,product_id,quantity,line_revenue,currency,eligibility_status\n"
        "o1,l1,2026-07-15,p1,1,120.00,USD,paid\n"
        "o2,l2,2026-10-15,p1,1,100.00,USD,paid\n",
        encoding="utf-8",
    )
    session = RetainedRunSession.begin(tmp_path / "retention")
    outcome = run_public_analysis(
        _intent(source), artifact_store=session.artifact_store, metadata_store=session.metadata_store,
        run_id=session.run_id, retention_session=session,
        **_declared_authority(source, session.artifact_store),
    )
    if failure_point == "metadata":
        monkeypatch.setattr(session.metadata_store, "update_retained_run", lambda record: (_ for _ in ()).throw(OSError("metadata write")))
    elif failure_point in {"analysis_result", "public_response"}:
        original_write = session.artifact_store.write_json_artifact
        def fail_final(path, payload, **kwargs):
            if str(path).endswith(f"{failure_point}.json"):
                raise OSError(f"{failure_point} write")
            return original_write(path, payload, **kwargs)
        monkeypatch.setattr(session.artifact_store, "write_json_artifact", fail_final)
    else:
        monkeypatch.setattr(RetentionStore, "verify_run", lambda self, run_id: ({"injected": False}, ["injected final verification failure"]))
    with pytest.raises(Exception):
        session.finalize(outcome, public_payload={"rendered_text": outcome.response.render_text()})
    assert RetentionStore(tmp_path / "retention").list_runs()[0]["retention_status"] != "retained_complete"
