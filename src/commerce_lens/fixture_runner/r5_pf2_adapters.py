"""PF2 adapters over existing deterministic CommerceLens production authorities."""

from __future__ import annotations

import json
import sqlite3
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path

from commerce_lens.application import evaluate_claim
from commerce_lens.contracts.common import ClaimState, ClaimType, SourceType
from commerce_lens.contracts.evidence import ClaimCandidate
from commerce_lens.evidence.admissibility import evaluate_evidence_admissibility
from commerce_lens.evidence.claim_admissibility import (
    CLAIM_POLICY_VERSION,
    ClaimAdmissibilityError,
    evaluate_claim_admissibility,
    verify_claim_decision_artifact,
)
from commerce_lens.evidence.identifiers import canonical_json_bytes, canonical_json_fingerprint, sha256_file, stable_content_id
from commerce_lens.fixture_runner.r5_adapters import AdapterRegistration, AdapterRegistry
from commerce_lens.fixture_runner.r5_manifest import ActualProjection, ExecutionMode, LoadedR5Fixture
from commerce_lens.fixture_runner.r5_pf1_adapters import (
    _analysis_runtime,
    _analysis_request,
    _available_evidence,
    _blocker,
    _canonicalization_request,
    _coverage,
    _failure_codes,
    _fixture_authority,
    _input_path,
    _json_input,
    _not_reached,
    _public_intent,
    _stage,
    _validated_result,
    build_r5_pf1_adapter_registry,
)
from commerce_lens.intake.registry import DatasetRegistry
from commerce_lens.metrics import METRIC_DEFINITION_VERSION, METRIC_REGISTRY_VERSION
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.persistence.retention import RetainedRunSession, RetentionStore
from commerce_lens.skill.integration import run_public_analysis


_R3_EVIDENCE = "R3 v1.0 §§12–30"
_R3_ADMISSION = "R3 v1.0 §26"
_R1_CLAIM = "R1 v1.0 §20"
_R2_CLAIM = "R2 v1.0 §§18, 27"
_VERSION_AUTHORITY = "Architecture v1.0 §19"
_PROVENANCE_AUTHORITY = "Evidence Contract v1.0 §§45–46"
_PREC_AUTHORITY = "R1 v1.0 §19.2"


def build_r5_pf2_adapter_registry() -> AdapterRegistry:
    """Return the PF1 registry extended only with owner-approved PF2 capabilities."""
    registry = build_r5_pf1_adapter_registry()
    for registration in (
        AdapterRegistration(
            adapter_id="data_sufficiency_boundary",
            execution_mode=ExecutionMode.APPLICATION_SERVICE,
            capability_name="current_data_sufficiency_authority",
            capability_version="p2_001_v1",
            actual_output_producer="commerce_lens.application.analysis_service.run_analysis",
            producer=_produce_data_sufficiency_boundary,
        ),
        AdapterRegistration(
            adapter_id="evidence_admissibility_boundary",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="current_evidence_admissibility_authority",
            capability_version="p6_001_v1",
            actual_output_producer="commerce_lens.evidence.admissibility.evaluate_evidence_admissibility",
            producer=_produce_evidence_admissibility_boundary,
        ),
        AdapterRegistration(
            adapter_id="canonical_quality_boundary",
            execution_mode=ExecutionMode.APPLICATION_SERVICE,
            capability_name="canonical_currency_quality_authority",
            capability_version="canonical_mvp_v1",
            actual_output_producer="commerce_lens.application.analysis_service.run_analysis",
            producer=_produce_canonical_quality_boundary,
        ),
        AdapterRegistration(
            adapter_id="unsupported_claim_policy",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="current_claim_class_restriction",
            capability_version="p8_001_v1",
            actual_output_producer="commerce_lens.application.analysis_service.evaluate_claim",
            producer=_produce_unsupported_claim_policy,
        ),
        AdapterRegistration(
            adapter_id="public_claim_authority_boundary",
            execution_mode=ExecutionMode.APPLICATION_SERVICE,
            capability_name="public_claim_decision_render_gate",
            capability_version="public_v0_1",
            actual_output_producer="commerce_lens.skill.integration.run_public_analysis",
            producer=_produce_public_claim_authority_boundary,
        ),
        AdapterRegistration(
            adapter_id="claim_binding_verifier",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="authoritative_claim_decision_binding_verification",
            capability_version="p8_001_v1",
            actual_output_producer="commerce_lens.evidence.claim_admissibility.verify_claim_decision_artifact",
            producer=_produce_claim_binding_verification,
        ),
        AdapterRegistration(
            adapter_id="exact_version_binding_verifier",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="current_exact_version_binding_authority",
            capability_version="current_authority_v1",
            actual_output_producer="commerce_lens.application.analysis_service.run_analysis",
            producer=_produce_exact_version_binding,
        ),
        AdapterRegistration(
            adapter_id="claim_policy_version_verifier",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="current_claim_policy_version_authority",
            capability_version="p8_001_v1",
            actual_output_producer="commerce_lens.evidence.claim_admissibility.evaluate_claim_admissibility",
            producer=_produce_claim_policy_version_binding,
        ),
        AdapterRegistration(
            adapter_id="retention_state_verifier",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="retained_run_integrity_and_history_verification",
            capability_version="f2a_retention_v1",
            actual_output_producer="commerce_lens.persistence.retention.RetentionStore.verify_run",
            producer=_produce_retention_state,
        ),
        AdapterRegistration(
            adapter_id="retention_integrity_state_observer",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="retained_run_integrity_and_state_observation",
            capability_version="f2a_retention_v1",
            actual_output_producer=(
                "commerce_lens.persistence.retention.RetentionStore.verify_run"
                "+retained_filesystem_state_observation"
            ),
            producer=_produce_retention_integrity_state,
        ),
        AdapterRegistration(
            adapter_id="provenance_authority_verifier",
            execution_mode=ExecutionMode.COMPONENT_BOUNDARY,
            capability_name="persisted_evidence_and_claim_lineage_authentication",
            capability_version="p8_001_v1",
            actual_output_producer="commerce_lens.application.analysis_service.evaluate_claim",
            producer=_produce_provenance_authority,
        ),
    ):
        registry.register(registration)
    return registry


