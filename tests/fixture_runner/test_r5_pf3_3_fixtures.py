from __future__ import annotations

import hashlib
import inspect
import json
import re
import shutil
from pathlib import Path

import pytest
import yaml

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
PF3_3_IDS = (
    "FX-R5-VERSION-007A",
    "FX-R5-VERSION-008A",
    "FX-R5-VERSION-009A",
    "FX-R5-VERSION-010A",
    "FX-R5-PROV-006A",
    "FX-R5-PROV-007A",
    "FX-R5-CHAIN-002A",
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


def test_pf3_3_exact_seven_controlled_cases_pass() -> None:
    registry = build_r5_pf3_adapter_registry()
    for fixture_id in PF3_3_IDS:
        fixture = load_r5_manifest(_case_dir(fixture_id))
        registration = registry.require(fixture.manifest.execution.adapter_id)
        assert fixture.manifest.execution.mode is ExecutionMode.CONTROLLED_CASE
        assert registration.execution_mode is ExecutionMode.CONTROLLED_CASE
        assert registration.producer is not None
        assert registration.actual_output_producer.startswith(CONTROLLED_PRODUCER_PREFIX)
        result = run_case_dir(_case_dir(fixture_id), registry)
        assert result.status is HarnessResultStatus.PASS
        assert result.mismatches == ()


def test_pf3_3_inputs_contain_lower_level_facts_only() -> None:
    forbidden = {
        "expected",
        "outcome",
        "disposition",
        "blocker",
        "final",
        "valid",
        "admissible",
        "chain_valid",
        "continuity_ok",
        "provenance_valid",
        "version_valid",
        "support_evaluated",
        "causal_support_evaluated",
        "diagnostic_support_evaluated",
        "final_disposition",
        "chain_disposition",
    }
    for fixture_id in PF3_3_IDS:
        fixture = load_r5_manifest(_case_dir(fixture_id))
        for input_spec in fixture.manifest.inputs:
            value = load_controlled_object(fixture, input_spec.role)
            assert not forbidden.intersection(_walk_keys(value))


def test_version_007_exact_historical_binding_changes_result(tmp_path: Path) -> None:
    registry = build_r5_pf3_adapter_registry()
    fixture = load_r5_manifest(_case_dir("FX-R5-VERSION-007A"))
    producer = registry.require("controlled_version_boundary").producer
    assert producer is not None
    baseline = producer(fixture)

    def restore_historical_authority(state):
        historical = state["historical_binding"]["authority_reference"]
        state["current_binding"]["authority_reference"] = dict(historical)
        state["authority_records"][1].update(historical)

    changed = producer(
        _copy_with_mutation(tmp_path, "FX-R5-VERSION-007A", restore_historical_authority)
    )
    assert baseline.final_disposition == "NON_CONFORMING_HISTORICAL_REWRITE"
    assert changed.final_disposition != baseline.final_disposition
    assert changed.first_controlling_blocker == "NONE"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda state: state["lookup_request"].update({"resolution_mode": "exact"}),
        lambda state: state["resolved_authority_reference"].update({"fingerprint": "a" * 64}),
        lambda state: state["resolved_authority_reference"].update({"version": "stale_v0"}),
    ],
    ids=["exact-restore", "wrong-fingerprint", "wrong-version"],
)
def test_version_008_requires_exact_version_and_fingerprint_binding(tmp_path: Path, mutate) -> None:
    registry = build_r5_pf3_adapter_registry()
    fixture = load_r5_manifest(_case_dir("FX-R5-VERSION-008A"))
    producer = registry.require("controlled_version_boundary").producer
    assert producer is not None
    baseline = producer(fixture)
    changed = producer(_copy_with_mutation(tmp_path, "FX-R5-VERSION-008A", mutate))
    if changed.trace_integrity_state["resolution_mode"] == "exact":
        assert changed.final_disposition != baseline.final_disposition
        assert changed.first_controlling_blocker == "NONE"
    else:
        assert changed.final_disposition == baseline.final_disposition
        assert changed.trace_integrity_state["exact_binding_resolved"] is False


def test_version_duplicate_exact_authority_record_fails_closed(tmp_path: Path) -> None:
    registry = build_r5_pf3_adapter_registry()
    fixture_id = "FX-R5-VERSION-008A"
    producer = registry.require("controlled_version_boundary").producer
    assert producer is not None

    def add_duplicate_exact_authority(state):
        state["lookup_request"]["resolution_mode"] = "exact"
        state["authority_records"].append(dict(state["authority_records"][0]))

    changed_fixture = _copy_with_mutation(tmp_path, fixture_id, add_duplicate_exact_authority)
    with pytest.raises(ControlledInputError, match="ambiguous exact PF3 authority binding"):
        producer(changed_fixture)


