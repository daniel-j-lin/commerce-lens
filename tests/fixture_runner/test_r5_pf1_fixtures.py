from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from commerce_lens.fixture_runner.r5_comparator import compare_fixture
from commerce_lens.fixture_runner.r5_discovery import discover_r5_fixtures
from commerce_lens.fixture_runner.r5_inventory import ImplementationStatus, load_r5_inventory
from commerce_lens.fixture_runner.r5_pf2_adapters import build_r5_pf2_adapter_registry
from commerce_lens.fixture_runner.r5_result import CapabilityStatus, HarnessResultStatus
from commerce_lens.fixture_runner.r5_runner import run_suite


ROOT = Path(__file__).resolve().parents[2]
R5_ROOT = ROOT / "fixtures/r5"
PF1_IDS = (
    "FX-R5-CLAIM-001A",
    "FX-R5-EVID-010A",
    "FX-R5-EVID-018A",
    "FX-R5-EVID-023A",
    "FX-R5-LANG-014A",
    "FX-R5-PREC-003A",
    "FX-R5-PROV-002A",
)
BLOCKED_ID = "FX-R5-PREC-003A"
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
LEGACY_EXECUTABLE_IDS = set(PF1_IDS) | PF2_IDS
EXPECTED_FIRST_BLOCKERS = {
    "FX-R5-EVID-010A": ("currency_compatibility", "data_sufficiency", "canonical.currency.mixed"),
    "FX-R5-EVID-018A": ("required_validation", "validation", "value_mismatch"),
    "FX-R5-CLAIM-001A": (
        "requested_claim_class_restriction",
        "claim_decision",
        "unsupported_claim_type",
    ),
    "FX-R5-PROV-002A": (
        "retained_artifact_integrity",
        "artifact_integrity",
        "retained_artifact_hash_mismatch",
    ),
}


@pytest.fixture(scope="module")
def pf1_state():
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


def test_the_seven_approved_pf1_bundles_remain_present_and_load(pf1_state) -> None:
    inventory, fixtures, _, _ = pf1_state
    discovered = {item.manifest.fixture_id for item in fixtures}
    assert set(PF1_IDS).issubset(discovered)
    physical_dirs = tuple(
        sorted(
            path.name
            for family in (R5_ROOT / "active").iterdir()
            if family.is_dir()
            for path in family.iterdir()
            if path.is_dir()
        )
    )
    assert (set(PF1_IDS) | PF2_IDS | TRANSFERRED_CLASS_C_IDS | PF3_IDS | PF4_1_IDS).issubset(
        physical_dirs
    )
    assert len(physical_dirs) >= 76
    assert len(inventory.active.entries) == 129
    assert len(inventory.deferred.entries) == 25


def test_inventory_preserves_pf1_and_adds_only_the_pf2_allowlist(pf1_state) -> None:
    inventory, _, _, _ = pf1_state
    changed = {
        item.fixture_id: item.implementation_status
        for item in inventory.active.entries
        if item.implementation_status is not ImplementationStatus.NOT_IMPLEMENTED
    }
    assert (set(PF1_IDS) | PF2_IDS).issubset(changed)
    assert changed[BLOCKED_ID] is ImplementationStatus.DEPENDENCY_BLOCKED
    assert all(
        changed[fixture_id] is ImplementationStatus.PHYSICAL_READY
        for fixture_id in TRANSFERRED_CLASS_C_IDS
    )
    assert all(
        changed[fixture_id] is ImplementationStatus.EXECUTABLE
        for fixture_id in LEGACY_EXECUTABLE_IDS - {BLOCKED_ID}
    )
    assert all(
        status is ImplementationStatus.PHYSICAL_READY
        for fixture_id, status in changed.items()
        if fixture_id not in LEGACY_EXECUTABLE_IDS
    )
    assert all(not item.executable for item in inventory.deferred.entries)


@pytest.mark.parametrize("fixture_id", PF1_IDS)
def test_each_pf1_bundle_has_valid_adapter_and_result_taxonomy(pf1_state, fixture_id) -> None:
    _, fixtures, registry, report = pf1_state
    fixture = next(item for item in fixtures if item.manifest.fixture_id == fixture_id)
    registration = registry.require(fixture.manifest.execution.adapter_id)
    result = next(item for item in report.results if item.fixture_id == fixture_id)
    assert registration.execution_mode is fixture.manifest.execution.mode
    assert registration.capability_name == fixture.manifest.execution.required_capability
    assert registration.capability_version == fixture.manifest.execution.required_capability_version
    if fixture_id == BLOCKED_ID:
        assert registration.producer is None
        assert result.status is HarnessResultStatus.DEPENDENCY_BLOCKED
        assert result.capability_status is CapabilityStatus.UNAVAILABLE
        assert result.actual_final_disposition is None
    else:
        assert registration.producer is not None
        assert result.status is HarnessResultStatus.PASS
        assert result.capability_status is CapabilityStatus.AVAILABLE
        assert result.mismatches == ()
        assert result.actual_final_disposition == result.expected_final_disposition


