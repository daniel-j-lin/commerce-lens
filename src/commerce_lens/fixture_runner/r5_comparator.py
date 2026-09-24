"""Exact R5 projection comparison; contains no CommerceLens business semantics."""

from __future__ import annotations

from typing import Any

from commerce_lens.fixture_runner.r5_manifest import ActualProjection, LoadedR5Fixture, Reachability
from commerce_lens.fixture_runner.r5_result import (
    CapabilityStatus,
    HarnessResult,
    HarnessResultStatus,
    MaterialMismatch,
)


def compare_fixture(fixture: LoadedR5Fixture, actual: ActualProjection) -> HarnessResult:
    expected = fixture.manifest.expected
    mismatches: list[MaterialMismatch] = []
    _diff("final_disposition", expected.final_disposition, actual.final_disposition, mismatches)
    _diff(
        "first_controlling_blocker",
        _dump(expected.first_controlling_blocker),
        _dump(actual.first_controlling_blocker),
        mismatches,
    )
    _diff(
        "material_path",
        [_dump(item) for item in expected.material_path],
        [_dump(item) for item in actual.material_path],
        mismatches,
    )
    _diff("chain_dispositions", expected.chain_dispositions, actual.chain_dispositions, mismatches)
    _diff(
        "trace_integrity_state",
        expected.trace_integrity_expectation,
        actual.trace_integrity_state,
        mismatches,
    )
    return HarnessResult(
        fixture_id=fixture.manifest.fixture_id,
        semantic_family=fixture.manifest.family.value,
        execution_mode=fixture.manifest.execution.mode,
        adapter_id=fixture.manifest.execution.adapter_id,
        capability_status=CapabilityStatus.AVAILABLE,
        status=HarnessResultStatus.NON_CONFORMING if mismatches else HarnessResultStatus.PASS,
        expected_final_disposition=expected.final_disposition,
        actual_final_disposition=actual.final_disposition,
        expected_first_blocker=_dump(expected.first_controlling_blocker),
        actual_first_blocker=_dump(actual.first_controlling_blocker),
        expected_reached_stages=_reached(expected.material_path),
        actual_reached_stages=_reached(actual.material_path),
        mismatches=tuple(mismatches),
        artifact_evidence_refs=actual.artifact_evidence_refs,
    )


def _reached(path) -> tuple[str, ...]:
    return tuple(
        f"{item.chain_id}:{item.stage.value}"
        for item in path
        if item.reachability is not Reachability.NOT_REACHED
    )


def _dump(value: Any) -> Any:
    return value if isinstance(value, str) else value.model_dump(mode="json")


def _diff(field: str, expected: Any, actual: Any, mismatches: list[MaterialMismatch]) -> None:
    if expected != actual:
        mismatches.append(MaterialMismatch(field=field, expected=expected, actual=actual))
