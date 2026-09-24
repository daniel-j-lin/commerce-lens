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
LANG_IDS = (
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
)


def _case_dir(fixture_id: str) -> Path:
    return R5_ROOT / "active" / "LANG" / fixture_id


def _copy_with_mutation(
    tmp_path: Path,
    fixture_id: str,
    *,
    mutate_utterance=None,
    mutate_state=None,
) -> object:
    target = tmp_path / fixture_id
    shutil.copytree(_case_dir(fixture_id), target)
    manifest = yaml.safe_load((target / "manifest.yaml").read_text(encoding="utf-8"))
    for input_spec in manifest["inputs"]:
        path = target / input_spec["path"]
        if input_spec["role"] == "utterance" and mutate_utterance is not None:
            text = path.read_text(encoding="utf-8")
            text = mutate_utterance(text)
            path.write_text(text, encoding="utf-8")
        elif input_spec["role"] == "language_state" and mutate_state is not None:
            state = json.loads(path.read_text(encoding="utf-8"))
            mutate_state(state)
            raw = json.dumps(state, indent=2, sort_keys=True).encode("utf-8") + b"\n"
            path.write_bytes(raw)
        input_spec["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
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
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def test_pf3_5_exact_fourteen_controlled_cases_pass() -> None:
    registry = build_r5_pf3_adapter_registry()
    assert len(LANG_IDS) == 14
    for fixture_id in LANG_IDS:
        fixture = load_r5_manifest(_case_dir(fixture_id))
        registration = registry.require(fixture.manifest.execution.adapter_id)
        assert fixture.manifest.execution.mode is ExecutionMode.CONTROLLED_CASE
        assert registration.execution_mode is ExecutionMode.CONTROLLED_CASE
        assert registration.actual_output_producer.startswith(CONTROLLED_PRODUCER_PREFIX)
        result = run_case_dir(_case_dir(fixture_id), registry)
        assert result.status is HarnessResultStatus.PASS, result.mismatches
        assert result.mismatches == ()


def test_lang014_remains_outside_pf3_5_controlled_corpus() -> None:
    manifest = load_r5_manifest(_case_dir("FX-R5-LANG-014A"))
    assert manifest.manifest.execution.adapter_id != "controlled_language_corpus"


def test_pf3_5_inputs_are_lower_level_facts_only() -> None:
    forbidden = {
        "scenario",
        "expected",
        "outcome",
        "disposition",
        "blocker",
        "final",
        "valid",
        "admissible",
        "classification",
        "semantic_label",
        "fixture_outcome",
    }
    for fixture_id in LANG_IDS:
        fixture = load_r5_manifest(_case_dir(fixture_id))
        for input_spec in fixture.manifest.inputs:
            if input_spec.media_type != "application/json":
                continue
            keys = set(_walk_keys(load_controlled_object(fixture, input_spec.role)))
            assert not forbidden.intersection(keys), (fixture_id, keys)


def test_pf3_5_source_has_no_oracle_or_nlp_authority() -> None:
    from commerce_lens.fixture_runner import r5_pf3_adapters

    source = inspect.getsource(r5_pf3_adapters)
    assert not re.search(r"\bFX-R5-[A-Z0-9-]+", source)
    assert "manifest.expected" not in source
    assert "fixture.manifest.expected" not in source
    assert "EXPECTED_BY_FIXTURE_ID" not in source
    assert "scenario" not in source
    lowered = source.lower()
    for forbidden in ("llm", "embedding", "fuzzy", "keyword", "substring", "normalize"):
        assert forbidden not in lowered


@pytest.mark.parametrize(
    "mutation",
    [
        pytest.param(lambda text: text[:-1] + " \n", id="trailing-space"),
        pytest.param(lambda text: " " + text, id="leading-space"),
        pytest.param(lambda text: text.replace("Revenue", "revenue", 1), id="capitalization"),
    ],
)
def test_unknown_or_loosely_changed_utterance_does_not_inherit_baseline(
    tmp_path: Path, mutation
) -> None:
    _, _, producer = _producer("FX-R5-LANG-001A")
    changed = producer(
        _copy_with_mutation(tmp_path, "FX-R5-LANG-001A", mutate_utterance=mutation)
    )
    assert changed.final_disposition == "CONTROLLED_LANGUAGE_FORM_UNRECOGNIZED"
    assert changed.first_controlling_blocker != "NONE"


@pytest.mark.parametrize("fixture_id", LANG_IDS)
def test_each_language_form_rejects_an_unregistered_alternate(
    tmp_path: Path, fixture_id: str
) -> None:
    _, fixture, producer = _producer(fixture_id)
    baseline = producer(fixture)
    changed = producer(
        _copy_with_mutation(
            tmp_path,
            fixture_id,
            mutate_utterance=lambda text: text[:-2] + "?\n",
        )
    )
    assert changed.final_disposition == "CONTROLLED_LANGUAGE_FORM_UNRECOGNIZED"
    assert changed.final_disposition != baseline.final_disposition


def test_valid_authority_does_not_rescue_mutated_utterance(tmp_path: Path) -> None:
    _, _, producer = _producer("FX-R5-LANG-009A")
    changed = producer(
        _copy_with_mutation(
            tmp_path,
            "FX-R5-LANG-009A",
            mutate_utterance=lambda text: text.replace("declined", "fell", 1),
        )
    )
    assert changed.final_disposition == "CONTROLLED_LANGUAGE_FORM_UNRECOGNIZED"


def test_authority_state_mutations_block_language_forms(tmp_path: Path) -> None:
    cases = (
        (
            "FX-R5-LANG-009A",
            lambda state: next(
                record for record in state["authority_records"]
                if record["record_type"] == "claim_decision"
            ).update({"claim_class": "causal"}),
        ),
        (
            "FX-R5-LANG-010A",
            lambda state: state["authority_records"][0].update(
                {"method_kind": "other_method"}
            ),
        ),
        (
            "FX-R5-LANG-011A",
            lambda state: state["authority_records"][0].update(
                {"hypothesis_form": "unsupported_free_text"}
            ),
        ),
        (
            "FX-R5-LANG-015A",
            lambda state: state["authority_records"][0].update(
                {"resolution_state": "resolved"}
            ),
        ),
        (
            "FX-R5-LANG-016A",
            lambda state: state["requested_claim"].update({"claim_class": "descriptive"}),
        ),
    )
    for index, (fixture_id, mutation) in enumerate(cases):
        _, _, producer = _producer(fixture_id)
        changed = producer(
            _copy_with_mutation(tmp_path / str(index), fixture_id, mutate_state=mutation)
        )
        assert changed.final_disposition == "CONTROLLED_LANGUAGE_AUTHORITY_REQUIRED__BLOCKED"
        assert changed.first_controlling_blocker != "NONE"


def test_duplicate_exact_authority_records_fail_closed(tmp_path: Path) -> None:
    _, _, producer = _producer("FX-R5-LANG-009A")

    def duplicate(state):
        record = next(
            record
            for record in state["authority_records"]
            if record["record_type"] == "claim_decision"
        )
        state["authority_records"].append(dict(record))

    with pytest.raises(ControlledInputError, match="ambiguous exact PF3 authority binding"):
        producer(
            _copy_with_mutation(
                tmp_path / "duplicate", "FX-R5-LANG-009A", mutate_state=duplicate
            )
        )


def test_authority_record_order_does_not_change_result(tmp_path: Path) -> None:
    _, fixture, producer = _producer("FX-R5-LANG-009A")
    baseline = producer(fixture)

    def reverse(state):
        state["authority_records"].reverse()

    changed = producer(
        _copy_with_mutation(
            tmp_path / "reordered", "FX-R5-LANG-009A", mutate_state=reverse
        )
    )
    assert changed.model_dump(mode="json") == baseline.model_dump(mode="json")


def test_repeated_language_production_is_deterministic() -> None:
    for fixture_id in LANG_IDS:
        _, fixture, producer = _producer(fixture_id)
        assert producer(fixture).model_dump(mode="json") == producer(fixture).model_dump(mode="json")
