from __future__ import annotations

import json
from pathlib import Path

from commerce_lens.fixture_runner.r5_adapters import AdapterRegistration, AdapterRegistry
from commerce_lens.fixture_runner.r5_inventory import ImplementationStatus, load_r5_inventory
from commerce_lens.fixture_runner.r5_manifest import ActualProjection, ExecutionMode, load_r5_manifest
from commerce_lens.fixture_runner.r5_result import CapabilityStatus, HarnessResultStatus
from commerce_lens.fixture_runner.r5_runner import run_fixture, run_suite
from tests.fixture_runner.r5_test_support import (
    fixed_actual,
    manifest_payload,
    mismatched_actual,
    registration,
    write_case,
)


ROOT = Path(__file__).resolve().parents[2]


def test_available_independent_subject_exact_match_passes(tmp_path) -> None:
    fixture = load_r5_manifest(write_case(tmp_path))
    registry = AdapterRegistry()
    registry.register(registration("dummy_exact", fixed_actual, "tests.fixed_actual"))
    result = run_fixture(fixture, registry)
    assert result.status is HarnessResultStatus.PASS
    assert result.capability_status is CapabilityStatus.AVAILABLE
    assert result.mismatches == ()


def test_available_subject_mismatch_is_non_conforming(tmp_path) -> None:
    payload = manifest_payload(adapter_id="dummy_mismatch")
    fixture = load_r5_manifest(write_case(tmp_path, payload))
    registry = AdapterRegistry()
    registry.register(registration("dummy_mismatch", mismatched_actual, "tests.mismatched_actual"))
    result = run_fixture(fixture, registry)
    assert result.status is HarnessResultStatus.NON_CONFORMING
    assert {item.field for item in result.mismatches} >= {"final_disposition", "material_path"}


def test_unavailable_subject_is_dependency_blocked_and_cannot_self_certify(tmp_path) -> None:
    payload = manifest_payload(adapter_id="dummy_unavailable")
    fixture = load_r5_manifest(write_case(tmp_path, payload))
    registry = AdapterRegistry()
    registry.register(
        AdapterRegistration(
            adapter_id="dummy_unavailable",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="pf0_dummy_subject",
            capability_version="1",
            actual_output_producer="tests.unavailable",
            producer=None,
        )
    )
    result = run_fixture(fixture, registry)
    assert result.status is HarnessResultStatus.DEPENDENCY_BLOCKED
    assert result.actual_final_disposition is None
    assert result.status is not HarnessResultStatus.PASS


def test_unknown_adapter_is_fixture_invalid(tmp_path) -> None:
    fixture = load_r5_manifest(write_case(tmp_path))
    result = run_fixture(fixture, AdapterRegistry())
    assert result.status is HarnessResultStatus.FIXTURE_INVALID
    assert "unknown adapter" in result.mismatches[0].actual


def test_available_subject_exception_is_not_dependency_blocked(tmp_path) -> None:
    payload = manifest_payload(adapter_id="dummy_raises")
    fixture = load_r5_manifest(write_case(tmp_path, payload))

    def raises(_fixture):
        raise RuntimeError("controlled failure")

    registry = AdapterRegistry()
    registry.register(registration("dummy_raises", raises, "tests.raises"))
    result = run_fixture(fixture, registry)
    assert result.status is HarnessResultStatus.NON_CONFORMING
    assert result.capability_status is CapabilityStatus.EXECUTION_FAILED


def test_actual_output_producer_binding_is_verified(tmp_path) -> None:
    fixture = load_r5_manifest(write_case(tmp_path))
    registry = AdapterRegistry()
    registry.register(registration("dummy_exact", fixed_actual, "different.producer"))
    result = run_fixture(fixture, registry)
    assert result.status is HarnessResultStatus.NON_CONFORMING
    assert result.mismatches[0].field == "actual_output_producer"


def test_json_and_text_are_derived_from_same_result(tmp_path) -> None:
    fixture = load_r5_manifest(write_case(tmp_path))
    registry = AdapterRegistry()
    registry.register(registration("dummy_exact", fixed_actual, "tests.fixed_actual"))
    result = run_fixture(fixture, registry)
    decoded = json.loads(result.to_json())
    assert decoded == result.model_dump(mode="json")
    text = result.to_text()
    assert f"fixture: {decoded['fixture_id']}" in text
    assert f"result: {decoded['status']}" in text
    assert "score" not in decoded and "percentage" not in decoded


