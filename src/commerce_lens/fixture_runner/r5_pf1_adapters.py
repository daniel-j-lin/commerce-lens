"""Real PF1 adapters that project existing deterministic CommerceLens authorities."""

from __future__ import annotations

import csv
import json
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Iterator

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
    PeriodDefinition,
    ScopeDefinition,
    SourceType,
)
from commerce_lens.contracts.evidence import ClaimCandidate, MetricReference
from commerce_lens.contracts.execution import ExecutedResult
from commerce_lens.contracts.requests import AnalysisRequest
from commerce_lens.contracts.results import AnalysisResult
from commerce_lens.contracts.validation import ValidatedResult, ValidationStatus
from commerce_lens.engine.execution import _revenue_change_result_fingerprint
from commerce_lens.engine.plan_builder import build_execution_plan
from commerce_lens.evidence.identifiers import generate_id
from commerce_lens.fixture_runner.r5_adapters import AdapterRegistration, AdapterRegistry
from commerce_lens.fixture_runner.r5_manifest import ActualProjection, ExecutionMode, LoadedR5Fixture
from commerce_lens.intake.registry import DatasetRegistry
from commerce_lens.metrics import METRIC_DEFINITION_VERSION, METRIC_REGISTRY_VERSION
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.persistence.retention import RetainedRunSession, RetentionStore
from commerce_lens.skill.integration import (
    PublicAnalysisIntent,
    PublicClaimIntent,
    PublicQuestionClass,
    PublicSourceSelection,
    run_public_analysis,
)
from commerce_lens.validation.validator import validate_executed_result


_R3_CURRENCY = "R3 v1.0 §21"
_R3_VALIDATION = "R3 v1.0 §24"
_R1_CLAIM = "R1 v1.0 §20"
_RETENTION_AUTHORITY = "Evidence Contract v1.0 §§45–46"
_INSUFFICIENT_WORDING = "Insufficient evidence to conclude why Revenue declined."


@dataclass(frozen=True)
class _AnalysisContext:
    result: AnalysisResult
    request: AnalysisRequest
    artifact_store: ArtifactStore
    metadata_store: MetadataStore


def build_r5_pf1_adapter_registry() -> AdapterRegistry:
    registry = AdapterRegistry()
    for registration in (
        AdapterRegistration(
            adapter_id="governed_descriptive_analysis",
            execution_mode=ExecutionMode.APPLICATION_SERVICE,
            capability_name="current_descriptive_evidence_chain",
            capability_version="application_service_v1",
            actual_output_producer="commerce_lens.application.analysis_service.run_analysis",
            producer=_produce_descriptive_evidence,
        ),
        AdapterRegistration(
            adapter_id="governed_currency_gate",
            execution_mode=ExecutionMode.APPLICATION_SERVICE,
            capability_name="canonical_currency_compatibility_gate",
            capability_version="canonical_mvp_v1",
            actual_output_producer="commerce_lens.application.analysis_service.run_analysis",
            producer=_produce_mixed_currency_block,
        ),
        AdapterRegistration(
            adapter_id="required_validation_boundary",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="deterministic_metric_validation",
            capability_version="p5_001_v1",
            actual_output_producer="commerce_lens.validation.validator.validate_executed_result",
            producer=_produce_required_validation_failure,
        ),
        AdapterRegistration(
            adapter_id="claim_decision_policy",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="current_claim_admissibility_policy",
            capability_version="p8_001_v1",
            actual_output_producer="commerce_lens.application.analysis_service.evaluate_claim",
            producer=_produce_diagnostic_claim_denial,
        ),
        AdapterRegistration(
            adapter_id="controlled_public_response_output",
            execution_mode=ExecutionMode.APPLICATION_SERVICE,
            capability_name="structured_controlled_refusal_output",
            capability_version="public_v0_1",
            actual_output_producer="commerce_lens.skill.public_response.PublicResponse.unsupported_conclusions",
            producer=_produce_insufficient_evidence_wording,
        ),
        AdapterRegistration(
            adapter_id="retention_integrity_verifier",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="retained_run_integrity_verification",
            capability_version="f2a_retention_v1",
            actual_output_producer="commerce_lens.persistence.retention.RetentionStore.verify_run",
            producer=_produce_retained_artifact_tamper,
        ),
        AdapterRegistration(
            adapter_id="diagnostic_precedence_projection",
            execution_mode=ExecutionMode.DEPENDENCY_GATE,
            capability_name="r2_validation_claim_precedence_projection",
            capability_version="not_implemented",
            actual_output_producer="unavailable:r2_validation_claim_precedence_projection",
            producer=None,
        ),
    ):
        registry.register(registration)
    return registry


