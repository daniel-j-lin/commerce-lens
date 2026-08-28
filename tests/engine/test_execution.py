import csv
import sqlite3
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import Workbook

from commerce_lens.canonical import (
    CanonicalizationRequest,
    EligibilityMode,
    EligibilityState,
    EligibilityValueMapping,
    canonicalize_dataset,
    identity_mapping,
)
from commerce_lens.contracts.common import (
    FailureDetail,
    FailureStage,
    GroupingDimension,
    MetricState,
    PeriodDefinition,
    ScopeDefinition,
    ScopeFilter,
    SourceType,
)
from commerce_lens.contracts.evidence import MetricReference
from commerce_lens.contracts.plans import PlanMetricNode
from commerce_lens.contracts.requests import AnalysisRequest
from commerce_lens.contracts.sufficiency import DataSufficiencyResult, MetricEligibility, SufficiencyState
from commerce_lens.engine import MetricExecutionError, execute_plan
from commerce_lens.engine.plan_builder import build_execution_plan
from commerce_lens.intake.registry import DatasetRegistry
from commerce_lens.metrics import METRIC_DEFINITION_VERSION, METRIC_REGISTRY_VERSION
from commerce_lens.persistence.artifact_store import ArtifactStore


def test_revenue_executes_single_and_multiple_eligible_lines_with_decimal_authority(tmp_path) -> None:
    plan, canonical, store = _execution_inputs(
        tmp_path,
        ("revenue",),
        [
            _row(order_id="o1", order_line_id="l1", order_date="2026-01-01", line_revenue="10.10"),
            _row(order_id="o2", order_line_id="l1", order_date="2026-01-02", line_revenue="0"),
            _row(order_id="o3", order_line_id="l1", order_date="2026-01-03", line_revenue="99.99"),
            _row(
                order_id="o4",
                order_line_id="l1",
                order_date="2026-01-01",
                line_revenue="100.00",
                eligibility_status="cancelled",
            ),
        ],
    )

    outcome = execute_plan(plan, canonical, store)

    baseline = _result(outcome, "revenue", "baseline")
    comparison = _result(outcome, "revenue", "comparison")
    assert baseline.value == Decimal("10.10")
    assert comparison.value == Decimal("99.99")
    assert isinstance(baseline.value, Decimal)
    assert not isinstance(baseline.value, float)


def test_revenue_uses_line_revenue_not_quantity_times_unit_price(tmp_path) -> None:
    plan, canonical, store = _execution_inputs(
        tmp_path,
        ("revenue",),
        [_row(quantity="10", line_revenue="7.25", unit_price="99.99")],
    )

    result = _result(execute_plan(plan, canonical, store), "revenue", "baseline")

    assert result.value == Decimal("7.25")


def test_revenue_preserves_high_scale_decimal_and_repeatability(tmp_path) -> None:
    plan, canonical, store = _execution_inputs(
        tmp_path,
        ("revenue",),
        [
            _row(order_id="o1", order_line_id="l1", line_revenue="10.123456789123"),
            _row(order_id="o1", order_line_id="l2", line_revenue="0.000000000007"),
        ],
    )

    first = execute_plan(plan, canonical, store)
    second = execute_plan(plan, canonical, store)

    assert _result(first, "revenue", "baseline").value == Decimal("10.123456789130")
    assert _result(first, "revenue", "baseline").value == _result(second, "revenue", "baseline").value
    assert _result(first, "revenue", "baseline").result_id == _result(second, "revenue", "baseline").result_id


def test_orders_count_distinct_eligible_orders_not_lines(tmp_path) -> None:
    plan, canonical, store = _execution_inputs(
        tmp_path,
        ("orders",),
        [
            _row(order_id="o1", order_line_id="l1", line_revenue="10.00"),
            _row(order_id="o1", order_line_id="l2", line_revenue="5.00"),
            _row(order_id="o2", order_line_id="l1", line_revenue="0"),
            _row(order_id="o3", order_line_id="l1", eligibility_status="cancelled"),
            _row(order_id="o4", order_line_id="l1", order_date="2026-01-03"),
        ],
    )

    outcome = execute_plan(plan, canonical, store)

    baseline = _result(outcome, "orders", "baseline")
    comparison = _result(outcome, "orders", "comparison")
    assert baseline.value == 2
    assert comparison.value == 1
    assert isinstance(baseline.value, int)
    assert not isinstance(baseline.value, float)


