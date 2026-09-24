from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from commerce_lens.fixture_runner.r5_manifest import (
    FROZEN_AUTHORITY_VERSIONS,
    MAX_YAML_BYTES,
    R5_ACTIVE_ID_PATTERN,
    R5_DEFERRED_ID_PATTERN,
    R5FixtureManifest,
    R5ManifestError,
    load_r5_manifest,
    safe_load_yaml_mapping,
)
from tests.fixture_runner.r5_test_support import manifest_payload, write_case


def test_identity_patterns_reject_malformed_and_unknown_family() -> None:
    assert R5_ACTIVE_ID_PATTERN.fullmatch("FX-R5-R4-001A")
    assert R5_DEFERRED_ID_PATTERN.fullmatch("DF-R5-R4-001")
    assert R5_ACTIVE_ID_PATTERN.fullmatch("FX-R5-NOPE-001A") is None
    assert R5_ACTIVE_ID_PATTERN.fullmatch("FX-R5-R4-1A") is None
    assert R5_DEFERRED_ID_PATTERN.fullmatch("DF-R5-EVID-001A") is None


@pytest.mark.parametrize("field", ["title", "purpose", "primary_authority", "expected"])
def test_manifest_rejects_missing_required_field(field) -> None:
    payload = manifest_payload()
    payload.pop(field)
    with pytest.raises(ValueError):
        R5FixtureManifest.model_validate(payload)


def test_manifest_rejects_extra_or_executable_fields() -> None:
    payload = manifest_payload()
    payload["python_import"] = "os.system"
    payload["execution"]["shell_command"] = "echo unsafe"
    with pytest.raises(ValueError, match="extra_forbidden"):
        R5FixtureManifest.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    (("status", "DEFERRED"), ("family", "UNKNOWN"), ("layer", "C")),
)
def test_manifest_rejects_invalid_status_family_or_layer(field, value) -> None:
    payload = manifest_payload()
    payload[field] = value
    with pytest.raises(ValueError):
        R5FixtureManifest.model_validate(payload)


def test_manifest_rejects_unknown_authority_document() -> None:
    payload = manifest_payload()
    payload["primary_authority"]["document"] = "INVENTORY_IS_NOT_AUTHORITY.md"
    with pytest.raises(ValueError, match="not allowlisted"):
        R5FixtureManifest.model_validate(payload)


def test_frozen_authority_version_mapping_and_all_exact_pairs() -> None:
    assert dict(FROZEN_AUTHORITY_VERSIONS) == {
        "PROJECT_MASTER_INSTRUCTIONS.md": "v1.1",
        "SKILL_SCOPE_SPECIFICATION.md": "v1.0",
        "EVIDENCE_CONTRACT_SPECIFICATION.md": "v1.0",
        "ARCHITECTURE_SPECIFICATION.md": "v1.0",
        "CANONICAL_DATASET_AND_METRIC_DICTIONARY.md": "v1.0",
        "EVALUATION_FIXTURES_SPECIFICATION.md": "v1.0",
        "DIAGNOSTIC_REASONING_SPECIFICATION.md": "R1 v1.0",
        "HYPOTHESIS_FINDING_STATE_MODEL_SPECIFICATION.md": "R2 v1.0",
        "REQUIRED_EVIDENCE_MATRIX_SPECIFICATION.md": "R3 v1.0",
        "DETERMINISTIC_REVENUE_DECOMPOSITION_SPECIFICATION.md": "R4 v1.0",
        "DIAGNOSTIC_SYNTHETIC_FIXTURE_SUITE_SPECIFICATION.md": "R5 v1.0",
    }
    for document, version in FROZEN_AUTHORITY_VERSIONS.items():
        payload = manifest_payload()
        payload["primary_authority"].update({"document": document, "frozen_version": version})
        assert R5FixtureManifest.model_validate(payload).primary_authority.frozen_version == version


@pytest.mark.parametrize(
    ("document", "incorrect_version"),
    [
        ("DETERMINISTIC_REVENUE_DECOMPOSITION_SPECIFICATION.md", "R4 v999"),
        ("DIAGNOSTIC_SYNTHETIC_FIXTURE_SUITE_SPECIFICATION.md", "R4 v1.0"),
    ],
)
def test_manifest_rejects_authority_version_binding_mismatch(document, incorrect_version) -> None:
    payload = manifest_payload()
    payload["primary_authority"].update({"document": document, "frozen_version": incorrect_version})
    with pytest.raises(ValueError, match="authority-version binding mismatch"):
        R5FixtureManifest.model_validate(payload)


