from datetime import date

import pytest
from pydantic import ValidationError

from commerce_lens.contracts.common import GroupingDimension, PeriodDefinition, ScopeDefinition, ScopeFilter
from commerce_lens.contracts.evidence import MetricReference
from commerce_lens.contracts.populations import CATEGORY_UNCLASSIFIED_RULE_REF, PopulationPeriodRole
from commerce_lens.contracts.requests import AnalysisRequest
from commerce_lens.contracts.sufficiency import DataSufficiencyResult, MetricEligibility, SufficiencyState
from commerce_lens.engine.populations import build_population_definitions
from commerce_lens.metrics import METRIC_DEFINITION_VERSION, METRIC_REGISTRY_VERSION


def test_population_fingerprint_is_deterministic() -> None:
    request = _request(grouping=GroupingDimension.PRODUCT)
    sufficiency = _sufficiency(request)

    first = build_population_definitions(request, sufficiency)
    second = build_population_definitions(request, sufficiency)

    assert [item.population_fingerprint for item in first] == [
        item.population_fingerprint for item in second
    ]
    assert [item.population_id for item in first] == [item.population_id for item in second]


def test_different_period_and_currency_change_population_identity() -> None:
    base = _request(scope=ScopeDefinition(scope_id="all", filters=(ScopeFilter(field="currency", operator="equals", value="USD"),)))
    different_period = _request(
        baseline=(date(2026, 2, 1), date(2026, 2, 2)),
        comparison=(date(2026, 2, 3), date(2026, 2, 4)),
        scope=base.scope,
    )
    different_currency = _request(
        scope=ScopeDefinition(scope_id="all", filters=(ScopeFilter(field="currency", operator="equals", value="EUR"),))
    )

    assert build_population_definitions(base, _sufficiency(base))[0].population_id != build_population_definitions(
        different_period, _sufficiency(different_period)
    )[0].population_id
    assert build_population_definitions(base, _sufficiency(base))[0].population_id != build_population_definitions(
        different_currency, _sufficiency(different_currency)
    )[0].population_id


def test_equivalent_scope_filter_order_has_same_population_identity() -> None:
    first = _request(
        scope=ScopeDefinition(
            scope_id="filtered",
            filters=(
                ScopeFilter(field="product_id", operator="equals", value="p1"),
                ScopeFilter(field="currency", operator="equals", value="USD"),
            ),
        )
    )
    second = _request(
        scope=ScopeDefinition(
            scope_id="filtered",
            filters=(
                ScopeFilter(field="currency", operator="equals", value="USD"),
                ScopeFilter(field="product_id", operator="equals", value="p1"),
            ),
        )
    )

    assert build_population_definitions(first, _sufficiency(first))[0].population_fingerprint == build_population_definitions(
        second, _sufficiency(second)
    )[0].population_fingerprint


def test_materially_different_filters_change_population_identity() -> None:
    product = _request(
        scope=ScopeDefinition(
            scope_id="filtered",
            filters=(
                ScopeFilter(field="currency", operator="equals", value="USD"),
                ScopeFilter(field="product_id", operator="equals", value="p1"),
            ),
        )
    )
    category = _request(
        scope=ScopeDefinition(
            scope_id="filtered",
            filters=(
                ScopeFilter(field="currency", operator="equals", value="USD"),
                ScopeFilter(field="category_id", operator="equals", value="c1"),
            ),
        )
    )

    assert build_population_definitions(product, _sufficiency(product))[0].population_fingerprint != build_population_definitions(
        category, _sufficiency(category)
    )[0].population_fingerprint


def test_scope_description_does_not_change_semantic_population_identity() -> None:
    plain = _request(scope=ScopeDefinition(scope_id="all"))
    described = _request(scope=ScopeDefinition(scope_id="all", description="For display only"))

    assert build_population_definitions(plain, _sufficiency(plain))[0].population_fingerprint == build_population_definitions(
        described, _sufficiency(described)
    )[0].population_fingerprint


def test_population_grouping_changes_material_identity() -> None:
    total = _request(grouping=GroupingDimension.NONE)
    product = _request(grouping=GroupingDimension.PRODUCT)
    category = _request(grouping=GroupingDimension.CATEGORY)

    assert build_population_definitions(total, _sufficiency(total))[0].population_fingerprint != build_population_definitions(
        product, _sufficiency(product)
    )[0].population_fingerprint
    assert build_population_definitions(product, _sufficiency(product))[0].population_fingerprint != build_population_definitions(
        category, _sufficiency(category)
    )[0].population_fingerprint


def test_scope_filters_are_limited_to_phase2_governed_contract() -> None:
    with pytest.raises(ValidationError):
        ScopeFilter(field="arbitrary_sql", operator="equals", value="1=1")

    with pytest.raises(ValidationError):
        ScopeFilter(field="product_id", operator="contains", value="p1")


def test_product_and_category_grouping_semantics_are_structural() -> None:
    product_request = _request(grouping=GroupingDimension.PRODUCT)
    category_request = _request(grouping=GroupingDimension.CATEGORY)

    product_population = build_population_definitions(product_request, _sufficiency(product_request))[0]
    category_population = build_population_definitions(category_request, _sufficiency(category_request))[0]

    assert product_population.grouping_keys == ("product_id",)
    assert not product_population.preserves_unclassified_category
    assert category_population.grouping_keys == ("category_id",)
    assert category_population.preserves_unclassified_category
    assert CATEGORY_UNCLASSIFIED_RULE_REF == "canonical_dictionary:20:unclassified_bucket"


def test_baseline_and_comparison_populations_remain_distinct() -> None:
    request = _request()
    baseline, comparison = build_population_definitions(request, _sufficiency(request))

    assert baseline.period_role is PopulationPeriodRole.BASELINE
    assert comparison.period_role is PopulationPeriodRole.COMPARISON
    assert baseline.population_id != comparison.population_id


def _request(
    *,
    baseline: tuple[date, date] = (date(2026, 1, 1), date(2026, 1, 2)),
    comparison: tuple[date, date] = (date(2026, 1, 3), date(2026, 1, 4)),
    grouping: GroupingDimension = GroupingDimension.NONE,
    scope: ScopeDefinition = ScopeDefinition(scope_id="all"),
) -> AnalysisRequest:
    return AnalysisRequest(
        canonical_business_question_id="canonical_revenue_change",
        metrics=(MetricReference(metric_id="revenue_change", definition_version=METRIC_DEFINITION_VERSION),),
        baseline_period=PeriodDefinition(
            period_id="baseline",
            label="Baseline",
            start_date=baseline[0],
            end_date=baseline[1],
            date_convention_ref="order_date_utc",
        ),
        comparison_period=PeriodDefinition(
            period_id="comparison",
            label="Comparison",
            start_date=comparison[0],
            end_date=comparison[1],
            date_convention_ref="order_date_utc",
        ),
        scope=scope,
        grouping=grouping,
        dataset_ref_id="ds_1",
        canonical_schema_version="canonical_mvp_v1",
        metric_registry_version=METRIC_REGISTRY_VERSION,
    )


def _sufficiency(request: AnalysisRequest) -> DataSufficiencyResult:
    return DataSufficiencyResult(
        sufficiency_id=f"suff_{request.request_id}",
        request_id=request.request_id,
        dataset_ref_id=request.dataset_ref_id,
        canonical_dataset_ref_id="cds_1",
        metric_eligibility=tuple(
            MetricEligibility(metric_ref=metric.metric_id, eligible=True) for metric in request.metrics
        ),
        state=SufficiencyState.SUFFICIENT,
    )
