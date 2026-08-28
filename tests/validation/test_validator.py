from __future__ import annotations

import sqlite3
from decimal import Decimal, ROUND_DOWN, ROUND_UP, getcontext, localcontext
from pathlib import Path

import pytest

from commerce_lens.contracts.common import MetricState
from commerce_lens.contracts.validation import ValidatedResult, ValidationStatus
from commerce_lens.engine import execute_plan
from commerce_lens.engine.execution import _result_fingerprint
from commerce_lens.evidence.identifiers import generate_id
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import SCHEMA_VERSION, MetadataStore
from commerce_lens.validation import validate_executed_result
from tests.engine.test_execution import _execution_inputs, _record, _result, _row
from tests.persistence.test_metadata_store import _create_supported_v2_tables


def test_correct_revenue_passes_and_persists_validation(tmp_path) -> None:
    outcome, plan, canonical, store, metadata_store = _executed(
        tmp_path,
        ("revenue",),
        [_row(line_revenue="10.00"), _row(order_id="o2", order_line_id="l1", line_revenue="5.25")],
    )
    record = _record(outcome, "revenue", "baseline")
    result = _result(outcome, "revenue", "baseline")

    validation = validate_executed_result(
        execution_id=record.execution_id,
        result_id=result.result_id,
        plan=plan,
        canonical_dataset=canonical,
        artifact_store=store,
        metadata_store=metadata_store,
    )

    assert validation.validation_record.status is ValidationStatus.PASSED
    assert validation.validation_record.expected_value == Decimal("15.25")
    assert validation.validated_result is not None
    assert validation.validated_result.value == Decimal("15.25")
    assert validation.validated_result.metric_state is MetricState.VALID
    stored_record = metadata_store.get_validation_record(validation.validation_record.validation_id)
    assert stored_record.validation_id == validation.validation_record.validation_id
    assert stored_record.status is ValidationStatus.PASSED
    assert stored_record.validated_result_ref == validation.validated_result.validated_result_id
    artifact = metadata_store.get_artifact_reference(validation.validation_record.validated_result_artifact_ref.artifact_id)
    restored = ValidatedResult.model_validate_json(store.safe_path(artifact.path).read_text(encoding="utf-8"))
    assert restored == validation.validated_result
    assert isinstance(restored.value, Decimal)


def test_tampered_revenue_value_fails_without_validated_result(tmp_path) -> None:
    outcome, plan, canonical, store, metadata_store = _executed(tmp_path, ("revenue",), [_row()])
    tampered_record, tampered_result = _persist_replacement_result(
        outcome,
        plan,
        canonical,
        store,
        metadata_store,
        "revenue",
        "baseline",
        value=Decimal("11.00"),
        recompute_fingerprint=True,
    )

    validation = validate_executed_result(
        execution_id=tampered_record.execution_id,
        result_id=tampered_result.result_id,
        plan=plan,
        canonical_dataset=canonical,
        artifact_store=store,
        metadata_store=metadata_store,
    )

    assert validation.validation_record.status is ValidationStatus.FAILED
    assert validation.validation_record.failure_code == "value_mismatch"
    assert validation.validated_result is None
    stored_record = metadata_store.get_validation_record(validation.validation_record.validation_id)
    assert stored_record.validation_id == validation.validation_record.validation_id
    assert stored_record.status is ValidationStatus.FAILED
    assert stored_record.failure_code == "value_mismatch"


