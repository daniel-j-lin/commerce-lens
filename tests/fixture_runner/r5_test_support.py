from __future__ import annotations

from pathlib import Path

import yaml

from commerce_lens.fixture_runner.r5_adapters import AdapterRegistration
from commerce_lens.fixture_runner.r5_manifest import ActualProjection, ExecutionMode


def manifest_payload(
    *,
    fixture_id: str = "FX-R5-EVID-001A",
    family: str = "EVID",
    layer: str = "A",
    adapter_id: str = "dummy_exact",
    mode: str = "component_boundary",
) -> dict:
    return {
        "fixture_schema_version": "r5_pf0_v1",
        "fixture_id": fixture_id,
        "fixture_version": "1.0.0",
        "title": "PF0 mechanical harness case",
        "status": "ACTIVE",
        "family": family,
        "layer": layer,
        "purpose": "Exercise harness mechanics without CommerceLens semantics.",
        "primary_authority": {
            "document": "DIAGNOSTIC_SYNTHETIC_FIXTURE_SUITE_SPECIFICATION.md",
            "frozen_version": "R5 v1.0",
            "section": "§12",
            "controlling_rule": "PF0 test-only contract shape",
        },
        "supporting_authorities": [],
        "execution": {
            "mode": mode,
            "adapter_id": adapter_id,
            "required_capability": "pf0_dummy_subject",
            "required_capability_version": "1",
        },
        "inputs": [],
        "context": {
            "question_or_proposition": None,
            "execution_context": "test-only",
            "intended_use": "harness mechanics",
            "scope": None,
            "population": None,
            "periods": [],
            "currency": None,
        },
        "bindings": {},
        "expected": {
            "expectation_kind": "positive",
            "material_path": [
                {"stage": "execution", "chain_id": "main", "reachability": "reached", "outcome": {"state": "ready"}}
            ],
            "chain_dispositions": {"main": "ready"},
            "first_controlling_blocker": "NONE",
            "final_disposition": "ready",
            "permitted_meaning": ["test-only harness match"],
            "prohibited_meaning": ["CommerceLens analytical authority"],
            "trace_integrity_expectation": None,
            "unique_outcome_rationale": "Fixed dummy subject output either matches or does not match.",
        },
    }


def write_case(root: Path, payload: dict | None = None) -> Path:
    data = payload or manifest_payload()
    family = data["family"]
    case_dir = root / "active" / family / data["fixture_id"]
    case_dir.mkdir(parents=True)
    (case_dir / "manifest.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return case_dir


def fixed_actual(_fixture) -> ActualProjection:
    return ActualProjection.model_validate(
        {
            "material_path": [
                {"stage": "execution", "chain_id": "main", "reachability": "reached", "outcome": {"state": "ready"}}
            ],
            "chain_dispositions": {"main": "ready"},
            "first_controlling_blocker": "NONE",
            "final_disposition": "ready",
            "trace_integrity_state": None,
            "artifact_evidence_refs": [],
            "actual_output_producer": "tests.fixed_actual",
        }
    )


def mismatched_actual(_fixture) -> ActualProjection:
    return ActualProjection.model_validate(
        {
            "material_path": [
                {"stage": "execution", "chain_id": "main", "reachability": "reached", "outcome": {"state": "different"}}
            ],
            "chain_dispositions": {"main": "different"},
            "first_controlling_blocker": "NONE",
            "final_disposition": "different",
            "actual_output_producer": "tests.mismatched_actual",
        }
    )


def registration(adapter_id: str, producer, producer_name: str) -> AdapterRegistration:
    return AdapterRegistration(
        adapter_id=adapter_id,
        execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
        capability_name="pf0_dummy_subject",
        capability_version="1",
        actual_output_producer=producer_name,
        producer=producer,
    )
