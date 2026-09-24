"""Static R6-1 authority for the three approved MVP hypothesis families."""

from __future__ import annotations

import re
from typing import Any, Mapping, Self

from pydantic import Field, model_validator

from commerce_lens.contracts.common import ContractBase
from commerce_lens.contracts.hypotheses import (
    CandidateProposal,
    FamilyActivationPolicy,
    FamilyClassification,
    HypothesisFamilyDefinition,
    hypothesis_family_semantic_fingerprint,
)
from commerce_lens.contracts.required_evidence import (
    ApplicabilityLevel,
    ApplicabilityState,
    DependencyClassification,
    DependencyRequirement,
    DimensionRequirement,
    EvidenceDimension,
    EvidenceRole,
    HypothesisFamilyRequirementTemplate,
    MeasurementClassification,
    MeasurementRequirement,
    requirement_template_semantic_fingerprint,
)
from commerce_lens.evidence.identifiers import canonical_json_fingerprint


REGISTRY_ID = "commerce_lens_r6_mvp_hypothesis_families"
REGISTRY_VERSION = "1.0.0"
FAMILY_VERSION = "1.0.0"
ACTIVE_FAMILY_IDS = frozenset(
    {
        "product_composition_association",
        "discounting_association",
        "external_market_association",
    }
)


class HypothesisFamilyRegistry(ContractBase):
    registry_id: str = Field(min_length=1)
    registry_version: str = Field(min_length=1)
    registry_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    active_families: tuple[HypothesisFamilyDefinition, ...] = Field(min_length=3, max_length=3)
    requirement_templates: tuple[HypothesisFamilyRequirementTemplate, ...] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def validate_registry(self) -> Self:
        family_ids = {family.family_id for family in self.active_families}
        if family_ids != ACTIVE_FAMILY_IDS or len(family_ids) != len(self.active_families):
            raise ValueError("R6-1 registry must contain exactly the three approved MVP families")
        template_by_id = {template.template_id: template for template in self.requirement_templates}
        if len(template_by_id) != len(self.requirement_templates):
            raise ValueError("requirement template IDs must be unique")
        for family in self.active_families:
            template = template_by_id.get(family.requirement_template_ref)
            if template is None:
                raise ValueError(f"family {family.family_id} has no bound requirement template")
            if (
                template.template_version != family.requirement_template_version
                or template.template_fingerprint != family.requirement_template_fingerprint
                or template.family_id != family.family_id
                or template.family_version != family.family_version
            ):
                raise ValueError(f"family {family.family_id} template binding mismatch")
        if self.registry_fingerprint != family_registry_semantic_fingerprint(self):
            raise ValueError("registry_fingerprint does not match active family authority")
        return self

    def get_family(self, family_id: str, family_version: str = FAMILY_VERSION) -> HypothesisFamilyDefinition:
        for family in self.active_families:
            if family.family_id == family_id:
                if family.family_version != family_version:
                    raise ValueError(f"unsupported family version for {family_id}: {family_version}")
                return family
        raise ValueError(f"unknown hypothesis family: {family_id}")

    def get_requirement_template(self, family_id: str) -> HypothesisFamilyRequirementTemplate:
        family = self.get_family(family_id)
        for template in self.requirement_templates:
            if template.template_id == family.requirement_template_ref:
                return template
        raise ValueError(f"missing requirement template for family: {family_id}")

    def validate_candidate(self, candidate: CandidateProposal) -> CandidateProposal:
        family = self.get_family(candidate.family_id, candidate.family_version)
        values = {item.slot: item.value for item in candidate.structured_slot_values}
        supplied = set(values)
        allowed = set(family.allowed_proposition_slots)
        unsupported = supplied - allowed
        if unsupported:
            raise ValueError(f"unsupported proposition slots: {', '.join(sorted(unsupported))}")
        missing = set(family.required_proposition_slots) - supplied
        if missing:
            raise ValueError(f"missing required proposition slots: {', '.join(sorted(missing))}")
        if candidate.display_template_id is not None and candidate.display_template_id not in family.display_template_ids:
            raise ValueError("candidate display_template_id is not approved for its family")
        if candidate.family_id == "product_composition_association":
            identity = _normalized_values(values["product_identity_ref"])
            if "product_name" in identity:
                raise ValueError("product_name cannot substitute for governed product identity")
        elif candidate.family_id == "discounting_association":
            discount_authority_values = _normalized_values(values["original_or_list_price_ref"])
            discount_authority_values |= _normalized_values(values["discount_semantics_ref"])
            forbidden = discount_authority_values & {"unit_price", "line_revenue", "aov", "revenue"}
            if forbidden:
                raise ValueError(
                    "discount authority cannot be inferred from: " + ", ".join(sorted(forbidden))
                )
        elif candidate.family_id == "external_market_association":
            if not values.get("explicit_activation_ref"):
                raise ValueError("external family requires explicit user-request activation metadata")
        return candidate