def test_aov_uses_executed_revenue_and_orders_dependencies(tmp_path) -> None:
    plan, canonical, store = _execution_inputs(
        tmp_path,
        ("aov",),
        [
            _row(order_id="o1", order_line_id="l1", line_revenue="10.00"),
            _row(order_id="o1", order_line_id="l2", line_revenue="5.00"),
            _row(order_id="o2", order_line_id="l1", line_revenue="15.00"),
            _row(order_id="o3", order_line_id="l1", order_date="2026-01-03", line_revenue="10.00"),
        ],
    )

    outcome = execute_plan(plan, canonical, store)
    baseline = _result(outcome, "aov", "baseline")
    comparison = _result(outcome, "aov", "comparison")
    baseline_record = _record(outcome, "aov", "baseline")

    assert baseline.value == Decimal("15.00")
    assert comparison.value == Decimal("10.00")
    assert isinstance(baseline.value, Decimal)
    assert baseline_record.operation["method"] == "python_decimal_dependency_arithmetic"
    assert "revenue_result_ref" in baseline_record.operation
    assert "orders_result_ref" in baseline_record.operation


def test_aov_zero_revenue_with_orders_is_decimal_zero(tmp_path) -> None:
    plan, canonical, store = _execution_inputs(
        tmp_path,
        ("aov",),
        [_row(order_id="o1", order_line_id="l1", line_revenue="0")],
    )

    result = _result(execute_plan(plan, canonical, store), "aov", "baseline")

    assert result.value == Decimal("0")
    assert isinstance(result.value, Decimal)


def test_aov_orders_zero_is_undefined_not_execution_failure(tmp_path) -> None:
    plan, canonical, store = _execution_inputs(
        tmp_path,
        ("aov",),
        [_row(order_id="o1", order_line_id="l1", eligibility_status="cancelled")],
    )

    outcome = execute_plan(plan, canonical, store)
    result = _result(outcome, "aov", "baseline")
    record = _record(outcome, "aov", "baseline")

    assert result.value is None
    assert result.metric_state is MetricState.UNDEFINED
    assert result.undefined_reason == "orders_equals_zero"
    assert result.execution_status.value == "completed"
    assert record.status.value == "completed"


def test_aov_exact_decimal_division_does_not_use_float(tmp_path) -> None:
    plan, canonical, store = _execution_inputs(
        tmp_path,
        ("aov",),
        [
            _row(order_id="o1", order_line_id="l1", line_revenue="1"),
            _row(order_id="o2", order_line_id="l1", line_revenue="0"),
            _row(order_id="o3", order_line_id="l1", line_revenue="0"),
        ],
    )

    result = _result(execute_plan(plan, canonical, store), "aov", "baseline")

    assert result.value == Decimal("0.3333333333333333333333333333")
    assert isinstance(result.value, Decimal)


def test_executable_revenue_and_orders_execute_while_blocked_nodes_do_not(tmp_path) -> None:
    revenue_plan, canonical, store = _execution_inputs(tmp_path, ("revenue",), [_row()])
    revenue_outcome = execute_plan(revenue_plan, canonical, store)
    assert _result(revenue_outcome, "revenue", "baseline").value == Decimal("10.00")

    blocked_revenue = revenue_plan.model_copy(
        update={
            "ordered_metrics": tuple(
                node.model_copy(
                    update={
                        "planning_state": "blocked",
                        "authorized_requested_metric_refs": (),
                        "failure_details": (_blocked_failure(node),),
                    }
                )
                for node in revenue_plan.ordered_metrics
            ),
            "eligible_requested_metric_refs": (),
            "blocked_metric_refs": ("revenue",),
        }
    )
    assert execute_plan(blocked_revenue, canonical, store).executed_results == ()

    orders_plan, canonical, store = _execution_inputs(tmp_path, ("orders",), [_row(order_id="o2")], filename="orders.csv")
    orders_outcome = execute_plan(orders_plan, canonical, store)
    assert _result(orders_outcome, "orders", "baseline").value == 1

    blocked_orders = orders_plan.model_copy(
        update={
            "ordered_metrics": tuple(
                node.model_copy(
                    update={
                        "planning_state": "blocked",
                        "authorized_requested_metric_refs": (),
                        "failure_details": (_blocked_failure(node),),
                    }
                )
                for node in orders_plan.ordered_metrics
            ),
            "eligible_requested_metric_refs": (),
            "blocked_metric_refs": ("orders",),
        }
    )
    assert execute_plan(blocked_orders, canonical, store).execution_records == ()


