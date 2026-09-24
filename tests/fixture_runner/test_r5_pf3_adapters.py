from __future__ import annotations

import hashlib
import inspect
import json
import re
from pathlib import Path

import pytest
import yaml

from commerce_lens.fixture_runner.r5_adapters import AdapterRegistry
from commerce_lens.fixture_runner.r5_manifest import ExecutionMode, load_r5_manifest
from commerce_lens.fixture_runner.r5_pf2_adapters import build_r5_pf2_adapter_registry
from commerce_lens.fixture_runner.r5_pf3_adapters import (
    CONTROLLED_PRODUCER_PREFIX,
    ControlledAuthorityGraph,
    ControlledInputError,
    ControlledReference,
    build_r5_pf3_adapter_registry,
    controlled_blocker,
    controlled_projection,
    controlled_stage,
    fingerprint_matches,
    load_controlled_json,
    load_controlled_object,
    load_controlled_text,
    reference_from_mapping,
    register_controlled_adapter,
    references_match,
    versions_match,
)
from tests.fixture_runner.r5_test_support import manifest_payload


def _controlled_case(tmp_path: Path):
    case = tmp_path / "active" / "CLAIM" / "FX-R5-CLAIM-003A"
    case.mkdir(parents=True)
    state = {"authority": {"id": "decision-1", "version": "p8_001_v1"}}
    state_bytes = json.dumps(state, sort_keys=True).encode("utf-8")
    (case / "state.json").write_bytes(state_bytes)
    (case / "utterance.txt").write_text("controlled form\n", encoding="utf-8")
    payload = manifest_payload(
        fixture_id="FX-R5-CLAIM-003A",
        family="CLAIM",
        layer="C",
        mode="controlled_case",
    )
    payload["inputs"] = [
        {
            "path": "state.json",
            "role": "authority_state",
            "media_type": "application/json",
            "sha256": hashlib.sha256(state_bytes).hexdigest(),
        },
        {
            "path": "utterance.txt",
            "role": "utterance",
            "media_type": "text/plain",
            "sha256": hashlib.sha256(b"controlled form\n").hexdigest(),
        },
    ]
    (case / "manifest.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )
    return load_r5_manifest(case)


def test_pf3_registry_extends_pf2_without_registering_family_cases() -> None:
    pf2 = build_r5_pf2_adapter_registry()
    pf3 = build_r5_pf3_adapter_registry()
    assert set(pf2.ids()).issubset(pf3.ids())
    assert set(pf3.ids()) - set(pf2.ids()) == {
        "controlled_diagnostic_admission",
        "controlled_alternative_evidence",
        "controlled_diagnostic_boundary",
        "controlled_narrowing_boundary",
        "controlled_claim_decision_boundary",
        "controlled_finding_authority",
        "controlled_claim_rendering",
        "controlled_causal_boundary",
        "controlled_version_boundary",
        "controlled_provenance_boundary",
        "controlled_chain_boundary",
        "controlled_precision_boundary",
        "controlled_language_corpus",
    }


def test_controlled_registration_requires_controlled_mode_and_namespace() -> None:
    registry = AdapterRegistry()

    def producer(_fixture):
        raise AssertionError("not executed")

    register_controlled_adapter(
        registry,
        adapter_id="controlled_test",
        capability_name="controlled_test_capability",
        capability_version="pf3_0_v1",
        actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}test",
        producer=producer,
    )
    registration = registry.require("controlled_test")
    assert registration.execution_mode is ExecutionMode.CONTROLLED_CASE
    assert registration.actual_output_producer == f"{CONTROLLED_PRODUCER_PREFIX}test"

    with pytest.raises(ControlledInputError, match="controlled namespace"):
        register_controlled_adapter(
            registry,
            adapter_id="wrong_namespace",
            capability_name="controlled_test_capability",
            capability_version="pf3_0_v1",
            actual_output_producer="commerce_lens.application.analysis_service.run_analysis",
            producer=producer,
        )