def test_partial_independent_chains_compare_separately(tmp_path) -> None:
    payload = manifest_payload(adapter_id="dummy_chains")
    payload["expected"]["material_path"] = [
        {"stage": "validation", "chain_id": "revenue_chain", "reachability": "reached", "outcome": "valid"},
        {
            "stage": "validation", "chain_id": "r4_chain", "reachability": "blocked", "outcome": "failed",
            "controlling_reason": "trace incomplete", "authority_ref": "R5 §33",
        },
    ]
    payload["expected"]["chain_dispositions"] = {
        "revenue_chain": "renderable", "r4_chain": "withheld"
    }
    payload["expected"]["expectation_kind"] = "negative"
    payload["expected"]["first_controlling_blocker"] = {
        "blocker_id": "r4_trace", "stage": "validation", "chain_id": "r4_chain",
        "reason": "trace incomplete", "authority_ref": "R5 §33",
    }
    payload["expected"]["final_disposition"] = "partial_material_result"
    fixture = load_r5_manifest(write_case(tmp_path, payload))

    def chains(_fixture):
        return ActualProjection.model_validate(
            {
                "material_path": payload["expected"]["material_path"],
                "chain_dispositions": payload["expected"]["chain_dispositions"],
                "first_controlling_blocker": payload["expected"]["first_controlling_blocker"],
                "final_disposition": "partial_material_result",
                "actual_output_producer": "tests.chains",
            }
        )

    registry = AdapterRegistry()
    registry.register(registration("dummy_chains", chains, "tests.chains"))
    result = run_fixture(fixture, registry)
    assert result.status is HarnessResultStatus.PASS
    assert result.expected_reached_stages == ("revenue_chain:validation", "r4_chain:validation")


def test_precedence_compares_exact_blocker_without_inference(tmp_path) -> None:
    payload = manifest_payload(adapter_id="dummy_prec")
    payload["expected"]["expectation_kind"] = "precedence"
    payload["expected"]["material_path"] = [
        {
            "stage": "evidence_admissibility", "reachability": "blocked", "outcome": "inadmissible",
            "controlling_reason": "evidence inadmissible", "authority_ref": "R5 §34",
        },
        {"stage": "analytical_outcome", "reachability": "not_reached", "not_reached_due_to": "evidence_admissibility"},
    ]
    payload["expected"]["first_controlling_blocker"] = {
        "blocker_id": "evidence", "stage": "evidence_admissibility", "reason": "evidence inadmissible",
        "authority_ref": "R5 §34",
    }
    payload["expected"]["final_disposition"] = "blocked"
    fixture = load_r5_manifest(write_case(tmp_path, payload))

    def wrong_blocker(_fixture):
        return ActualProjection.model_validate(
            {
                "material_path": [
                    {
                        "stage": "validation", "reachability": "blocked", "outcome": "failed",
                        "controlling_reason": "later validation", "authority_ref": "test",
                    }
                ],
                "first_controlling_blocker": {
                    "blocker_id": "validation", "stage": "validation", "reason": "later validation",
                    "authority_ref": "test",
                },
                "final_disposition": "blocked",
                "actual_output_producer": "tests.wrong_blocker",
            }
        )

    registry = AdapterRegistry()
    registry.register(registration("dummy_prec", wrong_blocker, "tests.wrong_blocker"))
    result = run_fixture(fixture, registry)
    assert result.status is HarnessResultStatus.NON_CONFORMING
    assert "first_controlling_blocker" in {item.field for item in result.mismatches}


def test_empty_physical_tranche_reports_counts_without_scoring(tmp_path) -> None:
    (tmp_path / "active").mkdir()
    report = run_suite(tmp_path, load_r5_inventory(ROOT), AdapterRegistry())
    assert report.semantic_active == 129
    assert report.semantic_deferred == 25
    assert report.physical_implemented == report.executable == 0
    assert report.results == ()
    payload = json.loads(report.to_json())
    assert "score" not in payload and "percentage" not in payload


def test_physical_ready_bundle_is_counted_but_not_executed(tmp_path) -> None:
    inventory = load_r5_inventory(ROOT)
    entries = tuple(
        item.model_copy(update={"implementation_status": ImplementationStatus.PHYSICAL_READY})
        if item.fixture_id == "FX-R5-EVID-001A"
        else item
        for item in inventory.active.entries
    )
    inventory = inventory.model_copy(
        update={"active": inventory.active.model_copy(update={"entries": entries})}
    )
    write_case(tmp_path)

    def must_not_run(_fixture):
        raise AssertionError("PHYSICAL_READY producer must not execute")

    registry = AdapterRegistry()
    registry.register(registration("dummy_exact", must_not_run, "tests.must_not_run"))
    report = run_suite(tmp_path, inventory, registry)

    assert report.physical_implemented == 1
    assert report.executable == 0
    assert report.results == ()
