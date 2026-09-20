"""F2-A self-contained local evidence retention lifecycle."""

from __future__ import annotations

import json
import shutil
import sqlite3
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

from commerce_lens import __version__ as PACKAGE_VERSION
from commerce_lens.contracts.common import ArtifactReference, utc_now
from commerce_lens.contracts.evidence import AdmissibleEvidence
from commerce_lens.contracts.execution import ExecutedResult
from commerce_lens.contracts.results import AnalysisResult
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, generate_id, sha256_file
from commerce_lens.contracts.validation import ValidatedResult
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.manifests import (
    RetainedRunManifest,
    RetainedRunRecord,
    RetentionStatus,
    RunLifecycleStatus,
)
from commerce_lens.persistence.metadata_store import MetadataStore


class RetentionError(RuntimeError):
    """Raised when a retained run cannot be finalized or verified."""


class RetainedRunSession:
    """Own one isolated retained run directory and its paired stores."""

    COMPLETE_MARKER = "complete.marker"

    def __init__(self, retention_root: str | Path, run_id: str | None = None) -> None:
        self.retention_root = Path(retention_root).expanduser().resolve()
        self.run_id = run_id or generate_id("run")
        if Path(self.run_id).name != self.run_id or self.run_id in {"", ".", ".."}:
            raise ValueError("run_id must be a single safe path component")
        self.run_root = self.retention_root / self.run_id
        if self.run_root.exists():
            raise FileExistsError(f"retained run already exists: {self.run_id}")
        self.run_root.mkdir(parents=True, exist_ok=False)
        self.artifact_store = ArtifactStore(self.run_root / "artifacts")
        self.metadata_store = MetadataStore(self.run_root / "metadata.sqlite")
        self.artifact_store.ensure_layout()
        self.metadata_store.initialize()
        self.created_at = utc_now()
        self._context_artifacts: list[ArtifactReference] = []
        self._declaration_artifact: ArtifactReference | None = None
        self._declaration_payload: dict[str, Any] | None = None
        self._write_initial_manifest()

    @classmethod
    def begin(cls, retention_root: str | Path) -> "RetainedRunSession":
        return cls(retention_root)

    def _write_initial_manifest(self) -> None:
        manifest = RetainedRunManifest(
            run_id=self.run_id,
            created_at=self.created_at,
            lifecycle_status=RunLifecycleStatus.INITIALIZING,
            retention_status=RetentionStatus.RETAINED_INCOMPLETE,
            package_version=PACKAGE_VERSION,
        )
        self._write_manifest(manifest)
        self.metadata_store.insert_retained_run(
            RetainedRunRecord(
                run_id=self.run_id,
                lifecycle_status=manifest.lifecycle_status,
                retention_status=manifest.retention_status,
                manifest_path="manifest.json",
                created_at=self.created_at,
            )
        )

    def capture_context(self, *, intent: Any, request: Any, canonicalization_request: Any) -> None:
        self._set_lifecycle(RunLifecycleStatus.WRITING)
        for name, value in (
            ("structured_intent", intent),
            ("canonicalization_request", canonicalization_request),
        ):
            payload = _jsonable(value)
            artifact = self.artifact_store.write_json_artifact(
                Path("runs") / self.run_id / "context" / f"{name}.json", payload
            )
            self.metadata_store.insert_artifact_reference(artifact)
            self._context_artifacts.append(artifact)
        request_id = getattr(request, "request_id", None)
        self._update_manifest_metadata(request_id=request_id)

    def capture_declaration(self, declaration: Any, artifact: ArtifactReference) -> None:
        self._declaration_artifact = artifact
        self._declaration_payload = _jsonable(declaration)
        self._update_manifest_metadata()

    def finalize(
        self,
        outcome: Any,
        *,
        public_payload: dict[str, Any],
        plugin_version: str | None = None,
    ) -> RetainedRunManifest:
        """Persist final projections, verify all links, then mark the run complete."""
        self._set_lifecycle(RunLifecycleStatus.VERIFYING)
        analysis_result = getattr(outcome, "analysis_result", None)
        request = getattr(outcome, "request", None)
        if analysis_result is None or request is None:
            reason = "retained runs require a persisted AnalysisResult and AnalysisRequest"
            self._fail(reason)
            raise RetentionError(reason)
        try:
            result_artifact = self.artifact_store.write_json_artifact(
                Path("runs") / self.run_id / "final" / "analysis_result.json",
                analysis_result.model_dump(mode="json"),
            )
            self.metadata_store.insert_artifact_reference(result_artifact)
            response_payload = _jsonable(public_payload)
            if not isinstance(response_payload, dict):
                response_payload = {}
            response_payload.update({"run_id": self.run_id, "request_id": request.request_id})
            response_artifact = self.artifact_store.write_json_artifact(
                Path("runs") / self.run_id / "final" / "public_response.json",
                response_payload,
            )
            self.metadata_store.insert_artifact_reference(response_artifact)
            manifest = self._build_manifest(
                outcome,
                request=request,
                result_artifact=result_artifact,
                response_artifact=response_artifact,
                plugin_version=plugin_version,
            )
            # Persist the final refs while the run is still non-complete. The
            # disk-backed verifier must inspect this exact manifest before any
            # durable complete state is published.
            manifest = self._with_manifest_fingerprint(
                manifest.model_copy(
                    update={
                        "lifecycle_status": RunLifecycleStatus.VERIFYING,
                        "retention_status": RetentionStatus.RETAINED_INCOMPLETE,
                        "finalized_at": None,
                        "integrity": {},
                        "errors": (),
                    }
                )
            )
            self._persist_manifest_and_record(manifest)
            checks, errors = RetentionStore(self.retention_root).verify_run(self.run_id)
            if errors:
                failed = manifest.model_copy(
                    update={
                        "lifecycle_status": RunLifecycleStatus.FAILED,
                        "retention_status": RetentionStatus.RETENTION_FAILED,
                        "integrity": checks,
                        "errors": tuple(errors),
                    }
                )
                self._persist_manifest_and_record(self._with_manifest_fingerprint(failed))
                raise RetentionError("retained run finalization failed: " + "; ".join(errors))
            completed = manifest.model_copy(
                update={
                    "lifecycle_status": RunLifecycleStatus.COMPLETE,
                    "retention_status": RetentionStatus.RETAINED_COMPLETE,
                    "finalized_at": utc_now(),
                    "integrity": checks,
                }
            )
            completed = self._with_manifest_fingerprint(completed)
            self._persist_manifest_and_record(completed)
            # This is deliberately the last durable transition. A crash before
            # this write leaves the persisted manifest non-complete; a crash
            # after the manifest write but before this marker is reported as
            # incomplete by list/inspect and fails verify_run.
            try:
                self._write_complete_marker(completed)
            except Exception as exc:
                self._fail(f"complete marker persistence failed: {exc}")
                raise RetentionError(f"retained run complete marker persistence failed: {exc}") from exc
            return completed
        except RetentionError:
            raise
        except Exception as exc:
            self._fail(str(exc))
            raise RetentionError(f"retained run persistence failed: {exc}") from exc

    def fail(self, reason: str) -> RetainedRunManifest:
        return self._fail(reason)

    def _fail(self, reason: str) -> RetainedRunManifest:
        try:
            current = self._load_manifest()
            failed = current.model_copy(
                update={
                    "lifecycle_status": RunLifecycleStatus.FAILED,
                    "retention_status": RetentionStatus.RETENTION_FAILED,
                    "errors": (*current.errors, reason),
                    "manifest_fingerprint": None,
                }
            )
            failed = self._with_manifest_fingerprint(failed)
            self._persist_manifest_and_record(failed)
            return failed
        except Exception:
            raise RetentionError(f"retained run failed: {reason}")

    def _set_lifecycle(self, status: RunLifecycleStatus) -> None:
        current = self._load_manifest()
        updated = current.model_copy(update={"lifecycle_status": status})
        self._write_manifest(self._with_manifest_fingerprint(updated))
        record = self.metadata_store.get_retained_run(self.run_id)
        if record is not None:
            self.metadata_store.update_retained_run(
                record.model_copy(update={"lifecycle_status": status})
            )

    def _update_manifest_metadata(self, *, request_id: str | None = None) -> None:
        current = self._load_manifest()
        updated = current.model_copy(
            update={
                "request_id": request_id or current.request_id,
                "context_artifacts": tuple(self._context_artifacts),
                "declaration_artifact": self._declaration_artifact,
                "coverage": _coverage_summary(self._declaration_payload),
            }
        )
        self._write_manifest(self._with_manifest_fingerprint(updated))
        record = self.metadata_store.get_retained_run(self.run_id)
        if record is not None:
            self.metadata_store.update_retained_run(
                record.model_copy(update={"request_id": updated.request_id})
            )

    def _build_manifest(
        self,
        outcome: Any,
        *,
        request: Any,
        result_artifact: ArtifactReference,
        response_artifact: ArtifactReference,
        plugin_version: str | None,
    ) -> RetainedRunManifest:
        datasets = self.metadata_store.list_datasets()
        canonical_datasets = self.metadata_store.list_canonical_datasets()
        dataset = datasets[0] if datasets else None
        canonical = canonical_datasets[0] if canonical_datasets else None
        analysis_result = outcome.analysis_result
        records = {
            "request_id": request.request_id,
            "dataset_ids": [item.dataset_id for item in datasets],
            "canonical_dataset_ids": [item.canonical_dataset_id for item in canonical_datasets],
            "canonicalization_ids": [
                item.canonicalization_id for item in self.metadata_store.list_canonicalization_records()
            ],
            "sufficiency_ids": [item.sufficiency_id for item in self.metadata_store.list_data_sufficiency_results()],
            "execution_ids": [item.execution_id for item in self.metadata_store.list_execution_records()],
            "validation_ids": [item.validation_id for item in self.metadata_store.list_validation_records()],
            "admissibility_ids": [item.admissibility_id for item in self.metadata_store.list_evidence_admissibility_records()],
            "claim_candidate_ids": [item.claim_candidate_id for item in self.metadata_store.list_claim_candidates()],
            "claim_decision_ids": [item.claim_decision_id for item in self.metadata_store.list_claim_decision_records(self.artifact_store)],
        }
        artifacts = tuple(self.metadata_store.list_artifact_references())
        policies = tuple(
            sorted(
                {
                    *(decision.policy_version for decision in outcome.claim_decisions),
                    *(
                        [self._declaration_payload.get("policy_version")]
                        if self._declaration_payload and self._declaration_payload.get("policy_version")
                        else []
                    ),
                }
            )
        )
        current = self._load_manifest()
        return current.model_copy(
            update={
                "request_id": request.request_id,
                "analysis_run_status": analysis_result.run_status.value,
                "package_version": PACKAGE_VERSION,
                "plugin_version": plugin_version,
                "contract_version": request.contract_version,
                "metric_registry_version": request.metric_registry_version,
                "policy_versions": policies,
                "record_refs": records,
                "artifact_refs": artifacts,
                "analysis_result_artifact": result_artifact,
                "public_response_artifact": response_artifact,
                "source": _dataset_summary(dataset),
                "canonical": _canonical_summary(canonical),
                "coverage": _coverage_summary(self._declaration_payload),
            }
        )

    def _verify_components(self, manifest: RetainedRunManifest) -> tuple[dict[str, Any], list[str]]:
        return RetentionStore(self.retention_root).verify_manifest(manifest)

    def _persist_manifest_and_record(self, manifest: RetainedRunManifest) -> None:
        self._write_manifest(manifest)
        marker = self.run_root / self.COMPLETE_MARKER
        if manifest.retention_status is not RetentionStatus.RETAINED_COMPLETE and marker.exists():
            marker.unlink()
        record_json = {
            "manifest_version": manifest.manifest_version,
            "record_refs": manifest.record_refs,
            "artifact_ids": [item.artifact_id for item in manifest.artifact_refs],
        }
        record = self.metadata_store.get_retained_run(self.run_id)
        if record is None:
            record = RetainedRunRecord(
                run_id=self.run_id,
                request_id=manifest.request_id,
                lifecycle_status=manifest.lifecycle_status,
                retention_status=manifest.retention_status,
                analysis_run_status=manifest.analysis_run_status,
                manifest_path="manifest.json",
                manifest_fingerprint=manifest.manifest_fingerprint,
                created_at=manifest.created_at,
                finalized_at=manifest.finalized_at,
                record_json=record_json,
            )
            self.metadata_store.insert_retained_run(record)
        else:
            self.metadata_store.update_retained_run(
                record.model_copy(
                    update={
                        "request_id": manifest.request_id,
                        "lifecycle_status": manifest.lifecycle_status,
                        "retention_status": manifest.retention_status,
                        "analysis_run_status": manifest.analysis_run_status,
                        "manifest_fingerprint": manifest.manifest_fingerprint,
                        "finalized_at": manifest.finalized_at,
                        "record_json": record_json,
                    }
                )
            )

    def _write_complete_marker(self, manifest: RetainedRunManifest) -> None:
        if manifest.retention_status is not RetentionStatus.RETAINED_COMPLETE:
            raise RetentionError("only a retained_complete manifest may receive a complete marker")
        if not manifest.manifest_fingerprint:
            raise RetentionError("retained_complete manifest is missing its fingerprint")
        ArtifactStore._atomic_write_bytes(
            self.run_root / self.COMPLETE_MARKER,
            manifest.manifest_fingerprint.encode("ascii"),
        )

    def _load_manifest(self) -> RetainedRunManifest:
        return RetainedRunManifest.model_validate_json(
            (self.run_root / "manifest.json").read_text(encoding="utf-8")
        )

    def _write_manifest(self, manifest: RetainedRunManifest) -> None:
        payload = manifest.model_dump(mode="json")
        ArtifactStore._atomic_write_bytes(
            self.run_root / "manifest.json",
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"),
        )

    @staticmethod
    def _with_manifest_fingerprint(manifest: RetainedRunManifest) -> RetainedRunManifest:
        # Integrity checks are derived from the manifest and may be updated after
        # the first verification pass; they are deliberately not fingerprinted.
        payload = manifest.model_dump(mode="json", exclude={"manifest_fingerprint", "integrity"})
        return manifest.model_copy(update={"manifest_fingerprint": canonical_json_fingerprint(payload)})


