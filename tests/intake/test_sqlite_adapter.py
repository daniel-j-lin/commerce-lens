import sqlite3

from commerce_lens.evidence.identifiers import sha256_file
from commerce_lens.intake.inspection import InspectionStatus
from commerce_lens.intake.sqlite_adapter import SQLiteInspectionAdapter


def test_sqlite_inspection_requires_explicit_table_when_ambiguous(tmp_path) -> None:
    path = tmp_path / "source.sqlite"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE orders (order_id TEXT)")
    conn.execute("CREATE TABLE lines (order_line_id TEXT)")
    conn.commit()
    conn.close()

    result = SQLiteInspectionAdapter().inspect(path)

    assert result.status is InspectionStatus.AMBIGUOUS
    assert result.available_tables == ("lines", "orders")


def test_sqlite_inspection_is_read_only_and_preserves_source(tmp_path) -> None:
    path = tmp_path / "source.sqlite"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE orders (order_id TEXT, line_revenue REAL)")
    conn.execute("INSERT INTO orders VALUES ('1', 10.5)")
    conn.commit()
    conn.close()
    before = sha256_file(path)

    result = SQLiteInspectionAdapter().inspect(path, table_name="orders")

    assert result.status is InspectionStatus.SUPPORTED
    assert result.selected_table == "orders"
    assert [column.name for column in result.columns] == ["order_id", "line_revenue"]
    assert result.row_count == 1
    assert sha256_file(path) == before


def test_sqlite_rejects_unknown_table_without_sql_execution(tmp_path) -> None:
    path = tmp_path / "source.sqlite"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE orders (order_id TEXT)")
    conn.commit()
    conn.close()

    result = SQLiteInspectionAdapter().inspect(path, table_name="orders; DROP TABLE orders;")

    assert result.status is InspectionStatus.FAILED
    assert "does not exist" in result.failure_detail.reason

