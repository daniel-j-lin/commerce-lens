from __future__ import annotations

import hashlib
import inspect
import json
import re
import shutil
from pathlib import Path

import pytest
import yaml

from commerce_lens.fixture_runner.r5_inventory import load_r5_inventory
from commerce_lens.fixture_runner.r5_manifest import ExecutionMode, load_r5_manifest
from commerce_lens.fixture_runner.r5_pf3_adapters import (
    CONTROLLED_PRODUCER_PREFIX,
    ControlledInputError,
    build_r5_pf3_adapter_registry,
    load_controlled_object,
)
from commerce_lens.fixture_runner.r5_result import HarnessResultStatus
from commerce_lens.fixture_runner.r5_runner import run_case_dir


ROOT = Path(__file__).resolve().parents[2]
R5_ROOT = ROOT / "fixtures/r5"
PF3_2_IDS = (
    "FX-R5-CLAIM-003A",
    "FX-R5-CLAIM-004A",
    "FX-R5-CLAIM-005A",
    "FX-R5-CAUSE-001A",
    "FX-R5-CAUSE-002A",
    "FX-R5-CAUSE-003A",
    "FX-R5-CAUSE-004A",
    "FX-R5-CAUSE-005A",
    "FX-R5-CAUSE-006A",
)


def _case_dir(fixture_id: str) -> Path:
    family = fixture_id.removeprefix("FX-R5-").split("-", 1)[0]
    return R5_ROOT / "active" / family / fixture_id


def _copy_with_mutation(tmp_path: Path, fixture_id: str, mutate):
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


def test_pf3_2_exact_nine_controlled_cases_pass() -> None:
    registry = build_r5_pf3_adapter_registry()
    for fixture_id in PF3_2_IDS:
        fixture = load_r5_manifest(_case_dir(fixture_id))
        registration = registry.require(fixture.manifest.execution.adapter_id)
        assert fixture.manifest.execution.mode is ExecutionMode.CONTROLLED_CASE
        assert registration.execution_mode is ExecutionMode.CONTROLLED_CASE
        assert registration.producer is not None
        assert registration.actual_output_producer.startswith(CONTROLLED_PRODUCER_PREFIX)
        result = run_case_dir(_case_dir(fixture_id), registry)
        assert result.status is HarnessResultStatus.PASS
        assert result.mismatches == ()


def test_pf3_2_inputs_have_no_conclusion_valued_keys() -> None:
    forbidden = {"expected", "outcome", "disposition", "blocker", "final", "valid", "admissible"}
    for fixture_id in PF3_2_IDS:
        fixture = load_r5_manifest(_case_dir(fixture_id))
        for input_spec in fixture.manifest.inputs:
            value = load_controlled_object(fixture, input_spec.role)
            assert not forbidden.intersection(_walk_keys(value))


@pytest.mark.parametrize(
    "mutate",
    [
        lambda state: (
            state["claim_decision"].update({"claim_class": "diagnostic"}),
            state["attempted_rendering"].update({"rendering_class": "diagnostic"}),
        ),
        lambda state: (
            state["claim_decision"].update({"scope_id": "regional"}),
        ),
        lambda state: (
            state["claim_decision"]["proposition"].update(
                {"id": "regional_revenue_decline", "fingerprint": "a" * 64}
            ),
        ),
    ],
)
def test_claim_003_structural_decision_scope_class_and_binding_mutations_change_result(
    tmp_path: Path, mutate
) -> None:
    registry = build_r5_pf3_adapter_registry()
    fixture = load_r5_manifest(_case_dir("FX-R5-CLAIM-003A"))
    registration = registry.require(fixture.manifest.execution.adapter_id)
    assert registration.producer is not None
    baseline = registration.producer(fixture)
    changed_fixture = _copy_with_mutation(tmp_path, "FX-R5-CLAIM-003A", mutate)
    changed = registration.producer(changed_fixture)
    assert changed.trace_integrity_state != baseline.trace_integrity_state
    if changed.trace_integrity_state["decision_claim_class"] == "diagnostic":
        assert changed.final_disposition != baseline.final_disposition


def test_claim_004_matching_claim_decision_authority_changes_result(tmp_path: Path) -> None:
    registry = build_r5_pf3_adapter_registry()
    fixture = load_r5_manifest(_case_dir("FX-R5-CLAIM-004A"))
    registration = registry.require(fixture.manifest.execution.adapter_id)
    assert registration.producer is not None
    baseline = registration.producer(fixture)

    def add_matching_decision(state):
        candidate = state["finding_candidate"]
        state["authority_records"].append(
            {
                **state["claim_decision_reference"],
                "record_type": "claim_decision",
                "claim_class": "finding",
                "scope_id": state["requested_materialization"]["scope_id"],
                "proposition": candidate["proposition"],
            }
        )

    changed_fixture = _copy_with_mutation(tmp_path, "FX-R5-CLAIM-004A", add_matching_decision)
    changed = registration.producer(changed_fixture)
    assert changed.final_disposition != baseline.final_disposition
    assert changed.first_controlling_blocker == "NONE"
    assert changed.trace_integrity_state["claim_decision_reference_present"] is True


