from __future__ import annotations

import socket
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import pytest

from commerce_lens.application import ApplicationServiceError, evaluate_claim, run_analysis
from commerce_lens.contracts.common import (
    AvailableEvidence,
    ClaimState,
    ClaimType,
    EvidenceRequirement,
    FailureDetail,
    FailureStage,
    MetricState,
    RunStatus,
    ScopeDefinition,
    SourceType,
)
from commerce_lens.contracts.evidence import (
    AdmissibleEvidence,
    ClaimCandidate,
    ClaimPropositionType,
)
from commerce_lens.contracts.sufficiency import SufficiencyState
from commerce_lens.contracts.validation import ValidationStatus
from commerce_lens.evidence.claim_admissibility import ClaimAdmissibilityError
from commerce_lens.evidence.identifiers import sha256_file
from commerce_lens.persistence.metadata_store import MetadataStore, SCHEMA_VERSION
from tests.engine.test_execution import (
    _canonicalization_request,
    _registered_source,
    _request,
    _row,
    _write_csv,
)


@dataclass(frozen=True)
class _AppFixture:
    result: object
    request: object
    artifact_store: object
    metadata_store: MetadataStore
    source_path: object
    source_fingerprint: str


def test_revenue_orders_numeric_aov_and_revenue_change_run_through_analysis(tmp_path) -> None:
    cases = (
        ("revenue", Decimal("100.00"), MetricState.VALID),
        ("orders", 1, MetricState.VALID),
        ("aov", Decimal("100.00"), MetricState.VALID),
        ("revenue_change", Decimal("20.00"), MetricState.VALID),
    )
    for metric_ref, expected_value, expected_state in cases:
        rows = [_row(line_revenue="100.00"), _row(order_id="o2", order_date="2026-01-03", line_revenue="120.00")]
        fixture = _run(tmp_path / metric_ref, (metric_ref,), rows)

        metric = _metric(fixture.result, metric_ref)
        values = _validated_values(fixture, metric_ref)

        assert metric.metric_state is expected_state
        assert expected_value in values
        assert metric.executed_result_refs
        assert metric.validation_record_refs
        assert metric.validated_result_refs
        assert metric.admissible_evidence_refs
        assert fixture.result.run_status is RunStatus.COMPLETED


def test_multi_metric_request_preserves_independent_per_chain_states_and_partial_completion(tmp_path) -> None:
    fixture = _run(
        tmp_path,
        ("revenue", "aov"),
        [_row(order_id="o1", eligibility_status="cancelled")],
    )

    revenue = _metric(fixture.result, "revenue")
    aov = _metric(fixture.result, "aov")

    assert revenue.metric_state is MetricState.VALID
    assert _validated_values(fixture, "revenue") == [Decimal("0"), Decimal("0")]
    assert aov.metric_state is MetricState.UNDEFINED
    assert _validated_states(fixture, "aov") == [MetricState.UNDEFINED, MetricState.UNDEFINED]
    assert fixture.result.run_status is RunStatus.PARTIALLY_COMPLETED
    assert len(fixture.result.metric_results) == 2


def test_aov_orders_zero_remains_undefined_not_zero(tmp_path) -> None:
    fixture = _run(tmp_path, ("aov",), [_row(eligibility_status="cancelled")])

    metric = _metric(fixture.result, "aov")
    values = _validated_values(fixture, "aov")
    states = _validated_states(fixture, "aov")

    assert metric.metric_state is MetricState.UNDEFINED
    assert states == [MetricState.UNDEFINED, MetricState.UNDEFINED]
    assert values == [None, None]
    assert Decimal("0") not in values


def test_data_sufficiency_failure_stops_blocked_chain_before_execution(tmp_path) -> None:
    fixture = _run(
        tmp_path,
        ("revenue", "orders"),
        [_row()],
        unsatisfied_requirement_metric="orders",
    )

    revenue = _metric(fixture.result, "revenue")
    orders = _metric(fixture.result, "orders")

    assert fixture.result.data_sufficiency_state is SufficiencyState.PARTIAL
    assert fixture.result.run_status is RunStatus.PARTIALLY_COMPLETED
    assert revenue.metric_state is MetricState.VALID
    assert orders.metric_state is MetricState.INADMISSIBLE
    assert orders.executed_result_refs == ()
    assert "orders" in fixture.result.blocked_metric_refs