def _produce_descriptive_evidence(fixture: LoadedR5Fixture) -> ActualProjection:
    with _analysis_runtime(fixture, ("revenue_change",)) as context:
        result = context.result
        validation_records = _validation_records(context)
        evidence_records = context.metadata_store.list_evidence_admissibility_records()
        material_path = (
            _stage("data_sufficiency", "reached", result.data_sufficiency_state.value),
            _stage("execution", "reached", result.run_status.value),
            _stage(
                "validation",
                "reached",
                "passed" if validation_records and all(item.status is ValidationStatus.PASSED for item in validation_records) else "failed",
            ),
            _stage(
                "evidence_admissibility",
                "reached",
                "passed" if evidence_records and all(item.status.value == "passed" for item in evidence_records) else "failed",
            ),
        )
        complete = (
            result.data_sufficiency_state.value == "sufficient"
            and result.run_status.value == "completed"
            and all(item["outcome"] == "passed" for item in material_path[2:])
        )
        return ActualProjection.model_validate(
            {
                "material_path": material_path,
                "chain_dispositions": {"main": "descriptive_evidence_eligible" if complete else "blocked"},
                "first_controlling_blocker": "NONE",
                "final_disposition": (
                    "DESCRIPTIVE_EVIDENCE_ELIGIBLE_FOR_OWN_GOVERNED_USE"
                    if complete
                    else "DESCRIPTIVE_EVIDENCE_CHAIN_INCOMPLETE"
                ),
                "trace_integrity_state": {
                    "validated_results_present": bool(result.validated_result_refs),
                    "admissible_evidence_present": bool(result.admissible_evidence_refs),
                },
                "artifact_evidence_refs": result.admissible_evidence_refs,
                "actual_output_producer": "commerce_lens.application.analysis_service.run_analysis",
            }
        )


def _produce_mixed_currency_block(fixture: LoadedR5Fixture) -> ActualProjection:
    with _analysis_runtime(fixture, ("revenue",)) as context:
        codes = _failure_codes(context)
        mixed = "canonical.currency.mixed" in codes
        if not mixed:
            return ActualProjection.model_validate(
                {
                    "material_path": (_stage("data_sufficiency", "reached", context.result.data_sufficiency_state.value),),
                    "chain_dispositions": {"main": "currency_gate_did_not_block"},
                    "first_controlling_blocker": "NONE",
                    "final_disposition": "CURRENCY_GATE_DID_NOT_BLOCK",
                    "trace_integrity_state": {"failure_codes": codes},
                    "actual_output_producer": "commerce_lens.application.analysis_service.run_analysis",
                }
            )
        return ActualProjection.model_validate(
            {
                "material_path": (
                    _stage(
                        "data_sufficiency",
                        "blocked",
                        "MIXED_CURRENCY__TEST_NOT_ELIGIBLE",
                        reason="canonical.currency.mixed",
                        authority=_R3_CURRENCY,
                    ),
                    _not_reached("execution", "data_sufficiency"),
                    _not_reached("validation", "data_sufficiency"),
                    _not_reached("evidence_admissibility", "data_sufficiency"),
                ),
                "chain_dispositions": {"main": "test_not_eligible"},
                "first_controlling_blocker": _blocker(
                    "currency_compatibility", "data_sufficiency", "canonical.currency.mixed", _R3_CURRENCY
                ),
                "final_disposition": "MIXED_CURRENCY__TEST_NOT_ELIGIBLE",
                "trace_integrity_state": {
                    "failure_code": "canonical.currency.mixed",
                    "executed_results": len(context.result.executed_result_refs),
                },
                "actual_output_producer": "commerce_lens.application.analysis_service.run_analysis",
            }
        )


