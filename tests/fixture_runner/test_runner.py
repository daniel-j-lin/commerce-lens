from __future__ import annotations

from pathlib import Path

from commerce_lens.fixture_runner.cases import EXPECTED_CASE_IDS, FixtureCase, discover_cases
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


def test_case_order_must_name_each_case_exactly_once(tmp_path) -> None:
    try:
        run_suite(CASES_ROOT, runtime_root=tmp_path / "runtime", case_order=EXPECTED_CASE_IDS[:-1])
    except ValueError as exc:
        assert "case_order must contain each discovered P9 case exactly once" in str(exc)
    else:
        raise AssertionError("run_suite accepted incomplete case_order")


def _material_observation(result: CaseRunResult) -> dict[str, object]:
    assert result.observed is not None
    observed = dict(result.observed)
    observed.pop("request_id", None)
    for metric in observed["metrics"].values():
        metric.pop("executed_result_refs", None)
        metric.pop("validated_result_refs", None)
        metric.pop("admissible_evidence_refs", None)
    return observed
