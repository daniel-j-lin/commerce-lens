from __future__ import annotations

import csv
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import pytest

from commerce_lens.canonical.models import PeriodCoverageEvidence
from commerce_lens.contracts.common import (
    AvailableEvidence,
    ClaimType,
    PeriodDefinition,
    SourceType,
)
from commerce_lens.contracts.diagnostic import AnalyticalOutcome
from commerce_lens.intake.registry import DatasetRegistry
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.skill.integration import (
    PublicAnalysisIntent,
    PublicClaimIntent,
    PublicQuestionClass,
    PublicSourceSelection,
    run_public_analysis,
)


HEADERS = (
    "order_id", "order_line_id", "order_date", "product_id", "product_name",
    "category_id", "category_name", "quantity", "line_revenue", "currency",
    "unit_price", "eligibility_status",
)


@pytest.mark.parametrize(
    ("revenues", "inverse_mix", "expected", "phrase"),
    (
        ((800, 700, 600, 500, 400, 300, 200, 100), False, AnalyticalOutcome.CRITERION_MET, "one possible explanation"),
        ((100, 300, 700, 800, 200, 400, 500, 600), False, AnalyticalOutcome.CRITERION_NOT_MET, "did not reach the support threshold"),
        ((800, 700, 600, 500, 400, 300, 200, 100), True, AnalyticalOutcome.PROPOSITION_CONTRADICTED, "opposite direction"),
        ((800, 800, 800), False, AnalyticalOutcome.NOT_EVALUATED, "too few complete weeks"),
    ),
)
def test_public_diagnostic_executes_all_governed_terminal_outcomes(
    tmp_path: Path,
    revenues: tuple[int, ...],
    inverse_mix: bool,
    expected: AnalyticalOutcome,
    phrase: str,
) -> None:
    outcome = _run(tmp_path, revenues, inverse_mix=inverse_mix)

    assert outcome.response.diagnostic_analysis is not None
    assert outcome.response.diagnostic_analysis.analytical_outcome is expected
    assert outcome.response.diagnostic_analysis.family_id == "product_composition_association"
    assert outcome.response.diagnostic_analysis.method_id == "weekly_product_presence_revenue_association"
    rendered = outcome.response.render_text()
    assert phrase in rendered
    assert "statistically significant" not in rendered.lower()
    assert "Recommendation" not in rendered
    if expected is AnalyticalOutcome.CRITERION_MET:
        assert "does not prove that product mix caused" in rendered


def test_insufficient_descriptive_evidence_does_not_invoke_r7(tmp_path: Path, monkeypatch) -> None:
    import commerce_lens.skill.integration as integration

    source = _write_rows(tmp_path / "orders.csv", [_row(date(2026, 1, 5), "P1", "")])
    invoked = False

    def forbidden(**kwargs):
        nonlocal invoked
        invoked = True
        raise AssertionError("R7 orchestration must not be invoked")

    monkeypatch.setattr(integration, "run_public_r7_flow", forbidden)
    outcome = _run_source(tmp_path, source)

    assert invoked is False
    assert outcome.response.diagnostic_analysis is None
    assert outcome.response.insufficient_evidence_message == "Insufficient evidence to conclude."


def test_unsupported_diagnostic_family_fails_before_execution(tmp_path: Path, monkeypatch) -> None:
    import commerce_lens.skill.integration as integration

    source = _source(tmp_path, (800, 700, 600, 500, 400, 300, 200, 100))
    intent = replace(_intent(source), diagnostic_family_id="discounting_association")
    monkeypatch.setattr(
        integration,
        "run_public_r7_flow",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("must not execute")),
    )
    outcome = _run_source(tmp_path, source, intent=intent)

    assert outcome.request is None
    assert outcome.response.clarification_required == (
        "unsupported diagnostic family: discounting_association",
    )


def test_causal_wording_never_produces_a_causal_overclaim(tmp_path: Path) -> None:
    source = _source(tmp_path, (800, 700, 600, 500, 400, 300, 200, 100))
    intent = replace(
        _intent(source),
        original_question_text="What caused Revenue to fall, and what should I do?",
        claim_intents=(PublicClaimIntent(ClaimType.CAUSAL, "cause"),),
    )
    outcome = _run_source(tmp_path, source, intent=intent)

    assert outcome.request is None
    assert "unsupported Claim type: causal" in outcome.response.clarification_required


def test_missing_product_id_fails_closed_without_r7(tmp_path: Path, monkeypatch) -> None:
    import commerce_lens.skill.integration as integration

    rows = [_row(date(2026, 1, 5) + timedelta(days=7 * week), "P1", 100 - week) for week in range(8)]
    source = _write_rows(tmp_path / "orders.csv", rows, headers=tuple(item for item in HEADERS if item != "product_id"))
    invoked = False

    def forbidden(**kwargs):
        nonlocal invoked
        invoked = True
        raise AssertionError("R7 orchestration must not be invoked")

    monkeypatch.setattr(integration, "run_public_r7_flow", forbidden)
    outcome = _run_source(tmp_path, source)

    assert invoked is False
    assert outcome.response.insufficient_evidence_message == "Insufficient evidence to conclude."
    assert "product_id" in " ".join(
        (*outcome.response.clarification_required, *outcome.response.additional_evidence_needed)
    )


