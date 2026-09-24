from __future__ import annotations

import pytest

from commerce_lens.application.analysis_service import SUPPORTED_APPLICATION_METRICS
from commerce_lens.application.r4_service import R4EligibilityError
from commerce_lens.contracts.r4 import R4ExecutionContext
from commerce_lens.contracts.sufficiency import MetricEligibility, SufficiencyState
from tests.engine.test_execution import _row
from tests.r4.support import make_r4_fixture, run_r4


def test_standalone_succeeds_without_r2_r3_or_claim_authority(tmp_path) -> None:
    fixture = make_r4_fixture(
        tmp_path,
        [
            _row(order_id="b", order_date="2026-01-01", line_revenue="1"),
            _row(order_id="c", order_date="2026-01-03", line_revenue="2"),
        ],
    )
    outcome = run_r4(fixture)
    assert outcome.validated_result.intended_use == "standalone_mechanical_decomposition"
    payload = outcome.validated_result.model_dump(mode="json")
    assert not any("claim" in key or "finding" in key or "proposition" in key for key in payload)


def test_diagnostic_context_without_exact_r3_authority_fails_before_execution(tmp_path) -> None:
    fixture = make_r4_fixture(tmp_path, [_row(), _row(order_id="c", order_date="2026-01-03")])
    diagnostic = fixture.request.model_copy(
        update={
            "execution_context": R4ExecutionContext.DIAGNOSTIC_WORKFLOW,
            "diagnostic_proposition_ref": "prop_exact",
            "diagnostic_r3_profile_ref": "profile_unavailable",
            "diagnostic_r3_profile_version": "r3_v1",
        }
    )
    with pytest.raises(R4EligibilityError, match="not eligible") as exc:
        run_r4(fixture, request=diagnostic)
    assert exc.value.code == "diagnostic_r3_authority_unavailable"


@pytest.mark.parametrize(
    ("update", "code"),
    [
        ({"method_version": "R4 v2.0"}, "r4_method_authority_mismatch"),
        ({"plan_fingerprint": "0" * 64}, "plan_binding_mismatch"),
        ({"baseline_population_fingerprint": "1" * 64}, "population_binding_mismatch"),
        (
            {"confirmed_product_identity_defect_refs": ("confirmed_cross_period_id_reuse",)},
            "product_identity_defect",
        ),
    ],
)
def test_stale_or_defective_authority_fails_closed(tmp_path, update, code) -> None:
    fixture = make_r4_fixture(tmp_path, [_row(), _row(order_id="c", order_date="2026-01-03")])
    with pytest.raises(R4EligibilityError) as exc:
        run_r4(fixture, request=fixture.request.model_copy(update=update))
    assert exc.value.code == code


def test_equivalent_copied_scalar_value_without_validated_lineage_is_rejected(tmp_path) -> None:
    fixture = make_r4_fixture(tmp_path, [_row(), _row(order_id="c", order_date="2026-01-03")])
    copied = fixture.request.model_copy(
        update={"baseline_revenue_validated_result_ref": "valres_equivalent_value_without_lineage"}
    )
    with pytest.raises(RuntimeError, match="authority is missing"):
        run_r4(fixture, request=copied)


def test_insufficient_coverage_authority_blocks_before_execution(tmp_path) -> None:
    fixture = make_r4_fixture(tmp_path, [_row(), _row(order_id="c", order_date="2026-01-03")])
    insufficient = fixture.scalar.sufficiency.model_copy(
        update={
            "sufficiency_id": "suff_r4_incomplete_coverage",
            "metric_eligibility": (
                MetricEligibility(metric_ref="revenue_change", eligible=False),
            ),
            "state": SufficiencyState.INSUFFICIENT_EVIDENCE,
        }
    )
    fixture.scalar.metadata_store.insert_data_sufficiency_result(
        insufficient,
        fixture.scalar.artifact_store,
    )
    request = fixture.request.model_copy(update={"sufficiency_ref": insufficient.sufficiency_id})
    with pytest.raises(R4EligibilityError) as exc:
        run_r4(fixture, request=request)
    assert exc.value.code == "insufficient_governed_evidence"


def test_public_metric_surface_does_not_expose_r4() -> None:
    assert SUPPORTED_APPLICATION_METRICS == frozenset({"revenue", "orders", "aov", "revenue_change"})
    assert "product_level_revenue_decomposition" not in SUPPORTED_APPLICATION_METRICS
