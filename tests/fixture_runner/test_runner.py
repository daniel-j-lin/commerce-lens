from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from commerce_lens.fixture_runner.cases import EXPECTED_CASE_IDS, FixtureCase, discover_cases
from commerce_lens.fixture_runner import runner as runner_module
from commerce_lens.fixture_runner.runner import CaseRunResult, run_case, run_suite


CASES_ROOT = Path("tests/fixtures/p9/cases")


def test_full_p9_case_inventory_passes(tmp_path) -> None:
    results = run_suite(CASES_ROOT, runtime_root=tmp_path / "runtime")

    assert tuple(result.case_id for result in results) == EXPECTED_CASE_IDS
    assert all(result.passed for result in results)
    assert all(result.mismatches == () for result in results)


def test_full_inventory_is_order_independent_in_reversed_order(tmp_path) -> None:
    reversed_order = tuple(reversed(EXPECTED_CASE_IDS))

    results = run_suite(CASES_ROOT, runtime_root=tmp_path / "runtime", case_order=reversed_order)

    assert tuple(result.case_id for result in results) == reversed_order
    assert all(result.passed for result in results)


def test_representative_physical_case_repeat_run_preserves_material_state(tmp_path) -> None:
    case = discover_cases(CASES_ROOT)[0]

    first = run_case(case, runtime_root=tmp_path / "first")
    second = run_case(case, runtime_root=tmp_path / "second")

    assert first.passed
    assert second.passed
    assert _material_observation(first) == _material_observation(second)


def test_unexpected_metric_value_reports_failed_case_without_scoring(tmp_path) -> None:
    case = discover_cases(CASES_ROOT)[0]
    first_expected = case.manifest.expected.expected_validated_results[0]
    bad_expected = first_expected.model_copy(update={"value": "11.00"})
    manifest = case.manifest.model_copy(
        update={
            "expected": case.manifest.expected.model_copy(
                update={
                    "expected_validated_results": (
                        bad_expected,
                        *case.manifest.expected.expected_validated_results[1:],
                    )
                }
            )
        }
    )
    bad_case = FixtureCase(case_dir=case.case_dir, manifest=manifest)

    result = run_case(bad_case, runtime_root=tmp_path / "runtime")

    assert not result.passed
    assert any("value expected" in mismatch for mismatch in result.mismatches)
    assert not hasattr(result, "score")
    assert not hasattr(result, "pass_percentage")


def test_fail_closed_sufficiency_cases_expose_inadmissible_metric_state(tmp_path) -> None:
    cases = {case.case_id: case for case in discover_cases(CASES_ROOT)}

    missing = run_case(cases["P9-CONF-SUFF-MISSING-REVENUE-001"], runtime_root=tmp_path / "missing")
    mixed = run_case(cases["P9-CONF-SUFF-MIXED-CURRENCY-001"], runtime_root=tmp_path / "mixed")

    assert missing.passed
    assert mixed.passed
    assert missing.observed["metrics"]["revenue"]["metric_state"] == "Inadmissible"
    assert mixed.observed["metrics"]["revenue"]["metric_state"] == "Inadmissible"


def test_execution_disposition_is_checked(tmp_path) -> None:
    case = discover_cases(CASES_ROOT)[0]
    bad_case = _case_with_expected(case, execution_disposition="not_started")

    result = run_case(bad_case, runtime_root=tmp_path / "runtime")

    assert not result.passed
    assert any("execution_disposition" in mismatch for mismatch in result.mismatches)


def test_validation_disposition_is_checked(tmp_path) -> None:
    case = discover_cases(CASES_ROOT)[0]
    bad_case = _case_with_expected(case, validation_disposition="failed")

    result = run_case(bad_case, runtime_root=tmp_path / "runtime")

    assert not result.passed
    assert any("validation_disposition" in mismatch for mismatch in result.mismatches)


def test_no_claim_decision_is_checked_after_claim_evaluation(tmp_path) -> None:
    case = discover_cases(CASES_ROOT)[0]
    bad_case = _case_with_expected(case, no_claim_decision=True)

    result = run_case(bad_case, runtime_root=tmp_path / "runtime")

    assert not result.passed
    assert any("no ClaimDecision" in mismatch for mismatch in result.mismatches)


def test_unexpected_metric_state_causes_case_failure(tmp_path) -> None:
    case = discover_cases(CASES_ROOT)[0]
    metric = case.manifest.expected.expected_metric_results[0].model_copy(update={"metric_state": "Inadmissible"})
    bad_case = _case_with_expected(
        case,
        expected_metric_results=(metric, *case.manifest.expected.expected_metric_results[1:]),
    )

    result = run_case(bad_case, runtime_root=tmp_path / "runtime")

    assert not result.passed
    assert any("MetricResult state expected" in mismatch for mismatch in result.mismatches)


