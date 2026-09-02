"""Thin P9 fixture runner over the public application service."""

from __future__ import annotations

import csv
import tempfile
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from commerce_lens.application import evaluate_claim, run_analysis
from commerce_lens.canonical import (
    CanonicalizationRequest,
    EligibilityMode,
    EligibilityState,
    EligibilityValueMapping,
    identity_mapping,
)
from commerce_lens.canonical.models import PeriodCoverageEvidence
from commerce_lens.contracts.common import (
    AvailableEvidence,
    ClaimState,
    ClaimType,
    EvidenceRequirement,
    GroupingDimension,
    MetricState,
    PeriodDefinition,
    RunStatus,
    ScopeDefinition,
    SourceType,
)
from commerce_lens.contracts.evidence import (
    AdmissibleEvidence,
    ClaimCandidate,
    ClaimPropositionType,
    EvidenceAdmissibilityStatus,
    MetricReference,
)
from commerce_lens.contracts.requests import AnalysisRequest
from commerce_lens.contracts.results import AnalysisResult
from commerce_lens.contracts.validation import ValidatedResult, ValidationStatus
from commerce_lens.evidence.identifiers import generate_id
from commerce_lens.intake.registry import DatasetRegistry
from commerce_lens.metrics import METRIC_DEFINITION_VERSION, METRIC_REGISTRY_VERSION
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore

from commerce_lens.fixture_runner.cases import (
    DEFAULT_CASES_ROOT,
    CaseManifest,
    ExpectedClaim,
    ExpectedMetricResult,
    ExpectedValidatedResult,
    FixtureCase,
    discover_cases,
)
from commerce_lens.fixture_runner.hostile_validation import run_revenue_change_wrong_value_case


CSV_HEADERS = (
    "order_id",
    "order_line_id",
    "order_date",
    "product_id",
    "product_name",
    "category_id",
    "category_name",
    "quantity",
    "line_revenue",
    "currency",
    "unit_price",
    "eligibility_status",
)


@dataclass(frozen=True)
class CaseRunResult:
    case_id: str
    passed: bool
    mismatches: tuple[str, ...] = ()
    observed: dict[str, object] | None = None


@dataclass(frozen=True)
class _Runtime:
    artifact_store: ArtifactStore
    metadata_store: MetadataStore
    root: Path


@dataclass(frozen=True)
class _AnalysisContext:
    result: AnalysisResult
    request: AnalysisRequest
    artifact_store: ArtifactStore
    metadata_store: MetadataStore


def run_suite(
    cases_root: str | Path = DEFAULT_CASES_ROOT,
    *,
    runtime_root: str | Path | None = None,
    case_order: tuple[str, ...] | None = None,
) -> tuple[CaseRunResult, ...]:
    """Run the exact P9 inventory and return ordered per-case outcomes."""
    cases = discover_cases(cases_root)
    if case_order is not None:
        by_id = {case.case_id: case for case in cases}
        if set(case_order) != set(by_id) or len(case_order) != len(by_id):
            raise ValueError("case_order must contain each discovered P9 case exactly once")
        cases = tuple(by_id[case_id] for case_id in case_order)
    return tuple(run_case(case, runtime_root=runtime_root) for case in cases)


def run_case(case: FixtureCase, *, runtime_root: str | Path | None = None) -> CaseRunResult:
    """Run one P9 case in an isolated runtime directory."""
    try:
        return _run_case(case, runtime_root=runtime_root)
    except Exception as exc:
        return CaseRunResult(case_id=case.case_id, passed=False, mismatches=(f"case execution failed closed: {exc}",))


def _run_case(case: FixtureCase, *, runtime_root: str | Path | None = None) -> CaseRunResult:
    with _isolated_runtime(case.case_id, runtime_root) as runtime:
        if case.case_id == "P9-CONF-VAL-REVCHG-WRONG-VALUE-001":
            return _compare_hostile(case.manifest, runtime)
        if case.case_id == "P9-CONF-CLAIM-DIAGNOSTIC-REFUSAL-001":
            return _run_diagnostic_refusal(case.manifest, runtime)
        if case.case_id == "P9-CONF-TAMPER-CROSS-REQUEST-001":
            return _run_cross_request_tamper(case.manifest, runtime)
        if case.input_path is None:
            raise ValueError(f"{case.case_id} lacks required physical input")
        context = _run_analysis_for_source(case.manifest, case.input_path, runtime)
        mismatches = _compare_analysis(case.manifest, context)
        mismatches += _evaluate_expected_claims(case.manifest, context)
        mismatches += _compare_claim_decision_absence(case.manifest, context)
        mismatches += _compare_final_disposition(case.manifest, context)
        return CaseRunResult(
            case_id=case.case_id,
            passed=not mismatches,
            mismatches=mismatches,
            observed=_observed_analysis(context),
        )


