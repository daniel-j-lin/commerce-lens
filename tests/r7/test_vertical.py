from datetime import date, timedelta
from decimal import Decimal

import duckdb

from commerce_lens.contracts.common import ArtifactReference, PeriodDefinition, ScopeDefinition
from commerce_lens.contracts.evidence import CanonicalDatasetReference
from commerce_lens.contracts.populations import PopulationDefinition, PopulationPeriodRole
from commerce_lens.contracts.r7 import DiagnosticTestRequest, R7ValidationStatus, diagnostic_test_request_fingerprint
from commerce_lens.engine.r7_execution import execute_r7_diagnostic
from commerce_lens.evidence.identifiers import sha256_file, stable_content_id
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.validation.r7_validator import validate_r7_result
from tests.engine.test_r7_execution import _request


def _population(role, period):
    return PopulationDefinition(
        population_id=f"population:{'b' if role is PopulationPeriodRole.BASELINE else 'c'}",
        canonical_dataset_ref_id="canonical:1", dataset_ref_id="dataset:1", period=period,
        period_role=role, currency_basis_ref="currency:USD", scope=ScopeDefinition(scope_id="scope:1"),
        population_fingerprint="a" * 64,
    )


def test_primary_vertical_executes_recomputes_validates_and_preserves_semantic_result(tmp_path):
    store = ArtifactStore(tmp_path / "runtime"); store.ensure_layout()
    parquet = store.safe_path("canonical", "r7-primary.parquet")
    connection = duckdb.connect(":memory:")
    connection.execute("CREATE TABLE sales(order_date DATE, product_id VARCHAR, line_revenue DECIMAL(18,2), eligibility_status VARCHAR)")
    products = tuple(f"P{i}" for i in range(10))
    rows = []
    for week in range(8):
        active = products[:10-week]; monday = date(2026, 1, 5) + timedelta(days=week*7)
        total = Decimal(800 - week*100)
        rows.extend((monday, product, total if index == 0 else Decimal(0), "Eligible") for index, product in enumerate(active))
    connection.executemany("INSERT INTO sales VALUES (?, ?, ?, ?)", rows)
    connection.execute("COPY sales TO ? (FORMAT PARQUET)", [str(parquet)])
    fingerprint = sha256_file(parquet)
    artifact = ArtifactReference(
        artifact_id=stable_content_id("art", fingerprint), path="canonical/r7-primary.parquet",
        fingerprint=fingerprint, media_type="application/vnd.apache.parquet", size_bytes=parquet.stat().st_size,
    )
    canonical = CanonicalDatasetReference(
        canonical_dataset_id="canonical:1", source_dataset_id="dataset:1", canonical_schema_version="1",
        content_fingerprint=fingerprint, artifact=artifact, row_count=len(rows),
    )
    baseline_period = PeriodDefinition(period_id="period:b", label="Baseline", start_date=date(2026,1,5), end_date=date(2026,2,1), date_convention_ref="canonical:order_date")
    comparison_period = PeriodDefinition(period_id="period:c", label="Comparison", start_date=date(2026,2,2), end_date=date(2026,3,1), date_convention_ref="canonical:order_date")
    baseline = _population(PopulationPeriodRole.BASELINE, baseline_period)
    comparison = _population(PopulationPeriodRole.COMPARISON, comparison_period)
    data = _request().model_dump(mode="python")
    data.update(canonical_dataset_fingerprint=fingerprint, request_fingerprint="0"*64, test_request_id="pending")
    request_fp = diagnostic_test_request_fingerprint(data)
    data.update(request_fingerprint=request_fp, test_request_id=stable_content_id("r7req", request_fp))
    request = DiagnosticTestRequest(**data)

    first = execute_r7_diagnostic(request=request, canonical_dataset=canonical, baseline_population=baseline, comparison_population=comparison, artifact_store=store)
    validated = validate_r7_result(request=request, executed_result=first.executed_result, canonical_dataset=canonical, baseline_population=baseline, comparison_population=comparison, artifact_store=store)
    second = execute_r7_diagnostic(request=request, canonical_dataset=canonical, baseline_population=baseline, comparison_population=comparison, artifact_store=store)

    assert first.executed_result.spearman_rho == -1.0
    assert validated.validation_record.status is R7ValidationStatus.PASSED
    assert validated.validated_result is not None
    assert validated.validated_result.validated_result_id != first.executed_result.executed_result_id
    assert first.execution_record.execution_event_id != second.execution_record.execution_event_id
    assert first.executed_result.result_fingerprint == second.executed_result.result_fingerprint