def family_registry_semantic_fingerprint(
    registry: HypothesisFamilyRegistry | Mapping[str, Any],
) -> str:
    if isinstance(registry, HypothesisFamilyRegistry):
        data = registry.model_dump(mode="python")
    else:
        data = registry
    families = data["active_families"]
    material = []
    for family in families:
        if isinstance(family, HypothesisFamilyDefinition):
            item = {
                "family_id": family.family_id,
                "family_version": family.family_version,
                "family_fingerprint": family.family_fingerprint,
                "requirement_template_ref": family.requirement_template_ref,
                "requirement_template_version": family.requirement_template_version,
                "requirement_template_fingerprint": family.requirement_template_fingerprint,
            }
        else:
            item = {
                key: family[key]
                for key in (
                    "family_id",
                    "family_version",
                    "family_fingerprint",
                    "requirement_template_ref",
                    "requirement_template_version",
                    "requirement_template_fingerprint",
                )
            }
        material.append(item)
    return canonical_json_fingerprint(
        {
            "registry_id": data["registry_id"],
            "registry_version": data["registry_version"],
            "active_families": sorted(material, key=lambda item: item["family_id"]),
        }
    )


def _dimension_requirements(family_id: str) -> tuple[DimensionRequirement, ...]:
    cross_role = {
        EvidenceDimension.TEMPORAL_ALIGNMENT,
        EvidenceDimension.POPULATION_ALIGNMENT,
        EvidenceDimension.METRIC_COMPATIBILITY,
        EvidenceDimension.UNIT_CURRENCY_COMPATIBILITY,
    }
    shared = {EvidenceDimension.PROVENANCE, EvidenceDimension.VALIDATION_STATUS}
    requirements = []
    for dimension in EvidenceDimension:
        if dimension in cross_role:
            level = ApplicabilityLevel.CROSS_ROLE_RELATIONSHIP
        elif dimension in shared:
            level = ApplicabilityLevel.SHARED_AUTHORITY
        elif dimension is EvidenceDimension.RELEVANCE:
            level = ApplicabilityLevel.PROPOSITION
        else:
            level = ApplicabilityLevel.ROLE
        conditional_ref = {
            EvidenceDimension.METRIC_COMPATIBILITY: (
                "R3:metric_compatibility_when_governed_metric_or_metric_derived_construct_participates"
            ),
            EvidenceDimension.UNIT_CURRENCY_COMPATIBILITY: (
                "R3:unit_currency_compatibility_when_material_unit_or_monetary_evidence_participates"
            ),
        }.get(dimension)
        applicability = (
            ApplicabilityState.CONDITIONAL
            if conditional_ref is not None
            else ApplicabilityState.REQUIRED
        )
        requirements.append(
            DimensionRequirement(
                dimension=dimension,
                applicability=applicability,
                applicability_level=level,
                requirement_ref=f"{family_id}:{dimension.value}",
                applicability_condition_ref=conditional_ref,
                controlling_authority_refs=("R1_EVIDENCE_CONTRACT", "R3_REQUIRED_EVIDENCE_MATRIX"),
                failure_consequence="blocks diagnostic test eligibility",
            )
        )
    return tuple(requirements)