@pytest.mark.parametrize("fixture_id", tuple(EXPECTED_FIRST_BLOCKERS))
def test_negative_pf1_first_blocker_is_observed_exactly(pf1_state, fixture_id) -> None:
    _, _, _, report = pf1_state
    result = next(item for item in report.results if item.fixture_id == fixture_id)
    blocker_id, stage, reason = EXPECTED_FIRST_BLOCKERS[fixture_id]
    assert result.actual_first_blocker["blocker_id"] == blocker_id
    assert result.actual_first_blocker["stage"] == stage
    assert result.actual_first_blocker["reason"] == reason
    assert result.actual_first_blocker == result.expected_first_blocker


def test_pf1_coverage_counts_are_statuses_not_scores(pf1_state) -> None:
    _, _, _, report = pf1_state
    assert report.semantic_active == 129
    assert report.semantic_deferred == 25
    assert report.physical_implemented >= 76
    assert report.executable == 31
    assert report.dependency_blocked == 1
    assert report.passed == 31
    assert report.non_conforming == report.fixture_invalid == 0
    assert "score" not in report.to_json()
    assert "percentage" not in report.to_json()


def test_executable_adapters_do_not_read_fixture_expected_projection(pf1_state) -> None:
    _, fixtures, registry, _ = pf1_state
    for fixture in fixtures:
        if fixture.manifest.fixture_id not in LEGACY_EXECUTABLE_IDS:
            continue
        registration = registry.require(fixture.manifest.execution.adapter_id)
        if registration.producer is None:
            continue
        source = inspect.getsource(registration.producer)
        assert "manifest.expected" not in source
        assert "fixture.manifest.expected" not in source


def test_lang_014a_declares_and_tests_one_structured_production_source(pf1_state) -> None:
    _, fixtures, registry, report = pf1_state
    fixture = next(item for item in fixtures if item.manifest.fixture_id == "FX-R5-LANG-014A")
    registration = registry.require(fixture.manifest.execution.adapter_id)
    result = next(item for item in report.results if item.fixture_id == fixture.manifest.fixture_id)

    producer_identity = "commerce_lens.skill.public_response.PublicResponse.unsupported_conclusions"
    assert fixture.manifest.execution.adapter_id == "controlled_public_response_output"
    assert fixture.manifest.execution.required_capability == "structured_controlled_refusal_output"
    assert registration.actual_output_producer == producer_identity
    assert registration.producer is not None
    actual = registration.producer(fixture)
    assert actual.actual_output_producer == producer_identity
    assert result.status is HarnessResultStatus.PASS
    source = inspect.getsource(registration.producer)
    assert "outcome.response.unsupported_conclusions" in source
    assert "render_text" not in source
    assert "else text" not in source


def test_lang_014a_production_output_tamper_becomes_non_conforming(pf1_state) -> None:
    _, fixtures, registry, _ = pf1_state
    fixture = next(item for item in fixtures if item.manifest.fixture_id == "FX-R5-LANG-014A")
    registration = registry.require(fixture.manifest.execution.adapter_id)
    assert registration.producer is not None
    actual = registration.producer(fixture)
    rendering = actual.material_path[1]
    tampered_rendering = rendering.model_copy(
        update={
            "outcome": {
                "classification": "UNRECOGNIZED_CONTROLLED_WORDING",
                "text": "Altered after production.",
            }
        }
    )
    tampered = actual.model_copy(
        update={"material_path": (actual.material_path[0], tampered_rendering)}
    )

    result = compare_fixture(fixture, tampered)

    assert result.status is HarnessResultStatus.NON_CONFORMING
    mismatch = next(item for item in result.mismatches if item.field == "material_path")
    assert mismatch.expected != mismatch.actual


def test_real_sut_projection_tamper_becomes_non_conforming(pf1_state) -> None:
    _, fixtures, registry, _ = pf1_state
    fixture = next(item for item in fixtures if item.manifest.fixture_id == "FX-R5-CLAIM-001A")
    registration = registry.require(fixture.manifest.execution.adapter_id)
    assert registration.producer is not None
    actual = registration.producer(fixture)
    tampered = actual.model_copy(update={"final_disposition": "TAMPERED_AFTER_SUT"})
    result = compare_fixture(fixture, tampered)
    assert result.status is HarnessResultStatus.NON_CONFORMING
    mismatch = next(item for item in result.mismatches if item.field == "final_disposition")
    assert mismatch.expected == "CLAIM_PROHIBITED__UNSUPPORTED_CLAIM_TYPE"
    assert mismatch.actual == "TAMPERED_AFTER_SUT"


def test_blocked_and_not_reached_paths_never_fabricate_downstream_outcomes(pf1_state) -> None:
    _, fixtures, _, _ = pf1_state
    for fixture in fixtures:
        for stage in fixture.manifest.expected.material_path:
            if stage.reachability.value == "not_reached":
                assert stage.outcome is None
                assert stage.not_reached_due_to is not None
