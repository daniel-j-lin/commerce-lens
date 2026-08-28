"""P6-001 deterministic Evidence admissibility evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from commerce_lens.contracts.common import ArtifactReference, ClaimType, Limitation, MetricState, utc_now
from commerce_lens.contracts.evidence import (
    AdmissibleEvidence,
    EvidenceAdmissibilityRecord,
    EvidenceAdmissibilityStatus,
    EvidenceRole,
)
from commerce_lens.contracts.execution import ExecutedResult, ExecutionRecord, ExecutionStatus
from commerce_lens.contracts.requests import AnalysisRequest
from commerce_lens.contracts.sufficiency import DataSufficiencyResult
from commerce_lens.contracts.validation import ValidatedResult, ValidationRecord, ValidationStatus
from commerce_lens.engine.populations import material_scope_payload
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, generate_id, sha256_file, stable_content_id
from commerce_lens.metrics.registry import get_metric_registry
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.validation.rules import require_p5_rule
from commerce_lens.validation.validator import (
    _bundle_validation_fingerprint_from_validated_result,
    _rule_validation_fingerprint_from_record,
)


EVIDENCE_ADMISSIBILITY_EVALUATOR_ID = "commerce_lens_p6_evidence_admissibility"
EVIDENCE_ADMISSIBILITY_EVALUATOR_VERSION = "p6_001_v1"
SUPPORTED_P6_METRICS = frozenset({"revenue", "orders", "aov"})


class EvidenceAdmissibilityError(ValueError):
    """Raised when P6-001 evidence admissibility fails closed."""

    def __init__(self, failure_code: str, reason: str) -> None:
        super().__init__(reason)
        self.failure_code = failure_code
        self.reason = reason


@dataclass(frozen=True)
class EvidenceAdmissibilityOutcome:
    admissibility_record: EvidenceAdmissibilityRecord
    admissible_evidence: AdmissibleEvidence | None


@dataclass(frozen=True)
class _AuthenticatedValidatedResult:
    result: ValidatedResult
    artifact: ArtifactReference
    validation_records: tuple[ValidationRecord, ...]
    execution_record: ExecutionRecord
    executed_result: ExecutedResult


def evaluate_evidence_admissibility(
    *,
    request_id: str,
    sufficiency_id: str,
    validated_result_id: str,
    claim_type: ClaimType,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    evidence_role: EvidenceRole | None = None,
    supplied_request: AnalysisRequest | None = None,
    supplied_sufficiency: DataSufficiencyResult | None = None,
    supplied_validated_result: ValidatedResult | None = None,
) -> EvidenceAdmissibilityOutcome:
    """Evaluate one persisted ValidatedResult for one governed P6 material-use context."""
    metadata_store.initialize()
    started_at = utc_now()
    admissibility_id = generate_id("eadm")
    checks: list[str] = []
    context: dict[str, Any] = {
        "request_id": request_id,
        "sufficiency_id": sufficiency_id,
        "validated_result_id": validated_result_id,
        "supported_claim_type": claim_type,
    }
    try:
        if claim_type is not ClaimType.DESCRIPTIVE:
            raise EvidenceAdmissibilityError(
                "unsupported_claim_type_for_p6_001",
                "P6-001 supports Evidence admissibility only for descriptive material use",
            )
        checks.append("claim_type_descriptive")

        request = _load_request(request_id, artifact_store, metadata_store, supplied_request)
        context["canonical_business_question_id"] = request.canonical_business_question_id
        context["dataset_ref_id"] = request.dataset_ref_id
        checks.append("analysis_request_authority_verified")

        sufficiency = _load_sufficiency(sufficiency_id, artifact_store, metadata_store, supplied_sufficiency)
        _verify_sufficiency_request_context(request, sufficiency)
        checks.append("sufficiency_request_context_verified")

        auth = _authenticate_validated_result(
            validated_result_id=validated_result_id,
            artifact_store=artifact_store,
            metadata_store=metadata_store,
            supplied_validated_result=supplied_validated_result,
        )
        result = auth.result
        context.update(
            {
                "validated_result_validation_fingerprint": result.validation_fingerprint,
                "validated_result_artifact_ref": auth.artifact,
                "validation_record_ids": tuple(record.validation_id for record in auth.validation_records),
                "executed_result_id": result.executed_result_id,
                "execution_id": result.execution_id,
                "execution_record_id": auth.execution_record.execution_id,
                "metric_ref": result.metric_ref,
                "metric_definition_version": result.metric_definition_version,
                "canonical_dataset_ref_id": result.canonical_dataset_ref_id,
                "canonical_dataset_fingerprint": result.canonical_dataset_fingerprint,
                "population_ref": result.population_ref,
                "population_fingerprint": result.population_fingerprint,
                "period_ref": result.period_ref,
                "period_role": result.period_role,
            }
        )
        checks.append("validated_result_p5_authority_authenticated")

        _verify_request_metric_context(request, result)
        checks.append("analysis_request_metric_context_verified")
        _verify_lineage_context(request, sufficiency, auth)
        checks.append("request_sufficiency_execution_lineage_verified")
        applicable_requirement_ids = _applicable_required_evidence_requirement_ids(request, result.metric_ref, claim_type)
        if not applicable_requirement_ids:
            raise EvidenceAdmissibilityError(
                "required_evidence_context_missing",
                "no applicable Required Evidence requirement exists for the P6 material-use context",
            )
        _verify_available_evidence_satisfies_requirements(sufficiency, applicable_requirement_ids)
        checks.append("applicable_required_evidence_verified")

        _verify_sufficiency_metric_authority(request, sufficiency, result, applicable_requirement_ids)
        checks.append("sufficiency_metric_authority_verified")

        assigned_role = _resolve_evidence_role(result, evidence_role)
        context["evidence_role"] = assigned_role
        checks.append("metric_state_evidence_role_verified")

        limitations = tuple(
            Limitation(
                limitation_id=f"lim_{detail.target_ref or result.metric_ref}_{index}",
                statement=detail.reason,
                affected_ref=detail.target_ref,
                blocking=True,
            )
            for index, detail in enumerate(sufficiency.data_quality_failures)
            if detail.dependency_scope in (None, result.metric_ref)
        )
        if any(item.blocking for item in limitations):
            raise EvidenceAdmissibilityError(
                "blocking_limitation_present",
                "blocking sufficiency limitation exists for the target evidence chain",
            )

        evidence_fingerprint = _evidence_fingerprint(
            request=request,
            sufficiency=sufficiency,
            result=result,
            claim_type=claim_type,
            evidence_role=assigned_role,
            applicable_requirement_ids=applicable_requirement_ids,
            limitations=limitations,
        )
        evidence_id = stable_content_id("ev", evidence_fingerprint)
        evidence = AdmissibleEvidence(
            evidence_id=evidence_id,
            evidence_fingerprint=evidence_fingerprint,
            request_id=request.request_id,
            sufficiency_id=sufficiency.sufficiency_id,
            validated_result_ids=(result.validated_result_id,),
            validation_record_ids=tuple(record.validation_id for record in auth.validation_records),
            executed_result_id=result.executed_result_id,
            execution_id=result.execution_id,
            applicable_required_evidence_requirement_ids=applicable_requirement_ids,
            metric_refs=tuple(metric for metric in request.metrics if metric.metric_id == result.metric_ref),
            metric_ref=result.metric_ref,
            metric_definition_version=result.metric_definition_version,
            dataset_ref_id=request.dataset_ref_id,
            canonical_dataset_ref_id=result.canonical_dataset_ref_id,
            canonical_dataset_fingerprint=result.canonical_dataset_fingerprint,
            population_ref=result.population_ref,
            population_fingerprint=result.population_fingerprint,
            period_ref=result.period_ref,
            period_role=result.period_role,
            supported_claim_type=ClaimType.DESCRIPTIVE,
            evidence_role=assigned_role,
            scope=request.scope,
            assumptions=request.assumptions,
            limitations=limitations,
            qualifications=sufficiency.qualifications,
        )
        artifact = _persist_admissible_evidence(evidence, artifact_store, metadata_store)
        ended_at = utc_now()
        record = EvidenceAdmissibilityRecord(
            admissibility_id=admissibility_id,
            evaluator_id=EVIDENCE_ADMISSIBILITY_EVALUATOR_ID,
            evaluator_version=EVIDENCE_ADMISSIBILITY_EVALUATOR_VERSION,
            request_id=request.request_id,
            sufficiency_id=sufficiency.sufficiency_id,
            validated_result_id=result.validated_result_id,
            validated_result_validation_fingerprint=result.validation_fingerprint,
            validated_result_artifact_ref=auth.artifact,
            validation_record_ids=tuple(record.validation_id for record in auth.validation_records),
            executed_result_id=result.executed_result_id,
            execution_id=result.execution_id,
            execution_record_id=auth.execution_record.execution_id,
            metric_ref=result.metric_ref,
            metric_definition_version=result.metric_definition_version,
            canonical_business_question_id=request.canonical_business_question_id,
            dataset_ref_id=request.dataset_ref_id,
            canonical_dataset_ref_id=result.canonical_dataset_ref_id,
            canonical_dataset_fingerprint=result.canonical_dataset_fingerprint,
            population_ref=result.population_ref,
            population_fingerprint=result.population_fingerprint,
            period_ref=result.period_ref,
            period_role=result.period_role,
            supported_claim_type=ClaimType.DESCRIPTIVE,
            evidence_role=assigned_role,
            applicable_required_evidence_requirement_ids=applicable_requirement_ids,
            sufficiency_authority_checked=True,
            assumptions=request.assumptions,
            qualifications=sufficiency.qualifications,
            limitations=limitations,
            checks_performed=tuple(checks),
            status=EvidenceAdmissibilityStatus.PASSED,
            started_at=started_at,
            ended_at=ended_at,
            admissible_evidence_id=evidence.evidence_id,
            admissible_evidence_artifact_ref=artifact,
            evidence_fingerprint=evidence_fingerprint,
        )
        metadata_store.insert_evidence_admissibility_record(record)
        return EvidenceAdmissibilityOutcome(record, evidence)
    except EvidenceAdmissibilityError as exc:
        ended_at = utc_now()
        record = EvidenceAdmissibilityRecord(
            admissibility_id=admissibility_id,
            evaluator_id=EVIDENCE_ADMISSIBILITY_EVALUATOR_ID,
            evaluator_version=EVIDENCE_ADMISSIBILITY_EVALUATOR_VERSION,
            request_id=context.get("request_id"),
            sufficiency_id=context.get("sufficiency_id"),
            validated_result_id=context.get("validated_result_id"),
            validated_result_validation_fingerprint=context.get("validated_result_validation_fingerprint"),
            validated_result_artifact_ref=context.get("validated_result_artifact_ref"),
            validation_record_ids=context.get("validation_record_ids", ()),
            executed_result_id=context.get("executed_result_id"),
            execution_id=context.get("execution_id"),
            execution_record_id=context.get("execution_record_id"),
            metric_ref=context.get("metric_ref"),
            metric_definition_version=context.get("metric_definition_version"),
            canonical_business_question_id=context.get("canonical_business_question_id"),
            dataset_ref_id=context.get("dataset_ref_id"),
            canonical_dataset_ref_id=context.get("canonical_dataset_ref_id"),
            canonical_dataset_fingerprint=context.get("canonical_dataset_fingerprint"),
            population_ref=context.get("population_ref"),
            population_fingerprint=context.get("population_fingerprint"),
            period_ref=context.get("period_ref"),
            period_role=context.get("period_role"),
            supported_claim_type=claim_type,
            evidence_role=context.get("evidence_role"),
            applicable_required_evidence_requirement_ids=context.get(
                "applicable_required_evidence_requirement_ids",
                (),
            ),
            sufficiency_authority_checked="sufficiency_metric_authority_verified" in checks,
            checks_performed=tuple(checks),
            status=EvidenceAdmissibilityStatus.FAILED,
            failure_code=exc.failure_code,
            failure_reason=exc.reason,
            started_at=started_at,
            ended_at=ended_at,
        )
        metadata_store.insert_evidence_admissibility_record(record)
        return EvidenceAdmissibilityOutcome(record, None)


def _load_request(
    request_id: str,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    supplied_request: AnalysisRequest | None,
) -> AnalysisRequest:
    try:
        request = metadata_store.get_analysis_request(request_id, artifact_store)
    except Exception as exc:
        raise EvidenceAdmissibilityError(
            "analysis_request_tamper_or_mismatch",
            f"persisted AnalysisRequest authority is invalid: {exc}",
        ) from exc
    if request is None:
        raise EvidenceAdmissibilityError("analysis_request_missing", "persisted AnalysisRequest authority is missing")
    if supplied_request is not None and supplied_request != request:
        raise EvidenceAdmissibilityError(
            "analysis_request_tamper_or_mismatch",
            "caller AnalysisRequest differs from persisted authority",
        )
    return request


def _load_sufficiency(
    sufficiency_id: str,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    supplied_sufficiency: DataSufficiencyResult | None,
) -> DataSufficiencyResult:
    try:
        sufficiency = metadata_store.get_data_sufficiency_result(sufficiency_id, artifact_store)
    except Exception as exc:
        raise EvidenceAdmissibilityError(
            "sufficiency_tamper_or_mismatch",
            f"persisted DataSufficiencyResult authority is invalid: {exc}",
        ) from exc
    if sufficiency is None:
        raise EvidenceAdmissibilityError(
            "sufficiency_record_missing",
            "persisted DataSufficiencyResult authority is missing",
        )
    if supplied_sufficiency is not None and supplied_sufficiency != sufficiency:
        raise EvidenceAdmissibilityError(
            "sufficiency_tamper_or_mismatch",
            "caller DataSufficiencyResult differs from persisted authority",
        )
    return sufficiency


def _verify_sufficiency_request_context(request: AnalysisRequest, sufficiency: DataSufficiencyResult) -> None:
    if sufficiency.request_id != request.request_id or sufficiency.dataset_ref_id != request.dataset_ref_id:
        raise EvidenceAdmissibilityError(
            "sufficiency_context_mismatch",
            "DataSufficiencyResult request or dataset authority does not match AnalysisRequest",
        )


def _verify_request_metric_context(request: AnalysisRequest, result: ValidatedResult) -> None:
    if result.metric_ref not in SUPPORTED_P6_METRICS:
        raise EvidenceAdmissibilityError("required_evidence_metric_mismatch", "Metric is not supported by P6-001")
    matching = tuple(metric for metric in request.metrics if metric.metric_id == result.metric_ref)
    if len(matching) != 1:
        raise EvidenceAdmissibilityError("required_evidence_metric_mismatch", "target Metric is not in AnalysisRequest")
    metric_ref = matching[0]
    if metric_ref.definition_version != result.metric_definition_version:
        raise EvidenceAdmissibilityError(
            "metric_definition_mismatch",
            "ValidatedResult Metric definition version does not match AnalysisRequest",
        )
    registry_definition = get_metric_registry().require(result.metric_ref)
    if result.metric_definition_version != registry_definition.definition_version:
        raise EvidenceAdmissibilityError(
            "metric_definition_mismatch",
            "ValidatedResult Metric definition version does not match Metric Registry",
        )
    if request.metric_registry_version != get_metric_registry().registry_version:
        raise EvidenceAdmissibilityError(
            "metric_definition_mismatch",
            "AnalysisRequest Metric Registry version does not match active registry",
        )
    if result.period_ref not in {request.baseline_period.period_id, request.comparison_period.period_id}:
        raise EvidenceAdmissibilityError("period_mismatch", "ValidatedResult period is outside AnalysisRequest periods")


def _applicable_required_evidence_requirement_ids(
    request: AnalysisRequest,
    metric_ref: str,
    claim_type: ClaimType,
) -> tuple[str, ...]:
    return tuple(
        requirement.requirement_id
        for requirement in request.required_evidence
        if requirement.metric_ref in (None, metric_ref)
        and requirement.claim_type in (None, claim_type)
    )


def _verify_available_evidence_satisfies_requirements(
    sufficiency: DataSufficiencyResult,
    requirement_ids: tuple[str, ...],
) -> None:
    satisfied = {
        requirement_id
        for evidence in sufficiency.available_evidence
        for requirement_id in evidence.satisfies_requirement_ids
    }
    missing = tuple(requirement_id for requirement_id in requirement_ids if requirement_id not in satisfied)
    if missing:
        raise EvidenceAdmissibilityError(
            "missing_required_evidence",
            f"applicable Required Evidence is not satisfied by Available Evidence: {', '.join(missing)}",
        )


def _verify_sufficiency_metric_authority(
    request: AnalysisRequest,
    sufficiency: DataSufficiencyResult,
    result: ValidatedResult,
    applicable_requirement_ids: tuple[str, ...],
) -> None:
    if sufficiency.canonical_dataset_ref_id != result.canonical_dataset_ref_id:
        raise EvidenceAdmissibilityError(
            "dataset_mismatch",
            "DataSufficiencyResult canonical dataset authority does not match ValidatedResult",
        )
    matching = tuple(item for item in sufficiency.metric_eligibility if item.metric_ref == result.metric_ref)
    if not matching:
        raise EvidenceAdmissibilityError(
            "sufficiency_metric_eligibility_absent",
            "target MetricEligibility is missing",
        )
    if len(matching) > 1:
        raise EvidenceAdmissibilityError(
            "sufficiency_metric_eligibility_duplicate",
            "target MetricEligibility is duplicated",
        )
    eligibility = matching[0]
    if not eligibility.eligible:
        raise EvidenceAdmissibilityError("sufficiency_not_eligible", "target MetricEligibility is not eligible")
    for failure in eligibility.failure_details:
        if failure.dependency_scope in (None, result.metric_ref):
            raise EvidenceAdmissibilityError(
                "sufficiency_not_eligible",
                "target MetricEligibility has blocking failure details",
            )
    sufficiency_requirement_ids = {requirement.requirement_id for requirement in sufficiency.required_evidence}
    if not set(applicable_requirement_ids).issubset(sufficiency_requirement_ids):
        raise EvidenceAdmissibilityError(
            "required_evidence_context_missing",
            "DataSufficiencyResult does not retain applicable Required Evidence authority",
        )
    if request.dataset_ref_id != sufficiency.dataset_ref_id:
        raise EvidenceAdmissibilityError("dataset_mismatch", "request and sufficiency dataset authority differ")


def _verify_lineage_context(
    request: AnalysisRequest,
    sufficiency: DataSufficiencyResult,
    auth: _AuthenticatedValidatedResult,
) -> None:
    result = auth.result
    execution_record = auth.execution_record
    executed_result = auth.executed_result
    if execution_record.request_id != request.request_id:
        raise EvidenceAdmissibilityError("executed_result_lineage_missing", "ExecutionRecord request authority mismatches AnalysisRequest")
    if request.dataset_ref_id not in execution_record.dataset_ref_ids:
        raise EvidenceAdmissibilityError("dataset_mismatch", "ExecutionRecord dataset authority mismatches AnalysisRequest")
    if sufficiency.canonical_dataset_ref_id != result.canonical_dataset_ref_id:
        raise EvidenceAdmissibilityError("dataset_mismatch", "ValidatedResult canonical dataset mismatches sufficiency authority")
    if result.canonical_dataset_ref_id not in execution_record.canonical_dataset_ref_ids:
        raise EvidenceAdmissibilityError("dataset_mismatch", "ExecutionRecord canonical dataset authority mismatches ValidatedResult")
    if result.canonical_dataset_fingerprint not in execution_record.canonical_dataset_fingerprints:
        raise EvidenceAdmissibilityError("dataset_mismatch", "ExecutionRecord canonical dataset fingerprint mismatches ValidatedResult")
    if result.population_ref not in execution_record.population_refs:
        raise EvidenceAdmissibilityError("population_mismatch", "ExecutionRecord population authority mismatches ValidatedResult")
    if result.population_fingerprint not in execution_record.population_fingerprints:
        raise EvidenceAdmissibilityError("population_mismatch", "ExecutionRecord population fingerprint mismatches ValidatedResult")
    if result.period_ref not in execution_record.period_refs:
        raise EvidenceAdmissibilityError("period_mismatch", "ExecutionRecord period authority mismatches ValidatedResult")
    if result.period_role != execution_record.period_role:
        raise EvidenceAdmissibilityError("period_mismatch", "ExecutionRecord period role mismatches ValidatedResult")
    if execution_record.grouping != request.grouping.value:
        raise EvidenceAdmissibilityError("population_mismatch", "ExecutionRecord grouping mismatches AnalysisRequest scope")
    _verify_request_scope_matches_execution(request, result, execution_record)
    if executed_result.metric_ref != result.metric_ref:
        raise EvidenceAdmissibilityError("required_evidence_metric_mismatch", "ExecutedResult Metric mismatches ValidatedResult")
    if executed_result.scope_ref != result.population_ref:
        raise EvidenceAdmissibilityError("population_mismatch", "ExecutedResult population mismatches ValidatedResult")
    if executed_result.period_ref != result.period_ref:
        raise EvidenceAdmissibilityError("period_mismatch", "ExecutedResult period mismatches ValidatedResult")
    if executed_result.value != result.value or executed_result.metric_state is not result.metric_state:
        raise EvidenceAdmissibilityError("executed_result_lineage_missing", "ExecutedResult value or state mismatches ValidatedResult")
    if executed_result.undefined_reason != result.undefined_reason:
        raise EvidenceAdmissibilityError("undefined_state_context_mismatch", "ExecutedResult undefined reason mismatches ValidatedResult")
    if executed_result.currency != result.currency:
        raise EvidenceAdmissibilityError("currency_mismatch", "ExecutedResult currency mismatches ValidatedResult")


def _verify_request_scope_matches_execution(
    request: AnalysisRequest,
    result: ValidatedResult,
    execution_record: ExecutionRecord,
) -> None:
    request_filters = tuple(material_scope_payload(request.scope)["filters"])
    if tuple(execution_record.scope_filters) != request_filters:
        raise EvidenceAdmissibilityError("population_mismatch", "ExecutionRecord scope filters mismatch AnalysisRequest scope")
    if request.scope.population_ref is not None and request.scope.population_ref != result.population_ref:
        raise EvidenceAdmissibilityError("population_mismatch", "AnalysisRequest population_ref mismatches ValidatedResult population")


def _resolve_evidence_role(result: ValidatedResult, requested_role: EvidenceRole | None) -> EvidenceRole:
    if result.metric_state is MetricState.VALID:
        if requested_role not in (None, EvidenceRole.METRIC_VALUE):
            raise EvidenceAdmissibilityError("metric_state_not_admissible", "Valid MetricState requires metric_value EvidenceRole")
        return EvidenceRole.METRIC_VALUE
    if result.metric_state is MetricState.QUALIFIED:
        raise EvidenceAdmissibilityError(
            "qualified_metric_state_not_supported_p6_001",
            "Qualified MetricState Evidence admissibility is not supported by P6-001",
        )
    if result.metric_state is MetricState.UNDEFINED:
        if requested_role is EvidenceRole.METRIC_VALUE:
            raise EvidenceAdmissibilityError(
                "undefined_aov_metric_value_not_supported_p6_001",
                "governed AOV Undefined state cannot serve as metric_value Evidence",
            )
        if result.metric_ref != "aov" or result.value is not None or result.undefined_reason != "orders_equals_zero":
            raise EvidenceAdmissibilityError(
                "undefined_state_context_mismatch",
                "only AOV Undefined because Orders equals zero is admissible in P6-001",
            )
        return EvidenceRole.METRIC_STATE
    raise EvidenceAdmissibilityError("metric_state_not_admissible", "MetricState cannot become AdmissibleEvidence")


def _authenticate_validated_result(
    *,
    validated_result_id: str,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    supplied_validated_result: ValidatedResult | None,
) -> _AuthenticatedValidatedResult:
    records = tuple(
        record
        for record in metadata_store.list_validation_records()
        if record.validated_result_ref == validated_result_id
    )
    if not records:
        raise EvidenceAdmissibilityError(
            "validated_result_metadata_missing",
            "ValidatedResult is not linked from persisted ValidationRecord metadata",
        )
    artifact = records[0].validated_result_artifact_ref
    if artifact is None:
        raise EvidenceAdmissibilityError(
            "validated_result_artifact_missing",
            "ValidationRecord has no ValidatedResult artifact reference",
        )
    for record in records:
        if record.validated_result_artifact_ref != artifact:
            raise EvidenceAdmissibilityError(
                "validated_result_metadata_missing",
                "ValidationRecords do not reference one ValidatedResult artifact",
            )
    result = _load_validated_result_artifact(artifact, artifact_store, metadata_store)
    if result.validated_result_id != validated_result_id:
        raise EvidenceAdmissibilityError(
            "validated_result_metadata_missing",
            "ValidatedResult artifact identity does not match requested authority",
        )
    if supplied_validated_result is not None and supplied_validated_result != result:
        raise EvidenceAdmissibilityError(
            "validated_result_artifact_hash_mismatch",
            "caller ValidatedResult differs from persisted artifact authority",
        )
    _precheck_p6_metric_state(result)
    required_rule_ids = get_metric_registry().require(result.metric_ref).required_validation_rule_refs
    if len(result.required_validation_record_ids) != len(required_rule_ids):
        raise EvidenceAdmissibilityError(
            "validation_bundle_incomplete",
            "ValidatedResult does not reference every required ValidationRecord",
        )
    records_by_id = {record.validation_id: record for record in records}
    ordered_records: list[ValidationRecord] = []
    for record_id, rule_id in zip(result.required_validation_record_ids, required_rule_ids):
        record = records_by_id.get(record_id) or metadata_store.get_validation_record(record_id)
        if record is None:
            raise EvidenceAdmissibilityError("validation_bundle_incomplete", "required ValidationRecord is missing")
        ordered_records.append(record)
        _verify_validation_record(result, record, rule_id)
    if tuple(record.validation_rule_id for record in ordered_records) != required_rule_ids:
        raise EvidenceAdmissibilityError(
            "validation_bundle_incomplete",
            "ValidationRecord rule IDs do not match Metric Registry authority",
        )
    expected_bundle = _bundle_validation_fingerprint_from_validated_result(
        result,
        required_rule_ids=required_rule_ids,
        rule_validation_fingerprints=tuple(record.validation_fingerprint or "" for record in ordered_records),
    )
    if result.validation_fingerprint != expected_bundle:
        raise EvidenceAdmissibilityError(
            "validation_fingerprint_mismatch",
            "ValidatedResult validation fingerprint does not match the required validation bundle",
        )
    execution_record = metadata_store.get_execution_record(result.execution_id)
    if execution_record is None:
        raise EvidenceAdmissibilityError("execution_record_lineage_missing", "source ExecutionRecord is missing")
    executed_result = _load_executed_result(result, execution_record, artifact_store, metadata_store)
    return _AuthenticatedValidatedResult(result, artifact, tuple(ordered_records), execution_record, executed_result)


def _precheck_p6_metric_state(result: ValidatedResult) -> None:
    if result.metric_state is MetricState.QUALIFIED:
        raise EvidenceAdmissibilityError(
            "qualified_metric_state_not_supported_p6_001",
            "Qualified MetricState Evidence admissibility is not supported by P6-001",
        )
    if result.metric_state is MetricState.INADMISSIBLE:
        raise EvidenceAdmissibilityError("metric_state_not_admissible", "MetricState cannot become AdmissibleEvidence")
    if result.metric_state is MetricState.UNDEFINED:
        if result.metric_ref != "aov" or result.value is not None or result.undefined_reason != "orders_equals_zero":
            raise EvidenceAdmissibilityError(
                "undefined_state_context_mismatch",
                "only AOV Undefined because Orders equals zero is admissible in P6-001",
            )


def _load_validated_result_artifact(
    artifact: ArtifactReference,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ValidatedResult:
    persisted = metadata_store.get_artifact_reference(artifact.artifact_id)
    if persisted != artifact:
        raise EvidenceAdmissibilityError(
            "validated_result_artifact_missing",
            "ValidatedResult artifact reference is missing or mismatched",
        )
    path = artifact_store.safe_path(artifact.path)
    if not path.is_file():
        raise EvidenceAdmissibilityError("validated_result_artifact_missing", "ValidatedResult artifact is missing")
    if artifact.fingerprint is None or sha256_file(path) != artifact.fingerprint:
        raise EvidenceAdmissibilityError(
            "validated_result_artifact_hash_mismatch",
            "ValidatedResult artifact hash does not match metadata",
        )
    try:
        return ValidatedResult.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        raise EvidenceAdmissibilityError(
            "validated_result_schema_invalid",
            f"ValidatedResult artifact is schema-invalid: {exc}",
        ) from exc


def _verify_validation_record(result: ValidatedResult, record: ValidationRecord, expected_rule_id: str) -> None:
    rule = require_p5_rule(expected_rule_id, result.metric_ref)
    if record.status is not ValidationStatus.PASSED:
        raise EvidenceAdmissibilityError("validation_record_failed", "required ValidationRecord did not pass")
    if record.validation_rule_id != expected_rule_id or record.validation_version != rule.rule_version:
        raise EvidenceAdmissibilityError("validation_bundle_incomplete", "required ValidationRecord rule authority mismatches")
    expected_fields = {
        "execution_id": result.execution_id,
        "target_result_ref": result.executed_result_id,
        "metric_ref": result.metric_ref,
        "metric_definition_version": result.metric_definition_version,
        "plan_id": result.plan_id,
        "plan_node_id": result.plan_node_id,
        "canonical_dataset_ref_id": result.canonical_dataset_ref_id,
        "canonical_dataset_fingerprint": result.canonical_dataset_fingerprint,
        "population_ref": result.population_ref,
        "population_fingerprint": result.population_fingerprint,
        "period_ref": result.period_ref,
        "period_role": result.period_role,
        "result_fingerprint": result.result_fingerprint,
        "validated_result_ref": result.validated_result_id,
    }
    for field_name, expected in expected_fields.items():
        if getattr(record, field_name) != expected:
            raise EvidenceAdmissibilityError(
                "executed_result_lineage_missing",
                "ValidationRecord lineage does not match ValidatedResult",
            )
    if record.validated_result_artifact_ref is None:
        raise EvidenceAdmissibilityError("validated_result_artifact_missing", "ValidationRecord lacks ValidatedResult artifact")
    if record.validation_fingerprint != _rule_validation_fingerprint_from_record(record):
        raise EvidenceAdmissibilityError(
            "validation_fingerprint_mismatch",
            "ValidationRecord rule fingerprint is not authentic",
        )


def _load_executed_result(
    result: ValidatedResult,
    execution_record: ExecutionRecord,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ExecutedResult:
    if execution_record.status is not ExecutionStatus.COMPLETED:
        raise EvidenceAdmissibilityError("execution_record_lineage_missing", "source ExecutionRecord is not completed")
    if execution_record.result_ref != result.executed_result_id:
        raise EvidenceAdmissibilityError("executed_result_lineage_missing", "ExecutionRecord result_ref mismatches ValidatedResult")
    if not execution_record.output_artifacts:
        raise EvidenceAdmissibilityError("executed_result_lineage_missing", "ExecutionRecord lacks source result artifact")
    artifact = execution_record.output_artifacts[0]
    persisted = metadata_store.get_artifact_reference(artifact.artifact_id)
    if persisted != artifact:
        raise EvidenceAdmissibilityError("executed_result_lineage_missing", "ExecutedResult artifact reference is not persisted")
    path = artifact_store.safe_path(artifact.path)
    if not path.is_file() or artifact.fingerprint is None or sha256_file(path) != artifact.fingerprint:
        raise EvidenceAdmissibilityError("executed_result_lineage_missing", "ExecutedResult artifact integrity check failed")
    try:
        executed_result = ExecutedResult.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        raise EvidenceAdmissibilityError(
            "executed_result_lineage_missing",
            f"ExecutedResult artifact is schema-invalid: {exc}",
        ) from exc
    if executed_result.result_id != result.executed_result_id or executed_result.execution_id != result.execution_id:
        raise EvidenceAdmissibilityError("executed_result_lineage_missing", "ExecutedResult identity mismatches ValidatedResult")
    if executed_result.result_fingerprint != result.result_fingerprint:
        raise EvidenceAdmissibilityError("executed_result_lineage_missing", "ExecutedResult fingerprint mismatches ValidatedResult")
    return executed_result


def _evidence_fingerprint(
    *,
    request: AnalysisRequest,
    sufficiency: DataSufficiencyResult,
    result: ValidatedResult,
    claim_type: ClaimType,
    evidence_role: EvidenceRole,
    applicable_requirement_ids: tuple[str, ...],
    limitations: tuple[Limitation, ...],
) -> str:
    return canonical_json_fingerprint(
        {
            "evaluator_id": EVIDENCE_ADMISSIBILITY_EVALUATOR_ID,
            "evaluator_version": EVIDENCE_ADMISSIBILITY_EVALUATOR_VERSION,
            "claim_type": claim_type.value,
            "evidence_role": evidence_role.value,
            "request_id": request.request_id,
            "analysis_request_fingerprint": canonical_json_fingerprint(request.model_dump(mode="json")),
            "canonical_business_question_id": request.canonical_business_question_id,
            "metric_ref": result.metric_ref,
            "metric_definition_version": result.metric_definition_version,
            "validation_fingerprint": result.validation_fingerprint,
            "dataset_ref_id": request.dataset_ref_id,
            "canonical_dataset_ref_id": result.canonical_dataset_ref_id,
            "canonical_dataset_fingerprint": result.canonical_dataset_fingerprint,
            "population_ref": result.population_ref,
            "population_fingerprint": result.population_fingerprint,
            "period_ref": result.period_ref,
            "period_role": result.period_role,
            "scope": request.scope.model_dump(mode="json"),
            "applicable_required_evidence_requirement_ids": applicable_requirement_ids,
            "sufficiency_id": sufficiency.sufficiency_id,
            "sufficiency_fingerprint": canonical_json_fingerprint(sufficiency.model_dump(mode="json")),
            "sufficiency_context": {
                "request_id": sufficiency.request_id,
                "dataset_ref_id": sufficiency.dataset_ref_id,
                "canonical_dataset_ref_id": sufficiency.canonical_dataset_ref_id,
                "state": sufficiency.state.value,
            },
            "assumptions": [item.model_dump(mode="json") for item in request.assumptions],
            "qualifications": [item.model_dump(mode="json") for item in sufficiency.qualifications],
            "limitations": [item.model_dump(mode="json") for item in limitations],
        }
    )


def _persist_admissible_evidence(
    evidence: AdmissibleEvidence,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ArtifactReference:
    for record in metadata_store.list_evidence_admissibility_records():
        if (
            record.status is EvidenceAdmissibilityStatus.PASSED
            and record.admissible_evidence_id == evidence.evidence_id
        ):
            if record.admissible_evidence_artifact_ref is None:
                raise EvidenceAdmissibilityError(
                    "admissible_evidence_artifact_integrity_failure",
                    "successful EvidenceAdmissibilityRecord lacks AdmissibleEvidence artifact reference",
                )
            restored = verify_admissible_evidence_artifact(
                record.admissible_evidence_artifact_ref,
                artifact_store=artifact_store,
                metadata_store=metadata_store,
                expected_evidence=evidence,
                admissibility_record=record,
            )
            if restored == evidence:
                return record.admissible_evidence_artifact_ref
            raise EvidenceAdmissibilityError(
                "admissible_evidence_artifact_integrity_failure",
                "existing AdmissibleEvidence artifact differs from expected semantic Evidence",
            )
    try:
        artifact = artifact_store.write_json_artifact(
            Path("runs") / (evidence.execution_id or "unknown_execution") / "admissible_evidence" / f"{evidence.evidence_id}.json",
            evidence.model_dump(mode="json"),
        )
    except ValueError as exc:
        if str(exc) == "existing JSON artifact content mismatch":
            raise EvidenceAdmissibilityError(
                "admissible_evidence_artifact_integrity_failure",
                "existing AdmissibleEvidence artifact content mismatches the expected semantic Evidence",
            ) from exc
        raise
    metadata_store.insert_artifact_reference(artifact)
    verify_admissible_evidence_artifact(
        artifact,
        artifact_store=artifact_store,
        metadata_store=metadata_store,
        expected_evidence=evidence,
    )
    return artifact


def verify_admissible_evidence_artifact(
    artifact: ArtifactReference,
    *,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    expected_evidence: AdmissibleEvidence | None = None,
    admissibility_record: EvidenceAdmissibilityRecord | None = None,
) -> AdmissibleEvidence:
    persisted = metadata_store.get_artifact_reference(artifact.artifact_id)
    if persisted != artifact:
        raise EvidenceAdmissibilityError(
            "admissible_evidence_artifact_integrity_failure",
            "AdmissibleEvidence artifact reference is missing or mismatched",
        )
    path = artifact_store.safe_path(artifact.path)
    if not path.is_file():
        raise EvidenceAdmissibilityError(
            "admissible_evidence_artifact_integrity_failure",
            "AdmissibleEvidence artifact is missing",
        )
    if artifact.fingerprint is None or sha256_file(path) != artifact.fingerprint:
        raise EvidenceAdmissibilityError(
            "admissible_evidence_artifact_integrity_failure",
            "AdmissibleEvidence artifact hash does not match metadata",
        )
    try:
        evidence = AdmissibleEvidence.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        raise EvidenceAdmissibilityError(
            "admissible_evidence_artifact_integrity_failure",
            f"AdmissibleEvidence artifact is schema-invalid: {exc}",
        ) from exc
    if evidence.evidence_fingerprint is None:
        raise EvidenceAdmissibilityError(
            "admissible_evidence_artifact_integrity_failure",
            "AdmissibleEvidence lacks semantic evidence_fingerprint",
        )
    if evidence.evidence_id != stable_content_id("ev", evidence.evidence_fingerprint):
        raise EvidenceAdmissibilityError(
            "admissible_evidence_artifact_integrity_failure",
            "AdmissibleEvidence evidence_id does not match semantic fingerprint",
        )
    if expected_evidence is not None:
        if evidence.evidence_id != expected_evidence.evidence_id:
            raise EvidenceAdmissibilityError(
                "admissible_evidence_artifact_integrity_failure",
                "AdmissibleEvidence artifact identity does not match expected Evidence",
            )
        if evidence.evidence_fingerprint != expected_evidence.evidence_fingerprint:
            raise EvidenceAdmissibilityError(
                "admissible_evidence_artifact_integrity_failure",
                "AdmissibleEvidence semantic fingerprint does not match expected Evidence",
            )
        if evidence != expected_evidence:
            raise EvidenceAdmissibilityError(
                "admissible_evidence_artifact_integrity_failure",
                "AdmissibleEvidence artifact content differs from expected semantic Evidence",
            )
    if admissibility_record is not None:
        _verify_admissible_evidence_record_lineage(evidence, admissibility_record, artifact)
    return evidence


def _verify_admissible_evidence_record_lineage(
    evidence: AdmissibleEvidence,
    record: EvidenceAdmissibilityRecord,
    artifact: ArtifactReference,
) -> None:
    expected = {
        "request_id": evidence.request_id,
        "sufficiency_id": evidence.sufficiency_id,
        "validated_result_id": evidence.validated_result_ids[0],
        "validation_record_ids": evidence.validation_record_ids,
        "executed_result_id": evidence.executed_result_id,
        "execution_id": evidence.execution_id,
        "metric_ref": evidence.metric_ref,
        "metric_definition_version": evidence.metric_definition_version,
        "dataset_ref_id": evidence.dataset_ref_id,
        "canonical_dataset_ref_id": evidence.canonical_dataset_ref_id,
        "canonical_dataset_fingerprint": evidence.canonical_dataset_fingerprint,
        "population_ref": evidence.population_ref,
        "population_fingerprint": evidence.population_fingerprint,
        "period_ref": evidence.period_ref,
        "period_role": evidence.period_role,
        "supported_claim_type": evidence.supported_claim_type,
        "evidence_role": evidence.evidence_role,
        "applicable_required_evidence_requirement_ids": evidence.applicable_required_evidence_requirement_ids,
        "admissible_evidence_id": evidence.evidence_id,
        "admissible_evidence_artifact_ref": artifact,
        "evidence_fingerprint": evidence.evidence_fingerprint,
    }
    for field_name, expected_value in expected.items():
        if getattr(record, field_name) != expected_value:
            raise EvidenceAdmissibilityError(
                "admissible_evidence_artifact_integrity_failure",
                "AdmissibleEvidence artifact lineage mismatches EvidenceAdmissibilityRecord",
            )