def test_controlled_inputs_are_loaded_by_verified_role_only(tmp_path) -> None:
    fixture = _controlled_case(tmp_path)
    assert load_controlled_object(fixture, "authority_state")["authority"]["id"] == "decision-1"
    assert load_controlled_text(fixture, "utterance") == "controlled form\n"
    with pytest.raises(ControlledInputError, match="not permitted"):
        load_controlled_json(fixture, "expected")
    with pytest.raises(ControlledInputError, match="exactly one"):
        load_controlled_json(fixture, "missing_role")


def test_controlled_reference_graph_and_identity_helpers() -> None:
    left = ControlledReference("decision-1", "a" * 64, "p8_001_v1")
    right = ControlledReference("decision-1", "a" * 64, "p8_001_v1")
    changed = ControlledReference("decision-1", "b" * 64, "p8_001_v1")
    graph = ControlledAuthorityGraph((left,))
    assert graph.require("decision-1") == left
    assert references_match(left, right)
    assert not references_match(left, changed)
    assert fingerprint_matches("controlled", hashlib.sha256(b"controlled").hexdigest())
    assert versions_match("v1", "v1")
    assert not versions_match("v1", "v2")

    with pytest.raises(ControlledInputError, match="absent"):
        graph.require("missing")
    with pytest.raises(ControlledInputError, match="duplicate"):
        ControlledAuthorityGraph((left, right)).require("decision-1")


def test_reference_parser_rejects_conclusion_valued_input() -> None:
    reference = reference_from_mapping(
        {"authority": {"id": "artifact-1", "fingerprint": "c" * 64, "version": "v1"}},
        field="authority",
    )
    assert reference.reference_id == "artifact-1"
    with pytest.raises(ControlledInputError, match="conclusion-valued"):
        reference_from_mapping({"authority": {"id": "artifact-1", "valid": False}}, field="authority")


def test_controlled_projection_requires_truthful_producer_and_validates_path() -> None:
    path = (
        controlled_stage("execution", "reached", "observed"),
        controlled_stage(
            "claim_decision",
            "blocked",
            "blocked",
            controlling_reason="authority_absent",
            authority_ref="R1 v1.0 §20",
        ),
        controlled_stage(
            "rendering",
            "not_reached",
            not_reached_due_to="claim_decision",
        ),
    )
    blocker = controlled_blocker(
        "claim_authority",
        "claim_decision",
        "authority_absent",
        "R1 v1.0 §20",
    )
    projection = controlled_projection(
        material_path=path,
        chain_dispositions={"main": "blocked"},
        first_controlling_blocker=blocker,
        final_disposition="CONTROLLED_BLOCKED",
        actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}claim_boundary",
    )
    assert projection.final_disposition == "CONTROLLED_BLOCKED"
    with pytest.raises(ControlledInputError, match="controlled namespace"):
        controlled_projection(
            material_path=path,
            chain_dispositions={"main": "blocked"},
            first_controlling_blocker=blocker,
            final_disposition="CONTROLLED_BLOCKED",
            actual_output_producer="production.authority",
        )


def test_controlled_projection_rejects_not_reached_without_prior_block() -> None:
    invalid_path = (
        controlled_stage("execution", "reached", "observed"),
        controlled_stage(
            "rendering",
            "not_reached",
            not_reached_due_to="claim_decision",
        ),
    )
    with pytest.raises(ValueError, match="not_reached_due_to"):
        controlled_projection(
            material_path=invalid_path,
            chain_dispositions={"main": "blocked"},
            first_controlling_blocker="NONE",
            final_disposition="INVALID",
            actual_output_producer=f"{CONTROLLED_PRODUCER_PREFIX}invalid_path",
        )


def test_pf3_infrastructure_has_no_expected_access_or_fixture_id_oracle() -> None:
    from commerce_lens.fixture_runner import r5_pf3_adapters

    source = inspect.getsource(r5_pf3_adapters)
    assert "manifest.expected" not in source
    assert "fixture.manifest.expected" not in source
    assert "EXPECTED_BY_FIXTURE_ID" not in source
    assert not re.search(r"\bFX-R5-[A-Z]+-\d{3}[A-Z]\b", source)
    assert "DIAGNOSTIC_SYNTHETIC_FIXTURE_SUITE_SPECIFICATION.md" not in source
