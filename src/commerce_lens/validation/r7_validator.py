"""Independent reconstruction validator for R7 diagnostic results."""

from __future__ import annotations

from dataclasses import dataclass

from commerce_lens.contracts.common import utc_now
from commerce_lens.contracts.evidence import CanonicalDatasetReference
from commerce_lens.contracts.populations import PopulationDefinition
from commerce_lens.contracts.r7 import (
    DiagnosticTestRequest, DiagnosticValidationCheck, DiagnosticValidationRecord,
    ExecutedDiagnosticResult, R7ValidationStatus, ValidatedDiagnosticResult,
)
from commerce_lens.engine.r7_execution import _load_transactions, _verified_path, calculate_r7_result
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, generate_id, stable_content_id
from commerce_lens.persistence.artifact_store import ArtifactStore


@dataclass(frozen=True)
class R7ValidationOutcome:
    validation_record: DiagnosticValidationRecord
    validated_result: ValidatedDiagnosticResult | None


def validate_r7_result(*, request: DiagnosticTestRequest, executed_result: ExecutedDiagnosticResult,
                       canonical_dataset: CanonicalDatasetReference, baseline_population: PopulationDefinition,
                       comparison_population: PopulationDefinition, artifact_store: ArtifactStore) -> R7ValidationOutcome:
    started = utc_now(); event_id = generate_id("r7val")
    path = _verified_path(canonical_dataset, artifact_store)
    rows = _load_transactions(path, baseline_population, request.baseline_start, request.comparison_end)
    expected = calculate_r7_result(request=request, transactions=rows, execution_event_id=executed_result.execution_event_id)
    comparisons = {
        "method_version_fingerprint": executed_result.method == request.method,
        "family_and_request_binding": executed_result.test_request_ref == request.test_request_id and executed_result.request_fingerprint == request.request_fingerprint,
        "weekly_bucket_membership_and_full_week_rule": executed_result.observations == expected.observations and executed_result.excluded_observations == expected.excluded_observations,
        "baseline_product_set_reconstruction": executed_result.baseline_product_set_fingerprint == expected.baseline_product_set_fingerprint and executed_result.baseline_product_count == expected.baseline_product_count,
        "weekly_revenue_median_deviation_and_ranks": executed_result.baseline_weekly_revenue_reference == expected.baseline_weekly_revenue_reference,
        "rho_and_finite_numeric_domain": executed_result.spearman_rho == expected.spearman_rho,
        "sample_minimums_and_vector_variation": executed_result.inconclusive_reasons == expected.inconclusive_reasons,
        "semantic_fingerprint": executed_result.result_fingerprint == expected.result_fingerprint,
    }
    checks = tuple(DiagnosticValidationCheck(check_id=key, passed=value, failure_code=None if value else "R7_VALIDATION_MISMATCH") for key, value in comparisons.items())
    status = R7ValidationStatus.PASSED if all(comparisons.values()) else R7ValidationStatus.FAILED
    validation_fp = canonical_json_fingerprint({"executed_result_fingerprint": executed_result.result_fingerprint, "checks": [c.model_dump(mode="json") for c in checks], "status": status.value})
    validated = None
    if status is R7ValidationStatus.PASSED:
        validated_id = stable_content_id("r7validated", validation_fp)
        validated = ValidatedDiagnosticResult(
            validated_result_id=validated_id, validation_event_id=event_id,
            execution_event_id=executed_result.execution_event_id, executed_result_ref=executed_result.executed_result_id,
            result_fingerprint=executed_result.result_fingerprint, validation_fingerprint=validation_fp,
            test_request_ref=request.test_request_id, method=request.method, support_criterion=request.support_criterion,
            validation_profile=request.validation_profile, baseline_week_count=executed_result.baseline_week_count,
            comparison_week_count=executed_result.comparison_week_count, spearman_rho=executed_result.spearman_rho,
            inconclusive_reasons=executed_result.inconclusive_reasons,
        )
    record = DiagnosticValidationRecord(
        validation_event_id=event_id, executed_result_ref=executed_result.executed_result_id,
        executed_result_fingerprint=executed_result.result_fingerprint, validation_profile=request.validation_profile,
        checks=checks, status=status, validated_result_ref=validated.validated_result_id if validated else None,
        started_at=started, ended_at=utc_now(), validation_fingerprint=validation_fp,
    )
    return R7ValidationOutcome(record, validated)