def _produce_data_sufficiency_boundary(fixture: LoadedR5Fixture) -> ActualProjection:
    scenario = _json_input(fixture, "scenario")["scenario"]
    with tempfile.TemporaryDirectory(prefix="r5-pf2-sufficiency-") as temporary:
        root = Path(temporary)
        artifact_store = ArtifactStore(root / "artifacts")
        metadata_store = MetadataStore(root / "metadata.sqlite")
        source = _input_path(fixture, "orders")
        dataset = DatasetRegistry(artifact_store).register_source(source, SourceType.CSV)
        request = _analysis_request(fixture, dataset.dataset_id, ("revenue_change",))
        available = _available_evidence(request)
        coverage = _coverage(request)
        if scenario == "missing_required_evidence":
            available = ()
        elif scenario == "incomplete_coverage":
            coverage = (
                coverage[0].model_copy(
                    update={"observed_end_date": request.comparison_period.end_date.replace(day=30)}
                ),
            )
        elif scenario == "unknown_coverage":
            coverage = ()
        else:
            raise ValueError(f"unsupported Data Sufficiency scenario: {scenario}")
        from commerce_lens.application import run_analysis

        result = run_analysis(
            request,
            canonicalization_request=_canonicalization_request(dataset.dataset_id, source),
            artifact_store=artifact_store,
            metadata_store=metadata_store,
            source_path=source,
            source_type=SourceType.CSV,
            available_evidence=available,
            period_coverage_evidence=coverage,
        )
        reasons = tuple(item.reason for item in result.failure_details)
    if scenario == "missing_required_evidence":
        observed = next((item for item in reasons if item.startswith("required evidence is missing:")), None)
        stage = "required_evidence"
        blocker_id = "available_evidence_mapping"
        final = "MISSING_INTERNAL_EVIDENCE__TEST_NOT_ELIGIBLE"
        reason = "required_evidence_missing"
    elif scenario == "incomplete_coverage":
        observed = next((item for item in reasons if "comparison period" in item), None)
        stage = "data_sufficiency"
        blocker_id = "coverage_completeness"
        final = "INCOMPLETE_COVERAGE__TEST_NOT_ELIGIBLE"
        reason = "explicit_coverage_incomplete"
    else:
        observed = next((item for item in reasons if "coverage evidence" in item), None)
        stage = "data_sufficiency"
        blocker_id = "coverage_completeness"
        final = "UNKNOWN_COVERAGE__TEST_NOT_ELIGIBLE"
        reason = "qualifying_coverage_authority_absent"
    detected = observed is not None
    if not detected:
        return _unexpected("commerce_lens.application.analysis_service.run_analysis", "SUFFICIENCY_BLOCKER_NOT_OBSERVED", reasons)
    path = (
        _stage(stage, "blocked", final, reason=reason, authority=_R3_EVIDENCE),
        _not_reached("execution", stage),
        _not_reached("validation", stage),
        _not_reached("evidence_admissibility", stage),
    )
    return _projection(
        producer="commerce_lens.application.analysis_service.run_analysis",
        path=path,
        disposition=final,
        blocker=_blocker(blocker_id, stage, reason, _R3_EVIDENCE),
        chain="test_not_eligible",
        trace={"blocker_detected": True, "sufficiency_state": result.data_sufficiency_state.value},
    )


