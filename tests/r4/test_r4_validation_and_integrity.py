from __future__ import annotations

from pathlib import Path

import pytest

from commerce_lens.contracts.common import ArtifactReference
from commerce_lens.evidence.identifiers import canonical_json_bytes, sha256_file, stable_content_id
from commerce_lens.persistence.r4_repository import (
    R4ArtifactIntegrityError,
    _r4_result_fingerprint,
    _r4_trace_fingerprint,
    load_r4_trace,
    load_validated_r4_result,
)
from commerce_lens.validation.r4_validator import validate_r4_decomposition
from tests.engine.test_execution import _row
from tests.r4.support import make_r4_fixture, run_r4


def _validate_hostile(fixture, outcome, artifact):
    return validate_r4_decomposition(
        executed_result_artifact=artifact,
        execution_record=outcome.execution.execution_record,
        execution_record_artifact=outcome.execution.execution_record_artifact,
        canonical_dataset=fixture.scalar.canonical,
        baseline_population=fixture.baseline_population,
        comparison_population=fixture.comparison_population,
        baseline_revenue_authority=fixture.baseline,
        comparison_revenue_authority=fixture.comparison,
        revenue_change_authority=fixture.change,
        artifact_store=fixture.scalar.artifact_store,
        metadata_store=fixture.scalar.metadata_store,
    )


def test_executor_output_tamper_is_independently_rejected_with_no_validated_result(tmp_path) -> None:
    fixture = make_r4_fixture(
        tmp_path,
        [
            _row(order_id="b", order_date="2026-01-01", product_id="p", line_revenue="10"),
            _row(order_id="c", order_date="2026-01-03", product_id="p", line_revenue="12"),
        ],
    )
    outcome = run_r4(fixture)
    hostile = outcome.execution.executed_result.model_copy(
        update={"continuing_component": outcome.execution.executed_result.continuing_component + 1}
    )
    hostile = hostile.model_copy(update={"result_fingerprint": _r4_result_fingerprint(hostile)})
    artifact = fixture.scalar.artifact_store.write_json_artifact(
        Path("runs") / hostile.execution_id / "r4" / "hostile_result.json",
        hostile.model_dump(mode="json"),
    )
    fixture.scalar.metadata_store.insert_artifact_reference(artifact)
    validation = _validate_hostile(fixture, outcome, artifact)
    assert validation.validation_record.status.value == "failed"
    assert validation.validated_result is None
    assert validation.validated_result_artifact is None
    failed_ids = {check.check_id for check in validation.validation_record.checks if not check.passed}
    assert "continuing_component_aggregation" in failed_ids


def test_missing_trace_product_is_validation_failure_not_repaired_by_aggregates(tmp_path) -> None:
    fixture = make_r4_fixture(
        tmp_path,
        [
            _row(order_id="b", order_date="2026-01-01", product_id="p", line_revenue="10"),
            _row(order_id="c", order_date="2026-01-03", product_id="q", line_revenue="12"),
        ],
    )
    outcome = run_r4(fixture)
    original_trace = outcome.execution.product_trace
    hostile_trace = original_trace.model_copy(
        update={"rows": original_trace.rows[:-1], "row_count": len(original_trace.rows) - 1}
    )
    hostile_trace = hostile_trace.model_copy(
        update={"trace_fingerprint": _r4_trace_fingerprint(hostile_trace)}
    )
    trace_artifact = fixture.scalar.artifact_store.write_json_artifact(
        Path("runs") / hostile_trace.execution_id / "r4" / "hostile_trace.json",
        hostile_trace.model_dump(mode="json"),
    )
    fixture.scalar.metadata_store.insert_artifact_reference(trace_artifact)
    hostile_result = outcome.execution.executed_result.model_copy(
        update={
            "product_trace_ref": trace_artifact,
            "product_trace_fingerprint": hostile_trace.trace_fingerprint,
        }
    )
    hostile_result = hostile_result.model_copy(
        update={"result_fingerprint": _r4_result_fingerprint(hostile_result)}
    )
    result_artifact = fixture.scalar.artifact_store.write_json_artifact(
        Path("runs") / hostile_result.execution_id / "r4" / "hostile_trace_result.json",
        hostile_result.model_dump(mode="json"),
    )
    fixture.scalar.metadata_store.insert_artifact_reference(result_artifact)
    validation = _validate_hostile(fixture, outcome, result_artifact)
    assert validation.validated_result is None
    failed_ids = {check.check_id for check in validation.validation_record.checks if not check.passed}
    assert "complete_product_universe" in failed_ids
    assert "trace_context_completeness" in failed_ids


