from __future__ import annotations

import hashlib
import inspect
from collections import Counter
from decimal import Decimal
from pathlib import Path

import pytest

from commerce_lens.fixture_runner.r5_inventory import load_r5_inventory
from commerce_lens.fixture_runner.r5_comparator import compare_fixture
from commerce_lens.fixture_runner.r5_manifest import ExecutionMode, load_r5_manifest
from commerce_lens.fixture_runner.r5_pf4_adapters import (
    PF4_PRESENTATION_ROUNDING_DISPOSITION,
    PF4_R4_ACTUAL_OUTPUT_PRODUCER,
    build_r5_pf4_adapter_registry,
)
from commerce_lens.fixture_runner.r5_result import HarnessResultStatus


ROOT = Path(__file__).resolve().parents[2]
R5_ROOT = ROOT / "fixtures/r5"
R4_ROOT = R5_ROOT / "active/R4"
PF4_1_IDS = (
    "FX-R5-R4-001A",
    "FX-R5-R4-002A",
    "FX-R5-R4-003A",
    "FX-R5-R4-004A",
    "FX-R5-R4-005A",
    "FX-R5-R4-006A",
    "FX-R5-R4-023A",
)
ORDINARY_IDS = PF4_1_IDS[:-1]
PRESENTATION_ADAPTER_ID = (
    "production_r4_material_projection_with_presentation_observation"
)
FROZEN_ANCHORS = {
    "FX-R5-R4-001A": ("140.00", "140.00", "0.00", "0", "0", "0.00"),
    "FX-R5-R4-002A": ("100.00", "125.00", "25.00", "25.00", "0", "0.00"),
    "FX-R5-R4-003A": ("125.00", "100.00", "-25.00", "0", "-25.00", "0.00"),
    "FX-R5-R4-004A": ("100.00", "130.00", "30.00", "0", "0", "30.00"),
    "FX-R5-R4-005A": ("200.00", "240.00", "40.00", "100.00", "-60.00", "0.00"),
    "FX-R5-R4-006A": ("150.00", "150.00", "0.00", "70.00", "-50.00", "-20.00"),
    "FX-R5-R4-023A": ("10.00", "10.80", "0.80", "0.40", "0", "0.40"),
}


@pytest.fixture(scope="module")
def pf4_1_state():
    registry = build_r5_pf4_adapter_registry()
    fixtures = {}
    actuals = {}
    results = {}
    for fixture_id in PF4_1_IDS:
        case = R4_ROOT / fixture_id
        fixture = load_r5_manifest(case)
        registration = registry.require(fixture.manifest.execution.adapter_id)
        assert registration.producer is not None
        fixtures[fixture_id] = fixture
        actuals[fixture_id] = registration.producer(fixture)
        results[fixture_id] = compare_fixture(fixture, actuals[fixture_id])
    return registry, fixtures, actuals, results


def _material(actual) -> dict:
    return next(item.outcome for item in actual.material_path if item.stage.value == "validation")


def _rows(actual) -> dict[str, dict]:
    return {row["product_id"]: row for row in _material(actual)["trace_rows"]}


def _contains_float(value) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_float(item) for item in value)
    return False


def test_exact_seven_pf4_1_bundles_remain_physical_and_csv_only(pf4_1_state) -> None:
    _, fixtures, _, _ = pf4_1_state
    physical = {path.name for path in R4_ROOT.iterdir() if path.is_dir()}
    assert set(PF4_1_IDS).issubset(physical)
    assert set(fixtures) == set(PF4_1_IDS)
    for fixture in fixtures.values():
        assert len(fixture.manifest.inputs) == 1
        assert fixture.manifest.inputs[0].role == "orders"
        assert fixture.manifest.inputs[0].media_type == "text/csv"
        assert fixture.manifest.inputs[0].sha256 == hashlib.sha256(
            fixture.input_paths[0].read_bytes()
        ).hexdigest()