def _compare_hostile(manifest: CaseManifest, runtime: _Runtime) -> CaseRunResult:
    outcome = run_revenue_change_wrong_value_case(manifest, runtime.root)
    mismatches: list[str] = []
    expected = manifest.expected
    hostile = expected.hostile_revenue_change
    if hostile is None:
        return CaseRunResult(case_id=manifest.case_id, passed=False, mismatches=("missing hostile authority",))
    if outcome.data_sufficiency_state != expected.data_sufficiency_state:
        mismatches.append(
            f"data_sufficiency_state expected {expected.data_sufficiency_state}, observed {outcome.data_sufficiency_state}"
        )
    if outcome.baseline_revenue != hostile.baseline_revenue:
        mismatches.append(f"baseline_revenue expected {hostile.baseline_revenue}, observed {outcome.baseline_revenue}")
    if outcome.comparison_revenue != hostile.comparison_revenue:
        mismatches.append(f"comparison_revenue expected {hostile.comparison_revenue}, observed {outcome.comparison_revenue}")
    if outcome.authoritative_revenue_change != hostile.authoritative_revenue_change:
        mismatches.append(
            f"authoritative_revenue_change expected {hostile.authoritative_revenue_change}, observed {outcome.authoritative_revenue_change}"
        )
    if outcome.submitted_value != hostile.submitted_revenue_change:
        mismatches.append(f"hostile submitted value expected {hostile.submitted_revenue_change}, observed {outcome.submitted_value}")
    if outcome.execution_disposition != expected.execution_disposition:
        mismatches.append(f"execution_disposition expected {expected.execution_disposition}, observed {outcome.execution_disposition}")
    if outcome.validation_status != expected.validation_disposition:
        mismatches.append(f"validation status expected {expected.validation_disposition}, observed {outcome.validation_status}")
    if outcome.validation_rule_id != hostile.validation_rule_id:
        mismatches.append(f"validation rule expected {hostile.validation_rule_id}, observed {outcome.validation_rule_id}")
    if outcome.failure_code != expected.failure_code:
        mismatches.append(f"failure_code expected {expected.failure_code}, observed {outcome.failure_code}")
    if outcome.failure_code != hostile.failure_code:
        mismatches.append(f"hostile failure_code expected {hostile.failure_code}, observed {outcome.failure_code}")
    if outcome.final_disposition != expected.final_disposition:
        mismatches.append(f"final_disposition expected {expected.final_disposition}, observed {outcome.final_disposition}")
    if outcome.validated_result_authorized:
        mismatches.append("hostile failed chain unexpectedly authorized ValidatedResult")
    if outcome.admissible_evidence_authorized:
        mismatches.append("hostile failed chain unexpectedly authorized AdmissibleEvidence")
    if outcome.claim_decision_authorized:
        mismatches.append("hostile failed chain unexpectedly authorized ClaimDecision")
    return CaseRunResult(case_id=manifest.case_id, passed=not mismatches, mismatches=tuple(mismatches), observed=outcome.observed)


def _run_diagnostic_refusal(manifest: CaseManifest, runtime: _Runtime) -> CaseRunResult:
    setup = manifest.setup_contexts[0]
    source_path = _materialize_setup_csv(runtime.root / "setup" / setup.name / "input.csv", setup.rows)
    context = _run_analysis_for_source(manifest, source_path, runtime)
    mismatches = _compare_analysis(manifest, context)
    mismatches += _evaluate_expected_claims(manifest, context)
    mismatches += _compare_claim_decision_absence(manifest, context)
    mismatches += _compare_final_disposition(manifest, context)
    return CaseRunResult(case_id=manifest.case_id, passed=not mismatches, mismatches=mismatches, observed=_observed_analysis(context))


