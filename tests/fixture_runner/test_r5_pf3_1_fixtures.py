from __future__ import annotations

import hashlib
import inspect
import json
import shutil
from pathlib import Path

import pytest
import yaml

from commerce_lens.fixture_runner.r5_inventory import load_r5_inventory
from commerce_lens.fixture_runner.r5_manifest import ExecutionMode, load_r5_manifest
from commerce_lens.fixture_runner.r5_pf3_adapters import (
    CONTROLLED_PRODUCER_PREFIX,
    build_r5_pf3_adapter_registry,
    load_controlled_object,
)
from commerce_lens.fixture_runner.r5_result import HarnessResultStatus
from commerce_lens.fixture_runner.r5_runner import run_case_dir


ROOT = Path(__file__).resolve().parents[2]
R5_ROOT = ROOT / "fixtures/r5"
PF3_IDS = (
    "FX-R5-ADMIT-003A",
    "FX-R5-ALT-006A",
    "FX-R5-DIAG-003A",
    "FX-R5-NARROW-001A",
)


def _case_dir(fixture_id: str) -> Path:
    family = fixture_id.removeprefix("FX-R5-").split("-", 1)[0]
    return R5_ROOT / "active" / family / fixture_id


def _copy_with_mutation(tmp_path: Path, fixture_id: str, mutate) -> object:
    source = _case_dir(fixture_id)
    target = tmp_path / fixture_id
    shutil.copytree(source, target)
    manifest = yaml.safe_load((target / "manifest.yaml").read_text(encoding="utf-8"))
    input_spec = manifest["inputs"][0]
    state_path = target / input_spec["path"]
    state = json.loads(state_path.read_text(encoding="utf-8"))
    mutate(state)
    state_bytes = json.dumps(state, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    state_path.write_bytes(state_bytes)
    input_spec["sha256"] = hashlib.sha256(state_bytes).hexdigest()
    (target / "manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
    )
    return load_r5_manifest(target)


def _walk_keys(value):
    if isinstance(value, dict):
        yield from value.keys()
        for child in value.values():
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def test_pf3_1_exact_fixtures_are_controlled_and_pass() -> None:
    registry = build_r5_pf3_adapter_registry()
    for fixture_id in PF3_IDS:
        fixture = load_r5_manifest(_case_dir(fixture_id))
        registration = registry.require(fixture.manifest.execution.adapter_id)
        assert fixture.manifest.execution.mode is ExecutionMode.CONTROLLED_CASE
        assert registration.execution_mode is ExecutionMode.CONTROLLED_CASE
        assert registration.producer is not None
        assert registration.actual_output_producer.startswith(CONTROLLED_PRODUCER_PREFIX)
        result = run_case_dir(_case_dir(fixture_id), registry)
        assert result.status is HarnessResultStatus.PASS
        assert result.mismatches == ()


def test_pf3_1_inputs_are_lower_level_facts_only() -> None:
    forbidden = {"expected", "outcome", "disposition", "blocker", "final", "valid", "admissible"}
    for fixture_id in PF3_IDS:
        fixture = load_r5_manifest(_case_dir(fixture_id))
        for input_spec in fixture.manifest.inputs:
            value = load_controlled_object(fixture, input_spec.role)
            assert not forbidden.intersection(_walk_keys(value))


@pytest.mark.parametrize(
    ("fixture_id", "mutate"),
    [
        (
            "FX-R5-ADMIT-003A",
            lambda state: state["authority_records"].append(
                {
                    "id": state["required_authority_id"],
                    "fingerprint": "a" * 64,
                    "version": "diagnostic_admission_v1",
                }
            ),
        ),
        (
            "FX-R5-ALT-006A",
            lambda state: state["evidence_records"].append(
                {
                    "id": state["required_evidence_id"],
                    "fingerprint": "b" * 64,
                    "version": "competitor_evidence_v1",
                }
            ),
        ),
        (
            "FX-R5-DIAG-003A",
            lambda state: state["authority_records"].append(
                {
                    "id": state["required_authority_id"],
                    "fingerprint": "c" * 64,
                    "version": "diagnostic_support_definition_v1",
                }
            ),
        ),
        (
            "FX-R5-NARROW-001A",
            lambda state: (
                state["rendered_proposition"].update(
                    {
                        "id": "revenue_decline_paid_orders",
                        "fingerprint": "d" * 64,
                        "population_id": "paid_orders",
                    }
                ),
                state["rendered_evaluation"].update(
                    {
                        "id": "evaluation_revenue_decline_paid_orders",
                        "fingerprint": "e" * 64,
                    }
                ),
            ),
        ),
    ],
)
def test_pf3_1_lower_level_state_mutation_changes_controlled_result(
    tmp_path: Path, fixture_id: str, mutate
) -> None:
    registry = build_r5_pf3_adapter_registry()
    baseline_fixture = load_r5_manifest(_case_dir(fixture_id))
    registration = registry.require(baseline_fixture.manifest.execution.adapter_id)
    assert registration.producer is not None
    baseline = registration.producer(baseline_fixture)
    mutated_fixture = _copy_with_mutation(tmp_path, fixture_id, mutate)
    mutated = registration.producer(mutated_fixture)
    assert mutated.final_disposition != baseline.final_disposition
    assert mutated.trace_integrity_state != baseline.trace_integrity_state


def test_pf3_1_disclaimer_alone_does_not_change_narrowing_identity(tmp_path: Path) -> None:
    registry = build_r5_pf3_adapter_registry()
    fixture = load_r5_manifest(_case_dir("FX-R5-NARROW-001A"))
    registration = registry.require(fixture.manifest.execution.adapter_id)
    assert registration.producer is not None
    baseline = registration.producer(fixture)

    def add_disclaimer(state):
        state["rendering"]["disclaimer_text"] = "A different disclaimer."

    changed_rendering = _copy_with_mutation(tmp_path, "FX-R5-NARROW-001A", add_disclaimer)
    changed = registration.producer(changed_rendering)
    assert changed.final_disposition == baseline.final_disposition
    assert changed.trace_integrity_state == baseline.trace_integrity_state


def test_pf3_1_source_has_no_fixture_or_expected_or_scenario_oracle() -> None:
    module = __import__(
        "commerce_lens.fixture_runner.r5_pf3_adapters", fromlist=["r5_pf3_adapters"]
    )
    source = inspect.getsource(module)
    assert "EXPECTED_BY_FIXTURE_ID" not in source
    assert "manifest.expected" not in source
    assert "fixture.manifest.expected" not in source
    assert not __import__("re").search(r"FX-R5-[A-Z0-9-]+", source)
    assert not __import__("re").search(r"\bscenario\b", source, flags=__import__("re").IGNORECASE)


def test_pf3_1_inventory_marks_only_authorized_four_as_executable() -> None:
    inventory = load_r5_inventory(ROOT)
    entries = {entry.fixture_id: entry for entry in inventory.active.entries}
    assert set(PF3_IDS).issubset(entries)
    assert all(entries[fixture_id].executable for fixture_id in PF3_IDS)