def _produce_evidence_admissibility_boundary(fixture: LoadedR5Fixture) -> ActualProjection:
    scenario = _json_input(fixture, "scenario")["scenario"]
    with _analysis_runtime(fixture, ("revenue_change",)) as context:
        result = _validated_result(context, "revenue_change", "comparison")
        sufficiency_id = context.result.data_sufficiency_ref
        if sufficiency_id is None:
            raise ValueError("valid setup lacks DataSufficiencyResult authority")
        claim_type = ClaimType.DESCRIPTIVE
        if scenario in {"diagnostic_use", "precedence_inadmissible"}:
            claim_type = ClaimType.DIAGNOSTIC
        elif scenario == "period_mismatch":
            _replace_execution_record(context.metadata_store, result.execution_id, period_refs=["outside"])
        elif scenario == "population_mismatch":
            _replace_execution_record(context.metadata_store, result.execution_id, population_refs=["pop_wrong"])
        elif scenario == "metric_version_mismatch":
            _replace_request_metric_version(context, "metric_dictionary_wrong")
        elif scenario == "provenance_missing":
            with sqlite3.connect(context.metadata_store.db_path) as connection:
                connection.execute("DELETE FROM execution_records WHERE execution_id = ?", (result.execution_id,))
        else:
            raise ValueError(f"unsupported Evidence admissibility scenario: {scenario}")
        outcome = evaluate_evidence_admissibility(
            request_id=context.request.request_id,
            sufficiency_id=sufficiency_id,
            validated_result_id=result.validated_result_id,
            claim_type=claim_type,
            artifact_store=context.artifact_store,
            metadata_store=context.metadata_store,
        )
        record = outcome.admissibility_record
    if record.status.value != "failed" or record.failure_code is None:
        return _unexpected("commerce_lens.evidence.admissibility.evaluate_evidence_admissibility", "EVIDENCE_WAS_NOT_REJECTED", record.status.value)
    profiles = {
        "period_mismatch": ("TEMPORALLY_MISALIGNED__TEST_NOT_ELIGIBLE", "temporal_alignment", "period_mismatch", _R3_EVIDENCE),
        "population_mismatch": ("POPULATION_MISMATCH__TEST_NOT_ELIGIBLE", "population_alignment", "population_mismatch", _R3_EVIDENCE),
        "metric_version_mismatch": (
            "METRIC_VERSION_MISMATCH__AFFECTED_CHAIN_BLOCKED"
            if fixture.manifest.family.value == "VERSION"
            else "METRIC_VERSION_INCOMPATIBLE__TEST_NOT_ELIGIBLE",
            "metric_version_binding" if fixture.manifest.family.value == "VERSION" else "metric_compatibility",
            "metric_definition_mismatch",
            _VERSION_AUTHORITY if fixture.manifest.family.value == "VERSION" else _R3_EVIDENCE,
        ),
        "provenance_missing": ("PROVENANCE_INCOMPLETE__TEST_NOT_ELIGIBLE", "provenance", "execution_record_lineage_missing", _PROVENANCE_AUTHORITY),
        "diagnostic_use": (
            "PRESENT_BUT_INADMISSIBLE__TEST_NOT_ELIGIBLE" if fixture.manifest.family.value == "EVID" else "AUTHENTICATED_CANDIDATE_ONLY__NOT_DIAGNOSTIC_INPUT_ADMISSIBLE",
            "evidence_admissibility" if fixture.manifest.family.value == "EVID" else "diagnostic_intended_use_admission",
            "unsupported_claim_type_for_p6_001",
            _R3_ADMISSION,
        ),
        "precedence_inadmissible": ("EVIDENCE_INADMISSIBLE__ANALYTICAL_SUPPORT_NOT_REACHED", "evidence_admissibility", "unsupported_claim_type_for_p6_001", _PREC_AUTHORITY),
    }
    disposition, blocker_id, required_code, authority = profiles[scenario]
    if record.failure_code != required_code:
        return _unexpected("commerce_lens.evidence.admissibility.evaluate_evidence_admissibility", "UNEXPECTED_EVIDENCE_FAILURE", record.failure_code)
    tail = (
        (_not_reached("analytical_outcome", "evidence_admissibility"),)
        if scenario == "precedence_inadmissible"
        else (_not_reached("claim_decision", "evidence_admissibility"),)
    )
    return _projection(
        producer="commerce_lens.evidence.admissibility.evaluate_evidence_admissibility",
        path=(
            _stage("validation", "reached", "passed"),
            _stage("evidence_admissibility", "blocked", disposition, reason=record.failure_code, authority=authority),
            *tail,
        ),
        disposition=disposition,
        blocker=_blocker(blocker_id, "evidence_admissibility", record.failure_code, authority),
        chain=(
            "analytical_support_unreachable"
            if scenario == "precedence_inadmissible"
            else "affected_chain_blocked"
            if fixture.manifest.family.value == "VERSION"
            else "test_not_eligible"
        ),
        trace={"status": record.status.value, "failure_code": record.failure_code},
    )