def _template(
    *,
    family_id: str,
    slots: tuple[str, ...],
    roles: tuple[EvidenceRole, ...],
    dependencies: tuple[DependencyRequirement, ...],
    measurements: tuple[MeasurementRequirement, ...],
    blockers: tuple[str, ...],
    maximum_evidence_use: str,
    substitutions: tuple[str, ...],
) -> HypothesisFamilyRequirementTemplate:
    data: dict[str, Any] = {
        "template_id": f"r3-template:{family_id}",
        "template_version": FAMILY_VERSION,
        "family_id": family_id,
        "family_version": FAMILY_VERSION,
        "allowed_proposition_slots": slots,
        "required_evidence_roles": roles,
        "dimension_requirements": _dimension_requirements(family_id),
        "dependency_source_classifications": dependencies,
        "measurement_classifications": measurements,
        "method_specific_requirement_slots": ("method_ref", "support_criterion_ref", "validation_profile_ref"),
        "known_blocking_conditions": blockers,
        "maximum_evidence_use": maximum_evidence_use,
        "prohibited_evidence_substitutions": substitutions,
    }
    data["template_fingerprint"] = requirement_template_semantic_fingerprint(data)
    return HypothesisFamilyRequirementTemplate(**data)


PRODUCT_SLOTS = (
    "outcome_ref",
    "baseline_period_ref",
    "comparison_period_ref",
    "baseline_population_ref",
    "comparison_population_ref",
    "scope_ref",
    "product_identity_ref",
    "monetary_observation_ref",
    "source_observation_refs",
    "optional_r4_result_ref",
)
DISCOUNT_SLOTS = (
    "outcome_ref",
    "baseline_period_ref",
    "comparison_period_ref",
    "baseline_population_ref",
    "comparison_population_ref",
    "scope_ref",
    "original_or_list_price_ref",
    "discount_semantics_ref",
    "monetary_observation_ref",
    "source_observation_refs",
)
EXTERNAL_SLOTS = (
    "outcome_ref",
    "baseline_period_ref",
    "comparison_period_ref",
    "baseline_population_ref",
    "comparison_population_ref",
    "scope_ref",
    "external_factor_ref",
    "external_evidence_dependency_ref",
    "source_observation_refs",
    "explicit_activation_ref",
)


PRODUCT_TEMPLATE = _template(
    family_id="product_composition_association",
    slots=PRODUCT_SLOTS,
    roles=(
        EvidenceRole.OBSERVED_OUTCOME,
        EvidenceRole.EXPLANATORY_VARIABLE,
        EvidenceRole.POPULATION_ELIGIBILITY,
        EvidenceRole.COMPLETENESS_COVERAGE,
        EvidenceRole.SOURCE_AUTHORITY_PROVENANCE,
        EvidenceRole.IDENTITY_JOIN,
        EvidenceRole.UNIT_CURRENCY,
    ),
    dependencies=(
        DependencyRequirement(requirement_ref="governed_product_id", classification=DependencyClassification.INTERNAL),
        DependencyRequirement(requirement_ref="line_revenue_observation", classification=DependencyClassification.INTERNAL),
    ),
    measurements=(
        MeasurementRequirement(
            requirement_ref="product_composition_measurement",
            role=EvidenceRole.EXPLANATORY_VARIABLE,
            classification=MeasurementClassification.GOVERNED_TRANSFORMED_MEASUREMENT,
            permitted_use="bounded future non-causal association test",
        ),
    ),
    blockers=(
        "missing governed product_id identity",
        "period or population misalignment",
        "missing governed method/support/validation authority",
    ),
    maximum_evidence_use="proposal for a future bounded non-causal association test",
    substitutions=(
        "product_name for product identity",
        "unit_price for governed price evidence",
        "R4 Entry/Exit/Continuing as diagnostic support",
    ),
)