def test_validation_failure_cannot_become_validated_result_or_evidence(tmp_path, monkeypatch) -> None:
    import commerce_lens.application.analysis_service as service

    original_execute_plan = service.execute_plan

    def execute_with_tampered_artifact(plan, canonical_dataset, artifact_store, metadata_store):
        outcome = original_execute_plan(plan, canonical_dataset, artifact_store, metadata_store)
        record = next(item for item in outcome.execution_records if item.metric_refs == ("revenue",))
        artifact_path = artifact_store.safe_path(record.output_artifacts[0].path)
        artifact_path.write_text(artifact_path.read_text(encoding="utf-8").replace("10.00", "11.00"), encoding="utf-8")
        return outcome

    monkeypatch.setattr(service, "execute_plan", execute_with_tampered_artifact)
    fixture = _run(tmp_path, ("revenue",), [_row()])

    metric = _metric(fixture.result, "revenue")
    failed = [
        record
        for record in fixture.metadata_store.list_validation_records()
        if record.status is ValidationStatus.FAILED
    ]

    assert failed
    assert fixture.result.run_status is RunStatus.PARTIALLY_COMPLETED
    assert metric.metric_state is MetricState.VALID
    evidence_records = fixture.metadata_store.list_evidence_admissibility_records()
    assert all(record.validated_result_ref is None for record in failed)
    assert all(record.target_result_ref not in metric.validated_result_refs for record in failed)
    assert all(
        evidence.validated_result_id != record.target_result_ref
        for evidence in evidence_records
        for record in failed
    )


def test_local_source_registration_path_uses_intake_and_preserves_request_dataset_authority(tmp_path) -> None:
    source_path = tmp_path / "orders.csv"
    _write_csv(source_path, [_row()])
    artifact_store = _artifact_store(tmp_path / "runtime")
    from commerce_lens.intake.registry import DatasetRegistry

    dataset = DatasetRegistry(artifact_store).register_source(source_path, SourceType.CSV)
    request = _request(("orders",), dataset.dataset_id, scope=ScopeDefinition(scope_id="all_eligible"))
    request = request.model_copy(update={"required_evidence": _requirements(("orders",))})
    metadata_store = MetadataStore(tmp_path / "metadata.sqlite")

    result = run_analysis(
        request,
        canonicalization_request=_canonicalization_request(dataset),
        artifact_store=artifact_store,
        metadata_store=metadata_store,
        source_path=source_path,
        source_type=SourceType.CSV,
        period_coverage_evidence=_coverage(dataset.dataset_id),
        available_evidence=_available_evidence(request),
    )

    assert result.request_id == request.request_id
    assert metadata_store.get_dataset(request.dataset_ref_id).dataset_id == request.dataset_ref_id
    assert _metric(result, "orders").metric_state is MetricState.VALID


def test_base_analysis_does_not_construct_claim_candidate_or_claim_decision(tmp_path) -> None:
    fixture = _run(tmp_path, ("revenue",), [_row()])

    assert fixture.result.claim_decisions == ()
    assert fixture.metadata_store.list_claim_candidates() == []
    assert fixture.metadata_store.list_claim_decision_records(fixture.artifact_store) == []


def test_descriptive_claim_candidate_returns_authoritative_admissible_decision(tmp_path) -> None:
    fixture = _run(tmp_path, ("revenue",), [_row()])
    validated = _validated_result(fixture, "revenue")
    evidence = _admissible_evidence(fixture, "revenue")
    candidate = _candidate_from_evidence(fixture, validated, evidence)

    decision = evaluate_claim(candidate, artifact_store=fixture.artifact_store, metadata_store=fixture.metadata_store)
    authoritative = fixture.metadata_store.get_claim_decision_record(decision.claim_decision_id, fixture.artifact_store)

    assert decision.claim_state is ClaimState.ADMISSIBLE
    assert decision.failure_code is None
    assert authoritative == decision
    assert decision.claim_candidate_ref == candidate.claim_candidate_id


def test_diagnostic_claim_candidate_is_inadmissible_with_unsupported_claim_type(tmp_path) -> None:
    fixture = _run(tmp_path, ("revenue",), [_row()])
    validated = _validated_result(fixture, "revenue")
    evidence = _admissible_evidence(fixture, "revenue")
    candidate = _candidate_from_evidence(fixture, validated, evidence, claim_type=ClaimType.DIAGNOSTIC)

    decision = evaluate_claim(candidate, artifact_store=fixture.artifact_store, metadata_store=fixture.metadata_store)

    assert decision.claim_state is ClaimState.INADMISSIBLE
    assert decision.failure_code == "unsupported_claim_type"


def test_cross_request_or_forged_claim_authority_fails_closed(tmp_path) -> None:
    fixture = _run(tmp_path, ("revenue",), [_row()])
    validated = _validated_result(fixture, "revenue")
    evidence = _admissible_evidence(fixture, "revenue")
    forged = _candidate_from_evidence(fixture, validated, evidence).model_copy(update={"request_id": "req_forged"})

    decision = evaluate_claim(forged, artifact_store=fixture.artifact_store, metadata_store=fixture.metadata_store)

    assert decision.claim_state is ClaimState.INADMISSIBLE
    assert decision.failure_code == "cross_request_substitution"