def test_unexpected_claim_state_causes_case_failure(tmp_path) -> None:
    case = discover_cases(CASES_ROOT)[0]
    claim = case.manifest.expected.expected_claims[0].model_copy(update={"claim_state": "Inadmissible"})
    bad_case = _case_with_expected(case, expected_claims=(claim, *case.manifest.expected.expected_claims[1:]))

    result = run_case(bad_case, runtime_root=tmp_path / "runtime")

    assert not result.passed
    assert any("ClaimState expected" in mismatch for mismatch in result.mismatches)


def test_unexpected_failure_code_causes_case_failure(tmp_path) -> None:
    case = next(item for item in discover_cases(CASES_ROOT) if item.case_id == "P9-CONF-SUFF-MISSING-REVENUE-001")
    bad_case = _case_with_expected(case, failure_code="canonical.line_revenue.other")

    result = run_case(bad_case, runtime_root=tmp_path / "runtime")

    assert not result.passed
    assert any("failure_code expected" in mismatch for mismatch in result.mismatches)


def test_final_disposition_is_checked(tmp_path) -> None:
    case = discover_cases(CASES_ROOT)[0]
    bad_case = _case_with_expected(case, final_disposition="blocked_insufficient")

    result = run_case(bad_case, runtime_root=tmp_path / "runtime")

    assert not result.passed
    assert any("final_disposition" in mismatch for mismatch in result.mismatches)


def test_hostile_submitted_value_deviation_fails_closed(tmp_path) -> None:
    case = next(item for item in discover_cases(CASES_ROOT) if item.case_id == "P9-CONF-VAL-REVCHG-WRONG-VALUE-001")
    hostile = case.manifest.expected.hostile_revenue_change.model_copy(
        update={"submitted_revenue_change": Decimal("22.00")}
    )
    bad_case = _case_with_expected(case, hostile_revenue_change=hostile)

    result = run_case(bad_case, runtime_root=tmp_path / "runtime")

    assert not result.passed
    assert any("submitted_revenue_change" in mismatch for mismatch in result.mismatches)


def test_hostile_expected_metric_state_is_compared(tmp_path, monkeypatch) -> None:
    case = next(item for item in discover_cases(CASES_ROOT) if item.case_id == "P9-CONF-VAL-REVCHG-WRONG-VALUE-001")

    def mismatched_hostile_outcome(manifest, runtime_root):
        hostile = manifest.expected.hostile_revenue_change
        return SimpleNamespace(
            data_sufficiency_state=manifest.expected.data_sufficiency_state,
            baseline_revenue=hostile.baseline_revenue,
            comparison_revenue=hostile.comparison_revenue,
            authoritative_revenue_change=hostile.authoritative_revenue_change,
            submitted_value=hostile.submitted_revenue_change,
            execution_disposition=manifest.expected.execution_disposition,
            validation_status=manifest.expected.validation_disposition,
            validation_rule_id=hostile.validation_rule_id,
            failure_code=hostile.failure_code,
            failed_metric_state="Valid",
            final_disposition=manifest.expected.final_disposition,
            validated_result_authorized=False,
            admissible_evidence_authorized=False,
            claim_decision_authorized=False,
            observed={"failed_metric_state": "Valid"},
        )

    monkeypatch.setattr(runner_module, "run_revenue_change_wrong_value_case", mismatched_hostile_outcome)
    result = runner_module._compare_hostile(case.manifest, SimpleNamespace(root=tmp_path / "runtime"))

    assert not result.passed
    assert any("hostile MetricState expected" in mismatch for mismatch in result.mismatches)


def test_case_order_must_name_each_case_exactly_once(tmp_path) -> None:
    try:
        run_suite(CASES_ROOT, runtime_root=tmp_path / "runtime", case_order=EXPECTED_CASE_IDS[:-1])
    except ValueError as exc:
        assert "case_order must contain each discovered P9 case exactly once" in str(exc)
    else:
        raise AssertionError("run_suite accepted incomplete case_order")


def _case_with_expected(case, **updates) -> FixtureCase:
    return FixtureCase(
        case_dir=case.case_dir,
        manifest=case.manifest.model_copy(
            update={"expected": case.manifest.expected.model_copy(update=updates)}
        ),
    )


def _material_observation(result: CaseRunResult) -> dict[str, object]:
    assert result.observed is not None
    observed = dict(result.observed)
    observed.pop("request_id", None)
    for metric in observed["metrics"].values():
        metric.pop("executed_result_refs", None)
        metric.pop("validated_result_refs", None)
        metric.pop("admissible_evidence_refs", None)
    return observed