def test_blocked_aov_chain_does_not_execute_hidden_dependencies(tmp_path) -> None:
    plan, canonical, store = _execution_inputs(
        tmp_path,
        ("aov",),
        [_row()],
        ineligible={"aov": ()},
        filename="blocked_aov.csv",
    )

    outcome = execute_plan(plan, canonical, store)

    assert outcome.execution_records == ()
    assert outcome.executed_results == ()


def test_aov_malformed_dependency_results_fail_closed(tmp_path) -> None:
    plan, canonical, store = _execution_inputs(tmp_path, ("aov",), [_row()])
    aov_node = next(node for node in plan.ordered_metrics if node.metric_ref == "aov")
    malformed_aov = aov_node.model_copy(update={"dependency_node_ids": aov_node.dependency_node_ids[:1]})
    malformed_plan = plan.model_copy(
        update={
            "ordered_metrics": tuple(
                malformed_aov if node.node_id == aov_node.node_id else node
                for node in plan.ordered_metrics
            ),
        }
    )

    outcome = execute_plan(malformed_plan, canonical, store)
    failed_aov = [record for record in outcome.execution_records if record.metric_refs == ("aov",)]

    assert failed_aov
    assert failed_aov[0].status.value == "failed"
    assert "AOV requires executed Revenue and Orders" in failed_aov[0].failure_details[0].reason
    assert not any(
        result.metric_ref == "aov" and result.period_ref == aov_node.period_refs[0]
        for result in outcome.executed_results
    )


def test_unsupported_p4_metric_node_fails_closed_without_executed_result(tmp_path) -> None:
    plan, canonical, store = _execution_inputs(
        tmp_path,
        ("revenue_change",),
        [
            _row(order_id="o1", order_date="2026-01-01", line_revenue="10.00"),
            _row(order_id="o2", order_date="2026-01-03", line_revenue="11.00"),
        ],
    )

    outcome = execute_plan(plan, canonical, store)
    failed = [record for record in outcome.execution_records if record.metric_refs == ("revenue_change",)]

    assert failed
    assert failed[0].status.value == "failed"
    assert "unsupported P4-001 Metric execution" in failed[0].failure_details[0].reason
    assert not any(result.metric_ref == "revenue_change" for result in outcome.executed_results)


def test_malformed_executable_authorization_fails_before_execution(tmp_path) -> None:
    plan, canonical, store = _execution_inputs(tmp_path, ("revenue",), [_row()])
    bad_node = plan.ordered_metrics[0].model_copy(update={"authorized_requested_metric_refs": ()})
    bad_plan = plan.model_copy(update={"ordered_metrics": (bad_node, *plan.ordered_metrics[1:])})

    with pytest.raises(Exception):
        execute_plan(bad_plan, canonical, store)


def test_provenance_records_plan_node_metric_dataset_population_executor_operation_and_result(tmp_path) -> None:
    plan, canonical, store = _execution_inputs(
        tmp_path,
        ("revenue",),
        [_row()],
        scope=ScopeDefinition(
            scope_id="usd_only",
            filters=(ScopeFilter(field="currency", operator="equals", value="USD"),),
        ),
    )

    outcome = execute_plan(plan, canonical, store)
    record = _record(outcome, "revenue", "baseline")

    assert record.plan_id == plan.plan_id
    assert record.plan_fingerprint == plan.plan_fingerprint
    assert record.plan_node_id
    assert record.metric_refs == ("revenue",)
    assert record.metric_definition_version == METRIC_DEFINITION_VERSION
    assert record.canonical_dataset_ref_ids == (canonical.canonical_dataset_id,)
    assert record.canonical_dataset_fingerprints == (canonical.content_fingerprint,)
    assert record.population_refs
    assert record.population_fingerprints
    assert record.executor_id == "commerce_lens_duckdb_reference_executor"
    assert record.executor_version == "p4_001_v1"
    assert record.duckdb_version
    assert record.operation["method"] == "duckdb_sql"
    assert "SUM(line_revenue)" in record.operation["sql"]
    assert record.result_ref == _result(outcome, "revenue", "baseline").result_id
    assert not hasattr(record, "validation_passed")
    assert not hasattr(record, "admissible_evidence_ref")


