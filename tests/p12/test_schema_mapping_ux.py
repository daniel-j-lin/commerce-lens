from __future__ import annotations

import contextlib
import csv
import importlib.util
import io
import json
import sys
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

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
    validate_public_intent,
)
from commerce_lens.skill.schema_mapping import assess_schema_mapping, confirmed_mapping_from_source_to_canonical


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

AMBIGUOUS_HEADERS = (
    "ID",
    "Line ID",
    "Date",
    "Product ID",
    "Qty",
    "Total",
    "Currency",
    "Status",
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


def test_identity_mapping_needs_no_confirmation_and_preserves_revenue_change(tmp_path: Path) -> None:
    source = _write_csv(tmp_path / "canonical.csv", BASE_ROWS)

    outcome = _run(tmp_path, _revenue_change_intent(source))

    assert outcome.response.clarification_required == ()
    assert outcome.response.mapping_proposals == ()
    assert outcome.response.supported_claims[0].value == Decimal("-20.00")


def test_human_readable_csv_requires_confirmation_then_confirmed_mapping_succeeds(tmp_path: Path) -> None:
    source = _write_csv(
        tmp_path / "human.csv",
        _renamed_rows(HUMAN_HEADERS),
        headers=tuple(HUMAN_HEADERS.values()),
    )

    unconfirmed = _run(tmp_path / "unconfirmed", _revenue_change_intent(source))

    assert unconfirmed.request is None
    assert unconfirmed.response.blocked is True
    assert unconfirmed.response.supported_claims == ()
    assert ("Revenue", "line_revenue") in {
        (proposal.source_field, proposal.canonical_field)
        for proposal in unconfirmed.response.mapping_proposals
    }

    confirmed = _run(
        tmp_path / "confirmed",
        replace(
            _revenue_change_intent(source),
            source=PublicSourceSelection(
                source,
                SourceType.CSV,
                mapping=confirmed_mapping_from_source_to_canonical(
                    {source_field: canonical for canonical, source_field in HUMAN_HEADERS.items()}
                ),
                mapping_mode="confirmed_source_to_canonical_mapping",
            ),
        ),
    )

    assert confirmed.response.supported_claims[0].value == Decimal("-20.00")
    assert confirmed.response.supported_claims[0].metric_state is MetricState.VALID


def test_mapping_json_runner_interface_executes_confirmed_csv_mapping(tmp_path: Path) -> None:
    source = _write_csv(
        tmp_path / "human_runner.csv",
        _renamed_rows(HUMAN_HEADERS),
        headers=tuple(HUMAN_HEADERS.values()),
    )

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
            "--mapping-json",
            json.dumps({source_field: canonical for canonical, source_field in HUMAN_HEADERS.items()}),
        ],
    )

    assert returncode == 0
    payload = json.loads(stdout)
    assert payload["response"]["supported_claims"][0]["value"] == "-20.00"
    assert payload["validated_results_summary"]


def test_xlsx_human_readable_headers_succeed_with_confirmed_mapping(tmp_path: Path) -> None:
    source = _write_xlsx(
        tmp_path / "human.xlsx",
        _renamed_rows(HUMAN_HEADERS),
        headers=tuple(HUMAN_HEADERS.values()),
    )

    outcome = _run(
        tmp_path,
        replace(
            _revenue_change_intent(source, source_type=SourceType.EXCEL_XLSX, selected_sheet="Orders"),
            source=PublicSourceSelection(
                source,
                SourceType.EXCEL_XLSX,
                selected_sheet="Orders",
                mapping=confirmed_mapping_from_source_to_canonical(
                    {source_field: canonical for canonical, source_field in HUMAN_HEADERS.items()}
                ),
                mapping_mode="confirmed_source_to_canonical_mapping",
            ),
        ),
    )

    assert outcome.response.supported_claims[0].value == Decimal("-20.00")
    assert outcome.response.evidence_summary[0].source_type == "excel_xlsx"


def test_corrected_mapping_uses_only_confirmed_authority(tmp_path: Path) -> None:
    corrected_headers = dict(HUMAN_HEADERS)
    corrected_headers["line_revenue"] = "Net Sales"
    source = _write_csv(
        tmp_path / "corrected.csv",
        _renamed_rows(corrected_headers),
        headers=tuple(corrected_headers.values()),
    )

    proposal = assess_schema_mapping(tuple(corrected_headers.values()), "revenue_change")

    assert "line_revenue" in proposal.missing_required_fields

    outcome = _run(
        tmp_path,
        replace(
            _revenue_change_intent(source),
            source=PublicSourceSelection(
                source,
                SourceType.CSV,
                mapping=confirmed_mapping_from_source_to_canonical(
                    {source_field: canonical for canonical, source_field in corrected_headers.items()}
                ),
                mapping_mode="confirmed_source_to_canonical_mapping",
            ),
        ),
    )

    assert outcome.response.supported_claims[0].value == Decimal("-20.00")


