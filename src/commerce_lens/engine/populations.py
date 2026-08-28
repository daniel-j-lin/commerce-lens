"""Governed population-definition construction for pre-execution planning."""

from __future__ import annotations

from commerce_lens.contracts.common import (
    GroupingDimension,
    ScopeDefinition,
    SUPPORTED_SCOPE_FILTER_FIELDS,
    SUPPORTED_SCOPE_FILTER_OPERATORS,
)
from commerce_lens.contracts.populations import (
    CATEGORY_UNCLASSIFIED_RULE_REF,
    POPULATION_DEFINITION_VERSION,
    PopulationDefinition,
    PopulationPeriodRole,
)
from commerce_lens.contracts.requests import AnalysisRequest
from commerce_lens.contracts.sufficiency import DataSufficiencyResult
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, stable_content_id


class PopulationDefinitionError(ValueError):
    """Raised when governed population definitions cannot be built safely."""


def build_population_definitions(
    request: AnalysisRequest,
    sufficiency: DataSufficiencyResult,
    *,
    groupings: tuple[GroupingDimension, ...] | None = None,
) -> tuple[PopulationDefinition, ...]:
    """Create deterministic Baseline and Comparison population definitions.

    This records the structural row-selection authority for future execution. It
    intentionally does not read or materialize canonical rows.
    """
    if sufficiency.canonical_dataset_ref_id is None:
        raise PopulationDefinitionError("canonical_dataset_ref_id is required to define governed populations")
    if request.request_id != sufficiency.request_id:
        raise PopulationDefinitionError("AnalysisRequest and DataSufficiencyResult request IDs must match")
    if request.dataset_ref_id != sufficiency.dataset_ref_id:
        raise PopulationDefinitionError("AnalysisRequest and DataSufficiencyResult dataset refs must match")

    requested_groupings = tuple(dict.fromkeys(groupings or (request.grouping,)))
    return tuple(
        _population_for_period(request, sufficiency, period_role, grouping)
        for grouping in requested_groupings
        for period_role in (PopulationPeriodRole.BASELINE, PopulationPeriodRole.COMPARISON)
    )


def _population_for_period(
    request: AnalysisRequest,
    sufficiency: DataSufficiencyResult,
    period_role: PopulationPeriodRole,
    grouping: GroupingDimension,
) -> PopulationDefinition:
    period = request.baseline_period if period_role is PopulationPeriodRole.BASELINE else request.comparison_period
    grouping_keys = _grouping_keys(grouping)
    preserves_unclassified = grouping in (GroupingDimension.CATEGORY, GroupingDimension.PRODUCT_AND_CATEGORY)
    currency_basis_ref = _currency_basis_ref(request)
    canonical_scope = _canonical_scope(request.scope)
    payload = semantic_population_payload(
        canonical_dataset_ref_id=sufficiency.canonical_dataset_ref_id,
        dataset_ref_id=request.dataset_ref_id,
        period=period,
        period_role=period_role,
        currency_basis_ref=currency_basis_ref,
        scope=canonical_scope,
        grouping=grouping,
        grouping_keys=grouping_keys,
        preserves_unclassified_category=preserves_unclassified,
    )
    fingerprint = canonical_json_fingerprint(payload)
    return PopulationDefinition(
        population_id=stable_content_id("pop", fingerprint),
        canonical_dataset_ref_id=sufficiency.canonical_dataset_ref_id,
        dataset_ref_id=request.dataset_ref_id,
        period=period,
        period_role=period_role,
        currency_basis_ref=currency_basis_ref,
        scope=canonical_scope,
        grouping=grouping,
        grouping_keys=grouping_keys,
        supported_filter_fields=tuple(sorted(SUPPORTED_SCOPE_FILTER_FIELDS)),
        supported_filter_operators=tuple(sorted(SUPPORTED_SCOPE_FILTER_OPERATORS)),
        preserves_unclassified_category=preserves_unclassified,
        population_fingerprint=fingerprint,
    )


def semantic_population_payload(
    *,
    canonical_dataset_ref_id: str,
    dataset_ref_id: str,
    period,
    period_role: PopulationPeriodRole,
    currency_basis_ref: str,
    scope: ScopeDefinition,
    grouping: GroupingDimension,
    grouping_keys: tuple[str, ...],
    preserves_unclassified_category: bool,
) -> dict[str, object]:
    return {
        "definition_version": POPULATION_DEFINITION_VERSION,
        "canonical_dataset_ref_id": canonical_dataset_ref_id,
        "dataset_ref_id": dataset_ref_id,
        "period": period.model_dump(mode="json"),
        "period_role": period_role.value,
        "eligibility_rule_ref": "canonical_dictionary:27:phase2_governed_eligible_population",
        "currency_basis_ref": currency_basis_ref,
        "scope": material_scope_payload(scope),
        "grouping": grouping.value,
        "grouping_keys": grouping_keys,
        "supported_filter_fields": sorted(SUPPORTED_SCOPE_FILTER_FIELDS),
        "supported_filter_operators": sorted(SUPPORTED_SCOPE_FILTER_OPERATORS),
        "preserves_unclassified_category": preserves_unclassified_category,
        "category_unclassified_rule_ref": CATEGORY_UNCLASSIFIED_RULE_REF if preserves_unclassified_category else None,
    }


def population_fingerprint(population: PopulationDefinition) -> str:
    return canonical_json_fingerprint(
        semantic_population_payload(
            canonical_dataset_ref_id=population.canonical_dataset_ref_id,
            dataset_ref_id=population.dataset_ref_id,
            period=population.period,
            period_role=population.period_role,
            currency_basis_ref=population.currency_basis_ref,
            scope=population.scope,
            grouping=population.grouping,
            grouping_keys=population.grouping_keys,
            preserves_unclassified_category=population.preserves_unclassified_category,
        )
    )


def population_id_for_fingerprint(fingerprint: str) -> str:
    return stable_content_id("pop", fingerprint)


def _grouping_keys(grouping: GroupingDimension) -> tuple[str, ...]:
    if grouping is GroupingDimension.PRODUCT:
        return ("product_id",)
    if grouping is GroupingDimension.CATEGORY:
        return ("category_id",)
    if grouping is GroupingDimension.PRODUCT_AND_CATEGORY:
        return ("product_id", "category_id")
    return ()


def _currency_basis_ref(request: AnalysisRequest) -> str:
    currency_filters = tuple(item for item in _canonical_filters(request.scope.filters) if item.field == "currency")
    if len(currency_filters) == 1 and currency_filters[0].operator == "equals":
        return f"currency:{currency_filters[0].value}"
    if len(currency_filters) > 1:
        values = ",".join(str(item.value) for item in _canonical_filters(currency_filters))
        return f"currency_filters:{values}"
    return "currency_basis:phase2_single_governed_currency"


def material_scope_payload(scope) -> dict[str, object]:
    return {
        "scope_id": scope.scope_id,
        "population_ref": scope.population_ref,
        "filters": [item.model_dump(mode="json") for item in _canonical_filters(scope.filters)],
    }


def _canonical_scope(scope: ScopeDefinition) -> ScopeDefinition:
    return scope.model_copy(update={"filters": _canonical_filters(scope.filters)})


def _canonical_filters(filters) -> tuple:
    canonical = sorted(
        filters,
        key=lambda item: (item.field, item.operator, type(item.value).__name__, str(item.value)),
    )
    deduplicated = {}
    for item in canonical:
        key = (item.field, item.operator, type(item.value).__name__, item.value)
        deduplicated.setdefault(key, item)
    return tuple(deduplicated.values())
