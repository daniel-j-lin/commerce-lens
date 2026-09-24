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
PF4_4_IDS = (
    "FX-R5-R4-018A",
    "FX-R5-R4-019A",
    "FX-R5-R4-020A",
    "FX-R5-R4-021A",
    "FX-R5-R4-022A",
    "FX-R5-R4-024A",
    "FX-R5-R4-025A",
    "FX-R5-R4-027A",
    "FX-R5-R4-028A",
    "FX-R5-CHAIN-001A",
)


def _case_dir(fixture_id: str) -> Path:
    family = fixture_id.split("-")[2]
    return ROOT / "fixtures/r5/active" / family / fixture_id


@pytest.fixture(scope="module")
def pf4_4_state():
    registry = build_r5_pf4_adapter_registry()
    actuals, results = {}, {}
    for fixture_id in PF4_4_IDS:
        fixture = load_r5_manifest(_case_dir(fixture_id))
        producer = registry.require(fixture.manifest.execution.adapter_id).producer
        assert producer is not None
        actual = producer(fixture)
        actuals[fixture_id] = actual
        results[fixture_id] = compare_fixture(fixture, actual)
    return actuals, results


def test_exact_pf4_4_set_passes_exact_comparison(pf4_4_state) -> None:
    _, results = pf4_4_state
    assert tuple(results) == PF4_4_IDS
    for fixture_id, result in results.items():
        assert result.status is HarnessResultStatus.PASS, (fixture_id, result.mismatches)


def test_hostile_actuals_preserve_exact_validation_or_integrity_layer(pf4_4_state) -> None:
    actuals = pf4_4_state[0]
    expected = {
        "FX-R5-R4-018A": "baseline_product_revenue_sum",
        "FX-R5-R4-019A": "R4ArtifactIntegrityError",
        "FX-R5-R4-020A": "R4ArtifactIntegrityError",
        "FX-R5-R4-021A": "component_sum",
        "FX-R5-R4-022A": "exact_zero_reconciliation",
        "FX-R5-R4-024A": "complete_product_universe",
        "FX-R5-R4-025A": "R4ArtifactIntegrityError",
        "FX-R5-R4-027A": "method_version_binding",
    }
    for fixture_id, check in expected.items():
        actual = actuals[fixture_id]
        assert actual.material_path[-1].stage.value == "validation"
        assert actual.material_path[-1].reachability.value == "blocked"
        assert actual.trace_integrity_state == {
            "failure_layer": "RESULT_VALIDATION_OR_INTEGRITY",
            "controlling_validation_check": check,
        }


def test_runtime_dependency_loss_occurs_only_after_eligibility(pf4_4_state) -> None:
    actual = pf4_4_state[0]["FX-R5-R4-028A"]
    assert actual.material_path[0].outcome == "eligible"
    assert actual.material_path[1].reachability.value == "blocked"
    assert actual.material_path[1].outcome == "R4ExecutionError"
    assert actual.material_path[2].reachability.value == "not_reached"
    assert actual.trace_integrity_state == {"failure_layer": "EXECUTION"}


def test_independent_scalar_chain_survives_r4_rejection(pf4_4_state) -> None:
    actual = pf4_4_state[0]["FX-R5-CHAIN-001A"]
    scalar, r4_execution, r4_validation = actual.material_path
    assert scalar.chain_id == "scalar"
    assert scalar.outcome == {
        "metric_ref": "revenue",
        "value": "200.00",
        "authority_unchanged": True,
    }
    assert r4_execution.chain_id == r4_validation.chain_id == "r4"
    assert r4_validation.reachability.value == "blocked"
    assert actual.chain_dispositions == {
        "scalar": "revenue_valid",
        "r4": "r4_withheld",
    }


def test_pf4_4_inventory_gate() -> None:
    inventory = load_r5_inventory(ROOT)
    statuses = Counter(item.implementation_status for item in inventory.active.entries)
    assert statuses[ImplementationStatus.EXECUTABLE] >= 104
    assert statuses[ImplementationStatus.DEPENDENCY_BLOCKED] == 1
    assert statuses[ImplementationStatus.NOT_IMPLEMENTED] <= 24
    assert len(tuple((ROOT / "fixtures/r5/active").glob("*/*/manifest.yaml"))) >= 105
