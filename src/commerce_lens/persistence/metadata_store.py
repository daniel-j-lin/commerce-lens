"""Minimal SQLite metadata registry foundation."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from commerce_lens.contracts.common import ArtifactReference, ClaimState
from commerce_lens.contracts.evidence import (
    CanonicalDatasetReference,
    CanonicalizationRecord,
    DatasetReference,
    EvidenceAdmissibilityRecord,
    ClaimCandidate,
    ClaimDecision,
    claim_candidate_semantic_fingerprint,
    claim_decision_semantic_fingerprint,
)
from commerce_lens.contracts.execution import ExecutionRecord
from commerce_lens.contracts.requests import AnalysisRequest
from commerce_lens.contracts.sufficiency import DataSufficiencyResult
from commerce_lens.contracts.validation import ValidationRecord
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, sha256_file
from commerce_lens.persistence.artifact_store import ArtifactStore


SCHEMA_VERSION = 6
PHASE2_SCHEMA_VERSION = 2
PHASE3_SCHEMA_VERSION = 3
PHASE4_SCHEMA_VERSION = 4
PHASE5_SCHEMA_VERSION = 5

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

_PHASE3_TABLE_COLUMNS = {
    "execution_records": {
        "execution_id",
        "request_id",
        "plan_id",
        "plan_node_id",
        "metric_ref",
        "status",
        "result_ref",
        "result_artifact_id",
        "started_at",
        "ended_at",
        "record_json",
    },
}

_PHASE4_TABLE_COLUMNS = {
    "validation_records": {
        "validation_id",
        "execution_id",
        "result_ref",
        "metric_ref",
        "status",
        "failure_code",
        "validated_result_ref",
        "validated_result_artifact_id",
        "started_at",
        "ended_at",
        "record_json",
    },
}

_PHASE5_TABLE_COLUMNS = {
    "analysis_requests": {
        "request_id",
        "canonical_business_question_id",
        "dataset_ref_id",
        "request_artifact_id",
        "record_fingerprint",
        "created_at",
        "record_json",
    },
    "data_sufficiency_results": {
        "sufficiency_id",
        "request_id",
        "dataset_ref_id",
        "canonical_dataset_ref_id",
        "sufficiency_artifact_id",
        "state",
        "record_fingerprint",
        "record_json",
    },
    "evidence_admissibility_records": {
        "admissibility_id",
        "request_id",
        "sufficiency_id",
        "validated_result_id",
        "metric_ref",
        "status",
        "failure_code",
        "admissible_evidence_id",
        "admissible_evidence_artifact_id",
        "evidence_fingerprint",
        "started_at",
        "ended_at",
        "record_json",
    },
}


_PHASE6_TABLE_COLUMNS = {
    "claim_candidates": {
        "claim_candidate_id",
        "claim_id",
        "request_id",
        "claim_type",
        "metric_ref",
        "metric_definition_version",
        "dataset_ref_id",
        "canonical_dataset_ref_id",
        "canonical_dataset_fingerprint",
        "claim_candidate_fingerprint",
        "claim_candidate_artifact_id",
        "supporting_evidence_refs_json",
        "supporting_validated_result_refs_json",
        "created_at",
        "record_fingerprint",
        "record_json",
    },
    "claim_decisions": {
        "claim_decision_id",
        "decision_id",
        "claim_candidate_ref",
        "claim_state",
        "policy_id",
        "policy_version",
        "decision_fingerprint",
        "claim_decision_artifact_id",
        "supporting_evidence_refs_json",
        "supporting_validated_result_refs_json",
        "decided_at",
        "failure_code",
        "record_fingerprint",
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
                self._create_phase3_tables(conn)
                self._create_phase4_tables(conn)
                self._create_phase5_tables(conn)
                self._create_phase6_tables(conn)
                self._verify_phase6_schema(conn)
                conn.execute("INSERT INTO schema_version (id, version) VALUES (1, ?)", (SCHEMA_VERSION,))
                return

            stored_version = int(row["version"])
            if stored_version == 1:
                self._migrate_v1_to_v2(conn)
                self._migrate_v2_to_v3(conn)
                self._migrate_v3_to_v4(conn)
                self._migrate_v4_to_v5(conn)
                self._migrate_v5_to_v6(conn)
                return
            if stored_version == PHASE2_SCHEMA_VERSION:
                self._migrate_v2_to_v3(conn)
                self._migrate_v3_to_v4(conn)
                self._migrate_v4_to_v5(conn)
                self._migrate_v5_to_v6(conn)
                return
            if stored_version == PHASE3_SCHEMA_VERSION:
                self._migrate_v3_to_v4(conn)
                self._migrate_v4_to_v5(conn)
                self._migrate_v5_to_v6(conn)
                return
            if stored_version == PHASE4_SCHEMA_VERSION:
                self._migrate_v4_to_v5(conn)
                self._migrate_v5_to_v6(conn)
                return
            if stored_version == PHASE5_SCHEMA_VERSION:
                self._migrate_v5_to_v6(conn)
                return
            if stored_version == SCHEMA_VERSION:
                self._verify_phase6_schema(conn)
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

    def insert_artifact_reference(self, artifact: ArtifactReference) -> ArtifactReference:
        payload = artifact.model_dump_json()
        with self._connect() as conn:
            if not self._stable_record_needs_insert(
                conn,
                table="artifact_references",
                id_column="artifact_id",
                stable_id=artifact.artifact_id,
                payload=payload,
            ):
                return artifact
            conn.execute(
                """
                INSERT INTO artifact_references (
                    artifact_id, path, fingerprint, media_type, size_bytes, record_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact.artifact_id,
                    artifact.path,
                    artifact.fingerprint,
                    artifact.media_type,
                    artifact.size_bytes,
                    payload,
                ),
            )
        return self.get_artifact_reference(artifact.artifact_id) or artifact

    def get_artifact_reference(self, artifact_id: str) -> ArtifactReference | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT record_json FROM artifact_references WHERE artifact_id = ?",
                (artifact_id,),
            ).fetchone()
        if row is None:
            return None
        return ArtifactReference.model_validate(json.loads(row["record_json"]))

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

    def insert_execution_record(self, execution_record: ExecutionRecord) -> ExecutionRecord:
        payload = execution_record.model_dump_json()
        result_artifact_id = execution_record.output_artifacts[0].artifact_id if execution_record.output_artifacts else None
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO execution_records (
                    execution_id, request_id, plan_id, plan_node_id, metric_ref, status,
                    result_ref, result_artifact_id, started_at, ended_at, record_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    execution_record.execution_id,
                    execution_record.request_id,
                    execution_record.plan_id,
                    execution_record.plan_node_id,
                    execution_record.metric_refs[0] if execution_record.metric_refs else None,
                    execution_record.status.value,
                    execution_record.result_ref,
                    result_artifact_id,
                    execution_record.started_at.isoformat(),
                    execution_record.ended_at.isoformat() if execution_record.ended_at is not None else None,
                    payload,
                ),
            )
        return self.get_execution_record(execution_record.execution_id) or execution_record

    def get_execution_record(self, execution_id: str) -> ExecutionRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT record_json FROM execution_records WHERE execution_id = ?",
                (execution_id,),
            ).fetchone()
        if row is None:
            return None
        return ExecutionRecord.model_validate(json.loads(row["record_json"]))

    def list_execution_records(self) -> list[ExecutionRecord]:
        with self._connect() as conn:
            rows = conn.execute("SELECT record_json FROM execution_records ORDER BY started_at, execution_id").fetchall()
        return [ExecutionRecord.model_validate(json.loads(row["record_json"])) for row in rows]

    def insert_validation_record(self, validation_record: ValidationRecord) -> ValidationRecord:
        payload = validation_record.model_dump_json()
        artifact_id = (
            validation_record.validated_result_artifact_ref.artifact_id
            if validation_record.validated_result_artifact_ref is not None
            else None
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO validation_records (
                    validation_id, execution_id, result_ref, metric_ref, status,
                    failure_code, validated_result_ref, validated_result_artifact_id,
                    started_at, ended_at, record_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    validation_record.validation_id,
                    validation_record.execution_id,
                    validation_record.target_result_ref,
                    validation_record.metric_ref,
                    validation_record.status.value,
                    validation_record.failure_code,
                    validation_record.validated_result_ref,
                    artifact_id,
                    validation_record.started_at.isoformat(),
                    validation_record.ended_at.isoformat() if validation_record.ended_at is not None else None,
                    payload,
                ),
            )
        return self.get_validation_record(validation_record.validation_id) or validation_record

    def get_validation_record(self, validation_id: str) -> ValidationRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT record_json FROM validation_records WHERE validation_id = ?",
                (validation_id,),
            ).fetchone()
        if row is None:
            return None
        return ValidationRecord.model_validate(json.loads(row["record_json"]))

    def list_validation_records(self) -> list[ValidationRecord]:
        with self._connect() as conn:
            rows = conn.execute("SELECT record_json FROM validation_records ORDER BY started_at, validation_id").fetchall()
        return [ValidationRecord.model_validate(json.loads(row["record_json"])) for row in rows]

    def insert_analysis_request(
        self,
        request: AnalysisRequest,
        artifact_store: ArtifactStore | None = None,
    ) -> AnalysisRequest:
        artifact_store = self._authority_artifact_store(artifact_store)
        payload = request.model_dump_json()
        payload_obj = json.loads(payload)
        record_fingerprint = canonical_json_fingerprint(payload_obj)
        with self._connect() as conn:
            if not self._stable_record_needs_insert(
                conn,
                table="analysis_requests",
                id_column="request_id",
                stable_id=request.request_id,
                payload=payload,
            ):
                return request
        artifact = artifact_store.write_json_artifact(
            Path("runs") / request.request_id / "analysis_request" / f"{request.request_id}.json",
            payload_obj,
        )
        self.insert_artifact_reference(artifact)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO analysis_requests (
                    request_id, canonical_business_question_id, dataset_ref_id,
                    request_artifact_id, record_fingerprint, created_at, record_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.request_id,
                    request.canonical_business_question_id,
                    request.dataset_ref_id,
                    artifact.artifact_id,
                    record_fingerprint,
                    request.created_at.isoformat(),
                    payload,
                ),
            )
        return self.get_analysis_request(request.request_id, artifact_store) or request

    def get_analysis_request(
        self,
        request_id: str,
        artifact_store: ArtifactStore | None = None,
    ) -> AnalysisRequest | None:
        artifact_store = self._authority_artifact_store(artifact_store)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT request_id, canonical_business_question_id, dataset_ref_id,
                       request_artifact_id, record_fingerprint, created_at, record_json
                FROM analysis_requests
                WHERE request_id = ?
                """,
                (request_id,),
            ).fetchone()
        if row is None:
            return None
        payload = self._verified_authority_payload(
            row,
            artifact_store,
            id_column="request_id",
            expected_id=request_id,
            artifact_id_column="request_artifact_id",
            record_type="analysis request",
        )
        request = AnalysisRequest.model_validate(payload)
        if request.request_id != request_id:
            raise RuntimeError(f"analysis request artifact identity mismatch for {request_id}")
        if row["canonical_business_question_id"] != request.canonical_business_question_id:
            raise RuntimeError(f"analysis request indexed authority mismatch for {request_id}")
        if row["dataset_ref_id"] != request.dataset_ref_id:
            raise RuntimeError(f"analysis request indexed authority mismatch for {request_id}")
        if row["created_at"] != request.created_at.isoformat():
            raise RuntimeError(f"analysis request indexed authority mismatch for {request_id}")
        return request

    def insert_data_sufficiency_result(
        self,
        result: DataSufficiencyResult,
        artifact_store: ArtifactStore | None = None,
    ) -> DataSufficiencyResult:
        artifact_store = self._authority_artifact_store(artifact_store)
        payload = result.model_dump_json()
        payload_obj = json.loads(payload)
        record_fingerprint = canonical_json_fingerprint(payload_obj)
        with self._connect() as conn:
            if not self._stable_record_needs_insert(
                conn,
                table="data_sufficiency_results",
                id_column="sufficiency_id",
                stable_id=result.sufficiency_id,
                payload=payload,
            ):
                return result
        artifact = artifact_store.write_json_artifact(
            Path("runs") / result.request_id / "data_sufficiency" / f"{result.sufficiency_id}.json",
            payload_obj,
        )
        self.insert_artifact_reference(artifact)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO data_sufficiency_results (
                    sufficiency_id, request_id, dataset_ref_id, canonical_dataset_ref_id,
                    sufficiency_artifact_id, state, record_fingerprint, record_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.sufficiency_id,
                    result.request_id,
                    result.dataset_ref_id,
                    result.canonical_dataset_ref_id,
                    artifact.artifact_id,
                    result.state.value,
                    record_fingerprint,
                    payload,
                ),
            )
        return self.get_data_sufficiency_result(result.sufficiency_id, artifact_store) or result

    def get_data_sufficiency_result(
        self,
        sufficiency_id: str,
        artifact_store: ArtifactStore | None = None,
    ) -> DataSufficiencyResult | None:
        artifact_store = self._authority_artifact_store(artifact_store)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT sufficiency_id, request_id, dataset_ref_id, canonical_dataset_ref_id,
                       sufficiency_artifact_id, state, record_fingerprint, record_json
                FROM data_sufficiency_results
                WHERE sufficiency_id = ?
                """,
                (sufficiency_id,),
            ).fetchone()
        if row is None:
            return None
        payload = self._verified_authority_payload(
            row,
            artifact_store,
            id_column="sufficiency_id",
            expected_id=sufficiency_id,
            artifact_id_column="sufficiency_artifact_id",
            record_type="data sufficiency",
        )
        result = DataSufficiencyResult.model_validate(payload)
        if result.sufficiency_id != sufficiency_id:
            raise RuntimeError(f"data sufficiency artifact identity mismatch for {sufficiency_id}")
        indexed = {
            "request_id": result.request_id,
            "dataset_ref_id": result.dataset_ref_id,
            "canonical_dataset_ref_id": result.canonical_dataset_ref_id,
            "state": result.state.value,
        }
        for key, expected in indexed.items():
            if row[key] != expected:
                raise RuntimeError(f"data sufficiency indexed authority mismatch for {sufficiency_id}")
        return result

    def insert_evidence_admissibility_record(
        self,
        record: EvidenceAdmissibilityRecord,
    ) -> EvidenceAdmissibilityRecord:
        payload = record.model_dump_json()
        artifact_id = (
            record.admissible_evidence_artifact_ref.artifact_id
            if record.admissible_evidence_artifact_ref is not None
            else None
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO evidence_admissibility_records (
                    admissibility_id, request_id, sufficiency_id, validated_result_id,
                    metric_ref, status, failure_code, admissible_evidence_id,
                    admissible_evidence_artifact_id, evidence_fingerprint,
                    started_at, ended_at, record_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.admissibility_id,
                    record.request_id,
                    record.sufficiency_id,
                    record.validated_result_id,
                    record.metric_ref,
                    record.status.value,
                    record.failure_code,
                    record.admissible_evidence_id,
                    artifact_id,
                    record.evidence_fingerprint,
                    record.started_at.isoformat(),
                    record.ended_at.isoformat(),
                    payload,
                ),
            )
        return self.get_evidence_admissibility_record(record.admissibility_id) or record

    def get_evidence_admissibility_record(
        self,
        admissibility_id: str,
    ) -> EvidenceAdmissibilityRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT record_json FROM evidence_admissibility_records WHERE admissibility_id = ?",
                (admissibility_id,),
            ).fetchone()
        if row is None:
            return None
        return EvidenceAdmissibilityRecord.model_validate(json.loads(row["record_json"]))

    def list_evidence_admissibility_records(self) -> list[EvidenceAdmissibilityRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT record_json FROM evidence_admissibility_records ORDER BY started_at, admissibility_id"
            ).fetchall()
        return [EvidenceAdmissibilityRecord.model_validate(json.loads(row["record_json"])) for row in rows]

    def insert_claim_candidate(
        self,
        candidate: ClaimCandidate,
        artifact_store: ArtifactStore | None = None,
    ) -> ClaimCandidate:
        artifact_store = self._authority_artifact_store(artifact_store)
        expected_fingerprint = claim_candidate_semantic_fingerprint(candidate)
        if candidate.claim_candidate_fingerprint not in (None, expected_fingerprint):
            raise RuntimeError(f"ClaimCandidate semantic fingerprint mismatch for {candidate.claim_candidate_id}")
        persisted = candidate.model_copy(update={"claim_candidate_fingerprint": expected_fingerprint})
        payload = persisted.model_dump_json()
        payload_obj = json.loads(payload)
        record_fingerprint = canonical_json_fingerprint(payload_obj)
        request_id = persisted.request_id
        with self._connect() as conn:
            if not self._stable_record_needs_insert(
                conn,
                table="claim_candidates",
                id_column="claim_candidate_id",
                stable_id=persisted.claim_candidate_id,
                payload=payload,
            ):
                return persisted
        artifact = artifact_store.write_json_artifact(
            Path("runs") / str(request_id or persisted.claim_candidate_id) / "claim_candidates" / f"{persisted.claim_candidate_id}.json",
            payload_obj,
        )
        self.insert_artifact_reference(artifact)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO claim_candidates (
                    claim_candidate_id, claim_id, request_id, claim_type, metric_ref,
                    metric_definition_version, dataset_ref_id, canonical_dataset_ref_id,
                    canonical_dataset_fingerprint, claim_candidate_fingerprint,
                    claim_candidate_artifact_id, supporting_evidence_refs_json,
                    supporting_validated_result_refs_json, created_at, record_fingerprint, record_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    persisted.claim_candidate_id,
                    persisted.claim_id,
                    request_id,
                    persisted.claim_type.value,
                    persisted.metric_ref,
                    persisted.metric_definition_version,
                    persisted.dataset_ref_id,
                    persisted.canonical_dataset_ref_id,
                    persisted.canonical_dataset_fingerprint,
                    persisted.claim_candidate_fingerprint,
                    artifact.artifact_id,
                    json.dumps(list(persisted.supporting_evidence_refs), sort_keys=True),
                    json.dumps(list(persisted.supporting_validated_result_refs), sort_keys=True),
                    persisted.metadata.get("created_at"),
                    record_fingerprint,
                    payload,
                ),
            )
        return self.get_claim_candidate(persisted.claim_candidate_id, artifact_store) or persisted

    def get_claim_candidate(
        self,
        claim_candidate_id: str,
        artifact_store: ArtifactStore | None = None,
    ) -> ClaimCandidate | None:
        artifact_store = self._authority_artifact_store(artifact_store)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT claim_candidate_id, claim_id, request_id, claim_type, metric_ref,
                       metric_definition_version, dataset_ref_id, canonical_dataset_ref_id,
                       canonical_dataset_fingerprint, claim_candidate_fingerprint,
                       claim_candidate_artifact_id, supporting_evidence_refs_json,
                       supporting_validated_result_refs_json, created_at, record_fingerprint, record_json
                FROM claim_candidates
                WHERE claim_candidate_id = ?
                """,
                (claim_candidate_id,),
            ).fetchone()
        if row is None:
            return None
        payload = self._verified_authority_payload(
            row,
            artifact_store,
            id_column="claim_candidate_id",
            expected_id=claim_candidate_id,
            artifact_id_column="claim_candidate_artifact_id",
            record_type="claim candidate",
        )
        candidate = ClaimCandidate.model_validate(payload)
        expected_fingerprint = claim_candidate_semantic_fingerprint(candidate)
        indexed = {
            "claim_id": candidate.claim_id,
            "claim_type": candidate.claim_type.value,
            "metric_ref": candidate.metric_ref,
            "metric_definition_version": candidate.metric_definition_version,
            "request_id": candidate.request_id,
            "dataset_ref_id": candidate.dataset_ref_id,
            "canonical_dataset_ref_id": candidate.canonical_dataset_ref_id,
            "canonical_dataset_fingerprint": candidate.canonical_dataset_fingerprint,
            "claim_candidate_fingerprint": expected_fingerprint,
            "supporting_evidence_refs_json": json.dumps(list(candidate.supporting_evidence_refs), sort_keys=True),
            "supporting_validated_result_refs_json": json.dumps(list(candidate.supporting_validated_result_refs), sort_keys=True),
        }
        for key, expected in indexed.items():
            if row[key] != expected:
                raise RuntimeError(f"claim candidate indexed authority mismatch for {claim_candidate_id}")
        if candidate.claim_candidate_fingerprint != expected_fingerprint:
            raise RuntimeError(f"claim candidate semantic fingerprint mismatch for {claim_candidate_id}")
        return candidate

    def list_claim_candidates(self) -> list[ClaimCandidate]:
        with self._connect() as conn:
            rows = conn.execute("SELECT claim_candidate_id FROM claim_candidates ORDER BY claim_candidate_id").fetchall()
        return [item for row in rows if (item := self.get_claim_candidate(row["claim_candidate_id"])) is not None]

    def insert_claim_decision(
        self,
        decision: ClaimDecision,
        artifact_store: ArtifactStore | None = None,
    ) -> ClaimDecision:
        if decision.claim_state is ClaimState.ADMISSIBLE:
            raise RuntimeError(
                "Admissible ClaimDecision must be persisted by the deterministic Claim admissibility evaluator"
            )
        derived_fingerprint = self._claim_candidate_fingerprint_for_decision(decision, artifact_store)
        return self._insert_claim_decision_record(
            decision,
            artifact_store,
            claim_candidate_fingerprint=derived_fingerprint,
        )

    def _insert_evaluated_claim_decision(
        self,
        decision: ClaimDecision,
        artifact_store: ArtifactStore | None = None,
        *,
        claim_candidate_fingerprint: str | None = None,
    ) -> ClaimDecision:
        derived_fingerprint = self._claim_candidate_fingerprint_for_decision(decision, artifact_store)
        if claim_candidate_fingerprint is not None and claim_candidate_fingerprint != derived_fingerprint:
            raise RuntimeError(f"ClaimDecision candidate authority mismatch for {decision.claim_decision_id}")
        if decision.claim_state is ClaimState.ADMISSIBLE and derived_fingerprint is None:
            raise RuntimeError(f"Admissible ClaimDecision lacks authentic ClaimCandidate authority for {decision.claim_decision_id}")
        return self._insert_claim_decision_record(
            decision,
            artifact_store,
            claim_candidate_fingerprint=derived_fingerprint,
        )

    def _insert_claim_decision_record(
        self,
        decision: ClaimDecision,
        artifact_store: ArtifactStore | None = None,
        *,
        claim_candidate_fingerprint: str | None = None,
    ) -> ClaimDecision:
        artifact_store = self._authority_artifact_store(artifact_store)
        decision_id = decision.decision_id or decision.claim_decision_id
        prepared = decision.model_copy(update={"decision_id": decision_id})
        expected_fingerprint = claim_decision_semantic_fingerprint(
            prepared,
            claim_candidate_fingerprint=claim_candidate_fingerprint,
        )
        if prepared.decision_fingerprint not in (None, expected_fingerprint):
            raise RuntimeError(f"ClaimDecision semantic fingerprint mismatch for {prepared.claim_decision_id}")
        persisted = prepared.model_copy(update={"decision_fingerprint": expected_fingerprint})
        payload = persisted.model_dump_json()
        payload_obj = json.loads(payload)
        record_fingerprint = canonical_json_fingerprint(payload_obj)
        run_ref = persisted.claim_candidate_ref or persisted.claim_decision_id
        artifact = artifact_store.write_json_artifact(
            Path("runs") / run_ref / "claim_decisions" / f"{persisted.claim_decision_id}.json",
            payload_obj,
        )
        self.insert_artifact_reference(artifact)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO claim_decisions (
                    claim_decision_id, decision_id, claim_candidate_ref, claim_state,
                    policy_id, policy_version, decision_fingerprint,
                    claim_decision_artifact_id, supporting_evidence_refs_json,
                    supporting_validated_result_refs_json, decided_at, failure_code,
                    record_fingerprint, record_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    persisted.claim_decision_id,
                    persisted.decision_id,
                    persisted.claim_candidate_ref,
                    persisted.claim_state.value,
                    persisted.policy_id,
                    persisted.policy_version,
                    persisted.decision_fingerprint,
                    artifact.artifact_id,
                    json.dumps(list(persisted.supporting_evidence_refs), sort_keys=True),
                    json.dumps(list(persisted.supporting_validated_result_refs), sort_keys=True),
                    persisted.decided_at.isoformat(),
                    persisted.failure_code,
                    record_fingerprint,
                    payload,
                ),
            )
        return self.get_claim_decision_record(persisted.claim_decision_id, artifact_store) or persisted

    def get_claim_decision_record(
        self,
        claim_decision_id: str,
        artifact_store: ArtifactStore | None = None,
    ) -> ClaimDecision | None:
        artifact_store = self._authority_artifact_store(artifact_store)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT claim_decision_id, decision_id, claim_candidate_ref, claim_state,
                       policy_id, policy_version, decision_fingerprint,
                       claim_decision_artifact_id, supporting_evidence_refs_json,
                       supporting_validated_result_refs_json, decided_at, failure_code,
                       record_fingerprint, record_json
                FROM claim_decisions
                WHERE claim_decision_id = ?
                """,
                (claim_decision_id,),
            ).fetchone()
        if row is None:
            return None
        payload = self._verified_authority_payload(
            row,
            artifact_store,
            id_column="claim_decision_id",
            expected_id=claim_decision_id,
            artifact_id_column="claim_decision_artifact_id",
            record_type="claim decision",
        )
        decision = ClaimDecision.model_validate(payload)
        claim_candidate_fingerprint = self._claim_candidate_fingerprint_for_decision(decision, artifact_store)
        expected_fingerprint = claim_decision_semantic_fingerprint(
            decision,
            claim_candidate_fingerprint=claim_candidate_fingerprint,
        )
        indexed = {
            "decision_id": decision.decision_id,
            "claim_candidate_ref": decision.claim_candidate_ref,
            "claim_state": decision.claim_state.value,
            "policy_id": decision.policy_id,
            "policy_version": decision.policy_version,
            "decision_fingerprint": expected_fingerprint,
            "supporting_evidence_refs_json": json.dumps(list(decision.supporting_evidence_refs), sort_keys=True),
            "supporting_validated_result_refs_json": json.dumps(list(decision.supporting_validated_result_refs), sort_keys=True),
            "decided_at": decision.decided_at.isoformat(),
            "failure_code": decision.failure_code,
        }
        for key, expected in indexed.items():
            if row[key] != expected:
                raise RuntimeError(f"claim decision indexed authority mismatch for {claim_decision_id}")
        if decision.decision_fingerprint != expected_fingerprint:
            raise RuntimeError(f"claim decision semantic fingerprint mismatch for {claim_decision_id}")
        return decision

    def list_claim_decision_records(self, artifact_store: ArtifactStore | None = None) -> list[ClaimDecision]:
        artifact_store = self._authority_artifact_store(artifact_store)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT claim_decision_id FROM claim_decisions ORDER BY decided_at, claim_decision_id"
            ).fetchall()
        return [
            item
            for row in rows
            if (item := self.get_claim_decision_record(row["claim_decision_id"], artifact_store)) is not None
        ]

    def get_claim_decision_artifact_reference(self, claim_decision_id: str) -> ArtifactReference | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT claim_decision_artifact_id FROM claim_decisions WHERE claim_decision_id = ?",
                (claim_decision_id,),
            ).fetchone()
        if row is None:
            return None
        return self.get_artifact_reference(row["claim_decision_artifact_id"])

    def get_claim_decision(
        self,
        claim_decision_id: str,
        artifact_store: ArtifactStore | None = None,
    ) -> ClaimDecision | None:
        decision = self.get_claim_decision_record(claim_decision_id, artifact_store)
        if decision is not None and decision.claim_state is ClaimState.ADMISSIBLE:
            raise RuntimeError(
                "get_claim_decision returns persistence records only; use the P8 authoritative "
                "ClaimDecision retrieval API for Admissible material permission"
            )
        return decision

    def list_claim_decisions(self, artifact_store: ArtifactStore | None = None) -> list[ClaimDecision]:
        decisions = self.list_claim_decision_records(artifact_store)
        if any(decision.claim_state is ClaimState.ADMISSIBLE for decision in decisions):
            raise RuntimeError(
                "list_claim_decisions returns persistence records only; use the P8 authoritative "
                "ClaimDecision list API for Admissible material permission"
            )
        return decisions

    def _claim_candidate_fingerprint_for_decision(
        self,
        decision: ClaimDecision,
        artifact_store: ArtifactStore | None = None,
    ) -> str | None:
        if not decision.claim_candidate_ref:
            if decision.claim_state is ClaimState.ADMISSIBLE:
                raise RuntimeError(f"Admissible ClaimDecision lacks ClaimCandidate reference for {decision.claim_decision_id}")
            return None
        try:
            candidate = self.get_claim_candidate(decision.claim_candidate_ref, artifact_store)
        except RuntimeError:
            if decision.claim_state is ClaimState.ADMISSIBLE:
                raise
            return None
        if candidate is None:
            if decision.claim_state is ClaimState.ADMISSIBLE:
                raise RuntimeError(
                    f"Admissible ClaimDecision lacks authentic ClaimCandidate authority for {decision.claim_decision_id}"
                )
            return None
        return candidate.claim_candidate_fingerprint

    def _migrate_v1_to_v2(self, conn: sqlite3.Connection) -> None:
        self._verify_phase1_schema(conn)
        self._create_phase2_tables(conn)
        self._verify_phase2_schema(conn)
        conn.execute("UPDATE schema_version SET version = ? WHERE id = 1", (PHASE2_SCHEMA_VERSION,))

    def _migrate_v2_to_v3(self, conn: sqlite3.Connection) -> None:
        self._verify_phase2_schema(conn)
        self._create_phase3_tables(conn)
        self._verify_phase3_schema(conn)
        conn.execute("UPDATE schema_version SET version = ? WHERE id = 1", (PHASE3_SCHEMA_VERSION,))

    def _migrate_v3_to_v4(self, conn: sqlite3.Connection) -> None:
        self._verify_phase3_schema(conn)
        self._create_phase4_tables(conn)
        self._verify_phase4_schema(conn)
        conn.execute("UPDATE schema_version SET version = ? WHERE id = 1", (PHASE4_SCHEMA_VERSION,))

    def _migrate_v4_to_v5(self, conn: sqlite3.Connection) -> None:
        self._verify_phase4_schema(conn)
        self._create_phase5_tables(conn)
        self._verify_phase5_schema(conn)
        conn.execute("UPDATE schema_version SET version = ? WHERE id = 1", (PHASE5_SCHEMA_VERSION,))

    def _migrate_v5_to_v6(self, conn: sqlite3.Connection) -> None:
        self._verify_phase5_schema(conn)
        self._create_phase6_tables(conn)
        self._verify_phase6_schema(conn)
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

    def _create_phase3_tables(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS execution_records (
                execution_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                plan_id TEXT,
                plan_node_id TEXT,
                metric_ref TEXT,
                status TEXT NOT NULL,
                result_ref TEXT,
                result_artifact_id TEXT,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                record_json TEXT NOT NULL
            )
            """
        )

    def _create_phase4_tables(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS validation_records (
                validation_id TEXT PRIMARY KEY,
                execution_id TEXT NOT NULL,
                result_ref TEXT NOT NULL,
                metric_ref TEXT,
                status TEXT NOT NULL,
                failure_code TEXT,
                validated_result_ref TEXT,
                validated_result_artifact_id TEXT,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                record_json TEXT NOT NULL
            )
            """
        )

    def _create_phase5_tables(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_requests (
                request_id TEXT PRIMARY KEY,
                canonical_business_question_id TEXT NOT NULL,
                dataset_ref_id TEXT NOT NULL,
                request_artifact_id TEXT NOT NULL,
                record_fingerprint TEXT NOT NULL,
                created_at TEXT NOT NULL,
                record_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS data_sufficiency_results (
                sufficiency_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                dataset_ref_id TEXT NOT NULL,
                canonical_dataset_ref_id TEXT,
                sufficiency_artifact_id TEXT NOT NULL,
                state TEXT NOT NULL,
                record_fingerprint TEXT NOT NULL,
                record_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evidence_admissibility_records (
                admissibility_id TEXT PRIMARY KEY,
                request_id TEXT,
                sufficiency_id TEXT,
                validated_result_id TEXT,
                metric_ref TEXT,
                status TEXT NOT NULL,
                failure_code TEXT,
                admissible_evidence_id TEXT,
                admissible_evidence_artifact_id TEXT,
                evidence_fingerprint TEXT,
                started_at TEXT NOT NULL,
                ended_at TEXT NOT NULL,
                record_json TEXT NOT NULL
            )
            """
        )

    def _create_phase6_tables(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS claim_candidates (
                claim_candidate_id TEXT PRIMARY KEY,
                claim_id TEXT,
                request_id TEXT,
                claim_type TEXT NOT NULL,
                metric_ref TEXT,
                metric_definition_version TEXT,
                dataset_ref_id TEXT,
                canonical_dataset_ref_id TEXT,
                canonical_dataset_fingerprint TEXT,
                claim_candidate_fingerprint TEXT NOT NULL,
                claim_candidate_artifact_id TEXT NOT NULL,
                supporting_evidence_refs_json TEXT NOT NULL,
                supporting_validated_result_refs_json TEXT NOT NULL,
                created_at TEXT,
                record_fingerprint TEXT NOT NULL,
                record_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS claim_decisions (
                claim_decision_id TEXT PRIMARY KEY,
                decision_id TEXT,
                claim_candidate_ref TEXT,
                claim_state TEXT NOT NULL,
                policy_id TEXT NOT NULL,
                policy_version TEXT NOT NULL,
                decision_fingerprint TEXT NOT NULL,
                claim_decision_artifact_id TEXT NOT NULL,
                supporting_evidence_refs_json TEXT NOT NULL,
                supporting_validated_result_refs_json TEXT NOT NULL,
                decided_at TEXT NOT NULL,
                failure_code TEXT,
                record_fingerprint TEXT NOT NULL,
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

    def _verify_phase3_schema(self, conn: sqlite3.Connection) -> None:
        self._verify_phase2_schema(conn)
        for table, expected_columns in _PHASE3_TABLE_COLUMNS.items():
            actual_columns = self._table_columns(conn, table)
            if actual_columns != expected_columns:
                raise RuntimeError(f"metadata schema version 3 is incompatible: {table}")

    def _verify_phase4_schema(self, conn: sqlite3.Connection) -> None:
        self._verify_phase3_schema(conn)
        for table, expected_columns in _PHASE4_TABLE_COLUMNS.items():
            actual_columns = self._table_columns(conn, table)
            if actual_columns != expected_columns:
                raise RuntimeError(f"metadata schema version 4 is incompatible: {table}")

    def _verify_phase5_schema(self, conn: sqlite3.Connection) -> None:
        self._verify_phase4_schema(conn)
        for table, expected_columns in _PHASE5_TABLE_COLUMNS.items():
            actual_columns = self._table_columns(conn, table)
            if actual_columns != expected_columns:
                raise RuntimeError(f"metadata schema version 5 is incompatible: {table}")

    def _verify_phase6_schema(self, conn: sqlite3.Connection) -> None:
        self._verify_phase5_schema(conn)
        for table, expected_columns in _PHASE6_TABLE_COLUMNS.items():
            actual_columns = self._table_columns(conn, table)
            if actual_columns != expected_columns:
                raise RuntimeError(f"metadata schema version 6 is incompatible: {table}")

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

    def _verified_authority_payload(
        self,
        row: sqlite3.Row,
        artifact_store: ArtifactStore,
        *,
        id_column: str,
        expected_id: str,
        artifact_id_column: str,
        record_type: str,
    ) -> dict:
        row_payload = json.loads(row["record_json"])
        if canonical_json_fingerprint(row_payload) != row["record_fingerprint"]:
            raise RuntimeError(f"{record_type} durable authority tamper detected for {expected_id}")
        artifact = self.get_artifact_reference(row[artifact_id_column])
        if artifact is None:
            raise RuntimeError(f"{record_type} authority artifact reference missing for {expected_id}")
        path = artifact_store.safe_path(artifact.path)
        if not path.is_file():
            raise RuntimeError(f"{record_type} authority artifact missing for {expected_id}")
        if artifact.fingerprint is None or sha256_file(path) != artifact.fingerprint:
            raise RuntimeError(f"{record_type} authority artifact hash mismatch for {expected_id}")
        artifact_payload = json.loads(path.read_text(encoding="utf-8"))
        if artifact_payload.get(id_column) != expected_id:
            raise RuntimeError(f"{record_type} authority artifact identity mismatch for {expected_id}")
        if artifact_payload != row_payload:
            raise RuntimeError(f"{record_type} row cache mismatches immutable artifact for {expected_id}")
        if row["record_fingerprint"] != canonical_json_fingerprint(artifact_payload):
            raise RuntimeError(f"{record_type} fingerprint mismatches immutable artifact for {expected_id}")
        return artifact_payload

    def _authority_artifact_store(self, artifact_store: ArtifactStore | None) -> ArtifactStore:
        return artifact_store or ArtifactStore(self.db_path.parent / "artifacts")

    def _quote_literal(self, value: str) -> str:
        return "'" + value.replace("'", "''") + "'"

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn


def _first_non_empty(*values):
    for value in values:
        if value:
            return value
    return None