def test_claim_operation_returns_authoritative_boundary_not_persistence_only_record(tmp_path, monkeypatch) -> None:
    import commerce_lens.application.analysis_service as service

    fixture = _run(tmp_path, ("revenue",), [_row()])
    validated = _validated_result(fixture, "revenue")
    evidence = _admissible_evidence(fixture, "revenue")
    candidate = _candidate_from_evidence(fixture, validated, evidence)

    def retrieval_fails(*args, **kwargs):
        raise ClaimAdmissibilityError("claim_decision_artifact_hash_mismatch", "forced retrieval boundary")

    monkeypatch.setattr(service, "get_authoritative_claim_decision", retrieval_fails)

    with pytest.raises(ClaimAdmissibilityError, match="forced retrieval boundary"):
        evaluate_claim(candidate, artifact_store=fixture.artifact_store, metadata_store=fixture.metadata_store)


def test_source_selected_sheet_or_table_runtime_mismatch_fails_closed(tmp_path) -> None:
    source_path = tmp_path / "orders.csv"
    _write_csv(source_path, [_row()])
    preflight_store = _artifact_store(tmp_path / "preflight")
    from commerce_lens.intake.registry import DatasetRegistry

    dataset = DatasetRegistry(preflight_store).register_source(source_path, SourceType.CSV)
    request = _request(("revenue",), dataset.dataset_id, scope=ScopeDefinition(scope_id="all_eligible")).model_copy(
        update={"selected_table": "request_table"}
    )
    canonical_request = _canonicalization_request(dataset)
    metadata_store = MetadataStore(tmp_path / "metadata.sqlite")

    with pytest.raises(ApplicationServiceError, match="selected_table"):
        run_analysis(
            request,
            canonicalization_request=canonical_request,
            artifact_store=preflight_store,
            metadata_store=metadata_store,
            source_path=source_path,
            source_type=SourceType.CSV,
            selected_table="runtime_table",
            period_coverage_evidence=_coverage(dataset.dataset_id),
        )


def test_repeat_invocation_preserves_material_semantics_and_source_input(tmp_path) -> None:
    rows = [_row(line_revenue="10.00"), _row(order_id="o2", order_date="2026-01-03", line_revenue="15.00")]
    fixture = _run(tmp_path, ("revenue",), rows)
    second = run_analysis(
        fixture.request,
        canonicalization_request=_canonicalization_request(
            fixture.metadata_store.get_dataset(fixture.request.dataset_ref_id)
        ),
        artifact_store=fixture.artifact_store,
        metadata_store=fixture.metadata_store,
        period_coverage_evidence=_coverage(fixture.request.dataset_ref_id),
        available_evidence=_available_evidence(fixture.request),
    )

    assert _validated_values_for_analysis(fixture, fixture.result, "revenue") == [Decimal("10.00"), Decimal("15.00")]
    assert _validated_values_for_analysis(fixture, second, "revenue") == [Decimal("10.00"), Decimal("15.00")]
    assert [item.metric_state for item in second.metric_results] == [MetricState.VALID]
    assert fixture.source_fingerprint == sha256_file(fixture.source_path)


def test_analysis_has_no_network_dependency(tmp_path, monkeypatch) -> None:
    def forbidden_socket(*args, **kwargs):
        raise AssertionError("network is not allowed")

    monkeypatch.setattr(socket, "socket", forbidden_socket)

    fixture = _run(tmp_path, ("orders",), [_row()])

    assert _metric(fixture.result, "orders").metric_state is MetricState.VALID
    assert fixture.metadata_store.schema_version() == SCHEMA_VERSION


def _run(
    tmp_path,
    metrics: tuple[str, ...],
    rows: list[dict[str, str]],
    *,
    unsatisfied_requirement_metric: str | None = None,
) -> _AppFixture:
    tmp_path.mkdir(parents=True, exist_ok=True)
    source_path = tmp_path / "orders.csv"
    _write_csv(source_path, rows)
    source_fingerprint = sha256_file(source_path)
    dataset, artifact_store = _registered_source(tmp_path, rows, filename="orders.csv", source_type="csv")
    metadata_store = MetadataStore(tmp_path / "metadata.sqlite")
    request = _request(metrics, dataset.dataset_id, scope=ScopeDefinition(scope_id="all_eligible"))
    request = request.model_copy(update={"required_evidence": _requirements(metrics)})
    available = _available_evidence(request, unsatisfied_metric=unsatisfied_requirement_metric)
    result = run_analysis(
        request,
        canonicalization_request=_canonicalization_request(dataset),
        artifact_store=artifact_store,
        metadata_store=metadata_store,
        dataset=dataset,
        period_coverage_evidence=_coverage(dataset.dataset_id),
        available_evidence=available,
    )
    return _AppFixture(result, request, artifact_store, metadata_store, source_path, source_fingerprint)


