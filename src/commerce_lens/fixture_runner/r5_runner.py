"""PF0 R5 harness runner with dependency gating and no family business logic."""

from __future__ import annotations

from pathlib import Path

from commerce_lens.fixture_runner.r5_adapters import AdapterRegistry, AdapterRegistryError
from commerce_lens.fixture_runner.r5_comparator import compare_fixture
from commerce_lens.fixture_runner.r5_discovery import discover_r5_fixtures
from commerce_lens.fixture_runner.r5_inventory import ImplementationStatus, R5Inventory, coverage_status
from commerce_lens.fixture_runner.r5_manifest import LoadedR5Fixture, R5ManifestError, Reachability, load_r5_manifest
from commerce_lens.fixture_runner.r5_result import (
    CapabilityStatus,
    HarnessResult,
    HarnessResultStatus,
    HarnessSuiteReport,
    MaterialMismatch,
)


def run_fixture(fixture: LoadedR5Fixture, registry: AdapterRegistry) -> HarnessResult:
    manifest = fixture.manifest
    expected = manifest.expected
    try:
        adapter = registry.require(manifest.execution.adapter_id)
    except AdapterRegistryError as exc:
        return _invalid(fixture, str(exc))
    if adapter.execution_mode is not manifest.execution.mode:
        return _invalid(fixture, "adapter execution mode does not match manifest")
    if (
        adapter.capability_name != manifest.execution.required_capability
        or adapter.capability_version != manifest.execution.required_capability_version
    ):
        return _invalid(fixture, "adapter capability binding does not match manifest")
    if not adapter.available:
        return HarnessResult(
            fixture_id=manifest.fixture_id,
            semantic_family=manifest.family.value,
            execution_mode=manifest.execution.mode,
            adapter_id=manifest.execution.adapter_id,
            capability_status=CapabilityStatus.UNAVAILABLE,
            status=HarnessResultStatus.DEPENDENCY_BLOCKED,
            expected_final_disposition=expected.final_disposition,
            expected_first_blocker=_dump_blocker(expected.first_controlling_blocker),
            expected_reached_stages=_reached(expected.material_path),
        )
    try:
        actual = adapter.producer(fixture)  # type: ignore[misc]
    except Exception as exc:
        return HarnessResult(
            fixture_id=manifest.fixture_id,
            semantic_family=manifest.family.value,
            execution_mode=manifest.execution.mode,
            adapter_id=manifest.execution.adapter_id,
            capability_status=CapabilityStatus.EXECUTION_FAILED,
            status=HarnessResultStatus.NON_CONFORMING,
            expected_final_disposition=expected.final_disposition,
            expected_first_blocker=_dump_blocker(expected.first_controlling_blocker),
            expected_reached_stages=_reached(expected.material_path),
            mismatches=(MaterialMismatch(field="subject_under_test_execution", expected="actual projection", actual=str(exc)),),
        )
    if actual.actual_output_producer != adapter.actual_output_producer:
        return HarnessResult(
            fixture_id=manifest.fixture_id,
            semantic_family=manifest.family.value,
            execution_mode=manifest.execution.mode,
            adapter_id=manifest.execution.adapter_id,
            capability_status=CapabilityStatus.AVAILABLE,
            status=HarnessResultStatus.NON_CONFORMING,
            expected_final_disposition=expected.final_disposition,
            actual_final_disposition=actual.final_disposition,
            expected_first_blocker=_dump_blocker(expected.first_controlling_blocker),
            actual_first_blocker=_dump_blocker(actual.first_controlling_blocker),
            expected_reached_stages=_reached(expected.material_path),
            actual_reached_stages=_reached(actual.material_path),
            mismatches=(
                MaterialMismatch(
                    field="actual_output_producer",
                    expected=adapter.actual_output_producer,
                    actual=actual.actual_output_producer,
                ),
            ),
        )
    return compare_fixture(fixture, actual)


def run_case_dir(case_dir: str | Path, registry: AdapterRegistry) -> HarnessResult:
    try:
        fixture = load_r5_manifest(case_dir)
    except R5ManifestError as exc:
        return HarnessResult(
            fixture_id=Path(case_dir).name or "UNKNOWN",
            capability_status=CapabilityStatus.NOT_CHECKED,
            status=HarnessResultStatus.FIXTURE_INVALID,
            mismatches=(MaterialMismatch(field="fixture", expected="valid R5 fixture", actual=str(exc)),),
        )
    return run_fixture(fixture, registry)


def run_suite(fixtures_root: str | Path, inventory: R5Inventory, registry: AdapterRegistry) -> HarnessSuiteReport:
    fixtures = discover_r5_fixtures(fixtures_root, inventory)
    status_by_id = {entry.fixture_id: entry.implementation_status for entry in inventory.active.entries}
    runnable = tuple(
        fixture
        for fixture in fixtures
        if status_by_id[fixture.manifest.fixture_id]
        in {ImplementationStatus.EXECUTABLE, ImplementationStatus.DEPENDENCY_BLOCKED}
    )
    results = tuple(sorted((run_fixture(fixture, registry) for fixture in runnable), key=lambda item: item.fixture_id))
    coverage = coverage_status(inventory, tuple(fixture.manifest.fixture_id for fixture in fixtures))
    return HarnessSuiteReport(
        semantic_active=coverage.semantic_active,
        semantic_deferred=coverage.semantic_deferred,
        physical_implemented=coverage.physical_implemented,
        executable=coverage.executable,
        dependency_blocked=sum(item.status is HarnessResultStatus.DEPENDENCY_BLOCKED for item in results),
        passed=sum(item.status is HarnessResultStatus.PASS for item in results),
        non_conforming=sum(item.status is HarnessResultStatus.NON_CONFORMING for item in results),
        fixture_invalid=sum(item.status is HarnessResultStatus.FIXTURE_INVALID for item in results),
        results=results,
    )


def _invalid(fixture: LoadedR5Fixture, reason: str) -> HarnessResult:
    manifest = fixture.manifest
    return HarnessResult(
        fixture_id=manifest.fixture_id,
        semantic_family=manifest.family.value,
        execution_mode=manifest.execution.mode,
        adapter_id=manifest.execution.adapter_id,
        capability_status=CapabilityStatus.NOT_CHECKED,
        status=HarnessResultStatus.FIXTURE_INVALID,
        expected_final_disposition=manifest.expected.final_disposition,
        expected_first_blocker=_dump_blocker(manifest.expected.first_controlling_blocker),
        expected_reached_stages=_reached(manifest.expected.material_path),
        mismatches=(MaterialMismatch(field="adapter_binding", expected="valid allowlisted adapter", actual=reason),),
    )


def _dump_blocker(value):
    return value if isinstance(value, str) else value.model_dump(mode="json")


def _reached(path) -> tuple[str, ...]:
    return tuple(
        f"{item.chain_id}:{item.stage.value}"
        for item in path
        if item.reachability is not Reachability.NOT_REACHED
    )
