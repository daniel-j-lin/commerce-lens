from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from commerce_lens.contracts.diagnostic import AnalyticalOutcome
from commerce_lens.contracts.r7 import DiagnosticTestRequest, diagnostic_test_request_fingerprint
from commerce_lens.diagnostic.r7_evaluation import map_r7_outcome
from commerce_lens.diagnostic.r7_method_registry import METHOD_DEFINITION, authority_ref
from commerce_lens.engine.r7_execution import R7Transaction, average_ranks, calculate_r7_result, spearman_rho
from commerce_lens.evidence.identifiers import stable_content_id

HASH = "a" * 64


def _request() -> DiagnosticTestRequest:
    method = authority_ref(METHOD_DEFINITION)
    data = dict(
        test_request_id="pending", handoff_ref="handoff:1", handoff_fingerprint=HASH,
        governed_hypothesis_ref="hyp:1", governed_hypothesis_fingerprint=HASH,
        diagnostic_proposition_ref="prop:1", diagnostic_proposition_fingerprint=HASH,
        pretest_evaluation_ref="pre:1", pretest_evaluation_fingerprint=HASH,
        resolved_profile_ref="profile:1", resolved_profile_fingerprint=HASH,
        requirement_judgment_bundle_ref="bundle:1", requirement_judgment_bundle_fingerprint=HASH,
        method=method, support_criterion=METHOD_DEFINITION.support_criterion_ref,
        validation_profile=METHOD_DEFINITION.validation_profile_ref, implementation=METHOD_DEFINITION.implementation_ref,
        evidence_input_set_ref="evidence:1", evidence_input_set_fingerprint=HASH,
        canonical_dataset_ref="canonical:1", canonical_dataset_fingerprint=HASH, scope_ref="scope:1",
        baseline_period_ref="period:b", comparison_period_ref="period:c",
        baseline_start=date(2026, 1, 5), baseline_end=date(2026, 2, 1),
        comparison_start=date(2026, 2, 2), comparison_end=date(2026, 3, 1),
        baseline_population_ref="population:b", baseline_population_fingerprint=HASH,
        comparison_population_ref="population:c", comparison_population_fingerprint=HASH,
        metric_refs=("metric:revenue_change@metric_dictionary_v1",),
        variable_refs=("field:product_id", "field:line_revenue"),
        normalized_parameters=METHOD_DEFINITION.fixed_parameters, created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    fp = diagnostic_test_request_fingerprint(data)
    data.update(request_fingerprint=fp, test_request_id=stable_content_id("r7req", fp))
    return DiagnosticTestRequest(**data)


def _monotone_rows() -> tuple[R7Transaction, ...]:
    products = tuple(f"P{i}" for i in range(10))
    rows = []
    for week in range(8):
        active = products[: 10 - week]
        monday = date(2026, 1, 5) + timedelta(days=7 * week)
        total = Decimal(800 - 100 * week)
        rows.extend(R7Transaction(monday, product, total if index == 0 else Decimal("0")) for index, product in enumerate(active))
    return tuple(rows)


def test_average_rank_ties_and_spearman_match_independent_known_values():
    assert average_ranks((1, 2, 2, 4)) == (1.0, 2.5, 2.5, 4.0)
    assert spearman_rho((1, 2, 3, 4), (4, 3, 2, 1)) == -1.0


def test_complete_method_is_deterministic_and_support_boundary_is_exact():
    request = _request()
    first = calculate_r7_result(request=request, transactions=_monotone_rows(), execution_event_id="event:1")
    second = calculate_r7_result(request=request, transactions=_monotone_rows(), execution_event_id="event:2")
    assert first.spearman_rho == -1.0
    assert first.result_fingerprint == second.result_fingerprint
    assert first.baseline_week_count == first.comparison_week_count == 4
    assert map_r7_outcome(-0.5) is AnalyticalOutcome.CRITERION_MET
    assert map_r7_outcome(0.5) is AnalyticalOutcome.PROPOSITION_CONTRADICTED
    assert map_r7_outcome(0.0) is AnalyticalOutcome.CRITERION_NOT_MET


def test_constant_vector_and_insufficient_weeks_are_inconclusive():
    request = _request()
    products = tuple(f"P{i}" for i in range(3))
    rows = tuple(
        R7Transaction(date(2026, 1, 5) + timedelta(days=7 * week), product, Decimal("10"))
        for week in range(3) for product in products
    )
    result = calculate_r7_result(request=request, transactions=rows, execution_event_id="event:1")
    assert result.spearman_rho is None
    assert "MINIMUM_TOTAL_WEEKS_NOT_MET" in result.inconclusive_reasons
    assert "CONSTANT_JACCARD_VECTOR" in result.inconclusive_reasons
    assert map_r7_outcome(result.spearman_rho, result.inconclusive_reasons) is AnalyticalOutcome.NOT_EVALUATED
