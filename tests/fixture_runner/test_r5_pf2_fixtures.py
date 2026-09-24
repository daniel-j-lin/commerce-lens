from __future__ import annotations

import inspect
from dataclasses import replace
from pathlib import Path

import pytest

from commerce_lens.fixture_runner.r5_comparator import compare_fixture
from commerce_lens.fixture_runner.r5_discovery import discover_r5_fixtures
from commerce_lens.fixture_runner.r5_inventory import ImplementationStatus, load_r5_inventory
from commerce_lens.fixture_runner.r5_pf2_adapters import (
    _RetainedStateObservation,
    _classify_artifact_integrity,
    _classify_completion_integrity,
    build_r5_pf2_adapter_registry,
)
from commerce_lens.fixture_runner.r5_result import HarnessResultStatus
from commerce_lens.fixture_runner.r5_runner import run_fixture, run_suite


ROOT = Path(__file__).resolve().parents[2]
R5_ROOT = ROOT / "fixtures/r5"
PF1_IDS = {
    "FX-R5-EVID-023A", "FX-R5-EVID-010A", "FX-R5-EVID-018A", "FX-R5-CLAIM-001A",
    "FX-R5-LANG-014A", "FX-R5-PROV-002A", "FX-R5-PREC-003A",
}
PF2_IDS = {
    "FX-R5-EVID-002A", "FX-R5-EVID-003A", "FX-R5-EVID-006A", "FX-R5-EVID-007A",
    "FX-R5-EVID-008A", "FX-R5-EVID-011A", "FX-R5-EVID-012A", "FX-R5-EVID-013A",
    "FX-R5-EVID-017A", "FX-R5-ADMIT-001A", "FX-R5-DIAG-001A", "FX-R5-DIAG-011A",
    "FX-R5-DIAG-012A", "FX-R5-CLAIM-002A", "FX-R5-CLAIM-006A",
    "FX-R5-VERSION-001A", "FX-R5-VERSION-004A", "FX-R5-VERSION-005A", "FX-R5-VERSION-006A",
    "FX-R5-PROV-001A", "FX-R5-PROV-003A", "FX-R5-PROV-004A", "FX-R5-PROV-005A",
    "FX-R5-PROV-008A", "FX-R5-PROV-009A",
}
TRANSFERRED_CLASS_C_IDS = {"FX-R5-CLAIM-004A", "FX-R5-PREC-002A"}
PF3_IDS = {
    "FX-R5-ADMIT-003A",
    "FX-R5-ALT-006A",
    "FX-R5-DIAG-003A",
    "FX-R5-NARROW-001A",
    "FX-R5-CLAIM-003A",
    "FX-R5-CLAIM-004A",
    "FX-R5-CLAIM-005A",
    "FX-R5-CAUSE-001A",
    "FX-R5-CAUSE-002A",
    "FX-R5-CAUSE-003A",
    "FX-R5-CAUSE-004A",
    "FX-R5-CAUSE-005A",
    "FX-R5-CAUSE-006A",
    "FX-R5-VERSION-007A",
    "FX-R5-VERSION-008A",
    "FX-R5-VERSION-009A",
    "FX-R5-VERSION-010A",
    "FX-R5-PROV-006A",
    "FX-R5-PROV-007A",
    "FX-R5-CHAIN-002A",
    "FX-R5-PREC-002A",
    "FX-R5-PREC-004A",
    "FX-R5-PREC-005A",
    "FX-R5-LANG-001A",
    "FX-R5-LANG-002A",
    "FX-R5-LANG-003A",
    "FX-R5-LANG-004A",
    "FX-R5-LANG-005A",
    "FX-R5-LANG-006A",
    "FX-R5-LANG-007A",
    "FX-R5-LANG-008A",
    "FX-R5-LANG-009A",
    "FX-R5-LANG-010A",
    "FX-R5-LANG-011A",
    "FX-R5-LANG-015A",
    "FX-R5-LANG-016A",
    "FX-R5-LANG-017A",
}
PF4_1_IDS = {
    "FX-R5-R4-001A", "FX-R5-R4-002A", "FX-R5-R4-003A", "FX-R5-R4-004A",
    "FX-R5-R4-005A", "FX-R5-R4-006A", "FX-R5-R4-023A",
}
LEGACY_EXECUTABLE_IDS = PF1_IDS | PF2_IDS
EXCLUDED = {
    "FX-R5-EVID-001A", "FX-R5-EVID-004A", "FX-R5-EVID-005A", "FX-R5-EVID-009A",
    "FX-R5-EVID-014A", "FX-R5-EVID-015A", "FX-R5-EVID-016A", "FX-R5-EVID-019A",
    "FX-R5-EVID-020A", "FX-R5-EVID-021A", "FX-R5-EVID-022A",
}