def _produce_canonical_quality_boundary(fixture: LoadedR5Fixture) -> ActualProjection:
    with _analysis_runtime(fixture, ("revenue",)) as context:
        codes = _failure_codes(context)
        detected = "canonical.currency.missing" in codes
        result = context.result
    if not detected:
        return _unexpected("commerce_lens.application.analysis_service.run_analysis", "UNKNOWN_CURRENCY_NOT_DETECTED", codes)
    return _projection(
        producer="commerce_lens.application.analysis_service.run_analysis",
        path=(
            _stage("data_sufficiency", "blocked", "UNKNOWN_CURRENCY__TEST_NOT_ELIGIBLE", reason="canonical.currency.missing", authority="R3 v1.0 §21"),
            _not_reached("execution", "data_sufficiency"),
            _not_reached("validation", "data_sufficiency"),
            _not_reached("evidence_admissibility", "data_sufficiency"),
        ),
        disposition="UNKNOWN_CURRENCY__TEST_NOT_ELIGIBLE",
        blocker=_blocker("currency_compatibility", "data_sufficiency", "canonical.currency.missing", "R3 v1.0 §21"),
        chain="test_not_eligible",
        trace={"failure_code": "canonical.currency.missing", "executed_results": len(result.executed_result_refs)},
    )


def _produce_unsupported_claim_policy(fixture: LoadedR5Fixture) -> ActualProjection:
    candidate = ClaimCandidate.model_validate(_json_input(fixture, "claim_candidate"))
    with tempfile.TemporaryDirectory(prefix="r5-pf2-claim-") as temporary:
        root = Path(temporary)
        decision = evaluate_claim(candidate, artifact_store=ArtifactStore(root / "artifacts"), metadata_store=MetadataStore(root / "metadata.sqlite"))
    if decision.claim_state is not ClaimState.INADMISSIBLE or decision.failure_code != "unsupported_claim_type":
        return _unexpected("commerce_lens.application.analysis_service.evaluate_claim", "CLAIM_CLASS_NOT_REFUSED", decision.model_dump(mode="json"))
    if candidate.claim_type is ClaimType.CAUSAL:
        disposition = "CLAIM_PROHIBITED__CAUSAL_AUTHORITY_UNAVAILABLE"
        blocker_id = "causal_claim_class_restriction"
    else:
        disposition = "CLAIM_PROHIBITED"
        blocker_id = "requested_claim_class_unavailable"
    return _projection(
        producer="commerce_lens.application.analysis_service.evaluate_claim",
        path=(_stage("claim_decision", "blocked", disposition, reason=decision.failure_code, authority=_R1_CLAIM),),
        disposition=disposition,
        blocker=_blocker(blocker_id, "claim_decision", decision.failure_code, _R1_CLAIM),
        chain="claim_prohibited",
        trace={"claim_state": decision.claim_state.value, "failure_code": decision.failure_code, "policy_version": decision.policy_version},
        refs=((decision.artifact_ref.artifact_id,) if decision.artifact_ref else ()),
    )


def _produce_public_claim_authority_boundary(fixture: LoadedR5Fixture) -> ActualProjection:
    scenario = _json_input(fixture, "scenario")["scenario"]
    with tempfile.TemporaryDirectory(prefix="r5-pf2-public-") as temporary:
        root = Path(temporary)
        artifact_store = ArtifactStore(root / "artifacts")
        metadata_store = MetadataStore(root / "metadata.sqlite")
        source = _input_path(fixture, "orders")
        diagnostic = scenario == "descriptive_not_diagnostic"
        intent = _public_intent(fixture, source, diagnostic=diagnostic)
        if scenario == "finding_without_decision":
            intent = replace(intent, claim_intents=())
        outcome = run_public_analysis(intent, artifact_store=artifact_store, metadata_store=metadata_store, **_fixture_authority(intent.source, artifact_store, fixture))
    if scenario == "descriptive_not_diagnostic":
        supported = tuple(item for item in outcome.response.supported_claims if item.claim_state is ClaimState.ADMISSIBLE)
        denied = tuple(item for item in outcome.claim_decisions if item.failure_code == "unsupported_claim_type")
        observed = bool(supported) and bool(denied)
        disposition = "VALIDATED_DESCRIPTIVE_RESULT_ONLY__NO_DIAGNOSTIC_MEANING"
        trace = {"descriptive_supported": bool(supported), "diagnostic_claim_denied": bool(denied), "diagnostic_findings": 0}
    elif scenario == "finding_without_decision":
        observed = not outcome.claim_decisions and not outcome.response.supported_claims
        disposition = "AUTHORITY_BYPASS__FINDING_BLOCKED"
        trace = {"claim_decisions": len(outcome.claim_decisions), "supported_findings": len(outcome.response.supported_claims)}
    else:
        raise ValueError(f"unsupported public authority scenario: {scenario}")
    if not observed:
        return _unexpected("commerce_lens.skill.integration.run_public_analysis", "PUBLIC_AUTHORITY_BOUNDARY_NOT_OBSERVED", trace)
    if scenario == "descriptive_not_diagnostic":
        return _projection(
            producer="commerce_lens.skill.integration.run_public_analysis",
            path=(_stage("validation", "reached", "validated_descriptive_result"),),
            disposition=disposition,
            blocker="NONE",
            chain="descriptive_result_only",
            trace=trace,
        )
    return _projection(
        producer="commerce_lens.skill.integration.run_public_analysis",
        path=(
            _stage("validation", "reached", "validated_descriptive_result"),
            _stage("claim_decision", "blocked", disposition, reason="claim_decision_required_or_denied", authority=_R1_CLAIM),
            _not_reached("rendering", "claim_decision"),
        ),
        disposition=disposition,
        blocker=_blocker("claim_authority_boundary", "claim_decision", "claim_decision_required_or_denied", _R1_CLAIM),
        chain="finding_blocked",
        trace=trace,
    )


