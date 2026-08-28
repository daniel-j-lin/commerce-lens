"""Single governed Metric Registry authority for the approved MVP metrics."""

from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from commerce_lens.contracts.common import ContractBase, GroupingDimension


METRIC_REGISTRY_VERSION = "metric_registry_mvp_v1"
METRIC_DEFINITION_VERSION = "metric_dictionary_v1"
PRECISION_POLICY_REF = "canonical_dictionary:34:exact_decimal_presentation_rounding_only"
EXECUTION_NOT_IMPLEMENTED_REF = "not_implemented:p3_001_metric_execution_not_authorized"


class MetricCategory(str, Enum):
    CORE = "core"
    PERIOD_COMPARISON = "period_comparison"
    PRODUCT = "product"
    CATEGORY = "category"
    RANKING = "ranking"


class PeriodRequirement(str, Enum):
    SINGLE_PERIOD = "single_period"
    BASELINE_AND_COMPARISON = "baseline_and_comparison"


class Additivity(str, Enum):
    ADDITIVE = "additive"
    NON_ADDITIVE = "non_additive"
    DERIVED_NON_ADDITIVE = "derived_non_additive"
    RANKING = "ranking"


class DependencyPeriodRole(str, Enum):
    SAME_AS_PARENT = "same_as_parent"
    BASELINE = "baseline"
    COMPARISON = "comparison"
    BASELINE_AND_COMPARISON = "baseline_and_comparison"
    NO_PERIOD = "no_period"


class MetricDependency(ContractBase):
    metric_id: str = Field(min_length=1)
    period_role: DependencyPeriodRole
    grouping: GroupingDimension | None = None
    applies_to_groupings: tuple[GroupingDimension, ...] = ()


class MetricDefinition(ContractBase):
    metric_id: str = Field(min_length=1)
    definition_version: str = METRIC_DEFINITION_VERSION
    display_name: str = Field(min_length=1)
    business_definition: str = Field(min_length=1)
    metric_category: MetricCategory
    required_canonical_fields: tuple[str, ...] = ()
    prerequisite_metric_ids: tuple[str, ...] = ()
    dependencies: tuple[MetricDependency, ...] = ()
    population_definition_ref: str = Field(min_length=1)
    grouping_requirement: GroupingDimension | None = GroupingDimension.NONE
    supported_groupings: tuple[GroupingDimension, ...] = ()
    required_canonical_fields_by_grouping: dict[GroupingDimension, tuple[str, ...]] = Field(default_factory=dict)
    period_requirement: PeriodRequirement
    currency_unit_semantics: str = Field(min_length=1)
    additivity: Additivity
    undefined_conditions: tuple[str, ...] = ()
    qualification_conditions: tuple[str, ...] = ()
    precision_policy_ref: str = PRECISION_POLICY_REF
    required_validation_rule_refs: tuple[str, ...] = ()
    execution_implementation_ref: str = EXECUTION_NOT_IMPLEMENTED_REF
    output_shape: str = Field(min_length=1)


