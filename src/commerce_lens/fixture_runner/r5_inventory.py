"""Derived R5 implementation inventory; frozen Markdown remains semantic authority."""

from __future__ import annotations

import hashlib
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from commerce_lens.evidence.identifiers import sha256_file
from commerce_lens.fixture_runner.r5_manifest import (
    R5_ACTIVE_ID_PATTERN,
    R5_DEFERRED_ID_PATTERN,
    R5Family,
    R5ManifestError,
    StrictModel,
    safe_load_yaml_mapping,
)


R5_SPEC_RELATIVE_PATH = Path("docs/frozen/DIAGNOSTIC_SYNTHETIC_FIXTURE_SUITE_SPECIFICATION.md")
R5_INVENTORY_ROOT = Path("fixtures/r5")
EXPECTED_ACTIVE_COUNT = 129
EXPECTED_DEFERRED_COUNT = 25
EXPECTED_ACTIVE_IDENTITY_SHA256 = "c97b71eca888117ebdaae920d841d53b715c02b1eb9637707d26389d9390523e"
EXPECTED_DEFERRED_IDENTITY_SHA256 = "8dfe5b00ccaa7d30716e9fcdd73ef9098a768f675a299977f79f64740aaba423"


class ImplementationStatus(str, Enum):
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    PHYSICAL_READY = "PHYSICAL_READY"
    DEPENDENCY_BLOCKED = "DEPENDENCY_BLOCKED"
    EXECUTABLE = "EXECUTABLE"


class InventoryBinding(StrictModel):
    registry_role: Literal["DERIVED_IMPLEMENTATION_INDEX"]
    semantic_authority: Literal["FROZEN_R5_SPECIFICATION"]
    r5_version: Literal["R5 v1.0"]
    spec_path: Literal["docs/frozen/DIAGNOSTIC_SYNTHETIC_FIXTURE_SUITE_SPECIFICATION.md"]
    spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ActiveInventoryEntry(StrictModel):
    fixture_id: str
    family: R5Family
    semantic_status: Literal["ACTIVE"]
    implementation_status: ImplementationStatus
    executable: bool

    @model_validator(mode="after")
    def validate_identity(self) -> "ActiveInventoryEntry":
        match = R5_ACTIVE_ID_PATTERN.fullmatch(self.fixture_id)
        if match is None or match.group(1) != self.family.value:
            raise ValueError("ACTIVE inventory ID/family is invalid")
        if self.executable != (self.implementation_status is ImplementationStatus.EXECUTABLE):
            raise ValueError("executable must be true only for EXECUTABLE implementation status")
        return self


class DeferredInventoryEntry(StrictModel):
    deferred_id: str
    family: R5Family
    semantic_status: Literal["FUTURE_REQUIRED_DEFERRED"]
    implementation_status: Literal[ImplementationStatus.NOT_IMPLEMENTED]
    executable: Literal[False]
    frozen_authority_reference: str = Field(min_length=1)
    missing_authority: str = Field(min_length=1)
    activation_prerequisite: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_identity(self) -> "DeferredInventoryEntry":
        match = R5_DEFERRED_ID_PATTERN.fullmatch(self.deferred_id)
        if match is None or match.group(1) != self.family.value:
            raise ValueError("DEFERRED inventory ID/family is invalid")
        return self


class ActiveInventory(StrictModel):
    binding: InventoryBinding
    entries: tuple[ActiveInventoryEntry, ...]

    @model_validator(mode="after")
    def validate_inventory(self) -> "ActiveInventory":
        ids = [entry.fixture_id for entry in self.entries]
        _validate_exact_unique_sorted(ids, EXPECTED_ACTIVE_COUNT, "ACTIVE")
        return self


class DeferredInventory(StrictModel):
    binding: InventoryBinding
    entries: tuple[DeferredInventoryEntry, ...]

    @model_validator(mode="after")
    def validate_inventory(self) -> "DeferredInventory":
        ids = [entry.deferred_id for entry in self.entries]
        _validate_exact_unique_sorted(ids, EXPECTED_DEFERRED_COUNT, "DEFERRED")
        return self