def _produce_required_validation_failure(fixture: LoadedR5Fixture) -> ActualProjection:
    hostile = _json_input(fixture, "hostile_result")
    with _analysis_runtime(fixture, ("revenue_change",)) as context:
        submitted = Decimal(str(hostile["submitted_value"]))
        validation = _validate_hostile_revenue_change(context, submitted)
        record = validation.validation_record
        if record.status is not ValidationStatus.FAILED:
            return ActualProjection.model_validate(
                {
                    "material_path": (_stage("validation", "reached", record.status.value),),
                    "chain_dispositions": {"main": "validation_passed"},
                    "first_controlling_blocker": "NONE",
                    "final_disposition": "VALIDATION_PASSED",
                    "trace_integrity_state": {"validation_status": record.status.value},
                    "actual_output_producer": "commerce_lens.validation.validator.validate_executed_result",
                }
            )
        reason = record.failure_code or "required_validation_failed"
        return ActualProjection.model_validate(
            {
                "material_path": (
                    _stage("data_sufficiency", "reached", "sufficient"),
                    _stage("execution", "reached", "hostile_result_submitted"),
                    _stage(
                        "validation",
                        "blocked",
                        "REQUIRED_VALIDATION_FAILED__TEST_NOT_ELIGIBLE",
                        reason=reason,
                        authority=_R3_VALIDATION,
                    ),
                    _not_reached("evidence_admissibility", "validation"),
                    _not_reached("claim_decision", "validation"),
                ),
                "chain_dispositions": {"main": "test_not_eligible"},
                "first_controlling_blocker": _blocker(
                    "required_validation", "validation", reason, _R3_VALIDATION
                ),
                "final_disposition": "REQUIRED_VALIDATION_FAILED__TEST_NOT_ELIGIBLE",
                "trace_integrity_state": {
                    "validation_status": record.status.value,
                    "failure_code": record.failure_code,
                    "validated_result_authorized": validation.validated_result is not None,
                },
                "actual_output_producer": "commerce_lens.validation.validator.validate_executed_result",
            }
        )


def _produce_diagnostic_claim_denial(fixture: LoadedR5Fixture) -> ActualProjection:
    candidate = ClaimCandidate.model_validate(_json_input(fixture, "claim_candidate"))
    with tempfile.TemporaryDirectory(prefix="r5-pf1-claim-") as temporary:
        root = Path(temporary)
        decision = evaluate_claim(
            candidate,
            artifact_store=ArtifactStore(root / "artifacts"),
            metadata_store=MetadataStore(root / "metadata.sqlite"),
        )
    if decision.claim_state is not ClaimState.INADMISSIBLE:
        return ActualProjection.model_validate(
            {
                "material_path": (_stage("claim_decision", "reached", decision.claim_state.value),),
                "chain_dispositions": {"main": "claim_authorized"},
                "first_controlling_blocker": "NONE",
                "final_disposition": "CLAIM_AUTHORIZED",
                "trace_integrity_state": {"policy_version": decision.policy_version},
                "actual_output_producer": "commerce_lens.application.analysis_service.evaluate_claim",
            }
        )
    reason = decision.failure_code or "claim_inadmissible"
    return ActualProjection.model_validate(
        {
            "material_path": (
                _stage(
                    "claim_decision",
                    "blocked",
                    "CLAIM_PROHIBITED__UNSUPPORTED_CLAIM_TYPE",
                    reason=reason,
                    authority=_R1_CLAIM,
                ),
            ),
            "chain_dispositions": {"main": "claim_prohibited"},
            "first_controlling_blocker": _blocker(
                "requested_claim_class_restriction", "claim_decision", reason, _R1_CLAIM
            ),
            "final_disposition": "CLAIM_PROHIBITED__UNSUPPORTED_CLAIM_TYPE",
            "trace_integrity_state": {
                "claim_state": decision.claim_state.value,
                "failure_code": decision.failure_code,
                "policy_version": decision.policy_version,
            },
            "artifact_evidence_refs": ((decision.artifact_ref.artifact_id,) if decision.artifact_ref else ()),
            "actual_output_producer": "commerce_lens.application.analysis_service.evaluate_claim",
        }
    )


