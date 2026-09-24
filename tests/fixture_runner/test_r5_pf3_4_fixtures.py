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
PF3_4_IDS = (
    "FX-R5-PREC-002A",
    "FX-R5-PREC-004A",
    "FX-R5-PREC-005A",
)


def _case_dir(fixture_id: str) -> Path:
    family = fixture_id.removeprefix("FX-R5-").split("-", 1)[0]
    return R5_ROOT / "active" / family / fixture_id


def _copy_with_mutation(tmp_path: Path, fixture_id: str, mutate):
    source = _case_dir(fixture_id)
    target = tmp_path / fixture_id
    shutil.copytree(source, target)
    manifest = yaml.safe_load((target / "manifest.yaml").read_text(encoding="utf-8"))
    input_spec = next(item for item in manifest["inputs"] if item["role"] == "precision_state")
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


def _producer(fixture_id: str):
    registry = build_r5_pf3_adapter_registry()
    fixture = load_r5_manifest(_case_dir(fixture_id))
    registration = registry.require(fixture.manifest.execution.adapter_id)
    assert registration.producer is not None
    return registry, fixture, registration.producer


def _walk_keys(value):
    if isinstance(value, dict):
        yield from value.keys()
        for child in value.values():
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def test_pf3_4_exact_three_controlled_cases_pass() -> None:
    registry = build_r5_pf3_adapter_registry()
    for fixture_id in PF3_4_IDS:
        fixture = load_r5_manifest(_case_dir(fixture_id))
        registration = registry.require(fixture.manifest.execution.adapter_id)
        assert fixture.manifest.execution.mode is ExecutionMode.CONTROLLED_CASE
        assert registration.execution_mode is ExecutionMode.CONTROLLED_CASE
        assert registration.producer is not None
        assert registration.actual_output_producer.startswith(CONTROLLED_PRODUCER_PREFIX)
        result = run_case_dir(_case_dir(fixture_id), registry)
        assert result.status is HarnessResultStatus.PASS
        assert result.mismatches == ()


def test_pf3_4_inputs_are_lower_level_facts_without_scenario_or_conclusions() -> None:
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
        "final_disposition",
        "chain_disposition",
    }
    for fixture_id in PF3_4_IDS:
        fixture = load_r5_manifest(_case_dir(fixture_id))
        for input_spec in fixture.manifest.inputs:
            if input_spec.media_type != "application/json":
                continue
            value = load_controlled_object(fixture, input_spec.role)
            keys = set(_walk_keys(value))
            assert "scenario" not in keys
            assert not forbidden.intersection(keys)


def test_prec002_derives_evidence_blocker_and_leaves_later_support_unreached() -> None:
    _, fixture, producer = _producer("FX-R5-PREC-002A")
    actual = producer(fixture)
    assert actual.final_disposition == "EVIDENCE_INADMISSIBLE__ANALYTICAL_SUPPORT_NOT_REACHED"
    assert actual.material_path[-1].not_reached_due_to.value == "evidence_admissibility"
    assert actual.artifact_evidence_refs == ("hypothetical_support_prec002",)
    assert actual.trace_integrity_state == {
        "status": "failed",
        "failure_code": "unsupported_claim_type_for_p6_001",
    }


def test_prec002_requested_use_mutation_changes_controlled_result(tmp_path: Path) -> None:
    _, fixture, producer = _producer("FX-R5-PREC-002A")
    baseline = producer(fixture)
    changed_fixture = _copy_with_mutation(
        tmp_path,
        "FX-R5-PREC-002A",
        lambda state: state["evidence_admissibility_request"]["requested_use"].update(
            {"claim_class": "descriptive"}
        ),
    )
    changed = producer(changed_fixture)
    assert changed.final_disposition != baseline.final_disposition
    assert changed.first_controlling_blocker == "NONE"


