from __future__ import annotations

import csv
import socket
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import Workbook

from commerce_lens.application import evaluate_claim
from commerce_lens.canonical.models import PeriodCoverageEvidence
from commerce_lens.contracts.common import (
    AvailableEvidence,
    ClaimState,
    ClaimType,
    GroupingDimension,
    MetricState,
    PeriodDefinition,
    ScopeDefinition,
    SourceType,
)
from commerce_lens.contracts.evidence import ClaimPropositionType
from commerce_lens.evidence.identifiers import sha256_file
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.skill.integration import (
    PublicAnalysisIntent,
    PublicClaimIntent,
    PublicQuestionClass,
    PublicSourceSelection,
    bind_claim_candidate_from_authority,
    run_public_analysis,
    validate_public_intent,
)


def test_csv_revenue_orders_and_numeric_aov_supported(tmp_path) -> None:
    cases = (
        ("revenue", Decimal("120.00"), "Revenue"),
        ("orders", 1, "Orders"),
        ("aov", Decimal("120.00"), "AOV"),
    )
    for metric_ref, expected_value, display_name in cases:
        source = _write_csv(
            tmp_path / metric_ref / "orders.csv",
            [
                _row(order_id="q3-o1", order_date="2026-07-15", line_revenue="100.00"),
                _row(order_id="q4-o1", order_date="2026-10-15", line_revenue="120.00"),
            ],
        )
        outcome = _run(tmp_path / metric_ref, _single_intent(source, metric_ref))

        assert outcome.response.supported_claims[0].metric_display_name == display_name
        assert outcome.response.supported_claims[0].metric_state is MetricState.VALID
        assert outcome.response.supported_claims[0].claim_state is ClaimState.ADMISSIBLE
        assert outcome.response.supported_claims[0].value == expected_value
        assert outcome.claim_decisions[0].claim_state is ClaimState.ADMISSIBLE


def test_revenue_change_killer_demo_1_uses_governed_chain_without_percentage_or_recommendation(tmp_path) -> None:
    source = _write_csv(
        tmp_path / "orders.csv",
        [
            _row(order_id="q3-o1", order_date="2026-07-15", line_revenue="100.00"),
            _row(order_id="q4-o1", order_date="2026-10-15", line_revenue="120.00"),
        ],
    )
    outcome = _run(
        tmp_path,
        _revenue_change_intent(source, "How did revenue change from Q3 2026 to Q4 2026?"),
    )
    rendered = outcome.response.render_text()

    assert outcome.request is not None
    assert outcome.analysis_result is not None
    assert outcome.request.metrics[0].metric_id == "revenue_change"
    assert outcome.request.grouping is GroupingDimension.NONE
    assert outcome.analysis_result.metric_results[0].admissible_evidence_refs
    assert outcome.claim_candidates[0].proposition_type is ClaimPropositionType.METRIC_VALUE_EQUALS
    assert outcome.response.supported_claims[0].value == Decimal("20.00")
    assert outcome.response.evidence_summary[0].metric_ref == "revenue_change"
    assert outcome.claim_decisions[0].claim_state is ClaimState.ADMISSIBLE
    assert "%" not in rendered
    assert "why" not in rendered.lower()
    assert "Recommendation" not in rendered


def test_xlsx_equivalent_supported_path(tmp_path) -> None:
    source = _write_xlsx(
        tmp_path / "orders.xlsx",
        "Orders",
        [
            _row(order_id="q3-o1", order_date="2026-07-15", line_revenue="80.00"),
            _row(order_id="q4-o1", order_date="2026-10-15", line_revenue="95.00"),
        ],
    )
    outcome = _run(
        tmp_path,
        _single_intent(
            source,
            "revenue",
            source_type=SourceType.EXCEL_XLSX,
            selected_sheet="Orders",
        ),
    )

    assert outcome.response.supported_claims[0].value == Decimal("95.00")
    assert outcome.response.evidence_summary[0].source_type == "excel_xlsx"


