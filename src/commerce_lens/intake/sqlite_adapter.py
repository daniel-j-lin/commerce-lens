"""Read-only SQLite source inspection adapter."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from commerce_lens.contracts.common import FailureDetail, FailureStage, SourceType
from commerce_lens.intake.inspection import ColumnInspection, InspectionStatus, IntakeInspectionResult, infer_observed_type
from commerce_lens.intake.registry import DatasetRegistry


class SQLiteInspectionAdapter:
    def __init__(self, registry: DatasetRegistry | None = None, *, sample_rows: int = 50) -> None:
        self.registry = registry
        self.sample_rows = sample_rows

    def inspect(self, source_path: str | Path, *, table_name: str | None = None) -> IntakeInspectionResult:
        path = Path(source_path).expanduser().resolve()
        if not path.exists():
            return _failure("SQLite source file does not exist", InspectionStatus.FAILED)
        try:
            conn = _connect_read_only(path)
        except sqlite3.Error as exc:
            return _failure(f"SQLite source is unreadable in read-only mode: {exc}", InspectionStatus.FAILED)
        with conn:
            tables = tuple(_list_tables(conn))
            if table_name is None:
                if len(tables) != 1:
                    return IntakeInspectionResult(
                        source_type=SourceType.SQLITE,
                        status=InspectionStatus.AMBIGUOUS,
                        available_tables=tables,
                        ambiguities=("multiple tables/views require explicit table selection",),
                        failure_detail=FailureDetail(stage=FailureStage.INTAKE, reason="multiple tables/views require explicit table selection"),
                    )
                table_name = tables[0]
            if table_name not in tables:
                return _failure(f"selected table/view does not exist: {table_name}", InspectionStatus.FAILED, tables=tables)

            pragma_rows = conn.execute(f"PRAGMA table_info({_quote_literal(table_name)})").fetchall()
            columns = [
                ColumnInspection(
                    name=row["name"],
                    position=int(row["cid"]),
                    declared_type=row["type"] or None,
                    observed_type=None,
                    nullable_observed=None,
                )
                for row in pragma_rows
            ]
            quoted = _quote_identifier(table_name)
            sample = conn.execute(f"SELECT * FROM {quoted} LIMIT ?", (self.sample_rows,)).fetchall()
            column_names = [column.name for column in columns]
            inspected = []
            for index, column in enumerate(columns):
                observed_type, nullable = infer_observed_type([row[column_names[index]] for row in sample])
                inspected.append(
                    column.model_copy(update={"observed_type": observed_type, "nullable_observed": nullable})
                )
            row_count = conn.execute(f"SELECT COUNT(*) AS count FROM {quoted}").fetchone()["count"]

        dataset_id = None
        if self.registry is not None:
            dataset_id = self.registry.register_source(path, SourceType.SQLITE, selected_table=table_name).dataset_id
        return IntakeInspectionResult(
            source_type=SourceType.SQLITE,
            status=InspectionStatus.SUPPORTED,
            dataset_ref_id=dataset_id,
            selected_table=table_name,
            available_tables=tables,
            columns=tuple(inspected),
            row_count=int(row_count),
        )


def _connect_read_only(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _list_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type IN ('table', 'view')
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    return [row["name"] for row in rows]


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _quote_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _failure(reason: str, status: InspectionStatus, *, tables: tuple[str, ...] = ()) -> IntakeInspectionResult:
    return IntakeInspectionResult(
        source_type=SourceType.SQLITE,
        status=status,
        available_tables=tables,
        failure_detail=FailureDetail(stage=FailureStage.INTAKE, reason=reason),
        ambiguities=(reason,) if status is InspectionStatus.AMBIGUOUS else (),
    )