class R5Inventory(StrictModel):
    active: ActiveInventory
    deferred: DeferredInventory

    @model_validator(mode="after")
    def validate_shared_binding(self) -> "R5Inventory":
        if self.active.binding != self.deferred.binding:
            raise ValueError("ACTIVE and DEFERRED registries must share the exact R5 binding")
        return self

    @property
    def active_ids(self) -> tuple[str, ...]:
        return tuple(item.fixture_id for item in self.active.entries)

    @property
    def deferred_ids(self) -> tuple[str, ...]:
        return tuple(item.deferred_id for item in self.deferred.entries)


class CoverageStatus(StrictModel):
    semantic_active: int
    semantic_deferred: int
    physical_implemented: int
    executable: int
    dependency_blocked: int


def load_r5_inventory(repo_root: str | Path, inventory_root: str | Path | None = None) -> R5Inventory:
    root = Path(repo_root).resolve()
    registry_root = Path(inventory_root).resolve() if inventory_root is not None else root / R5_INVENTORY_ROOT
    try:
        active = ActiveInventory.model_validate(safe_load_yaml_mapping(registry_root / "inventory" / "active.yaml"))
        deferred = DeferredInventory.model_validate(safe_load_yaml_mapping(registry_root / "inventory" / "deferred.yaml"))
        if active.binding.spec_sha256 != deferred.binding.spec_sha256:
            raise R5ManifestError("R5 inventory binding fingerprint differs between ACTIVE and DEFERRED registries")
        inventory = R5Inventory(active=active, deferred=deferred)
    except R5ManifestError:
        raise
    except Exception as exc:
        raise R5ManifestError(f"R5 derived inventory is invalid: {exc}") from exc
    spec_path = root / R5_SPEC_RELATIVE_PATH
    if not spec_path.is_file():
        raise R5ManifestError(f"frozen R5 specification is missing: {spec_path}")
    actual = sha256_file(spec_path)
    if inventory.active.binding.spec_sha256 != actual:
        raise R5ManifestError("R5 inventory binding fingerprint does not match frozen specification")
    if _identity_digest(inventory.active_ids) != EXPECTED_ACTIVE_IDENTITY_SHA256:
        raise R5ManifestError("R5 ACTIVE inventory identity set disagrees with its reviewed frozen-spec derivation")
    if _identity_digest(inventory.deferred_ids) != EXPECTED_DEFERRED_IDENTITY_SHA256:
        raise R5ManifestError("R5 DEFERRED inventory identity set disagrees with its reviewed frozen-spec derivation")
    return inventory


def coverage_status(inventory: R5Inventory, physical_ids: tuple[str, ...]) -> CoverageStatus:
    by_id = {entry.fixture_id: entry for entry in inventory.active.entries}
    unknown = sorted(set(physical_ids) - set(by_id))
    if unknown:
        raise R5ManifestError(f"physical coverage contains orphan ID(s): {', '.join(unknown)}")
    return CoverageStatus(
        semantic_active=len(inventory.active.entries),
        semantic_deferred=len(inventory.deferred.entries),
        physical_implemented=len(set(physical_ids)),
        executable=sum(by_id[item].implementation_status is ImplementationStatus.EXECUTABLE for item in set(physical_ids)),
        dependency_blocked=sum(
            by_id[item].implementation_status is ImplementationStatus.DEPENDENCY_BLOCKED for item in set(physical_ids)
        ),
    )


def _validate_exact_unique_sorted(ids: list[str], expected_count: int, label: str) -> None:
    if len(ids) != expected_count:
        raise ValueError(f"{label} inventory must contain exactly {expected_count} identities")
    duplicates = sorted(item for item in set(ids) if ids.count(item) > 1)
    if duplicates:
        raise ValueError(f"duplicate {label} inventory ID(s): {', '.join(duplicates)}")
    if ids != sorted(ids):
        raise ValueError(f"{label} inventory must be sorted by canonical identity")


def _identity_digest(ids: tuple[str, ...]) -> str:
    canonical = "".join(f"{item}\n" for item in ids).encode("ascii")
    return hashlib.sha256(canonical).hexdigest()