def test_tampered_r6_handoff_never_invokes_r7(tmp_path: Path, monkeypatch) -> None:
    import commerce_lens.application.public_r7_service as service

    source = _source(tmp_path, (800, 700, 600, 500, 400, 300, 200, 100))
    invoked = False

    def reject_handoff(self, *args, **kwargs):
        raise ValueError("tampered R6 handoff")

    def forbidden_r7(**kwargs):
        nonlocal invoked
        invoked = True
        raise AssertionError("R7 must not execute")

    monkeypatch.setattr(service.R6Repository, "load_r6_to_r7_handoff", reject_handoff)
    monkeypatch.setattr(service, "run_r7_diagnostic", forbidden_r7)
    outcome = _run_source(tmp_path, source)

    assert invoked is False
    assert outcome.response.diagnostic_analysis is None
    assert outcome.response.insufficient_evidence_message == "Insufficient evidence to conclude."


def test_tampered_r7_terminal_result_is_not_rendered_as_authoritative(tmp_path: Path, monkeypatch) -> None:
    import commerce_lens.application.public_r7_service as service

    source = _source(tmp_path, (800, 700, 600, 500, 400, 300, 200, 100))

    def reject_terminal(self, *args, **kwargs):
        raise ValueError("tampered R7 terminal result")

    monkeypatch.setattr(service.R7Repository, "load_complete_posttest_evaluation", reject_terminal)
    outcome = _run_source(tmp_path, source)

    assert outcome.response.diagnostic_analysis is None
    assert outcome.response.insufficient_evidence_message == "Insufficient evidence to conclude."
    assert "tampered R7 terminal result" in outcome.response.additional_evidence_needed[0]


def test_production_public_wiring_has_no_test_or_fixture_authority_imports() -> None:
    root = Path(__file__).parents[2]
    for relative in (
        "src/commerce_lens/application/public_r7_service.py",
        "src/commerce_lens/skill/integration.py",
        "src/commerce_lens/skill/public_response.py",
    ):
        text = (root / relative).read_text(encoding="utf-8")
        assert "from tests" not in text
        assert "import tests" not in text
        assert "fixtures/r7" not in text
        assert "TEST / CONFORMANCE AUTHORITY ONLY" not in text


def _run(tmp_path: Path, revenues: tuple[int, ...], *, inverse_mix: bool = False):
    source = _source(tmp_path, revenues, inverse_mix=inverse_mix)
    return _run_source(tmp_path, source)


def _run_source(tmp_path: Path, source: Path, *, intent: PublicAnalysisIntent | None = None):
    artifacts = ArtifactStore(tmp_path / "runtime")
    selection = PublicSourceSelection(source, SourceType.CSV)
    dataset = DatasetRegistry(artifacts).register_source(source, SourceType.CSV)
    authority = {
        "available_evidence": (
            AvailableEvidence(
                evidence_id="public-r7-test-coverage",
                description="Test-authored complete bounded fixture",
                source_ref=dataset.dataset_id,
                satisfies_requirement_ids=("req_global", "req_revenue_change"),
            ),
        ),
        "period_coverage_evidence": (
            PeriodCoverageEvidence(
                coverage_ref_id="public-r7-test-periods",
                dataset_ref_id=dataset.dataset_id,
                observed_start_date=date(2026, 1, 5),
                observed_end_date=date(2026, 3, 1),
                date_convention_ref="order_date_utc",
                governing_note_ref="test-authored-complete-fixture",
            ),
        ),
    }
    return run_public_analysis(
        intent or _intent(source),
        artifact_store=artifacts,
        metadata_store=MetadataStore(tmp_path / "metadata.sqlite"),
        **authority,
    )


def _intent(source: Path) -> PublicAnalysisIntent:
    return PublicAnalysisIntent(
        question_class=PublicQuestionClass.DIAGNOSTIC_REVENUE_DROP,
        metric_id="revenue_change",
        baseline_period=PeriodDefinition(
            period_id="baseline", label="Baseline", start_date=date(2026, 1, 5),
            end_date=date(2026, 2, 1), date_convention_ref="order_date_utc",
        ),
        comparison_period=PeriodDefinition(
            period_id="comparison", label="Comparison", start_date=date(2026, 2, 2),
            end_date=date(2026, 3, 1), date_convention_ref="order_date_utc",
        ),
        source=PublicSourceSelection(source, SourceType.CSV),
        original_question_text="What caused Revenue to fall?",
        claim_intents=(PublicClaimIntent(ClaimType.DESCRIPTIVE, "Revenue Change"),),
        diagnostic_family_id="product_composition_association",
    )


def _source(tmp_path: Path, revenues: tuple[int, ...], *, inverse_mix: bool = False) -> Path:
    products = tuple(f"P{index}" for index in range(8))
    rows = []
    for week, revenue in enumerate(revenues):
        if inverse_mix:
            sizes = (1, 2, 3, 4, 8, 7, 6, 5)
            if week < 4:
                starts = (0, 1, 3, 4)
                active = tuple(products[(starts[week] + offset) % 8] for offset in range(sizes[week]))
            else:
                active = products[: sizes[week]]
        else:
            active = products[: max(1, 8 - week)]
        day = date(2026, 1, 5) + timedelta(days=7 * week)
        for index, product in enumerate(active):
            rows.append(_row(day, product, revenue if index == 0 else 0, suffix=f"{week}-{index}"))
    return _write_rows(tmp_path / "orders.csv", rows)


def _row(day: date, product: str, revenue, *, suffix: str = "0") -> dict[str, object]:
    return {
        "order_id": f"o-{suffix}", "order_line_id": f"l-{suffix}",
        "order_date": day.isoformat(), "product_id": product, "product_name": product,
        "category_id": "c1", "category_name": "Category", "quantity": 1,
        "line_revenue": revenue, "currency": "USD", "unit_price": revenue or 0,
        "eligibility_status": "paid",
    }


def _write_rows(path: Path, rows: list[dict[str, object]], *, headers=HEADERS) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path