def _produce_insufficient_evidence_wording(fixture: LoadedR5Fixture) -> ActualProjection:
    with _public_runtime(fixture, diagnostic=True) as outcome:
        controlled_output = outcome.response.unsupported_conclusions
        diagnostic_decision = next(
            (item for item in outcome.claim_decisions if item.failure_code == "unsupported_claim_type"),
            None,
        )
        exact = diagnostic_decision is not None and controlled_output == (_INSUFFICIENT_WORDING,)
        classification = "PERMITTED_INSUFFICIENCY_WORDING" if exact else "UNRECOGNIZED_CONTROLLED_WORDING"
        projected_text: object = controlled_output[0] if len(controlled_output) == 1 else controlled_output
        return ActualProjection.model_validate(
            {
                "material_path": (
                    _stage(
                        "claim_decision",
                        "reached",
                        {
                            "claim_state": diagnostic_decision.claim_state.value if diagnostic_decision else None,
                            "failure_code": diagnostic_decision.failure_code if diagnostic_decision else None,
                        },
                    ),
                    _stage(
                        "rendering",
                        "reached",
                        {"classification": classification, "text": projected_text},
                    ),
                ),
                "chain_dispositions": {"main": "controlled_refusal_rendered" if exact else "wording_unrecognized"},
                "first_controlling_blocker": "NONE",
                "final_disposition": classification,
                "trace_integrity_state": {"controlled_exact_text_present": exact},
                "actual_output_producer": (
                    "commerce_lens.skill.public_response.PublicResponse.unsupported_conclusions"
                ),
            }
        )


def _produce_retained_artifact_tamper(fixture: LoadedR5Fixture) -> ActualProjection:
    with tempfile.TemporaryDirectory(prefix="r5-pf1-retention-") as temporary:
        root = Path(temporary)
        session = RetainedRunSession.begin(root / "retention")
        source = _input_path(fixture, "orders")
        intent = _public_intent(fixture, source, diagnostic=False)
        authority = _fixture_authority(intent.source, session.artifact_store, fixture)
        outcome = run_public_analysis(
            intent,
            artifact_store=session.artifact_store,
            metadata_store=session.metadata_store,
            run_id=session.run_id,
            retention_session=session,
            **authority,
        )
        manifest = session.finalize(outcome, public_payload={"rendered_text": outcome.response.render_text()})
        retained = session.artifact_store.safe_path(manifest.analysis_result_artifact.path)
        retained.write_text("tampered\n", encoding="utf-8")
        checks, errors = RetentionStore(root / "retention").verify_run(session.run_id)
        detected = checks.get("artifact_hashes") is False and any("hash mismatch" in item for item in errors)
        if not detected:
            return ActualProjection.model_validate(
                {
                    "material_path": (_stage("artifact_integrity", "reached", "tamper_not_detected"),),
                    "chain_dispositions": {"main": "integrity_unverified"},
                    "first_controlling_blocker": "NONE",
                    "final_disposition": "TAMPER_NOT_DETECTED",
                    "trace_integrity_state": {"artifact_hashes": checks.get("artifact_hashes")},
                    "actual_output_producer": "commerce_lens.persistence.retention.RetentionStore.verify_run",
                }
            )
        return ActualProjection.model_validate(
            {
                "material_path": (
                    _stage(
                        "artifact_integrity",
                        "blocked",
                        "ARTIFACT_INTEGRITY_FAILURE__AFFECTED_AUTHORITY_BLOCKED",
                        reason="retained_artifact_hash_mismatch",
                        authority=_RETENTION_AUTHORITY,
                    ),
                ),
                "chain_dispositions": {"main": "affected_authority_blocked"},
                "first_controlling_blocker": _blocker(
                    "retained_artifact_integrity",
                    "artifact_integrity",
                    "retained_artifact_hash_mismatch",
                    _RETENTION_AUTHORITY,
                ),
                "final_disposition": "ARTIFACT_INTEGRITY_FAILURE__AFFECTED_AUTHORITY_BLOCKED",
                "trace_integrity_state": {"artifact_hashes": False},
                "artifact_evidence_refs": (manifest.analysis_result_artifact.artifact_id,),
                "actual_output_producer": "commerce_lens.persistence.retention.RetentionStore.verify_run",
            }
        )