@pytest.fixture(scope="module")
def pf2_state():
    inventory = load_r5_inventory(ROOT)
    # PF1/PF2 regression uses the pre-PF3/PF4 registry; keep later bundles
    # physical but out of the legacy executable tranche.
    inventory = inventory.model_copy(
        update={
            "active": inventory.active.model_copy(
                update={
                    "entries": tuple(
                        entry.model_copy(
                            update={
                                "implementation_status": ImplementationStatus.PHYSICAL_READY,
                                "executable": False,
                            }
                        )
                        if entry.fixture_id not in LEGACY_EXECUTABLE_IDS
                        and entry.implementation_status is ImplementationStatus.EXECUTABLE
                        else entry
                        for entry in inventory.active.entries
                    )
                }
            )
        }
    )
    fixtures = discover_r5_fixtures(R5_ROOT, inventory)
    registry = build_r5_pf2_adapter_registry()
    report = run_suite(R5_ROOT, inventory, registry)
    return inventory, fixtures, registry, report


def _result(report, fixture_id):
    return next(item for item in report.results if item.fixture_id == fixture_id)


def test_exact_pf2_allowlist_and_combined_physical_inventory(pf2_state) -> None:
    inventory, fixtures, _, _ = pf2_state
    physical = {item.manifest.fixture_id for item in fixtures}
    assert len(PF2_IDS) == 25
    assert (PF1_IDS | PF2_IDS | TRANSFERRED_CLASS_C_IDS | PF3_IDS | PF4_1_IDS).issubset(
        physical
    )
    assert len(physical) >= 76
    assert not physical.intersection(EXCLUDED)
    assert not physical.intersection(item.deferred_id for item in inventory.deferred.entries)


def test_inventory_totals_and_excluded_cases(pf2_state) -> None:
    inventory, _, _, report = pf2_state
    statuses = {item.fixture_id: item.implementation_status for item in inventory.active.entries}
    assert sum(value is ImplementationStatus.EXECUTABLE for value in statuses.values()) == 31
    assert sum(value is ImplementationStatus.DEPENDENCY_BLOCKED for value in statuses.values()) == 1
    assert sum(value is ImplementationStatus.PHYSICAL_READY for value in statuses.values()) >= 44
    assert sum(value is ImplementationStatus.NOT_IMPLEMENTED for value in statuses.values()) <= 53
    assert statuses["FX-R5-PREC-003A"] is ImplementationStatus.DEPENDENCY_BLOCKED
    assert all(
        statuses[item] is ImplementationStatus.PHYSICAL_READY
        for item in TRANSFERRED_CLASS_C_IDS | PF3_IDS | PF4_1_IDS
    )
    assert all(statuses[item] is ImplementationStatus.NOT_IMPLEMENTED for item in EXCLUDED)
    assert report.physical_implemented >= 76
    assert (report.executable, report.dependency_blocked) == (31, 1)
    assert report.passed == 31
    assert not TRANSFERRED_CLASS_C_IDS.intersection(item.fixture_id for item in report.results)


def test_owner_amendment_records_exact_pf2_and_pf3_classification() -> None:
    readme = (R5_ROOT / "README.md").read_text(encoding="utf-8")
    project_state = (ROOT / "PROJECT_STATE.md").read_text(encoding="utf-8")
    assert "PF2 remaining Class A tranche: 25" in project_state
    assert "PF3 controlled Class C tranche: 37" in project_state
    assert "FX-R5-CLAIM-004A" in readme and "Class A → Class C" in readme
    assert "FX-R5-PREC-002A" in readme and "Class A → Class C" in readme


@pytest.mark.parametrize("fixture_id", sorted(PF2_IDS))
def test_every_pf2_fixture_uses_available_truthful_producer_and_passes(pf2_state, fixture_id) -> None:
    _, fixtures, registry, report = pf2_state
    fixture = next(item for item in fixtures if item.manifest.fixture_id == fixture_id)
    registration = registry.require(fixture.manifest.execution.adapter_id)
    result = _result(report, fixture_id)
    assert registration.available
    assert registration.execution_mode is fixture.manifest.execution.mode
    assert registration.capability_name == fixture.manifest.execution.required_capability
    assert registration.capability_version == fixture.manifest.execution.required_capability_version
    assert result.status is HarnessResultStatus.PASS
    assert result.actual_final_disposition == result.expected_final_disposition
    assert result.actual_first_blocker == result.expected_first_blocker