def test_missing_or_mismatched_canonical_artifact_fails_closed(tmp_path) -> None:
    plan, canonical, store = _execution_inputs(tmp_path, ("revenue",), [_row()])
    missing = canonical.model_copy(
        update={"artifact": canonical.artifact.model_copy(update={"path": "canonical/missing.parquet"})}
    )

    with pytest.raises(MetricExecutionError):
        execute_plan(plan, missing, store)


def test_csv_xlsx_sqlite_converge_through_canonical_artifact_execution(tmp_path) -> None:
    rows = [
        _row(order_id="o1", line_revenue="10.25"),
        _row(order_id="o2", order_date="2026-01-03", line_revenue="20.50"),
    ]
    outcomes = []
    for source_type in ("csv", "xlsx", "sqlite"):
        plan, canonical, store = _execution_inputs(
            tmp_path,
            ("revenue", "orders", "aov"),
            rows,
            filename=f"converge.{source_type}",
            source_type=source_type,
        )
        outcomes.append(execute_plan(plan, canonical, store))

    observed = [
        (
            _result(outcome, "revenue", "baseline").value,
            _result(outcome, "orders", "baseline").value,
            _result(outcome, "aov", "comparison").value,
        )
        for outcome in outcomes
    ]
    assert observed == [(Decimal("10.25"), 1, Decimal("20.50"))] * 3


def _execution_inputs(
    tmp_path: Path,
    metrics: tuple[str, ...],
    rows: list[dict[str, str]],
    *,
    ineligible: dict[str, tuple[FailureDetail, ...]] | None = None,
    filename: str = "orders.csv",
    source_type: str = "csv",
    scope: ScopeDefinition = ScopeDefinition(scope_id="all_eligible"),
):
    dataset, store = _registered_source(tmp_path, rows, filename=filename, source_type=source_type)
    canonicalization = canonicalize_dataset(dataset, _canonicalization_request(dataset), store)
    assert canonicalization.canonical_dataset is not None
    request = _request(metrics, dataset.dataset_id, scope=scope)
    plan = build_execution_plan(
        request,
        _sufficiency(
            request,
            canonicalization.canonical_dataset.canonical_dataset_id,
            ineligible=ineligible,
        ),
    )
    return plan, canonicalization.canonical_dataset, store


def _request(metrics: tuple[str, ...], dataset_ref_id: str, *, scope: ScopeDefinition) -> AnalysisRequest:
    return AnalysisRequest(
        canonical_business_question_id="canonical_revenue_change",
        metrics=tuple(
            MetricReference(metric_id=metric_id, definition_version=METRIC_DEFINITION_VERSION)
            for metric_id in metrics
        ),
        baseline_period=PeriodDefinition(
            period_id="baseline",
            label="Baseline",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
            date_convention_ref="order_date_utc",
        ),
        comparison_period=PeriodDefinition(
            period_id="comparison",
            label="Comparison",
            start_date=date(2026, 1, 3),
            end_date=date(2026, 1, 4),
            date_convention_ref="order_date_utc",
        ),
        scope=scope,
        grouping=GroupingDimension.NONE,
        dataset_ref_id=dataset_ref_id,
        canonical_schema_version="canonical_mvp_v1",
        metric_registry_version=METRIC_REGISTRY_VERSION,
    )


