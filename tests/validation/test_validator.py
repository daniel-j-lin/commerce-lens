from __future__ import annotations

import json
import sqlite3
from decimal import Decimal, ROUND_DOWN, ROUND_UP, getcontext, localcontext
from pathlib import Path

import pytest

from commerce_lens.contracts.common import MetricState
from commerce_lens.contracts.validation import ValidatedResult, ValidationStatus
from commerce_lens.engine import execute_plan
from commerce_lens.engine.execution import _result_fingerprint
from commerce_lens.engine.execution import _revenue_change_result_fingerprint
from commerce_lens.evidence.identifiers import generate_id
from commerce_lens.metrics.registry import get_metric_registry
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import SCHEMA_VERSION, MetadataStore
from commerce_lens.validation import validate_executed_result
from commerce_lens.validation.rules import P5_VALIDATION_RULES, P5_VALIDATION_RULE_VERSION, P7_VALIDATION_RULE_VERSION
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
    assert tuple(record.validation_rule_id for record in validation.validation_records) == (
        "validation:revenue_sum",
        "validation:currency_consistency",
        "validation:population_consistency",
    )
    assert all(record.status is ValidationStatus.PASSED for record in validation.validation_records)
    assert validation.validation_record.expected_value == Decimal("15.25")
    assert validation.validated_result is not None
    assert validation.validated_result.value == Decimal("15.25")
    assert validation.validated_result.metric_state is MetricState.VALID
    assert validation.validated_result.required_validation_record_ids == tuple(
        record.validation_id for record in validation.validation_records
    )
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
    assert tuple(record.validation_id for record in first.validation_records) != tuple(
        record.validation_id for record in second.validation_records
    )
    assert first.validation_record.started_at <= first.validation_record.ended_at
    assert second.validation_record.started_at <= second.validation_record.ended_at
    assert tuple(record.validation_fingerprint for record in first.validation_records) == tuple(
        record.validation_fingerprint for record in second.validation_records
    )
    assert tuple(record.validation_fingerprint for record in first.validation_records) == tuple(
        record.validation_fingerprint for record in equivalent_execution.validation_records
    )
    assert first.validated_result.validation_fingerprint == second.validated_result.validation_fingerprint
    assert first.validated_result.validated_result_id != second.validated_result.validated_result_id
    assert len(metadata_store.list_validation_records()) == 9


def test_required_rule_registry_and_successful_record_sets(tmp_path) -> None:
    registry = get_metric_registry()
    assert registry.require("revenue").required_validation_rule_refs == (
        "validation:revenue_sum",
        "validation:currency_consistency",
        "validation:population_consistency",
    )
    assert registry.require("orders").required_validation_rule_refs == (
        "validation:distinct_order_count",
        "validation:population_consistency",
    )
    assert registry.require("aov").required_validation_rule_refs == (
        "validation:aov_from_revenue_orders",
        "validation:population_consistency",
    )
    assert registry.require("revenue_change").required_validation_rule_refs == (
        "validation:revenue_change_from_validated_revenues",
        "validation:revenue_change_dependency_context",
        "validation:revenue_change_currency_consistency",
    )
    assert tuple(P5_VALIDATION_RULES) == (
        "validation:revenue_sum",
        "validation:currency_consistency",
        "validation:population_consistency",
        "validation:distinct_order_count",
        "validation:aov_from_revenue_orders",
        "validation:revenue_change_from_validated_revenues",
        "validation:revenue_change_dependency_context",
        "validation:revenue_change_currency_consistency",
    )
    assert {rule.rule_version for rule in P5_VALIDATION_RULES.values()} == {
        P5_VALIDATION_RULE_VERSION,
        P7_VALIDATION_RULE_VERSION,
    }

    outcome, plan, canonical, store, metadata_store = _executed(tmp_path, ("aov",), [_row(line_revenue="10.00")])
    revenue = _validate_metric(outcome, plan, canonical, store, metadata_store, "revenue", "baseline")
    orders = _validate_metric(outcome, plan, canonical, store, metadata_store, "orders", "baseline")
    aov = _validate_metric(
        outcome,
        plan,
        canonical,
        store,
        metadata_store,
        "aov",
        "baseline",
        dependencies=(revenue.validated_result, orders.validated_result),
    )

    assert _record_rule_ids(revenue) == registry.require("revenue").required_validation_rule_refs
    assert _record_rule_ids(orders) == registry.require("orders").required_validation_rule_refs
    assert _record_rule_ids(aov) == registry.require("aov").required_validation_rule_refs
    assert len(revenue.validated_result.required_validation_record_ids) == 3
    assert len(orders.validated_result.required_validation_record_ids) == 2
    assert len(aov.validated_result.required_validation_record_ids) == 2
    for validation in (revenue, orders, aov):
        records = [metadata_store.get_validation_record(record_id) for record_id in validation.validated_result.required_validation_record_ids]
        assert [record.status for record in records] == [ValidationStatus.PASSED] * len(records)