def test_all_seven_use_their_approved_production_adapter_and_pass_exact_comparison(
    pf4_1_state,
) -> None:
    registry, fixtures, actuals, results = pf4_1_state
    for fixture_id in PF4_1_IDS:
        fixture = fixtures[fixture_id]
        registration = registry.require(fixture.manifest.execution.adapter_id)
        result = results[fixture_id]
        assert fixture.manifest.execution.mode is ExecutionMode.APPLICATION_SERVICE
        expected_adapter = (
            PRESENTATION_ADAPTER_ID
            if fixture_id == "FX-R5-R4-023A"
            else "production_r4_material_projection"
        )
        assert fixture.manifest.execution.adapter_id == expected_adapter
        assert registration.actual_output_producer == PF4_R4_ACTUAL_OUTPUT_PRODUCER
        assert actuals[fixture_id].actual_output_producer == PF4_R4_ACTUAL_OUTPUT_PRODUCER
        assert result.status is HarnessResultStatus.PASS, result.mismatches
        assert result.mismatches == ()


def test_six_ordinary_adapters_have_no_presentation_obligation(pf4_1_state) -> None:
    _, fixtures, actuals, _ = pf4_1_state
    for fixture_id in ORDINARY_IDS:
        actual = actuals[fixture_id]
        assert "whole_unit_presentation" not in actual.trace_integrity_state
        assert actual.final_disposition == "VALIDATED_R4_MECHANICAL_RESULT"
        assert (
            "whole_unit_presentation"
            not in fixtures[fixture_id].manifest.expected.trace_integrity_expectation
        )


def test_adapter_selection_not_r4_023_identity_controls_presentation(pf4_1_state) -> None:
    registry, fixtures, presentation_actuals, _ = pf4_1_state
    fixture = fixtures["FX-R5-R4-023A"]
    ordinary_producer = registry.require("production_r4_material_projection").producer
    assert ordinary_producer is not None
    ordinary_actual = ordinary_producer(fixture)
    presentation_actual = presentation_actuals["FX-R5-R4-023A"]

    assert "whole_unit_presentation" not in ordinary_actual.trace_integrity_state
    assert ordinary_actual.final_disposition == "VALIDATED_R4_MECHANICAL_RESULT"
    assert "whole_unit_presentation" in presentation_actual.trace_integrity_state
    assert presentation_actual.final_disposition == PF4_PRESENTATION_ROUNDING_DISPOSITION
    assert _material(ordinary_actual) == _material(presentation_actual)


@pytest.mark.parametrize("fixture_id", PF4_1_IDS)
def test_each_fixture_matches_its_frozen_numerical_anchor(pf4_1_state, fixture_id) -> None:
    _, fixtures, actuals, _ = pf4_1_state
    material = _material(actuals[fixture_id])
    expected = fixtures[fixture_id].manifest.expected.material_path[-1].outcome
    baseline, comparison, change, entry, exit_value, continuing = FROZEN_ANCHORS[fixture_id]
    assert (
        material["baseline_revenue"],
        material["comparison_revenue"],
        material["observed_revenue_change"],
        material["entry_component"],
        material["exit_component"],
        material["continuing_component"],
    ) == (baseline, comparison, change, entry, exit_value, continuing)
    assert material == expected
    assert material["component_sum"] == change
    assert material["reconciliation_difference"] == "0.00"
    assert material["authority_bindings_validated"] is True
    assert material["validation_status"] == "passed"


def test_r4_001_exact_reconciliation_retains_opposing_product_contributions(pf4_1_state) -> None:
    material = _material(pf4_1_state[2]["FX-R5-R4-001A"])
    rows = _rows(pf4_1_state[2]["FX-R5-R4-001A"])
    assert material["observed_revenue_change"] == material["component_sum"] == "0.00"
    assert rows["p_a"]["contribution"] == "20.00"
    assert rows["p_b"]["contribution"] == "-20.00"
    assert {row["classification"] for row in rows.values()} == {"continuing"}


def test_r4_002_entry_only_uses_genuine_baseline_absence(pf4_1_state) -> None:
    actual = pf4_1_state[2]["FX-R5-R4-002A"]
    material, rows = _material(actual), _rows(actual)
    assert material["entry_component"] == "25.00"
    assert material["exit_component"] == "0"
    assert material["continuing_component"] == "0.00"
    assert rows["p_b"]["baseline_present"] is False
    assert rows["p_b"]["comparison_present"] is True
    assert rows["p_b"]["classification"] == "comparison_only"