def _sufficiency(
    request: AnalysisRequest,
    canonical_dataset_ref_id: str,
    *,
    ineligible: dict[str, tuple[FailureDetail, ...]] | None = None,
) -> DataSufficiencyResult:
    ineligible = ineligible or {}
    return DataSufficiencyResult(
        sufficiency_id=f"suff_{request.request_id}",
        request_id=request.request_id,
        dataset_ref_id=request.dataset_ref_id,
        canonical_dataset_ref_id=canonical_dataset_ref_id,
        metric_eligibility=tuple(
            MetricEligibility(
                metric_ref=metric.metric_id,
                eligible=metric.metric_id not in ineligible,
                metric_state=MetricState.INADMISSIBLE if metric.metric_id in ineligible else None,
                failure_details=ineligible.get(metric.metric_id, ()),
            )
            for metric in request.metrics
        ),
        state=SufficiencyState.PARTIAL if ineligible else SufficiencyState.SUFFICIENT,
    )


def _canonicalization_request(dataset) -> CanonicalizationRequest:
    headers = _headers()
    return CanonicalizationRequest(
        source_dataset_id=dataset.dataset_id,
        mapping=identity_mapping(headers, require_eligibility=True),
        eligibility_mode=EligibilityMode.EXPLICIT_STATUS_MAPPING,
        eligibility_value_mapping=(
            EligibilityValueMapping(source_value="paid", normalized_status=EligibilityState.ELIGIBLE),
            EligibilityValueMapping(source_value="cancelled", normalized_status=EligibilityState.EXCLUDED),
        ),
    )


def _registered_source(
    tmp_path: Path,
    rows: list[dict[str, str]],
    *,
    filename: str,
    source_type: str,
):
    path = tmp_path / filename
    if source_type == "csv":
        _write_csv(path, rows)
        selected_sheet = None
        selected_table = None
        source = SourceType.CSV
    elif source_type == "xlsx":
        _write_xlsx(path, rows)
        selected_sheet = "Orders"
        selected_table = None
        source = SourceType.EXCEL_XLSX
    elif source_type == "sqlite":
        _write_sqlite(path, rows)
        selected_sheet = None
        selected_table = "orders"
        source = SourceType.SQLITE
    else:
        raise AssertionError(f"unknown source_type {source_type}")
    store = ArtifactStore(tmp_path / f"runtime_{filename}")
    registry = DatasetRegistry(store)
    return registry.register_source(path, source, selected_sheet=selected_sheet, selected_table=selected_table), store


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=_headers())
        writer.writeheader()
        writer.writerows([{key: row.get(key, "") for key in _headers()} for row in rows])


def _write_xlsx(path: Path, rows: list[dict[str, str]]) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Orders"
    sheet.append(_headers())
    for row in rows:
        sheet.append([row.get(key, "") for key in _headers()])
    workbook.save(path)


def _write_sqlite(path: Path, rows: list[dict[str, str]]) -> None:
    conn = sqlite3.connect(path)
    with conn:
        columns = ", ".join(f"{header} TEXT" for header in _headers())
        conn.execute(f"CREATE TABLE orders ({columns})")
        placeholders = ", ".join("?" for _ in _headers())
        conn.executemany(
            f"INSERT INTO orders VALUES ({placeholders})",
            [[row.get(key, "") for key in _headers()] for row in rows],
        )
    conn.close()


def _headers() -> tuple[str, ...]:
    return (
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


def _row(**overrides: str) -> dict[str, str]:
    row = {
        "order_id": "o1",
        "order_line_id": "l1",
        "order_date": "2026-01-01",
        "product_id": "p1",
        "product_name": "Tea",
        "category_id": "c1",
        "category_name": "Drinks",
        "quantity": "1",
        "line_revenue": "10.00",
        "currency": "USD",
        "unit_price": "",
        "eligibility_status": "paid",
    }
    row.update(overrides)
    return row


def _result(outcome, metric_ref: str, period_ref: str):
    return next(
        result
        for result in outcome.executed_results
        if result.metric_ref == metric_ref and result.period_ref == period_ref
    )


def _record(outcome, metric_ref: str, period_ref: str):
    return next(
        record
        for record in outcome.execution_records
        if record.metric_refs == (metric_ref,) and record.period_refs == (period_ref,)
    )


def _blocked_failure(node: PlanMetricNode) -> FailureDetail:
    return FailureDetail(
        stage=FailureStage.PLANNING,
        reason="test blocked by Data Sufficiency",
        target_ref=node.node_id,
        governing_ref="tasks:P3-001",
        dependency_scope=node.metric_ref,
        independent_chains_may_continue=True,
    )
