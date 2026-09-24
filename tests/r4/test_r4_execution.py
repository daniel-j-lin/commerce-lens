from __future__ import annotations

from decimal import Decimal

import pytest

from commerce_lens.contracts.common import ScopeDefinition, ScopeFilter
from commerce_lens.contracts.r4 import R4ProductClassification
from commerce_lens.persistence.r4_repository import load_validated_r4_result
from tests.engine.test_execution import _row
from tests.r4.support import make_r4_fixture, run_r4


def test_all_three_components_execute_and_reconcile_exactly(tmp_path) -> None:
    fixture = make_r4_fixture(
        tmp_path,
        [
            _row(order_id="b1", order_line_id="l1", order_date="2026-01-01", product_id="exit", line_revenue="20.00"),
            _row(order_id="b2", order_line_id="l1", order_date="2026-01-01", product_id="continuing", line_revenue="30.00"),
            _row(order_id="c1", order_line_id="l1", order_date="2026-01-03", product_id="entry", line_revenue="40.00"),
            _row(order_id="c2", order_line_id="l1", order_date="2026-01-03", product_id="continuing", line_revenue="35.00"),
        ],
    )

    outcome = run_r4(fixture)
    result = outcome.validated_result

    assert result.entry_component == Decimal("40.00")
    assert result.exit_component == Decimal("-20.00")
    assert result.continuing_component == Decimal("5.00")
    assert result.component_sum == result.observed_revenue_change == Decimal("25.00")
    assert result.reconciliation_difference == Decimal("0.00")
    assert (result.entry_product_count, result.exit_product_count, result.continuing_product_count) == (1, 1, 1)
    assert outcome.validation.validation_record.status.value == "passed"
    restored = load_validated_r4_result(
        outcome.validation.validated_result_artifact,
        fixture.scalar.artifact_store,
        fixture.scalar.metadata_store,
    )
    assert restored == result


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        (
            [_row(order_date="2026-01-03", product_id="entry", line_revenue="7.00")],
            (Decimal("7.00"), Decimal("0"), Decimal("0")),
        ),
        (
            [_row(order_date="2026-01-01", product_id="exit", line_revenue="7.00")],
            (Decimal("0"), Decimal("-7.00"), Decimal("0")),
        ),
        (
            [
                _row(order_id="b", order_date="2026-01-01", product_id="same", line_revenue="7.00"),
                _row(order_id="c", order_date="2026-01-03", product_id="same", line_revenue="9.00"),
            ],
            (Decimal("0"), Decimal("0"), Decimal("2.00")),
        ),
    ],
)
def test_single_component_paths(tmp_path, rows, expected) -> None:
    scope = ScopeDefinition(
        scope_id="usd",
        filters=(ScopeFilter(field="currency", operator="equals", value="USD"),),
    )
    result = run_r4(make_r4_fixture(tmp_path, rows, scope=scope)).validated_result
    assert (result.entry_component, result.exit_component, result.continuing_component) == expected
    assert result.reconciliation_difference == Decimal("0")


def test_product_id_controls_identity_not_product_name(tmp_path) -> None:
    fixture = make_r4_fixture(
        tmp_path,
        [
            _row(order_id="b1", order_date="2026-01-01", product_id="stable", product_name="Old", line_revenue="10"),
            _row(order_id="c1", order_date="2026-01-03", product_id="stable", product_name="New", line_revenue="12"),
            _row(order_id="b2", order_date="2026-01-01", product_id="id-a", product_name="Shared", line_revenue="3"),
            _row(order_id="c2", order_date="2026-01-03", product_id="id-b", product_name="Shared", line_revenue="4"),
        ],
    )
    outcome = run_r4(fixture)
    rows = {row.product_id: row for row in outcome.execution.product_trace.rows}
    assert rows["stable"].classification is R4ProductClassification.CONTINUING
    assert rows["id-a"].classification is R4ProductClassification.BASELINE_ONLY
    assert rows["id-b"].classification is R4ProductClassification.COMPARISON_ONLY