def test_revenue_change_validates_from_authentic_baseline_and_comparison_revenues(tmp_path) -> None:
    outcome, plan, canonical, store, metadata_store = _executed(
        tmp_path,
        ("revenue_change",),
        [
            _row(order_id="o1", order_date="2026-01-01", line_revenue="100.00"),
            _row(order_id="o2", order_date="2026-01-03", line_revenue="120.00"),
        ],
    )
    baseline = _validate_metric(outcome, plan, canonical, store, metadata_store, "revenue", "baseline").validated_result
    comparison = _validate_metric(outcome, plan, canonical, store, metadata_store, "revenue", "comparison").validated_result

    validation = _validate_metric(
        outcome,
        plan,
        canonical,
        store,
        metadata_store,
        "revenue_change",
        "comparison",
        dependencies=(baseline, comparison),
    )

    assert validation.validation_record.status is ValidationStatus.PASSED
    assert _record_rule_ids(validation) == get_metric_registry().require("revenue_change").required_validation_rule_refs
    assert validation.validated_result is not None
    assert validation.validated_result.value == Decimal("20.00")
    assert validation.validated_result.metric_state is MetricState.VALID
    assert validation.validated_result.period_ref == "comparison"
    assert validation.validated_result.period_role == "baseline_and_comparison"
    assert len(validation.validated_result.required_validation_record_ids) == 3


def test_revenue_change_validation_rejects_current_dependency_execution_record_dataset_tamper(tmp_path) -> None:
    context = _revenue_change_validation_context(tmp_path)
    _tamper_dependency_execution_record(
        context["metadata_store"],
        context["baseline"].execution_id,
        {"dataset_ref_ids": ("ds_substituted",)},
    )

    validation = _validate_revenue_change_context(context)

    assert validation.validation_record.status is ValidationStatus.FAILED
    assert validation.validation_record.failure_code == "dependency_lineage_mismatch"
    assert validation.validated_result is None


@pytest.mark.parametrize("period_role", ("baseline", "comparison"))
@pytest.mark.parametrize(
    "field_name",
    (
        "dataset_ref_ids",
        "canonical_dataset_ref_ids",
        "canonical_dataset_fingerprints",
        "population_refs",
        "population_fingerprints",
        "plan_node_id",
        "period_refs",
        "period_role",
        "scope_filters",
        "grouping",
        "metric_refs",
        "metric_definition_version",
        "metric_implementation_ref",
        "resolved_currency",
    ),
)
def test_revenue_change_validation_rejects_current_dependency_execution_record_lineage_tamper(
    tmp_path,
    field_name: str,
    period_role: str,
) -> None:
    context = _revenue_change_validation_context(tmp_path)
    dependency = context[period_role]
    update = {field_name: _tampered_dependency_execution_record_value(field_name, period_role)}

    _tamper_dependency_execution_record(context["metadata_store"], dependency.execution_id, update)
    validation = _validate_revenue_change_context(context)

    assert validation.validation_record.status is ValidationStatus.FAILED
    assert validation.validation_record.failure_code == "dependency_lineage_mismatch"
    assert validation.validated_result is None