def test_aov_orders_zero_binds_metric_state_is_undefined_not_zero(tmp_path) -> None:
    source = _write_csv(
        tmp_path / "orders.csv",
        [
            _row(order_id="q3-o1", order_date="2026-07-15", eligibility_status="cancelled"),
            _row(order_id="q4-o1", order_date="2026-10-15", eligibility_status="cancelled"),
        ],
    )
    outcome = _run(tmp_path, _single_intent(source, "aov"))
    claim = outcome.response.supported_claims[0]
    candidate = outcome.claim_candidates[0]

    assert claim.metric_state is MetricState.UNDEFINED
    assert claim.claim_state is ClaimState.ADMISSIBLE
    assert claim.value is None
    assert claim.undefined_reason == "orders_equals_zero"
    assert candidate.proposition_type is ClaimPropositionType.METRIC_STATE_IS
    assert candidate.claimed_metric_state is MetricState.UNDEFINED
    assert candidate.claimed_value is None
    assert Decimal("0") != claim.value


def test_diagnostic_killer_demo_2_supports_descriptive_change_and_refuses_why(tmp_path) -> None:
    source = _write_csv(
        tmp_path / "orders.csv",
        [
            _row(order_id="q3-o1", order_date="2026-07-15", line_revenue="120.00"),
            _row(order_id="q4-o1", order_date="2026-10-15", line_revenue="100.00"),
        ],
    )
    intent = replace(
        _revenue_change_intent(source, "Why did revenue drop from Q3 2026 to Q4 2026?"),
        question_class=PublicQuestionClass.DIAGNOSTIC_REVENUE_DROP,
        claim_intents=(
            PublicClaimIntent(ClaimType.DESCRIPTIVE, "Revenue Change descriptive portion"),
            PublicClaimIntent(ClaimType.DIAGNOSTIC, "Diagnostic reason for Revenue decline"),
        ),
    )
    outcome = _run(tmp_path, intent)
    rendered = outcome.response.render_text()

    assert [decision.claim_state for decision in outcome.claim_decisions] == [
        ClaimState.ADMISSIBLE,
        ClaimState.INADMISSIBLE,
    ]
    assert outcome.claim_decisions[1].failure_code == "unsupported_claim_type"
    assert outcome.response.supported_claims[0].value == Decimal("-20.00")
    assert "Insufficient evidence to conclude why Revenue declined." in rendered
    assert "approved diagnostic workflow" in rendered
    for prohibited in ("promotion", "seasonality", "competition", "traffic", "inventory", "demand"):
        assert prohibited not in rendered.lower()


def test_forecast_recommendation_product_category_and_percentage_are_rejected(tmp_path) -> None:
    source = _write_csv(tmp_path / "orders.csv", [_row()])

    invalid_intents = (
        replace(_single_intent(source, "revenue"), claim_intents=(PublicClaimIntent(ClaimType.PREDICTIVE),)),
        replace(_single_intent(source, "revenue"), claim_intents=(PublicClaimIntent(ClaimType.PRESCRIPTIVE),)),
        replace(_single_intent(source, "revenue"), grouping=GroupingDimension.PRODUCT),
        replace(_single_intent(source, "revenue"), grouping=GroupingDimension.CATEGORY),
        _revenue_change_percentage_intent(source),
    )

    for intent in invalid_intents:
        outcome = _run(tmp_path, intent)
        assert outcome.request is None
        assert outcome.response.clarification_required


def test_ambiguous_period_and_mapping_require_clarification(tmp_path) -> None:
    source = _write_csv(tmp_path / "orders.csv", [_row()])
    ambiguous_period = replace(_single_intent(source, "revenue"), comparison_period=None)
    ambiguous_mapping = replace(
        _single_intent(source, "revenue"),
        source=PublicSourceSelection(source, SourceType.CSV, mapping_mode="needs_user_mapping"),
    )

    assert "explicit governed baseline" in validate_public_intent(ambiguous_period)[0]
    assert "mapping selection requires clarification" in validate_public_intent(ambiguous_mapping)


def test_missing_governed_data_produces_no_supported_claim(tmp_path) -> None:
    source = _write_csv(tmp_path / "orders.csv", [_row(line_revenue="")])
    outcome = _run(tmp_path, _single_intent(source, "revenue"))

    assert outcome.response.supported_claims == ()
    assert outcome.claim_decisions == ()
    assert outcome.response.blocked
    assert outcome.response.insufficient_evidence_message == "Insufficient evidence to conclude."