def test_revenue_type_currency_population_dataset_linkage_and_artifact_tamper_fail_closed(tmp_path) -> None:
    outcome, plan, canonical, store, metadata_store = _executed(tmp_path, ("revenue",), [_row()])

    cases = [
        ("float_value", {"value": 10.0}, "invalid_revenue_type"),
        ("wrong_currency", {"currency": "EUR"}, "currency_mismatch"),
        ("stale_population", {"scope_ref": "pop_stale"}, "population_missing"),
        ("wrong_canonical", {}, "canonical_fingerprint_mismatch"),
        ("linkage", {"execution_id": "exec_wrong"}, "execution_result_linkage_mismatch"),
        ("fingerprint", {"result_fingerprint": "0" * 64}, "result_fingerprint_mismatch"),
    ]
    for label, result_updates, expected_code in cases:
        active_canonical = canonical
        if label == "wrong_canonical":
            active_canonical = canonical.model_copy(update={"content_fingerprint": "1" * 64})
        tampered_record, tampered_result = _persist_replacement_result(
            outcome,
            plan,
            canonical,
            store,
            metadata_store,
            "revenue",
            "baseline",
            result_updates=result_updates,
            recompute_fingerprint=label in {"float_value", "wrong_currency"},
            suffix=label,
        )
        validation = validate_executed_result(
            execution_id=tampered_record.execution_id,
            result_id=tampered_result.result_id,
            plan=plan,
            canonical_dataset=active_canonical,
            artifact_store=store,
            metadata_store=metadata_store,
        )
        assert validation.validation_record.status is ValidationStatus.FAILED
        assert validation.validation_record.failure_code == expected_code
        assert validation.validated_result is None

    record = _record(outcome, "revenue", "baseline")
    artifact_path = store.safe_path(record.output_artifacts[0].path)
    artifact_path.write_text(artifact_path.read_text(encoding="utf-8").replace("10.00", "12.00"), encoding="utf-8")
    artifact_validation = validate_executed_result(
        execution_id=record.execution_id,
        result_id=record.result_ref,
        plan=plan,
        canonical_dataset=canonical,
        artifact_store=store,
        metadata_store=metadata_store,
    )
    assert artifact_validation.validation_record.failure_code == "result_artifact_hash_mismatch"


def test_empty_complete_revenue_zero_and_persisted_result_validate(tmp_path) -> None:
    outcome, plan, canonical, store, metadata_store = _executed(
        tmp_path,
        ("revenue",),
        [_row(order_id="o1", order_date="2026-01-03", line_revenue="7.00", currency="USD")],
    )
    record = _record(outcome, "revenue", "baseline")
    result = _result(outcome, "revenue", "baseline")

    validation = validate_executed_result(
        execution_id=record.execution_id,
        result_id=result.result_id,
        plan=plan,
        canonical_dataset=canonical,
        artifact_store=store,
        metadata_store=metadata_store,
    )

    assert validation.validation_record.status is ValidationStatus.PASSED
    assert validation.validated_result.value == Decimal("0")


def test_correct_orders_multiline_and_zero_pass(tmp_path) -> None:
    outcome, plan, canonical, store, metadata_store = _executed(
        tmp_path,
        ("orders",),
        [
            _row(order_id="o1", order_line_id="l1"),
            _row(order_id="o1", order_line_id="l2", line_revenue="3.00"),
            _row(order_id="o2", order_line_id="l1", order_date="2026-01-03"),
        ],
    )

    baseline = _validate_metric(outcome, plan, canonical, store, metadata_store, "orders", "baseline")
    comparison = _validate_metric(outcome, plan, canonical, store, metadata_store, "orders", "comparison")

    assert baseline.validated_result.value == 1
    assert comparison.validated_result.value == 1

    empty_outcome, empty_plan, empty_canonical, empty_store, empty_metadata = _executed(
        tmp_path,
        ("orders",),
        [_row(order_id="o9", order_date="2026-01-05")],
        filename="orders_empty.csv",
    )
    empty = _validate_metric(empty_outcome, empty_plan, empty_canonical, empty_store, empty_metadata, "orders", "baseline")
    assert empty.validation_record.status is ValidationStatus.PASSED
    assert empty.validated_result.value == 0


