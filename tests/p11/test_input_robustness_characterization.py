from __future__ import annotations

import csv
import contextlib
import importlib.util
import io
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import Workbook

from commerce_lens.canonical.mapping import CanonicalFieldMapping, CanonicalMapping
from commerce_lens.contracts.common import MetricState, PeriodDefinition, SourceType
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.skill.integration import (
    PublicAnalysisIntent,
    PublicQuestionClass,
    PublicSourceSelection,
    run_public_analysis,
)


CANONICAL_HEADERS = (
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

BASE_ROWS = (
    {
        "order_id": "q3-o1",
        "order_line_id": "q3-l1",
        "order_date": "2026-07-15",
        "product_id": "p1",
        "product_name": "Widget",
        "category_id": "c1",
        "category_name": "Widgets",
        "quantity": "1",
        "line_revenue": "120.00",
        "currency": "USD",
        "unit_price": "120.00",
        "eligibility_status": "paid",
    },
    {
        "order_id": "q4-o1",
        "order_line_id": "q4-l1",
        "order_date": "2026-10-15",
        "product_id": "p1",
        "product_name": "Widget",
        "category_id": "c1",
        "category_name": "Widgets",
        "quantity": "1",
        "line_revenue": "100.00",
        "currency": "USD",
        "unit_price": "100.00",
        "eligibility_status": "paid",
    },
)

HUMAN_HEADERS = {
    "order_id": "Order ID",
    "order_line_id": "Order Line ID",
    "order_date": "Order Date",
    "product_id": "Product ID",
    "product_name": "Product Name",
    "category_id": "Category ID",
    "category_name": "Category Name",
    "quantity": "Quantity",
    "line_revenue": "Revenue",
    "currency": "Currency",
    "unit_price": "Unit Price",
    "eligibility_status": "Order Status",
}

CAMEL_HEADERS = {
    "order_id": "orderId",
    "order_line_id": "orderLineId",
    "order_date": "orderDate",
    "product_id": "productId",
    "product_name": "productName",
    "category_id": "categoryId",
    "category_name": "categoryName",
    "quantity": "quantity",
    "line_revenue": "lineRevenue",
    "currency": "currency",
    "unit_price": "unitPrice",
    "eligibility_status": "eligibilityStatus",
}

EXPORT_HEADERS = {
    "order_id": "Order Number",
    "order_line_id": "Line Item ID",
    "order_date": "Created At",
    "product_id": "SKU",
    "product_name": "Product",
    "category_id": "Product Type",
    "category_name": "Product Type Name",
    "quantity": "Qty",
    "line_revenue": "Total Sales",
    "currency": "Currency",
    "unit_price": "Price",
    "eligibility_status": "Financial Status",
}

AMBIGUOUS_HEADERS = {
    "order_id": "ID",
    "order_line_id": "Line ID",
    "order_date": "Date",
    "product_id": "Product ID",
    "product_name": "Product",
    "category_id": "Category ID",
    "category_name": "Category",
    "quantity": "Qty",
    "line_revenue": "Total",
    "currency": "Currency",
    "unit_price": "Price",
    "eligibility_status": "Status",
}

HUMAN_ROWS = tuple({HUMAN_HEADERS[key]: value for key, value in row.items()} for row in BASE_ROWS)
CAMEL_ROWS = tuple({CAMEL_HEADERS[key]: value for key, value in row.items()} for row in BASE_ROWS)
EXPORT_ROWS = tuple({EXPORT_HEADERS[key]: value for key, value in row.items()} for row in BASE_ROWS)
AMBIGUOUS_ROWS = tuple({AMBIGUOUS_HEADERS[key]: value for key, value in row.items()} for row in BASE_ROWS)
MISSING_REVENUE_ROWS = tuple({key: value for key, value in row.items() if key != "line_revenue"} for row in BASE_ROWS)
MISSING_REVENUE_HEADERS = tuple(header for header in CANONICAL_HEADERS if header != "line_revenue")


@dataclass(frozen=True)
class Observed:
    supported: bool
    value: object | None
    blocked: bool
    clarification_required: tuple[str, ...]
    limitations: tuple[str, ...]
    metric_state: MetricState | None
    crashed: bool = False


def test_p11_canonical_baseline_control_csv_passes(tmp_path: Path) -> None:
    source = _write_csv(tmp_path / "canonical.csv", BASE_ROWS)

    observed = _observe(source, metric="revenue_change")

    assert observed.supported is True
    assert observed.value == Decimal("-20.00")
    assert observed.metric_state is MetricState.VALID
    assert observed.crashed is False


@pytest.mark.parametrize(
    ("variant_id", "rename_map"),
    (
        ("human_readable_headers", HUMAN_HEADERS),
        ("camelcase_api_headers", CAMEL_HEADERS),
        ("commerce_export_headers", EXPORT_HEADERS),
        ("ambiguous_headers", AMBIGUOUS_HEADERS),
    ),
)
def test_p11_noncanonical_csv_headers_fail_closed_without_automatic_mapping(
    tmp_path: Path,
    variant_id: str,
    rename_map: dict[str, str],
) -> None:
    rows_by_variant = {
        "human_readable_headers": HUMAN_ROWS,
        "camelcase_api_headers": CAMEL_ROWS,
        "commerce_export_headers": EXPORT_ROWS,
        "ambiguous_headers": AMBIGUOUS_ROWS,
    }
    source = _write_csv(tmp_path / f"{variant_id}.csv", rows_by_variant[variant_id], headers=tuple(rename_map.values()))

    observed = _observe(source, metric="revenue_change")

    assert observed.supported is False
    assert observed.blocked is True or observed.clarification_required
    assert observed.crashed is False
    assert any("required canonical field" in item for item in observed.limitations) or observed.clarification_required


def test_p11_missing_revenue_field_csv_fails_closed_for_revenue_change(tmp_path: Path) -> None:
    headers = tuple(header for header in CANONICAL_HEADERS if header != "line_revenue")
    rows = tuple({key: value for key, value in row.items() if key != "line_revenue"} for row in BASE_ROWS)
    source = _write_csv(tmp_path / "missing_revenue.csv", rows, headers=headers)

    observed = _observe(source, metric="revenue_change")

    assert observed.supported is False
    assert observed.blocked is True or observed.clarification_required
    assert observed.crashed is False
    assert any("line_revenue" in item for item in observed.limitations) or any(
        "line_revenue" in item for item in observed.clarification_required
    )


@pytest.mark.parametrize("metric", ("orders", "aov"))
def test_p11_missing_order_identifier_csv_fails_closed_for_orders_and_aov(tmp_path: Path, metric: str) -> None:
    headers = tuple(header for header in CANONICAL_HEADERS if header != "order_id")
    rows = tuple({key: value for key, value in row.items() if key != "order_id"} for row in BASE_ROWS)
    source = _write_csv(tmp_path / f"missing_order_id_{metric}.csv", rows, headers=headers)

    observed = _observe(source, metric=metric)

    assert observed.supported is False
    assert observed.blocked is True or observed.clarification_required
    assert observed.crashed is False
    assert any("order_id" in item for item in observed.limitations) or any(
        "order_id" in item for item in observed.clarification_required
    )


def test_p11_missing_eligibility_field_csv_fails_closed_even_when_status_matters(tmp_path: Path) -> None:
    rows = (
        BASE_ROWS[0],
        {**BASE_ROWS[1], "eligibility_status": "cancelled", "line_revenue": "999.00"},
    )
    headers = tuple(header for header in CANONICAL_HEADERS if header != "eligibility_status")
    source = _write_csv(
        tmp_path / "missing_eligibility.csv",
        tuple({key: value for key, value in row.items() if key != "eligibility_status"} for row in rows),
        headers=headers,
    )

    observed = _observe(source, metric="revenue_change")

    assert observed.supported is False
    assert observed.blocked is True or observed.clarification_required
    assert observed.crashed is False
    assert any("eligibility_status" in item for item in observed.limitations) or any(
        "eligibility_status" in item for item in observed.clarification_required
    )


@pytest.mark.parametrize(
    ("date_text", "supported"),
    (
        ("2026-07-15", True),
        ("07/15/2026", False),
        ("15/07/2026", False),
        ("Jul 15 2026", True),
        ("2026-07-15T00:00:00", True),
    ),
)
def test_p11_csv_date_format_characterization(tmp_path: Path, date_text: str, supported: bool) -> None:
    rows = ({**BASE_ROWS[0], "order_date": date_text}, BASE_ROWS[1])
    source = _write_csv(tmp_path / f"date_{date_text.replace('/', '_').replace(':', '_')}.csv", rows)

    observed = _observe(source, metric="revenue_change")

    assert observed.supported is supported
    assert observed.crashed is False


@pytest.mark.parametrize(
    ("q3_value", "expected_value", "supported"),
    (
        ("120.00", Decimal("-20.00"), True),
        ("120", Decimal("-20"), True),
        ("$120.00", Decimal("-20.00"), True),
        ("1,200.00", Decimal("-1100.00"), True),
        ("USD 120.00", Decimal("-20.00"), True),
    ),
)
def test_p11_csv_monetary_format_characterization(
    tmp_path: Path,
    q3_value: str,
    expected_value: Decimal | None,
    supported: bool,
) -> None:
    rows = ({**BASE_ROWS[0], "line_revenue": q3_value}, BASE_ROWS[1])
    source = _write_csv(tmp_path / "money.csv", rows)

    observed = _observe(source, metric="revenue_change")

    assert observed.supported is supported
    assert observed.value == expected_value
    assert observed.crashed is False


@pytest.mark.parametrize(
    ("variant_id", "headers"),
    (
        ("uppercase", tuple(header.upper() for header in CANONICAL_HEADERS)),
        ("title_underscore", tuple("_".join(part.title() for part in header.split("_")) for header in CANONICAL_HEADERS)),
        ("space_revenue_only", tuple("line revenue" if header == "line_revenue" else header for header in CANONICAL_HEADERS)),
    ),
)
def test_p11_case_and_whitespace_header_variations_csv(
    tmp_path: Path,
    variant_id: str,
    headers: tuple[str, ...],
) -> None:
    rename_map = dict(zip(CANONICAL_HEADERS, headers, strict=True))
    source = _write_csv(tmp_path / f"{variant_id}.csv", _renamed_rows(rename_map), headers=headers)

    observed = _observe(source, metric="revenue_change")

    assert observed.supported is False
    assert observed.blocked is True or observed.clarification_required
    assert observed.crashed is False


def test_p11_extra_irrelevant_columns_do_not_change_csv_output(tmp_path: Path) -> None:
    rows = tuple(
        {
            **row,
            "customer_email": "buyer@example.com",
            "notes": "ignored",
            "shipping_method": "ground",
            "campaign": "fall",
            "internal_comment": "synthetic p11 field",
        }
        for row in BASE_ROWS
    )
    source = _write_csv(tmp_path / "extra_columns.csv", rows, headers=tuple(rows[0].keys()))

    observed = _observe(source, metric="revenue_change")

    assert observed.supported is True
    assert observed.value == Decimal("-20.00")
    assert observed.crashed is False


def test_p11_duplicate_conflicting_semantic_columns_csv_uses_exact_canonical_authority(
    tmp_path: Path,
) -> None:
    rows = tuple({**row, "Revenue": "9999.00", "Created At": "2000-01-01"} for row in BASE_ROWS)
    source = _write_csv(tmp_path / "duplicate_semantics.csv", rows, headers=tuple(rows[0].keys()))

    observed = _observe(source, metric="revenue_change")

    assert observed.supported is True
    assert observed.value == Decimal("-20.00")
    assert observed.crashed is False


@pytest.mark.parametrize(
    ("variant_id", "rows", "headers", "supported"),
    (
        ("canonical_xlsx", BASE_ROWS, CANONICAL_HEADERS, True),
        ("human_readable_xlsx", HUMAN_ROWS, tuple(HUMAN_HEADERS.values()), False),
        ("missing_revenue_xlsx", MISSING_REVENUE_ROWS, MISSING_REVENUE_HEADERS, False),
        ("ambiguous_xlsx", AMBIGUOUS_ROWS, tuple(AMBIGUOUS_HEADERS.values()), False),
    ),
)
def test_p11_selected_xlsx_header_variants(
    tmp_path: Path,
    variant_id: str,
    rows: tuple[dict[str, object], ...],
    headers: tuple[str, ...],
    supported: bool,
) -> None:
    source = _write_xlsx(tmp_path / f"{variant_id}.xlsx", rows, headers=headers)

    observed = _observe(source, metric="revenue_change", source_type=SourceType.EXCEL_XLSX, selected_sheet="Orders")

    assert observed.supported is supported
    if not supported:
        assert observed.blocked is True or observed.clarification_required
    assert observed.crashed is False


def test_p11_xlsx_native_date_is_accepted_but_timestamp_is_rejected(tmp_path: Path) -> None:
    native_date = _write_xlsx(
        tmp_path / "native_date.xlsx",
        ({**BASE_ROWS[0], "order_date": date(2026, 7, 15)}, BASE_ROWS[1]),
    )
    timestamp = _write_xlsx(
        tmp_path / "timestamp.xlsx",
        ({**BASE_ROWS[0], "order_date": datetime(2026, 7, 15, 1, 2, 3)}, BASE_ROWS[1]),
    )

    assert _observe(native_date, metric="revenue_change", source_type=SourceType.EXCEL_XLSX, selected_sheet="Orders").supported is True
    assert _observe(timestamp, metric="revenue_change", source_type=SourceType.EXCEL_XLSX, selected_sheet="Orders").supported is False


def test_p11_explicit_authorized_mapping_makes_human_headers_succeed_at_engine_level(tmp_path: Path) -> None:
    source = _write_csv(tmp_path / "human_authorized.csv", _renamed_rows(HUMAN_HEADERS), headers=tuple(HUMAN_HEADERS.values()))
    mapping = CanonicalMapping(
        mapping_id="p11_explicit_authorized_human_headers",
        entries=tuple(
            CanonicalFieldMapping(canonical_field=canonical, source_field=source_field)
            for canonical, source_field in HUMAN_HEADERS.items()
        ),
    )

    observed = _observe(source, metric="revenue_change", mapping=mapping)

    assert observed.supported is True
    assert observed.value == Decimal("-20.00")
    assert observed.crashed is False


@pytest.mark.parametrize(
    ("variant_id", "rows", "headers", "expected_supported"),
    (
        ("canonical", BASE_ROWS, CANONICAL_HEADERS, True),
        ("human_readable", HUMAN_ROWS, tuple(HUMAN_HEADERS.values()), False),
        ("ambiguous", AMBIGUOUS_ROWS, tuple(AMBIGUOUS_HEADERS.values()), False),
        ("missing_revenue", MISSING_REVENUE_ROWS, MISSING_REVENUE_HEADERS, False),
    ),
)
def test_p11_runner_natural_language_representative_subset(
    tmp_path: Path,
    variant_id: str,
    rows: tuple[dict[str, object], ...],
    headers: tuple[str, ...],
    expected_supported: bool,
) -> None:
    source = _write_csv(tmp_path / f"{variant_id}.csv", rows, headers=headers)

    returncode, stdout = _run_public_analysis_script(
        [
            "--source",
            str(source),
            "--source-type",
            "csv",
            "--question-class",
            "revenue_change",
            "--metric",
            "revenue_change",
            "--baseline-label",
            "Q3 2026",
            "--baseline-start",
            "2026-07-01",
            "--baseline-end",
            "2026-09-30",
            "--comparison-label",
            "Q4 2026",
            "--comparison-start",
            "2026-10-01",
            "--comparison-end",
            "2026-12-31",
            "--original-question",
            "How did revenue change from Q3 2026 to Q4 2026?",
        ],
    )

    assert returncode == 0
    payload = json.loads(stdout)
    assert bool(payload["response"]["supported_claims"]) is expected_supported
    if expected_supported:
        assert payload["response"]["supported_claims"][0]["value"] == "-20.00"
    else:
        assert payload["response"]["blocked"] is True or payload["response"]["clarification_required"]


def _observe(
    source: Path,
    *,
    metric: str,
    source_type: SourceType = SourceType.CSV,
    selected_sheet: str | None = None,
    mapping: CanonicalMapping | None = None,
) -> Observed:
    try:
        outcome = run_public_analysis(
            _intent(source, metric=metric, source_type=source_type, selected_sheet=selected_sheet, mapping=mapping),
            artifact_store=ArtifactStore(source.parent / "artifacts"),
            metadata_store=MetadataStore(source.parent / "metadata.sqlite"),
        )
    except Exception:
        return Observed(False, None, False, (), (), None, crashed=True)
    claim = outcome.response.supported_claims[0] if outcome.response.supported_claims else None
    return Observed(
        supported=claim is not None,
        value=claim.value if claim is not None else None,
        blocked=outcome.response.blocked,
        clarification_required=outcome.response.clarification_required,
        limitations=outcome.response.limitations,
        metric_state=claim.metric_state if claim is not None else None,
    )


def _run_public_analysis_script(argv: list[str]) -> tuple[int, str]:
    script = Path(__file__).resolve().parents[2] / "skills" / "commerce-lens" / "scripts" / "run_public_analysis.py"
    module_name = "p11_run_public_analysis_script"
    spec = importlib.util.spec_from_file_location(module_name, script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        returncode = module.main(argv)
    assert stderr.getvalue() == ""
    return returncode, stdout.getvalue()


def _intent(
    source: Path,
    *,
    metric: str,
    source_type: SourceType,
    selected_sheet: str | None,
    mapping: CanonicalMapping | None,
) -> PublicAnalysisIntent:
    question_class = (
        PublicQuestionClass.REVENUE_CHANGE if metric == "revenue_change" else PublicQuestionClass.SINGLE_PERIOD_METRIC
    )
    return PublicAnalysisIntent(
        question_class=question_class,
        metric_id=metric,
        baseline_period=PeriodDefinition(
            period_id="baseline",
            label="Q3 2026",
            start_date=date(2026, 7, 1),
            end_date=date(2026, 9, 30),
            date_convention_ref="order_date_utc",
        ),
        comparison_period=PeriodDefinition(
            period_id="comparison",
            label="Q4 2026",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 12, 31),
            date_convention_ref="order_date_utc",
        ),
        source=PublicSourceSelection(
            source_path=source,
            source_type=source_type,
            selected_sheet=selected_sheet,
            mapping=mapping,
        ),
        original_question_text="How did revenue change from Q3 2026 to Q4 2026?",
        result_period_role="comparison" if metric != "revenue_change" else None,
    )


def _renamed_rows(rename_map: dict[str, str]) -> tuple[dict[str, object], ...]:
    return tuple({rename_map[key]: value for key, value in row.items()} for row in BASE_ROWS)


def _write_csv(
    path: Path,
    rows: tuple[dict[str, object], ...],
    *,
    headers: tuple[str, ...] = CANONICAL_HEADERS,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def _write_xlsx(
    path: Path,
    rows: tuple[dict[str, object], ...],
    *,
    headers: tuple[str, ...] = CANONICAL_HEADERS,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Orders"
    sheet.append(list(headers))
    for row in rows:
        sheet.append([row.get(header) for header in headers])
    workbook.save(path)
    return path
