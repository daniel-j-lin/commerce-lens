from __future__ import annotations

import ast
import hashlib
import inspect
from decimal import Decimal
from pathlib import Path

import pytest

from commerce_lens.contracts.common import PeriodDefinition
from commerce_lens.engine.r4_execution import R4ExecutionError
from commerce_lens.fixture_runner.r5_discovery import discover_r5_fixtures
from commerce_lens.fixture_runner.r5_inventory import load_r5_inventory
from commerce_lens.fixture_runner.r5_manifest import (
    LoadedR5Fixture,
    R5FixtureManifest,
    R5ManifestError,
)
from commerce_lens.fixture_runner.r5_pf4_adapters import (
    PF4HarnessSetupError,
    PF4_NON_MATERIAL_FIELDS,
    PF4_R4_ACTUAL_OUTPUT_PRODUCER,
    PF4_R4_PREREQUISITE_OUTPUT_PRODUCER,
    build_pf4_upstream_authority,
    build_r5_pf4_adapter_registry,
    classify_r4_failure,
    compare_r4_material,
    observe_independent_scalar_and_r4,
    prepare_hostile_r4_submission,
    project_r4_material,
    run_pf4_r4,
    validate_hostile_r4_submission,
)
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.persistence.r4_repository import (
    R4ArtifactIntegrityError,
    load_authenticated_scalar_validated_result,
)
from tests.fixture_runner.r5_test_support import manifest_payload


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_orders(path: Path, *, continuing_comparison: str = "80.00") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "order_id,order_line_id,order_date,product_id,product_name,category_id,category_name,"
        "quantity,line_revenue,currency,unit_price,eligibility_status\n"
        "b-1,b-l1,2026-07-15,p1,Widget,c1,Widgets,1,100.00,USD,100.00,paid\n"
        "b-2,b-l2,2026-07-16,p2,Legacy,c1,Widgets,1,50.00,USD,50.00,paid\n"
        f"c-1,c-l1,2026-10-15,p1,Widget,c1,Widgets,1,{continuing_comparison},USD,"
        f"{continuing_comparison},paid\n"
        "c-2,c-l2,2026-10-16,p3,New,c1,Widgets,1,40.00,USD,40.00,paid\n",
        encoding="utf-8",
    )
    return path


def _periods() -> tuple[PeriodDefinition, PeriodDefinition]:
    return (
        PeriodDefinition(
            period_id="baseline_q3_2026",
            label="Baseline Q3 2026",
            start_date="2026-07-01",
            end_date="2026-09-30",
            date_convention_ref="order_date_calendar_day",
        ),
        PeriodDefinition(
            period_id="comparison_q4_2026",
            label="Comparison Q4 2026",
            start_date="2026-10-01",
            end_date="2026-12-31",
            date_convention_ref="order_date_calendar_day",
        ),
    )


def _authority(tmp_path: Path, *, continuing_comparison: str = "80.00"):
    source = _write_orders(tmp_path / "orders.csv", continuing_comparison=continuing_comparison)
    baseline, comparison = _periods()
    return build_pf4_upstream_authority(
        source_path=source,
        baseline_period=baseline,
        comparison_period=comparison,
        artifact_store=ArtifactStore(tmp_path / "artifacts"),
        metadata_store=MetadataStore(tmp_path / "metadata.sqlite"),
    )


