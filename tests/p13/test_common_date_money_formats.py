from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook

from commerce_lens.canonical import CanonicalizationRequest, EligibilityMode, canonicalize_dataset, identity_mapping
from commerce_lens.canonical.service import _decimal_from_source
from commerce_lens.contracts.common import MetricState, SourceType
from commerce_lens.intake.registry import DatasetRegistry
from commerce_lens.persistence.artifact_store import ArtifactStore
from tests.p12.test_schema_mapping_ux import _revenue_change_intent, _run as _run_public


HEADERS = (
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


def test_p13_safe_date_representations_canonicalize_equivalently(tmp_path: Path) -> None:
    for index, raw_date in enumerate(
        (
            "2026-07-15",
            "2026/07/15",
            "Jul 15 2026",
            "July 15, 2026",
            " 2026-07-15 ",
            "2026-07-15T00:00:00",
        ),
        start=1,
    ):
        dataset, store = _registered_csv(tmp_path, [_row(order_date=raw_date)], filename=f"date_{index}.csv")

        result = canonicalize_dataset(dataset, _request(dataset), store)

        assert result.canonical_dataset is not None
        assert result.canonical_rows[0].order_date.isoformat() == "2026-07-15"


def test_p13_ambiguous_and_unsafe_dates_fail_closed(tmp_path: Path) -> None:
    cases = (
        ("01/02/2026", "canonical.order_date.ambiguous"),
        ("02/01/2026", "canonical.order_date.ambiguous"),
        ("2026-07-15T13:30:00", "canonical.order_date.timestamp_unsupported"),
        ("2026-07-15T00:00:00Z", "canonical.order_date.timestamp_unsupported"),
        ("not-a-date", "canonical.order_date.invalid"),
    )
    for index, (raw_date, check_id) in enumerate(cases, start=1):
        dataset, store = _registered_csv(tmp_path, [_row(order_date=raw_date)], filename=f"bad_date_{index}.csv")

        result = canonicalize_dataset(dataset, _request(dataset), store)

        assert result.canonical_dataset is None
        assert any(check.check_id == check_id for check in result.data_quality_results)


def test_p13_money_representations_canonicalize_equivalently_with_currency_authority(tmp_path: Path) -> None:
    for index, raw_money in enumerate(
        (
            "120",
            "120.00",
            "$120.00",
            "USD 120.00",
            "1,200.00",
            "$1,200.00",
            " 120.00 ",
            " USD 120.00 ",
        ),
        start=1,
    ):
        expected = Decimal("1200.00") if "," in raw_money else Decimal("120.00")
        dataset, store = _registered_csv(tmp_path, [_row(line_revenue=raw_money)], filename=f"money_{index}.csv")

        result = canonicalize_dataset(dataset, _request(dataset), store)

        assert result.canonical_dataset is not None
        assert result.canonical_rows[0].line_revenue == expected


def test_p13_negative_money_parser_preserves_sign_but_canonical_revenue_eligibility_still_blocks(
    tmp_path: Path,
) -> None:
    for raw_money in ("-120.00", "-$120.00", "(120.00)", "($120.00)", "(1,200.00)"):
        parsed, failure = _decimal_from_source(raw_money, currency_authority="USD")
        assert failure is None
        assert parsed is not None
        assert parsed < 0

        dataset, store = _registered_csv(
            tmp_path,
            [_row(line_revenue=raw_money)],
            filename=f"negative_{raw_money.replace('$', 'usd').replace(',', '').replace('.', '_').replace('(', '').replace(')', '')}.csv",
        )
        result = canonicalize_dataset(dataset, _request(dataset), store)

        assert result.canonical_dataset is None
        assert any(check.check_id == "canonical.line_revenue.negative" for check in result.data_quality_results)


def test_p13_money_ambiguous_malformed_and_currency_authority_cases_fail_closed(tmp_path: Path) -> None:
    cases = (
        (_row(line_revenue="1.200,00"), "canonical.line_revenue.ambiguous_locale"),
        (_row(line_revenue="12,00.00"), "canonical.line_revenue.malformed_grouping"),
        (_row(line_revenue="1,23,4.00"), "canonical.line_revenue.malformed_grouping"),
        (_row(line_revenue="1,,200.00"), "canonical.line_revenue.malformed_grouping"),
        (_row(line_revenue="$120.00", currency=""), "canonical.line_revenue.currency_authority_missing"),
        (_row(line_revenue="USD 120.00", currency="EUR"), "canonical.line_revenue.currency_conflict"),
    )
    for index, (row, check_id) in enumerate(cases, start=1):
        dataset, store = _registered_csv(tmp_path, [row], filename=f"bad_money_{index}.csv")

        result = canonicalize_dataset(dataset, _request(dataset), store)

        assert result.canonical_dataset is None
        assert any(check.check_id == check_id for check in result.data_quality_results)


def test_p13_currency_authority_matrix_distinguishes_symbol_from_textual_currency(tmp_path: Path) -> None:
    accepted_cases = (
        ("plain_usd", _row(line_revenue="120.00", currency="USD"), Decimal("120.00"), "USD"),
        ("symbol_usd", _row(line_revenue="$120.00", currency="USD"), Decimal("120.00"), "USD"),
        ("symbol_cad", _row(line_revenue="$120.00", currency="CAD"), Decimal("120.00"), "CAD"),
        ("text_usd", _row(line_revenue="USD 120.00", currency="USD"), Decimal("120.00"), "USD"),
    )
    for filename, row, expected_revenue, expected_currency in accepted_cases:
        dataset, store = _registered_csv(tmp_path, [row], filename=f"{filename}.csv")

        result = canonicalize_dataset(dataset, _request(dataset), store)

        assert result.canonical_dataset is not None
        assert result.canonical_rows[0].line_revenue == expected_revenue
        assert result.canonical_rows[0].currency == expected_currency

    rejected_cases = (
        ("symbol_missing", _row(line_revenue="$120.00", currency=""), "canonical.currency.missing"),
        ("text_conflict", _row(line_revenue="USD 120.00", currency="CAD"), "canonical.line_revenue.currency_conflict"),
        ("text_missing", _row(line_revenue="USD 120.00", currency=""), "canonical.currency.missing"),
    )
    for filename, row, check_id in rejected_cases:
        dataset, store = _registered_csv(tmp_path, [row], filename=f"{filename}.csv")

        result = canonicalize_dataset(dataset, _request(dataset), store)

        assert result.canonical_dataset is None
        assert any(check.check_id == check_id for check in result.data_quality_results)


def test_p13_xlsx_native_and_text_formats_match_csv_canonical_values(tmp_path: Path) -> None:
    csv_dataset, csv_store = _registered_csv(
        tmp_path,
        [_row(order_date="2026-07-15", line_revenue="1200.00", unit_price="1200.00")],
        filename="baseline.csv",
    )
    xlsx_dataset, xlsx_store = _registered_xlsx(
        tmp_path,
        [
            _row(
                order_date=datetime(2026, 7, 15, 0, 0, 0),
                line_revenue=1200,
                unit_price=1200,
            )
        ],
        filename="typed.xlsx",
    )
    text_xlsx_dataset, text_xlsx_store = _registered_xlsx(
        tmp_path,
        [_row(order_date="July 15, 2026", line_revenue="$1,200.00", unit_price="USD 1,200.00")],
        filename="text.xlsx",
    )

    results = (
        canonicalize_dataset(csv_dataset, _request(csv_dataset), csv_store),
        canonicalize_dataset(xlsx_dataset, _request(xlsx_dataset), xlsx_store),
        canonicalize_dataset(text_xlsx_dataset, _request(text_xlsx_dataset), text_xlsx_store),
    )

    assert [result.canonical_rows[0].order_date for result in results] == [results[0].canonical_rows[0].order_date] * 3
    assert [result.canonical_rows[0].line_revenue for result in results] == [Decimal("1200.00")] * 3
    assert [result.canonical_rows[0].unit_price for result in results] == [Decimal("1200.00")] * 3


def test_p13_equivalent_public_analysis_outputs_match_for_csv_and_xlsx(tmp_path: Path) -> None:
    canonical_rows = (
        _row(order_id="q3-o1", order_line_id="q3-l1", order_date="2026-07-15", line_revenue="120.00"),
        _row(order_id="q4-o1", order_line_id="q4-l1", order_date="2026-10-15", line_revenue="100.00"),
    )
    alternate_rows = (
        _row(order_id="q3-o1", order_line_id="q3-l1", order_date="July 15, 2026", line_revenue="$120.00"),
        _row(order_id="q4-o1", order_line_id="q4-l1", order_date="2026/10/15", line_revenue="USD 100.00"),
    )
    canonical_csv = _write_csv(tmp_path / "canonical_public.csv", canonical_rows)
    alternate_csv = _write_csv(tmp_path / "alternate_public.csv", alternate_rows)
    alternate_xlsx = _write_xlsx(tmp_path / "alternate_public.xlsx", alternate_rows)

    canonical = _run_public(tmp_path / "canonical", _revenue_change_intent(canonical_csv))
    alternate = _run_public(tmp_path / "alternate", _revenue_change_intent(alternate_csv))
    xlsx = _run_public(
        tmp_path / "xlsx",
        _revenue_change_intent(alternate_xlsx, source_type=SourceType.EXCEL_XLSX, selected_sheet="Orders"),
    )

    assert canonical.response.supported_claims[0].value == Decimal("-20.00")
    assert alternate.response.supported_claims[0].value == canonical.response.supported_claims[0].value
    assert xlsx.response.supported_claims[0].value == canonical.response.supported_claims[0].value
    assert alternate.response.supported_claims[0].metric_state is MetricState.VALID
    assert xlsx.response.supported_claims[0].metric_state is MetricState.VALID
    assert alternate.response.evidence_summary
    assert xlsx.response.evidence_summary


def test_p13_xlsx_datetime_with_time_component_still_fails_closed(tmp_path: Path) -> None:
    dataset, store = _registered_xlsx(
        tmp_path,
        [_row(order_date=datetime(2026, 7, 15, 13, 30, 0))],
        filename="unsafe_datetime.xlsx",
    )

    result = canonicalize_dataset(dataset, _request(dataset), store)

    assert result.canonical_dataset is None
    assert any(check.check_id == "canonical.order_date.timestamp_unsupported" for check in result.data_quality_results)


def _request(dataset) -> CanonicalizationRequest:
    return CanonicalizationRequest(
        source_dataset_id=dataset.dataset_id,
        mapping=identity_mapping(HEADERS),
        eligibility_mode=EligibilityMode.UPSTREAM_ELIGIBLE_ONLY,
    )


def _row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "order_id": "o1",
        "order_line_id": "l1",
        "order_date": "2026-07-15",
        "product_id": "p1",
        "product_name": "Tea",
        "category_id": "c1",
        "category_name": "Drinks",
        "quantity": "1",
        "line_revenue": "120.00",
        "currency": "USD",
        "unit_price": "",
        "eligibility_status": "paid",
    }
    row.update(overrides)
    return row


def _registered_csv(tmp_path: Path, rows: list[dict[str, object]], *, filename: str):
    path = _write_csv(tmp_path / filename, tuple(rows))
    store = ArtifactStore(tmp_path / f"runtime_{path.stem}")
    registry = DatasetRegistry(store)
    return registry.register_source(path, SourceType.CSV), store


def _write_csv(path: Path, rows: tuple[dict[str, object], ...]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows([{key: row.get(key, "") for key in HEADERS} for row in rows])
    return path


def _registered_xlsx(tmp_path: Path, rows: list[dict[str, object]], *, filename: str):
    path = _write_xlsx(tmp_path / filename, tuple(rows))
    store = ArtifactStore(tmp_path / f"runtime_{path.stem}")
    registry = DatasetRegistry(store)
    return registry.register_source(path, SourceType.EXCEL_XLSX, selected_sheet="Orders"), store


def _write_xlsx(path: Path, rows: tuple[dict[str, object], ...]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Orders"
    sheet.append(HEADERS)
    for row in rows:
        sheet.append([row.get(header, "") for header in HEADERS])
    workbook.save(path)
    return path
