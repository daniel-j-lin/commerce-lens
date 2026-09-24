"""Artifact-backed persistence and authoritative retrieval for R4."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from commerce_lens.contracts.common import ArtifactReference
from commerce_lens.contracts.r4 import (
    ExecutedR4DecompositionResult,
    R4DecompositionRequest,
    R4ExecutionRecord,
    R4ProductTrace,
    R4ValidationRecord,
    R4ValidationStatus,
    ValidatedR4DecompositionResult,
)
from commerce_lens.contracts.validation import ValidatedResult, ValidationStatus
from commerce_lens.evidence.identifiers import canonical_json_fingerprint, sha256_file
from commerce_lens.metrics.registry import get_metric_registry
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore


class R4ArtifactIntegrityError(RuntimeError):
    """Raised when persisted R4 or upstream authority cannot be authenticated."""


ModelT = TypeVar("ModelT", bound=BaseModel)


def persist_r4_request(
    request: R4DecompositionRequest,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ArtifactReference:
    return _persist_model(
        Path("runs") / request.r4_request_id / "r4" / "request.json",
        request,
        artifact_store,
        metadata_store,
    )


def persist_r4_trace(
    trace: R4ProductTrace,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ArtifactReference:
    return _persist_model(
        Path("runs") / trace.execution_id / "r4" / "product_trace.json",
        trace,
        artifact_store,
        metadata_store,
    )


def persist_r4_executed_result(
    result: ExecutedR4DecompositionResult,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ArtifactReference:
    return _persist_model(
        Path("runs") / result.execution_id / "r4" / "executed_result.json",
        result,
        artifact_store,
        metadata_store,
    )


def persist_r4_execution_record(
    record: R4ExecutionRecord,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ArtifactReference:
    return _persist_model(
        Path("runs") / record.execution_id / "r4" / "execution_record.json",
        record,
        artifact_store,
        metadata_store,
    )


def persist_r4_validation_record(
    record: R4ValidationRecord,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ArtifactReference:
    return _persist_model(
        Path("runs") / record.execution_id / "r4" / "validation_records" / f"{record.validation_id}.json",
        record,
        artifact_store,
        metadata_store,
    )


def persist_validated_r4_result(
    result: ValidatedR4DecompositionResult,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ArtifactReference:
    return _persist_model(
        Path("runs") / result.execution_id / "r4" / "validated_results" / f"{result.validated_result_id}.json",
        result,
        artifact_store,
        metadata_store,
    )


def load_r4_trace(
    artifact: ArtifactReference,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> R4ProductTrace:
    return _load_model(artifact, R4ProductTrace, artifact_store, metadata_store)


def load_r4_executed_result(
    artifact: ArtifactReference,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ExecutedR4DecompositionResult:
    result = _load_model(artifact, ExecutedR4DecompositionResult, artifact_store, metadata_store)
    trace = load_r4_trace(result.product_trace_ref, artifact_store, metadata_store)
    if trace.trace_fingerprint != _r4_trace_fingerprint(trace):
        raise R4ArtifactIntegrityError("R4 trace semantic fingerprint mismatch")
    if trace.trace_fingerprint != result.product_trace_fingerprint:
        raise R4ArtifactIntegrityError("R4 executed result trace fingerprint binding mismatch")
    if result.result_fingerprint != _r4_result_fingerprint(result):
        raise R4ArtifactIntegrityError("R4 executed result semantic fingerprint mismatch")
    return result


def load_validated_r4_result(
    artifact: ArtifactReference,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ValidatedR4DecompositionResult:
    validated = _load_model(artifact, ValidatedR4DecompositionResult, artifact_store, metadata_store)
    executed = load_r4_executed_result(
        validated.source_result_artifact_ref,
        artifact_store,
        metadata_store,
    )
    execution_record = _load_model(
        validated.execution_record_artifact_ref,
        R4ExecutionRecord,
        artifact_store,
        metadata_store,
    )
    validation_record = _load_model(
        validated.validation_record_artifact_ref,
        R4ValidationRecord,
        artifact_store,
        metadata_store,
    )
    if validated.executed_result_id != executed.result_id or validated.execution_id != executed.execution_id:
        raise R4ArtifactIntegrityError("validated R4 result execution linkage mismatch")
    if execution_record.execution_id != validated.execution_id or execution_record.result_ref != executed.result_id:
        raise R4ArtifactIntegrityError("validated R4 result execution-record linkage mismatch")
    if validation_record.validation_id != validated.validation_record_id:
        raise R4ArtifactIntegrityError("validated R4 result validation-record linkage mismatch")
    if validation_record.validation_fingerprint != validated.validation_fingerprint:
        raise R4ArtifactIntegrityError("validated R4 result validation fingerprint mismatch")
    if validation_record.status is not R4ValidationStatus.PASSED or not all(
        check.passed for check in validation_record.checks
    ):
        raise R4ArtifactIntegrityError("validated R4 result references non-passing validation authority")
    if validation_record.validation_fingerprint != _r4_validation_fingerprint(validation_record):
        raise R4ArtifactIntegrityError("R4 validation semantic fingerprint mismatch")
    if executed.result_fingerprint != validated.result_fingerprint:
        raise R4ArtifactIntegrityError("validated R4 result source fingerprint mismatch")
    if executed.authority != validated.authority or validation_record.authority != validated.authority:
        raise R4ArtifactIntegrityError("validated R4 result authority binding mismatch")
    if executed.product_trace_ref != validated.product_trace_ref:
        raise R4ArtifactIntegrityError("validated R4 result trace reference mismatch")
    projection_fields = (
        "baseline_revenue",
        "comparison_revenue",
        "observed_revenue_change",
        "entry_component",
        "exit_component",
        "continuing_component",
        "component_sum",
        "reconciliation_difference",
        "product_count",
        "entry_product_count",
        "exit_product_count",
        "continuing_product_count",
        "product_trace_fingerprint",
    )
    if any(getattr(validated, name) != getattr(executed, name) for name in projection_fields):
        raise R4ArtifactIntegrityError("validated R4 result projection contradicts executed authority")
    return validated


def load_authenticated_scalar_validated_result(
    validated_result_id: str,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ValidatedResult:
    matching = [
        record
        for record in metadata_store.list_validation_records()
        if record.validated_result_ref == validated_result_id
    ]
    if not matching:
        raise R4ArtifactIntegrityError(f"validated scalar result authority is missing: {validated_result_id}")
    artifact = matching[0].validated_result_artifact_ref
    if artifact is None or any(record.validated_result_artifact_ref != artifact for record in matching):
        raise R4ArtifactIntegrityError("validated scalar result artifact binding is incomplete")
    result = _load_model(artifact, ValidatedResult, artifact_store, metadata_store)
    if result.validated_result_id != validated_result_id:
        raise R4ArtifactIntegrityError("validated scalar result identity mismatch")
    if tuple(record.validation_id for record in matching) != result.required_validation_record_ids:
        by_id = {record.validation_id: record for record in matching}
        try:
            matching = [by_id[record_id] for record_id in result.required_validation_record_ids]
        except KeyError as exc:
            raise R4ArtifactIntegrityError("validated scalar result required validation bundle is incomplete") from exc
    if result.validation_record_id != result.required_validation_record_ids[0]:
        raise R4ArtifactIntegrityError("validated scalar result governing validation record mismatch")
    definition = get_metric_registry().require(result.metric_ref)
    if tuple(record.validation_rule_id for record in matching) != definition.required_validation_rule_refs:
        raise R4ArtifactIntegrityError("validated scalar result rule bundle does not match Metric authority")
    rule_fingerprints: list[str] = []
    for record in matching:
        if record.status is not ValidationStatus.PASSED:
            raise R4ArtifactIntegrityError("validated scalar result contains a non-passing validation record")
        expected_fields = {
            "execution_id": result.execution_id,
            "target_result_ref": result.executed_result_id,
            "metric_ref": result.metric_ref,
            "metric_definition_version": result.metric_definition_version,
            "plan_id": result.plan_id,
            "plan_node_id": result.plan_node_id,
            "canonical_dataset_ref_id": result.canonical_dataset_ref_id,
            "canonical_dataset_fingerprint": result.canonical_dataset_fingerprint,
            "population_ref": result.population_ref,
            "population_fingerprint": result.population_fingerprint,
            "period_ref": result.period_ref,
            "period_role": result.period_role,
            "result_fingerprint": result.result_fingerprint,
            "validated_result_ref": result.validated_result_id,
        }
        if any(getattr(record, name) != value for name, value in expected_fields.items()):
            raise R4ArtifactIntegrityError("validated scalar result validation lineage mismatch")
        expected_rule_fingerprint = _scalar_rule_fingerprint(record)
        if record.validation_fingerprint != expected_rule_fingerprint:
            raise R4ArtifactIntegrityError("validated scalar result rule fingerprint mismatch")
        rule_fingerprints.append(expected_rule_fingerprint)
    expected_bundle = _scalar_bundle_fingerprint(
        result,
        definition.required_validation_rule_refs,
        tuple(rule_fingerprints),
    )
    if result.validation_fingerprint != expected_bundle:
        raise R4ArtifactIntegrityError("validated scalar result bundle fingerprint mismatch")
    return result


def _persist_model(
    relative_path: Path,
    model: BaseModel,
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ArtifactReference:
    artifact = artifact_store.write_json_artifact(relative_path, model.model_dump(mode="json"))
    metadata_store.insert_artifact_reference(artifact)
    restored = type(model).model_validate_json(
        artifact_store.safe_path(artifact.path).read_text(encoding="utf-8")
    )
    if restored != model:
        raise R4ArtifactIntegrityError(f"persisted {type(model).__name__} did not round-trip")
    return artifact


def _load_model(
    artifact: ArtifactReference,
    model_type: type[ModelT],
    artifact_store: ArtifactStore,
    metadata_store: MetadataStore,
) -> ModelT:
    if metadata_store.get_artifact_reference(artifact.artifact_id) != artifact:
        raise R4ArtifactIntegrityError("artifact reference is not registered as exact MetadataStore authority")
    path = artifact_store.safe_path(artifact.path)
    if not path.is_file():
        raise R4ArtifactIntegrityError("required authority artifact is missing")
    if artifact.fingerprint is None or sha256_file(path) != artifact.fingerprint:
        raise R4ArtifactIntegrityError("authority artifact fingerprint mismatch")
    try:
        return model_type.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise R4ArtifactIntegrityError(f"authority artifact schema invalid: {exc}") from exc


def _scalar_rule_fingerprint(record) -> str:
    return canonical_json_fingerprint(
        {
            "validator_id": record.validator_id,
            "validator_version": record.validator_version,
            "validation_rule_id": record.validation_rule_id,
            "validation_rule_version": record.validation_version,
            "status": record.status.value,
            "failure_code": record.failure_code,
            "metric_ref": record.metric_ref,
            "metric_definition_version": record.metric_definition_version,
            "result_fingerprint": record.result_fingerprint,
            "canonical_dataset_ref": record.canonical_dataset_ref_id,
            "canonical_dataset_fingerprint": record.canonical_dataset_fingerprint,
            "population_ref": record.population_ref,
            "population_fingerprint": record.population_fingerprint,
            "checks_performed": record.checks_performed,
            "operation": record.validation_operation,
            "expected_value": _json_scalar(record.expected_value),
            "expected_state": record.expected_state.value if record.expected_state else None,
            "actual_value": _json_scalar(record.actual_value),
            "actual_state": record.actual_state.value if record.actual_state else None,
            "precision": record.authoritative_precision,
            "precision_metadata": (record.observed or {}).get("precision_metadata") if isinstance(record.observed, dict) else None,
            "unit": (record.observed or {}).get("unit") if isinstance(record.observed, dict) else None,
            "currency": (record.observed or {}).get("currency") if isinstance(record.observed, dict) else None,
        }
    )


def _scalar_bundle_fingerprint(result, required_rule_ids, rule_validation_fingerprints) -> str:
    return canonical_json_fingerprint(
        {
            "validator_id": "commerce_lens_p5_deterministic_validator",
            "validator_version": "p5_001_v1",
            "intended_use": result.intended_use,
            "metric_ref": result.metric_ref,
            "metric_definition_version": result.metric_definition_version,
            "result_fingerprint": result.result_fingerprint,
            "canonical_dataset_ref": result.canonical_dataset_ref_id,
            "canonical_dataset_fingerprint": result.canonical_dataset_fingerprint,
            "population_ref": result.population_ref,
            "population_fingerprint": result.population_fingerprint,
            "required_validation_rule_ids": required_rule_ids,
            "rule_validation_fingerprints": rule_validation_fingerprints,
            "metric_state": result.metric_state.value,
            "value": _json_scalar(result.value),
            "undefined_reason": result.undefined_reason,
            "precision": result.precision,
            "precision_metadata": result.precision_metadata,
            "unit": result.unit,
            "currency": result.currency,
        }
    )


def _json_scalar(value):
    return str(value) if isinstance(value, Decimal) else value


def _r4_trace_fingerprint(trace: R4ProductTrace) -> str:
    return canonical_json_fingerprint(
        {
            "authority": trace.authority.model_dump(mode="json"),
            "rows": [
                {key: value for key, value in row.model_dump(mode="json").items() if key != "execution_id"}
                for row in trace.rows
            ],
        }
    )


def _r4_result_fingerprint(result: ExecutedR4DecompositionResult) -> str:
    return canonical_json_fingerprint(
        {
            "authority": result.authority.model_dump(mode="json"),
            "baseline_revenue": str(result.baseline_revenue),
            "comparison_revenue": str(result.comparison_revenue),
            "observed_revenue_change": str(result.observed_revenue_change),
            "entry_component": str(result.entry_component),
            "exit_component": str(result.exit_component),
            "continuing_component": str(result.continuing_component),
            "component_sum": str(result.component_sum),
            "reconciliation_difference": str(result.reconciliation_difference),
            "product_trace_fingerprint": result.product_trace_fingerprint,
            "product_count": result.product_count,
            "entry_product_count": result.entry_product_count,
            "exit_product_count": result.exit_product_count,
            "continuing_product_count": result.continuing_product_count,
        }
    )


def _r4_validation_fingerprint(record: R4ValidationRecord) -> str:
    return canonical_json_fingerprint(
        {
            "validator_id": record.validator_id,
            "validator_version": record.validator_version,
            "target_result_ref": record.target_result_ref,
            "target_result_fingerprint": record.target_result_fingerprint,
            "product_trace_fingerprint": record.product_trace_fingerprint,
            "authority": record.authority.model_dump(mode="json"),
            "checks": [check.model_dump(mode="json") for check in record.checks],
            "status": record.status.value,
        }
    )