def _loaded_fixture(
    tmp_path: Path,
    *,
    fixture_id: str = "FX-R5-R4-001A",
    title: str = "PF4 production R4 case",
    purpose: str = "Exercise production R4 without expected-output access.",
    question: str = "Decompose observed Revenue Change by product presence.",
    expected_outcome: str = "deliberately_not_the_actual_result",
    continuing_comparison: str = "80.00",
) -> LoadedR5Fixture:
    source = _write_orders(tmp_path / f"{fixture_id}.csv", continuing_comparison=continuing_comparison)
    payload = manifest_payload(
        fixture_id=fixture_id,
        family="R4",
        layer="B",
        adapter_id="production_r4_material_projection",
        mode="application_service",
    )
    payload.update({"title": title, "purpose": purpose})
    payload["execution"].update(
        {
            "required_capability": "approved_production_r4",
            "required_capability_version": "R4 v1.0",
        }
    )
    payload["inputs"] = [
        {
            "path": source.name,
            "role": "orders",
            "media_type": "text/csv",
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        }
    ]
    payload["context"] = {
        "question_or_proposition": question,
        "execution_context": "reporting",
        "intended_use": "PF4 production R4 conformance",
        "scope": {"scope_id": "all_eligible"},
        "population": None,
        "periods": [
            {
                "period_id": "baseline_q3_2026",
                "label": "Baseline Q3 2026",
                "start_date": "2026-07-01",
                "end_date": "2026-09-30",
                "date_convention_ref": "order_date_calendar_day",
            },
            {
                "period_id": "comparison_q4_2026",
                "label": "Comparison Q4 2026",
                "start_date": "2026-10-01",
                "end_date": "2026-12-31",
                "date_convention_ref": "order_date_calendar_day",
            },
        ],
        "currency": "USD",
    }
    payload["bindings"] = {"r4_method_version": "R4 v1.0"}
    payload["expected"]["material_path"][0]["outcome"] = expected_outcome
    manifest = R5FixtureManifest.model_validate(payload)
    return LoadedR5Fixture(case_dir=tmp_path, manifest=manifest, input_paths=(source.resolve(),))


def _validation_outcome(actual):
    return next(item.outcome for item in actual.material_path if item.stage.value == "validation")


def _business_material(outcome: dict) -> dict:
    scalar_fields = (
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
        "execution_status",
        "validation_status",
        "semantic_boundary",
    )
    row_fields = (
        "product_id",
        "baseline_present",
        "comparison_present",
        "baseline_revenue",
        "comparison_revenue",
        "classification",
        "contribution",
        "assigned_component",
        "currency",
        "method_id",
        "method_version",
        "precision_policy_ref",
        "precision_policy_version",
        "validation_policy_id",
        "validation_policy_version",
    )
    return {
        **{field: outcome[field] for field in scalar_fields},
        "trace_rows": [
            {field: row[field] for field in row_fields}
            for row in outcome["trace_rows"]
        ],
    }


def test_pf4_registry_is_narrow_and_names_the_production_r4_subject() -> None:
    registry = build_r5_pf4_adapter_registry()
    assert {
        "production_r4_diagnostic_gate",
        "production_r4_eligibility_projection",
        "production_r4_material_projection",
        "production_r4_material_projection_with_presentation_observation",
    }.issubset(registry.ids())
    approved_producers = {
        PF4_R4_ACTUAL_OUTPUT_PRODUCER,
        PF4_R4_PREREQUISITE_OUTPUT_PRODUCER,
        "commerce_lens.contracts.r4.R4DecompositionRequest",
        "commerce_lens.validation.r4_validator.validate_r4_decomposition",
        "commerce_lens.persistence.r4_repository.load_r4_trace",
        "commerce_lens.engine.r4_execution.execute_r4_decomposition",
        "commerce_lens.production.scalar_and_r4_chains",
        "commerce_lens.production.r4_same_evaluator_comparison",
        "commerce_lens.fixture_runner.r4_presentation_observation",
        "commerce_lens.fixture_runner.compare_r4_material",
    }
    for adapter_id in registry.ids():
        registration = registry.require(adapter_id)
        assert registration.actual_output_producer in approved_producers
        assert registration.available


def test_upstream_builder_uses_authentic_scalar_and_evidence_authorities(tmp_path) -> None:
    authority = _authority(tmp_path)
    assert authority.baseline_revenue.value == Decimal("150.00")
    assert authority.comparison_revenue.value == Decimal("120.00")
    assert authority.revenue_change.value == Decimal("-30.00")
    for scalar in (
        authority.baseline_revenue,
        authority.comparison_revenue,
        authority.revenue_change,
    ):
        assert (
            load_authenticated_scalar_validated_result(
                scalar.validated_result_id,
                authority.artifact_store,
                authority.metadata_store,
            )
            == scalar
        )
    for evidence, scalar in (
        (authority.baseline_evidence, authority.baseline_revenue),
        (authority.comparison_evidence, authority.comparison_revenue),
        (authority.revenue_change_evidence, authority.revenue_change),
    ):
        assert evidence.validated_result_ids == (scalar.validated_result_id,)
        assert evidence.supported_claim_type.value == "descriptive"
        assert evidence.evidence_role.value == "metric_value"