def _run_cross_request_tamper(manifest: CaseManifest, runtime: _Runtime) -> CaseRunResult:
    by_name = {setup.name: setup for setup in manifest.setup_contexts}
    original_path = _materialize_setup_csv(runtime.root / "setup" / "original" / "input.csv", by_name["original"].rows)
    foreign_path = _materialize_setup_csv(runtime.root / "setup" / "foreign" / "input.csv", by_name["foreign"].rows)
    original = _run_analysis_for_source(manifest, original_path, runtime)
    foreign = _run_analysis_for_source(manifest, foreign_path, runtime)
    expected_claim = manifest.expected.expected_claims[0]
    original_result = _select_validated_result(original, expected_claim.metric_ref, expected_claim.period_ref, expected_claim.period_role)
    foreign_result = _select_validated_result(foreign, expected_claim.metric_ref, expected_claim.period_ref, expected_claim.period_role)
    foreign_evidence = _select_admissible_evidence(foreign, expected_claim.metric_ref, expected_claim.period_ref, expected_claim.period_role)
    candidate = _claim_candidate_from_authority(
        original,
        original_result,
        foreign_evidence,
        claim_type=ClaimType(expected_claim.claim_type),
        supporting_validated_result_refs=foreign_evidence.validated_result_ids,
    )
    decision = evaluate_claim(candidate, artifact_store=runtime.artifact_store, metadata_store=runtime.metadata_store)
    mismatches = _compare_analysis(manifest, original)
    if foreign_result.value != original_result.value:
        mismatches += (f"foreign value expected to equal original {original_result.value}, observed {foreign_result.value}",)
    mismatches += _compare_claim_decision(expected_claim, decision.claim_state, decision.failure_code)
    mismatches += _compare_claim_decision_absence(manifest, original)
    mismatches += _compare_final_disposition(manifest, original)
    return CaseRunResult(
        case_id=manifest.case_id,
        passed=not mismatches,
        mismatches=mismatches,
        observed={
            "original_request_id": original.request.request_id,
            "foreign_request_id": foreign.request.request_id,
            "original_value": _json_value(original_result.value),
            "foreign_value": _json_value(foreign_result.value),
            "claim_state": decision.claim_state.value,
            "failure_code": decision.failure_code,
        },
    )


def _run_analysis_for_source(manifest: CaseManifest, source_path: Path, runtime: _Runtime) -> _AnalysisContext:
    dataset = DatasetRegistry(runtime.artifact_store).register_source(source_path, SourceType.CSV)
    request = _analysis_request(manifest.request, dataset.dataset_id)
    result = run_analysis(
        request,
        canonicalization_request=_canonicalization_request(dataset.dataset_id, _read_headers(source_path)),
        artifact_store=runtime.artifact_store,
        metadata_store=runtime.metadata_store,
        source_path=source_path,
        source_type=SourceType.CSV,
        period_coverage_evidence=_coverage(request),
        available_evidence=_available_evidence(request),
    )
    return _AnalysisContext(result=result, request=request, artifact_store=runtime.artifact_store, metadata_store=runtime.metadata_store)


def _analysis_request(spec, dataset_ref_id: str) -> AnalysisRequest:
    return AnalysisRequest(
        canonical_business_question_id=spec.canonical_business_question_id,
        original_question_text=spec.analytical_request_class,
        metrics=tuple(MetricReference(metric_id=metric_id, definition_version=METRIC_DEFINITION_VERSION) for metric_id in spec.metrics),
        baseline_period=_period(spec.baseline_period),
        comparison_period=_period(spec.comparison_period),
        scope=ScopeDefinition(scope_id="all_eligible"),
        grouping=GroupingDimension.NONE,
        required_evidence=_requirements(spec.metrics),
        dataset_ref_id=dataset_ref_id,
        canonical_schema_version="canonical_mvp_v1",
        metric_registry_version=METRIC_REGISTRY_VERSION,
    )


def _period(spec) -> PeriodDefinition:
    return PeriodDefinition(
        period_id=spec.period_id,
        label=spec.label,
        start_date=spec.start_date,
        end_date=spec.end_date,
        date_convention_ref=spec.date_convention_ref,
    )