def test_claim_004_candidate_scope_mismatch_blocks_matching_decision(tmp_path: Path) -> None:
    registry = build_r5_pf3_adapter_registry()
    fixture = load_r5_manifest(_case_dir("FX-R5-CLAIM-004A"))
    registration = registry.require(fixture.manifest.execution.adapter_id)
    assert registration.producer is not None

    def add_matching_decision_then_mismatch_candidate_scope(state):
        candidate = state["finding_candidate"]
        state["authority_records"].append(
            {
                **state["claim_decision_reference"],
                "record_type": "claim_decision",
                "claim_class": "finding",
                "scope_id": state["requested_materialization"]["scope_id"],
                "proposition": candidate["proposition"],
            }
        )
        candidate["scope_id"] = "regional"

    changed_fixture = _copy_with_mutation(
        tmp_path, "FX-R5-CLAIM-004A", add_matching_decision_then_mismatch_candidate_scope
    )
    changed = registration.producer(changed_fixture)
    assert changed.final_disposition == "AUTHORITY_BYPASS__FINDING_BLOCKED"
    assert changed.first_controlling_blocker != "NONE"
    assert changed.trace_integrity_state["claim_decision_reference_present"] is False


def test_claim_005_structural_rendering_class_mutation_changes_result(tmp_path: Path) -> None:
    registry = build_r5_pf3_adapter_registry()
    fixture = load_r5_manifest(_case_dir("FX-R5-CLAIM-005A"))
    registration = registry.require(fixture.manifest.execution.adapter_id)
    assert registration.producer is not None
    baseline = registration.producer(fixture)
    changed_fixture = _copy_with_mutation(
        tmp_path,
        "FX-R5-CLAIM-005A",
        lambda state: state["attempted_rendering"].update({"rendering_class": "descriptive"}),
    )
    changed = registration.producer(changed_fixture)
    assert changed.final_disposition != baseline.final_disposition
    assert changed.trace_integrity_state["rendering_matches_decision"] is True


@pytest.mark.parametrize("fixture_id", PF3_2_IDS[3:])
def test_each_causal_boundary_uses_lower_level_basis_and_missing_authority(
    fixture_id: str, tmp_path: Path
) -> None:
    registry = build_r5_pf3_adapter_registry()
    fixture = load_r5_manifest(_case_dir(fixture_id))
    registration = registry.require(fixture.manifest.execution.adapter_id)
    assert registration.producer is not None
    baseline = registration.producer(fixture)
    assert baseline.first_controlling_blocker != "NONE"
    assert baseline.trace_integrity_state["requested_claim_class"] == "causal"
    assert baseline.trace_integrity_state["causal_authority_reference_present"] is False

    def add_authority(state):
        authority = state["causal_authority_reference"]
        state["authority_records"].append(
            {
                **authority,
                "record_type": "causal_authority_reference",
            }
        )

    changed_fixture = _copy_with_mutation(tmp_path, fixture_id, add_authority)
    changed = registration.producer(changed_fixture)
    assert changed.final_disposition != baseline.final_disposition
    assert changed.final_disposition != "CAUSAL_SUPPORTED"
    assert changed.first_controlling_blocker == "NONE"
    assert changed.trace_integrity_state["causal_authority_reference_present"] is True
    assert changed.trace_integrity_state["causal_support_evaluated"] is False


def test_causal_boundary_rejects_non_causal_requested_claim_class(tmp_path: Path) -> None:
    registry = build_r5_pf3_adapter_registry()
    fixture = load_r5_manifest(_case_dir("FX-R5-CAUSE-001A"))
    registration = registry.require(fixture.manifest.execution.adapter_id)
    assert registration.producer is not None
    changed_fixture = _copy_with_mutation(
        tmp_path,
        "FX-R5-CAUSE-001A",
        lambda state: state["requested_claim"].update({"claim_class": "descriptive"}),
    )
    with pytest.raises(ControlledInputError, match="governed causal requested Claim class"):
        registration.producer(changed_fixture)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda state: state["authority_records"].append(
            {
                **state["causal_authority_reference"],
                "fingerprint": "a" * 64,
                "record_type": "causal_authority_reference",
            }
        ),
        lambda state: state["authority_records"].append(
            {
                **state["causal_authority_reference"],
                "version": "wrong_version",
                "record_type": "causal_authority_reference",
            }
        ),
    ],
    ids=["wrong-fingerprint", "wrong-version"],
)
def test_causal_authority_requires_exact_fingerprint_and_version(
    tmp_path: Path, mutate
) -> None:
    registry = build_r5_pf3_adapter_registry()
    fixture = load_r5_manifest(_case_dir("FX-R5-CAUSE-001A"))
    registration = registry.require(fixture.manifest.execution.adapter_id)
    assert registration.producer is not None
    baseline = registration.producer(fixture)
    changed_fixture = _copy_with_mutation(tmp_path, "FX-R5-CAUSE-001A", mutate)
    changed = registration.producer(changed_fixture)
    assert changed.final_disposition == baseline.final_disposition
    assert changed.first_controlling_blocker == baseline.first_controlling_blocker
    assert changed.trace_integrity_state["causal_authority_reference_present"] is False


def test_pf3_2_source_has_no_expected_fixture_scenario_or_fuzzy_oracle() -> None:
    module = __import__(
        "commerce_lens.fixture_runner.r5_pf3_adapters", fromlist=["r5_pf3_adapters"]
    )
    source = inspect.getsource(module)
    assert "manifest.expected" not in source
    assert "fixture.manifest.expected" not in source
    assert not re.search(r"\bFX-R5-[A-Z0-9-]+", source)
    assert not re.search(r"\bscenario\b", source, flags=re.IGNORECASE)
    assert not re.search(r"\b(llm|fuzzy|free[-_ ]?text)\b", source, flags=re.IGNORECASE)


def test_pf3_2_inventory_marks_exact_nine_executable() -> None:
    inventory = load_r5_inventory(ROOT)
    entries = {entry.fixture_id: entry for entry in inventory.active.entries}
    assert set(PF3_2_IDS).issubset(entries)
    assert all(entries[fixture_id].executable for fixture_id in PF3_2_IDS)