def test_unconfirmed_or_rejected_mapping_blocks_even_if_mapping_payload_exists(tmp_path: Path) -> None:
    source = _write_csv(
        tmp_path / "human.csv",
        _renamed_rows(HUMAN_HEADERS),
        headers=tuple(HUMAN_HEADERS.values()),
    )
    mapping = confirmed_mapping_from_source_to_canonical(
        {source_field: canonical for canonical, source_field in HUMAN_HEADERS.items()}
    )

    for mode in ("proposed_unconfirmed_mapping", "mapping_rejected"):
        failures = validate_public_intent(
            replace(
                _revenue_change_intent(source),
                source=PublicSourceSelection(source, SourceType.CSV, mapping=mapping, mapping_mode=mode),
            )
        )
        assert "confirmed source-to-canonical mapping authority is required" in failures


def test_ambiguous_headers_require_clarification_without_material_result(tmp_path: Path) -> None:
    rows = tuple(
        {
            "ID": row["order_id"],
            "Line ID": row["order_line_id"],
            "Date": row["order_date"],
            "Product ID": row["product_id"],
            "Qty": row["quantity"],
            "Total": row["line_revenue"],
            "Currency": row["currency"],
            "Status": row["eligibility_status"],
        }
        for row in BASE_ROWS
    )
    source = _write_csv(tmp_path / "ambiguous.csv", rows, headers=AMBIGUOUS_HEADERS)

    outcome = _run(tmp_path, _revenue_change_intent(source))

    assert outcome.request is None
    assert outcome.response.supported_claims == ()
    assert outcome.response.clarification_required
    assert any("line_revenue" in item for item in outcome.response.clarification_required)


def test_missing_required_revenue_mapping_blocks(tmp_path: Path) -> None:
    headers = tuple(header for header in CANONICAL_HEADERS if header != "line_revenue")
    rows = tuple({key: value for key, value in row.items() if key != "line_revenue"} for row in BASE_ROWS)
    source = _write_csv(tmp_path / "missing_revenue.csv", rows, headers=headers)

    outcome = _run(tmp_path, _revenue_change_intent(source))

    assert outcome.request is None
    assert outcome.response.supported_claims == ()
    assert "line_revenue" in outcome.response.required_mapping_fields


def test_alias_cannot_silently_override_exact_canonical_field(tmp_path: Path) -> None:
    rows = tuple({**row, "Revenue": "9999.00"} for row in BASE_ROWS)
    source = _write_csv(tmp_path / "conflict.csv", rows, headers=tuple(rows[0].keys()))

    outcome = _run(tmp_path, _revenue_change_intent(source))

    assert outcome.response.clarification_required == ()
    assert outcome.response.supported_claims[0].value == Decimal("-20.00")


def test_validate_mapping_is_invoked_for_confirmed_mapping(tmp_path: Path, monkeypatch) -> None:
    source = _write_csv(
        tmp_path / "human.csv",
        _renamed_rows(HUMAN_HEADERS),
        headers=tuple(HUMAN_HEADERS.values()),
    )
    mapping = confirmed_mapping_from_source_to_canonical(
        {source_field: canonical for canonical, source_field in HUMAN_HEADERS.items()}
    )
    import commerce_lens.canonical.service as service

    original = service.validate_mapping
    observed_mapping_ids: list[str] = []

    def observe_validate_mapping(*args, **kwargs):
        observed_mapping_ids.append(args[0].mapping_id)
        return original(*args, **kwargs)

    monkeypatch.setattr(service, "validate_mapping", observe_validate_mapping)

    outcome = _run(
        tmp_path,
        replace(
            _revenue_change_intent(source),
            source=PublicSourceSelection(
                source,
                SourceType.CSV,
                mapping=mapping,
                mapping_mode="confirmed_source_to_canonical_mapping",
            ),
        ),
    )

    assert outcome.response.supported_claims[0].value == Decimal("-20.00")
    assert observed_mapping_ids == [mapping.mapping_id]


def _run(tmp_path: Path, intent: PublicAnalysisIntent):
    return run_public_analysis(
        intent,
        artifact_store=ArtifactStore(Path(tmp_path) / "runtime"),
        metadata_store=MetadataStore(Path(tmp_path) / "metadata.sqlite"),
    )


def _revenue_change_intent(
    source: Path,
    *,
    source_type: SourceType = SourceType.CSV,
    selected_sheet: str | None = None,
) -> PublicAnalysisIntent:
    return PublicAnalysisIntent(
        question_class=PublicQuestionClass.REVENUE_CHANGE,
        metric_id="revenue_change",
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
            source,
            source_type,
            selected_sheet=selected_sheet,
        ),
        original_question_text="How did revenue change from Q3 2026 to Q4 2026?",
    )


def _renamed_rows(rename_map: dict[str, str]) -> tuple[dict[str, object], ...]:
    return tuple({rename_map[key]: value for key, value in row.items()} for row in BASE_ROWS)


def _write_csv(path: Path, rows: tuple[dict[str, object], ...], *, headers: tuple[str, ...] = CANONICAL_HEADERS) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def _write_xlsx(path: Path, rows: tuple[dict[str, object], ...], *, headers: tuple[str, ...]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Orders"
    sheet.append(list(headers))
    for row in rows:
        sheet.append([row.get(header) for header in headers])
    workbook.save(path)
    return path


def _run_public_analysis_script(argv: list[str]) -> tuple[int, str]:
    script = Path(__file__).resolve().parents[2] / "skills" / "commerce-lens" / "scripts" / "run_public_analysis.py"
    module_name = "p12_run_public_analysis_script"
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