def test_pf2_producers_do_not_read_expected_or_encode_fixture_ids(pf2_state) -> None:
    _, fixtures, registry, _ = pf2_state
    module_source = inspect.getsource(__import__("commerce_lens.fixture_runner.r5_pf2_adapters", fromlist=["*"]))
    assert "manifest.expected" not in module_source
    assert "fixture.manifest.expected" not in module_source
    assert not any(fixture_id in module_source for fixture_id in PF2_IDS)
    for fixture in fixtures:
        if fixture.manifest.fixture_id not in PF2_IDS:
            continue
        registration = registry.require(fixture.manifest.execution.adapter_id)
        source = inspect.getsource(registration.producer)
        assert "manifest.expected" not in source
        assert fixture.manifest.fixture_id not in source


@pytest.mark.parametrize(
    ("fixture_id", "blocker"),
    [
        ("FX-R5-EVID-002A", "available_evidence_mapping"),
        ("FX-R5-EVID-003A", "evidence_admissibility"),
        ("FX-R5-EVID-006A", "temporal_alignment"),
        ("FX-R5-EVID-007A", "population_alignment"),
        ("FX-R5-EVID-008A", "metric_compatibility"),
        ("FX-R5-EVID-011A", "currency_compatibility"),
        ("FX-R5-EVID-012A", "coverage_completeness"),
        ("FX-R5-EVID-013A", "coverage_completeness"),
        ("FX-R5-EVID-017A", "provenance"),
    ],
)
def test_evid_family_observes_exact_production_blocker(pf2_state, fixture_id, blocker) -> None:
    result = _result(pf2_state[3], fixture_id)
    assert result.actual_first_blocker["blocker_id"] == blocker


def test_admit_family_denies_diagnostic_intended_use(pf2_state) -> None:
    result = _result(pf2_state[3], "FX-R5-ADMIT-001A")
    assert result.actual_first_blocker["reason"] == "unsupported_claim_type_for_p6_001"


def test_diag_family_preserves_result_level_and_claim_refusal_boundaries(pf2_state) -> None:
    report = pf2_state[3]
    assert _result(report, "FX-R5-DIAG-001A").actual_first_blocker == "NONE"
    assert _result(report, "FX-R5-DIAG-011A").actual_final_disposition == "CLAIM_PROHIBITED"
    assert _result(report, "FX-R5-DIAG-012A").actual_final_disposition.endswith("CAUSAL_AUTHORITY_UNAVAILABLE")


def test_claim_family_requires_authoritative_decision_and_binding(pf2_state) -> None:
    report = pf2_state[3]
    assert _result(report, "FX-R5-CLAIM-002A").actual_first_blocker["stage"] == "claim_decision"
    assert _result(report, "FX-R5-CLAIM-006A").actual_first_blocker["reason"] == "claim_decision_artifact_hash_mismatch"


def test_version_family_uses_current_and_persisted_authority(pf2_state) -> None:
    report = pf2_state[3]
    assert _result(report, "FX-R5-VERSION-001A").actual_first_blocker == "NONE"
    assert _result(report, "FX-R5-VERSION-004A").actual_first_blocker["reason"] == "metric_definition_mismatch"
    assert _result(report, "FX-R5-VERSION-005A").actual_first_blocker["reason"] == "policy_version_mismatch"
    assert _result(report, "FX-R5-VERSION-006A").actual_first_blocker == "NONE"


def test_prov_family_distinguishes_integrity_states(pf2_state) -> None:
    report = pf2_state[3]
    assert _result(report, "FX-R5-PROV-001A").actual_first_blocker == "NONE"
    assert _result(report, "FX-R5-PROV-003A").actual_first_blocker["reason"] == "required_artifact_missing"
    assert _result(report, "FX-R5-PROV-004A").actual_first_blocker["reason"] == "artifact_fingerprint_mismatch"
    assert _result(report, "FX-R5-PROV-005A").actual_first_blocker["reason"] == "missing_persisted_evidence_authority"
    assert _result(report, "FX-R5-PROV-008A").actual_first_blocker["reason"] == "complete_marker_missing"
    assert _result(report, "FX-R5-PROV-009A").actual_first_blocker["reason"] == "complete_marker_mismatch"