def test_prec002_controlling_authority_mutation_invalidates_path(tmp_path: Path) -> None:
    _, _, producer = _producer("FX-R5-PREC-002A")

    def mutate(state):
        state["evidence_admissibility_request"]["admissibility_authority_reference"][
            "fingerprint"
        ] = "d" * 64

    with pytest.raises(ControlledInputError, match="incomplete exact authority bindings"):
        producer(
            _copy_with_mutation(
                tmp_path, "FX-R5-PREC-002A", mutate
            )
        )


def test_prec002_later_assertion_mutation_cannot_displace_blocker(tmp_path: Path) -> None:
    _, fixture, producer = _producer("FX-R5-PREC-002A")
    baseline = producer(fixture)

    def mutate(state):
        request = state["evidence_admissibility_request"]
        request["later_support_assertion_reference"]["fingerprint"] = "c" * 64
        for record in request["authority_records"]:
            if record["record_type"] == "later_support_assertion":
                record["fingerprint"] = "c" * 64

    changed = producer(_copy_with_mutation(tmp_path, "FX-R5-PREC-002A", mutate))
    assert changed.final_disposition == baseline.final_disposition
    assert changed.first_controlling_blocker == baseline.first_controlling_blocker


def test_prec004_causal_class_and_evidence_binding_control_the_path(tmp_path: Path) -> None:
    _, fixture, producer = _producer("FX-R5-PREC-004A")
    baseline = producer(fixture)
    assert baseline.final_disposition == "CLAIM_PROHIBITED__ASSOCIATION_IS_NOT_CAUSATION"
    assert baseline.artifact_evidence_refs == ()
    changed = producer(
        _copy_with_mutation(
            tmp_path,
            "FX-R5-PREC-004A",
            lambda state: state["causal_request"]["requested_claim"].update(
                {"claim_class": "descriptive"}
            ),
        )
    )
    assert changed.final_disposition != baseline.final_disposition
    assert changed.first_controlling_blocker == "NONE"

    def wrong_evidence_fingerprint(state):
        state["causal_request"]["diagnostic_evidence_reference"]["fingerprint"] = "d" * 64

    with pytest.raises(ControlledInputError, match="incomplete exact evidence bindings"):
        producer(
            _copy_with_mutation(
                tmp_path / "mismatched-evidence", "FX-R5-PREC-004A", wrong_evidence_fingerprint
            )
        )


def test_prec004_authenticated_evidence_form_mismatch_fails_closed(tmp_path: Path) -> None:
    _, _, producer = _producer("FX-R5-PREC-004A")

    def mismatch(state):
        state["causal_request"]["authority_records"][0]["evidence_form"] = (
            "historical_transactional_correlation"
        )

    with pytest.raises(ControlledInputError, match="evidence kind disagrees"):
        producer(_copy_with_mutation(tmp_path, "FX-R5-PREC-004A", mismatch))


def test_prec005_external_dependency_controls_later_internal_defect(tmp_path: Path) -> None:
    _, fixture, producer = _producer("FX-R5-PREC-005A")
    baseline = producer(fixture)
    assert baseline.final_disposition == "EXTERNAL_EVIDENCE_REQUIRED"
    assert baseline.artifact_evidence_refs == ("later_internal_defect_prec005",)

    def resolve_dependency(state):
        dependency = state["external_dependency"]
        dependency["resolution_state"] = "resolved"
        for record in dependency["authority_records"]:
            if record["record_type"] == "external_dependency":
                record["resolution_state"] = "resolved"

    changed = producer(_copy_with_mutation(tmp_path, "FX-R5-PREC-005A", resolve_dependency))
    assert changed.final_disposition == "EXTERNAL_DEPENDENCY_RESOLVED__NEXT_STAGE_ONLY"
    assert changed.first_controlling_blocker == "NONE"


@pytest.mark.parametrize(
    ("declared_state", "record_state"),
    [("resolved", "unresolved"), ("unresolved", "resolved")],
    ids=["declared-resolved-record-unresolved", "declared-unresolved-record-resolved"],
)
def test_prec005_declared_state_must_match_authenticated_record(
    tmp_path: Path, declared_state: str, record_state: str
) -> None:
    _, _, producer = _producer("FX-R5-PREC-005A")

    def mismatch(state):
        dependency = state["external_dependency"]
        dependency["resolution_state"] = declared_state
        for record in dependency["authority_records"]:
            if record["record_type"] == "external_dependency":
                record["resolution_state"] = record_state

    with pytest.raises(ControlledInputError, match="disagrees with authenticated"):
        producer(_copy_with_mutation(tmp_path, "FX-R5-PREC-005A", mismatch))