def test_revenue_change_validation_rejects_cross_run_equal_value_dependency_record_substitution(tmp_path) -> None:
    context = _revenue_change_validation_context(tmp_path, filename="original.csv")
    foreign = _revenue_change_validation_context(
        tmp_path,
        filename="foreign.csv",
        rows=[
            _row(order_id="o1", order_date="2026-01-01", line_revenue="100.00"),
            _row(order_id="o2", order_date="2026-01-03", line_revenue="120.00"),
            _row(order_id="o3", order_date="2026-01-04", line_revenue="999.00", eligibility_status="cancelled"),
        ],
    )
    original_record = context["metadata_store"].get_execution_record(context["baseline"].execution_id)
    foreign_record = foreign["metadata_store"].get_execution_record(foreign["baseline"].execution_id)
    assert original_record is not None
    assert foreign_record is not None
    assert context["baseline"].value == foreign["baseline"].value == Decimal("100.00")

    _replace_execution_record(
        context["metadata_store"],
        original_record.model_copy(
            update={
                "request_id": foreign_record.request_id,
                "plan_id": foreign_record.plan_id,
                "plan_fingerprint": foreign_record.plan_fingerprint,
                "dataset_ref_ids": foreign_record.dataset_ref_ids,
                "canonical_dataset_ref_ids": foreign_record.canonical_dataset_ref_ids,
                "canonical_dataset_fingerprints": foreign_record.canonical_dataset_fingerprints,
                "population_refs": foreign_record.population_refs,
                "population_fingerprints": foreign_record.population_fingerprints,
                "period_refs": foreign_record.period_refs,
                "period_role": foreign_record.period_role,
            }
        ),
    )

    validation = _validate_revenue_change_context(context)

    assert validation.validation_record.status is ValidationStatus.FAILED
    assert validation.validation_record.failure_code == "dependency_request_mismatch"
    assert validation.validated_result is None


@pytest.mark.parametrize(
    ("tamper", "expected_code"),
    [
        ("missing_comparison", "missing_validated_dependency"),
        ("duplicate_baseline", "duplicate_validated_dependency"),
        ("wrong_plan", "dependency_plan_mismatch"),
        ("wrong_node", "dependency_plan_node_mismatch"),
        ("wrong_metric", "dependency_metric_mismatch"),
        ("wrong_period_role", "dependency_period_mismatch"),
        ("wrong_population", "dependency_population_mismatch"),
        ("wrong_currency", "dependency_validated_result_artifact_mismatch"),
        ("forged_bundle", "dependency_validation_fingerprint_mismatch"),
        ("failed_record", "dependency_validation_record_failed"),
    ],
)
def test_revenue_change_dependency_authority_failures(tmp_path, tamper, expected_code) -> None:
    outcome, plan, canonical, store, metadata_store = _executed(
        tmp_path,
        ("revenue_change",),
        [
            _row(order_id="o1", order_date="2026-01-01", line_revenue="100.00"),
            _row(order_id="o2", order_date="2026-01-03", line_revenue="120.00"),
        ],
    )
    baseline = _validate_metric(outcome, plan, canonical, store, metadata_store, "revenue", "baseline").validated_result
    comparison = _validate_metric(outcome, plan, canonical, store, metadata_store, "revenue", "comparison").validated_result
    dependencies = (baseline, comparison)
    if tamper == "missing_comparison":
        dependencies = (baseline,)
    elif tamper == "duplicate_baseline":
        dependencies = (baseline, baseline.model_copy(update={"validated_result_id": "valres_duplicate"}))
    elif tamper == "wrong_plan":
        dependencies = (baseline.model_copy(update={"plan_id": "plan_wrong"}), comparison)
    elif tamper == "wrong_node":
        dependencies = (baseline.model_copy(update={"plan_node_id": "node_wrong"}), comparison)
    elif tamper == "wrong_metric":
        dependencies = (baseline.model_copy(update={"metric_ref": "orders"}), comparison)
    elif tamper == "wrong_period_role":
        dependencies = (baseline.model_copy(update={"period_role": "forecast"}), comparison)
    elif tamper == "wrong_population":
        dependencies = (baseline.model_copy(update={"population_ref": "pop_wrong"}), comparison)
    elif tamper == "wrong_currency":
        dependencies = (baseline.model_copy(update={"currency": "EUR"}), comparison)
    elif tamper == "forged_bundle":
        dependencies = (baseline.model_copy(update={"validation_fingerprint": "f" * 64}), comparison)
    elif tamper == "failed_record":
        _set_validation_record_status(metadata_store, baseline.required_validation_record_ids[0], "failed")

    validation = _validate_metric(
        outcome,
        plan,
        canonical,
        store,
        metadata_store,
        "revenue_change",
        "comparison",
        dependencies=dependencies,
    )

    assert validation.validation_record.status is ValidationStatus.FAILED
    assert validation.validation_record.failure_code == expected_code
    assert validation.validated_result is None


