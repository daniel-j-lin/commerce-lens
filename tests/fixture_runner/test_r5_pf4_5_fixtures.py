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
PF4_5_IDS = (
    "FX-R5-R4-033A",
    "FX-R5-R4-035A",
    "FX-R5-R4-036A",
    "FX-R5-R4-037A",
)


def _case_dir(fixture_id: str) -> Path:
    return ROOT / "fixtures/r5/active/R4" / fixture_id


@pytest.fixture(scope="module")
def pf4_5_state():
    registry = build_r5_pf4_adapter_registry()
    actuals, results = {}, {}
    for fixture_id in PF4_5_IDS:
        fixture = load_r5_manifest(_case_dir(fixture_id))
        producer = registry.require(fixture.manifest.execution.adapter_id).producer
        assert producer is not None
        actual = producer(fixture)
        actuals[fixture_id] = actual
        results[fixture_id] = compare_fixture(fixture, actual)
    return actuals, results


def test_exact_pf4_5_set_passes_exact_comparison(pf4_5_state) -> None:
    _, results = pf4_5_state
    assert tuple(results) == PF4_5_IDS
    for fixture_id, result in results.items():
        assert result.status is HarnessResultStatus.PASS, (fixture_id, result.mismatches)


def test_repeated_same_evaluator_is_materially_identical(pf4_5_state) -> None:
    actual = pf4_5_state[0]["FX-R5-R4-033A"]
    assert actual.final_disposition == "MATERIAL_OUTPUT_IDENTICAL__CONFORMING"
    assert actual.trace_integrity_state == {
        "failure_layer": None,
        "material_difference_count": 0,
    }


def test_canonical_row_order_does_not_change_authority(pf4_5_state) -> None:
    actual = pf4_5_state[0]["FX-R5-R4-035A"]
    assert actual.final_disposition == "AUTHORITATIVE_RESULT_UNCHANGED"
    assert actual.trace_integrity_state == {
        "material_difference_count": 0,
        "source_row_order_differed": True,
    }


def test_presentation_order_is_non_material(pf4_5_state) -> None:
    actual = pf4_5_state[0]["FX-R5-R4-036A"]
    assert actual.final_disposition == "NON_MATERIAL_ORDER_DIFFERENCE__CONFORMING"
    assert actual.trace_integrity_state == {
        "authoritative_values_unchanged": True,
        "presentation_order_differed": True,
    }


def test_material_mutation_is_method_conformance_failure(pf4_5_state) -> None:
    actual = pf4_5_state[0]["FX-R5-R4-037A"]
    assert actual.final_disposition == "METHOD_OR_EVALUATOR_CONFORMANCE_FAILURE"
    assert actual.trace_integrity_state == {
        "failure_layer": "METHOD_CONFORMANCE",
        "difference_paths": ["r4.reconciliation_difference"],
    }


def test_pf4_final_inventory_and_exclusions() -> None:
    inventory = load_r5_inventory(ROOT)
    statuses = Counter(item.implementation_status for item in inventory.active.entries)
    assert statuses == {
        ImplementationStatus.EXECUTABLE: 108,
        ImplementationStatus.DEPENDENCY_BLOCKED: 1,
        ImplementationStatus.NOT_IMPLEMENTED: 20,
    }
    assert len(tuple((ROOT / "fixtures/r5/active").glob("*/*/manifest.yaml"))) == 109
    entries = {item.fixture_id: item for item in inventory.active.entries}
    assert entries["FX-R5-R4-034A"].implementation_status is ImplementationStatus.NOT_IMPLEMENTED
    assert not _case_dir("FX-R5-R4-034A").exists()
    assert entries["FX-R5-PREC-003A"].implementation_status is ImplementationStatus.DEPENDENCY_BLOCKED
    remaining = {
        item.fixture_id
        for item in inventory.active.entries
        if item.implementation_status is ImplementationStatus.NOT_IMPLEMENTED
    }
    assert len(remaining) == 20
    assert remaining & {item for item in remaining if item.startswith("FX-R5-R4-")} == {
        "FX-R5-R4-034A"
    }