def test_orders_type_value_population_and_dataset_mismatches_fail(tmp_path) -> None:
    outcome, plan, canonical, store, metadata_store = _executed(tmp_path, ("orders",), [_row()])

    cases = [
        ("float", {"value": 1.0}, "invalid_orders_type"),
        ("negative", {"value": -1}, "negative_orders"),
        ("bool", {"value": True}, "invalid_orders_type"),
        ("population", {"scope_ref": "pop_missing"}, "population_missing"),
    ]
    for label, updates, expected_code in cases:
        tampered_record, tampered_result = _persist_replacement_result(
            outcome,
            plan,
            canonical,
            store,
            metadata_store,
            "orders",
            "baseline",
            result_updates=updates,
            recompute_fingerprint=label in {"float", "negative", "bool"},
            suffix=label,
        )
        validation = validate_executed_result(
            execution_id=tampered_record.execution_id,
            result_id=tampered_result.result_id,
            plan=plan,
            canonical_dataset=canonical,
            artifact_store=store,
            metadata_store=metadata_store,
        )
        assert validation.validation_record.failure_code == expected_code
        assert validation.validated_result is None

    wrong_dataset = canonical.model_copy(update={"content_fingerprint": "2" * 64})
    validation = _validate_metric(outcome, plan, wrong_dataset, store, metadata_store, "orders", "baseline")
    assert validation.validation_record.status is ValidationStatus.FAILED
    assert validation.validation_record.failure_code == "canonical_fingerprint_mismatch"


def test_correct_aov_uses_validated_dependencies_and_is_ambient_decimal_safe(tmp_path) -> None:
    outcome, plan, canonical, store, metadata_store = _executed(
        tmp_path,
        ("aov",),
        [
            _row(order_id="o1", order_line_id="l1", line_revenue="1.00"),
            _row(order_id="o2", order_line_id="l1", line_revenue="0"),
            _row(order_id="o3", order_line_id="l1", line_revenue="0"),
        ],
    )
    revenue = _validate_metric(outcome, plan, canonical, store, metadata_store, "revenue", "baseline").validated_result
    orders = _validate_metric(outcome, plan, canonical, store, metadata_store, "orders", "baseline").validated_result

    with localcontext() as context:
        context.prec = 6
        context.rounding = ROUND_UP
        validation_up = _validate_metric(
            outcome,
            plan,
            canonical,
            store,
            metadata_store,
            "aov",
            "baseline",
            dependencies=(revenue, orders),
        )
    with localcontext() as context:
        context.prec = 4
        context.rounding = ROUND_DOWN
        validation_down = _validate_metric(
            outcome,
            plan,
            canonical,
            store,
            metadata_store,
            "aov",
            "baseline",
            dependencies=(revenue, orders),
        )

    expected = Decimal("0.33333333333333333333333333333333333333")
    assert validation_up.validated_result.value == expected
    assert validation_down.validated_result.value == expected
    assert getcontext().prec != 38


def test_aov_tampering_policy_currency_and_dependency_failures(tmp_path) -> None:
    outcome, plan, canonical, store, metadata_store = _executed(tmp_path, ("aov",), [_row(line_revenue="10.00")])
    revenue = _validate_metric(outcome, plan, canonical, store, metadata_store, "revenue", "baseline").validated_result
    orders = _validate_metric(outcome, plan, canonical, store, metadata_store, "orders", "baseline").validated_result

    for label, updates, expected_code in [
        ("value", {"value": Decimal("9.99")}, "value_mismatch"),
        ("policy", {"precision_metadata": {"calculation_policy_id": "wrong", "precision": 38, "rounding": "ROUND_HALF_EVEN"}}, "precision_policy_mismatch"),
        ("currency", {"currency": "EUR"}, "currency_mismatch"),
        ("undefined", {"value": None, "metric_state": MetricState.UNDEFINED, "undefined_reason": "orders_equals_zero"}, "invalid_metric_state"),
    ]:
        tampered_record, tampered_result = _persist_replacement_result(
            outcome,
            plan,
            canonical,
            store,
            metadata_store,
            "aov",
            "baseline",
            result_updates=updates,
            recompute_fingerprint=True,
            suffix=label,
        )
        validation = validate_executed_result(
            execution_id=tampered_record.execution_id,
            result_id=tampered_result.result_id,
            plan=plan,
            canonical_dataset=canonical,
            artifact_store=store,
            metadata_store=metadata_store,
            dependency_validated_results=(revenue, orders),
        )
        assert validation.validation_record.failure_code == expected_code
        assert validation.validated_result is None

    unvalidated = _validate_metric(outcome, plan, canonical, store, metadata_store, "aov", "baseline")
    assert unvalidated.validation_record.failure_code == "missing_validated_dependency"

    wrong_population_revenue = revenue.model_copy(update={"population_ref": "pop_other"})
    dep_validation = _validate_metric(
        outcome,
        plan,
        canonical,
        store,
        metadata_store,
        "aov",
        "baseline",
        dependencies=(wrong_population_revenue, orders),
    )
    assert dep_validation.validation_record.failure_code == "dependency_population_mismatch"

    wrong_period_orders = orders.model_copy(update={"period_ref": "comparison"})
    period_validation = _validate_metric(
        outcome,
        plan,
        canonical,
        store,
        metadata_store,
        "aov",
        "baseline",
        dependencies=(revenue, wrong_period_orders),
    )
    assert period_validation.validation_record.failure_code == "dependency_period_mismatch"