def test_revenue_change_incorrect_arithmetic_fails_after_result_fingerprint_recomputed(tmp_path) -> None:
    outcome, plan, canonical, store, metadata_store = _executed(
        tmp_path,
        ("revenue_change",),
        [
            _row(order_id="o1", order_date="2026-01-01", line_revenue="100.00"),
            _row(order_id="o2", order_date="2026-01-03", line_revenue="120.00"),
        ],
    )
    baseline = _validate_metric(outcome, plan, canonical, store, metadata_store, "revenue", "baseline").validated_result
    comparison = _validate_metric(outcome, plan, canonical, store, metadata_store, "revenue", "comparison").validated_result
    tampered_record, tampered_result = _persist_replacement_result(
        outcome,
        plan,
        canonical,
        store,
        metadata_store,
        "revenue_change",
        "comparison",
        value=Decimal("21.00"),
        recompute_fingerprint=True,
    )

    validation = validate_executed_result(
        execution_id=tampered_record.execution_id,
        result_id=tampered_result.result_id,
        plan=plan,
        canonical_dataset=canonical,
        artifact_store=store,
        metadata_store=metadata_store,
        dependency_validated_results=(baseline, comparison),
    )

    assert validation.validation_record.status is ValidationStatus.FAILED
    assert validation.validation_record.failure_code == "value_mismatch"
    assert validation.validated_result is None


@pytest.mark.parametrize(
    ("refs", "expected_code"),
    [
        ((), "required_validation_rule_refs_mismatch"),
        (("validation:forged_rule",), "required_validation_rule_refs_mismatch"),
        (("validation:revenue_sum", "validation:currency_consistency"), "required_validation_rule_refs_mismatch"),
        (
            (
                "validation:revenue_sum",
                "validation:currency_consistency",
                "validation:population_consistency",
                "validation:forged_rule",
            ),
            "required_validation_rule_refs_mismatch",
        ),
    ],
)
def test_plan_required_validation_rule_refs_are_enforced(tmp_path, refs, expected_code) -> None:
    outcome, plan, canonical, store, metadata_store = _executed(tmp_path, ("revenue",), [_row()])
    bad_plan = _plan_with_node_rule_refs(plan, "revenue", "baseline", refs)

    validation = _validate_metric(outcome, bad_plan, canonical, store, metadata_store, "revenue", "baseline")

    assert validation.validation_record.status is ValidationStatus.FAILED
    assert validation.validation_record.failure_code == expected_code
    assert validation.validated_result is None


def test_exact_valid_plan_required_validation_rule_refs_pass(tmp_path) -> None:
    outcome, plan, canonical, store, metadata_store = _executed(tmp_path, ("revenue",), [_row()])

    validation = _validate_metric(outcome, plan, canonical, store, metadata_store, "revenue", "baseline")

    assert validation.validation_record.status is ValidationStatus.PASSED