def test_registered_adapter_calls_the_production_r4_service(tmp_path, monkeypatch) -> None:
    from commerce_lens.fixture_runner import r5_pf4_adapters

    fixture = _loaded_fixture(tmp_path)
    original = r5_pf4_adapters.run_r4_decomposition
    calls = []

    def observed_call(**kwargs):
        calls.append(kwargs["request"].r4_request_id)
        return original(**kwargs)

    monkeypatch.setattr(r5_pf4_adapters, "run_r4_decomposition", observed_call)
    monkeypatch.setattr(
        r5_pf4_adapters,
        "_whole_unit_presentation_observation",
        lambda _material: pytest.fail("ordinary adapter calculated presentation rounding"),
    )
    producer = build_r5_pf4_adapter_registry().require("production_r4_material_projection").producer
    assert producer is not None
    actual = producer(fixture)
    assert len(calls) == 1
    assert actual.actual_output_producer == PF4_R4_ACTUAL_OUTPUT_PRODUCER
    assert _validation_outcome(actual)["validation_status"] == "passed"
    assert "whole_unit_presentation" not in actual.trace_integrity_state
    assert actual.final_disposition == "VALIDATED_R4_MECHANICAL_RESULT"


def test_presentation_adapter_calls_same_subject_only_then_observes_validated_result(
    tmp_path, monkeypatch
) -> None:
    from commerce_lens.fixture_runner import r5_pf4_adapters

    fixture = _loaded_fixture(tmp_path)
    original_run = r5_pf4_adapters.run_r4_decomposition
    original_observation = r5_pf4_adapters._whole_unit_presentation_observation
    calls = []
    observed_statuses = []

    def observed_run(**kwargs):
        calls.append(kwargs["request"].r4_request_id)
        return original_run(**kwargs)

    def observed_presentation(material):
        observed_statuses.append(material.validation_status)
        return original_observation(material)

    monkeypatch.setattr(r5_pf4_adapters, "run_r4_decomposition", observed_run)
    monkeypatch.setattr(
        r5_pf4_adapters,
        "_whole_unit_presentation_observation",
        observed_presentation,
    )
    producer = build_r5_pf4_adapter_registry().require(
        "production_r4_material_projection_with_presentation_observation"
    ).producer
    assert producer is not None
    actual = producer(fixture)
    assert len(calls) == 1
    assert observed_statuses == ["passed"]
    assert actual.actual_output_producer == PF4_R4_ACTUAL_OUTPUT_PRODUCER
    assert actual.trace_integrity_state["validation_status"] == "passed"
    assert "whole_unit_presentation" in actual.trace_integrity_state


def test_material_projection_ignores_only_event_identity_and_detects_material_drift(tmp_path) -> None:
    authority = _authority(tmp_path)
    first_outcome = run_pf4_r4(authority)
    second_outcome = run_pf4_r4(authority)
    assert first_outcome.execution.executed_result.execution_id != second_outcome.execution.executed_result.execution_id
    assert (
        first_outcome.validation.validation_record.validation_id
        != second_outcome.validation.validation_record.validation_id
    )
    first = project_r4_material(first_outcome)
    second = project_r4_material(second_outcome)
    assert compare_r4_material(first, second).conforming
    assert "ExecutedR4DecompositionResult.execution_id" in PF4_NON_MATERIAL_FIELDS

    changed_authority = first.model_copy(
        update={"authority": first.authority.model_copy(update={"method_version": "R4 vNEXT"})}
    )
    comparison = compare_r4_material(first, changed_authority)
    assert comparison.failure_layer == "METHOD_CONFORMANCE"
    assert {item.path for item in comparison.differences} == {"r4.authority.method_version"}

    changed_component = first.model_copy(update={"entry_component": first.entry_component + Decimal("1")})
    assert {item.path for item in compare_r4_material(first, changed_component).differences} == {
        "r4.entry_component"
    }

    changed_row = first.trace_rows[0].model_copy(
        update={"contribution": first.trace_rows[0].contribution + Decimal("1")}
    )
    changed_trace = first.model_copy(update={"trace_rows": (changed_row, *first.trace_rows[1:])})
    assert {item.path for item in compare_r4_material(first, changed_trace).differences} == {
        "r4.trace_rows[0].contribution"
    }

    changed_partition_row = first.trace_rows[1].model_copy(
        update={"classification": "continuing", "assigned_component": "continuing"}
    )
    changed_partition = first.model_copy(
        update={"trace_rows": (first.trace_rows[0], changed_partition_row, *first.trace_rows[2:])}
    )
    assert {item.path for item in compare_r4_material(first, changed_partition).differences} == {
        "r4.trace_rows[1].assigned_component",
        "r4.trace_rows[1].classification",
    }


