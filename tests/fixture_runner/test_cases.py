from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from commerce_lens.fixture_runner.cases import EXPECTED_CASE_IDS, FixtureCaseError, discover_cases, load_case


CASES_ROOT = Path("tests/fixtures/p9/cases")


def test_discovery_loads_exact_approved_inventory() -> None:
    cases = discover_cases(CASES_ROOT)

    assert tuple(case.case_id for case in cases) == EXPECTED_CASE_IDS
    assert len(cases) == 8
    assert all(case.manifest.frozen_fixture_id == "NONE" for case in cases)


def test_manifest_safe_yaml_schema_rejects_extra_fields(tmp_path) -> None:
    case_dir = _copy_case(tmp_path, "P9-CONF-POS-001")
    manifest_path = case_dir / "manifest.yaml"
    manifest_path.write_text(manifest_path.read_text(encoding="utf-8") + "\nunexpected: true\n", encoding="utf-8")

    with pytest.raises(FixtureCaseError, match="schema invalid"):
        load_case(case_dir)


def test_unsafe_python_object_yaml_tag_fails_safe_loading(tmp_path) -> None:
    case_dir = _copy_case(tmp_path, "P9-CONF-POS-001")
    (case_dir / "manifest.yaml").write_text("!!python/object/apply:os.system ['echo unsafe']\n", encoding="utf-8")

    with pytest.raises(FixtureCaseError, match="not safe-loadable YAML"):
        load_case(case_dir)


def test_invalid_data_sufficiency_state_fails_load(tmp_path) -> None:
    case_dir = _copy_case(tmp_path, "P9-CONF-POS-001")
    _replace(case_dir, "data_sufficiency_state: sufficient", "data_sufficiency_state: maybe")

    with pytest.raises(FixtureCaseError, match="schema invalid"):
        load_case(case_dir)


def test_invalid_metric_state_fails_load(tmp_path) -> None:
    case_dir = _copy_case(tmp_path, "P9-CONF-POS-001")
    _replace(case_dir, "metric_state: Valid", "metric_state: Maybe", count=1)

    with pytest.raises(FixtureCaseError, match="schema invalid"):
        load_case(case_dir)


def test_invalid_claim_type_and_state_fail_load(tmp_path) -> None:
    case_dir = _copy_case(tmp_path, "P9-CONF-POS-001")
    _replace(case_dir, "claim_type: descriptive, claim_state: Admissible", "claim_type: predictive, claim_state: Maybe", count=1)

    with pytest.raises(FixtureCaseError, match="schema invalid"):
        load_case(case_dir)


def test_missing_required_material_field_fails_load(tmp_path) -> None:
    case_dir = _copy_case(tmp_path, "P9-CONF-POS-001")
    _replace(case_dir, "  final_disposition: completed_admissible\n", "")

    with pytest.raises(FixtureCaseError, match="schema invalid"):
        load_case(case_dir)


def test_directory_manifest_case_id_mismatch_fails_load(tmp_path) -> None:
    case_dir = _copy_case(tmp_path, "P9-CONF-POS-001")
    _replace(case_dir, "case_id: P9-CONF-POS-001", "case_id: P9-CONF-REVCHG-001")

    with pytest.raises(FixtureCaseError, match="does not match directory"):
        load_case(case_dir)


def test_load_case_rejects_missing_physical_input(tmp_path) -> None:
    case_dir = _copy_case(tmp_path, "P9-CONF-POS-001")
    (case_dir / "input.csv").unlink()

    with pytest.raises(FixtureCaseError, match="missing physical P9 input.csv"):
        load_case(case_dir)


def test_discovery_rejects_unknown_case_directory(tmp_path) -> None:
    root = tmp_path / "cases"
    shutil.copytree(CASES_ROOT, root)
    (root / "P9-CONF-UNKNOWN-001").mkdir()

    with pytest.raises(FixtureCaseError, match="unknown P9 case"):
        discover_cases(root)


def test_public_operation_inconsistent_with_case_id_fails_load(tmp_path) -> None:
    case_dir = _copy_case(tmp_path, "P9-CONF-POS-001")
    _replace(case_dir, "public_operation: run_analysis(...), then evaluate_claim(...)", "public_operation: run_analysis(...)")

    with pytest.raises(FixtureCaseError, match="public_operation"):
        load_case(case_dir)


def test_setup_row_unknown_field_fails_load(tmp_path) -> None:
    case_dir = _copy_case(tmp_path, "P9-CONF-CLAIM-DIAGNOSTIC-REFUSAL-001")
    _replace(case_dir, "line_revenue: \"120.00\"", "line_revenue: \"120.00\", line_reveneu: \"typo\"", count=1)

    with pytest.raises(FixtureCaseError, match="schema invalid"):
        load_case(case_dir)


def test_harness_cases_do_not_require_placeholder_csv_files() -> None:
    for case_id in (
        "P9-CONF-VAL-REVCHG-WRONG-VALUE-001",
        "P9-CONF-CLAIM-DIAGNOSTIC-REFUSAL-001",
        "P9-CONF-TAMPER-CROSS-REQUEST-001",
    ):
        case = load_case(CASES_ROOT / case_id)
        assert case.input_path is None
        assert not (case.case_dir / "input.csv").exists()


def _copy_case(tmp_path: Path, case_id: str) -> Path:
    case_dir = tmp_path / case_id
    shutil.copytree(CASES_ROOT / case_id, case_dir)
    return case_dir


def _replace(case_dir: Path, old: str, new: str, *, count: int = -1) -> None:
    manifest_path = case_dir / "manifest.yaml"
    text = manifest_path.read_text(encoding="utf-8")
    if old not in text:
        raise AssertionError(f"manifest text not found: {old}")
    manifest_path.write_text(text.replace(old, new, count), encoding="utf-8")