def test_aov_orders_zero_undefined_passes_and_zero_fails(tmp_path) -> None:
    outcome, plan, canonical, store, metadata_store = _executed(
        tmp_path,
        ("aov",),
        [_row(order_id="o1", order_line_id="l1", eligibility_status="cancelled")],
    )
    revenue = _validate_metric(outcome, plan, canonical, store, metadata_store, "revenue", "baseline").validated_result
    orders = _validate_metric(outcome, plan, canonical, store, metadata_store, "orders", "baseline").validated_result
    aov = _validate_metric(outcome, plan, canonical, store, metadata_store, "aov", "baseline", dependencies=(revenue, orders))

    assert aov.validation_record.status is ValidationStatus.PASSED
    assert aov.validated_result.value is None
    assert aov.validated_result.metric_state is MetricState.UNDEFINED
    assert aov.validated_result.undefined_reason == "orders_equals_zero"

    tampered_record, tampered_result = _persist_replacement_result(
        outcome,
        plan,
        canonical,
        store,
        metadata_store,
        "aov",
        "baseline",
        result_updates={"value": Decimal("0"), "metric_state": MetricState.VALID, "undefined_reason": None},
        recompute_fingerprint=True,
        suffix="aov_zero",
    )
    validation = validate_executed_result(
        execution_id=tampered_record.execution_id,
        result_id=tampered_result.result_id,
        plan=plan,
        canonical_dataset=canonical,
        artifact_store=store,
        metadata_store=metadata_store,
        dependency_validated_results=(revenue, orders),
    )
    assert validation.validation_record.failure_code == "aov_undefined_mismatch"
    restored = ValidatedResult.model_validate_json(
        store.safe_path(aov.validation_record.validated_result_artifact_ref.path).read_text(encoding="utf-8")
    )
    assert restored.value is None
    assert restored.metric_state is MetricState.UNDEFINED


def test_repeated_validation_attempts_have_unique_events_and_equivalent_fingerprint(tmp_path) -> None:
    outcome, plan, canonical, store, metadata_store = _executed(tmp_path, ("revenue",), [_row()])
    second_outcome = execute_plan(plan, canonical, store, metadata_store)
    first = _validate_metric(outcome, plan, canonical, store, metadata_store, "revenue", "baseline")
    second = _validate_metric(outcome, plan, canonical, store, metadata_store, "revenue", "baseline")
    equivalent_execution = _validate_metric(
        second_outcome,
        plan,
        canonical,
        store,
        metadata_store,
        "revenue",
        "baseline",
    )

    assert first.validation_record.validation_id != second.validation_record.validation_id
    assert first.validation_record.started_at <= first.validation_record.ended_at
    assert second.validation_record.started_at <= second.validation_record.ended_at
    assert first.validation_record.validation_fingerprint == second.validation_record.validation_fingerprint
    assert first.validation_record.validation_fingerprint == equivalent_execution.validation_record.validation_fingerprint
    assert first.validated_result.validation_fingerprint == second.validated_result.validation_fingerprint
    assert len(metadata_store.list_validation_records()) == 3