def test_prec005_later_internal_defect_mutation_cannot_displace_external_blocker(
    tmp_path: Path,
) -> None:
    _, fixture, producer = _producer("FX-R5-PREC-005A")
    baseline = producer(fixture)
    changed = producer(
        _copy_with_mutation(
            tmp_path,
            "FX-R5-PREC-005A",
            lambda state: state["external_dependency"]["authority_records"][2].update(
                {"defect_kind": "different_internal_issue"}
            ),
        )
    )
    assert changed.final_disposition == baseline.final_disposition
    assert changed.first_controlling_blocker == baseline.first_controlling_blocker


def test_pf3_4_duplicate_exact_authority_records_fail_closed(tmp_path: Path) -> None:
    cases = (
        ("FX-R5-PREC-002A", "evidence_admissibility_authority"),
        ("FX-R5-PREC-004A", "diagnostic_evidence"),
        ("FX-R5-PREC-005A", "external_dependency"),
    )
    for fixture_id, record_type in cases:
        def duplicate(state, record_type=record_type):
            key = next(key for key in state if key in {"evidence_admissibility_request", "causal_request", "external_dependency"})
            records = state[key]["authority_records"]
            records.append(dict(next(item for item in records if item["record_type"] == record_type)))

        _, _, producer = _producer(fixture_id)
        with pytest.raises(ControlledInputError, match="ambiguous exact PF3 authority binding"):
            producer(_copy_with_mutation(tmp_path, fixture_id, duplicate))


def test_pf3_4_authority_record_order_does_not_change_result(tmp_path: Path) -> None:
    for fixture_id in PF3_4_IDS:
        _, fixture, producer = _producer(fixture_id)
        baseline = producer(fixture)
        changed = producer(
            _copy_with_mutation(
                tmp_path,
                fixture_id,
                lambda state: next(
                    state[key] for key in state if key in {"evidence_admissibility_request", "causal_request", "external_dependency"}
                )["authority_records"].reverse(),
            )
        )
        assert changed == baseline


def test_prec005_independent_simultaneous_blocker_fails_closed(tmp_path: Path) -> None:
    _, _, producer = _producer("FX-R5-PREC-005A")

    def add_independent_blocker(state):
        dependency = state["external_dependency"]
        reference = {
            "id": "independent_stage_prec005",
            "fingerprint": "e" * 64,
            "version": "independent_v1",
        }
        dependency["independent_stage_reference"] = reference
        dependency["authority_records"].append(
            {"record_type": "independent_stage", **reference}
        )

    with pytest.raises(ControlledInputError, match="no governed precedence"):
        producer(_copy_with_mutation(tmp_path, "FX-R5-PREC-005A", add_independent_blocker))


def test_pf3_4_source_has_no_oracle_authority() -> None:
    module = __import__(
        "commerce_lens.fixture_runner.r5_pf3_adapters", fromlist=["r5_pf3_adapters"]
    )
    source = inspect.getsource(module)
    assert "manifest.expected" not in source
    assert "fixture.manifest.expected" not in source
    assert not re.search(r"\bFX-R5-[A-Z0-9-]+", source)
    assert not re.search(r"\bscenario\b", source, flags=re.IGNORECASE)
    assert not re.search(r"\b(llm|fuzzy|free[-_ ]?text)\b", source, flags=re.IGNORECASE)


def test_pf3_4_inventory_marks_exact_three_executable() -> None:
    inventory = load_r5_inventory(ROOT)
    entries = {entry.fixture_id: entry for entry in inventory.active.entries}
    assert set(PF3_4_IDS).issubset(entries)
    assert all(entries[fixture_id].executable for fixture_id in PF3_4_IDS)
