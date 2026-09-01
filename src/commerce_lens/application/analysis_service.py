"""Public application service boundary for governed analysis orchestration."""

from __future__ import annotations

from pathlib import Path

from commerce_lens.canonical.models import CanonicalizationRequest, PeriodCoverageEvidence
from commerce_lens.canonical.service import canonicalize_dataset
from commerce_lens.contracts.common import (
    ArtifactReference,
    AvailableEvidence,
    ClaimType,
    FailureDetail,
    FailureStage,
    MetricState,
    RunStatus,
    SourceType,
)
from commerce_lens.contracts.evidence import (
    ClaimCandidate,
    ClaimDecision,
    DatasetReference,
    EvidenceAdmissibilityRecord,
    EvidenceRole,
)
from commerce_lens.contracts.execution import ExecutedResult, ExecutionRecord, ExecutionStatus
from commerce_lens.contracts.requests import AnalysisRequest
from commerce_lens.contracts.results import AnalysisResult, MetricResult
from commerce_lens.contracts.sufficiency import ClarificationItem, DataSufficiencyResult, SufficiencyState
from commerce_lens.contracts.validation import ValidatedResult, ValidationRecord, ValidationStatus
from commerce_lens.sufficiency.evaluator import evaluate_data_sufficiency
from commerce_lens.engine.execution import execute_plan
from commerce_lens.engine.plan_builder import build_execution_plan
from commerce_lens.evidence.admissibility import evaluate_evidence_admissibility
from commerce_lens.evidence.claim_admissibility import (
    evaluate_claim_admissibility,
    get_authoritative_claim_decision,
    persist_claim_candidate,
)
from commerce_lens.evidence.identifiers import generate_id
from commerce_lens.intake.csv_adapter import CsvInspectionAdapter
from commerce_lens.intake.excel_adapter import ExcelInspectionAdapter
from commerce_lens.intake.inspection import InspectionStatus
from commerce_lens.intake.registry import DatasetRegistry
from commerce_lens.intake.sqlite_adapter import SQLiteInspectionAdapter
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.validation.validator import validate_executed_result

SUPPORTED_APPLICATION_METRICS = frozenset({"revenue", "orders", "aov", "revenue_change"})


class ApplicationServiceError(ValueError):
    """Raised when application-boundary authority cannot fail closed as a result."""


def run_analysis(
    request: AnalysisRequest,
    *,
    canonicalization_request: CanonicalizationRequest,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    source_path: str | Path | None = None,
    source_type: SourceType | None = None,
    dataset: DatasetReference | None = None,
    selected_sheet: str | None = None,
    selected_table: str | None = None,
    available_evidence: tuple[AvailableEvidence, ...] = (),
    period_coverage_evidence: tuple[PeriodCoverageEvidence, ...] = (),
    clarification_items: tuple[ClarificationItem, ...] = (),
) -> AnalysisResult:
    """Run governed analysis through current P1-P8 production authorities."""
    metadata_store.initialize()
    artifact_store.ensure_layout()
    _assert_supported_metrics(request)
    _assert_selection_authority(request, selected_sheet=selected_sheet, selected_table=selected_table)
    _assert_canonicalization_authority(request, canonicalization_request)

    active_dataset = _resolve_dataset(
        request,
        artifact_store=artifact_store,
        metadata_store=metadata_store,
        source_path=source_path,
        source_type=source_type,
        dataset=dataset,
        selected_sheet=selected_sheet,
        selected_table=selected_table,
    )
    _assert_dataset_authority(request, active_dataset)

    canonicalization = canonicalize_dataset(active_dataset, canonicalization_request, artifact_store)
    if canonicalization.canonical_dataset is not None:
        metadata_store.insert_artifact_reference(canonicalization.canonical_dataset.artifact)
        metadata_store.insert_canonical_dataset(canonicalization.canonical_dataset)
    metadata_store.insert_canonicalization_record(canonicalization.record)

    persisted_request = metadata_store.insert_analysis_request(request, artifact_store)
    sufficiency = evaluate_data_sufficiency(
        persisted_request,
        canonicalization,
        available_evidence=available_evidence,
        period_coverage_evidence=period_coverage_evidence,
        clarification_items=clarification_items,
    )
    sufficiency = metadata_store.insert_data_sufficiency_result(sufficiency, artifact_store)

    if canonicalization.canonical_dataset is None:
        return _analysis_result(
            request=persisted_request,
            sufficiency=sufficiency,
            execution_records=(),
            executed_results=(),
            plan=None,
            dataset=active_dataset,
            canonicalization=canonicalization,
            validation_records=(),
            validated_results=(),
            evidence_records=(),
            evidence_failures=(),
        )

    plan = build_execution_plan(persisted_request, sufficiency)
    execution = execute_plan(plan, canonicalization.canonical_dataset, artifact_store, metadata_store)
    validation_records, validated_results = _validate_execution_results(
        execution_records=execution.execution_records,
        executed_results=execution.executed_results,
        plan=plan,
        canonical_dataset=canonicalization.canonical_dataset,
        artifact_store=artifact_store,
        metadata_store=metadata_store,
    )
    evidence_records, evidence_failures = _admit_requested_evidence(
        request=persisted_request,
        sufficiency=sufficiency,
        validated_results=validated_results,
        artifact_store=artifact_store,
        metadata_store=metadata_store,
    )
    return _analysis_result(
        request=persisted_request,
        sufficiency=sufficiency,
        execution_records=execution.execution_records,
        executed_results=execution.executed_results,
        plan=plan,
        dataset=active_dataset,
        canonicalization=canonicalization,
        validation_records=validation_records,
        validated_results=validated_results,
        evidence_records=tuple(evidence_records),
        evidence_failures=tuple(evidence_failures),
    )


