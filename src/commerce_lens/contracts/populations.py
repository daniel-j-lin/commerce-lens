"""Governed pre-execution population definition contracts."""

from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from commerce_lens.contracts.common import ContractBase, GroupingDimension, PeriodDefinition, ScopeDefinition


POPULATION_DEFINITION_VERSION = "population_mvp_v1"
ELIGIBILITY_RULE_REF = "canonical_dictionary:27:phase2_governed_eligible_population"
CATEGORY_UNCLASSIFIED_RULE_REF = "canonical_dictionary:20:unclassified_bucket"


class PopulationPeriodRole(str, Enum):
    BASELINE = "baseline"
    COMPARISON = "comparison"


class PopulationDefinition(ContractBase):
    population_id: str = Field(min_length=1)
    definition_version: str = POPULATION_DEFINITION_VERSION
    canonical_dataset_ref_id: str = Field(min_length=1)
    dataset_ref_id: str = Field(min_length=1)
    period: PeriodDefinition
    period_role: PopulationPeriodRole
    eligibility_rule_ref: str = ELIGIBILITY_RULE_REF
    currency_basis_ref: str = Field(min_length=1)
    scope: ScopeDefinition
    grouping: GroupingDimension = GroupingDimension.NONE
    grouping_keys: tuple[str, ...] = ()
    supported_filter_fields: tuple[str, ...] = ()
    supported_filter_operators: tuple[str, ...] = ()
    preserves_unclassified_category: bool = False
    population_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_grouping_keys(self) -> "PopulationDefinition":
        expected = {
            GroupingDimension.NONE: (),
            GroupingDimension.PRODUCT: ("product_id",),
            GroupingDimension.CATEGORY: ("category_id",),
            GroupingDimension.PRODUCT_AND_CATEGORY: ("product_id", "category_id"),
        }[self.grouping]
        if self.grouping_keys != expected:
            raise ValueError("population grouping_keys must match the governed grouping mode")
        if self.grouping in (GroupingDimension.CATEGORY, GroupingDimension.PRODUCT_AND_CATEGORY):
            if not self.preserves_unclassified_category:
                raise ValueError("category populations must preserve governed Unclassified attribution")
        return self
