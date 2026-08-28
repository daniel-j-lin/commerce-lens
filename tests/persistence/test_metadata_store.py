import sqlite3

import pytest

from commerce_lens.contracts.common import SourceType
from commerce_lens.canonical import CanonicalizationRequest, EligibilityMode, canonicalize_dataset, identity_mapping
from commerce_lens.intake.registry import DatasetRegistry
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore, SCHEMA_VERSION


def test_metadata_store_initializes_schema(tmp_path) -> None:
    store = MetadataStore(tmp_path / "registry.sqlite")
    store.initialize()
    assert store.schema_version() == SCHEMA_VERSION


def test_metadata_store_repeated_initialization_same_version_is_idempotent(tmp_path) -> None:
    store = MetadataStore(tmp_path / "registry.sqlite")
    store.initialize()
    store.initialize()
    assert store.schema_version() == SCHEMA_VERSION


def test_dataset_registration_persists_across_connections_and_deduplicates(tmp_path) -> None:
    source = tmp_path / "orders.csv"
    source.write_text("order_id,total\n1,10\n", encoding="utf-8")
    db_path = tmp_path / "registry.sqlite"
    registry = DatasetRegistry(ArtifactStore(tmp_path / "runtime"), MetadataStore(db_path))

    first = registry.register_source(source, SourceType.CSV)
    second = registry.register_source(source, SourceType.CSV)
    reopened = MetadataStore(db_path)

    assert first.dataset_id == second.dataset_id
    assert reopened.get_dataset(first.dataset_id) == first
    assert len(reopened.list_datasets()) == 1


