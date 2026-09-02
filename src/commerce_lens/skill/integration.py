"""Public v0.1 Skill integration over the frozen application service."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from commerce_lens.application import evaluate_claim, run_analysis
from commerce_lens.canonical import CanonicalizationRequest, EligibilityMode, EligibilityState, EligibilityValueMapping
from commerce_lens.canonical.mapping import CanonicalMapping, identity_mapping
from commerce_lens.canonical.models import PeriodCoverageEvidence
from commerce_lens.canonical.schema import CANONICAL_SCHEMA_VERSION
from commerce_lens.contracts.common import (
    AvailableEvidence,
    ClaimType,
    EvidenceRequirement,
    GroupingDimension,
    MetricState,
    PeriodDefinition,
    ScopeDefinition,
    SourceType,
)
from commerce_lens.contracts.evidence import (
    AdmissibleEvidence,
    ClaimCandidate,
    ClaimDecision,
    ClaimPropositionType,
    EvidenceAdmissibilityStatus,
    MetricReference,
)
from commerce_lens.contracts.requests import AnalysisRequest
from commerce_lens.contracts.results import AnalysisResult, MetricResult
from commerce_lens.contracts.validation import ValidatedResult
from commerce_lens.evidence.identifiers import generate_id
from commerce_lens.intake.csv_adapter import CsvInspectionAdapter
from commerce_lens.intake.excel_adapter import ExcelInspectionAdapter
from commerce_lens.intake.inspection import InspectionStatus
from commerce_lens.intake.registry import DatasetRegistry
from commerce_lens.metrics import METRIC_REGISTRY_VERSION, get_metric_registry
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.skill.public_response import EvaluatedClaimAuthority, PublicResponse, project_public_response


PUBLIC_V0_1_METRICS = frozenset({"revenue", "orders", "aov", "revenue_change"})
PUBLIC_SINGLE_PERIOD_METRICS = frozenset({"revenue", "orders", "aov"})
_SUPPORTED_SOURCE_TYPES = frozenset({SourceType.CSV, SourceType.EXCEL_XLSX})
_SUPPORTED_QUESTION_CLASSES = frozenset(
    {
        "single_period_metric",
        "revenue_change",
        "diagnostic_revenue_drop",
    }
)


class PublicQuestionClass(str, Enum):
    SINGLE_PERIOD_METRIC = "single_period_metric"
    REVENUE_CHANGE = "revenue_change"
    DIAGNOSTIC_REVENUE_DROP = "diagnostic_revenue_drop"


@dataclass(frozen=True)
class PublicSourceSelection:
    source_path: Path
    source_type: SourceType
    selected_sheet: str | None = None
    selected_table: str | None = None
    mapping: CanonicalMapping | None = None
    mapping_mode: str = "identity_canonical_columns"


@dataclass(frozen=True)
class PublicClaimIntent:
    claim_type: ClaimType = ClaimType.DESCRIPTIVE
    proposed_meaning: str = "Public v0.1 governed descriptive Metric claim"


@dataclass(frozen=True)
class PublicAnalysisIntent:
    question_class: PublicQuestionClass | str
    metric_id: str
    baseline_period: PeriodDefinition | None
    comparison_period: PeriodDefinition | None
    source: PublicSourceSelection
    original_question_text: str | None = None
    scope: ScopeDefinition = ScopeDefinition(scope_id="all_eligible")
    grouping: GroupingDimension = GroupingDimension.NONE
    result_period_role: str | None = None
    claim_intents: tuple[PublicClaimIntent, ...] = (PublicClaimIntent(),)


@dataclass(frozen=True)
class PublicAnalysisOutcome:
    intent: PublicAnalysisIntent
    response: PublicResponse
    request: AnalysisRequest | None = None
    analysis_result: AnalysisResult | None = None
    claim_candidates: tuple[ClaimCandidate, ...] = ()
    claim_decisions: tuple[ClaimDecision, ...] = ()


def validate_public_intent(intent: PublicAnalysisIntent) -> tuple[str, ...]:
    """Validate host-interpreted intent fail-closed before constructing a request."""
    failures: list[str] = []
    question_class = _question_class_value(intent.question_class)
    if question_class not in _SUPPORTED_QUESTION_CLASSES:
        failures.append(f"unsupported question class: {question_class}")
    if intent.metric_id not in PUBLIC_V0_1_METRICS:
        failures.append(f"unsupported Public v0.1 Metric: {intent.metric_id}")
    if intent.metric_id == "revenue_change" and question_class == PublicQuestionClass.SINGLE_PERIOD_METRIC.value:
        failures.append("revenue_change requires an explicitly comparable period question class")
    if intent.metric_id in PUBLIC_SINGLE_PERIOD_METRICS and question_class != PublicQuestionClass.SINGLE_PERIOD_METRIC.value:
        failures.append(f"{intent.metric_id} requires a single-period question class")
    if intent.grouping is not GroupingDimension.NONE:
        failures.append("Public v0.1 supports grouping NONE only")
    if intent.source.source_type not in _SUPPORTED_SOURCE_TYPES:
        failures.append(f"unsupported Public v0.1 source type: {intent.source.source_type.value}")
    if intent.source.selected_table is not None:
        failures.append("Public v0.1 does not expose table selection as a headline CSV/XLSX workflow")
    if intent.source.mapping is None and intent.source.mapping_mode != "identity_canonical_columns":
        failures.append("mapping selection requires clarification")
    if intent.baseline_period is None or intent.comparison_period is None:
        failures.append("explicit governed baseline and comparison periods are required by the current AnalysisRequest contract")
    if intent.metric_id in PUBLIC_SINGLE_PERIOD_METRICS and intent.result_period_role not in ("baseline", "comparison"):
        failures.append("single-period Metric intent requires an explicit result_period_role of baseline or comparison")
    if intent.metric_id == "revenue_change" and intent.result_period_role not in (None, "comparison"):
        failures.append("Revenue Change public response uses the governed comparison result")
    if not intent.claim_intents:
        failures.append("at least one Claim intent is required")
    for claim_intent in intent.claim_intents:
        if claim_intent.claim_type in (ClaimType.PREDICTIVE, ClaimType.CAUSAL, ClaimType.PRESCRIPTIVE):
            failures.append(f"unsupported Claim type: {claim_intent.claim_type.value}")
    return tuple(dict.fromkeys(failures))


def run_public_analysis(
    intent: PublicAnalysisIntent,
    *,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    available_evidence: tuple[AvailableEvidence, ...] | None = None,
    period_coverage_evidence: tuple[PeriodCoverageEvidence, ...] | None = None,
) -> PublicAnalysisOutcome:
    """Run the approved Public v0.1 integration chain."""
    validation_failures = validate_public_intent(intent)
    if validation_failures:
        return PublicAnalysisOutcome(
            intent=intent,
            response=PublicResponse(clarification_required=validation_failures),
        )

    source_headers, source_failure = _source_headers(intent.source)
    if source_failure is not None:
        return PublicAnalysisOutcome(
            intent=intent,
            response=PublicResponse(clarification_required=(source_failure,)),
        )

    artifact_store.ensure_layout()
    metadata_store.initialize()
    dataset = DatasetRegistry(artifact_store).register_source(
        intent.source.source_path,
        intent.source.source_type,
        selected_sheet=intent.source.selected_sheet,
        selected_table=intent.source.selected_table,
        metadata={"public_workflow": "public_v0_1"},
    )
    request = _analysis_request(intent, dataset.dataset_id)
    canonicalization_request = _canonicalization_request(intent, dataset.dataset_id, source_headers)
    result = run_analysis(
        request,
        canonicalization_request=canonicalization_request,
        artifact_store=artifact_store,
        metadata_store=metadata_store,
        source_path=intent.source.source_path,
        source_type=intent.source.source_type,
        selected_sheet=intent.source.selected_sheet,
        selected_table=intent.source.selected_table,
        available_evidence=available_evidence if available_evidence is not None else _available_evidence(request),
        period_coverage_evidence=(
            period_coverage_evidence
            if period_coverage_evidence is not None
            else _period_coverage_evidence(request)
        ),
    )

    evaluated: list[EvaluatedClaimAuthority] = []
    candidates: list[ClaimCandidate] = []
    decisions: list[ClaimDecision] = []
    for claim_intent in intent.claim_intents:
        try:
            candidate, validated, evidence = bind_claim_candidate_from_authority(
                intent,
                result,
                artifact_store=artifact_store,
                metadata_store=metadata_store,
                claim_type=claim_intent.claim_type,
                proposed_meaning=claim_intent.proposed_meaning,
            )
        except ValueError:
            continue
        decision = evaluate_claim(candidate, artifact_store=artifact_store, metadata_store=metadata_store)
        candidates.append(candidate)
        decisions.append(decision)
        evaluated.append(
            EvaluatedClaimAuthority(
                candidate=candidate,
                decision=decision,
                validated_result=validated,
                evidence=evidence,
            )
        )

    return PublicAnalysisOutcome(
        intent=intent,
        request=request,
        analysis_result=result,
        claim_candidates=tuple(candidates),
        claim_decisions=tuple(decisions),
        response=project_public_response(
            intent=intent,
            request=request,
            result=result,
            evaluated_claims=tuple(evaluated),
            metadata_store=metadata_store,
        ),
    )


def bind_claim_candidate_from_authority(
    intent: PublicAnalysisIntent,
    result: AnalysisResult,
    *,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
    claim_type: ClaimType,
    proposed_meaning: str,
) -> tuple[ClaimCandidate, ValidatedResult, AdmissibleEvidence]:
    """Bind one schema-valid ClaimCandidate from exact AnalysisResult refs."""
    metric = _metric_result(result, intent.metric_id)
    if metric is None:
        raise ValueError(f"AnalysisResult has no MetricResult for {intent.metric_id}")
    validated = _select_validated_result_from_metric(metric, intent, artifact_store, metadata_store)
    evidence = _select_admissible_evidence_from_metric(metric, validated, artifact_store, metadata_store)
    execution_record = metadata_store.get_execution_record(validated.execution_id)
    if execution_record is None:
        raise ValueError(f"missing execution authority for {validated.execution_id}")

    update = {}
    if validated.metric_ref == "revenue_change":
        if len(execution_record.period_refs) != 2 or len(execution_record.population_refs) != 2:
            raise ValueError("Revenue Change execution authority lacks exact baseline/comparison context")
        update = {
            "baseline_period_ref": execution_record.period_refs[0],
            "comparison_period_ref": execution_record.period_refs[1],
            "baseline_population_ref": execution_record.population_refs[0],
            "comparison_population_ref": execution_record.population_refs[1],
            "baseline_population_fingerprint": execution_record.population_fingerprints[0],
            "comparison_population_fingerprint": execution_record.population_fingerprints[1],
        }

    return (
        ClaimCandidate(
            claim_candidate_id=generate_id("clmcand_public_v0_1"),
            claim_id=generate_id("claim_public_v0_1"),
            claim_type=claim_type,
            metric_ref=validated.metric_ref,
            metric_definition_version=validated.metric_definition_version,
            request_id=result.request_id,
            dataset_ref_id=evidence.dataset_ref_id,
            canonical_dataset_ref_id=evidence.canonical_dataset_ref_id,
            canonical_dataset_fingerprint=evidence.canonical_dataset_fingerprint,
            intended_scope=evidence.scope,
            population_ref=validated.population_ref,
            population_fingerprint=validated.population_fingerprint,
            period_ref=validated.period_ref,
            period_role=validated.period_role,
            proposition_type=(
                ClaimPropositionType.METRIC_STATE_IS
                if validated.metric_state is MetricState.UNDEFINED
                else ClaimPropositionType.METRIC_VALUE_EQUALS
            ),
            claimed_value=None if validated.metric_state is MetricState.UNDEFINED else validated.value,
            claimed_metric_state=MetricState.UNDEFINED if validated.metric_state is MetricState.UNDEFINED else None,
            undefined_reason=validated.undefined_reason,
            unit=validated.unit,
            currency=validated.currency,
            supporting_evidence_refs=(evidence.evidence_id,),
            supporting_validated_result_refs=evidence.validated_result_ids,
            proposed_meaning=proposed_meaning,
            **update,
        ),
        validated,
        evidence,
    )


def _question_class_value(question_class: PublicQuestionClass | str) -> str:
    if isinstance(question_class, PublicQuestionClass):
        return question_class.value
    return str(question_class)


def _source_headers(source: PublicSourceSelection) -> tuple[tuple[str, ...], str | None]:
    if source.source_type is SourceType.CSV:
        inspection = CsvInspectionAdapter().inspect(source.source_path)
        if inspection.status is not InspectionStatus.SUPPORTED:
            reason = inspection.failure_detail.reason if inspection.failure_detail is not None else inspection.status.value
            return (), reason
        return _csv_headers(source.source_path), None
    if source.source_type is SourceType.EXCEL_XLSX:
        inspection = ExcelInspectionAdapter().inspect(source.source_path, sheet_name=source.selected_sheet)
        if inspection.status is not InspectionStatus.SUPPORTED:
            reason = inspection.failure_detail.reason if inspection.failure_detail is not None else inspection.status.value
            return (), reason
        return tuple(column.name for column in inspection.columns), None
    return (), f"unsupported Public v0.1 source type: {source.source_type.value}"


def _csv_headers(path: Path) -> tuple[str, ...]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as file_obj:
        return tuple(next(csv.reader(file_obj)))


def _analysis_request(intent: PublicAnalysisIntent, dataset_ref_id: str) -> AnalysisRequest:
    registry = get_metric_registry()
    metric = registry.require(intent.metric_id)
    assert intent.baseline_period is not None
    assert intent.comparison_period is not None
    return AnalysisRequest(
        canonical_business_question_id=f"public_v0_1:{_question_class_value(intent.question_class)}",
        original_question_text=intent.original_question_text,
        metrics=(MetricReference(metric_id=metric.metric_id, definition_version=metric.definition_version),),
        baseline_period=intent.baseline_period,
        comparison_period=intent.comparison_period,
        scope=intent.scope,
        grouping=GroupingDimension.NONE,
        required_evidence=_requirements((intent.metric_id,)),
        dataset_ref_id=dataset_ref_id,
        selected_sheet=intent.source.selected_sheet,
        selected_table=intent.source.selected_table,
        canonical_schema_version=CANONICAL_SCHEMA_VERSION,
        metric_registry_version=METRIC_REGISTRY_VERSION,
    )


def _canonicalization_request(
    intent: PublicAnalysisIntent,
    dataset_ref_id: str,
    source_headers: tuple[str, ...],
) -> CanonicalizationRequest:
    return CanonicalizationRequest(
        source_dataset_id=dataset_ref_id,
        selected_sheet=intent.source.selected_sheet,
        selected_table=intent.source.selected_table,
        mapping=intent.source.mapping or identity_mapping(source_headers, require_eligibility=True),
        eligibility_mode=EligibilityMode.EXPLICIT_STATUS_MAPPING,
        eligibility_value_mapping=(
            EligibilityValueMapping(source_value="paid", normalized_status=EligibilityState.ELIGIBLE),
            EligibilityValueMapping(source_value="cancelled", normalized_status=EligibilityState.EXCLUDED),
        ),
    )


def _requirements(metrics: tuple[str, ...]) -> tuple[EvidenceRequirement, ...]:
    return (
        EvidenceRequirement(requirement_id="req_global", description="global source authority"),
        *(
            EvidenceRequirement(requirement_id=f"req_{metric}", description=f"{metric} authority", metric_ref=metric)
            for metric in metrics
        ),
    )


def _available_evidence(request: AnalysisRequest) -> tuple[AvailableEvidence, ...]:
    return (
        AvailableEvidence(
            evidence_id="avail_source",
            description="governed source and period coverage",
            source_ref=request.dataset_ref_id,
            satisfies_requirement_ids=tuple(requirement.requirement_id for requirement in request.required_evidence),
        ),
    )


def _period_coverage_evidence(request: AnalysisRequest) -> tuple[PeriodCoverageEvidence, ...]:
    return (
        PeriodCoverageEvidence(
            coverage_ref_id="coverage_all",
            dataset_ref_id=request.dataset_ref_id,
            observed_start_date=min(request.baseline_period.start_date, request.comparison_period.start_date),
            observed_end_date=max(request.baseline_period.end_date, request.comparison_period.end_date),
            date_convention_ref=request.baseline_period.date_convention_ref,
        ),
    )


def _metric_result(result: AnalysisResult, metric_ref: str) -> MetricResult | None:
    matches = tuple(item for item in result.metric_results if item.metric_ref == metric_ref)
    if len(matches) != 1:
        return None
    return matches[0]


def _select_validated_result_from_metric(
    metric: MetricResult,
    intent: PublicAnalysisIntent,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ValidatedResult:
    candidates = tuple(_load_validated_result(ref, artifact_store, metadata_store) for ref in metric.validated_result_refs)
    if intent.metric_id in PUBLIC_SINGLE_PERIOD_METRICS:
        candidates = tuple(result for result in candidates if result.period_role == intent.result_period_role)
    elif intent.metric_id == "revenue_change":
        candidates = tuple(result for result in candidates if result.metric_ref == "revenue_change")
    if len(candidates) != 1:
        raise ValueError(f"expected one exact ValidatedResult authority, observed {len(candidates)}")
    return candidates[0]


def _load_validated_result(
    validated_result_id: str,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ValidatedResult:
    records = tuple(
        record
        for record in metadata_store.list_validation_records()
        if record.validated_result_ref == validated_result_id
        and record.validated_result_artifact_ref is not None
    )
    if not records:
        raise ValueError(f"ValidatedResult authority is not exact for {validated_result_id}")
    artifact_paths = tuple(dict.fromkeys(record.validated_result_artifact_ref.path for record in records))
    if len(artifact_paths) != 1:
        raise ValueError(f"ValidatedResult authority is not exact for {validated_result_id}")
    validated = ValidatedResult.model_validate_json(
        artifact_store.safe_path(artifact_paths[0]).read_text(encoding="utf-8")
    )
    if validated.validated_result_id != validated_result_id:
        raise ValueError(f"ValidatedResult artifact identity mismatch for {validated_result_id}")
    return validated


def _select_admissible_evidence_from_metric(
    metric: MetricResult,
    validated: ValidatedResult,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> AdmissibleEvidence:
    wanted_refs = set(metric.admissible_evidence_refs)
    records = tuple(
        record
        for record in metadata_store.list_evidence_admissibility_records()
        if record.status is EvidenceAdmissibilityStatus.PASSED
        and record.admissible_evidence_id in wanted_refs
        and record.validated_result_id == validated.validated_result_id
    )
    if len(records) != 1 or records[0].admissible_evidence_artifact_ref is None:
        raise ValueError(f"AdmissibleEvidence authority is not exact for {validated.validated_result_id}")
    evidence = AdmissibleEvidence.model_validate_json(
        artifact_store.safe_path(records[0].admissible_evidence_artifact_ref.path).read_text(encoding="utf-8")
    )
    if evidence.validated_result_ids != (validated.validated_result_id,):
        raise ValueError("AdmissibleEvidence does not bind the selected exact ValidatedResult")
    return evidence