@contextmanager
def _analysis_runtime(fixture: LoadedR5Fixture, metrics: tuple[str, ...]) -> Iterator[_AnalysisContext]:
    with tempfile.TemporaryDirectory(prefix="r5-pf1-analysis-") as temporary:
        root = Path(temporary)
        artifact_store = ArtifactStore(root / "artifacts")
        metadata_store = MetadataStore(root / "metadata.sqlite")
        source = _input_path(fixture, "orders")
        dataset = DatasetRegistry(artifact_store).register_source(source, SourceType.CSV)
        request = _analysis_request(fixture, dataset.dataset_id, metrics)
        result = run_analysis(
            request,
            canonicalization_request=_canonicalization_request(dataset.dataset_id, source),
            artifact_store=artifact_store,
            metadata_store=metadata_store,
            source_path=source,
            source_type=SourceType.CSV,
            available_evidence=_available_evidence(request),
            period_coverage_evidence=_coverage(request),
        )
        yield _AnalysisContext(result, request, artifact_store, metadata_store)


@contextmanager
def _public_runtime(fixture: LoadedR5Fixture, *, diagnostic: bool) -> Iterator[object]:
    with tempfile.TemporaryDirectory(prefix="r5-pf1-public-") as temporary:
        root = Path(temporary)
        artifact_store = ArtifactStore(root / "artifacts")
        metadata_store = MetadataStore(root / "metadata.sqlite")
        source = _input_path(fixture, "orders")
        intent = _public_intent(fixture, source, diagnostic=diagnostic)
        outcome = run_public_analysis(
            intent,
            artifact_store=artifact_store,
            metadata_store=metadata_store,
            **_fixture_authority(intent.source, artifact_store, fixture),
        )
        yield outcome


def _public_intent(fixture: LoadedR5Fixture, source: Path, *, diagnostic: bool) -> PublicAnalysisIntent:
    baseline, comparison = _periods(fixture)
    return PublicAnalysisIntent(
        question_class=(
            PublicQuestionClass.DIAGNOSTIC_REVENUE_DROP if diagnostic else PublicQuestionClass.REVENUE_CHANGE
        ),
        metric_id="revenue_change",
        baseline_period=baseline,
        comparison_period=comparison,
        source=PublicSourceSelection(source, SourceType.CSV),
        original_question_text=fixture.manifest.context.question_or_proposition,
        claim_intents=(
            (
                PublicClaimIntent(ClaimType.DESCRIPTIVE, "Revenue Change descriptive portion"),
                PublicClaimIntent(ClaimType.DIAGNOSTIC, "Diagnostic explanation"),
            )
            if diagnostic
            else (PublicClaimIntent(),)
        ),
    )


def _fixture_authority(source: PublicSourceSelection, artifact_store: ArtifactStore, fixture: LoadedR5Fixture) -> dict:
    dataset = DatasetRegistry(artifact_store).register_source(source.source_path, source.source_type)
    baseline, comparison = _periods(fixture)
    return {
        "available_evidence": (
            AvailableEvidence(
                evidence_id=f"{fixture.manifest.fixture_id.lower()}_source_authority",
                description="Frozen R5 synthetic fixture declares its tiny export complete",
                source_ref=dataset.dataset_id,
                satisfies_requirement_ids=("req_global", "req_revenue_change"),
            ),
        ),
        "period_coverage_evidence": (
            PeriodCoverageEvidence(
                coverage_ref_id=f"{fixture.manifest.fixture_id.lower()}_coverage",
                dataset_ref_id=dataset.dataset_id,
                observed_start_date=baseline.start_date,
                observed_end_date=comparison.end_date,
                date_convention_ref=baseline.date_convention_ref,
                governing_note_ref="frozen_r5_static_synthetic_fixture",
            ),
        ),
    }