def _produce_claim_binding_verification(fixture: LoadedR5Fixture) -> ActualProjection:
    with tempfile.TemporaryDirectory(prefix="r5-pf2-binding-") as temporary:
        root = Path(temporary)
        artifact_store = ArtifactStore(root / "artifacts")
        metadata_store = MetadataStore(root / "metadata.sqlite")
        source = _input_path(fixture, "orders")
        intent = _public_intent(fixture, source, diagnostic=False)
        outcome = run_public_analysis(intent, artifact_store=artifact_store, metadata_store=metadata_store, **_fixture_authority(intent.source, artifact_store, fixture))
        decision = outcome.claim_decisions[0]
        artifact = metadata_store.get_claim_decision_artifact_reference(decision.claim_decision_id)
        if artifact is None:
            raise ValueError("valid ClaimDecision lacks artifact authority")
        path = artifact_store.safe_path(artifact.path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["claim_candidate_ref"] = "clmcand_different_proposition"
        path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        try:
            verify_claim_decision_artifact(artifact, artifact_store=artifact_store, metadata_store=metadata_store)
        except ClaimAdmissibilityError as exc:
            failure_code = exc.failure_code
        else:
            failure_code = None
    if failure_code is None:
        return _unexpected("commerce_lens.evidence.claim_admissibility.verify_claim_decision_artifact", "REBIND_NOT_DETECTED", None)
    disposition = "CLAIMDECISION_BINDING_MISMATCH__BLOCKED"
    return _projection(
        producer="commerce_lens.evidence.claim_admissibility.verify_claim_decision_artifact",
        path=(_stage("claim_decision", "blocked", disposition, reason=failure_code, authority=_R2_CLAIM),),
        disposition=disposition,
        blocker=_blocker("claimdecision_binding", "claim_decision", failure_code, _R2_CLAIM),
        chain="claim_rebind_blocked",
        trace={"failure_code": failure_code},
    )


def _produce_exact_version_binding(fixture: LoadedR5Fixture) -> ActualProjection:
    scenario = _json_input(fixture, "scenario")["scenario"]
    if scenario != "exact_current_versions":
        raise ValueError(f"unsupported exact-version scenario: {scenario}")
    with _analysis_runtime(fixture, ("revenue_change",)) as context:
        result = _validated_result(context, "revenue_change", "comparison")
        exact = (
            result.metric_definition_version == METRIC_DEFINITION_VERSION
            and context.request.metric_registry_version == METRIC_REGISTRY_VERSION
            and bool(context.result.admissible_evidence_refs)
        )
        trace = {"metric_version": result.metric_definition_version, "registry_version": context.request.metric_registry_version, "evidence_bound": bool(context.result.admissible_evidence_refs)}
    if not exact:
        return _unexpected("commerce_lens.application.analysis_service.run_analysis", "EXACT_VERSION_BINDING_FAILED", trace)
    return _projection(
        producer="commerce_lens.application.analysis_service.run_analysis",
        path=(_stage("evidence_admissibility", "reached", "bound_authority_current_and_resolvable"),),
        disposition="BOUND_AUTHORITY_CURRENT_AND_RESOLVABLE",
        blocker="NONE",
        chain="bound_authority_current",
        trace=trace,
    )


def _produce_claim_policy_version_binding(fixture: LoadedR5Fixture) -> ActualProjection:
    scenario = _json_input(fixture, "scenario")["scenario"]
    if scenario != "claim_policy_mismatch":
        raise ValueError(f"unsupported claim-policy scenario: {scenario}")
    with tempfile.TemporaryDirectory(prefix="r5-pf2-policy-") as temporary:
        root = Path(temporary)
        artifact_store = ArtifactStore(root / "artifacts")
        metadata_store = MetadataStore(root / "metadata.sqlite")
        source = _input_path(fixture, "orders")
        intent = _public_intent(fixture, source, diagnostic=False)
        outcome = run_public_analysis(intent, artifact_store=artifact_store, metadata_store=metadata_store, **_fixture_authority(intent.source, artifact_store, fixture))
        candidate = outcome.claim_candidates[0]
        decision = evaluate_claim_admissibility(
            claim_candidate_id=candidate.claim_candidate_id,
            artifact_store=artifact_store,
            metadata_store=metadata_store,
            policy_version="p8_000_old",
        ).claim_decision
    if decision.failure_code != "policy_version_mismatch":
        return _unexpected("commerce_lens.evidence.claim_admissibility.evaluate_claim_admissibility", "POLICY_MISMATCH_NOT_DETECTED", decision.failure_code)
    disposition = "POLICY_BINDING_MISMATCH__DECISION_NOT_REUSABLE"
    return _projection(
        producer="commerce_lens.evidence.claim_admissibility.evaluate_claim_admissibility",
        path=(_stage("claim_decision", "blocked", disposition, reason=decision.failure_code, authority=_VERSION_AUTHORITY),),
        disposition=disposition,
        blocker=_blocker("claim_policy_version", "claim_decision", decision.failure_code, _VERSION_AUTHORITY),
        chain="decision_not_reusable",
        trace={"current_policy_version": CLAIM_POLICY_VERSION, "attempted_policy_version": "p8_000_old", "failure_code": decision.failure_code},
    )


@dataclass(frozen=True)
class _RetainedStateObservation:
    checks: dict
    errors: tuple[str, ...]
    retention_status: str
    target_artifact_id: str
    target_exists: bool
    retained_target_fingerprint: str | None
    actual_target_fingerprint: str | None
    marker_exists: bool
    marker_content: str | None
    manifest_fingerprint: str | None
    metric_registry_version: str
    policy_versions: tuple[str, ...]


@dataclass(frozen=True)
class _IntegrityClassification:
    disposition: str
    blocker_id: str
    reason: str
    trace: dict


def _observe_retained_state(
    fixture: LoadedR5Fixture,
    setup_condition: str,
) -> _RetainedStateObservation:
    with tempfile.TemporaryDirectory(prefix="r5-pf2-retention-") as temporary:
        root = Path(temporary)
        session = RetainedRunSession.begin(root / "retention")
        source = _input_path(fixture, "orders")
        intent = _public_intent(fixture, source, diagnostic=False)
        outcome = run_public_analysis(
            intent,
            artifact_store=session.artifact_store,
            metadata_store=session.metadata_store,
            run_id=session.run_id,
            retention_session=session,
            **_fixture_authority(intent.source, session.artifact_store, fixture),
        )
        manifest = session.finalize(
            outcome,
            public_payload={"rendered_text": outcome.response.render_text()},
        )
        target_ref = manifest.analysis_result_artifact
        if target_ref is None:
            raise ValueError("retained run lacks final AnalysisResult artifact")
        target = session.artifact_store.safe_path(target_ref.path)
        marker = session.run_root / RetainedRunSession.COMPLETE_MARKER
        if setup_condition == "missing_required_artifact":
            target.unlink()
        elif setup_condition == "fingerprint_content_mismatch":
            target.write_text("content differs from retained fingerprint\n", encoding="utf-8")
        elif setup_condition == "false_complete":
            marker.unlink()
        elif setup_condition == "marker_mismatch":
            marker.write_text("0" * 64, encoding="ascii")
        elif setup_condition not in {"verified_integrity", "historical_versions"}:
            raise ValueError(f"unsupported retention setup condition: {setup_condition}")
        store = RetentionStore(root / "retention")
        checks, errors = store.verify_run(session.run_id)
        inspected = store.inspect_run(session.run_id)
        target_exists = target.is_file()
        marker_exists = marker.is_file()
        return _RetainedStateObservation(
            checks=checks,
            errors=tuple(errors),
            retention_status=inspected["retention_status"],
            target_artifact_id=target_ref.artifact_id,
            target_exists=target_exists,
            retained_target_fingerprint=target_ref.fingerprint,
            actual_target_fingerprint=sha256_file(target) if target_exists else None,
            marker_exists=marker_exists,
            marker_content=marker.read_text(encoding="ascii") if marker_exists else None,
            manifest_fingerprint=manifest.manifest_fingerprint,
            metric_registry_version=manifest.metric_registry_version,
            policy_versions=manifest.policy_versions,
        )


def _classify_artifact_integrity(observation: _RetainedStateObservation) -> _IntegrityClassification:
    verifier_detected = observation.checks.get("artifact_hashes") is False and any(
        "missing or hash mismatch" in error for error in observation.errors
    )
    if not verifier_detected:
        raise ValueError("retention verifier did not detect an artifact integrity failure")
    if not observation.target_exists:
        return _IntegrityClassification(
            disposition="REQUIRED_ARTIFACT_MISSING__AFFECTED_AUTHORITY_BLOCKED",
            blocker_id="required_artifact_presence",
            reason="required_artifact_missing",
            trace={"artifact_hashes": False, "target_exists": False},
        )
    if (
        observation.actual_target_fingerprint is not None
        and observation.retained_target_fingerprint is not None
        and observation.actual_target_fingerprint != observation.retained_target_fingerprint
    ):
        return _IntegrityClassification(
            disposition="FINGERPRINT_MISMATCH__AFFECTED_AUTHORITY_BLOCKED",
            blocker_id="artifact_fingerprint",
            reason="artifact_fingerprint_mismatch",
            trace={"artifact_hashes": False, "target_exists": True},
        )
    raise ValueError("observed artifact state does not explain verifier failure")


def _classify_completion_integrity(observation: _RetainedStateObservation) -> _IntegrityClassification:
    verifier_detected = (
        observation.checks.get("complete_marker") is False
        and observation.retention_status == "retained_incomplete"
    )
    if not verifier_detected:
        raise ValueError("retention verifier did not detect a completion integrity failure")
    if not observation.marker_exists:
        return _IntegrityClassification(
            disposition="RETENTION_COMPLETION_FALSE__INTEGRITY_FAILURE",
            blocker_id="retention_completion",
            reason="complete_marker_missing",
            trace={
                "complete_marker": False,
                "effective_retention_status": observation.retention_status,
            },
        )
    if observation.marker_content != observation.manifest_fingerprint:
        return _IntegrityClassification(
            disposition="RETENTION_MARKER_MISMATCH__INTEGRITY_FAILURE",
            blocker_id="retention_marker",
            reason="complete_marker_mismatch",
            trace={
                "complete_marker": False,
                "effective_retention_status": observation.retention_status,
            },
        )
    raise ValueError("observed completion state does not explain verifier failure")


def _produce_retention_state(fixture: LoadedR5Fixture) -> ActualProjection:
    setup_condition = _json_input(fixture, "scenario")["scenario"]
    if setup_condition not in {"verified_integrity", "historical_versions"}:
        raise ValueError(f"unsupported retained-state verification setup: {setup_condition}")
    observation = _observe_retained_state(fixture, setup_condition)
    if setup_condition == "verified_integrity":
        if observation.errors:
            return _unexpected(
                "commerce_lens.persistence.retention.RetentionStore.verify_run",
                "INTEGRITY_NOT_VERIFIED",
                observation.errors,
            )
        return _projection(
            producer="commerce_lens.persistence.retention.RetentionStore.verify_run",
            path=(_stage("artifact_integrity", "reached", "integrity_verified"),),
            disposition="INTEGRITY_VERIFIED",
            blocker="NONE",
            chain="integrity_verified",
            trace={
                "manifest_fingerprint": observation.checks.get("manifest_fingerprint"),
                "artifact_hashes": observation.checks.get("artifact_hashes"),
                "complete_marker": observation.checks.get("complete_marker"),
            },
            refs=(observation.target_artifact_id,),
        )
    preserved = (
        not observation.errors
        and observation.metric_registry_version == METRIC_REGISTRY_VERSION
        and CLAIM_POLICY_VERSION in observation.policy_versions
    )
    if not preserved:
        return _unexpected(
            "commerce_lens.persistence.retention.RetentionStore.verify_run",
            "HISTORICAL_BINDING_NOT_PRESERVED",
            {
                "errors": observation.errors,
                "metric_registry_version": observation.metric_registry_version,
                "policy_versions": observation.policy_versions,
            },
        )
    return _projection(
        producer="commerce_lens.persistence.retention.RetentionStore.verify_run",
        path=(_stage("artifact_integrity", "reached", "historical_authority_preserved"),),
        disposition="HISTORICAL_AUTHORITY_PRESERVED",
        blocker="NONE",
        chain="historical_authority_preserved",
        trace={
            "metric_registry_version": observation.metric_registry_version,
            "policy_versions": list(observation.policy_versions),
            "manifest_verified": True,
        },
        refs=(observation.target_artifact_id,),
    )


def _produce_retention_integrity_state(fixture: LoadedR5Fixture) -> ActualProjection:
    setup_condition = _json_input(fixture, "scenario")["scenario"]
    observation = _observe_retained_state(fixture, setup_condition)
    if observation.checks.get("artifact_hashes") is False:
        classification = _classify_artifact_integrity(observation)
    elif observation.checks.get("complete_marker") is False:
        classification = _classify_completion_integrity(observation)
    else:
        raise ValueError("retention verifier did not expose a supported hostile integrity state")
    producer = (
        "commerce_lens.persistence.retention.RetentionStore.verify_run"
        "+retained_filesystem_state_observation"
    )
    return _projection(
        producer=producer,
        path=(
            _stage(
                "artifact_integrity",
                "blocked",
                classification.disposition,
                reason=classification.reason,
                authority=_PROVENANCE_AUTHORITY,
            ),
        ),
        disposition=classification.disposition,
        blocker=_blocker(
            classification.blocker_id,
            "artifact_integrity",
            classification.reason,
            _PROVENANCE_AUTHORITY,
        ),
        chain="affected_authority_blocked",
        trace=classification.trace,
        refs=(observation.target_artifact_id,),
    )


def _produce_provenance_authority(fixture: LoadedR5Fixture) -> ActualProjection:
    with tempfile.TemporaryDirectory(prefix="r5-pf2-provenance-") as temporary:
        root = Path(temporary)
        artifact_store = ArtifactStore(root / "artifacts")
        metadata_store = MetadataStore(root / "metadata.sqlite")
        source = _input_path(fixture, "orders")
        intent = _public_intent(fixture, source, diagnostic=False)
        outcome = run_public_analysis(intent, artifact_store=artifact_store, metadata_store=metadata_store, **_fixture_authority(intent.source, artifact_store, fixture))
        authentic = outcome.claim_candidates[0]
        copied = authentic.model_copy(
            update={
                "claim_candidate_id": "clmcand_copied_value_without_lineage",
                "supporting_evidence_refs": ("ev_copied_without_lineage",),
                "supporting_validated_result_refs": ("valres_copied_without_lineage",),
            }
        )
        decision = evaluate_claim(copied, artifact_store=artifact_store, metadata_store=metadata_store)
    if decision.failure_code != "missing_persisted_evidence_authority":
        return _unexpected("commerce_lens.application.analysis_service.evaluate_claim", "LINEAGE_ABSENCE_NOT_DETECTED", decision.failure_code)
    disposition = "VALUE_EQUIVALENCE_WITHOUT_AUTHORITY__INADMISSIBLE"
    return _projection(
        producer="commerce_lens.application.analysis_service.evaluate_claim",
        path=(_stage("evidence_admissibility", "blocked", disposition, reason=decision.failure_code, authority=_PROVENANCE_AUTHORITY),),
        disposition=disposition,
        blocker=_blocker("provenance_lineage", "evidence_admissibility", decision.failure_code, _PROVENANCE_AUTHORITY),
        chain="copied_value_inadmissible",
        trace={"claim_state": decision.claim_state.value, "failure_code": decision.failure_code},
        refs=((decision.artifact_ref.artifact_id,) if decision.artifact_ref else ()),
    )


def _replace_execution_record(metadata_store: MetadataStore, execution_id: str, **updates) -> None:
    record = metadata_store.get_execution_record(execution_id)
    if record is None:
        raise ValueError("execution record is missing before controlled mismatch")
    payload = record.model_dump(mode="json")
    payload.update(updates)
    with sqlite3.connect(metadata_store.db_path) as connection:
        connection.execute("UPDATE execution_records SET record_json = ? WHERE execution_id = ?", (json.dumps(payload, sort_keys=True), execution_id))


def _replace_request_metric_version(context, version: str) -> None:
    request = context.request.model_copy(update={"metrics": tuple(item.model_copy(update={"definition_version": version}) for item in context.request.metrics)})
    payload = request.model_dump(mode="json")
    with sqlite3.connect(context.metadata_store.db_path) as connection:
        row = connection.execute("SELECT request_artifact_id FROM analysis_requests WHERE request_id = ?", (request.request_id,)).fetchone()
    if row is None:
        raise ValueError("analysis request authority is missing")
    artifact = context.metadata_store.get_artifact_reference(row[0])
    if artifact is None:
        raise ValueError("analysis request artifact reference is missing")
    path = context.artifact_store.safe_path(artifact.path)
    path.write_bytes(canonical_json_bytes(payload))
    fingerprint = sha256_file(path)
    refreshed = artifact.model_copy(update={"artifact_id": stable_content_id("art", fingerprint), "fingerprint": fingerprint, "size_bytes": path.stat().st_size})
    context.metadata_store.insert_artifact_reference(refreshed)
    with sqlite3.connect(context.metadata_store.db_path) as connection:
        connection.execute(
            "UPDATE analysis_requests SET request_artifact_id = ?, record_json = ?, record_fingerprint = ? WHERE request_id = ?",
            (refreshed.artifact_id, json.dumps(payload, sort_keys=True), canonical_json_fingerprint(payload), request.request_id),
        )


def _projection(*, producer: str, path, disposition: str, blocker, chain: str, trace, refs=()) -> ActualProjection:
    return ActualProjection.model_validate(
        {
            "material_path": path,
            "chain_dispositions": {"main": chain},
            "first_controlling_blocker": blocker,
            "final_disposition": disposition,
            "trace_integrity_state": trace,
            "artifact_evidence_refs": refs,
            "actual_output_producer": producer,
        }
    )


def _unexpected(producer: str, disposition: str, trace) -> ActualProjection:
    return _projection(
        producer=producer,
        path=(_stage("artifact_integrity", "reached", disposition),),
        disposition=disposition,
        blocker="NONE",
        chain="unexpected_runtime_result",
        trace={"observed": trace},
    )
