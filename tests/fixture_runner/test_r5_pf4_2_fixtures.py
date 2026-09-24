from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from commerce_lens.fixture_runner.r5_comparator import compare_fixture
from commerce_lens.fixture_runner.r5_inventory import ImplementationStatus, load_r5_inventory
from commerce_lens.fixture_runner.r5_manifest import load_r5_manifest
from commerce_lens.fixture_runner.r5_pf4_adapters import build_r5_pf4_adapter_registry
from commerce_lens.fixture_runner.r5_result import HarnessResultStatus


ROOT = Path(__file__).resolve().parents[2]
R4_ROOT = ROOT / "fixtures/r5/active/R4"
PF4_2_IDS = (
    "FX-R5-R4-007A",
    "FX-R5-R4-007B",
    "FX-R5-R4-008A",
    "FX-R5-R4-009A",
    "FX-R5-R4-010A",
    "FX-R5-R4-011A",
    "FX-R5-R4-012A",
    "FX-R5-R4-013A",
)


@pytest.fixture(scope="module")
def pf4_2_state():
    registry = build_r5_pf4_adapter_registry()
    fixtures = {}
    actuals = {}
    results = {}
    for fixture_id in PF4_2_IDS:
        fixture = load_r5_manifest(R4_ROOT / fixture_id)
        producer = registry.require(fixture.manifest.execution.adapter_id).producer
        assert producer is not None
        actual = producer(fixture)
        fixtures[fixture_id] = fixture
        actuals[fixture_id] = actual
        results[fixture_id] = compare_fixture(fixture, actual)
    return fixtures, actuals, results


def _material(actual):
    return next(item.outcome for item in actual.material_path if item.stage.value == "validation")


def _rows(actual):
    return {item["product_id"]: item for item in _material(actual)["trace_rows"]}


def test_exact_pf4_2_set_passes_exact_comparison(pf4_2_state) -> None:
    fixtures, _, results = pf4_2_state
    assert tuple(sorted(fixtures)) == PF4_2_IDS
    for fixture_id, result in results.items():
        assert result.status is HarnessResultStatus.PASS, (fixture_id, result.mismatches)
        assert result.mismatches == ()


def test_complete_empty_period_semantics_are_exact(pf4_2_state) -> None:
    actuals = pf4_2_state[1]
    entry = _material(actuals["FX-R5-R4-007A"])
    exit_case = _material(actuals["FX-R5-R4-007B"])
    both_empty = _material(actuals["FX-R5-R4-008A"])
    assert (entry["entry_component"], entry["product_count"]) == ("100.00", 2)
    assert all(not row["baseline_present"] for row in entry["trace_rows"])
    assert (exit_case["exit_component"], exit_case["product_count"]) == ("-100.00", 2)
    assert all(not row["comparison_present"] for row in exit_case["trace_rows"])
    assert both_empty["trace_rows"] == []
    assert all(
        both_empty[field] == "0"
        for field in (
            "baseline_revenue",
            "comparison_revenue",
            "observed_revenue_change",
            "entry_component",
            "exit_component",
            "continuing_component",
            "component_sum",
            "reconciliation_difference",
        )
    )


def test_zero_revenue_line_still_establishes_presence(pf4_2_state) -> None:
    row = _rows(pf4_2_state[1]["FX-R5-R4-009A"])["p_a"]
    assert row["baseline_present"] is True
    assert row["baseline_revenue"] == "0.00"
    assert row["classification"] == "continuing"
    assert row["assigned_component"] == "continuing_product_revenue_change"


def test_product_identity_is_id_based_not_name_based(pf4_2_state) -> None:
    actuals = pf4_2_state[1]
    stable = _rows(actuals["FX-R5-R4-011A"])
    distinct = _rows(actuals["FX-R5-R4-012A"])
    assert tuple(stable) == ("p_a",)
    assert stable["p_a"]["classification"] == "continuing"
    assert set(distinct) == {"p_a", "p_b"}
    assert {row["classification"] for row in distinct.values()} == {
        "baseline_only",
        "comparison_only",
    }


def test_missing_and_confirmed_corrupt_identity_fail_before_execution(pf4_2_state) -> None:
    actuals = pf4_2_state[1]
    expected = {
        "FX-R5-R4-010A": (
            "product_identity_missing",
            "R4_NOT_EXECUTED__PRODUCT_IDENTITY_MISSING",
        ),
        "FX-R5-R4-013A": (
            "product_identity_defect",
            "R4_NOT_EXECUTED__PRODUCT_IDENTITY_CORRUPT",
        ),
    }
    for fixture_id, (code, disposition) in expected.items():
        actual = actuals[fixture_id]
        assert actual.material_path[0].reachability.value == "blocked"
        assert actual.material_path[0].outcome == code
        assert actual.material_path[1].reachability.value == "not_reached"
        assert actual.final_disposition == disposition
        assert actual.trace_integrity_state == {
            "failure_layer": "ELIGIBILITY",
            "production_failure_code": code,
        }


def test_pf4_2_inventory_floor_remains_satisfied() -> None:
    inventory = load_r5_inventory(ROOT)
    statuses = Counter(item.implementation_status for item in inventory.active.entries)
    assert statuses[ImplementationStatus.EXECUTABLE] >= 83
    assert statuses[ImplementationStatus.DEPENDENCY_BLOCKED] == 1
    assert statuses[ImplementationStatus.NOT_IMPLEMENTED] <= 45
    assert len(tuple((ROOT / "fixtures/r5/active").glob("*/*/manifest.yaml"))) >= 84