def _analysis_request(fixture: LoadedR5Fixture, dataset_id: str, metrics: tuple[str, ...]) -> AnalysisRequest:
    baseline, comparison = _periods(fixture)
    return AnalysisRequest(
        canonical_business_question_id="r5_pf1_descriptive_revenue_change",
        original_question_text=fixture.manifest.context.question_or_proposition or fixture.manifest.purpose,
        metrics=tuple(MetricReference(metric_id=item, definition_version=METRIC_DEFINITION_VERSION) for item in metrics),
        baseline_period=baseline,
        comparison_period=comparison,
        scope=ScopeDefinition(scope_id="all_eligible"),
        grouping=GroupingDimension.NONE,
        required_evidence=tuple(
            [EvidenceRequirement(requirement_id="req_global", description="global source authority")]
            + [
                EvidenceRequirement(requirement_id=f"req_{item}", description=f"{item} authority", metric_ref=item)
                for item in metrics
            ]
        ),
        dataset_ref_id=dataset_id,
        canonical_schema_version="canonical_mvp_v1",
        metric_registry_version=METRIC_REGISTRY_VERSION,
    )


def _periods(fixture: LoadedR5Fixture) -> tuple[PeriodDefinition, PeriodDefinition]:
    if len(fixture.manifest.context.periods) != 2:
        raise ValueError("PF1 governed analysis fixtures require exactly baseline and comparison periods")
    values = tuple(
        PeriodDefinition(
            period_id=item.period_id,
            label=item.label,
            start_date=date.fromisoformat(item.start_date),
            end_date=date.fromisoformat(item.end_date),
            date_convention_ref=item.date_convention_ref,
        )
        for item in fixture.manifest.context.periods
    )
    return values[0], values[1]


def _canonicalization_request(dataset_id: str, source: Path) -> CanonicalizationRequest:
    with source.open("r", encoding="utf-8-sig", newline="") as file_obj:
        headers = tuple(next(csv.reader(file_obj)))
    return CanonicalizationRequest(
        source_dataset_id=dataset_id,
        mapping=identity_mapping(headers, require_eligibility=True),
        eligibility_mode=EligibilityMode.EXPLICIT_STATUS_MAPPING,
        eligibility_value_mapping=(
            EligibilityValueMapping(source_value="paid", normalized_status=EligibilityState.ELIGIBLE),
            EligibilityValueMapping(source_value="cancelled", normalized_status=EligibilityState.EXCLUDED),
        ),
    )


def _available_evidence(request: AnalysisRequest) -> tuple[AvailableEvidence, ...]:
    return (
        AvailableEvidence(
            evidence_id="r5_pf1_static_source",
            description="Frozen R5 static synthetic source and reviewed coverage",
            source_ref=request.dataset_ref_id,
            satisfies_requirement_ids=tuple(item.requirement_id for item in request.required_evidence),
        ),
    )


def _coverage(request: AnalysisRequest) -> tuple[PeriodCoverageEvidence, ...]:
    return (
        PeriodCoverageEvidence(
            coverage_ref_id="r5_pf1_reviewed_coverage",
            dataset_ref_id=request.dataset_ref_id,
            observed_start_date=request.baseline_period.start_date,
            observed_end_date=request.comparison_period.end_date,
            date_convention_ref=request.baseline_period.date_convention_ref,
            governing_note_ref="frozen_r5_static_synthetic_fixture",
        ),
    )


