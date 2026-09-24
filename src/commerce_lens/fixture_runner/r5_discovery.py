"""Deterministic, tranche-aware discovery for future R5 fixture bundles."""

from __future__ import annotations

from pathlib import Path

from commerce_lens.fixture_runner.r5_inventory import ImplementationStatus, R5Inventory
from commerce_lens.fixture_runner.r5_manifest import (
    R5_DEFERRED_ID_PATTERN,
    R5_FAMILIES,
    LoadedR5Fixture,
    R5ManifestError,
    load_r5_manifest,
)


def discover_r5_fixtures(fixtures_root: str | Path, inventory: R5Inventory) -> tuple[LoadedR5Fixture, ...]:
    """Discover only implemented tranche bundles; missing ACTIVE IDs are allowed."""
    root = Path(fixtures_root).resolve()
    active_root = root / "active"
    if not active_root.is_dir() or active_root.is_symlink():
        raise R5ManifestError(f"R5 executable fixture root is missing or unsafe: {active_root}")
    entries = sorted((item for item in active_root.iterdir() if item.name != "README.md"), key=lambda item: item.name)
    unexpected_files = [item.name for item in entries if not item.is_dir()]
    if unexpected_files:
        raise R5ManifestError(f"unexpected file(s) in R5 active root: {', '.join(unexpected_files)}")
    unknown_families = [item.name for item in entries if item.name not in R5_FAMILIES]
    if unknown_families:
        raise R5ManifestError(f"unknown R5 family directorie(s): {', '.join(unknown_families)}")

    registry_by_id = {entry.fixture_id: entry for entry in inventory.active.entries}
    deferred_ids = set(inventory.deferred_ids)
    loaded: list[LoadedR5Fixture] = []
    for family_dir in entries:
        if family_dir.is_symlink():
            raise R5ManifestError(f"R5 family directory must not be a symlink: {family_dir}")
        for case_dir in sorted(family_dir.iterdir(), key=lambda item: item.name):
            if not case_dir.is_dir() or case_dir.is_symlink():
                raise R5ManifestError(f"malformed R5 family entry: {case_dir}")
            if case_dir.name in deferred_ids or R5_DEFERRED_ID_PATTERN.fullmatch(case_dir.name):
                raise R5ManifestError(f"DEFERRED identity is forbidden from executable root: {case_dir.name}")
            fixture = load_r5_manifest(case_dir)
            if fixture.manifest.family.value != family_dir.name:
                raise R5ManifestError(f"fixture family directory mismatch: {fixture.manifest.fixture_id}")
            entry = registry_by_id.get(fixture.manifest.fixture_id)
            if entry is None:
                raise R5ManifestError(f"physical orphan not present in derived ACTIVE inventory: {fixture.manifest.fixture_id}")
            if entry.implementation_status is ImplementationStatus.NOT_IMPLEMENTED:
                raise R5ManifestError(
                    f"physical fixture exists but inventory still says NOT_IMPLEMENTED: {fixture.manifest.fixture_id}"
                )
            loaded.append(fixture)

    ids = [fixture.manifest.fixture_id for fixture in loaded]
    duplicates = sorted(item for item in set(ids) if ids.count(item) > 1)
    if duplicates:
        raise R5ManifestError(f"duplicate physical R5 fixture ID(s): {', '.join(duplicates)}")
    return tuple(sorted(loaded, key=lambda fixture: fixture.manifest.fixture_id))