DISCOUNT_TEMPLATE = _template(
    family_id="discounting_association",
    slots=DISCOUNT_SLOTS,
    roles=(
        EvidenceRole.OBSERVED_OUTCOME,
        EvidenceRole.EXPLANATORY_VARIABLE,
        EvidenceRole.POPULATION_ELIGIBILITY,
        EvidenceRole.COMPLETENESS_COVERAGE,
        EvidenceRole.SOURCE_AUTHORITY_PROVENANCE,
        EvidenceRole.UNIT_CURRENCY,
    ),
    dependencies=(
        DependencyRequirement(requirement_ref="original_or_list_price", classification=DependencyClassification.INTERNAL),
        DependencyRequirement(requirement_ref="governed_discount_semantics", classification=DependencyClassification.INTERNAL),
    ),
    measurements=(
        MeasurementRequirement(
            requirement_ref="discount_measurement",
            role=EvidenceRole.EXPLANATORY_VARIABLE,
            classification=MeasurementClassification.INFERRED_CONSTRUCT,
            permitted_use="none until original/list-price and discount semantics are governed",
        ),
    ),
    blockers=(
        "missing original or list-price evidence",
        "missing governed discount semantics",
        "missing governed method/support/validation authority",
    ),
    maximum_evidence_use="untested discounting hypothesis with missing internal evidence",
    substitutions=("line_revenue", "Revenue", "AOV", "unit_price"),
)

EXTERNAL_TEMPLATE = _template(
    family_id="external_market_association",
    slots=EXTERNAL_SLOTS,
    roles=(
        EvidenceRole.OBSERVED_OUTCOME,
        EvidenceRole.EXPLANATORY_VARIABLE,
        EvidenceRole.POPULATION_ELIGIBILITY,
        EvidenceRole.COMPLETENESS_COVERAGE,
        EvidenceRole.SOURCE_AUTHORITY_PROVENANCE,
    ),
    dependencies=(
        DependencyRequirement(requirement_ref="external_market_evidence", classification=DependencyClassification.EXTERNAL),
    ),
    measurements=(
        MeasurementRequirement(
            requirement_ref="external_factor_measurement",
            role=EvidenceRole.EXPLANATORY_VARIABLE,
            classification=MeasurementClassification.INFERRED_CONSTRUCT,
            permitted_use="none until separately governed external admission exists",
        ),
    ),
    blockers=(
        "explicit user request absent",
        "external evidence not governed and admitted",
        "missing governed method/support/validation authority",
    ),
    maximum_evidence_use="proposal requiring separately governed external evidence",
    substitutions=(
        "automatic browsing",
        "model general knowledge as evidence",
        "causal conclusion",
        "current support",
        "confidence or likelihood wording",
    ),
)


def _family(
    *,
    family_id: str,
    display_name: str,
    template: HypothesisFamilyRequirementTemplate,
    classifications: tuple[FamilyClassification, ...],
    activation_policy: FamilyActivationPolicy,
    required_slots: tuple[str, ...],
    permitted_meanings: tuple[str, ...],
    prohibited_meanings: tuple[str, ...],
    dependencies: tuple[DependencyClassification, ...],
    display_template_id: str,
) -> HypothesisFamilyDefinition:
    data: dict[str, Any] = {
        "family_id": family_id,
        "family_version": FAMILY_VERSION,
        "classifications": classifications,
        "activation_policy": activation_policy,
        "requirement_template_ref": template.template_id,
        "requirement_template_version": template.template_version,
        "requirement_template_fingerprint": template.template_fingerprint,
        "allowed_proposition_slots": template.allowed_proposition_slots,
        "required_proposition_slots": required_slots,
        "permitted_meanings": permitted_meanings,
        "prohibited_meanings": prohibited_meanings,
        "dependency_classifications": dependencies,
        "display_template_ids": (display_template_id,),
        "registry_can_establish_execution_eligibility": False,
        "display_name": display_name,
    }
    data["family_fingerprint"] = hypothesis_family_semantic_fingerprint(data)
    return HypothesisFamilyDefinition(**data)