def test_missing_evidence_or_validation_failure_produces_no_supported_claim(tmp_path, monkeypatch) -> None:
    source = _write_csv(tmp_path / "orders.csv", [_row()])
    baseline = _single_intent(source, "revenue")
    no_evidence_outcome = _run(
        tmp_path / "no-evidence",
        baseline,
        available_evidence=(
            AvailableEvidence(
                evidence_id="avail_source",
                description="source only",
                source_ref="placeholder",
                satisfies_requirement_ids=("req_global",),
            ),
        ),
    )

    assert no_evidence_outcome.response.supported_claims == ()
    assert no_evidence_outcome.claim_decisions == ()

    import commerce_lens.skill.integration as integration
    from commerce_lens.contracts.results import AnalysisResult, MetricResult

    original_run_analysis = integration.run_analysis

    def validation_failed(*args, **kwargs):
        result = original_run_analysis(*args, **kwargs)
        metric = result.metric_results[0]
        failed_metric = MetricResult(
            metric_ref=metric.metric_ref,
            metric_state=MetricState.INADMISSIBLE,
            failure_details=metric.failure_details,
        )
        return AnalysisResult(
            request_id=result.request_id,
            run_id=result.run_id,
            run_status=result.run_status,
            data_sufficiency_ref=result.data_sufficiency_ref,
            data_sufficiency_state=result.data_sufficiency_state,
            metric_results=(failed_metric,),
            failure_details=result.failure_details,
        )

    monkeypatch.setattr(integration, "run_analysis", validation_failed)
    failed_outcome = _run(tmp_path / "validation-failed", baseline)

    assert failed_outcome.response.supported_claims == ()
    assert failed_outcome.claim_decisions == ()


def test_claim_candidate_exact_ref_binding_and_equal_value_substitution_rejected(tmp_path) -> None:
    first_source = _write_csv(
        tmp_path / "first.csv",
        [
            _row(order_id="q3-o1", order_date="2026-07-15", line_revenue="50.00"),
            _row(order_id="q4-o1", order_date="2026-10-15", line_revenue="75.00"),
        ],
    )
    second_source = _write_csv(
        tmp_path / "second.csv",
        [
            _row(order_id="q3-o2", order_date="2026-07-15", line_revenue="50.00"),
            _row(order_id="q4-o2", order_date="2026-10-15", line_revenue="75.00"),
        ],
    )
    artifact_store = ArtifactStore(tmp_path / "runtime")
    metadata_store = MetadataStore(tmp_path / "metadata.sqlite")
    first = run_public_analysis(_single_intent(first_source, "revenue"), artifact_store=artifact_store, metadata_store=metadata_store)
    second = run_public_analysis(_single_intent(second_source, "revenue"), artifact_store=artifact_store, metadata_store=metadata_store)

    assert first.claim_candidates[0].claimed_value == second.claim_candidates[0].claimed_value == Decimal("75.00")
    assert first.claim_candidates[0].supporting_evidence_refs[0] in first.analysis_result.admissible_evidence_refs
    assert first.claim_candidates[0].supporting_validated_result_refs[0] in first.analysis_result.validated_result_refs

    forged = first.claim_candidates[0].model_copy(
        update={
            "claim_candidate_id": "clmcand_test_forged_cross_request",
            "claim_id": "claim_test_forged_cross_request",
            "supporting_evidence_refs": second.claim_candidates[0].supporting_evidence_refs,
            "supporting_validated_result_refs": second.claim_candidates[0].supporting_validated_result_refs,
        }
    )
    decision = evaluate_claim(forged, artifact_store=artifact_store, metadata_store=metadata_store)

    assert decision.claim_state is ClaimState.INADMISSIBLE
    assert decision.failure_code in {"cross_request_substitution", "wrong_validated_result"}


def test_no_network_requirement_and_input_source_immutable(tmp_path, monkeypatch) -> None:
    source = _write_csv(tmp_path / "orders.csv", [_row()])
    original_fingerprint = sha256_file(source)

    def forbidden_socket(*args, **kwargs):
        raise AssertionError("network is not allowed")

    monkeypatch.setattr(socket, "socket", forbidden_socket)
    outcome = _run(tmp_path, _single_intent(source, "orders"))

    assert outcome.response.supported_claims[0].value == 1
    assert sha256_file(source) == original_fingerprint


