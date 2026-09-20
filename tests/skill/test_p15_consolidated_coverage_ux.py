from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from commerce_lens.contracts.common import PeriodDefinition, SourceType
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.skill.integration import (
    PublicAnalysisIntent,
    PublicCoverageContext,
    PublicSourceSelection,
    confirm_public_coverage,
    prepare_public_coverage,
    render_coverage_confirmation,
    run_public_analysis,
)
from commerce_lens.skill.schema_mapping import confirmed_mapping_from_source_to_canonical


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "validation" / "p15" / "data"
MAPPING = {
    "Order Number": "order_id",
    "Line Item ID": "order_line_id",
    "Order Date": "order_date",
    "SKU": "product_id",
    "Quantity": "quantity",
    "Net Merchandise Sales": "line_revenue",
    "Currency": "currency",
    "Order Status": "eligibility_status",
}
CONTEXT = PublicCoverageContext(
    all_pages_included=True,
    all_records_included=True,
    paid_included=True,
    cancelled_excluded=True,
    no_additional_hidden_filters=True,
    data_availability_cutoff=datetime(2026, 4, 1, tzinfo=UTC),
)


def _intent(source: Path) -> PublicAnalysisIntent:
    return PublicAnalysisIntent(
        question_class="revenue_change",
        metric_id="revenue_change",
        baseline_period=PeriodDefinition(
            period_id="baseline", label="Q1 2025", start_date=datetime(2025, 1, 1).date(),
            end_date=datetime(2025, 3, 31).date(), date_convention_ref="order_date_utc",
        ),
        comparison_period=PeriodDefinition(
            period_id="comparison", label="Q1 2026", start_date=datetime(2026, 1, 1).date(),
            end_date=datetime(2026, 3, 31).date(), date_convention_ref="order_date_utc",
        ),
        source=PublicSourceSelection(source, SourceType.CSV),
    )


def _mapped(intent: PublicAnalysisIntent) -> PublicAnalysisIntent:
    return replace(
        intent,
        source=replace(
            intent.source,
            mapping=confirmed_mapping_from_source_to_canonical(MAPPING),
            mapping_mode="confirmed_source_to_canonical_mapping",
        ),
    )


def test_dataset_a_mapping_confirmation_yields_one_complete_consolidated_proposal(tmp_path):
    intent = _intent(DATA / "P15-A-governed-marketplace.csv")
    mapping_response = run_public_analysis(
        intent,
        artifact_store=ArtifactStore(tmp_path / "mapping-artifacts"),
        metadata_store=MetadataStore(tmp_path / "mapping-metadata.sqlite"),
    )
    assert mapping_response.response.mapping_proposals

    mapped = _mapped(intent)
    prepared = prepare_public_coverage(
        mapped, artifact_store=ArtifactStore(tmp_path / "coverage-artifacts"),
        coverage_context=CONTEXT,
    )

    assert prepared["status"] == "coverage_confirmation_ready"
    assert prepared["confirmation_prompt"] == "請確認以上資訊是否正確。"
    assert prepared["missing_facts"] == ()
    facts = prepared["coverage_facts"]
    assert facts["all_pages_included"] is True
    assert facts["all_records_included"] is True
    assert facts["status_scope"]["paid"]["included"] is True
    assert facts["status_scope"]["cancelled"]["excluded"] is True
    assert facts["no_additional_hidden_filters"] is True
    assert prepared["coverage_proposal"]["data_availability_cutoff"] == "2026-04-01T00:00:00Z"
    assert prepared["disclosure"].startswith("Coverage is based on a user-provided declaration")
    assert "確認完整性" not in str(prepared)
    assert "確認完整匯出" not in str(prepared)
    text = prepared["confirmation_text"]
    assert text == render_coverage_confirmation(prepared)
    assert text.count("Coverage proposal:") == 1
    assert text.count("請確認以上資訊是否正確。") == 1
    assert "all export pages and all in-scope records included" in text
    assert "paid orders are included; cancelled orders are excluded" in text
    assert "Authority: USER_DECLARED" in text
    assert "not independently verified" in text
    assert "data-availability cutoff" not in text
    assert "yes/no" not in text.lower()
    assert "unknown" not in text.lower()
    assert "?" not in text

    declaration = confirm_public_coverage(
        mapped,
        prepared,
        response="確認",
        recorded_at=datetime.now(UTC),
        declaration_id="p15-a-plain-confirm",
    )
    assert declaration.authority_type == "USER_DECLARED"

    outcome = run_public_analysis(
        mapped,
        artifact_store=ArtifactStore(tmp_path / "run-artifacts"),
        metadata_store=MetadataStore(tmp_path / "run-metadata.sqlite"),
        coverage_declarations=(declaration,),
    )
    assert outcome.response.supported_claims[0].value == Decimal("-1200.00")


def test_legacy_cutoff_argument_is_merged_into_structured_context(tmp_path):
    mapped = _mapped(_intent(DATA / "P15-A-governed-marketplace.csv"))
    context_without_cutoff = replace(CONTEXT, data_availability_cutoff=None)

    prepared = prepare_public_coverage(
        mapped,
        artifact_store=ArtifactStore(tmp_path / "artifacts"),
        coverage_context=context_without_cutoff,
        data_availability_cutoff=datetime(2026, 4, 1, tzinfo=UTC),
    )

    assert prepared["status"] == "coverage_confirmation_ready"
    assert prepared["missing_facts"] == ()
    assert prepared["coverage_proposal"]["data_availability_cutoff"] == "2026-04-01T00:00:00Z"
    assert "Data available through: 2026-04-01T00:00:00Z." in prepared["confirmation_text"]
    assert prepared["confirmation_text"].endswith("請確認以上資訊是否正確。")


