"""Narrow P9 hostile Revenue Change validation seam."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from commerce_lens.application.analysis_service import _metric_state as application_metric_state_from_authority
from commerce_lens.contracts.execution import ExecutedResult
from commerce_lens.contracts.validation import ValidatedResult
from commerce_lens.engine.execution import _revenue_change_result_fingerprint
from commerce_lens.engine.plan_builder import build_execution_plan
from commerce_lens.evidence.identifiers import generate_id
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.validation.validator import validate_executed_result

from commerce_lens.fixture_runner.cases import CaseManifest, validate_fixed_hostile_authority


@dataclass(frozen=True)
class HostileRevenueChangeOutcome:
    data_sufficiency_state: str
    baseline_revenue: Decimal
    comparison_revenue: Decimal
    authoritative_revenue_change: Decimal
    submitted_value: Decimal
    execution_disposition: str
    validation_status: str
    validation_rule_id: str
    failure_code: str | None
    failed_metric_state: str
    final_disposition: str
    validated_result_authorized: bool
    admissible_evidence_authorized: bool
    claim_decision_authorized: bool
    observed: dict[str, object]


def run_revenue_change_wrong_value_case(manifest: CaseManifest, runtime_root: Path) -> HostileRevenueChangeOutcome:
    """Submit only the approved wrong Revenue Change value to the production validator."""
    from commerce_lens.fixture_runner.runner import CSV_HEADERS, _run_analysis_for_source, _materialize_setup_csv, _Runtime
    from commerce_lens.persistence.artifact_store import ArtifactStore

    artifact_store = ArtifactStore(runtime_root / "artifacts")
    metadata_store = MetadataStore(runtime_root / "metadata.sqlite")
    runtime = _Runtime(artifact_store=artifact_store, metadata_store=metadata_store, root=runtime_root)
    hostile = manifest.expected.hostile_revenue_change
    if hostile is None:
        raise ValueError("hostile Revenue Change manifest authority is required")
    hostile = validate_fixed_hostile_authority(hostile)
    rows = (
        {
            "order_id": "o1",
            "order_line_id": "l1",
            "order_date": "2026-01-01",
            "product_id": "p1",
            "product_name": "Tea",
            "category_id": "c1",
            "category_name": "Drinks",
            "quantity": "1",
            "line_revenue": str(hostile.baseline_revenue),
            "currency": "USD",
            "unit_price": "",
            "eligibility_status": "paid",
        },
        {
            "order_id": "o2",
            "order_line_id": "l1",
            "order_date": "2026-01-03",
            "product_id": "p1",
            "product_name": "Tea",
            "category_id": "c1",
            "category_name": "Drinks",
            "quantity": "1",
            "line_revenue": str(hostile.comparison_revenue),
            "currency": "USD",
            "unit_price": "",
            "eligibility_status": "paid",
        },
    )
    source_path = _materialize_setup_csv(runtime_root / "setup" / "hostile" / "input.csv", rows)
    context = _run_analysis_for_source(manifest, source_path, runtime)
    sufficiency = metadata_store.get_data_sufficiency_result(context.result.data_sufficiency_ref, artifact_store)
    if sufficiency is None or sufficiency.canonical_dataset_ref_id is None:
        raise ValueError("hostile Revenue Change setup lacks sufficiency/canonical authority")
    request = metadata_store.get_analysis_request(context.request.request_id, artifact_store)
    canonical = metadata_store.get_canonical_dataset(sufficiency.canonical_dataset_ref_id)
    if request is None or canonical is None:
        raise ValueError("hostile Revenue Change setup lacks request/canonical authority")
    plan = build_execution_plan(request, sufficiency)
    baseline = _validated_result(context, "revenue", "baseline")
    comparison = _validated_result(context, "revenue", "comparison")
    authoritative_change = _validated_result(context, "revenue_change", "comparison")
    record, tampered = _persist_wrong_revenue_change_result(context, plan, canonical, hostile.submitted_revenue_change)
    validation = validate_executed_result(
        execution_id=record.execution_id,
        result_id=tampered.result_id,
        plan=plan,
        canonical_dataset=canonical,
        artifact_store=artifact_store,
        metadata_store=metadata_store,
        dependency_validated_results=(baseline, comparison),
    )
    validated_refs = tuple(
        item.validated_result_ref
        for item in metadata_store.list_validation_records()
        if item.target_result_ref == tampered.result_id and item.validated_result_ref is not None
    )
    validated_result_authorized = validation.validated_result is not None or bool(validated_refs)
    admissible_evidence_authorized = any(
        record.executed_result_id == tampered.result_id
        or (record.validated_result_id is not None and record.validated_result_id in validated_refs)
        for record in metadata_store.list_evidence_admissibility_records()
    )
    claim_decision_authorized = bool(metadata_store.list_claim_decision_records(artifact_store))
    failed_metric_state = application_metric_state_from_authority(
        "revenue_change",
        sufficiency,
        (tampered,),
        (),
        (validation.validation_record,),
        validation.validation_record.failure_details,
    )
    execution_disposition = "hostile_submitted" if metadata_store.get_execution_record(record.execution_id) is not None else "not_started"
    final_disposition = (
        "validation_failed"
        if validation.validation_record.status.value == "failed"
        and not validated_result_authorized
        and not admissible_evidence_authorized
        and not claim_decision_authorized
        else "completed_admissible"
    )
    return HostileRevenueChangeOutcome(
        data_sufficiency_state=context.result.data_sufficiency_state.value,
        baseline_revenue=baseline.value,
        comparison_revenue=comparison.value,
        authoritative_revenue_change=authoritative_change.value,
        submitted_value=tampered.value,
        execution_disposition=execution_disposition,
        validation_status=validation.validation_record.status.value,
        validation_rule_id=validation.validation_record.validation_rule_id,
        failure_code=validation.validation_record.failure_code,
        failed_metric_state=failed_metric_state.value,
        final_disposition=final_disposition,
        validated_result_authorized=validated_result_authorized,
        admissible_evidence_authorized=admissible_evidence_authorized,
        claim_decision_authorized=claim_decision_authorized,
        observed={
            "baseline_revenue": str(baseline.value),
            "comparison_revenue": str(comparison.value),
            "authoritative_revenue_change": str(authoritative_change.value),
            "submitted_result_id": tampered.result_id,
            "submitted_value": str(tampered.value),
            "execution_disposition": execution_disposition,
            "validation_status": validation.validation_record.status.value,
            "validation_rule_id": validation.validation_record.validation_rule_id,
            "failure_code": validation.validation_record.failure_code,
            "failed_metric_state": failed_metric_state.value,
            "validated_result_authorized": validated_result_authorized,
            "admissible_evidence_authorized": admissible_evidence_authorized,
            "claim_decision_authorized": claim_decision_authorized,
            "final_disposition": final_disposition,
            "csv_headers": CSV_HEADERS,
        },
    )


def _persist_wrong_revenue_change_result(context, plan, canonical, value: Decimal):
    original_record = _execution_record(context, "revenue_change", "baseline_and_comparison")
    original_result = _executed_result(context, "revenue_change", "comparison")
    execution_id = generate_id("exec_p9_hostile")
    result_id = generate_id("exres_p9_hostile")
    result = original_result.model_copy(update={"execution_id": execution_id, "result_id": result_id, "value": value})
    node = next(item for item in plan.ordered_metrics if item.node_id == original_record.plan_node_id)
    populations = {item.population_id: item for item in plan.population_definitions}
    by_role = {populations[ref].period_role.value: populations[ref] for ref in node.population_refs}
    fingerprint = _revenue_change_result_fingerprint(
        node=node,
        baseline_population=by_role["baseline"],
        comparison_population=by_role["comparison"],
        canonical_dataset=canonical,
        value=result.value,
        currency=original_record.resolved_currency,
        baseline_result=_executed_result(context, "revenue", "baseline"),
        comparison_result=_executed_result(context, "revenue", "comparison"),
    )
    result = result.model_copy(update={"result_fingerprint": fingerprint})
    artifact = context.artifact_store.write_json_artifact(
        Path("runs") / execution_id / "results" / f"{result_id}.json",
        result.model_dump(mode="json"),
    )
    context.metadata_store.insert_artifact_reference(artifact)
    record = original_record.model_copy(
        update={
            "execution_id": execution_id,
            "result_ref": result_id,
            "output_artifacts": (artifact,),
        }
    )
    context.metadata_store.insert_execution_record(record)
    return record, result


def _validated_result(context, metric_ref: str, period_ref: str) -> ValidatedResult:
    from commerce_lens.fixture_runner.runner import _select_validated_result

    return _select_validated_result(context, metric_ref, period_ref, None)


def _execution_record(context, metric_ref: str, period_ref: str):
    for record in context.metadata_store.list_execution_records():
        if record.metric_refs != (metric_ref,):
            continue
        if record.period_refs == (period_ref,) or (
            metric_ref == "revenue_change"
            and period_ref == "baseline_and_comparison"
            and record.period_refs == ("baseline", "comparison")
        ):
            return record
    raise ValueError(f"missing ExecutionRecord for {metric_ref}/{period_ref}")


def _executed_result(context, metric_ref: str, period_ref: str) -> ExecutedResult:
    record = _execution_record(context, metric_ref, "baseline_and_comparison" if metric_ref == "revenue_change" else period_ref)
    artifact = record.output_artifacts[0]
    return ExecutedResult.model_validate_json(
        context.artifact_store.safe_path(artifact.path).read_text(encoding="utf-8")
    )
