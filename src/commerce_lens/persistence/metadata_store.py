"""Minimal SQLite metadata registry foundation."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from commerce_lens.contracts.evidence import CanonicalDatasetReference, CanonicalizationRecord, DatasetReference


SCHEMA_VERSION = 2

_PHASE1_TABLE_COLUMNS = {
    "dataset_registrations": {
        "dataset_id",
        "source_type",
        "original_name",
        "content_fingerprint",
        "size_bytes",
        "registered_at",
        "selected_sheet",
        "selected_table",
        "snapshot_path",
        "record_json",
    },
    "artifact_references": {
        "artifact_id",
        "path",
        "fingerprint",
        "media_type",
        "size_bytes",
        "record_json",
    },
    "run_records": {
        "run_id",
        "request_id",
        "run_status",
        "record_json",
        "created_at",
    },
}

_PHASE2_TABLE_COLUMNS = {
    "canonical_dataset_registrations": {
        "canonical_dataset_id",
        "source_dataset_id",
        "canonical_schema_version",
        "content_fingerprint",
        "artifact_id",
        "row_count",
        "record_json",
    },
    "canonicalization_records": {
        "canonicalization_id",
        "source_dataset_id",
        "canonical_dataset_id",
        "canonical_schema_version",
        "mapping_ref",
        "transformation_version",
        "record_json",
    },
}


class MetadataStore:
    """Small SQLite registry for Phase 1 and Phase 2 metadata."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    version INTEGER NOT NULL
                )
                """
            )
            row = conn.execute("SELECT version FROM schema_version WHERE id = 1").fetchone()
            if row is None:
                self._create_phase1_tables(conn)
                self._create_phase2_tables(conn)
                self._verify_phase2_schema(conn)
                conn.execute("INSERT INTO schema_version (id, version) VALUES (1, ?)", (SCHEMA_VERSION,))
                return

            stored_version = int(row["version"])
            if stored_version == 1:
                self._migrate_v1_to_v2(conn)
                return
            if stored_version == SCHEMA_VERSION:
                self._verify_phase2_schema(conn)
                return
            raise RuntimeError(
                f"metadata schema version mismatch: stored={stored_version} expected={SCHEMA_VERSION}"
            )

    def schema_version(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT version FROM schema_version WHERE id = 1").fetchone()
            if row is None:
                raise RuntimeError("metadata schema is not initialized")
            return int(row["version"])

    def insert_dataset(self, dataset: DatasetReference) -> DatasetReference:
        payload = dataset.model_dump_json()
        snapshot_path = dataset.snapshot_artifact.path if dataset.snapshot_artifact else None
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO dataset_registrations (
                    dataset_id, source_type, original_name, content_fingerprint,
                    size_bytes, registered_at, selected_sheet, selected_table,
                    snapshot_path, record_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dataset.dataset_id,
                    dataset.source_type.value,
                    dataset.original_name,
                    dataset.content_fingerprint,
                    dataset.size_bytes,
                    dataset.registered_at.isoformat(),
                    dataset.selected_sheet,
                    dataset.selected_table,
                    snapshot_path,
                    payload,
                ),
            )
        return self.get_dataset(dataset.dataset_id) or dataset

    def get_dataset(self, dataset_id: str) -> DatasetReference | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT record_json FROM dataset_registrations WHERE dataset_id = ?",
                (dataset_id,),
            ).fetchone()
        if row is None:
            return None
        return DatasetReference.model_validate(json.loads(row["record_json"]))

    def list_datasets(self) -> list[DatasetReference]:
        with self._connect() as conn:
            rows = conn.execute("SELECT record_json FROM dataset_registrations ORDER BY dataset_id").fetchall()
        return [DatasetReference.model_validate(json.loads(row["record_json"])) for row in rows]

    def insert_canonical_dataset(
        self,
        canonical_dataset: CanonicalDatasetReference,
    ) -> CanonicalDatasetReference:
        payload = canonical_dataset.model_dump_json()
        with self._connect() as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            if not self._stable_record_needs_insert(
                conn,
                table="canonical_dataset_registrations",
                id_column="canonical_dataset_id",
                stable_id=canonical_dataset.canonical_dataset_id,
                payload=payload,
            ):
                return canonical_dataset
            conn.execute(
                """
                INSERT INTO canonical_dataset_registrations (
                    canonical_dataset_id, source_dataset_id, canonical_schema_version,
                    content_fingerprint, artifact_id, row_count, record_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    canonical_dataset.canonical_dataset_id,
                    canonical_dataset.source_dataset_id,
                    canonical_dataset.canonical_schema_version,
                    canonical_dataset.content_fingerprint,
                    canonical_dataset.artifact.artifact_id,
                    canonical_dataset.row_count,
                    payload,
                ),
            )
        return self.get_canonical_dataset(canonical_dataset.canonical_dataset_id) or canonical_dataset

    def get_canonical_dataset(self, canonical_dataset_id: str) -> CanonicalDatasetReference | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT record_json FROM canonical_dataset_registrations WHERE canonical_dataset_id = ?",
                (canonical_dataset_id,),
            ).fetchone()
        if row is None:
            return None
        return CanonicalDatasetReference.model_validate(json.loads(row["record_json"]))

    def insert_canonicalization_record(
        self,
        canonicalization_record: CanonicalizationRecord,
    ) -> CanonicalizationRecord:
        payload = canonicalization_record.model_dump_json()
        with self._connect() as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            if not self._stable_record_needs_insert(
                conn,
                table="canonicalization_records",
                id_column="canonicalization_id",
                stable_id=canonicalization_record.canonicalization_id,
                payload=payload,
            ):
                return canonicalization_record
            conn.execute(
                """
                INSERT INTO canonicalization_records (
                    canonicalization_id, source_dataset_id, canonical_dataset_id,
                    canonical_schema_version, mapping_ref, transformation_version,
                    record_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    canonicalization_record.canonicalization_id,
                    canonicalization_record.source_dataset_id,
                    canonicalization_record.canonical_dataset_id,
                    canonicalization_record.canonical_schema_version,
                    canonicalization_record.mapping_ref,
                    canonicalization_record.transformation_version,
                    payload,
                ),
            )
        return self.get_canonicalization_record(canonicalization_record.canonicalization_id) or canonicalization_record

    def get_canonicalization_record(self, canonicalization_id: str) -> CanonicalizationRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT record_json FROM canonicalization_records WHERE canonicalization_id = ?",
                (canonicalization_id,),
            ).fetchone()
        if row is None:
            return None
        return CanonicalizationRecord.model_validate(json.loads(row["record_json"]))

    def _migrate_v1_to_v2(self, conn: sqlite3.Connection) -> None:
        self._verify_phase1_schema(conn)
        self._create_phase2_tables(conn)
        self._verify_phase2_schema(conn)
        conn.execute("UPDATE schema_version SET version = ? WHERE id = 1", (SCHEMA_VERSION,))

    def _create_phase1_tables(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dataset_registrations (
                dataset_id TEXT PRIMARY KEY,
                source_type TEXT NOT NULL,
                original_name TEXT NOT NULL,
                content_fingerprint TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                registered_at TEXT NOT NULL,
                selected_sheet TEXT,
                selected_table TEXT,
                snapshot_path TEXT,
                record_json TEXT NOT NULL,
                UNIQUE(source_type, content_fingerprint, selected_sheet, selected_table)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS artifact_references (
                artifact_id TEXT PRIMARY KEY,
                path TEXT NOT NULL,
                fingerprint TEXT,
                media_type TEXT,
                size_bytes INTEGER,
                record_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS run_records (
                run_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                run_status TEXT NOT NULL,
                record_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    def _create_phase2_tables(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS canonical_dataset_registrations (
                canonical_dataset_id TEXT PRIMARY KEY,
                source_dataset_id TEXT NOT NULL,
                canonical_schema_version TEXT NOT NULL,
                content_fingerprint TEXT NOT NULL,
                artifact_id TEXT NOT NULL,
                row_count INTEGER,
                record_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS canonicalization_records (
                canonicalization_id TEXT PRIMARY KEY,
                source_dataset_id TEXT NOT NULL,
                canonical_dataset_id TEXT,
                canonical_schema_version TEXT NOT NULL,
                mapping_ref TEXT,
                transformation_version TEXT,
                record_json TEXT NOT NULL
            )
            """
        )

    def _verify_phase1_schema(self, conn: sqlite3.Connection) -> None:
        for table, expected_columns in _PHASE1_TABLE_COLUMNS.items():
            actual_columns = self._table_columns(conn, table)
            if actual_columns != expected_columns:
                raise RuntimeError(f"metadata schema version 1 is incompatible: {table}")

    def _verify_phase2_schema(self, conn: sqlite3.Connection) -> None:
        self._verify_phase1_schema(conn)
        for table, expected_columns in _PHASE2_TABLE_COLUMNS.items():
            actual_columns = self._table_columns(conn, table)
            if actual_columns != expected_columns:
                raise RuntimeError(f"metadata schema version 2 is incompatible: {table}")

    def _table_columns(self, conn: sqlite3.Connection, table: str) -> set[str]:
        rows = conn.execute(f"PRAGMA table_info({self._quote_literal(table)})").fetchall()
        return {row["name"] for row in rows}

    def _stable_record_needs_insert(
        self,
        conn: sqlite3.Connection,
        *,
        table: str,
        id_column: str,
        stable_id: str,
        payload: str,
    ) -> bool:
        row = conn.execute(
            f"SELECT record_json FROM {table} WHERE {id_column} = ?",
            (stable_id,),
        ).fetchone()
        if row is None:
            return True
        if json.loads(row["record_json"]) == json.loads(payload):
            return False
        raise RuntimeError(f"stable provenance record conflict for {stable_id}")

    def _quote_literal(self, value: str) -> str:
        return "'" + value.replace("'", "''") + "'"

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
