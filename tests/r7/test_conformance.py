import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from commerce_lens.contracts.diagnostic import AnalyticalOutcome, TestEligibility as Eligibility
from commerce_lens.diagnostic.r7_evaluation import map_r7_outcome
from commerce_lens.engine.r7_execution import spearman_rho
from commerce_lens.application import r7_service
from tests.contracts.test_r7_contracts import _evidence_set
from tests.engine.test_r7_execution import _request


FIXTURES = Path(__file__).parents[2] / "fixtures" / "r7" / "cases.json"


def test_six_pinned_analytical_fixture_outcomes_are_independently_recomputed():
    cases = json.loads(FIXTURES.read_text())["cases"]
    assert [case["case_id"] for case in cases] == [
        "FX-R7-PROD-001A", "FX-R7-NOT-MET-001", "FX-R7-CONTRADICTED-001",
        "FX-R7-INCONCLUSIVE-N-001", "FX-R7-INCONCLUSIVE-X-001", "FX-R7-INCONCLUSIVE-Y-001",
    ]
    expected = {
        "CRITERION_MET": AnalyticalOutcome.CRITERION_MET,
        "CRITERION_NOT_MET": AnalyticalOutcome.CRITERION_NOT_MET,
        "PROPOSITION_CONTRADICTED": AnalyticalOutcome.PROPOSITION_CONTRADICTED,
        "NOT_EVALUATED": AnalyticalOutcome.NOT_EVALUATED,
    }
    for case in cases:
        rho = spearman_rho(case["distances"], case["weekly_revenues"])
        if case["expected_rho"] is None:
            assert rho is None or case["baseline_weeks"] + case["comparison_weeks"] < 8
            outcome = map_r7_outcome(None, (case["reason"],))
        else:
            assert rho == pytest.approx(case["expected_rho"])
            outcome = map_r7_outcome(rho)
        assert outcome is expected[case["expected_material_outcome"]]


def test_ineligible_handoff_fails_before_executor(monkeypatch):
    calls = 0
    def forbidden(**kwargs):
        nonlocal calls; calls += 1
    monkeypatch.setattr(r7_service, "execute_r7_diagnostic", forbidden)
    request = _request(); evidence = _evidence_set()
    fake_handoff = SimpleNamespace(
        handoff_fingerprint=request.handoff_fingerprint,
        test_eligibility=Eligibility.NOT_ELIGIBLE,
    )
    fake_r6 = SimpleNamespace(load_r6_to_r7_handoff=lambda *args, **kwargs: fake_handoff)
    with pytest.raises(ValueError, match="R7_GATE_HANDOFF_NOT_ELIGIBLE"):
        r7_service.run_r7_diagnostic(
            request=request, evidence_inputs=evidence, canonical_dataset=None,
            baseline_population=None, comparison_population=None, r6_repository=fake_r6,
            r7_repository=None, authority_registry=None,
        )
    assert calls == 0


def test_structured_evidence_supports_bounded_noncausal_why_explanation_only():
    fixture = json.loads(FIXTURES.read_text())
    primary = fixture["cases"][0]
    assert primary["expected_material_outcome"] == "CRITERION_MET"
    assert primary["expected_rho"] <= -0.5
    # Clause mapping: observations/distances → association; threshold → criterion;
    # authority wording → plausible contributor only; limitations → no causality or ruled-out alternatives.
    from commerce_lens.diagnostic.r7_method_registry import METHOD_DEFINITION
    text = " ".join((METHOD_DEFINITION.maximum_permitted_meaning, *METHOD_DEFINITION.prohibited_meanings, *METHOD_DEFINITION.limitations)).lower()
    assert "association" in text and "causal" in text
    assert all(term in text for term in ("seasonality", "discount", "inventory", "demand", "external"))


def test_r7_defines_no_claim_finding_or_r8_artifact_type():
    from commerce_lens.persistence.r7_repository import R7ArtifactType
    names = " ".join(item.value for item in R7ArtifactType).lower()
    assert "claim" not in names and "finding" not in names and "r8" not in names
