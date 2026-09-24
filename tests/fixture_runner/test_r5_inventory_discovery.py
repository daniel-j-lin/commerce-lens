from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from commerce_lens.fixture_runner.r5_discovery import discover_r5_fixtures
from commerce_lens.fixture_runner.r5_inventory import (
    ActiveInventory,
    EXPECTED_ACTIVE_COUNT,
    EXPECTED_DEFERRED_COUNT,
    ImplementationStatus,
    coverage_status,
    load_r5_inventory,
)
from commerce_lens.fixture_runner.r5_manifest import R5_FAMILIES, R5ManifestError
from tests.fixture_runner.r5_test_support import manifest_payload, write_case


ROOT = Path(__file__).resolve().parents[2]


def test_derived_inventory_is_bound_and_complete() -> None:
    inventory = load_r5_inventory(ROOT)
    assert len(inventory.active.entries) == EXPECTED_ACTIVE_COUNT == 129
    assert len(inventory.deferred.entries) == EXPECTED_DEFERRED_COUNT == 25
    assert all(item.semantic_status == "ACTIVE" for item in inventory.active.entries)
    assert all(
        item.executable == (item.implementation_status is ImplementationStatus.EXECUTABLE)
        for item in inventory.active.entries
    )
    assert all(item.semantic_status == "FUTURE_REQUIRED_DEFERRED" and not item.executable for item in inventory.deferred.entries)
    assert "FX-R5-R4-001A" in inventory.active_ids
    assert "DF-R5-R4-001" in inventory.deferred_ids


def test_family_allowlist_is_exact_and_includes_r4() -> None:
    assert R5_FAMILIES == (
        "EVID", "MEAS", "ADMIT", "R4", "DIAG", "ALT", "CLAIM",
        "CAUSE", "NARROW", "LANG", "VERSION", "PROV", "CHAIN", "PREC",
    )


def test_inventory_fingerprint_mismatch_is_invalid(tmp_path) -> None:
    copied = tmp_path / "r5"
    shutil.copytree(ROOT / "fixtures/r5", copied)
    path = copied / "inventory/active.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace("d8aff7", "000000"), encoding="utf-8")
    with pytest.raises(R5ManifestError, match="fingerprint"):
        load_r5_inventory(ROOT, copied)


def test_inventory_cannot_silently_substitute_a_canonical_looking_identity(tmp_path) -> None:
    copied = tmp_path / "r5"
    shutil.copytree(ROOT / "fixtures/r5", copied)
    path = copied / "inventory/active.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace("FX-R5-ADMIT-003A", "FX-R5-ADMIT-002A"), encoding="utf-8")
    with pytest.raises(R5ManifestError, match="identity set disagrees"):
        load_r5_inventory(ROOT, copied)


def test_duplicate_active_inventory_id_is_rejected() -> None:
    inventory = load_r5_inventory(ROOT)
    entries = list(inventory.active.entries)
    entries[-1] = entries[0]
    with pytest.raises(ValueError, match="duplicate ACTIVE"):
        ActiveInventory(binding=inventory.active.binding, entries=tuple(entries))


def test_discovery_allows_an_empty_physical_tranche(tmp_path) -> None:
    inventory = load_r5_inventory(ROOT)
    (tmp_path / "active").mkdir()
    assert discover_r5_fixtures(tmp_path, inventory) == ()
    coverage = coverage_status(inventory, ())
    assert coverage.model_dump() == {
        "semantic_active": 129,
        "semantic_deferred": 25,
        "physical_implemented": 0,
        "executable": 0,
        "dependency_blocked": 0,
    }


def test_discovery_sorts_fixture_ids(tmp_path) -> None:
    inventory = _physical_ready(load_r5_inventory(ROOT), "FX-R5-EVID-001A", "FX-R5-EVID-002A")
    write_case(tmp_path, manifest_payload(fixture_id="FX-R5-EVID-002A"))
    write_case(tmp_path, manifest_payload(fixture_id="FX-R5-EVID-001A"))
    assert [item.manifest.fixture_id for item in discover_r5_fixtures(tmp_path, inventory)] == [
        "FX-R5-EVID-001A", "FX-R5-EVID-002A"
    ]


def test_discovery_rejects_unknown_family(tmp_path) -> None:
    (tmp_path / "active/UNKNOWN").mkdir(parents=True)
    with pytest.raises(R5ManifestError, match="unknown R5 family"):
        discover_r5_fixtures(tmp_path, load_r5_inventory(ROOT))


def test_discovery_rejects_deferred_in_executable_root(tmp_path) -> None:
    (tmp_path / "active/EVID/DF-R5-EVID-001").mkdir(parents=True)
    with pytest.raises(R5ManifestError, match="DEFERRED identity"):
        discover_r5_fixtures(tmp_path, load_r5_inventory(ROOT))


def test_discovery_rejects_physical_orphan(tmp_path) -> None:
    write_case(tmp_path, manifest_payload(fixture_id="FX-R5-EVID-999A"))
    with pytest.raises(R5ManifestError, match="physical orphan"):
        discover_r5_fixtures(tmp_path, load_r5_inventory(ROOT))


def test_discovery_rejects_not_implemented_registry_state(tmp_path) -> None:
    write_case(tmp_path)
    with pytest.raises(R5ManifestError, match="NOT_IMPLEMENTED"):
        discover_r5_fixtures(tmp_path, load_r5_inventory(ROOT))


def test_discovery_rejects_directory_manifest_mismatch(tmp_path) -> None:
    payload = manifest_payload(fixture_id="FX-R5-EVID-002A")
    case_dir = tmp_path / "active/EVID/FX-R5-EVID-001A"
    case_dir.mkdir(parents=True)
    import yaml
    (case_dir / "manifest.yaml").write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    inventory = _physical_ready(load_r5_inventory(ROOT), "FX-R5-EVID-001A")
    with pytest.raises(R5ManifestError, match="directory name"):
        discover_r5_fixtures(tmp_path, inventory)


def _physical_ready(inventory, *fixture_ids):
    selected = set(fixture_ids)
    entries = tuple(
        item.model_copy(update={"implementation_status": ImplementationStatus.PHYSICAL_READY})
        if item.fixture_id in selected else item
        for item in inventory.active.entries
    )
    return inventory.model_copy(update={"active": inventory.active.model_copy(update={"entries": entries})})