class RetentionStore:
    """Read-only cross-process operations over a retention root."""

    def __init__(self, retention_root: str | Path) -> None:
        self.root = Path(retention_root).expanduser().resolve()

    def list_runs(self) -> list[dict[str, Any]]:
        if not self.root.exists():
            return []
        summaries: list[dict[str, Any]] = []
        if (self.root / "metadata.sqlite").is_file() or (self.root / "artifacts").is_dir():
            return [
                {
                    "run_id": self.root.name,
                    "retention_status": "legacy_incomplete",
                    "reason": "legacy component store; no self-contained retained-run manifest",
                }
            ]
        for child in sorted(self.root.iterdir()):
            if child.is_symlink():
                summaries.append(
                    {
                        "run_id": child.name,
                        "retention_status": "retention_failed",
                        "error": "retained run entry must not be a symlink",
                    }
                )
                continue
            if not child.is_dir():
                continue
            manifest_path = child / "manifest.json"
            if not manifest_path.is_file():
                summaries.append({"run_id": child.name, "retention_status": "legacy_incomplete"})
                continue
            try:
                manifest = RetainedRunManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
                status, status_error = self._effective_status(child, manifest)
                summaries.append(
                    {
                        "run_id": manifest.run_id,
                        "request_id": manifest.request_id,
                        "created_at": manifest.created_at.isoformat(),
                        "finalized_at": manifest.finalized_at.isoformat() if manifest.finalized_at else None,
                        "retention_status": status,
                        "lifecycle_status": manifest.lifecycle_status.value,
                        "analysis_run_status": manifest.analysis_run_status,
                        "source": manifest.source,
                        **({"error": status_error} if status_error else {}),
                    }
                )
            except Exception as exc:
                summaries.append({"run_id": child.name, "retention_status": "retention_failed", "error": str(exc)})
        return summaries

    def inspect_run(self, run_id: str) -> dict[str, Any]:
        manifest = self._load_manifest(run_id)
        payload = manifest.model_dump(mode="json")
        status, status_error = self._effective_status(self._run_root(run_id), manifest)
        payload["manifest_retention_status"] = payload["retention_status"]
        payload["retention_status"] = status
        payload["effective_retention_status"] = status
        payload["complete_marker_valid"] = status == RetentionStatus.RETAINED_COMPLETE.value
        if status_error:
            payload["effective_status_error"] = status_error
        return payload

    def verify_run(self, run_id: str) -> tuple[dict[str, Any], list[str]]:
        manifest = self._load_manifest(run_id)
        return self.verify_manifest(manifest)

    def verify_manifest(self, manifest: RetainedRunManifest) -> tuple[dict[str, Any], list[str]]:
        checks: dict[str, Any] = {}
        errors: list[str] = []
        run_root = self._run_root(manifest.run_id)
        artifact_store = ArtifactStore(run_root / "artifacts")
        try:
            expected = canonical_json_fingerprint(
                manifest.model_dump(mode="json", exclude={"manifest_fingerprint", "integrity"})
            )
            checks["manifest_fingerprint"] = manifest.manifest_fingerprint == expected
            if not checks["manifest_fingerprint"]:
                errors.append("manifest fingerprint mismatch")
        except Exception as exc:
            checks["manifest_fingerprint"] = False
            errors.append(f"manifest invalid: {exc}")
        artifact_ok = True
        for artifact in (*manifest.artifact_refs, *manifest.context_artifacts):
            try:
                path = artifact_store.safe_path(artifact.path)
                if not path.is_file() or artifact.fingerprint is None or sha256_file(path) != artifact.fingerprint:
                    artifact_ok = False
                    errors.append(f"artifact missing or hash mismatch: {artifact.artifact_id}")
            except Exception as exc:
                artifact_ok = False
                errors.append(f"artifact reference invalid: {artifact.artifact_id}: {exc}")
        for artifact in (manifest.analysis_result_artifact, manifest.public_response_artifact, manifest.declaration_artifact):
            if artifact is None:
                continue
            try:
                path = artifact_store.safe_path(artifact.path)
                if not path.is_file() or artifact.fingerprint is None or sha256_file(path) != artifact.fingerprint:
                    artifact_ok = False
                    errors.append(f"final artifact missing or hash mismatch: {artifact.artifact_id}")
            except Exception as exc:
                artifact_ok = False
                errors.append(f"final artifact reference invalid: {exc}")
        checks["artifact_hashes"] = artifact_ok
        metadata_ok = (run_root / "metadata.sqlite").is_file()
        if metadata_ok:
            try:
                with sqlite3.connect(run_root / "metadata.sqlite") as conn:
                    metadata_ok = conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            except Exception as exc:
                metadata_ok = False
                errors.append(f"metadata integrity check failed: {exc}")
        if not metadata_ok:
            errors.append("metadata.sqlite missing or corrupt")
        checks["metadata_integrity"] = metadata_ok
        marker_ok = True
        if manifest.retention_status is RetentionStatus.RETAINED_COMPLETE:
            marker = run_root / RetainedRunSession.COMPLETE_MARKER
            marker_ok = marker.is_file() and marker.read_text(encoding="ascii") == manifest.manifest_fingerprint
            if not marker_ok:
                errors.append("complete marker missing or mismatched")
        checks["complete_marker"] = marker_ok
        try:
            metadata = MetadataStore(run_root / "metadata.sqlite")
            metadata.initialize()
            checks["metadata_schema_version"] = metadata.schema_version() == 7
            if not checks["metadata_schema_version"]:
                errors.append("metadata schema is not v7")
            indexed_artifacts = {
                item.artifact_id: item for item in metadata.list_artifact_references()
            }
            refs_by_id = {
                item.artifact_id: item
                for item in (*manifest.artifact_refs, *manifest.context_artifacts)
            }
            refs_by_id.update(
                {
                    item.artifact_id: item
                    for item in (
                        manifest.analysis_result_artifact,
                        manifest.public_response_artifact,
                        manifest.declaration_artifact,
                    )
                    if item is not None
                }
            )
            metadata_artifacts_ok = all(indexed_artifacts.get(key) == value for key, value in refs_by_id.items())
            checks["metadata_artifact_linkage"] = metadata_artifacts_ok
            if not metadata_artifacts_ok:
                errors.append("manifest artifact references are not fully indexed in metadata")
            record_checks = {
                "dataset_ids": {item.dataset_id for item in metadata.list_datasets()},
                "canonical_dataset_ids": {item.canonical_dataset_id for item in metadata.list_canonical_datasets()},
                "canonicalization_ids": {
                    item.canonicalization_id for item in metadata.list_canonicalization_records()
                },
                "sufficiency_ids": {
                    item.sufficiency_id for item in metadata.list_data_sufficiency_results(artifact_store)
                },
                "execution_ids": {item.execution_id for item in metadata.list_execution_records()},
                "validation_ids": {item.validation_id for item in metadata.list_validation_records()},
                "admissibility_ids": {
                    item.admissibility_id for item in metadata.list_evidence_admissibility_records()
                },
                "claim_candidate_ids": {
                    item.claim_candidate_id for item in metadata.list_claim_candidates()
                },
                "claim_decision_ids": {
                    item.claim_decision_id for item in metadata.list_claim_decision_records(artifact_store)
                },
            }
            records_ok = all(
                set(manifest.record_refs.get(key, ())) == values
                for key, values in record_checks.items()
            )
            checks["record_linkage"] = records_ok
            if not records_ok:
                errors.append("manifest record references are not fully present in metadata")
            request = metadata.get_analysis_request(manifest.request_id, artifact_store) if manifest.request_id else None
            checks["request_linkage"] = request is not None
            if request is None:
                errors.append("request linkage missing")
            if manifest.analysis_result_artifact is not None:
                result_payload = json.loads(artifact_store.safe_path(manifest.analysis_result_artifact.path).read_text(encoding="utf-8"))
                checks["analysis_result_linkage"] = result_payload.get("run_id") == manifest.run_id and result_payload.get("request_id") == manifest.request_id
                if not checks["analysis_result_linkage"]:
                    errors.append("AnalysisResult run/request linkage mismatch")
            if manifest.public_response_artifact is not None:
                response_payload = json.loads(
                    artifact_store.safe_path(manifest.public_response_artifact.path).read_text(encoding="utf-8")
                )
                checks["public_response_linkage"] = (
                    response_payload.get("run_id") == manifest.run_id
                    and response_payload.get("request_id") == manifest.request_id
                )
                if not checks["public_response_linkage"]:
                    errors.append("PublicResponse run/request linkage mismatch")
            if manifest.declaration_artifact is not None:
                declaration = json.loads(artifact_store.safe_path(manifest.declaration_artifact.path).read_text(encoding="utf-8"))
                declaration_fields = (
                    "declaration_id",
                    "policy_version",
                    "authority_type",
                    "dataset_id",
                    "content_fingerprint",
                    "source_type",
                    "selected_sheet",
                    "selected_table",
                    "source_filename",
                    "covered_start",
                    "covered_end",
                    "date_convention_ref",
                    "scope",
                    "filters_status",
                    "context_fingerprint",
                    "data_availability_cutoff",
                    "completeness_assertion",
                    "source_basis",
                    "source_basis_detail",
                )
                checks["declaration_linkage"] = (
                    declaration.get("authority_type") == "USER_DECLARED"
                    and all(
                        manifest.coverage.get(field) == declaration.get(field)
                        for field in declaration_fields
                    )
                )
                if not checks["declaration_linkage"]:
                    errors.append("USER_DECLARED declaration identity/policy/scope linkage invalid")
                source_id = manifest.source.get("dataset_id")
                if source_id and declaration.get("dataset_id") != source_id:
                    errors.append("USER_DECLARED dataset linkage mismatch")
                source_fingerprint = manifest.source.get("content_fingerprint")
                if source_fingerprint and declaration.get("content_fingerprint") != source_fingerprint:
                    errors.append("USER_DECLARED source fingerprint linkage mismatch")
                context_artifacts = [
                    item
                    for item in manifest.context_artifacts
                    if item.path.endswith("canonicalization_request.json")
                ]
                if (
                    len(context_artifacts) != 1
                    or canonical_json_fingerprint(
                        json.loads(artifact_store.safe_path(context_artifacts[0].path).read_text(encoding="utf-8"))
                    )
                    != declaration.get("context_fingerprint")
                ):
                    checks["declaration_context_linkage"] = False
                    errors.append("USER_DECLARED canonicalization context fingerprint mismatch")
                else:
                    checks["declaration_context_linkage"] = True
            else:
                checks["declaration_linkage"] = True
                checks["declaration_context_linkage"] = True
            linkage_checks, linkage_errors = self._verify_cross_record_linkages(
                manifest,
                metadata=metadata,
                artifact_store=artifact_store,
                request=request,
            )
            checks.update(linkage_checks)
            errors.extend(linkage_errors)
        except Exception as exc:
            checks["record_linkage"] = False
            errors.append(f"record linkage verification failed: {exc}")
        return checks, errors

    def _verify_cross_record_linkages(
        self,
        manifest: RetainedRunManifest,
        *,
        metadata: MetadataStore,
        artifact_store: ArtifactStore,
        request: Any,
    ) -> tuple[dict[str, Any], list[str]]:
        """Verify identities between the persisted records, not just their IDs."""
        checks: dict[str, Any] = {}
        errors: list[str] = []

        registry = metadata.get_retained_run(manifest.run_id)
        registry_ok = registry is not None and (
            registry.run_id == manifest.run_id
            and registry.request_id == manifest.request_id
            and registry.manifest_fingerprint == manifest.manifest_fingerprint
            and registry.record_json.get("record_refs") == manifest.record_refs
            and registry.retention_status is manifest.retention_status
        )
        checks["retained_run_registry_linkage"] = registry_ok
        if not registry_ok:
            errors.append("retained run registry linkage mismatch")
        if request is None:
            return checks, errors

        datasets = metadata.list_datasets()
        dataset = metadata.get_dataset(request.dataset_ref_id)
        dataset_ok = dataset is not None and manifest.source.get("dataset_id") == request.dataset_ref_id
        if dataset is not None:
            dataset_ok = dataset_ok and dataset.content_fingerprint == manifest.source.get("content_fingerprint")
            dataset_ok = dataset_ok and dataset.source_type.value == manifest.source.get("source_type")
            dataset_ok = dataset_ok and dataset.selected_sheet == manifest.source.get("selected_sheet")
            dataset_ok = dataset_ok and dataset.selected_table == manifest.source.get("selected_table")
        checks["dataset_request_linkage"] = dataset_ok
        if not dataset_ok:
            errors.append("source DatasetReference/request/fingerprint linkage mismatch")

        canonical_by_id = {
            item.canonical_dataset_id: item for item in metadata.list_canonical_datasets()
        }
        canonical_ids = tuple(manifest.record_refs.get("canonical_dataset_ids", ()))
        canonical_ok = True
        for canonical_id in canonical_ids:
            canonical = canonical_by_id.get(canonical_id)
            if canonical is None or canonical.source_dataset_id != request.dataset_ref_id:
                canonical_ok = False
                continue
            if canonical.artifact not in manifest.artifact_refs:
                canonical_ok = False
            if manifest.canonical.get("canonical_dataset_id") == canonical_id:
                canonical_ok = canonical_ok and manifest.canonical == canonical.model_dump(mode="json")
        checks["canonical_dataset_linkage"] = canonical_ok
        if not canonical_ok:
            errors.append("canonical dataset/source/artifact linkage mismatch")

        canonicalization_ok = True
        canonical_ids_set = set(canonical_by_id)
        for item in metadata.list_canonicalization_records():
            if item.canonicalization_id not in set(manifest.record_refs.get("canonicalization_ids", ())):
                canonicalization_ok = False
            if item.source_dataset_id != request.dataset_ref_id:
                canonicalization_ok = False
            if item.canonical_dataset_id is not None and item.canonical_dataset_id not in canonical_ids_set:
                canonicalization_ok = False
            if item.source_fingerprint and dataset is not None and item.source_fingerprint != dataset.content_fingerprint:
                canonicalization_ok = False
            if item.canonical_dataset_id and item.output_fingerprint:
                canonical = canonical_by_id.get(item.canonical_dataset_id)
                canonicalization_ok = canonicalization_ok and canonical is not None and item.output_fingerprint == canonical.content_fingerprint
        checks["canonicalization_linkage"] = canonicalization_ok
        if not canonicalization_ok:
            errors.append("canonicalization/source/canonical linkage mismatch")

        sufficiency_by_id = {
            item.sufficiency_id: item
            for item in metadata.list_data_sufficiency_results(artifact_store)
        }
        sufficiency_ok = all(
            item.request_id == manifest.request_id
            and item.dataset_ref_id == request.dataset_ref_id
            and (item.canonical_dataset_ref_id is None or item.canonical_dataset_ref_id in canonical_ids_set)
            for item in sufficiency_by_id.values()
        )
        checks["sufficiency_linkage"] = sufficiency_ok
        if not sufficiency_ok:
            errors.append("DataSufficiencyResult request/dataset/canonical linkage mismatch")

        executions = {item.execution_id: item for item in metadata.list_execution_records()}
        executed_results: dict[str, ExecutedResult] = {}
        execution_ok = True
        for execution in executions.values():
            if execution.request_id != manifest.request_id or execution.result_ref is None or len(execution.output_artifacts) != 1:
                execution_ok = False
                continue
            result = self._load_artifact_model(
                execution.output_artifacts[0], ExecutedResult, artifact_store, metadata
            )
            if result is None or result.result_id != execution.result_ref or result.execution_id != execution.execution_id:
                execution_ok = False
            else:
                executed_results[result.result_id] = result
        checks["execution_result_linkage"] = execution_ok
        if not execution_ok:
            errors.append("ExecutionRecord/ExecutedResult/request linkage mismatch")

        validations = {item.validation_id: item for item in metadata.list_validation_records()}
        validated_results: dict[str, ValidatedResult] = {}
        validation_ok = True
        for validation in validations.values():
            execution = executions.get(validation.execution_id)
            if execution is None or validation.target_result_ref != execution.result_ref:
                validation_ok = False
            if validation.validated_result_ref and validation.validated_result_artifact_ref:
                validated = self._load_artifact_model(
                    validation.validated_result_artifact_ref, ValidatedResult, artifact_store, metadata
                )
                if (
                    validated is None
                    or validated.validated_result_id != validation.validated_result_ref
                    or validated.execution_id != validation.execution_id
                    or validated.executed_result_id != validation.target_result_ref
                    or validation.validation_id not in validated.required_validation_record_ids
                ):
                    validation_ok = False
                elif validated is not None:
                    validated_results[validated.validated_result_id] = validated
        for validated in validated_results.values():
            if not set(validated.required_validation_record_ids).issubset(validations):
                validation_ok = False
        checks["validation_linkage"] = validation_ok
        if not validation_ok:
            errors.append("ValidationRecord/ValidatedResult/ExecutionRecord linkage mismatch")

        admissibility_ok = True
        evidence_ids: set[str] = set()
        for record in metadata.list_evidence_admissibility_records():
            if record.request_id not in (None, manifest.request_id):
                admissibility_ok = False
            if record.sufficiency_id and record.sufficiency_id not in sufficiency_by_id:
                admissibility_ok = False
            if record.validated_result_id:
                validated = validated_results.get(record.validated_result_id)
                if validated is None or record.execution_id not in (None, validated.execution_id):
                    admissibility_ok = False
            if record.status.value == "passed" and record.admissible_evidence_artifact_ref:
                evidence = self._load_artifact_model(
                    record.admissible_evidence_artifact_ref, AdmissibleEvidence, artifact_store, metadata
                )
                if evidence is None or evidence.evidence_id != record.admissible_evidence_id:
                    admissibility_ok = False
                else:
                    evidence_ids.add(evidence.evidence_id)
                    if evidence.request_id not in (None, manifest.request_id):
                        admissibility_ok = False
                    if record.validated_result_id and evidence.validated_result_ids != (record.validated_result_id,):
                        admissibility_ok = False
                    if dataset is not None and evidence.dataset_ref_id != dataset.dataset_id:
                        admissibility_ok = False
                    if evidence.canonical_dataset_ref_id and evidence.canonical_dataset_ref_id not in canonical_ids_set:
                        admissibility_ok = False
        checks["admissibility_linkage"] = admissibility_ok
        if not admissibility_ok:
            errors.append("AdmissibleEvidence/ValidatedResult/dataset/scope linkage mismatch")

        candidates = {
            item.claim_candidate_id: item for item in metadata.list_claim_candidates()
        }
        candidate_ok = all(
            item.request_id in (None, manifest.request_id)
            and (dataset is None or item.dataset_ref_id in (None, dataset.dataset_id))
            and (item.canonical_dataset_ref_id is None or item.canonical_dataset_ref_id in canonical_ids_set)
            and set(item.supporting_validated_result_refs).issubset(validated_results)
            and set(item.supporting_evidence_refs).issubset(evidence_ids)
            for item in candidates.values()
        )
        checks["claim_candidate_linkage"] = candidate_ok
        if not candidate_ok:
            errors.append("ClaimCandidate/request/metric/period/evidence linkage mismatch")

        decisions = {
            item.claim_decision_id: item
            for item in metadata.list_claim_decision_records(artifact_store)
        }
        decision_ok = True
        for decision in decisions.values():
            candidate = candidates.get(decision.claim_candidate_ref) if decision.claim_candidate_ref else None
            if decision.claim_candidate_ref and candidate is None:
                decision_ok = False
            if candidate is not None:
                if tuple(decision.supporting_validated_result_refs) != tuple(candidate.supporting_validated_result_refs):
                    decision_ok = False
                if tuple(decision.supporting_evidence_refs) != tuple(candidate.supporting_evidence_refs):
                    decision_ok = False
                if candidate.request_id not in (None, manifest.request_id):
                    decision_ok = False
        checks["claim_decision_linkage"] = decision_ok
        if not decision_ok:
            errors.append("ClaimDecision/ClaimCandidate/request linkage mismatch")

        result_ok = True
        result = self._load_artifact_model(
            manifest.analysis_result_artifact, AnalysisResult, artifact_store, metadata
        ) if manifest.analysis_result_artifact else None
        if result is None or result.run_id != manifest.run_id or result.request_id != manifest.request_id:
            result_ok = False
        else:
            result_ok = (
                set(result.executed_result_refs).issubset(executed_results)
                and set(result.validation_record_refs).issubset(validations)
                and set(result.validated_result_refs).issubset(validated_results)
                and {item.claim_decision_id for item in result.claim_decisions}.issubset(decisions)
                and (result.data_sufficiency_ref is None or result.data_sufficiency_ref in sufficiency_by_id)
            )
            for decision in result.claim_decisions:
                if decisions.get(decision.claim_decision_id) != decision:
                    result_ok = False
        checks["analysis_result_linkage"] = result_ok
        if not result_ok:
            errors.append("AnalysisResult/run/request/evidence/ClaimDecision linkage mismatch")

        response_ok = self._verify_public_response_linkage(manifest, artifact_store, metadata)
        checks["public_response_linkage"] = response_ok
        if not response_ok:
            errors.append("PublicResponse/request/run/result/ClaimDecision/disclosure linkage mismatch")
        return checks, errors

    @staticmethod
    def _load_artifact_model(artifact, model_type, artifact_store, metadata):
        if artifact is None or metadata.get_artifact_reference(artifact.artifact_id) != artifact:
            return None
        try:
            raw = artifact_store.safe_path(artifact.path).read_text(encoding="utf-8")
            if model_type is dict:
                return json.loads(raw)
            return model_type.model_validate_json(raw)
        except Exception:
            return None

    def _verify_public_response_linkage(self, manifest, artifact_store, metadata) -> bool:
        if manifest.public_response_artifact is None:
            return False
        payload = self._load_artifact_model(
            manifest.public_response_artifact, dict, artifact_store, metadata
        )
        if not isinstance(payload, dict):
            return False
        if payload.get("run_id") != manifest.run_id or payload.get("request_id") != manifest.request_id:
            return False
        if "claim_decisions" in payload:
            payload_decision_ids = {
                item.get("claim_decision_id")
                for item in payload.get("claim_decisions", ())
                if isinstance(item, dict)
            }
            if payload_decision_ids != set(manifest.record_refs.get("claim_decision_ids", ())):
                return False
        response = payload.get("response", payload)
        coverage = manifest.coverage
        if not coverage:
            return not response.get("coverage_provenance")
        disclosure = coverage.get("disclosure")
        if disclosure not in response.get("limitations", ()):
            return False
        provenance = response.get("coverage_provenance") or ()
        if len(provenance) != 1 or provenance[0].get("declaration_id") != coverage.get("declaration_id"):
            return False
        return (
            provenance[0].get("dataset_id") == coverage.get("dataset_id")
            and provenance[0].get("content_fingerprint") == coverage.get("content_fingerprint")
            and provenance[0].get("context_fingerprint") == coverage.get("context_fingerprint")
            and provenance[0].get("artifact") == manifest.declaration_artifact.model_dump(mode="json")
        )

    def delete_run(self, run_id: str) -> None:
        run_root = self._run_root(run_id)
        if not run_root.is_dir():
            raise FileNotFoundError(f"retained run does not exist: {run_id}")
        manifest_path = run_root / "manifest.json"
        if manifest_path.is_file():
            RetainedRunManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        shutil.rmtree(run_root)

    def _effective_status(
        self,
        run_root: Path,
        manifest: RetainedRunManifest,
    ) -> tuple[str, str | None]:
        if manifest.retention_status is not RetentionStatus.RETAINED_COMPLETE:
            return manifest.retention_status.value, None
        marker = run_root / RetainedRunSession.COMPLETE_MARKER
        try:
            marker_ok = marker.is_file() and marker.read_text(encoding="ascii") == manifest.manifest_fingerprint
        except Exception as exc:
            return RetentionStatus.RETAINED_INCOMPLETE.value, f"complete marker unreadable: {exc}"
        if not marker_ok:
            return (
                RetentionStatus.RETAINED_INCOMPLETE.value,
                "complete manifest is present but the final complete marker is missing or mismatched",
            )
        return RetentionStatus.RETAINED_COMPLETE.value, None

    def _load_manifest(self, run_id: str) -> RetainedRunManifest:
        run_root = self._run_root(run_id)
        manifest_path = run_root / "manifest.json"
        if not manifest_path.is_file():
            raise RetentionError(f"retained run manifest missing: {run_id}")
        return RetainedRunManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))

    def _run_root(self, run_id: str) -> Path:
        if Path(run_id).name != run_id or run_id in {"", ".", ".."}:
            raise ValueError("run_id must be a single safe path component")
        entry = self.root / run_id
        if entry.parent != self.root:
            raise ValueError("retained run path escapes retention root")
        # Inspect the direct child before resolving anything. Resolving first
        # would turn an internal symlink into another run's real directory and
        # allow delete_run() to remove the wrong target.
        if entry.is_symlink():
            raise ValueError("retained run path must not be a symlink")
        candidate = entry.resolve(strict=False)
        if candidate != entry or candidate.parent != self.root:
            raise ValueError("retained run path must be a direct non-symlink child")
        return entry


