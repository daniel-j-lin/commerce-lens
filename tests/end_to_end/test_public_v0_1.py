from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from commerce_lens.contracts.common import ClaimState, ClaimType, MetricState, PeriodDefinition, SourceType
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore, SCHEMA_VERSION
from commerce_lens.skill.integration import (
    PublicAnalysisIntent,
    PublicClaimIntent,
    PublicQuestionClass,
    PublicSourceSelection,
    run_public_analysis,
)


def test_public_v0_1_killer_demos_and_aov_undefined_end_to_end(tmp_path) -> None:
    source = _write_csv(
        tmp_path / "public_v0_1.csv",
        [
            _row(order_id="q3-o1", order_date="2026-07-15", line_revenue="120.00"),
            _row(order_id="q4-o1", order_date="2026-10-15", line_revenue="100.00"),
        ],
    )
    artifact_store = ArtifactStore(tmp_path / "runtime")
    metadata_store = MetadataStore(tmp_path / "metadata.sqlite")

    demo_1 = run_public_analysis(
        _intent(source, "How did revenue change from Q3 2026 to Q4 2026?"),
        artifact_store=artifact_store,
        metadata_store=metadata_store,
    )
    demo_2 = run_public_analysis(
        _intent(
            source,
            "Why did revenue drop from Q3 2026 to Q4 2026?",
            question_class=PublicQuestionClass.DIAGNOSTIC_REVENUE_DROP,
            claim_intents=(
                PublicClaimIntent(ClaimType.DESCRIPTIVE, "Revenue Change descriptive portion"),
                PublicClaimIntent(ClaimType.DIAGNOSTIC, "Diagnostic explanation"),
            ),
        ),
        artifact_store=artifact_store,
        metadata_store=metadata_store,
    )
    aov_source = _write_csv(
        tmp_path / "aov_zero.csv",
        [
            _row(order_id="q3-o1", order_date="2026-07-15", eligibility_status="cancelled"),
            _row(order_id="q4-o1", order_date="2026-10-15", eligibility_status="cancelled"),
        ],
    )
    aov = run_public_analysis(
        PublicAnalysisIntent(
            question_class=PublicQuestionClass.SINGLE_PERIOD_METRIC,
            metric_id="aov",
            baseline_period=_q3(),
            comparison_period=_q4(),
            result_period_role="comparison",
            source=PublicSourceSelection(aov_source, SourceType.CSV),
            original_question_text="What was AOV in Q4 2026?",
        ),
        artifact_store=ArtifactStore(tmp_path / "aov-runtime"),
        metadata_store=MetadataStore(tmp_path / "aov-metadata.sqlite"),
    )

    assert demo_1.response.supported_claims[0].metric_ref == "revenue_change"
    assert demo_1.response.supported_claims[0].value == Decimal("-20.00")
    assert demo_1.claim_decisions[0].claim_state is ClaimState.ADMISSIBLE
    assert "%" not in demo_1.response.render_text()
    assert "Recommendation" not in demo_1.response.render_text()

    assert demo_2.response.supported_claims[0].value == Decimal("-20.00")
    assert demo_2.claim_decisions[1].claim_state is ClaimState.INADMISSIBLE
    assert demo_2.claim_decisions[1].failure_code == "unsupported_claim_type"
    assert "Insufficient evidence to conclude why Revenue declined." in demo_2.response.render_text()

    assert aov.response.supported_claims[0].metric_state is MetricState.UNDEFINED
    assert aov.response.supported_claims[0].value is None
    assert aov.response.supported_claims[0].undefined_reason == "orders_equals_zero"
    assert metadata_store.schema_version() == SCHEMA_VERSION


def _intent(
    source: Path,
    question: str,
    *,
    question_class=PublicQuestionClass.REVENUE_CHANGE,
    claim_intents=(PublicClaimIntent(),),
) -> PublicAnalysisIntent:
    return PublicAnalysisIntent(
        question_class=question_class,
        metric_id="revenue_change",
        baseline_period=_q3(),
        comparison_period=_q4(),
        source=PublicSourceSelection(source, SourceType.CSV),
        original_question_text=question,
        claim_intents=claim_intents,
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