def test_r4_003_exit_only_uses_genuine_comparison_absence(pf4_1_state) -> None:
    actual = pf4_1_state[2]["FX-R5-R4-003A"]
    material, rows = _material(actual), _rows(actual)
    assert material["entry_component"] == "0"
    assert material["exit_component"] == "-25.00"
    assert material["continuing_component"] == "0.00"
    assert rows["p_b"]["baseline_present"] is True
    assert rows["p_b"]["comparison_present"] is False
    assert rows["p_b"]["classification"] == "baseline_only"


def test_r4_004_continuing_only_uses_the_same_product_identity(pf4_1_state) -> None:
    actual = pf4_1_state[2]["FX-R5-R4-004A"]
    material, rows = _material(actual), _rows(actual)
    assert material["entry_component"] == material["exit_component"] == "0"
    assert material["continuing_component"] == "30.00"
    assert tuple(rows) == ("p_a",)
    assert rows["p_a"]["classification"] == "continuing"
    assert "driver" not in actual.final_disposition.lower()


def test_r4_005_complete_union_has_one_exact_assignment_per_product(pf4_1_state) -> None:
    actual = pf4_1_state[2]["FX-R5-R4-005A"]
    material, rows = _material(actual), _rows(actual)
    assert tuple(rows) == ("p_a", "p_b", "p_c", "p_d")
    assert Counter(row["classification"] for row in rows.values()) == {
        "continuing": 2,
        "baseline_only": 1,
        "comparison_only": 1,
    }
    assert material["product_count"] == 4
    assert material["component_sum"] == material["observed_revenue_change"] == "40.00"


def test_r4_006_zero_net_retains_all_nonzero_offsetting_components(pf4_1_state) -> None:
    actual = pf4_1_state[2]["FX-R5-R4-006A"]
    material, rows = _material(actual), _rows(actual)
    assert material["observed_revenue_change"] == "0.00"
    assert (
        material["entry_component"],
        material["exit_component"],
        material["continuing_component"],
    ) == ("70.00", "-50.00", "-20.00")
    assert len(rows) == 3
    assert all(Decimal(row["contribution"]) != 0 for row in rows.values())


def test_r4_023_exact_authority_precedes_non_additive_whole_unit_display(pf4_1_state) -> None:
    actual = pf4_1_state[2]["FX-R5-R4-023A"]
    material = _material(actual)
    exact_components = (
        Decimal(material["entry_component"])
        + Decimal(material["exit_component"])
        + Decimal(material["continuing_component"])
    )
    assert exact_components == Decimal("0.80")
    assert exact_components == Decimal(material["observed_revenue_change"])
    assert material["reconciliation_difference"] == "0.00"
    presentation = actual.trace_integrity_state["whole_unit_presentation"]
    assert presentation["entry"] == presentation["continuing"] == "0"
    assert presentation["displayed_component_total"] == "0"
    assert presentation["observed_revenue_change"] == "1"
    assert presentation["appears_non_additive"] is True
    assert presentation["authoritative_values_unchanged"] is True
    assert actual.final_disposition == PF4_PRESENTATION_ROUNDING_DISPOSITION
    assert not _contains_float(actual.model_dump(mode="json"))


def test_all_pf4_1_inventory_entries_remain_executable() -> None:
    inventory = load_r5_inventory(ROOT)
    assert all(
        next(item for item in inventory.active.entries if item.fixture_id == fixture_id).executable
        for fixture_id in PF4_1_IDS
    )


def test_pf4_1_does_not_add_oracle_or_fixture_specific_adapter_logic() -> None:
    from commerce_lens.fixture_runner import r5_pf4_adapters

    source = inspect.getsource(r5_pf4_adapters)
    assert "manifest.expected" not in source
    assert "fixture_id" not in source
    assert not any(fixture_id in source for fixture_id in PF4_1_IDS)
    assert "R4ProductClassification" not in source
    assert "R4Component" not in source
    assert "_product_revenues" not in source
