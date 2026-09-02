"""Narrow P9 hostile Revenue Change validation seam."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from commerce_lens.contracts.common import MetricState
from commerce_lens.contracts.execution import ExecutedResult
from commerce_lens.contracts.validation import ValidatedResult
from commerce_lens.engine.execution import _revenue_change_result_fingerprint
from commerce_lens.engine.plan_builder import build_execution_plan
from commerce_lens.evidence.identifiers import generate_id
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.validation.validator import validate_executed_result

from commerce_lens.fixture_runner.cases import CaseManifest


@dataclass(frozen=True)
class HostileRevenueChangeOutcome:
    data_sufficiency_state: str
    submitted_value: Decimal
    validation_status: str
    validation_rule_id: str
    failure_code: str | None
    failed_metric_state: str
    validated_result_authorized: bool
    admissible_evidence_authorized: bool
    observed: dict[str, object]


def run_revenue_change_wrong_value_case(manifest: CaseManifest, runtime_root: Path) -> HostileRevenueChangeOutcome:
    """Submit only the approved wrong Revenue Change value to the production validator."""
    from commerce_lens.fixture_runner.runner import CSV_HEADERS, _run_analysis_for_source, _materialize_setup_csv, _Runtime
    from commerce_lens.persistence.artifact_store import ArtifactStore

    artifact_store = ArtifactStore(runtime_root / "artifacts")
    metadata_store = MetadataStore(runtime_root / "metadata.sqlite")
    runtime = _Runtime(artifact_store=artifact_store, metadata_store=metadata_store, root=runtime_root)
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
            "line_revenue": "100.00",
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
            "line_revenue": "120.00",
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
    record, tampered = _persist_wrong_revenue_change_result(context, plan, canonical, Decimal("21.00"))
    validation = validate_executed_result(
        execution_id=record.execution_id,
        result_id=tampered.result_id,
        plan=plan,
        canonical_dataset=canonical,
        artifact_store=artifact_store,
        metadata_store=metadata_store,
        dependency_validated_results=(baseline, comparison),
    )
    return HostileRevenueChangeOutcome(
        data_sufficiency_state=context.result.data_sufficiency_state.value,
        submitted_value=tampered.value,
        validation_status=validation.validation_record.status.value,
        validation_rule_id=validation.validation_record.validation_rule_id,
        failure_code=validation.validation_record.failure_code,
        failed_metric_state=MetricState.INADMISSIBLE.value,
        validated_result_authorized=validation.validated_result is not None,
        admissible_evidence_authorized=False,
        observed={
            "submitted_result_id": tampered.result_id,
            "submitted_value": str(tampered.value),
            "validation_status": validation.validation_record.status.value,
            "validation_rule_id": validation.validation_record.validation_rule_id,
            "failure_code": validation.validation_record.failure_code,
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