@pytest.mark.parametrize("blank_version", ["", "   "])
def test_manifest_rejects_blank_authority_version(blank_version) -> None:
    payload = manifest_payload()
    payload["primary_authority"]["frozen_version"] = blank_version
    with pytest.raises(ValueError):
        R5FixtureManifest.model_validate(payload)


def test_manifest_rejects_malformed_authority_section_and_execution_url() -> None:
    payload = manifest_payload()
    payload["primary_authority"]["section"] = "chapter twelve"
    with pytest.raises(ValueError, match="section-sign"):
        R5FixtureManifest.model_validate(payload)
    payload = manifest_payload()
    payload["execution"]["required_capability"] = "https://example.invalid/execute"
    with pytest.raises(ValueError, match="cannot be a URL"):
        R5FixtureManifest.model_validate(payload)


def test_negative_requires_blocker_and_positive_requires_none() -> None:
    negative = manifest_payload()
    negative["expected"]["expectation_kind"] = "negative"
    with pytest.raises(ValueError, match="explicit first blocker"):
        R5FixtureManifest.model_validate(negative)
    positive = manifest_payload()
    positive["expected"]["first_controlling_blocker"] = _blocker()
    with pytest.raises(ValueError, match="requires first_controlling_blocker=NONE"):
        R5FixtureManifest.model_validate(positive)


def test_material_path_rejects_unknown_stage_and_invalid_reachability() -> None:
    payload = manifest_payload()
    payload["expected"]["material_path"][0]["stage"] = "invented_stage"
    payload["expected"]["material_path"][0]["reachability"] = "maybe"
    with pytest.raises(ValueError):
        R5FixtureManifest.model_validate(payload)


def test_not_reached_rejects_fabricated_outcome_and_requires_cause() -> None:
    payload = manifest_payload()
    stage = payload["expected"]["material_path"][0]
    stage.update({"reachability": "not_reached", "outcome": {"fabricated": True}})
    with pytest.raises(ValueError, match="fabricated outcome"):
        R5FixtureManifest.model_validate(payload)


def test_blocked_stage_requires_reason_and_authority() -> None:
    payload = manifest_payload()
    stage = payload["expected"]["material_path"][0]
    stage.update({"reachability": "blocked", "outcome": "blocked"})
    with pytest.raises(ValueError, match="controlling_reason"):
        R5FixtureManifest.model_validate(payload)


def test_blocked_chain_rejects_fabricated_downstream_reached_state() -> None:
    payload = manifest_payload()
    payload["expected"].update(
        {
            "expectation_kind": "negative",
            "first_controlling_blocker": _blocker(),
            "material_path": [
                {
                    "stage": "validation",
                    "chain_id": "main",
                    "reachability": "blocked",
                    "outcome": "failed",
                    "controlling_reason": "test-only blocker",
                    "authority_ref": "R5 §12",
                },
                {
                    "stage": "claim_decision",
                    "chain_id": "main",
                    "reachability": "reached",
                    "outcome": "fabricated",
                },
            ],
        }
    )
    with pytest.raises(ValueError, match="after it is blocked"):
        R5FixtureManifest.model_validate(payload)


def test_not_reached_accepts_same_chain_earlier_blocker() -> None:
    payload = _path_payload([_blocked_stage(), _not_reached_stage()])
    assert R5FixtureManifest.model_validate(payload).expected.material_path[1].not_reached_due_to.value == "validation"


def test_not_reached_rejects_missing_referenced_blocker() -> None:
    payload = _path_payload([_not_reached_stage()])
    with pytest.raises(ValueError, match="earlier BLOCKED stage in the same material chain"):
        R5FixtureManifest.model_validate(payload)


def test_not_reached_rejects_referenced_stage_that_is_reached() -> None:
    reached_validation = {"stage": "validation", "reachability": "reached", "outcome": "valid"}
    payload = _path_payload([reached_validation, _not_reached_stage()])
    with pytest.raises(ValueError, match="earlier BLOCKED stage in the same material chain"):
        R5FixtureManifest.model_validate(payload)


def test_not_reached_rejects_blocker_in_another_chain() -> None:
    payload = _path_payload(
        [_blocked_stage("r4_chain"), _not_reached_stage("revenue_chain")],
        chain_dispositions={"r4_chain": "withheld", "revenue_chain": "not_reached"},
        blocker_chain="r4_chain",
    )
    with pytest.raises(ValueError, match="earlier BLOCKED stage in the same material chain"):
        R5FixtureManifest.model_validate(payload)