def _neutral_retained_observation() -> _RetainedStateObservation:
    return _RetainedStateObservation(
        checks={"artifact_hashes": False, "complete_marker": True},
        errors=("artifact missing or hash mismatch",),
        retention_status="retained_incomplete",
        target_artifact_id="art_neutral",
        target_exists=False,
        retained_target_fingerprint="a" * 64,
        actual_target_fingerprint=None,
        marker_exists=True,
        marker_content="m" * 64,
        manifest_fingerprint="m" * 64,
        metric_registry_version="metric_registry_mvp_v3",
        policy_versions=("p8_001_v1",),
    )


def test_artifact_classification_uses_observed_presence_and_hash_only() -> None:
    absent = _classify_artifact_integrity(_neutral_retained_observation())
    mismatched = _classify_artifact_integrity(
        replace(
            _neutral_retained_observation(),
            target_exists=True,
            actual_target_fingerprint="b" * 64,
        )
    )
    assert absent.reason == "required_artifact_missing"
    assert mismatched.reason == "artifact_fingerprint_mismatch"
    assert "scenario" not in inspect.getsource(_classify_artifact_integrity)


def test_completion_classification_uses_observed_marker_state_only() -> None:
    base = replace(
        _neutral_retained_observation(),
        checks={"artifact_hashes": True, "complete_marker": False},
        errors=("complete marker missing or mismatched",),
    )
    absent = _classify_completion_integrity(
        replace(base, marker_exists=False, marker_content=None)
    )
    mismatched = _classify_completion_integrity(
        replace(base, marker_exists=True, marker_content="x" * 64)
    )
    assert absent.reason == "complete_marker_missing"
    assert mismatched.reason == "complete_marker_mismatch"
    assert "scenario" not in inspect.getsource(_classify_completion_integrity)


def test_corrected_prov_producer_attribution_names_verifier_and_observation(pf2_state) -> None:
    _, fixtures, registry, _ = pf2_state
    for fixture_id in {
        "FX-R5-PROV-003A",
        "FX-R5-PROV-004A",
        "FX-R5-PROV-008A",
        "FX-R5-PROV-009A",
    }:
        fixture = next(item for item in fixtures if item.manifest.fixture_id == fixture_id)
        producer = registry.require(fixture.manifest.execution.adapter_id).actual_output_producer
        assert producer.endswith("RetentionStore.verify_run+retained_filesystem_state_observation")


def test_transferred_class_c_bundles_are_physical_but_not_executed(pf2_state) -> None:
    _, fixtures, _, report = pf2_state
    physical = {item.manifest.fixture_id for item in fixtures}
    result_ids = {item.fixture_id for item in report.results}
    assert TRANSFERRED_CLASS_C_IDS.issubset(physical)
    assert TRANSFERRED_CLASS_C_IDS.isdisjoint(result_ids)


def test_representative_post_sut_tamper_is_non_conforming(pf2_state) -> None:
    _, fixtures, registry, _ = pf2_state
    for fixture_id in ("FX-R5-EVID-002A", "FX-R5-CLAIM-002A", "FX-R5-PROV-001A"):
        fixture = next(item for item in fixtures if item.manifest.fixture_id == fixture_id)
        registration = registry.require(fixture.manifest.execution.adapter_id)
        actual = registration.producer(fixture)
        tampered = actual.model_copy(update={"final_disposition": "TAMPERED_AFTER_SUT"})
        assert compare_fixture(fixture, tampered).status is HarnessResultStatus.NON_CONFORMING


def test_repeat_execution_preserves_material_semantics(pf2_state) -> None:
    _, fixtures, registry, _ = pf2_state
    fixture = next(item for item in fixtures if item.manifest.fixture_id == "FX-R5-CLAIM-002A")
    producer = registry.require(fixture.manifest.execution.adapter_id).producer
    first = producer(fixture)
    second = producer(fixture)
    assert first.final_disposition == second.final_disposition
    assert first.first_controlling_blocker == second.first_controlling_blocker
    assert first.material_path == second.material_path


def test_all_pf1_results_remain_approved(pf2_state) -> None:
    report = pf2_state[3]
    for fixture_id in PF1_IDS - {"FX-R5-PREC-003A"}:
        assert _result(report, fixture_id).status is HarnessResultStatus.PASS
    assert _result(report, "FX-R5-PREC-003A").status is HarnessResultStatus.DEPENDENCY_BLOCKED
