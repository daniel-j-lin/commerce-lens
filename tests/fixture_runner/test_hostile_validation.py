from __future__ import annotations

from pathlib import Path

from commerce_lens.fixture_runner.cases import load_case
from commerce_lens.fixture_runner.runner import run_case


CASES_ROOT = Path("tests/fixtures/p9/cases")


def test_revenue_change_wrong_value_hostile_case_fails_validation_only(tmp_path) -> None:
    case = load_case(CASES_ROOT / "P9-CONF-VAL-REVCHG-WRONG-VALUE-001")

    result = run_case(case, runtime_root=tmp_path / "runtime")

    assert result.passed
    assert result.observed is not None
    assert result.observed["submitted_value"] == "21.00"
    assert result.observed["validation_status"] == "failed"
    assert result.observed["validation_rule_id"] == "validation:revenue_change_from_validated_revenues"
    assert result.observed["failure_code"] == "value_mismatch"
    assert result.observed["failed_metric_state"] == "Inadmissible"
    assert result.observed["validated_result_authorized"] is False
    assert result.observed["admissible_evidence_authorized"] is False
    assert result.observed["claim_decision_authorized"] is False