def test_r4_020_overlapping_partition_reaches_registered_repository_validator_boundary(tmp_path) -> None:
    authority = _authority(tmp_path)
    outcome = run_pf4_r4(authority)
    trace_payload = outcome.execution.product_trace.model_dump(mode="json")
    trace_payload["rows"].append(dict(trace_payload["rows"][0]))
    trace_payload["row_count"] += 1
    submission = prepare_hostile_r4_submission(authority, outcome, trace_payload=trace_payload)

    with pytest.raises(R4ArtifactIntegrityError) as caught:
        validate_hostile_r4_submission(authority, outcome, submission)
    observation = classify_r4_failure(caught.value)
    assert observation.failure_layer == "RESULT_VALIDATION_OR_INTEGRITY"
    assert observation.failure_code == "R4ArtifactIntegrityError"
    assert "schema invalid" in observation.reason
    assert "unique product IDs in stable order" in observation.reason


def test_r4_028_test_local_dependency_loss_fails_inside_genuine_executor(tmp_path, monkeypatch) -> None:
    import commerce_lens.engine.r4_execution as production_executor

    authority = _authority(tmp_path)

    def unavailable(*_args, **_kwargs):
        raise RuntimeError("PF4 test dependency unavailable: DuckDB connection")

    monkeypatch.setattr(production_executor.duckdb, "connect", unavailable)
    with pytest.raises(R4ExecutionError) as caught:
        run_pf4_r4(authority)
    observation = classify_r4_failure(caught.value)
    assert observation.failure_layer == "EXECUTION"
    assert observation.failure_code == "R4ExecutionError"
    assert "R4 deterministic execution failed" in observation.reason
    assert "PF4 test dependency unavailable" in observation.reason


def test_r4_037_same_evaluator_detects_test_side_material_mutation(tmp_path) -> None:
    authority = _authority(tmp_path)
    reference = project_r4_material(run_pf4_r4(authority))
    repeated = project_r4_material(run_pf4_r4(authority))
    assert compare_r4_material(reference, repeated).conforming

    mutated = repeated.model_copy(
        update={"reconciliation_difference": repeated.reconciliation_difference + Decimal("0.01")}
    )
    comparison = compare_r4_material(reference, mutated)
    assert not comparison.conforming
    assert comparison.failure_layer == "METHOD_CONFORMANCE"
    assert {item.path for item in comparison.differences} == {"r4.reconciliation_difference"}


def test_independent_chain_preserves_scalar_authority_when_r4_integrity_fails(tmp_path) -> None:
    authority = _authority(tmp_path)
    outcome = run_pf4_r4(authority)
    trace_payload = outcome.execution.product_trace.model_dump(mode="json")
    trace_payload["rows"].append(dict(trace_payload["rows"][0]))
    trace_payload["row_count"] += 1
    submission = prepare_hostile_r4_submission(authority, outcome, trace_payload=trace_payload)
    observation = observe_independent_scalar_and_r4(
        authority.baseline_revenue,
        lambda: validate_hostile_r4_submission(authority, outcome, submission),
    )
    assert observation.scalar_value == Decimal("150.00")
    assert observation.scalar_validation_fingerprint == authority.baseline_revenue.validation_fingerprint
    assert observation.r4_failure is not None
    assert observation.r4_failure.failure_layer == "RESULT_VALIDATION_OR_INTEGRITY"


