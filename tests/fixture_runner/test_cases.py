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
    case_dir = tmp_path / "P9-CONF-POS-001"
    shutil.copytree(CASES_ROOT / "P9-CONF-POS-001", case_dir)
    manifest_path = case_dir / "manifest.yaml"
    manifest_path.write_text(manifest_path.read_text(encoding="utf-8") + "\nunexpected: true\n", encoding="utf-8")

    with pytest.raises(FixtureCaseError, match="schema invalid"):
        load_case(case_dir)


def test_load_case_rejects_missing_physical_input(tmp_path) -> None:
    case_dir = tmp_path / "P9-CONF-POS-001"
    shutil.copytree(CASES_ROOT / "P9-CONF-POS-001", case_dir)
    (case_dir / "input.csv").unlink()

    with pytest.raises(FixtureCaseError, match="missing physical P9 input.csv"):
        load_case(case_dir)


def test_discovery_rejects_unknown_case_directory(tmp_path) -> None:
    root = tmp_path / "cases"
    shutil.copytree(CASES_ROOT, root)
    (root / "P9-CONF-UNKNOWN-001").mkdir()

    with pytest.raises(FixtureCaseError, match="unknown P9 case"):
        discover_cases(root)


def test_harness_cases_do_not_require_placeholder_csv_files() -> None:
    for case_id in (
        "P9-CONF-VAL-REVCHG-WRONG-VALUE-001",
        "P9-CONF-CLAIM-DIAGNOSTIC-REFUSAL-001",
        "P9-CONF-TAMPER-CROSS-REQUEST-001",
    ):
        case = load_case(CASES_ROOT / case_id)
        assert case.input_path is None
        assert not (case.case_dir / "input.csv").exists()