def _requirements(metrics: tuple[str, ...]) -> tuple[EvidenceRequirement, ...]:
    return (
        EvidenceRequirement(requirement_id="req_global", description="global source authority"),
        *(EvidenceRequirement(requirement_id=f"req_{metric}", description=f"{metric} authority", metric_ref=metric) for metric in metrics),
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


def _coverage(request: AnalysisRequest) -> tuple[PeriodCoverageEvidence, ...]:
    return (
        PeriodCoverageEvidence(
            coverage_ref_id="coverage_all",
            dataset_ref_id=request.dataset_ref_id,
            observed_start_date=request.baseline_period.start_date,
            observed_end_date=request.comparison_period.end_date,
            date_convention_ref="order_date_utc",
        ),
    )


def _canonicalization_request(dataset_ref_id: str, headers: tuple[str, ...]) -> CanonicalizationRequest:
    return CanonicalizationRequest(
        source_dataset_id=dataset_ref_id,
        mapping=identity_mapping(headers, require_eligibility=True),
        eligibility_mode=EligibilityMode.EXPLICIT_STATUS_MAPPING,
        eligibility_value_mapping=(
            EligibilityValueMapping(source_value="paid", normalized_status=EligibilityState.ELIGIBLE),
            EligibilityValueMapping(source_value="cancelled", normalized_status=EligibilityState.EXCLUDED),
        ),
    )


def _compare_analysis(manifest: CaseManifest, context: _AnalysisContext) -> tuple[str, ...]:
    expected = manifest.expected
    result = context.result
    mismatches: list[str] = []
    if result.data_sufficiency_state is None or result.data_sufficiency_state.value != expected.data_sufficiency_state:
        observed = result.data_sufficiency_state.value if result.data_sufficiency_state is not None else None
        mismatches.append(f"data_sufficiency_state expected {expected.data_sufficiency_state}, observed {observed}")
    if expected.run_status is not None and result.run_status.value != expected.run_status:
        mismatches.append(f"run_status expected {expected.run_status}, observed {result.run_status.value}")
    if expected.failure_code is not None and expected.failure_code not in _failure_codes(context):
        mismatches.append(f"failure_code expected {expected.failure_code}, observed {_failure_codes(context)}")
    mismatches.extend(_compare_execution_disposition(context, expected.execution_disposition))
    mismatches.extend(_compare_validation_disposition(context, expected.validation_disposition))
    if expected.no_executed_results and result.executed_result_refs:
        mismatches.append(f"expected no ExecutedResult refs, observed {result.executed_result_refs}")
    if expected.no_validated_results and result.validated_result_refs:
        mismatches.append(f"expected no ValidatedResult refs, observed {result.validated_result_refs}")
    if expected.no_admissible_evidence and result.admissible_evidence_refs:
        mismatches.append(f"expected no AdmissibleEvidence refs, observed {result.admissible_evidence_refs}")
    if expected.no_claim_decision and context.metadata_store.list_claim_decision_records(context.artifact_store):
        mismatches.append("expected no ClaimDecision authority, observed persisted ClaimDecision record(s)")
    for expected_metric in expected.expected_metric_results:
        mismatches.extend(_compare_expected_metric_result(context, expected_metric))
    for expected_result in expected.expected_validated_results:
        mismatches.extend(_compare_expected_validated_result(context, expected_result))
    return tuple(mismatches)


def _compare_execution_disposition(context: _AnalysisContext, expected: str) -> tuple[str, ...]:
    records = _execution_records_for_request(context)
    if expected == "not_started":
        if records:
            return (f"execution_disposition expected not_started, observed {len(records)} ExecutionRecord(s)",)
        return ()
    if expected == "completed":
        if not records:
            return ("execution_disposition expected completed, observed no ExecutionRecord authority",)
        incomplete = tuple(record.status.value for record in records if record.status.value != "completed")
        if incomplete:
            return (f"execution_disposition expected completed, observed non-completed status(es) {incomplete}",)
    return ()


def _compare_validation_disposition(context: _AnalysisContext, expected: str) -> tuple[str, ...]:
    records = _validation_records_for_request(context)
    if expected == "not_started":
        if records:
            return (f"validation_disposition expected not_started, observed {len(records)} ValidationRecord(s)",)
        return ()
    if expected == "passed":
        if not records:
            return ("validation_disposition expected passed, observed no ValidationRecord authority",)
        unexpected = tuple(record.status.value for record in records if record.status is not ValidationStatus.PASSED)
        if unexpected:
            return (f"validation_disposition expected passed, observed status(es) {unexpected}",)
    if expected == "failed":
        if not any(record.status is ValidationStatus.FAILED for record in records):
            return ("validation_disposition expected failed, observed no failed ValidationRecord authority",)
    return ()


def _compare_expected_metric_result(context: _AnalysisContext, expected: ExpectedMetricResult) -> tuple[str, ...]:
    metric = _metric_result(context.result, expected.metric_ref)
    if metric is None:
        raise ValueError(f"AnalysisResult exposes no MetricResult for expected metric {expected.metric_ref}")
    if metric.metric_state.value != expected.metric_state:
        return (f"{expected.metric_ref} MetricResult state expected {expected.metric_state}, observed {metric.metric_state.value}",)
    return ()


def _compare_expected_validated_result(context: _AnalysisContext, expected: ExpectedValidatedResult) -> tuple[str, ...]:
    mismatches: list[str] = []
    metric = _metric_result(context.result, expected.metric_ref)
    if metric is not None and metric.metric_state.value != expected.metric_state:
        mismatches.append(f"{expected.metric_ref} MetricResult state expected {expected.metric_state}, observed {metric.metric_state.value}")
    actual = _select_validated_result(context, expected.metric_ref, expected.period_ref, expected.period_role)
    if actual.metric_state.value != expected.metric_state:
        mismatches.append(f"{expected.metric_ref} ValidatedResult state expected {expected.metric_state}, observed {actual.metric_state.value}")
    if actual.value != expected.value:
        mismatches.append(f"{expected.metric_ref} value expected {expected.value!r}, observed {actual.value!r}")
    if actual.undefined_reason != expected.undefined_reason:
        mismatches.append(
            f"{expected.metric_ref} undefined_reason expected {expected.undefined_reason!r}, observed {actual.undefined_reason!r}"
        )
    if expected.evidence_status is not None:
        record = _select_evidence_record(context, expected.metric_ref, expected.period_ref, expected.period_role)
        if record.status.value != expected.evidence_status:
            mismatches.append(f"{expected.metric_ref} evidence status expected {expected.evidence_status}, observed {record.status.value}")
        role = record.evidence_role.value if record.evidence_role is not None else None
        if role != expected.evidence_role:
            mismatches.append(f"{expected.metric_ref} evidence role expected {expected.evidence_role}, observed {role}")
    return tuple(mismatches)


def _evaluate_expected_claims(manifest: CaseManifest, context: _AnalysisContext) -> tuple[str, ...]:
    mismatches: list[str] = []
    for expected in manifest.expected.expected_claims:
        result = _select_validated_result(context, expected.metric_ref, expected.period_ref, expected.period_role)
        evidence = _select_admissible_evidence(context, expected.metric_ref, expected.period_ref, expected.period_role)
        candidate = _claim_candidate_from_authority(context, result, evidence, claim_type=ClaimType(expected.claim_type))
        decision = evaluate_claim(candidate, artifact_store=context.artifact_store, metadata_store=context.metadata_store)
        mismatches.extend(_compare_claim_decision(expected, decision.claim_state, decision.failure_code))
    return tuple(mismatches)


def _compare_claim_decision(expected: ExpectedClaim, state: ClaimState, failure_code: str | None) -> tuple[str, ...]:
    mismatches: list[str] = []
    if state.value != expected.claim_state:
        mismatches.append(f"{expected.metric_ref} ClaimState expected {expected.claim_state}, observed {state.value}")
    if failure_code != expected.failure_code:
        mismatches.append(f"{expected.metric_ref} Claim failure_code expected {expected.failure_code}, observed {failure_code}")
    return tuple(mismatches)


def _compare_final_disposition(manifest: CaseManifest, context: _AnalysisContext) -> tuple[str, ...]:
    observed = _final_disposition(context)
    if observed != manifest.expected.final_disposition:
        return (f"final_disposition expected {manifest.expected.final_disposition}, observed {observed}",)
    return ()


def _compare_claim_decision_absence(manifest: CaseManifest, context: _AnalysisContext) -> tuple[str, ...]:
    if not manifest.expected.no_claim_decision:
        return ()
    decisions = context.metadata_store.list_claim_decision_records(context.artifact_store)
    if decisions:
        return ("expected no ClaimDecision authority, observed persisted ClaimDecision record(s)",)
    return ()


def _final_disposition(context: _AnalysisContext) -> str:
    decisions = context.metadata_store.list_claim_decision_records(context.artifact_store)
    if decisions:
        if any(decision.claim_state is ClaimState.INADMISSIBLE for decision in decisions):
            return "claim_inadmissible"
        if all(decision.claim_state is ClaimState.ADMISSIBLE for decision in decisions):
            return "completed_admissible"
    if context.result.run_status is RunStatus.BLOCKED:
        return "blocked_insufficient"
    if any(record.status is ValidationStatus.FAILED for record in _validation_records_for_request(context)):
        return "validation_failed"
    return "completed_admissible" if context.result.run_status is RunStatus.COMPLETED else context.result.run_status.value


def _claim_candidate_from_authority(
    context: _AnalysisContext,
    result: ValidatedResult,
    evidence: AdmissibleEvidence,
    *,
    claim_type: ClaimType,
    supporting_validated_result_refs: tuple[str, ...] | None = None,
) -> ClaimCandidate:
    execution_record = context.metadata_store.get_execution_record(result.execution_id)
    if execution_record is None:
        raise ValueError(f"missing execution authority for {result.execution_id}")
    update = {}
    if result.metric_ref == "revenue_change":
        update = {
            "baseline_period_ref": execution_record.period_refs[0],
            "comparison_period_ref": execution_record.period_refs[1],
            "baseline_population_ref": execution_record.population_refs[0],
            "comparison_population_ref": execution_record.population_refs[1],
            "baseline_population_fingerprint": execution_record.population_fingerprints[0],
            "comparison_population_fingerprint": execution_record.population_fingerprints[1],
        }
    return ClaimCandidate(
        claim_candidate_id=generate_id("clmcand_p9"),
        claim_id=generate_id("claim_p9"),
        claim_type=claim_type,
        metric_ref=result.metric_ref,
        metric_definition_version=result.metric_definition_version,
        request_id=context.request.request_id,
        dataset_ref_id=context.request.dataset_ref_id,
        canonical_dataset_ref_id=result.canonical_dataset_ref_id,
        canonical_dataset_fingerprint=result.canonical_dataset_fingerprint,
        intended_scope=evidence.scope,
        population_ref=result.population_ref,
        population_fingerprint=result.population_fingerprint,
        period_ref=result.period_ref,
        period_role=result.period_role,
        proposition_type=(
            ClaimPropositionType.METRIC_STATE_IS
            if result.metric_state is MetricState.UNDEFINED
            else ClaimPropositionType.METRIC_VALUE_EQUALS
        ),
        claimed_value=None if result.metric_state is MetricState.UNDEFINED else result.value,
        claimed_metric_state=MetricState.UNDEFINED if result.metric_state is MetricState.UNDEFINED else None,
        undefined_reason=result.undefined_reason,
        unit=result.unit,
        currency=result.currency,
        supporting_evidence_refs=(evidence.evidence_id,),
        supporting_validated_result_refs=supporting_validated_result_refs or evidence.validated_result_ids,
        proposed_meaning="P9 fixture-declared structured claim",
        metadata={"case_authority": "P9-001"},
        **update,
    )


def _select_validated_result(
    context: _AnalysisContext,
    metric_ref: str,
    period_ref: str | None,
    period_role: str | None,
) -> ValidatedResult:
    matches = tuple(
        result
        for result in _validated_results(context)
        if result.metric_ref == metric_ref
        and (period_ref is None or result.period_ref == period_ref)
        and (period_role is None or result.period_role == period_role)
    )
    if len(matches) != 1:
        raise ValueError(f"expected one ValidatedResult for {metric_ref}, observed {len(matches)}")
    return matches[0]


def _validated_results(context: _AnalysisContext) -> tuple[ValidatedResult, ...]:
    results: list[ValidatedResult] = []
    seen: set[str] = set()
    allowed = set(context.result.validated_result_refs)
    for record in context.metadata_store.list_validation_records():
        artifact = record.validated_result_artifact_ref
        if artifact is None or record.validated_result_ref is None or record.validated_result_ref in seen:
            continue
        if allowed and record.validated_result_ref not in allowed:
            continue
        seen.add(record.validated_result_ref)
        results.append(
            ValidatedResult.model_validate_json(
                context.artifact_store.safe_path(artifact.path).read_text(encoding="utf-8")
            )
        )
    return tuple(results)


def _select_admissible_evidence(
    context: _AnalysisContext,
    metric_ref: str,
    period_ref: str | None,
    period_role: str | None,
) -> AdmissibleEvidence:
    record = _select_evidence_record(context, metric_ref, period_ref, period_role)
    if record.admissible_evidence_artifact_ref is None:
        raise ValueError(f"missing AdmissibleEvidence artifact for {metric_ref}")
    return AdmissibleEvidence.model_validate_json(
        context.artifact_store.safe_path(record.admissible_evidence_artifact_ref.path).read_text(encoding="utf-8")
    )


def _select_evidence_record(context: _AnalysisContext, metric_ref: str, period_ref: str | None, period_role: str | None):
    allowed = set(context.result.admissible_evidence_refs)
    matches = tuple(
        record
        for record in context.metadata_store.list_evidence_admissibility_records()
        if record.status is EvidenceAdmissibilityStatus.PASSED
        and (not allowed or record.admissible_evidence_id in allowed)
        and record.metric_ref == metric_ref
        and (period_ref is None or record.period_ref == period_ref)
        and (period_role is None or record.period_role == period_role)
    )
    if len(matches) != 1:
        raise ValueError(f"expected one passed EvidenceAdmissibilityRecord for {metric_ref}, observed {len(matches)}")
    return matches[0]


def _metric_result(result: AnalysisResult, metric_ref: str):
    return next((item for item in result.metric_results if item.metric_ref == metric_ref), None)


def _execution_records_for_request(context: _AnalysisContext):
    return tuple(record for record in context.metadata_store.list_execution_records() if record.request_id == context.request.request_id)


def _validation_records_for_request(context: _AnalysisContext):
    execution_ids = {record.execution_id for record in _execution_records_for_request(context)}
    return tuple(record for record in context.metadata_store.list_validation_records() if record.execution_id in execution_ids)


def _failure_codes(context: _AnalysisContext) -> tuple[str, ...]:
    codes: list[str] = [detail.reason for detail in context.result.failure_details]
    for detail in context.result.failure_details:
        if detail.target_ref is None:
            continue
        canonicalization = context.metadata_store.get_canonicalization_record(detail.target_ref)
        if canonicalization is not None:
            codes.extend(canonicalization.data_quality_result_ids)
            codes.extend(canonicalization.failures)
    return tuple(dict.fromkeys(codes))


def _observed_analysis(context: _AnalysisContext) -> dict[str, object]:
    return {
        "request_id": context.request.request_id,
        "run_status": context.result.run_status.value,
        "data_sufficiency_state": context.result.data_sufficiency_state.value if context.result.data_sufficiency_state else None,
        "metrics": {
            metric.metric_ref: {
                "metric_state": metric.metric_state.value,
                "executed_result_refs": metric.executed_result_refs,
                "validated_result_refs": metric.validated_result_refs,
                "admissible_evidence_refs": metric.admissible_evidence_refs,
                "failure_codes": _failure_codes(context),
            }
            for metric in context.result.metric_results
        },
    }


def _read_headers(path: Path) -> tuple[str, ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as file_obj:
        reader = csv.reader(file_obj)
        headers = next(reader)
    return tuple(headers)


def _materialize_setup_csv(path: Path, rows) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for row in rows:
            payload = row.model_dump() if hasattr(row, "model_dump") else dict(row)
            unknown = set(payload) - set(CSV_HEADERS)
            if unknown:
                raise ValueError(f"setup row contains unknown field(s): {', '.join(sorted(unknown))}")
            writer.writerow({key: payload.get(key, "") for key in CSV_HEADERS})
    return path


def _json_value(value):
    if isinstance(value, Decimal):
        return str(value)
    return value


class _isolated_runtime:
    def __init__(self, case_id: str, runtime_root: str | Path | None) -> None:
        self.case_id = case_id
        self.runtime_root = Path(runtime_root) if runtime_root is not None else None
        self._tempdir: tempfile.TemporaryDirectory[str] | None = None

    def __enter__(self) -> _Runtime:
        if self.runtime_root is None:
            self._tempdir = tempfile.TemporaryDirectory(prefix=f"{self.case_id}-")
            root = Path(self._tempdir.name)
        else:
            self.runtime_root.mkdir(parents=True, exist_ok=True)
            root = Path(tempfile.mkdtemp(prefix=f"{self.case_id}-", dir=self.runtime_root))
        artifact_store = ArtifactStore(root / "artifacts")
        metadata_store = MetadataStore(root / "metadata.sqlite")
        return _Runtime(artifact_store=artifact_store, metadata_store=metadata_store, root=root)

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._tempdir is not None:
            self._tempdir.cleanup()