def test_diagnostic_missing_r3_authority_stops_before_execution(tmp_path) -> None:
    fixture = _loaded_fixture(tmp_path)
    producer = build_r5_pf4_adapter_registry().require("production_r4_diagnostic_gate").producer
    assert producer is not None
    actual = producer(fixture)
    eligibility, execution = actual.material_path
    assert eligibility.reachability.value == "blocked"
    assert eligibility.outcome == "diagnostic_r3_authority_unavailable"
    assert execution.reachability.value == "not_reached"
    assert actual.trace_integrity_state == {"failure_layer": "ELIGIBILITY"}


def test_adapter_output_is_independent_of_fixture_identity_prose_and_expected_output(tmp_path) -> None:
    first = _loaded_fixture(tmp_path / "first")
    second = _loaded_fixture(
        tmp_path / "second",
        fixture_id="FX-R5-R4-002A",
        title="Completely different title",
        purpose="Different prose cannot select the result.",
        question="Unrelated wording with the same factual source and periods.",
        expected_outcome="a_second_deliberately_wrong_expectation",
    )
    producer = build_r5_pf4_adapter_registry().require("production_r4_material_projection").producer
    assert producer is not None
    first_actual = producer(first)
    second_actual = producer(second)
    first_material = _validation_outcome(first_actual)
    second_material = _validation_outcome(second_actual)
    assert _business_material(first_material) == _business_material(second_material)
    for actual in (first_actual, second_actual):
        assert "whole_unit_presentation" not in actual.trace_integrity_state
        assert actual.final_disposition == "VALIDATED_R4_MECHANICAL_RESULT"


def test_factual_input_mutation_changes_production_actual_output(tmp_path) -> None:
    original = _loaded_fixture(tmp_path / "original", continuing_comparison="80.00")
    changed = _loaded_fixture(
        tmp_path / "changed",
        fixture_id="FX-R5-R4-002A",
        continuing_comparison="70.00",
    )
    producer = build_r5_pf4_adapter_registry().require("production_r4_material_projection").producer
    assert producer is not None
    original_material = _validation_outcome(producer(original))
    changed_material = _validation_outcome(producer(changed))
    assert original_material["observed_revenue_change"] == "-30.00"
    assert changed_material["observed_revenue_change"] == "-40.00"
    assert original_material["continuing_component"] != changed_material["continuing_component"]


def test_hostile_submission_rejects_expected_oracle_fields(tmp_path) -> None:
    authority = _authority(tmp_path)
    outcome = run_pf4_r4(authority)
    trace_payload = outcome.execution.product_trace.model_dump(mode="json")
    trace_payload["expected_failure"] = "overlapping_partition"
    with pytest.raises(PF4HarnessSetupError, match="expected-output key"):
        prepare_hostile_r4_submission(authority, outcome, trace_payload=trace_payload)


def test_pf4_module_has_no_expected_fixture_or_r4_formula_oracle() -> None:
    from commerce_lens.fixture_runner import r5_pf4_adapters

    source = inspect.getsource(r5_pf4_adapters)
    tree = ast.parse(source)
    assert "manifest.expected" not in source
    assert "fixture_id" not in source
    assert ".title" not in source
    assert ".purpose" not in source
    assert "scenario" not in source
    assert "ValidatedResult(" not in source
    assert "AdmissibleEvidence(" not in source
    assert "DataSufficiencyResult(" not in source
    assert "ExecutedR4DecompositionResult(" not in source
    assert "R4ProductClassification" not in source
    assert "R4Component" not in source
    assert "_product_revenues" not in source
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "sum" for node in ast.walk(tree))


def test_unexpected_physical_file_still_fails_closed(tmp_path) -> None:
    inventory = load_r5_inventory(REPO_ROOT)
    active = tmp_path / "active"
    active.mkdir()
    (active / "unexpected.txt").write_text("not a fixture bundle\n", encoding="utf-8")
    with pytest.raises(R5ManifestError, match="unexpected file"):
        discover_r5_fixtures(tmp_path, inventory)