def test_unregistered_equivalent_trace_copy_has_no_authority(tmp_path) -> None:
    fixture = make_r4_fixture(tmp_path, [_row(), _row(order_id="c", order_date="2026-01-03")])
    outcome = run_r4(fixture)
    original = outcome.execution.executed_result.product_trace_ref
    original_path = fixture.scalar.artifact_store.safe_path(original.path)
    copied_path = fixture.scalar.artifact_store.safe_path("temporary", "copied_trace.json")
    copied_path.parent.mkdir(parents=True, exist_ok=True)
    copied_path.write_bytes(original_path.read_bytes())
    copied = ArtifactReference(
        artifact_id=stable_content_id("art", sha256_file(copied_path)),
        path=str(copied_path.relative_to(fixture.scalar.artifact_store.root)),
        fingerprint=sha256_file(copied_path),
        media_type="application/json",
        size_bytes=copied_path.stat().st_size,
    )
    with pytest.raises(R4ArtifactIntegrityError, match="not registered"):
        load_r4_trace(copied, fixture.scalar.artifact_store, fixture.scalar.metadata_store)


def test_validated_result_tamper_fails_authoritative_retrieval(tmp_path) -> None:
    fixture = make_r4_fixture(tmp_path, [_row(), _row(order_id="c", order_date="2026-01-03")])
    outcome = run_r4(fixture)
    artifact = outcome.validation.validated_result_artifact
    path = fixture.scalar.artifact_store.safe_path(artifact.path)
    payload = outcome.validated_result.model_dump(mode="json")
    payload["entry_component"] = "999"
    path.write_bytes(canonical_json_bytes(payload))
    with pytest.raises(R4ArtifactIntegrityError, match="fingerprint mismatch"):
        load_validated_r4_result(artifact, fixture.scalar.artifact_store, fixture.scalar.metadata_store)


def test_validator_rejects_wrong_precision_policy_version_in_result_authority(tmp_path) -> None:
    fixture = make_r4_fixture(tmp_path, [_row(), _row(order_id="c", order_date="2026-01-03")])
    outcome = run_r4(fixture)
    hostile_authority = outcome.execution.executed_result.authority.model_copy(
        update={"precision_policy_version": "stale-v0"}
    )
    hostile = outcome.execution.executed_result.model_copy(update={"authority": hostile_authority})
    hostile = hostile.model_copy(update={"result_fingerprint": _r4_result_fingerprint(hostile)})
    artifact = fixture.scalar.artifact_store.write_json_artifact(
        Path("runs") / hostile.execution_id / "r4" / "hostile_precision_result.json",
        hostile.model_dump(mode="json"),
    )
    fixture.scalar.metadata_store.insert_artifact_reference(artifact)

    validation = _validate_hostile(fixture, outcome, artifact)

    assert validation.validated_result is None
    failed_ids = {check.check_id for check in validation.validation_record.checks if not check.passed}
    assert "authority_binding" in failed_ids
    assert "exact_decimal_no_presentation_repair" in failed_ids


def test_validator_rejects_wrong_precision_policy_version_in_trace_authority(tmp_path) -> None:
    fixture = make_r4_fixture(tmp_path, [_row(), _row(order_id="c", order_date="2026-01-03")])
    outcome = run_r4(fixture)
    original_trace = outcome.execution.product_trace
    hostile_authority = original_trace.authority.model_copy(update={"precision_policy_version": "stale-v0"})
    hostile_trace = original_trace.model_copy(update={"authority": hostile_authority})
    hostile_trace = hostile_trace.model_copy(update={"trace_fingerprint": _r4_trace_fingerprint(hostile_trace)})
    trace_artifact = fixture.scalar.artifact_store.write_json_artifact(
        Path("runs") / hostile_trace.execution_id / "r4" / "hostile_precision_trace.json",
        hostile_trace.model_dump(mode="json"),
    )
    fixture.scalar.metadata_store.insert_artifact_reference(trace_artifact)
    hostile_result = outcome.execution.executed_result.model_copy(
        update={
            "product_trace_ref": trace_artifact,
            "product_trace_fingerprint": hostile_trace.trace_fingerprint,
        }
    )
    hostile_result = hostile_result.model_copy(update={"result_fingerprint": _r4_result_fingerprint(hostile_result)})
    result_artifact = fixture.scalar.artifact_store.write_json_artifact(
        Path("runs") / hostile_result.execution_id / "r4" / "hostile_precision_trace_result.json",
        hostile_result.model_dump(mode="json"),
    )
    fixture.scalar.metadata_store.insert_artifact_reference(result_artifact)

    validation = _validate_hostile(fixture, outcome, result_artifact)

    assert validation.validated_result is None
    failed_ids = {check.check_id for check in validation.validation_record.checks if not check.passed}
    assert "authority_binding" in failed_ids