PRODUCT_COMPOSITION_ASSOCIATION = _family(
    family_id="product_composition_association",
    display_name="Product composition association",
    template=PRODUCT_TEMPLATE,
    classifications=(FamilyClassification.MVP,),
    activation_policy=FamilyActivationPolicy.STANDARD,
    required_slots=tuple(slot for slot in PRODUCT_SLOTS if slot != "optional_r4_result_ref"),
    permitted_meanings=(
        "future test of bounded non-causal association between governed product composition and Revenue Change",
        "hypothesis not tested",
    ),
    prohibited_meanings=(
        "composition actually changed",
        "association exists",
        "explanation or causality",
        "price, discount, demand, or preference effect",
        "primacy or support",
    ),
    dependencies=(DependencyClassification.INTERNAL,),
    display_template_id="r6-product-composition-untested-v1",
)

DISCOUNTING_ASSOCIATION = _family(
    family_id="discounting_association",
    display_name="Discounting association",
    template=DISCOUNT_TEMPLATE,
    classifications=(FamilyClassification.MVP, FamilyClassification.MISSING_INTERNAL_EVIDENCE_ONLY),
    activation_policy=FamilyActivationPolicy.STANDARD,
    required_slots=DISCOUNT_SLOTS,
    permitted_meanings=("untested discounting association proposal requiring unavailable governed evidence",),
    prohibited_meanings=(
        "line_revenue, Revenue, AOV, or unit_price proves discounting",
        "discounting occurred or explains the outcome",
        "causal, supported, confidence, or likelihood claim",
    ),
    dependencies=(DependencyClassification.INTERNAL,),
    display_template_id="r6-discounting-untested-v1",
)

EXTERNAL_MARKET_ASSOCIATION = _family(
    family_id="external_market_association",
    display_name="External market association",
    template=EXTERNAL_TEMPLATE,
    classifications=(FamilyClassification.MVP, FamilyClassification.EXTERNAL_EVIDENCE_REQUIRED),
    activation_policy=FamilyActivationPolicy.EXPLICIT_USER_REQUEST_ONLY,
    required_slots=EXTERNAL_SLOTS,
    permitted_meanings=("explicitly requested untested proposal requiring governed external evidence",),
    prohibited_meanings=(
        "automatic browsing or acquisition",
        "model general knowledge as evidence",
        "causal conclusion or current support",
        "confidence or likelihood wording",
    ),
    dependencies=(DependencyClassification.EXTERNAL,),
    display_template_id="r6-external-market-untested-v1",
)


_REGISTRY_DATA: dict[str, Any] = {
    "registry_id": REGISTRY_ID,
    "registry_version": REGISTRY_VERSION,
    "active_families": (
        PRODUCT_COMPOSITION_ASSOCIATION,
        DISCOUNTING_ASSOCIATION,
        EXTERNAL_MARKET_ASSOCIATION,
    ),
    "requirement_templates": (PRODUCT_TEMPLATE, DISCOUNT_TEMPLATE, EXTERNAL_TEMPLATE),
}
_REGISTRY_DATA["registry_fingerprint"] = family_registry_semantic_fingerprint(_REGISTRY_DATA)
MVP_FAMILY_REGISTRY = HypothesisFamilyRegistry(**_REGISTRY_DATA)


def _normalized_values(value: Any) -> set[str]:
    values = value if isinstance(value, tuple) else (value,)
    normalized: set[str] = set()
    for item in values:
        raw = str(item).strip().lower()
        normalized.add(raw)
        normalized.update(part for part in re.split(r"[^a-z0-9_]+", raw) if part)
    return normalized


__all__ = [
    "ACTIVE_FAMILY_IDS",
    "DISCOUNTING_ASSOCIATION",
    "EXTERNAL_MARKET_ASSOCIATION",
    "HypothesisFamilyRegistry",
    "MVP_FAMILY_REGISTRY",
    "PRODUCT_COMPOSITION_ASSOCIATION",
    "family_registry_semantic_fingerprint",
]
