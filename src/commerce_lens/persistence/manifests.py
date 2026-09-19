"""Retention and run-manifest contracts for F2-A."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from commerce_lens.contracts.common import ArtifactReference, ContractBase


class RetentionStatus(str, Enum):
    TEMPORARY = "temporary"
    RETAINED_INCOMPLETE = "retained_incomplete"
    RETAINED_COMPLETE = "retained_complete"
    RETENTION_FAILED = "retention_failed"


class RunLifecycleStatus(str, Enum):
    INITIALIZING = "initializing"
    WRITING = "writing"
    VERIFYING = "verifying"
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    FAILED = "failed"


class ArtifactManifest(ContractBase):
    manifest_id: str = Field(min_length=1)
    artifact_refs: tuple[ArtifactReference, ...] = ()


class RetainedRunRecord(ContractBase):
    """SQLite registry row for a self-contained retained run."""

    run_id: str = Field(min_length=1)
    request_id: str | None = None
    lifecycle_status: RunLifecycleStatus
    retention_status: RetentionStatus
    analysis_run_status: str | None = None
    manifest_path: str = Field(min_length=1)
    manifest_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    created_at: datetime
    finalized_at: datetime | None = None
    record_json: dict[str, Any] = Field(default_factory=dict)


class RetainedRunManifest(ContractBase):
    """Self-contained, finalized index of one retained run."""

    manifest_version: str = "f2_a_retention_v1"
    run_id: str = Field(min_length=1)
    request_id: str | None = None
    created_at: datetime
    finalized_at: datetime | None = None
    lifecycle_status: RunLifecycleStatus
    retention_status: RetentionStatus
    analysis_run_status: str | None = None
    package_version: str = Field(min_length=1)
    plugin_version: str | None = None
    contract_version: str | None = None
    metric_registry_version: str | None = None
    policy_versions: tuple[str, ...] = ()
    record_refs: dict[str, Any] = Field(default_factory=dict)
    artifact_refs: tuple[ArtifactReference, ...] = ()
    context_artifacts: tuple[ArtifactReference, ...] = ()
    analysis_result_artifact: ArtifactReference | None = None
    public_response_artifact: ArtifactReference | None = None
    declaration_artifact: ArtifactReference | None = None
    source: dict[str, Any] = Field(default_factory=dict)
    canonical: dict[str, Any] = Field(default_factory=dict)
    coverage: dict[str, Any] = Field(default_factory=dict)
    integrity: dict[str, Any] = Field(default_factory=dict)
    errors: tuple[str, ...] = ()
    manifest_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
