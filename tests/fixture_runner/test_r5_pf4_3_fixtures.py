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
PF4_3_IDS = (
    "FX-R5-R4-014A",
    "FX-R5-R4-015A",
    "FX-R5-R4-016A",
    "FX-R5-R4-017A",
    "FX-R5-R4-026A",
    "FX-R5-R4-029A",
    "FX-R5-R4-030A",
    "FX-R5-R4-032A",
    "FX-R5-DIAG-002A",
    "FX-R5-VERSION-003A",
    "FX-R5-PREC-001A",
)


def _case_dir(fixture_id: str) -> Path:
    family = fixture_id.split("-")[2]
    return ROOT / "fixtures/r5/active" / family / fixture_id


@pytest.fixture(scope="module")
def pf4_3_state():
    registry = build_r5_pf4_adapter_registry()
    fixtures, actuals, results = {}, {}, {}
    for fixture_id in PF4_3_IDS:
        fixture = load_r5_manifest(_case_dir(fixture_id))
        producer = registry.require(fixture.manifest.execution.adapter_id).producer
        assert producer is not None
        actual = producer(fixture)
        fixtures[fixture_id] = fixture
        actuals[fixture_id] = actual
        results[fixture_id] = compare_fixture(fixture, actual)
    return fixtures, actuals, results


def test_exact_pf4_3_set_passes_exact_comparison(pf4_3_state) -> None:
    fixtures, _, results = pf4_3_state
    assert tuple(fixtures) == PF4_3_IDS
    for fixture_id, result in results.items():
        assert result.status is HarnessResultStatus.PASS, (fixture_id, result.mismatches)


def test_coverage_currency_population_and_method_fail_at_eligibility(pf4_3_state) -> None:
    actuals = pf4_3_state[1]
    expected = {
        "FX-R5-R4-014A": "period_coverage_incomplete",
        "FX-R5-R4-015A": "mixed_currency",
        "FX-R5-R4-016A": "unknown_currency",
        "FX-R5-R4-017A": "population_binding_mismatch",
        "FX-R5-R4-026A": "r4_method_authority_mismatch",
        "FX-R5-VERSION-003A": "r4_method_authority_mismatch",
    }
    for fixture_id, code in expected.items():
        actual = actuals[fixture_id]
        assert actual.material_path[0].reachability.value == "blocked"
        assert actual.material_path[0].outcome == code
        assert actual.material_path[1].reachability.value == "not_reached"
        assert actual.trace_integrity_state["failure_layer"] == "ELIGIBILITY"
    assert actuals["FX-R5-R4-015A"].final_disposition != actuals[
        "FX-R5-R4-016A"
    ].final_disposition


def test_standalone_r4_executes_without_diagnostic_authority(pf4_3_state) -> None:
    actual = pf4_3_state[1]["FX-R5-R4-029A"]
    assert [item.reachability.value for item in actual.material_path] == [
        "reached",
        "reached",
        "reached",
    ]
    assert actual.final_disposition == "R4_MAY_EXECUTE_WITHOUT_DIAGNOSTIC_PROPOSITION"
    assert actual.trace_integrity_state["validation_status"] == "passed"


def test_artificial_diagnostic_authority_is_rejected_by_request_contract(pf4_3_state) -> None:
    actual = pf4_3_state[1]["FX-R5-R4-030A"]
    assert actual.final_disposition == (
        "NON_CONFORMING_ORCHESTRATION__ARTIFICIAL_DIAGNOSTIC_AUTHORITY"
    )
    assert actual.trace_integrity_state == {
        "request_contract_rejected": True,
        "production_r4_entered": False,
    }


def test_diagnostic_missing_profile_and_precedence_remain_fail_closed(pf4_3_state) -> None:
    actuals = pf4_3_state[1]
    for fixture_id in ("FX-R5-R4-032A", "FX-R5-PREC-001A"):
        actual = actuals[fixture_id]
        assert actual.material_path[0].outcome == "diagnostic_r3_authority_unavailable"
        assert actual.material_path[1].reachability.value == "not_reached"
        assert actual.final_disposition == (
            "R4_DIAGNOSTIC_WORKFLOW_NOT_ELIGIBLE__PROFILE_MISSING"
        )


def test_validated_r4_remains_mechanical_not_diagnostic(pf4_3_state) -> None:
    actual = pf4_3_state[1]["FX-R5-DIAG-002A"]
    assert actual.trace_integrity_state["validation_status"] == "passed"
    assert actual.final_disposition == (
        "VALIDATED_R4_MECHANICAL_RESULT_ONLY__NO_DIAGNOSTIC_MEANING"
    )
    assert actual.chain_dispositions == {"main": "mechanical_result_only"}


def test_pf4_3_inventory_floor_remains_satisfied() -> None:
    inventory = load_r5_inventory(ROOT)
    statuses = Counter(item.implementation_status for item in inventory.active.entries)
    assert statuses[ImplementationStatus.EXECUTABLE] >= 94
    assert statuses[ImplementationStatus.DEPENDENCY_BLOCKED] == 1
    assert statuses[ImplementationStatus.NOT_IMPLEMENTED] <= 34
    assert len(tuple((ROOT / "fixtures/r5/active").glob("*/*/manifest.yaml"))) >= 95