def evaluate_claim(
    candidate: ClaimCandidate,
    *,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ClaimDecision:
    """Evaluate a caller-supplied ClaimCandidate and return P8 authority."""
    metadata_store.initialize()
    artifact_store.ensure_layout()
    persisted = persist_claim_candidate(candidate, artifact_store=artifact_store, metadata_store=metadata_store)
    evaluated = evaluate_claim_admissibility(
        claim_candidate_id=persisted.claim_candidate_id,
        artifact_store=artifact_store,
        metadata_store=metadata_store,
        supplied_candidate=persisted,
    ).claim_decision
    authoritative = get_authoritative_claim_decision(
        evaluated.claim_decision_id,
        artifact_store=artifact_store,
        metadata_store=metadata_store,
    )
    if authoritative is None:
        raise ApplicationServiceError("authoritative ClaimDecision retrieval failed closed")
    return authoritative


def _assert_supported_metrics(request: AnalysisRequest) -> None:
    unsupported = tuple(metric.metric_id for metric in request.metrics if metric.metric_id not in SUPPORTED_APPLICATION_METRICS)
    if unsupported:
        raise ApplicationServiceError(f"unsupported application Metric requested: {', '.join(unsupported)}")


def _assert_selection_authority(
    request: AnalysisRequest,
    *,
    selected_sheet: str | None,
    selected_table: str | None,
) -> None:
    _assert_runtime_selection("selected_sheet", request.selected_sheet, selected_sheet)
    _assert_runtime_selection("selected_table", request.selected_table, selected_table)


def _assert_runtime_selection(name: str, request_value: str | None, runtime_value: str | None) -> None:
    if runtime_value is None:
        return
    if request_value is None:
        raise ApplicationServiceError(f"runtime {name} cannot supply authority absent from AnalysisRequest")
    if runtime_value != request_value:
        raise ApplicationServiceError(f"runtime {name} conflicts with AnalysisRequest {name}")


def _assert_canonicalization_authority(
    request: AnalysisRequest,
    canonicalization_request: CanonicalizationRequest,
) -> None:
    if canonicalization_request.source_dataset_id != request.dataset_ref_id:
        raise ApplicationServiceError("CanonicalizationRequest source_dataset_id must match AnalysisRequest dataset_ref_id")
    if canonicalization_request.selected_sheet is not None:
        if canonicalization_request.selected_sheet != request.selected_sheet:
            raise ApplicationServiceError("CanonicalizationRequest selected_sheet conflicts with AnalysisRequest")
    if canonicalization_request.selected_table is not None:
        if canonicalization_request.selected_table != request.selected_table:
            raise ApplicationServiceError("CanonicalizationRequest selected_table conflicts with AnalysisRequest")


def _resolve_dataset(
    request: AnalysisRequest,
    *,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    source_path: str | Path | None,
    source_type: SourceType | None,
    dataset: DatasetReference | None,
    selected_sheet: str | None,
    selected_table: str | None,
) -> DatasetReference:
    if dataset is not None:
        if source_path is not None or source_type is not None:
            raise ApplicationServiceError("supply either DatasetReference or source registration inputs, not both")
        metadata_store.insert_dataset(dataset)
        persisted = metadata_store.get_dataset(dataset.dataset_id)
        if persisted is None:
            raise ApplicationServiceError("DatasetReference durable authority is absent after persistence")
        if persisted != dataset:
            raise ApplicationServiceError("DatasetReference durable authority conflicts with supplied DatasetReference")
        return persisted
    if source_path is None or source_type is None:
        existing = metadata_store.get_dataset(request.dataset_ref_id)
        if existing is None:
            raise ApplicationServiceError("AnalysisRequest dataset_ref_id is not registered and no source was supplied")
        return existing

    registry = DatasetRegistry(artifact_store, metadata_store)
    physical_sheet = selected_sheet or request.selected_sheet
    physical_table = selected_table or request.selected_table
    if source_type is SourceType.CSV:
        inspection = CsvInspectionAdapter(registry).inspect(source_path)
    elif source_type is SourceType.EXCEL_XLSX:
        inspection = ExcelInspectionAdapter(registry).inspect(source_path, sheet_name=physical_sheet)
    elif source_type is SourceType.SQLITE:
        inspection = SQLiteInspectionAdapter(registry).inspect(source_path, table_name=physical_table)
    else:
        raise ApplicationServiceError(f"unsupported SourceType: {source_type}")
    if inspection.status is not InspectionStatus.SUPPORTED or inspection.dataset_ref_id is None:
        detail = inspection.failure_detail.reason if inspection.failure_detail is not None else inspection.status.value
        raise ApplicationServiceError(f"source inspection failed closed: {detail}")
    registered = metadata_store.get_dataset(inspection.dataset_ref_id)
    if registered is None:
        raise ApplicationServiceError("source registration did not persist DatasetReference authority")
    return registered


def _assert_dataset_authority(request: AnalysisRequest, dataset: DatasetReference) -> None:
    if dataset.dataset_id != request.dataset_ref_id:
        raise ApplicationServiceError("registered DatasetReference does not match AnalysisRequest dataset_ref_id")
    if dataset.selected_sheet != request.selected_sheet:
        raise ApplicationServiceError("DatasetReference selected_sheet does not match AnalysisRequest")
    if dataset.selected_table != request.selected_table:
        raise ApplicationServiceError("DatasetReference selected_table does not match AnalysisRequest")


def _validate_execution_results(
    *,
    execution_records: tuple[ExecutionRecord, ...],
    executed_results: tuple[ExecutedResult, ...],
    plan,
    canonical_dataset,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> tuple[tuple[ValidationRecord, ...], tuple[ValidatedResult, ...]]:
    record_by_result = {record.result_ref: record for record in execution_records if record.result_ref is not None}
    record_by_node = {record.plan_node_id: record for record in execution_records if record.plan_node_id is not None}
    result_by_id = {result.result_id: result for result in executed_results}
    node_by_id = {node.node_id: node for node in plan.ordered_metrics}
    validated: list[ValidatedResult] = []
    validated_by_node_id: dict[str, ValidatedResult] = {}
    records: list[ValidationRecord] = []

    for result in executed_results:
        record = record_by_result.get(result.result_id)
        if record is None:
            raise ApplicationServiceError("ExecutedResult lacks authentic ExecutionRecord lineage")
        if record.execution_id != result.execution_id:
            raise ApplicationServiceError("ExecutedResult execution_id conflicts with ExecutionRecord")
        if record.plan_node_id not in node_by_id:
            raise ApplicationServiceError("ExecutionRecord lacks authentic plan-node lineage")

    for node in plan.ordered_metrics:
        if node.planning_state != "executable":
            continue
        record = record_by_node.get(node.node_id)
        if record is None:
            raise ApplicationServiceError("executable plan node lacks an ExecutionRecord")
        if record.status is not ExecutionStatus.COMPLETED:
            continue
        if record.result_ref is None:
            raise ApplicationServiceError("completed ExecutionRecord lacks an ExecutedResult reference")
        result = result_by_id.get(record.result_ref)
        if result is None:
            raise ApplicationServiceError("ExecutionRecord result_ref is missing from execution outcome")
        dependencies = tuple(
            validated_by_node_id[dependency_id]
            for dependency_id in node.dependency_node_ids
            if dependency_id in validated_by_node_id
        )
        outcome = validate_executed_result(
            execution_id=record.execution_id,
            result_id=result.result_id,
            plan=plan,
            canonical_dataset=canonical_dataset,
            artifact_store=artifact_store,
            metadata_store=metadata_store,
            dependency_validated_results=dependencies,
        )
        records.extend(outcome.validation_records)
        if outcome.validated_result is not None:
            validated.append(outcome.validated_result)
            validated_by_node_id[node.node_id] = outcome.validated_result
    return tuple(records), tuple(validated)


def _admit_requested_evidence(
    *,
    request: AnalysisRequest,
    sufficiency: DataSufficiencyResult,
    validated_results: tuple[ValidatedResult, ...],
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> tuple[tuple[EvidenceAdmissibilityRecord, ...], tuple[FailureDetail, ...]]:
    requested_metrics = {metric.metric_id for metric in request.metrics}
    evidence_records: list[EvidenceAdmissibilityRecord] = []
    failures: list[FailureDetail] = []
    for result in validated_results:
        if result.metric_ref not in requested_metrics:
            continue
        outcome = evaluate_evidence_admissibility(
            request_id=request.request_id,
            sufficiency_id=sufficiency.sufficiency_id,
            validated_result_id=result.validated_result_id,
            claim_type=ClaimType.DESCRIPTIVE,
            artifact_store=artifact_store,
            metadata_store=metadata_store,
            supplied_request=request,
            supplied_sufficiency=sufficiency,
            supplied_validated_result=result,
            evidence_role=EvidenceRole.METRIC_STATE if result.metric_state is MetricState.UNDEFINED else None,
        )
        evidence_records.append(outcome.admissibility_record)
        if outcome.admissible_evidence is None and outcome.admissibility_record.failure_code is not None:
            failures.append(
                FailureDetail(
                    stage=FailureStage.EVIDENCE,
                    reason=outcome.admissibility_record.failure_reason or outcome.admissibility_record.failure_code,
                    target_ref=result.validated_result_id,
                    governing_ref="tasks:P6-001",
                    dependency_scope=result.metric_ref,
                    independent_chains_may_continue=True,
                )
            )
    return tuple(evidence_records), tuple(failures)


def _analysis_result(
    *,
    request: AnalysisRequest,
    sufficiency: DataSufficiencyResult,
    execution_records: tuple[ExecutionRecord, ...],
    executed_results: tuple[ExecutedResult, ...],
    plan,
    dataset: DatasetReference,
    canonicalization,
    validation_records: tuple[ValidationRecord, ...],
    validated_results: tuple[ValidatedResult, ...],
    evidence_records: tuple[EvidenceAdmissibilityRecord, ...],
    evidence_failures: tuple[FailureDetail, ...],
) -> AnalysisResult:
    metric_results = tuple(
        _metric_result(
            metric_ref=metric.metric_id,
            sufficiency=sufficiency,
            execution_records=execution_records,
            executed_results=executed_results,
            plan=plan,
            validation_records=validation_records,
            validated_results=validated_results,
            evidence_records=evidence_records,
            evidence_failures=evidence_failures,
        )
        for metric in request.metrics
    )
    all_failures = _dedupe_failures(
        tuple(detail for result in metric_results for detail in result.failure_details)
    )
    return AnalysisResult(
        request_id=request.request_id,
        run_id=generate_id("run"),
        traceability_id=sufficiency.sufficiency_id,
        run_status=_run_status(metric_results, sufficiency, execution_records, validation_records),
        data_sufficiency_ref=sufficiency.sufficiency_id,
        data_sufficiency_state=sufficiency.state,
        metric_results=metric_results,
        failure_details=all_failures,
        executed_result_refs=tuple(dict.fromkeys(result.result_id for result in executed_results)),
        validation_record_refs=tuple(dict.fromkeys(record.validation_id for record in validation_records)),
        validated_result_refs=tuple(dict.fromkeys(result.validated_result_id for result in validated_results)),
        admissible_evidence_refs=tuple(
            dict.fromkeys(
                record.admissible_evidence_id
                for record in evidence_records
                if record.admissible_evidence_id is not None
            )
        ),
        claim_decisions=(),
        qualifications=sufficiency.qualifications,
        assumptions=request.assumptions,
        blocked_metric_refs=tuple(
            dict.fromkeys(
                eligibility.metric_ref
                for eligibility in sufficiency.metric_eligibility
                if not eligibility.eligible
            )
        ),
        artifacts=_analysis_artifacts(
            dataset=dataset,
            canonicalization=canonicalization,
            execution_records=execution_records,
            validation_records=validation_records,
            evidence_records=evidence_records,
        ),
    )


def _metric_result(
    *,
    metric_ref: str,
    sufficiency: DataSufficiencyResult,
    execution_records: tuple[ExecutionRecord, ...],
    executed_results: tuple[ExecutedResult, ...],
    plan,
    validation_records: tuple[ValidationRecord, ...],
    validated_results: tuple[ValidatedResult, ...],
    evidence_records: tuple[EvidenceAdmissibilityRecord, ...],
    evidence_failures: tuple[FailureDetail, ...],
) -> MetricResult:
    execution_by_id = {record.execution_id: record for record in execution_records}
    node_by_id = {node.node_id: node for node in plan.ordered_metrics} if plan is not None else {}
    executed = tuple(result for result in executed_results if _executed_belongs_to_metric(result, execution_by_id, node_by_id, metric_ref))
    validations = tuple(record for record in validation_records if _validation_belongs_to_metric(record, execution_by_id, node_by_id, metric_ref))
    validated = tuple(result for result in validated_results if result.metric_ref == metric_ref)
    failure_details = _dedupe_failures(
        (
            *_sufficiency_failures(metric_ref, sufficiency),
            *(
                detail
                for record in execution_records
                if _execution_belongs_to_metric(record, node_by_id, metric_ref)
                for detail in record.failure_details
                if detail.dependency_scope in (None, metric_ref) or metric_ref in _authorized_metric_refs(record, node_by_id)
            ),
            *(detail for record in validations for detail in record.failure_details),
            *(detail for detail in evidence_failures if detail.dependency_scope in (None, metric_ref)),
        )
    )
    return MetricResult(
        metric_ref=metric_ref,
        metric_state=_metric_state(metric_ref, sufficiency, executed, validated, validations, failure_details),
        executed_result_refs=tuple(result.result_id for result in executed),
        validation_record_refs=tuple(record.validation_id for record in validations),
        validated_result_refs=tuple(result.validated_result_id for result in validated),
        admissible_evidence_refs=tuple(
            dict.fromkeys(
                record.admissible_evidence_id
                for record in evidence_records
                if record.metric_ref == metric_ref and record.admissible_evidence_id is not None
            )
        ),
        failure_details=failure_details,
        qualifications=sufficiency.qualifications,
    )


def _sufficiency_failures(metric_ref: str, sufficiency: DataSufficiencyResult) -> tuple[FailureDetail, ...]:
    failures: list[FailureDetail] = []
    for eligibility in sufficiency.metric_eligibility:
        if eligibility.metric_ref == metric_ref and not eligibility.eligible:
            failures.extend(eligibility.failure_details)
    return tuple(failures)


def _metric_state(
    metric_ref: str,
    sufficiency: DataSufficiencyResult,
    executed: tuple[ExecutedResult, ...],
    validated: tuple[ValidatedResult, ...],
    validations: tuple[ValidationRecord, ...],
    failure_details: tuple[FailureDetail, ...],
) -> MetricState:
    for eligibility in sufficiency.metric_eligibility:
        if eligibility.metric_ref == metric_ref and not eligibility.eligible:
            return eligibility.metric_state or MetricState.INADMISSIBLE
    if any(record.status is ValidationStatus.FAILED for record in validations):
        return MetricState.INADMISSIBLE
    if executed and not validations:
        return MetricState.INADMISSIBLE
    if not executed and failure_details:
        return MetricState.INADMISSIBLE
    states = tuple(result.metric_state for result in validated)
    if any(state is MetricState.UNDEFINED for state in states):
        return MetricState.UNDEFINED
    if states and all(state is MetricState.VALID for state in states):
        return MetricState.VALID
    if states:
        return states[0]
    return MetricState.INADMISSIBLE


def _run_status(
    metric_results: tuple[MetricResult, ...],
    sufficiency: DataSufficiencyResult,
    execution_records: tuple[ExecutionRecord, ...],
    validation_records: tuple[ValidationRecord, ...],
) -> RunStatus:
    if sufficiency.state is SufficiencyState.CLARIFICATION_REQUIRED:
        return RunStatus.CLARIFICATION_REQUIRED
    if not any(result.executed_result_refs or result.validated_result_refs for result in metric_results):
        return RunStatus.BLOCKED
    has_valid = any(result.metric_state is MetricState.VALID for result in metric_results)
    has_non_valid = any(result.metric_state is not MetricState.VALID for result in metric_results)
    has_validation_failure = any(record.status is ValidationStatus.FAILED for record in validation_records)
    has_execution_failure = any(record.status is ExecutionStatus.FAILED for record in execution_records)
    if has_valid and has_non_valid:
        return RunStatus.PARTIALLY_COMPLETED
    if has_validation_failure:
        return RunStatus.VALIDATION_FAILED if not has_valid else RunStatus.PARTIALLY_COMPLETED
    if has_execution_failure:
        return RunStatus.EXECUTION_FAILED if not has_valid else RunStatus.PARTIALLY_COMPLETED
    if has_non_valid and any(result.failure_details for result in metric_results):
        return RunStatus.PARTIALLY_COMPLETED if has_valid else RunStatus.BLOCKED
    return RunStatus.COMPLETED


def _dedupe_failures(failures: tuple[FailureDetail, ...]) -> tuple[FailureDetail, ...]:
    return tuple(dict.fromkeys(failures))


def _validation_belongs_to_metric(
    record: ValidationRecord,
    execution_by_id: dict[str, ExecutionRecord],
    node_by_id: dict[str, object],
    metric_ref: str,
) -> bool:
    if record.metric_ref == metric_ref:
        return True
    execution = execution_by_id.get(record.execution_id)
    if execution is None:
        return False
    return _execution_belongs_to_metric(execution, node_by_id, metric_ref)


def _executed_belongs_to_metric(
    result: ExecutedResult,
    execution_by_id: dict[str, ExecutionRecord],
    node_by_id: dict[str, object],
    metric_ref: str,
) -> bool:
    if result.metric_ref == metric_ref:
        return True
    execution = execution_by_id.get(result.execution_id)
    if execution is None:
        return False
    return _execution_belongs_to_metric(execution, node_by_id, metric_ref)


def _execution_belongs_to_metric(
    record: ExecutionRecord,
    node_by_id: dict[str, object],
    metric_ref: str,
) -> bool:
    if metric_ref in record.metric_refs:
        return True
    if metric_ref in _authorized_metric_refs(record, node_by_id):
        return True
    return any(detail.dependency_scope == metric_ref for detail in record.failure_details)


def _authorized_metric_refs(record: ExecutionRecord, node_by_id: dict[str, object]) -> tuple[str, ...]:
    node = node_by_id.get(record.plan_node_id)
    if node is None:
        return ()
    return tuple(getattr(node, "authorized_requested_metric_refs", ()))


def _analysis_artifacts(
    *,
    dataset: DatasetReference,
    canonicalization,
    execution_records: tuple[ExecutionRecord, ...],
    validation_records: tuple[ValidationRecord, ...],
    evidence_records: tuple[EvidenceAdmissibilityRecord, ...],
) -> tuple[ArtifactReference, ...]:
    artifacts: list[ArtifactReference] = []
    if dataset.snapshot_artifact is not None:
        artifacts.append(dataset.snapshot_artifact)
    if canonicalization.canonical_dataset is not None:
        artifacts.append(canonicalization.canonical_dataset.artifact)
    artifacts.extend(
        artifact
        for record in execution_records
        for artifact in record.output_artifacts
    )
    artifacts.extend(
        record.validated_result_artifact_ref
        for record in validation_records
        if record.validated_result_artifact_ref is not None
    )
    artifacts.extend(
        record.admissible_evidence_artifact_ref
        for record in evidence_records
        if record.admissible_evidence_artifact_ref is not None
    )
    deduped: list[ArtifactReference] = []
    seen: set[str] = set()
    for artifact in artifacts:
        if artifact.artifact_id in seen:
            continue
        seen.add(artifact.artifact_id)
        deduped.append(artifact)
    return tuple(deduped)