def test_version_009_claimdecision_version_binding_changes_result(tmp_path: Path) -> None:
    registry = build_r5_pf3_adapter_registry()
    fixture = load_r5_manifest(_case_dir("FX-R5-VERSION-009A"))
    producer = registry.require("controlled_version_boundary").producer
    assert producer is not None
    baseline = producer(fixture)

    def bind_requested_proposition(state):
        decision = state["authority_records"][0]["proposition"]
        state["requested_claim"]["proposition"] = dict(decision)

    changed = producer(
        _copy_with_mutation(tmp_path, "FX-R5-VERSION-009A", bind_requested_proposition)
    )
    assert changed.final_disposition != baseline.final_disposition
    assert changed.first_controlling_blocker == "NONE"


def test_version_010_current_derivation_wins_over_stale_cache(tmp_path: Path) -> None:
    registry = build_r5_pf3_adapter_registry()
    fixture = load_r5_manifest(_case_dir("FX-R5-VERSION-010A"))
    producer = registry.require("controlled_version_boundary").producer
    assert producer is not None
    baseline = producer(fixture)
    changed = producer(
        _copy_with_mutation(
            tmp_path,
            "FX-R5-VERSION-010A",
            lambda state: state["cached_derivation"].update(
                {"input_fingerprint": state["current_evaluation_reference"]["fingerprint"]}
            ),
        )
    )
    assert changed.final_disposition != baseline.final_disposition
    assert changed.first_controlling_blocker == "NONE"


@pytest.mark.parametrize("fixture_id", ["FX-R5-PROV-006A", "FX-R5-PROV-007A"])
def test_provenance_requires_retained_source_and_exact_linkage(tmp_path: Path, fixture_id: str) -> None:
    registry = build_r5_pf3_adapter_registry()
    fixture = load_r5_manifest(_case_dir(fixture_id))
    producer = registry.require("controlled_provenance_boundary").producer
    assert producer is not None
    baseline = producer(fixture)

    def restore_retained_artifact_binding(state):
        artifact = dict(state["required_retained_artifact_reference"])
        state["source_kind"] = "retained_artifact"
        state["source_reference"] = artifact
        state["provenance_link"]["source_reference"] = dict(artifact)
        state["authority_records"].extend(
            [
                {"record_type": "source_reference", **artifact},
                {"record_type": "retained_artifact", **artifact},
            ]
        )

    changed = producer(_copy_with_mutation(tmp_path, fixture_id, restore_retained_artifact_binding))
    assert changed.final_disposition != baseline.final_disposition
    assert changed.final_disposition == "RETAINED_PROVENANCE_BINDING__NEXT_STAGE_ONLY"
    assert changed.first_controlling_blocker == "NONE"


def test_provenance_broken_reference_does_not_resolve_retained_binding(tmp_path: Path) -> None:
    registry = build_r5_pf3_adapter_registry()
    fixture_id = "FX-R5-PROV-006A"
    producer = registry.require("controlled_provenance_boundary").producer
    assert producer is not None

    def retained_but_broken_link(state):
        artifact = dict(state["required_retained_artifact_reference"])
        state["source_kind"] = "retained_artifact"
        state["source_reference"] = artifact
        state["provenance_link"]["source_reference"] = {
            **artifact,
            "fingerprint": "d" * 64,
        }
        state["authority_records"].extend(
            [
                {"record_type": "source_reference", **artifact},
                {"record_type": "retained_artifact", **artifact},
            ]
        )

    changed = producer(_copy_with_mutation(tmp_path, fixture_id, retained_but_broken_link))
    assert changed.final_disposition == "PROVENANCE_LINKAGE_MISMATCH__BLOCKED"
    assert changed.first_controlling_blocker != "NONE"


def test_chain_exact_stage_link_restore_changes_only_affected_chain(tmp_path: Path) -> None:
    registry = build_r5_pf3_adapter_registry()
    fixture_id = "FX-R5-CHAIN-002A"
    producer = registry.require("controlled_chain_boundary").producer
    assert producer is not None
    baseline = producer(load_r5_manifest(_case_dir(fixture_id)))

    def restore_diagnostic_link(state):
        required = state["diagnostic_chain"]["required_profile_reference"]
        state["stage_links"][0]["reference"] = dict(required)

    changed = producer(_copy_with_mutation(tmp_path, fixture_id, restore_diagnostic_link))
    assert baseline.trace_integrity_state["diagnostic_chain_continuity"] is False
    assert changed.trace_integrity_state["diagnostic_chain_continuity"] is True
    assert changed.final_disposition != baseline.final_disposition
    assert changed.first_controlling_blocker == "NONE"
    assert changed.chain_dispositions["revenue_change_descriptive"] == "descriptive_claim_renderable"