def test_zero_revenue_is_presence_not_absence(tmp_path) -> None:
    fixture = make_r4_fixture(
        tmp_path,
        [
            _row(order_id="b", order_date="2026-01-01", product_id="zero-present", line_revenue="0"),
            _row(order_id="c", order_date="2026-01-03", product_id="zero-present", line_revenue="5.00"),
        ],
    )
    outcome = run_r4(fixture)
    row = outcome.execution.product_trace.rows[0]
    assert row.baseline_present is True and row.comparison_present is True
    assert row.classification is R4ProductClassification.CONTINUING
    assert outcome.validated_result.continuing_component == Decimal("5.00")
    assert outcome.validated_result.entry_component == Decimal("0")


def test_zero_total_change_with_offsetting_components(tmp_path) -> None:
    fixture = make_r4_fixture(
        tmp_path,
        [
            _row(order_id="b", order_date="2026-01-01", product_id="exit", line_revenue="10"),
            _row(order_id="c", order_date="2026-01-03", product_id="entry", line_revenue="10"),
        ],
    )
    result = run_r4(fixture).validated_result
    assert result.entry_component == Decimal("10")
    assert result.exit_component == Decimal("-10")
    assert result.observed_revenue_change == result.component_sum == result.reconciliation_difference == Decimal("0")


def test_both_complete_governed_periods_empty_produce_empty_zero_decomposition(tmp_path) -> None:
    scope = ScopeDefinition(
        scope_id="usd",
        filters=(ScopeFilter(field="currency", operator="equals", value="USD"),),
    )
    fixture = make_r4_fixture(
        tmp_path,
        [
            _row(order_id="excluded-b", order_date="2026-01-01", eligibility_status="cancelled"),
            _row(order_id="excluded-c", order_date="2026-01-03", eligibility_status="cancelled"),
        ],
        scope=scope,
    )
    outcome = run_r4(fixture)
    result = outcome.validated_result
    assert result.product_count == 0
    assert outcome.execution.product_trace.rows == ()
    assert result.entry_component == result.exit_component == result.continuing_component == Decimal("0")
    assert result.observed_revenue_change == result.reconciliation_difference == Decimal("0")


def test_decimal_precision_and_material_determinism_survive_row_order(tmp_path) -> None:
    rows = [
        _row(order_id="b1", order_line_id="l1", order_date="2026-01-01", product_id="p", line_revenue="0.123456789123"),
        _row(order_id="c1", order_line_id="l1", order_date="2026-01-03", product_id="p", line_revenue="0.123456789130"),
        _row(order_id="c2", order_line_id="l1", order_date="2026-01-03", product_id="q", line_revenue="0.000000000007"),
    ]
    first_fixture = make_r4_fixture(tmp_path / "first", rows)
    first = run_r4(first_fixture)
    second_same_authority = run_r4(first_fixture)
    repeated = run_r4(make_r4_fixture(tmp_path / "second", list(reversed(rows))))
    assert first.validated_result.continuing_component == Decimal("0.000000000007")
    assert first.validated_result.entry_component == Decimal("0.000000000007")
    assert first.validated_result.result_fingerprint == second_same_authority.validated_result.result_fingerprint
    assert first.validated_result.product_trace_fingerprint == second_same_authority.validated_result.product_trace_fingerprint
    assert first.validated_result.execution_id != second_same_authority.validated_result.execution_id
    assert (
        first.validated_result.entry_component,
        first.validated_result.exit_component,
        first.validated_result.continuing_component,
    ) == (
        repeated.validated_result.entry_component,
        repeated.validated_result.exit_component,
        repeated.validated_result.continuing_component,
    )
    assert tuple(row.product_id for row in first.execution.product_trace.rows) == tuple(
        row.product_id for row in repeated.execution.product_trace.rows
    )
