from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from commerce_lens.application.r4_service import R4RunOutcome, run_r4_decomposition
from commerce_lens.contracts.common import ClaimType, GroupingDimension, ScopeDefinition
from commerce_lens.contracts.evidence import EvidenceRole
from commerce_lens.contracts.r4 import R4DecompositionRequest
from commerce_lens.evidence.admissibility import evaluate_evidence_admissibility
from tests.evidence.test_admissibility import _fixture, _validate


@dataclass(frozen=True)
class R4Fixture:
    scalar: object
    baseline: object
    comparison: object
    change: object
    baseline_evidence: object
    comparison_evidence: object
    change_evidence: object
    baseline_population: object
    comparison_population: object
    request: R4DecompositionRequest


def make_r4_fixture(
    tmp_path: Path,
    rows: list[dict[str, str]],
    *,
    scope: ScopeDefinition | None = None,
) -> R4Fixture:
    scalar = _fixture(tmp_path, ("revenue_change", "revenue"), rows, scope=scope)
    scalar.metadata_store.insert_artifact_reference(scalar.canonical.artifact)
    scalar.metadata_store.insert_canonical_dataset(scalar.canonical)
    baseline = _validate(scalar, "revenue", period_ref="baseline").validated_result
    comparison = _validate(scalar, "revenue", period_ref="comparison").validated_result
    change = _validate(
        scalar,
        "revenue_change",
        period_ref="comparison",
        dependencies=(baseline, comparison),
    ).validated_result
    evidence = tuple(
        evaluate_evidence_admissibility(
            request_id=scalar.request.request_id,
            sufficiency_id=scalar.sufficiency.sufficiency_id,
            validated_result_id=result.validated_result_id,
            claim_type=ClaimType.DESCRIPTIVE,
            evidence_role=EvidenceRole.METRIC_VALUE,
            artifact_store=scalar.artifact_store,
            metadata_store=scalar.metadata_store,
        ).admissible_evidence
        for result in (baseline, comparison, change)
    )
    assert all(item is not None for item in evidence)
    baseline_evidence, comparison_evidence, change_evidence = evidence
    baseline_population = next(
        population
        for population in scalar.plan.population_definitions
        if population.period_role.value == "baseline" and population.grouping is GroupingDimension.NONE
    )
    comparison_population = next(
        population
        for population in scalar.plan.population_definitions
        if population.period_role.value == "comparison" and population.grouping is GroupingDimension.NONE
    )
    request = R4DecompositionRequest(
        analysis_request_ref=scalar.request.request_id,
        sufficiency_ref=scalar.sufficiency.sufficiency_id,
        plan_ref=scalar.plan.plan_id,
        plan_fingerprint=scalar.plan.plan_fingerprint,
        canonical_dataset_ref=scalar.canonical.canonical_dataset_id,
        canonical_dataset_fingerprint=scalar.canonical.content_fingerprint,
        baseline_population_ref=baseline_population.population_id,
        baseline_population_fingerprint=baseline_population.population_fingerprint,
        comparison_population_ref=comparison_population.population_id,
        comparison_population_fingerprint=comparison_population.population_fingerprint,
        baseline_revenue_validated_result_ref=baseline.validated_result_id,
        comparison_revenue_validated_result_ref=comparison.validated_result_id,
        revenue_change_validated_result_ref=change.validated_result_id,
        baseline_revenue_evidence_ref=baseline_evidence.evidence_id,
        baseline_revenue_evidence_fingerprint=baseline_evidence.evidence_fingerprint,
        comparison_revenue_evidence_ref=comparison_evidence.evidence_id,
        comparison_revenue_evidence_fingerprint=comparison_evidence.evidence_fingerprint,
        revenue_change_evidence_ref=change_evidence.evidence_id,
        revenue_change_evidence_fingerprint=change_evidence.evidence_fingerprint,
    )
    return R4Fixture(
        scalar,
        baseline,
        comparison,
        change,
        baseline_evidence,
        comparison_evidence,
        change_evidence,
        baseline_population,
        comparison_population,
        request,
    )


def run_r4(fixture: R4Fixture, *, request: R4DecompositionRequest | None = None) -> R4RunOutcome:
    scalar = fixture.scalar
    return run_r4_decomposition(
        request=request or fixture.request,
        plan=scalar.plan,
        canonical_dataset=scalar.canonical,
        artifact_store=scalar.artifact_store,
        metadata_store=scalar.metadata_store,
    )