def run_retained_public_analysis(intent: Any, retention_root: str | Path, **kwargs: Any) -> Any:
    """High-level API for an explicitly retained public analysis."""
    from commerce_lens.skill.integration import run_public_analysis

    session = RetainedRunSession.begin(retention_root)
    try:
        outcome = run_public_analysis(
            intent,
            artifact_store=session.artifact_store,
            metadata_store=session.metadata_store,
            run_id=session.run_id,
            retention_session=session,
            **kwargs,
        )
        payload = {
            "rendered_text": outcome.response.render_text(),
            "response": _jsonable(asdict(outcome.response)),
        }
        session.finalize(outcome, public_payload=payload)
        return outcome
    except Exception as exc:
        session.fail(str(exc))
        raise


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Decimal):
        return value.to_eng_string()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _dataset_summary(dataset: Any) -> dict[str, Any]:
    if dataset is None:
        return {}
    return {
        "dataset_id": dataset.dataset_id,
        "source_type": dataset.source_type.value,
        "original_name": dataset.original_name,
        "content_fingerprint": dataset.content_fingerprint,
        "selected_sheet": dataset.selected_sheet,
        "selected_table": dataset.selected_table,
        "snapshot_artifact": _jsonable(dataset.snapshot_artifact),
    }


def _canonical_summary(canonical: Any) -> dict[str, Any]:
    if canonical is None:
        return {}
    return _jsonable(canonical)


def _coverage_summary(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {}
    return {
        "declaration_id": payload.get("declaration_id"),
        "policy_version": payload.get("policy_version"),
        "authority_type": payload.get("authority_type"),
        "dataset_id": payload.get("dataset_id"),
        "content_fingerprint": payload.get("content_fingerprint"),
        "source_type": payload.get("source_type"),
        "source_filename": payload.get("source_filename"),
        "selected_sheet": payload.get("selected_sheet"),
        "selected_table": payload.get("selected_table"),
        "date_convention_ref": payload.get("date_convention_ref"),
        "context_fingerprint": payload.get("context_fingerprint"),
        "scope": payload.get("scope"),
        "filters_status": payload.get("filters_status"),
        "covered_start": payload.get("covered_start"),
        "covered_end": payload.get("covered_end"),
        "data_availability_cutoff": payload.get("data_availability_cutoff"),
        "completeness_assertion": payload.get("completeness_assertion"),
        "source_basis": payload.get("source_basis"),
        "source_basis_detail": payload.get("source_basis_detail"),
        "disclosure": "Coverage is based on a user-provided declaration and has not been independently verified by CommerceLens.",
    }