def test_v3_metadata_migrates_to_v4_and_malformed_v3_fails_closed(tmp_path) -> None:
    db_path = tmp_path / "legacy.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE schema_version (id INTEGER PRIMARY KEY CHECK (id = 1), version INTEGER NOT NULL)")
    conn.execute("INSERT INTO schema_version (id, version) VALUES (1, 3)")
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
    conn.execute(
        """
        INSERT INTO execution_records (
            execution_id, request_id, plan_id, plan_node_id, metric_ref, status,
            result_ref, result_artifact_id, started_at, ended_at, record_json
        )
        VALUES ('exec_1', 'req_1', 'plan_1', 'node_1', 'revenue', 'completed', 'res_1', 'art_1', '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:01+00:00', '{}')
        """
    )
    conn.commit()
    conn.close()

    store = MetadataStore(db_path)
    store.initialize()

    assert store.schema_version() == SCHEMA_VERSION
    reopened = sqlite3.connect(db_path)
    try:
        assert reopened.execute("SELECT COUNT(*) FROM execution_records").fetchone()[0] == 1
        tables = {row[0] for row in reopened.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()}
        assert "validation_records" in tables
    finally:
        reopened.close()

    malformed = tmp_path / "malformed.sqlite"
    conn = sqlite3.connect(malformed)
    conn.execute("CREATE TABLE schema_version (id INTEGER PRIMARY KEY CHECK (id = 1), version INTEGER NOT NULL)")
    conn.execute("INSERT INTO schema_version (id, version) VALUES (1, 3)")
    _create_supported_v2_tables(conn)
    conn.execute("CREATE TABLE execution_records (execution_id TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()

    with pytest.raises(RuntimeError, match="version 3 is incompatible"):
        MetadataStore(malformed).initialize()


def _executed(
    tmp_path: Path,
    metrics: tuple[str, ...],
    rows: list[dict[str, str]],
    *,
    filename: str = "orders.csv",
):
    plan, canonical, store = _execution_inputs(tmp_path, metrics, rows, filename=filename)
    metadata_store = MetadataStore(tmp_path / f"{filename}_registry.sqlite")
    outcome = execute_plan(plan, canonical, store, metadata_store)
    return outcome, plan, canonical, store, metadata_store


def _validate_metric(
    outcome,
    plan,
    canonical,
    store,
    metadata_store,
    metric_ref: str,
    period_ref: str,
    *,
    dependencies: tuple[ValidatedResult, ...] = (),
):
    record = _record(outcome, metric_ref, period_ref)
    result = _result(outcome, metric_ref, period_ref)
    return validate_executed_result(
        execution_id=record.execution_id,
        result_id=result.result_id,
        plan=plan,
        canonical_dataset=canonical,
        artifact_store=store,
        metadata_store=metadata_store,
        dependency_validated_results=dependencies,
    )


def _persist_replacement_result(
    outcome,
    plan,
    canonical,
    store: ArtifactStore,
    metadata_store: MetadataStore,
    metric_ref: str,
    period_ref: str,
    *,
    value=Ellipsis,
    result_updates: dict | None = None,
    recompute_fingerprint: bool,
    suffix: str = "tampered",
):
    original_record = _record(outcome, metric_ref, period_ref)
    original_result = _result(outcome, metric_ref, period_ref)
    execution_id = generate_id(f"exec_{suffix}")
    result_id = generate_id(f"exres_{suffix}")
    updates = {
        "execution_id": execution_id,
        "result_id": result_id,
    }
    if value is not Ellipsis:
        updates["value"] = value
    updates.update(result_updates or {})
    result = original_result.model_copy(update=updates)
    if recompute_fingerprint:
        node = next(item for item in plan.ordered_metrics if item.node_id == original_record.plan_node_id)
        population = next(item for item in plan.population_definitions if item.population_id == result.scope_ref)
        result = result.model_copy(
            update={
                "result_fingerprint": _result_fingerprint(
                    node,
                    population,
                    canonical,
                    result.value,
                    result.metric_state,
                    result.undefined_reason,
                    result.precision or "",
                    result.unit or "",
                    original_record.resolved_currency if result.unit != "orders" else None,
                )
            }
        )
    artifact = store.write_json_artifact(
        Path("runs") / execution_id / "results" / f"{result_id}.json",
        result.model_dump(mode="json"),
    )
    metadata_store.insert_artifact_reference(artifact)
    record = original_record.model_copy(
        update={
            "execution_id": execution_id,
            "result_ref": result_id,
            "output_artifacts": (artifact,),
        }
    )
    metadata_store.insert_execution_record(record)
    return record, result