def _requirements(metrics: tuple[str, ...]) -> tuple[EvidenceRequirement, ...]:
    return (
        EvidenceRequirement(requirement_id="req_global", description="global source authority"),
        *(
            EvidenceRequirement(requirement_id=f"req_{metric}", description=f"{metric} authority", metric_ref=metric)
            for metric in metrics
        ),
    )


def _available_evidence(
    request,
    *,
    unsatisfied_metric: str | None = None,
) -> tuple[AvailableEvidence, ...]:
    satisfied = tuple(
        requirement.requirement_id
        for requirement in request.required_evidence
        if not (unsatisfied_metric is not None and requirement.metric_ref == unsatisfied_metric)
    )
    return (
        AvailableEvidence(
            evidence_id="avail_source",
            description="governed source and period coverage",
            source_ref=request.dataset_ref_id,
            satisfies_requirement_ids=satisfied,
        ),
    )


def _coverage(dataset_ref_id: str):
    from commerce_lens.canonical.models import PeriodCoverageEvidence

    return (
        PeriodCoverageEvidence(
            coverage_ref_id="coverage_all",
            dataset_ref_id=dataset_ref_id,
            observed_start_date=date(2026, 1, 1),
            observed_end_date=date(2026, 1, 4),
            date_convention_ref="order_date_utc",
        ),
    )


def _artifact_store(path):
    from commerce_lens.persistence.artifact_store import ArtifactStore

    return ArtifactStore(path)


def _metric(result, metric_ref: str):
    return next(item for item in result.metric_results if item.metric_ref == metric_ref)


def _validated_result(fixture: _AppFixture, metric_ref: str):
    return next(
        record
        for record in fixture.metadata_store.list_validation_records()
        if record.metric_ref == metric_ref and record.status is ValidationStatus.PASSED
    ).validated_result_ref and next(
        item
        for item in _validated_results(fixture)
        if item.metric_ref == metric_ref
    )


def _validated_results(fixture: _AppFixture):
    from commerce_lens.contracts.validation import ValidatedResult

    results = []
    seen = set()
    for record in fixture.metadata_store.list_validation_records():
        artifact = record.validated_result_artifact_ref
        if artifact is None or record.validated_result_ref in seen:
            continue
        seen.add(record.validated_result_ref)
        results.append(
            ValidatedResult.model_validate_json(
                fixture.artifact_store.safe_path(artifact.path).read_text(encoding="utf-8")
            )
        )
    return results


def _validated_values(fixture: _AppFixture, metric_ref: str):
    return [item.value for item in _validated_results(fixture) if item.metric_ref == metric_ref]


def _validated_states(fixture: _AppFixture, metric_ref: str):
    return [item.metric_state for item in _validated_results(fixture) if item.metric_ref == metric_ref]


def _validated_values_for_analysis(fixture: _AppFixture, analysis_result, metric_ref: str):
    wanted = set(analysis_result.validated_result_refs)
    return [
        item.value
        for item in _validated_results(fixture)
        if item.validated_result_id in wanted and item.metric_ref == metric_ref
    ]


def _admissible_evidence(fixture: _AppFixture, metric_ref: str) -> AdmissibleEvidence:
    record = next(
        item
        for item in fixture.metadata_store.list_evidence_admissibility_records()
        if item.metric_ref == metric_ref and item.admissible_evidence_artifact_ref is not None
    )
    return AdmissibleEvidence.model_validate_json(
        fixture.artifact_store.safe_path(record.admissible_evidence_artifact_ref.path).read_text(encoding="utf-8")
    )


def _candidate_from_evidence(
    fixture: _AppFixture,
    result,
    evidence: AdmissibleEvidence,
    *,
    claim_type=ClaimType.DESCRIPTIVE,
):
    execution_record = fixture.metadata_store.get_execution_record(result.execution_id)
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
        claim_candidate_id="clmcand_application_test",
        claim_id="claim_application_test",
        claim_type=claim_type,
        metric_ref=result.metric_ref,
        metric_definition_version=result.metric_definition_version,
        request_id=evidence.request_id,
        dataset_ref_id=evidence.dataset_ref_id,
        canonical_dataset_ref_id=evidence.canonical_dataset_ref_id,
        canonical_dataset_fingerprint=evidence.canonical_dataset_fingerprint,
        intended_scope=evidence.scope,
        population_ref=evidence.population_ref,
        population_fingerprint=evidence.population_fingerprint,
        period_ref=evidence.period_ref,
        period_role=evidence.period_role,
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
        supporting_validated_result_refs=evidence.validated_result_ids,
        proposed_meaning="presentation-only text",
        metadata={"test": True},
        **update,
    )
