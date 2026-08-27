"""Read-only CSV inspection adapter."""

from __future__ import annotations

import csv
from pathlib import Path

from commerce_lens.contracts.common import FailureDetail, FailureStage, SourceType
from commerce_lens.intake.inspection import ColumnInspection, InspectionStatus, IntakeInspectionResult, infer_observed_type
from commerce_lens.intake.registry import DatasetRegistry


class CsvInspectionAdapter:
    def __init__(self, registry: DatasetRegistry | None = None, *, sample_rows: int = 50) -> None:
        self.registry = registry
        self.sample_rows = sample_rows

    def inspect(self, source_path: str | Path) -> IntakeInspectionResult:
        path = Path(source_path)
        if path.suffix.lower() != ".csv":
            return _failure("unsupported CSV source extension", InspectionStatus.UNSUPPORTED)
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            return _failure("CSV is not readable as utf-8-sig; encoding must be explicit", InspectionStatus.AMBIGUOUS)
        except OSError as exc:
            return _failure(f"CSV is unreadable: {exc}", InspectionStatus.FAILED)

        try:
            dialect = csv.Sniffer().sniff(text[:4096])
            rows = list(csv.reader(text.splitlines(), dialect))
        except csv.Error:
            delimiter = _single_visible_delimiter(text)
            if delimiter is None:
                return _failure("CSV delimiter could not be determined without ambiguity", InspectionStatus.AMBIGUOUS)
            rows = list(csv.reader(text.splitlines(), delimiter=delimiter))
        if not rows:
            return _failure("CSV contains no rows", InspectionStatus.FAILED)
        headers = [header.strip() for header in rows[0]]
        header_failure = _validate_headers(headers)
        if header_failure:
            return _failure(header_failure, InspectionStatus.FAILED)
        width = len(headers)
        for row_number, row in enumerate(rows[1:], start=2):
            if len(row) != width:
                return _failure(f"CSV row {row_number} has {len(row)} fields; expected {width}", InspectionStatus.FAILED)

        sample = rows[1 : self.sample_rows + 1]
        columns: list[ColumnInspection] = []
        for index, name in enumerate(headers):
            observed_type, nullable = infer_observed_type([row[index] for row in sample])
            columns.append(ColumnInspection(name=name, position=index, observed_type=observed_type, nullable_observed=nullable))

        dataset_id = None
        if self.registry is not None:
            dataset_id = self.registry.register_source(path, SourceType.CSV).dataset_id
        return IntakeInspectionResult(
            source_type=SourceType.CSV,
            status=InspectionStatus.SUPPORTED,
            dataset_ref_id=dataset_id,
            columns=tuple(columns),
            row_count=max(0, len(rows) - 1),
        )


def _validate_headers(headers: list[str]) -> str | None:
    if not headers or any(not header for header in headers):
        return "CSV header row contains empty column names"
    if len(set(headers)) != len(headers):
        return "CSV header row contains duplicate column names"
    return None


def _single_visible_delimiter(text: str) -> str | None:
    first_line = text.splitlines()[0] if text.splitlines() else ""
    candidates = [delimiter for delimiter in (",", "\t", ";", "|") if delimiter in first_line]
    return candidates[0] if len(candidates) == 1 else None


def _failure(reason: str, status: InspectionStatus) -> IntakeInspectionResult:
    return IntakeInspectionResult(
        source_type=SourceType.CSV,
        status=status,
        failure_detail=FailureDetail(stage=FailureStage.INTAKE, reason=reason),
        ambiguities=(reason,) if status is InspectionStatus.AMBIGUOUS else (),
    )