def test_not_reached_rejects_referenced_blocker_that_appears_later() -> None:
    payload = _path_payload([_not_reached_stage(), _blocked_stage()])
    with pytest.raises(ValueError, match="earlier BLOCKED stage in the same material chain"):
        R5FixtureManifest.model_validate(payload)


def test_material_outcome_rejects_binary_float() -> None:
    payload = manifest_payload()
    payload["expected"]["material_path"][0]["outcome"] = {"value": 0.1}
    with pytest.raises(ValueError, match="floating-point"):
        R5FixtureManifest.model_validate(payload)


def test_safe_yaml_rejects_unsafe_tag_alias_anchor_and_merge(tmp_path) -> None:
    cases = (
        "!!python/object/apply:os.system ['echo unsafe']\n",
        "a: &x {value: 1}\nb: *x\n",
        "base: &base {value: 1}\nchild: {<<: *base}\n",
    )
    for index, content in enumerate(cases):
        path = tmp_path / f"unsafe-{index}.yaml"
        path.write_text(content, encoding="utf-8")
        with pytest.raises(R5ManifestError):
            safe_load_yaml_mapping(path)


def test_safe_yaml_rejects_excessive_size_and_depth(tmp_path) -> None:
    large = tmp_path / "large.yaml"
    large.write_bytes(b"key: " + b"x" * MAX_YAML_BYTES)
    with pytest.raises(R5ManifestError, match="exceeds"):
        safe_load_yaml_mapping(large)
    deep = tmp_path / "deep.yaml"
    value = "leaf"
    for _ in range(35):
        value = [value]
    deep.write_text(yaml.safe_dump({"root": value}), encoding="utf-8")
    with pytest.raises(R5ManifestError, match="safety limits"):
        safe_load_yaml_mapping(deep)


@pytest.mark.parametrize("unsafe", ["/tmp/outside.csv", "../outside.csv", "nested/../../outside.csv"])
def test_manifest_rejects_absolute_or_traversal_input(unsafe) -> None:
    payload = manifest_payload()
    payload["inputs"] = [{"path": unsafe, "role": "input", "media_type": "text/csv", "sha256": "0" * 64}]
    with pytest.raises(ValueError, match="relative path"):
        R5FixtureManifest.model_validate(payload)


def test_loader_rejects_missing_file_wrong_hash_and_symlink_escape(tmp_path) -> None:
    payload = manifest_payload()
    payload["inputs"] = [{"path": "input.csv", "role": "input", "media_type": "text/csv", "sha256": "0" * 64}]
    case_dir = write_case(tmp_path, payload)
    with pytest.raises(R5ManifestError, match="missing"):
        load_r5_manifest(case_dir)
    (case_dir / "input.csv").write_text("x\n1\n", encoding="utf-8")
    with pytest.raises(R5ManifestError, match="hash mismatch"):
        load_r5_manifest(case_dir)
    (case_dir / "input.csv").unlink()
    outside = tmp_path / "outside.csv"
    outside.write_text("x\n1\n", encoding="utf-8")
    (case_dir / "input.csv").symlink_to(outside)
    payload["inputs"][0]["sha256"] = hashlib.sha256(outside.read_bytes()).hexdigest()
    (case_dir / "manifest.yaml").write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(R5ManifestError, match="symlink"):
        load_r5_manifest(case_dir)


def _blocker() -> dict:
    return {
        "blocker_id": "test_blocker",
        "stage": "validation",
        "chain_id": "main",
        "reason": "test-only blocker",
        "authority_ref": "R5 §12",
    }


def _blocked_stage(chain_id: str = "main") -> dict:
    return {
        "stage": "validation",
        "chain_id": chain_id,
        "reachability": "blocked",
        "outcome": "failed",
        "controlling_reason": "test-only blocker",
        "authority_ref": "R5 §12",
    }


def _not_reached_stage(chain_id: str = "main") -> dict:
    return {
        "stage": "claim_decision",
        "chain_id": chain_id,
        "reachability": "not_reached",
        "not_reached_due_to": "validation",
    }


def _path_payload(
    material_path: list[dict],
    *,
    chain_dispositions: dict[str, str] | None = None,
    blocker_chain: str = "main",
) -> dict:
    payload = manifest_payload()
    payload["expected"].update(
        {
            "expectation_kind": "negative",
            "material_path": material_path,
            "chain_dispositions": chain_dispositions or {"main": "blocked"},
            "first_controlling_blocker": {**_blocker(), "chain_id": blocker_chain},
            "final_disposition": "blocked",
        }
    )
    return payload