def test_metadata_store_schema_version_mismatch_fails_without_rewrite(tmp_path) -> None:
    db_path = tmp_path / "registry.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE schema_version (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            version INTEGER NOT NULL
        )
        """
    )
    conn.execute("INSERT INTO schema_version (id, version) VALUES (1, ?)", (SCHEMA_VERSION + 1,))
    conn.commit()
    conn.close()

    with pytest.raises(RuntimeError, match="metadata schema version mismatch"):
        MetadataStore(db_path).initialize()

    reopened = sqlite3.connect(db_path)
    stored_version = reopened.execute("SELECT version FROM schema_version WHERE id = 1").fetchone()[0]
    reopened.close()
    assert stored_version == SCHEMA_VERSION + 1


def test_metadata_store_migrates_phase1_schema_to_phase3(tmp_path) -> None:
    db_path = tmp_path / "registry.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE schema_version (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            version INTEGER NOT NULL
        )
        """
    )
    conn.execute("INSERT INTO schema_version (id, version) VALUES (1, 1)")
    _create_supported_v1_tables(conn)
    conn.commit()
    conn.close()

    store = MetadataStore(db_path)
    store.initialize()

    assert store.schema_version() == SCHEMA_VERSION
    reopened = sqlite3.connect(db_path)
    tables = {
        row[0]
        for row in reopened.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    reopened.close()
    assert "canonical_dataset_registrations" in tables
    assert "canonicalization_records" in tables
    assert "execution_records" in tables


def test_canonical_dataset_and_record_persist_and_round_trip(tmp_path) -> None:
    source = tmp_path / "orders.csv"
    source.write_text(
        "\n".join(
            [
                "order_id,order_line_id,order_date,product_id,quantity,line_revenue,currency",
                "o1,l1,2026-01-01,p1,1,10.00,USD",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    artifact_store = ArtifactStore(tmp_path / "runtime")
    metadata_store = MetadataStore(tmp_path / "registry.sqlite")
    registry = DatasetRegistry(artifact_store, metadata_store)
    dataset = registry.register_source(source, SourceType.CSV)
    request = CanonicalizationRequest(
        source_dataset_id=dataset.dataset_id,
        mapping=identity_mapping(
            (
                "order_id",
                "order_line_id",
                "order_date",
                "product_id",
                "quantity",
                "line_revenue",
                "currency",
            )
        ),
        eligibility_mode=EligibilityMode.UPSTREAM_ELIGIBLE_ONLY,
    )
    result = canonicalize_dataset(dataset, request, artifact_store)
    assert result.canonical_dataset is not None

    metadata_store.insert_canonical_dataset(result.canonical_dataset)
    metadata_store.insert_canonicalization_record(result.record)

    assert metadata_store.get_canonical_dataset(result.canonical_dataset.canonical_dataset_id) == result.canonical_dataset
    assert metadata_store.get_canonicalization_record(result.record.canonicalization_id) == result.record


def test_malformed_v1_schema_fails_without_rewriting_version(tmp_path) -> None:
    db_path = tmp_path / "registry.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE schema_version (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            version INTEGER NOT NULL
        )
        """
    )
    conn.execute("INSERT INTO schema_version (id, version) VALUES (1, 1)")
    conn.execute("CREATE TABLE dataset_registrations (dataset_id TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()

    with pytest.raises(RuntimeError, match="version 1 is incompatible"):
        MetadataStore(db_path).initialize()

    reopened = sqlite3.connect(db_path)
    stored_version = reopened.execute("SELECT version FROM schema_version WHERE id = 1").fetchone()[0]
    tables = {
        row[0]
        for row in reopened.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    }
    reopened.close()
    assert stored_version == 1
    assert "canonical_dataset_registrations" not in tables
    assert "canonicalization_records" not in tables


def test_metadata_store_migrates_phase2_schema_to_phase3_and_preserves_existing_rows(tmp_path) -> None:
    db_path = tmp_path / "registry.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE schema_version (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            version INTEGER NOT NULL
        )
        """
    )
    conn.execute("INSERT INTO schema_version (id, version) VALUES (1, 2)")
    _create_supported_v2_tables(conn)
    conn.execute(
        """
        INSERT INTO dataset_registrations (
            dataset_id, source_type, original_name, content_fingerprint,
            size_bytes, registered_at, selected_sheet, selected_table,
            snapshot_path, record_json
        )
        VALUES ('ds_1', 'csv', 'orders.csv', ?, 10, '2026-01-01T00:00:00+00:00', NULL, NULL, NULL, '{}')
        """,
        ("0" * 64,),
    )
    conn.execute(
        """
        INSERT INTO canonical_dataset_registrations (
            canonical_dataset_id, source_dataset_id, canonical_schema_version,
            content_fingerprint, artifact_id, row_count, record_json
        )
        VALUES ('cds_1', 'ds_1', 'canonical_mvp_v1', ?, 'art_1', 1, '{}')
        """,
        ("1" * 64,),
    )
    conn.execute(
        """
        INSERT INTO canonicalization_records (
            canonicalization_id, source_dataset_id, canonical_dataset_id,
            canonical_schema_version, mapping_ref, transformation_version, record_json
        )
        VALUES ('canonrec_1', 'ds_1', 'cds_1', 'canonical_mvp_v1', 'mapping', 'phase2', '{}')
        """
    )
    conn.commit()
    conn.close()

    store = MetadataStore(db_path)
    store.initialize()

    assert store.schema_version() == SCHEMA_VERSION
    reopened = sqlite3.connect(db_path)
    try:
        assert reopened.execute("SELECT COUNT(*) FROM dataset_registrations").fetchone()[0] == 1
        assert reopened.execute("SELECT COUNT(*) FROM canonical_dataset_registrations").fetchone()[0] == 1
        assert reopened.execute("SELECT COUNT(*) FROM canonicalization_records").fetchone()[0] == 1
        tables = {
            row[0]
            for row in reopened.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        }
        assert "execution_records" in tables
    finally:
        reopened.close()


def test_malformed_v2_schema_fails_without_rewriting_version(tmp_path) -> None:
    db_path = tmp_path / "registry.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE schema_version (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            version INTEGER NOT NULL
        )
        """
    )
    conn.execute("INSERT INTO schema_version (id, version) VALUES (1, 2)")
    _create_supported_v1_tables(conn)
    conn.execute("CREATE TABLE canonical_dataset_registrations (canonical_dataset_id TEXT PRIMARY KEY)")
    conn.execute(
        """
        CREATE TABLE canonicalization_records (
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
    conn.commit()
    conn.close()

    with pytest.raises(RuntimeError, match="version 2 is incompatible"):
        MetadataStore(db_path).initialize()

    reopened = sqlite3.connect(db_path)
    try:
        stored_version = reopened.execute("SELECT version FROM schema_version WHERE id = 1").fetchone()[0]
        tables = {
            row[0]
            for row in reopened.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        }
    finally:
        reopened.close()
    assert stored_version == 2
    assert "execution_records" not in tables


def test_equivalent_canonical_record_insertions_are_idempotent(tmp_path) -> None:
    metadata_store, result = _persisted_canonicalization(tmp_path)

    assert metadata_store.insert_canonical_dataset(result.canonical_dataset) == result.canonical_dataset
    assert metadata_store.insert_canonicalization_record(result.record) == result.record


def test_conflicting_canonical_dataset_record_with_same_stable_id_fails(tmp_path) -> None:
    metadata_store, result = _persisted_canonicalization(tmp_path)
    assert result.canonical_dataset is not None
    conflicting = result.canonical_dataset.model_copy(update={"row_count": 999})

    with pytest.raises(RuntimeError, match="stable provenance record conflict"):
        metadata_store.insert_canonical_dataset(conflicting)


def test_conflicting_canonicalization_record_with_same_stable_id_fails(tmp_path) -> None:
    metadata_store, result = _persisted_canonicalization(tmp_path)
    conflicting = result.record.model_copy(update={"canonical_row_count": 999})

    with pytest.raises(RuntimeError, match="stable provenance record conflict"):
        metadata_store.insert_canonicalization_record(conflicting)


def _persisted_canonicalization(tmp_path):
    source = tmp_path / "stable_orders.csv"
    source.write_text(
        "\n".join(
            [
                "order_id,order_line_id,order_date,product_id,quantity,line_revenue,currency",
                "o1,l1,2026-01-01,p1,1,10.00,USD",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    artifact_store = ArtifactStore(tmp_path / "stable_runtime")
    metadata_store = MetadataStore(tmp_path / "stable_registry.sqlite")
    registry = DatasetRegistry(artifact_store, metadata_store)
    dataset = registry.register_source(source, SourceType.CSV)
    request = CanonicalizationRequest(
        source_dataset_id=dataset.dataset_id,
        mapping=identity_mapping(
            (
                "order_id",
                "order_line_id",
                "order_date",
                "product_id",
                "quantity",
                "line_revenue",
                "currency",
            )
        ),
        eligibility_mode=EligibilityMode.UPSTREAM_ELIGIBLE_ONLY,
    )
    result = canonicalize_dataset(dataset, request, artifact_store)
    assert result.canonical_dataset is not None
    metadata_store.insert_canonical_dataset(result.canonical_dataset)
    metadata_store.insert_canonicalization_record(result.record)
    return metadata_store, result


def _create_supported_v1_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE dataset_registrations (
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
        CREATE TABLE artifact_references (
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
        CREATE TABLE run_records (
            run_id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL,
            run_status TEXT NOT NULL,
            record_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _create_supported_v2_tables(conn: sqlite3.Connection) -> None:
    _create_supported_v1_tables(conn)
    conn.execute(
        """
        CREATE TABLE canonical_dataset_registrations (
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
        CREATE TABLE canonicalization_records (
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