def test_chain_simultaneous_blockers_fail_closed_without_cross_chain_precedence(
    tmp_path: Path,
) -> None:
    registry = build_r5_pf3_adapter_registry()
    fixture_id = "FX-R5-CHAIN-002A"
    producer = registry.require("controlled_chain_boundary").producer
    assert producer is not None

    def break_descriptive_link(state):
        state["stage_links"][1]["reference"]["fingerprint"] = "e" * 64
        state["stage_links"][2]["reference"]["version"] = "stale_v0"

    changed = _copy_with_mutation(tmp_path, fixture_id, break_descriptive_link)
    with pytest.raises(ControlledInputError, match="no governed precedence"):
        producer(changed)


def test_chain_isolated_descriptive_blocker_remains_local(tmp_path: Path) -> None:
    registry = build_r5_pf3_adapter_registry()
    fixture_id = "FX-R5-CHAIN-002A"
    producer = registry.require("controlled_chain_boundary").producer
    assert producer is not None

    def restore_diagnostic_then_break_descriptive(state):
        state["stage_links"][0]["reference"] = dict(
            state["diagnostic_chain"]["required_profile_reference"]
        )
        state["stage_links"][1]["reference"]["fingerprint"] = "e" * 64
        state["stage_links"][2]["reference"]["version"] = "stale_v0"

    changed = producer(
        _copy_with_mutation(tmp_path, fixture_id, restore_diagnostic_then_break_descriptive)
    )
    assert changed.trace_integrity_state["diagnostic_chain_continuity"] is True
    assert changed.trace_integrity_state["descriptive_chain_continuity"] is False
    assert changed.first_controlling_blocker.chain_id == "revenue_change_descriptive"
    assert changed.final_disposition == "CHAIN_LINKAGE_BLOCKED__AFFECTED_CHAIN_WITHHELD"


def test_chain_duplicate_exact_authority_record_fails_closed(tmp_path: Path) -> None:
    registry = build_r5_pf3_adapter_registry()
    fixture_id = "FX-R5-CHAIN-002A"
    producer = registry.require("controlled_chain_boundary").producer
    assert producer is not None

    def add_duplicate_profile_record(state):
        state["authority_records"].append(dict(state["authority_records"][0]))

    changed_fixture = _copy_with_mutation(tmp_path, fixture_id, add_duplicate_profile_record)
    with pytest.raises(ControlledInputError, match="ambiguous exact PF3 authority binding"):
        producer(changed_fixture)


def test_chain_duplicate_exact_stage_link_fails_closed(tmp_path: Path) -> None:
    registry = build_r5_pf3_adapter_registry()
    fixture_id = "FX-R5-CHAIN-002A"
    producer = registry.require("controlled_chain_boundary").producer
    assert producer is not None

    def add_duplicate_rendering_link(state):
        state["stage_links"].append(dict(state["stage_links"][2]))

    changed_fixture = _copy_with_mutation(tmp_path, fixture_id, add_duplicate_rendering_link)
    with pytest.raises(ControlledInputError, match="ambiguous exact PF3 stage link"):
        producer(changed_fixture)


def test_pf3_3_source_has_no_expected_fixture_scenario_or_fuzzy_oracle() -> None:
    module = __import__(
        "commerce_lens.fixture_runner.r5_pf3_adapters", fromlist=["r5_pf3_adapters"]
    )
    source = inspect.getsource(module)
    assert "manifest.expected" not in source
    assert "fixture.manifest.expected" not in source
    assert not re.search(r"\bFX-R5-[A-Z0-9-]+", source)
    assert not re.search(r"\bscenario\b", source, flags=re.IGNORECASE)
    assert not re.search(r"\b(llm|fuzzy|free[-_ ]?text)\b", source, flags=re.IGNORECASE)


def test_pf3_3_inventory_marks_exact_seven_executable() -> None:
    from commerce_lens.fixture_runner.r5_inventory import load_r5_inventory

    inventory = load_r5_inventory(ROOT)
    entries = {entry.fixture_id: entry for entry in inventory.active.entries}
    assert set(PF3_3_IDS).issubset(entries)
    assert all(entries[fixture_id].executable for fixture_id in PF3_3_IDS)