def _validate_hostile_revenue_change(context: _AnalysisContext, submitted: Decimal):
    sufficiency = context.metadata_store.get_data_sufficiency_result(
        context.result.data_sufficiency_ref, context.artifact_store
    )
    if sufficiency is None or sufficiency.canonical_dataset_ref_id is None:
        raise ValueError("validation fixture setup lacks sufficiency/canonical authority")
    canonical = context.metadata_store.get_canonical_dataset(sufficiency.canonical_dataset_ref_id)
    if canonical is None:
        raise ValueError("validation fixture setup lacks canonical authority")
    plan = build_execution_plan(context.request, sufficiency)
    original_record = next(
        item for item in context.metadata_store.list_execution_records() if item.metric_refs == ("revenue_change",)
    )
    original_result = _executed_result(context, original_record)
    execution_id = generate_id("exec_r5_pf1")
    result_id = generate_id("exres_r5_pf1")
    hostile = original_result.model_copy(
        update={"execution_id": execution_id, "result_id": result_id, "value": submitted}
    )
    node = next(item for item in plan.ordered_metrics if item.node_id == original_record.plan_node_id)
    populations = {item.population_id: item for item in plan.population_definitions}
    by_role = {populations[item].period_role.value: populations[item] for item in node.population_refs}
    baseline_record = _execution_record(context, "revenue", "baseline")
    comparison_record = _execution_record(context, "revenue", "comparison")
    hostile = hostile.model_copy(
        update={
            "result_fingerprint": _revenue_change_result_fingerprint(
                node=node,
                baseline_population=by_role["baseline"],
                comparison_population=by_role["comparison"],
                canonical_dataset=canonical,
                value=hostile.value,
                currency=original_record.resolved_currency,
                baseline_result=_executed_result(context, baseline_record),
                comparison_result=_executed_result(context, comparison_record),
            )
        }
    )
    artifact = context.artifact_store.write_json_artifact(
        Path("runs") / execution_id / "results" / f"{result_id}.json", hostile.model_dump(mode="json")
    )
    context.metadata_store.insert_artifact_reference(artifact)
    record = original_record.model_copy(
        update={"execution_id": execution_id, "result_ref": result_id, "output_artifacts": (artifact,)}
    )
    context.metadata_store.insert_execution_record(record)
    dependencies = (
        _validated_result(context, "revenue", "baseline"),
        _validated_result(context, "revenue", "comparison"),
    )
    return validate_executed_result(
        execution_id=execution_id,
        result_id=result_id,
        plan=plan,
        canonical_dataset=canonical,
        artifact_store=context.artifact_store,
        metadata_store=context.metadata_store,
        dependency_validated_results=dependencies,
    )


def _execution_record(context: _AnalysisContext, metric: str, period: str):
    return next(
        item
        for item in context.metadata_store.list_execution_records()
        if item.metric_refs == (metric,) and item.period_refs == (period,)
    )


def _executed_result(context: _AnalysisContext, record) -> ExecutedResult:
    return ExecutedResult.model_validate_json(
        context.artifact_store.safe_path(record.output_artifacts[0].path).read_text(encoding="utf-8")
    )


def _validated_result(context: _AnalysisContext, metric: str, period: str) -> ValidatedResult:
    for record in context.metadata_store.list_validation_records():
        if record.validated_result_artifact_ref is None:
            continue
        result = ValidatedResult.model_validate_json(
            context.artifact_store.safe_path(record.validated_result_artifact_ref.path).read_text(encoding="utf-8")
        )
        if result.metric_ref == metric and result.period_ref == period:
            return result
    raise ValueError(f"missing validated {metric}/{period} dependency")


def _validation_records(context: _AnalysisContext):
    execution_ids = {
        item.execution_id
        for item in context.metadata_store.list_execution_records()
        if item.request_id == context.request.request_id
    }
    return tuple(
        item for item in context.metadata_store.list_validation_records() if item.execution_id in execution_ids
    )


def _failure_codes(context: _AnalysisContext) -> tuple[str, ...]:
    codes = [item.reason for item in context.result.failure_details]
    for detail in context.result.failure_details:
        if detail.target_ref is None:
            continue
        record = context.metadata_store.get_canonicalization_record(detail.target_ref)
        if record is not None:
            codes.extend(record.data_quality_result_ids)
            codes.extend(record.failures)
    return tuple(dict.fromkeys(codes))


def _input_path(fixture: LoadedR5Fixture, role: str) -> Path:
    for spec, path in zip(fixture.manifest.inputs, fixture.input_paths, strict=True):
        if spec.role == role:
            return path
    raise ValueError(f"fixture input role is missing: {role}")


def _json_input(fixture: LoadedR5Fixture, role: str) -> dict:
    payload = json.loads(_input_path(fixture, role).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"fixture JSON input must be an object: {role}")
    return payload


def _stage(stage: str, reachability: str, outcome, *, reason: str | None = None, authority: str | None = None) -> dict:
    payload = {"stage": stage, "reachability": reachability, "outcome": outcome}
    if reason is not None:
        payload["controlling_reason"] = reason
    if authority is not None:
        payload["authority_ref"] = authority
    return payload


def _not_reached(stage: str, due_to: str) -> dict:
    return {"stage": stage, "reachability": "not_reached", "not_reached_due_to": due_to}


def _blocker(blocker_id: str, stage: str, reason: str, authority: str) -> dict:
    return {
        "blocker_id": blocker_id,
        "stage": stage,
        "reason": reason,
        "authority_ref": authority,
    }