def test_equivalent_offset_cutoff_is_canonicalized_to_utc(tmp_path):
    mapped = _mapped(_intent(DATA / "P15-A-governed-marketplace.csv"))
    equivalent_cutoff = datetime(2026, 4, 1, 8, tzinfo=timezone(timedelta(hours=8)))

    prepared = prepare_public_coverage(
        mapped,
        artifact_store=ArtifactStore(tmp_path / "artifacts"),
        coverage_context=replace(CONTEXT, data_availability_cutoff=equivalent_cutoff),
    )

    assert prepared["coverage_facts"]["data_availability_cutoff"] == "2026-04-01T00:00:00Z"
    assert prepared["coverage_proposal"]["data_availability_cutoff"] == "2026-04-01T00:00:00Z"


def test_ambiguous_naive_cutoff_fails_closed_before_proposal(tmp_path):
    mapped = _mapped(_intent(DATA / "P15-A-governed-marketplace.csv"))
    try:
        context = replace(CONTEXT, data_availability_cutoff=datetime(2026, 4, 1))
    except ValueError as exc:
        assert "explicit timezone" in str(exc)
    else:
        raise AssertionError("naive cutoff unexpectedly created a coverage context")


def test_conflicting_cutoff_inputs_fail_closed(tmp_path):
    mapped = _mapped(_intent(DATA / "P15-A-governed-marketplace.csv"))
    try:
        prepare_public_coverage(
            mapped,
            artifact_store=ArtifactStore(tmp_path / "artifacts"),
            coverage_context=CONTEXT,
            data_availability_cutoff=datetime(2026, 4, 2, tzinfo=UTC),
        )
    except ValueError as exc:
        assert "conflicting coverage context field" in str(exc)
    else:
        raise AssertionError("conflicting cutoff inputs unexpectedly produced a proposal")


def test_dataset_b_without_context_stays_fail_closed_and_dates_do_not_authorize(tmp_path):
    mapped = _mapped(_intent(DATA / "P15-B-coverage-unknown.csv"))
    artifacts = ArtifactStore(tmp_path / "artifacts")
    prepared = prepare_public_coverage(mapped, artifact_store=artifacts)

    assert prepared["status"] == "coverage_confirmation_required"
    assert prepared["coverage_proposal"] is None
    assert prepared["missing_facts"]
    assert "確認完整性" not in str(prepared)
    assert "確認完整匯出" not in str(prepared)
    assert prepared["confirmation_text"].startswith("需要補充以下 coverage 資料：")
    assert "all export pages included" in prepared["confirmation_text"]
    assert "data-availability cutoff (UTC)" in prepared["confirmation_text"]
    assert "?" not in prepared["confirmation_text"]

    # A cutoff or the observed/requested dates alone must not manufacture the
    # all-pages/all-record completeness facts.
    dates_only = prepare_public_coverage(
        mapped,
        artifact_store=ArtifactStore(tmp_path / "dates-only-artifacts"),
        data_availability_cutoff=datetime(2026, 4, 1, tzinfo=UTC),
    )
    assert dates_only["coverage_proposal"] is None
    assert dates_only["status"] == "coverage_confirmation_required"

    outcome = run_public_analysis(
        mapped,
        artifact_store=ArtifactStore(tmp_path / "run-artifacts"),
        metadata_store=MetadataStore(tmp_path / "run-metadata.sqlite"),
    )
    assert outcome.response.blocked is True
    assert outcome.response.supported_claims == ()


def test_missing_cutoff_is_the_only_missing_fact_in_the_rendered_prompt(tmp_path):
    mapped = _mapped(_intent(DATA / "P15-A-governed-marketplace.csv"))
    prepared = prepare_public_coverage(
        mapped,
        artifact_store=ArtifactStore(tmp_path / "artifacts"),
        coverage_context=PublicCoverageContext(
            all_pages_included=True,
            all_records_included=True,
            paid_included=True,
            cancelled_excluded=True,
            no_additional_hidden_filters=True,
        ),
    )

    assert prepared["missing_facts"] == ("data_availability_cutoff",)
    assert prepared["confirmation_text"] == "需要補充：data-availability cutoff (UTC)。"
    assert "all export pages" not in prepared["confirmation_text"]
    assert "?" not in prepared["confirmation_text"]


def test_temporary_and_retained_preparation_share_the_same_consolidated_ux(tmp_path):
    from commerce_lens.persistence.retention import RetainedRunSession

    mapped = _mapped(_intent(DATA / "P15-A-governed-marketplace.csv"))
    temporary = prepare_public_coverage(
        mapped,
        artifact_store=ArtifactStore(tmp_path / "temporary-artifacts"),
        coverage_context=CONTEXT,
    )
    session = RetainedRunSession.begin(tmp_path / "retained")
    retained = prepare_public_coverage(
        mapped,
        artifact_store=session.artifact_store,
        coverage_context=CONTEXT,
    )

    for prepared in (temporary, retained):
        assert prepared["status"] == "coverage_confirmation_ready"
        assert prepared["confirmation_prompt"] == "請確認以上資訊是否正確。"
        assert prepared["coverage_facts"] == temporary["coverage_facts"]
        assert prepared["confirmation_text"] == temporary["confirmation_text"]
        assert "確認完整性" not in str(prepared)
        assert "確認完整匯出" not in str(prepared)