class MetricRegistry(ContractBase):
    registry_version: str = METRIC_REGISTRY_VERSION
    definitions: tuple[MetricDefinition, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_registry(self) -> "MetricRegistry":
        ids = [definition.metric_id for definition in self.definitions]
        if len(ids) != len(set(ids)):
            raise ValueError("Metric Registry cannot contain duplicate Metric IDs")
        defined = set(ids)
        for definition in self.definitions:
            dependency_ids = tuple(dict.fromkeys(dependency.metric_id for dependency in definition.dependencies))
            if dependency_ids != definition.prerequisite_metric_ids:
                raise ValueError(f"Metric {definition.metric_id} dependency metadata must match prerequisite Metric IDs")
            missing = [metric_id for metric_id in definition.prerequisite_metric_ids if metric_id not in defined]
            if missing:
                raise ValueError(f"Metric {definition.metric_id} references unknown prerequisite(s): {missing}")
        _assert_acyclic({definition.metric_id: definition.prerequisite_metric_ids for definition in self.definitions})
        return self

    @property
    def metric_ids(self) -> tuple[str, ...]:
        return tuple(definition.metric_id for definition in self.definitions)

    def get(self, metric_id: str) -> MetricDefinition | None:
        return next((definition for definition in self.definitions if definition.metric_id == metric_id), None)

    def require(self, metric_id: str) -> MetricDefinition:
        definition = self.get(metric_id)
        if definition is None:
            raise KeyError(f"unsupported Metric ID: {metric_id}")
        return definition


def get_metric_registry() -> MetricRegistry:
    return _DEFAULT_REGISTRY


def approved_metric_ids() -> tuple[str, ...]:
    return _DEFAULT_REGISTRY.metric_ids


def assert_registry_matches_approved_authority(registry: MetricRegistry) -> None:
    """Fail when a supplied registry changes the approved P3-001 authority."""
    approved = get_metric_registry()
    if registry.registry_version != approved.registry_version:
        raise ValueError("Metric Registry version does not match approved P3-001 authority")
    if registry.metric_ids != approved.metric_ids:
        raise ValueError("Metric Registry Metric set does not match approved P3-001 authority")
    approved_by_id = {definition.metric_id: definition for definition in approved.definitions}
    for definition in registry.definitions:
        if definition.model_dump(mode="json") != approved_by_id[definition.metric_id].model_dump(mode="json"):
            raise ValueError(f"Metric {definition.metric_id} does not match approved P3-001 authority")


def _dependency(
    metric_id: str,
    period_role: DependencyPeriodRole,
    *,
    grouping: GroupingDimension | None = None,
    applies_to_groupings: tuple[GroupingDimension, ...] = (),
) -> MetricDependency:
    return MetricDependency(
        metric_id=metric_id,
        period_role=period_role,
        grouping=grouping,
        applies_to_groupings=applies_to_groupings,
    )


def _definition(
    metric_id: str,
    display_name: str,
    business_definition: str,
    metric_category: MetricCategory,
    required_canonical_fields: tuple[str, ...],
    dependencies: tuple[MetricDependency, ...],
    grouping: GroupingDimension | None,
    period_requirement: PeriodRequirement,
    additivity: Additivity,
    validation_refs: tuple[str, ...],
    output_shape: str,
    *,
    undefined: tuple[str, ...] = (),
    qualifications: tuple[str, ...] = (),
    supported_groupings: tuple[GroupingDimension, ...] | None = None,
    required_fields_by_grouping: dict[GroupingDimension, tuple[str, ...]] | None = None,
    currency: str = "single governed currency for monetary metrics; count unit for Orders",
) -> MetricDefinition:
    return MetricDefinition(
        metric_id=metric_id,
        display_name=display_name,
        business_definition=business_definition,
        metric_category=metric_category,
        required_canonical_fields=required_canonical_fields,
        prerequisite_metric_ids=tuple(dict.fromkeys(dependency.metric_id for dependency in dependencies)),
        dependencies=dependencies,
        population_definition_ref="population_mvp_v1:governed_eligible_order_lines",
        grouping_requirement=grouping,
        supported_groupings=supported_groupings or (),
        required_canonical_fields_by_grouping=required_fields_by_grouping or {},
        period_requirement=period_requirement,
        currency_unit_semantics=currency,
        additivity=additivity,
        undefined_conditions=undefined,
        qualification_conditions=qualifications,
        required_validation_rule_refs=validation_refs,
        output_shape=output_shape,
    )


def _assert_acyclic(graph: dict[str, tuple[str, ...]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(metric_id: str) -> None:
        if metric_id in visiting:
            raise ValueError(f"Metric dependency cycle detected at {metric_id}")
        if metric_id in visited:
            return
        visiting.add(metric_id)
        for dependency in graph[metric_id]:
            visit(dependency)
        visiting.remove(metric_id)
        visited.add(metric_id)

    for metric_id in graph:
        visit(metric_id)


_DEFAULT_REGISTRY = MetricRegistry(
    definitions=(
        _definition(
            "revenue",
            "Revenue",
            "Sum of authoritative post-discount eligible merchandise sales value across eligible canonical order lines, excluding tax and shipping.",
            MetricCategory.CORE,
            ("order_id", "order_line_id", "order_date", "quantity", "line_revenue", "currency", "eligibility_status"),
            (),
            GroupingDimension.NONE,
            PeriodRequirement.SINGLE_PERIOD,
            Additivity.ADDITIVE,
            ("validation:revenue_sum", "validation:currency_consistency", "validation:population_consistency"),
            "scalar_decimal",
        ),
        _definition(
            "orders",
            "Orders",
            "Count of distinct eligible order_id values with at least one eligible canonical line in the governed scope and period.",
            MetricCategory.CORE,
            ("order_id", "order_line_id", "order_date", "eligibility_status"),
            (),
            GroupingDimension.NONE,
            PeriodRequirement.SINGLE_PERIOD,
            Additivity.NON_ADDITIVE,
            ("validation:distinct_order_count", "validation:population_consistency"),
            "scalar_integer",
            currency="count of distinct governed orders",
        ),
        _definition(
            "aov",
            "AOV",
            "Revenue divided by Orders for the identical governed scope, period, eligibility rules, and currency basis.",
            MetricCategory.CORE,
            ("order_id", "order_line_id", "order_date", "quantity", "line_revenue", "currency", "eligibility_status"),
            (
                _dependency("revenue", DependencyPeriodRole.SAME_AS_PARENT, grouping=GroupingDimension.NONE),
                _dependency("orders", DependencyPeriodRole.SAME_AS_PARENT, grouping=GroupingDimension.NONE),
            ),
            GroupingDimension.NONE,
            PeriodRequirement.SINGLE_PERIOD,
            Additivity.DERIVED_NON_ADDITIVE,
            ("validation:aov_from_revenue_orders", "validation:population_consistency"),
            "scalar_decimal",
            undefined=("orders_equals_zero",),
        ),
        _definition(
            "revenue_change",
            "Revenue Change",
            "Comparison Revenue minus Baseline Revenue for the governed scope.",
            MetricCategory.PERIOD_COMPARISON,
            ("order_date", "line_revenue", "currency"),
            (
                _dependency("revenue", DependencyPeriodRole.BASELINE, grouping=GroupingDimension.NONE),
                _dependency("revenue", DependencyPeriodRole.COMPARISON, grouping=GroupingDimension.NONE),
            ),
            GroupingDimension.NONE,
            PeriodRequirement.BASELINE_AND_COMPARISON,
            Additivity.ADDITIVE,
            ("validation:revenue_change_direction", "validation:comparison_population_consistency"),
            "scalar_decimal",
        ),
        _definition(
            "revenue_change_pct",
            "Revenue Change Percentage",
            "Revenue Change divided by Baseline Revenue, multiplied by 100, using authoritative unrounded values.",
            MetricCategory.PERIOD_COMPARISON,
            ("order_date", "line_revenue", "currency"),
            (
                _dependency("revenue", DependencyPeriodRole.BASELINE, grouping=GroupingDimension.NONE),
                _dependency("revenue", DependencyPeriodRole.COMPARISON, grouping=GroupingDimension.NONE),
            ),
            GroupingDimension.NONE,
            PeriodRequirement.BASELINE_AND_COMPARISON,
            Additivity.DERIVED_NON_ADDITIVE,
            ("validation:revenue_change_pct_denominator", "validation:comparison_population_consistency"),
            "scalar_percentage",
            undefined=("baseline_revenue_equals_zero",),
        ),
        _definition(
            "product_revenue",
            "Product Revenue",
            "Eligible Revenue aggregated by authoritative product_id under the common eligible population.",
            MetricCategory.PRODUCT,
            ("product_id", "line_revenue", "currency", "order_date", "eligibility_status"),
            (_dependency("revenue", DependencyPeriodRole.SAME_AS_PARENT, grouping=GroupingDimension.NONE),),
            GroupingDimension.PRODUCT,
            PeriodRequirement.SINGLE_PERIOD,
            Additivity.ADDITIVE,
            ("validation:product_revenue_reconciles_to_total",),
            "grouped_decimal",
        ),
        _definition(
            "product_orders",
            "Product Orders",
            "Distinct eligible order_id values containing at least one eligible line for the product in the governed period.",
            MetricCategory.PRODUCT,
            ("product_id", "order_id", "order_date", "eligibility_status"),
            (_dependency("orders", DependencyPeriodRole.SAME_AS_PARENT, grouping=GroupingDimension.NONE),),
            GroupingDimension.PRODUCT,
            PeriodRequirement.SINGLE_PERIOD,
            Additivity.NON_ADDITIVE,
            ("validation:product_orders_distinct", "validation:orders_non_additive"),
            "grouped_integer",
            currency="count of distinct governed orders",
        ),
        _definition(
            "product_revenue_change",
            "Product Revenue Change",
            "Product Comparison Revenue minus Product Baseline Revenue over the union of product_id values across complete periods.",
            MetricCategory.PRODUCT,
            ("product_id", "order_date", "line_revenue", "currency"),
            (
                _dependency("product_revenue", DependencyPeriodRole.BASELINE, grouping=GroupingDimension.PRODUCT),
                _dependency("product_revenue", DependencyPeriodRole.COMPARISON, grouping=GroupingDimension.PRODUCT),
            ),
            GroupingDimension.PRODUCT,
            PeriodRequirement.BASELINE_AND_COMPARISON,
            Additivity.ADDITIVE,
            ("validation:product_revenue_change_reconciles",),
            "grouped_decimal",
        ),
        _definition(
            "product_revenue_change_pct",
            "Product Revenue Change Percentage",
            "Product Revenue Change divided by Product Baseline Revenue, multiplied by 100, when the baseline denominator is non-zero.",
            MetricCategory.PRODUCT,
            ("product_id", "order_date", "line_revenue", "currency"),
            (
                _dependency("product_revenue", DependencyPeriodRole.BASELINE, grouping=GroupingDimension.PRODUCT),
                _dependency("product_revenue", DependencyPeriodRole.COMPARISON, grouping=GroupingDimension.PRODUCT),
            ),
            GroupingDimension.PRODUCT,
            PeriodRequirement.BASELINE_AND_COMPARISON,
            Additivity.DERIVED_NON_ADDITIVE,
            ("validation:product_revenue_change_pct_denominator",),
            "grouped_percentage",
            undefined=("product_baseline_revenue_equals_zero",),
        ),
        _definition(
            "product_absolute_contribution",
            "Product Absolute Contribution",
            "Product Revenue Change, used as the additive product contribution to net Revenue Change.",
            MetricCategory.PRODUCT,
            ("product_id", "order_date", "line_revenue", "currency"),
            (
                _dependency("product_revenue_change", DependencyPeriodRole.NO_PERIOD, grouping=GroupingDimension.PRODUCT),
                _dependency("revenue_change", DependencyPeriodRole.NO_PERIOD, grouping=GroupingDimension.NONE),
            ),
            GroupingDimension.PRODUCT,
            PeriodRequirement.BASELINE_AND_COMPARISON,
            Additivity.ADDITIVE,
            ("validation:product_contribution_sum_equals_total_revenue_change",),
            "grouped_decimal",
        ),
        _definition(
            "product_contribution_share",
            "Product Contribution Share",
            "Product Absolute Contribution divided by non-zero Total Revenue Change, multiplied by 100.",
            MetricCategory.PRODUCT,
            ("product_id", "order_date", "line_revenue", "currency"),
            (
                _dependency("product_absolute_contribution", DependencyPeriodRole.NO_PERIOD, grouping=GroupingDimension.PRODUCT),
                _dependency("revenue_change", DependencyPeriodRole.NO_PERIOD, grouping=GroupingDimension.NONE),
            ),
            GroupingDimension.PRODUCT,
            PeriodRequirement.BASELINE_AND_COMPARISON,
            Additivity.DERIVED_NON_ADDITIVE,
            ("validation:product_contribution_share_denominator",),
            "grouped_percentage",
            undefined=("total_revenue_change_equals_zero",),
            qualifications=("positive_and_negative_contributors_offset_against_net_change",),
        ),
        _definition(
            "category_revenue",
            "Category Revenue",
            "Eligible Revenue aggregated by authoritative category_id or governed Unclassified bucket.",
            MetricCategory.CATEGORY,
            ("category_id", "line_revenue", "currency", "order_date", "eligibility_status"),
            (_dependency("revenue", DependencyPeriodRole.SAME_AS_PARENT, grouping=GroupingDimension.NONE),),
            GroupingDimension.CATEGORY,
            PeriodRequirement.SINGLE_PERIOD,
            Additivity.ADDITIVE,
            ("validation:category_revenue_reconciles_to_total", "validation:unclassified_preserved"),
            "grouped_decimal",
            qualifications=("unclassified_category_present",),
        ),
        _definition(
            "category_orders",
            "Category Orders",
            "Distinct eligible order_id values containing at least one eligible line in the category bucket during the governed period.",
            MetricCategory.CATEGORY,
            ("category_id", "order_id", "order_date", "eligibility_status"),
            (_dependency("orders", DependencyPeriodRole.SAME_AS_PARENT, grouping=GroupingDimension.NONE),),
            GroupingDimension.CATEGORY,
            PeriodRequirement.SINGLE_PERIOD,
            Additivity.NON_ADDITIVE,
            ("validation:category_orders_distinct", "validation:orders_non_additive", "validation:unclassified_preserved"),
            "grouped_integer",
            currency="count of distinct governed orders",
        ),
        _definition(
            "category_revenue_change",
            "Category Revenue Change",
            "Category Comparison Revenue minus Category Baseline Revenue over the union of category buckets across complete periods.",
            MetricCategory.CATEGORY,
            ("category_id", "order_date", "line_revenue", "currency"),
            (
                _dependency("category_revenue", DependencyPeriodRole.BASELINE, grouping=GroupingDimension.CATEGORY),
                _dependency("category_revenue", DependencyPeriodRole.COMPARISON, grouping=GroupingDimension.CATEGORY),
            ),
            GroupingDimension.CATEGORY,
            PeriodRequirement.BASELINE_AND_COMPARISON,
            Additivity.ADDITIVE,
            ("validation:category_revenue_change_reconciles", "validation:unclassified_preserved"),
            "grouped_decimal",
        ),
        _definition(
            "category_revenue_change_pct",
            "Category Revenue Change Percentage",
            "Category Revenue Change divided by Category Baseline Revenue, multiplied by 100, when the baseline denominator is non-zero.",
            MetricCategory.CATEGORY,
            ("category_id", "order_date", "line_revenue", "currency"),
            (
                _dependency("category_revenue", DependencyPeriodRole.BASELINE, grouping=GroupingDimension.CATEGORY),
                _dependency("category_revenue", DependencyPeriodRole.COMPARISON, grouping=GroupingDimension.CATEGORY),
            ),
            GroupingDimension.CATEGORY,
            PeriodRequirement.BASELINE_AND_COMPARISON,
            Additivity.DERIVED_NON_ADDITIVE,
            ("validation:category_revenue_change_pct_denominator", "validation:unclassified_preserved"),
            "grouped_percentage",
            undefined=("category_baseline_revenue_equals_zero",),
            qualifications=("unclassified_category_present",),
        ),
        _definition(
            "category_absolute_contribution",
            "Category Absolute Contribution",
            "Category Revenue Change, used as the additive category contribution to net Revenue Change.",
            MetricCategory.CATEGORY,
            ("category_id", "order_date", "line_revenue", "currency"),
            (
                _dependency("category_revenue_change", DependencyPeriodRole.NO_PERIOD, grouping=GroupingDimension.CATEGORY),
                _dependency("revenue_change", DependencyPeriodRole.NO_PERIOD, grouping=GroupingDimension.NONE),
            ),
            GroupingDimension.CATEGORY,
            PeriodRequirement.BASELINE_AND_COMPARISON,
            Additivity.ADDITIVE,
            ("validation:category_contribution_sum_equals_total_revenue_change", "validation:unclassified_preserved"),
            "grouped_decimal",
            qualifications=("unclassified_category_present",),
        ),
        _definition(
            "category_contribution_share",
            "Category Contribution Share",
            "Category Absolute Contribution divided by non-zero Total Revenue Change, multiplied by 100.",
            MetricCategory.CATEGORY,
            ("category_id", "order_date", "line_revenue", "currency"),
            (
                _dependency("category_absolute_contribution", DependencyPeriodRole.NO_PERIOD, grouping=GroupingDimension.CATEGORY),
                _dependency("revenue_change", DependencyPeriodRole.NO_PERIOD, grouping=GroupingDimension.NONE),
            ),
            GroupingDimension.CATEGORY,
            PeriodRequirement.BASELINE_AND_COMPARISON,
            Additivity.DERIVED_NON_ADDITIVE,
            ("validation:category_contribution_share_denominator", "validation:unclassified_preserved"),
            "grouped_percentage",
            undefined=("total_revenue_change_equals_zero",),
            qualifications=("unclassified_category_present", "positive_and_negative_contributors_offset_against_net_change"),
        ),
        _definition(
            "leading_positive_contributors",
            "Leading Positive Contributors",
            "Entities with Absolute Contribution greater than zero, ordered by unrounded Absolute Contribution descending.",
            MetricCategory.RANKING,
            ("line_revenue", "currency", "order_date"),
            (
                _dependency(
                    "product_absolute_contribution",
                    DependencyPeriodRole.NO_PERIOD,
                    grouping=GroupingDimension.PRODUCT,
                    applies_to_groupings=(GroupingDimension.PRODUCT,),
                ),
                _dependency(
                    "category_absolute_contribution",
                    DependencyPeriodRole.NO_PERIOD,
                    grouping=GroupingDimension.CATEGORY,
                    applies_to_groupings=(GroupingDimension.CATEGORY,),
                ),
            ),
            None,
            PeriodRequirement.BASELINE_AND_COMPARISON,
            Additivity.RANKING,
            ("validation:positive_ranking_uses_absolute_contribution",),
            "ranking",
            supported_groupings=(GroupingDimension.PRODUCT, GroupingDimension.CATEGORY),
            required_fields_by_grouping={
                GroupingDimension.PRODUCT: ("product_id", "line_revenue", "currency", "order_date"),
                GroupingDimension.CATEGORY: ("category_id", "line_revenue", "currency", "order_date"),
            },
        ),
        _definition(
            "leading_negative_contributors",
            "Leading Negative Contributors",
            "Entities with Absolute Contribution less than zero, ordered from most negative to least negative using unrounded Absolute Contribution.",
            MetricCategory.RANKING,
            ("line_revenue", "currency", "order_date"),
            (
                _dependency(
                    "product_absolute_contribution",
                    DependencyPeriodRole.NO_PERIOD,
                    grouping=GroupingDimension.PRODUCT,
                    applies_to_groupings=(GroupingDimension.PRODUCT,),
                ),
                _dependency(
                    "category_absolute_contribution",
                    DependencyPeriodRole.NO_PERIOD,
                    grouping=GroupingDimension.CATEGORY,
                    applies_to_groupings=(GroupingDimension.CATEGORY,),
                ),
            ),
            None,
            PeriodRequirement.BASELINE_AND_COMPARISON,
            Additivity.RANKING,
            ("validation:negative_ranking_uses_absolute_contribution",),
            "ranking",
            supported_groupings=(GroupingDimension.PRODUCT, GroupingDimension.CATEGORY),
            required_fields_by_grouping={
                GroupingDimension.PRODUCT: ("product_id", "line_revenue", "currency", "order_date"),
                GroupingDimension.CATEGORY: ("category_id", "line_revenue", "currency", "order_date"),
            },
        ),
    )
)