@pytest.mark.parametrize(
    ("tamper", "expected_code"),
    [
        ("wrong_plan_id", "dependency_plan_mismatch"),
        ("wrong_plan_node_id", "dependency_plan_node_mismatch"),
        ("wrong_dependency_node", "dependency_plan_node_mismatch"),
        ("nonexistent_validation_record_id", "dependency_validation_record_missing"),
        ("missing_validation_record", "dependency_validation_record_missing"),
        ("failed_validation_record", "dependency_validation_record_failed"),
        ("missing_validated_result_artifact", "dependency_validated_result_artifact_missing"),
        ("artifact_content_differs", "dependency_validated_result_artifact_hash_mismatch"),
        ("forged_validation_fingerprint", "dependency_validation_fingerprint_mismatch"),
        ("incomplete_required_rules", "dependency_required_validation_incomplete"),
        ("wrong_rule_ids", "dependency_required_validation_wrong_rules"),
        ("equivalent_wrong_plan", "dependency_plan_mismatch"),
    ],
)
def test_aov_dependency_persisted_authority_failures(tmp_path, tamper, expected_code) -> None:
    outcome, plan, canonical, store, metadata_store = _executed(
        tmp_path,
        ("aov",),
        [
            _row(order_id="o1", order_line_id="l1", line_revenue="7.00"),
            _row(order_id="o2", order_line_id="l1", line_revenue="3.00"),
        ],
    )
    revenue = _validate_metric(outcome, plan, canonical, store, metadata_store, "revenue", "baseline").validated_result
    orders = _validate_metric(outcome, plan, canonical, store, metadata_store, "orders", "baseline").validated_result

    if tamper == "wrong_plan_id":
        revenue = revenue.model_copy(update={"plan_id": "plan_unrelated_wrong_authority"})
    elif tamper == "wrong_plan_node_id":
        revenue = revenue.model_copy(update={"plan_node_id": "node_unrelated_wrong_authority"})
    elif tamper == "wrong_dependency_node":
        comparison_revenue = _validate_metric(outcome, plan, canonical, store, metadata_store, "revenue", "comparison").validated_result
        revenue = comparison_revenue
    elif tamper == "nonexistent_validation_record_id":
        revenue = revenue.model_copy(update={"required_validation_record_ids": ("val_missing", *revenue.required_validation_record_ids[1:])})
    elif tamper == "missing_validation_record":
        _delete_validation_record(metadata_store, revenue.required_validation_record_ids[0])
    elif tamper == "failed_validation_record":
        _set_validation_record_status(metadata_store, revenue.required_validation_record_ids[0], "failed")
    elif tamper == "missing_validated_result_artifact":
        artifact = metadata_store.get_validation_record(revenue.required_validation_record_ids[0]).validated_result_artifact_ref
        store.safe_path(artifact.path).unlink()
    elif tamper == "artifact_content_differs":
        artifact = metadata_store.get_validation_record(revenue.required_validation_record_ids[0]).validated_result_artifact_ref
        path = store.safe_path(artifact.path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["value"] = "999.00"
        path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    elif tamper == "forged_validation_fingerprint":
        revenue = revenue.model_copy(update={"validation_fingerprint": "f" * 64})
    elif tamper == "incomplete_required_rules":
        revenue = revenue.model_copy(update={"required_validation_record_ids": revenue.required_validation_record_ids[:1]})
    elif tamper == "wrong_rule_ids":
        _set_validation_record_rule_id(metadata_store, revenue.required_validation_record_ids[0], "validation:forged_rule")
    elif tamper == "equivalent_wrong_plan":
        revenue = revenue.model_copy(update={"plan_id": "plan_otherwise_equivalent_wrong_authority"})

    validation = _validate_metric(
        outcome,
        plan,
        canonical,
        store,
        metadata_store,
        "aov",
        "baseline",
        dependencies=(revenue, orders),
    )

    assert validation.validation_record.status is ValidationStatus.FAILED
    assert validation.validation_record.failure_code == expected_code
    assert validation.validated_result is None


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
        if metric_ref == "revenue_change":
            populations = {item.population_id: item for item in plan.population_definitions}
            by_role = {populations[ref].period_role.value: populations[ref] for ref in node.population_refs}
            baseline_result = _result(outcome, "revenue", "baseline")
            comparison_result = _result(outcome, "revenue", "comparison")
            fingerprint = _revenue_change_result_fingerprint(
                node=node,
                baseline_population=by_role["baseline"],
                comparison_population=by_role["comparison"],
                canonical_dataset=canonical,
                value=result.value,
                currency=original_record.resolved_currency,
                baseline_result=baseline_result,
                comparison_result=comparison_result,
            )
        else:
            fingerprint = _result_fingerprint(
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
        result = result.model_copy(update={"result_fingerprint": fingerprint})
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


def _record_rule_ids(validation) -> tuple[str, ...]:
    return tuple(record.validation_rule_id for record in validation.validation_records)


def _plan_with_node_rule_refs(plan, metric_ref: str, period_ref: str, refs: tuple[str, ...]):
    return plan.model_copy(
        update={
            "ordered_metrics": tuple(
                node.model_copy(update={"required_validation_rule_refs": refs})
                if node.metric_ref == metric_ref and period_ref in node.period_refs
                else node
                for node in plan.ordered_metrics
            )
        }
    )


def _revenue_change_validation_context(
    tmp_path: Path,
    *,
    filename: str = "orders.csv",
    rows: list[dict[str, str]] | None = None,
):
    outcome, plan, canonical, store, metadata_store = _executed(
        tmp_path,
        ("revenue_change",),
        rows
        or [
            _row(order_id="o1", order_date="2026-01-01", line_revenue="100.00"),
            _row(order_id="o2", order_date="2026-01-03", line_revenue="120.00"),
        ],
        filename=filename,
    )
    baseline = _validate_metric(outcome, plan, canonical, store, metadata_store, "revenue", "baseline").validated_result
    comparison = _validate_metric(outcome, plan, canonical, store, metadata_store, "revenue", "comparison").validated_result
    return {
        "outcome": outcome,
        "plan": plan,
        "canonical": canonical,
        "store": store,
        "metadata_store": metadata_store,
        "baseline": baseline,
        "comparison": comparison,
    }


def _validate_revenue_change_context(context):
    return _validate_metric(
        context["outcome"],
        context["plan"],
        context["canonical"],
        context["store"],
        context["metadata_store"],
        "revenue_change",
        "comparison",
        dependencies=(context["baseline"], context["comparison"]),
    )


def _tamper_dependency_execution_record(metadata_store: MetadataStore, execution_id: str, update: dict) -> None:
    record = metadata_store.get_execution_record(execution_id)
    assert record is not None
    _replace_execution_record(metadata_store, record.model_copy(update=update))


def _tampered_dependency_execution_record_value(field_name: str, period_role: str):
    other_period = "comparison" if period_role == "baseline" else "baseline"
    return {
        "dataset_ref_ids": ("ds_substituted",),
        "canonical_dataset_ref_ids": ("cds_substituted",),
        "canonical_dataset_fingerprints": ("0" * 64,),
        "population_refs": ("pop_substituted",),
        "population_fingerprints": ("0" * 64,),
        "plan_node_id": "node_substituted",
        "period_refs": (other_period,),
        "period_role": other_period,
        "scope_filters": ({"field": "currency", "operator": "equals", "value": "EUR"},),
        "grouping": "product",
        "metric_refs": ("orders",),
        "metric_definition_version": "metric_dictionary_v0",
        "metric_implementation_ref": "p4_001:duckdb_reference:orders_v1",
        "resolved_currency": "EUR",
    }[field_name]


def _replace_execution_record(metadata_store: MetadataStore, record) -> None:
    result_artifact_id = record.output_artifacts[0].artifact_id if record.output_artifacts else None
    with sqlite3.connect(metadata_store.db_path) as conn:
        conn.execute(
            """
            UPDATE execution_records
            SET request_id = ?,
                plan_id = ?,
                plan_node_id = ?,
                metric_ref = ?,
                status = ?,
                result_ref = ?,
                result_artifact_id = ?,
                started_at = ?,
                ended_at = ?,
                record_json = ?
            WHERE execution_id = ?
            """,
            (
                record.request_id,
                record.plan_id,
                record.plan_node_id,
                record.metric_refs[0] if record.metric_refs else None,
                record.status.value,
                record.result_ref,
                result_artifact_id,
                record.started_at.isoformat(),
                record.ended_at.isoformat() if record.ended_at is not None else None,
                record.model_dump_json(),
                record.execution_id,
            ),
        )


def _delete_validation_record(metadata_store: MetadataStore, validation_id: str) -> None:
    with sqlite3.connect(metadata_store.db_path) as conn:
        conn.execute("DELETE FROM validation_records WHERE validation_id = ?", (validation_id,))


def _set_validation_record_status(metadata_store: MetadataStore, validation_id: str, status: str) -> None:
    record = metadata_store.get_validation_record(validation_id)
    payload = record.model_dump(mode="json")
    payload["status"] = status
    with sqlite3.connect(metadata_store.db_path) as conn:
        conn.execute(
            "UPDATE validation_records SET status = ?, record_json = ? WHERE validation_id = ?",
            (status, json.dumps(payload, sort_keys=True), validation_id),
        )


def _set_validation_record_rule_id(metadata_store: MetadataStore, validation_id: str, rule_id: str) -> None:
    record = metadata_store.get_validation_record(validation_id)
    payload = record.model_dump(mode="json")
    payload["validation_rule_id"] = rule_id
    with sqlite3.connect(metadata_store.db_path) as conn:
        conn.execute(
            "UPDATE validation_records SET record_json = ? WHERE validation_id = ?",
            (json.dumps(payload, sort_keys=True), validation_id),
        )