def test_bind_claim_candidate_uses_analysis_result_refs_not_metric_name_search(tmp_path) -> None:
    source = _write_csv(tmp_path / "orders.csv", [_row()])
    artifact_store = ArtifactStore(tmp_path / "runtime")
    metadata_store = MetadataStore(tmp_path / "metadata.sqlite")
    intent = _single_intent(source, "revenue")
    outcome = run_public_analysis(intent, artifact_store=artifact_store, metadata_store=metadata_store)
    assert outcome.analysis_result is not None

    stripped = outcome.analysis_result.model_copy(
        update={
            "metric_results": (
                outcome.analysis_result.metric_results[0].model_copy(
                    update={"validated_result_refs": (), "admissible_evidence_refs": ()}
                ),
            )
        }
    )

    with pytest.raises(ValueError, match="expected one exact ValidatedResult"):
        bind_claim_candidate_from_authority(
            intent,
            stripped,
            artifact_store=artifact_store,
            metadata_store=metadata_store,
            claim_type=ClaimType.DESCRIPTIVE,
            proposed_meaning="must fail without exact refs",
        )


def _run(tmp_path, intent, **kwargs):
    return run_public_analysis(
        intent,
        artifact_store=ArtifactStore(Path(tmp_path) / "runtime"),
        metadata_store=MetadataStore(Path(tmp_path) / "metadata.sqlite"),
        **kwargs,
    )


def _single_intent(
    source: Path,
    metric_id: str,
    *,
    source_type: SourceType = SourceType.CSV,
    selected_sheet: str | None = None,
) -> PublicAnalysisIntent:
    return PublicAnalysisIntent(
        question_class=PublicQuestionClass.SINGLE_PERIOD_METRIC,
        metric_id=metric_id,
        baseline_period=_q3(),
        comparison_period=_q4(),
        result_period_role="comparison",
        source=PublicSourceSelection(source, source_type, selected_sheet=selected_sheet),
        original_question_text=f"What was {metric_id} in Q4 2026?",
    )


def _revenue_change_intent(source: Path, question: str) -> PublicAnalysisIntent:
    return PublicAnalysisIntent(
        question_class=PublicQuestionClass.REVENUE_CHANGE,
        metric_id="revenue_change",
        baseline_period=_q3(),
        comparison_period=_q4(),
        source=PublicSourceSelection(source, SourceType.CSV),
        original_question_text=question,
    )


def _revenue_change_percentage_intent(source: Path) -> PublicAnalysisIntent:
    return PublicAnalysisIntent(
        question_class=PublicQuestionClass.REVENUE_CHANGE,
        metric_id="revenue_change_pct",
        baseline_period=_q3(),
        comparison_period=_q4(),
        source=PublicSourceSelection(source, SourceType.CSV),
        original_question_text="What was Revenue Change percentage from Q3 2026 to Q4 2026?",
    )


def _q3() -> PeriodDefinition:
    return PeriodDefinition(
        period_id="baseline",
        label="Q3 2026",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 9, 30),
        date_convention_ref="order_date_utc",
    )


def _q4() -> PeriodDefinition:
    return PeriodDefinition(
        period_id="comparison",
        label="Q4 2026",
        start_date=date(2026, 10, 1),
        end_date=date(2026, 12, 31),
        date_convention_ref="order_date_utc",
    )


CSV_HEADERS = (
    "order_id",
    "order_line_id",
    "order_date",
    "product_id",
    "product_name",
    "category_id",
    "category_name",
    "quantity",
    "line_revenue",
    "currency",
    "unit_price",
    "eligibility_status",
)


def _row(**updates) -> dict[str, str]:
    row = {
        "order_id": "o1",
        "order_line_id": "l1",
        "order_date": "2026-10-15",
        "product_id": "p1",
        "product_name": "Widget",
        "category_id": "c1",
        "category_name": "Widgets",
        "quantity": "1",
        "line_revenue": "10.00",
        "currency": "USD",
        "unit_price": "10.00",
        "eligibility_status": "paid",
    }
    row.update(updates)
    return row


def _write_csv(path: Path, rows: list[dict[str, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _write_xlsx(path: Path, sheet_name: str, rows: list[dict[str, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    sheet.append(CSV_HEADERS)
    for row in rows:
        sheet.append([row.get(header, "") for header in CSV_HEADERS])
    workbook.save(path)
    return path
