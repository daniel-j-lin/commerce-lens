"""Static authority for the single approved R7 MVP diagnostic method."""

from __future__ import annotations

from commerce_lens.contracts.r7 import (
    DiagnosticMethodDefinition,
    DiagnosticMethodImplementationBinding,
    DiagnosticSupportCriterionDefinition,
    DiagnosticValidationProfile,
    R7AuthorityReference,
    implementation_binding_fingerprint,
    method_definition_fingerprint,
    support_criterion_fingerprint,
    validation_profile_fingerprint,
)


METHOD_ID = "weekly_product_presence_revenue_association"
METHOD_VERSION = "1.0.0"
FAMILY_ID = "product_composition_association"
FAMILY_VERSION = "1.0.0"
FAMILY_FINGERPRINT = "757eae48d3b72d2caa83e3d614b5fd50eccf34f1a4c9d11d0a24bdb06fadead2"


def _support() -> DiagnosticSupportCriterionDefinition:
    data = {
        "criterion_id": "weekly_product_presence_revenue_association_support",
        "criterion_version": "1.0.0",
        "support_maximum": -0.5,
        "contradiction_minimum": 0.5,
        "inconclusive_reasons": (
            "total_valid_weeks<8", "baseline_valid_weeks<4", "comparison_valid_weeks<4",
            "constant_distance", "constant_revenue_deviation", "undefined_denominator",
            "observation_construction_failed",
        ),
    }
    data["criterion_fingerprint"] = support_criterion_fingerprint(data)
    return DiagnosticSupportCriterionDefinition(**data)


def _validation() -> DiagnosticValidationProfile:
    data = {
        "profile_id": "weekly_product_presence_revenue_association_validation",
        "profile_version": "1.0.0",
        "required_checks": (
            "authority_bindings", "iso_full_week_membership", "baseline_product_set",
            "jaccard_domain", "weekly_revenue_reconciliation", "baseline_median",
            "revenue_deviation", "average_ranks", "spearman_recomputation",
            "finite_numeric_domain", "sample_minimums", "vector_variation",
            "decision_boundary", "semantic_fingerprint",
        ),
    }
    data["profile_fingerprint"] = validation_profile_fingerprint(data)
    return DiagnosticValidationProfile(**data)


def _implementation() -> DiagnosticMethodImplementationBinding:
    data = {
        "implementation_id": "commerce_lens_r7_weekly_product_presence_revenue_association",
        "implementation_version": "1.0.0",
        "runtime": "python_stdlib_duckdb",
        "week_convention": "ISO-8601 Monday-Sunday",
        "numeric_convention": "IEEE-754 binary64 Spearman from deterministic average ranks",
        "dependencies": ("python>=3.11", "duckdb>=1.0,<2"),
    }
    data["implementation_fingerprint"] = implementation_binding_fingerprint(data)
    return DiagnosticMethodImplementationBinding(**data)


SUPPORT_CRITERION = _support()
VALIDATION_PROFILE = _validation()
IMPLEMENTATION_BINDING = _implementation()


def _ref(identifier: str, version: str, fingerprint: str) -> R7AuthorityReference:
    return R7AuthorityReference(authority_id=identifier, authority_version=version, authority_fingerprint=fingerprint)


def _method() -> DiagnosticMethodDefinition:
    data = {
        "method_id": METHOD_ID,
        "method_version": METHOD_VERSION,
        "family_id": FAMILY_ID,
        "family_version": FAMILY_VERSION,
        "family_fingerprint": FAMILY_FINGERPRINT,
        "intended_use": "diagnostic",
        "observation_unit": "full_iso_calendar_week",
        "predictor": "Jaccard distance of weekly active product_id set from baseline product_id set",
        "outcome": "weekly governed Revenue minus median governed Revenue across valid full baseline weeks",
        "association_measure": "spearman_average_rank",
        "required_variables": ("field:product_id", "field:line_revenue"),
        "required_source_class": "GOVERNED_INTERNAL",
        "fixed_parameters": {"minimum_weeks": 8, "minimum_baseline_weeks": 4, "minimum_comparison_weeks": 4, "weighting": "none"},
        "maximum_permitted_meaning": "bounded observed non-causal weekly association; one plausible contributor worth retaining",
        "prohibited_meanings": ("causality", "primary_or_sole_explanation", "statistical_significance", "generalization", "finding_or_claim_permission"),
        "limitations": ("time_trend", "seasonality", "promotion_timing", "inventory", "external_shocks", "customer_mix", "other_confounders"),
        "support_criterion_ref": _ref(SUPPORT_CRITERION.criterion_id, SUPPORT_CRITERION.criterion_version, SUPPORT_CRITERION.criterion_fingerprint),
        "validation_profile_ref": _ref(VALIDATION_PROFILE.profile_id, VALIDATION_PROFILE.profile_version, VALIDATION_PROFILE.profile_fingerprint),
        "implementation_ref": _ref(IMPLEMENTATION_BINDING.implementation_id, IMPLEMENTATION_BINDING.implementation_version, IMPLEMENTATION_BINDING.implementation_fingerprint),
    }
    data["method_fingerprint"] = method_definition_fingerprint(data)
    return DiagnosticMethodDefinition(**data)


METHOD_DEFINITION = _method()


def authority_ref(value) -> R7AuthorityReference:
    if isinstance(value, DiagnosticMethodDefinition):
        return _ref(value.method_id, value.method_version, value.method_fingerprint)
    if isinstance(value, DiagnosticSupportCriterionDefinition):
        return _ref(value.criterion_id, value.criterion_version, value.criterion_fingerprint)
    if isinstance(value, DiagnosticValidationProfile):
        return _ref(value.profile_id, value.profile_version, value.profile_fingerprint)
    return _ref(value.implementation_id, value.implementation_version, value.implementation_fingerprint)


class R7MethodAuthorityRegistry:
    def authenticate(self, method: R7AuthorityReference, family_id: str, family_version: str, family_fingerprint: str) -> DiagnosticMethodDefinition:
        if method != authority_ref(METHOD_DEFINITION):
            raise ValueError("method_unregistered_or_stale")
        if (family_id, family_version, family_fingerprint) != (FAMILY_ID, FAMILY_VERSION, FAMILY_FINGERPRINT):
            raise ValueError("method_family_mismatch")
        return METHOD_DEFINITION


R7_METHOD_REGISTRY = R7MethodAuthorityRegistry()
