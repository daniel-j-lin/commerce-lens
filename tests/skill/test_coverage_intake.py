"""F1-B owner acceptance cases, with an explicit post-period test clock."""
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys

import pytest

from commerce_lens.contracts.common import ClaimState, MetricState, ScopeDefinition, ScopeFilter, SourceType
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.skill import coverage_intake as intake
from commerce_lens.skill.integration import (
    PublicCoverageContext, prepare_public_coverage, run_public_analysis, PublicSourceSelection,
)
from commerce_lens.skill.schema_mapping import confirmed_mapping_from_source_to_canonical
from tests.skill.test_public_authority_regression import _intent, _args
from tests.public_fixture_authority import load_public_runner

NOW = datetime(2027, 1, 3, tzinfo=UTC)
CUTOFF = datetime(2027, 1, 1, tzinfo=UTC)
BASIS = intake.SOURCE_BASIS_ASSERTION
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def case(tmp_path, monkeypatch):
    monkeypatch.setattr(intake, "utc_now", lambda: NOW)
    source = tmp_path / "orders.csv"
    source.write_text("order_id,order_line_id,order_date,product_id,quantity,line_revenue,currency,eligibility_status\n"
                      "o1,l1,2026-07-15,p1,1,120.00,USD,paid\n")
    intent = _intent(source)
    artifacts = ArtifactStore(tmp_path / "artifacts")
    metadata = MetadataStore(tmp_path / "metadata.sqlite")
    template = prepare_public_coverage(intent, artifact_store=artifacts)["declaration_template"]
    declaration = intake.confirm_declaration(
        template, response="Confirm", recorded_at=NOW, declaration_id="decl-1",
        proposal_fingerprint=intake.coverage_proposal_fingerprint(
            template, requested_periods=(intent.baseline_period, intent.comparison_period),
            data_availability_cutoff=CUTOFF,
        ),
        requested_periods=(intent.baseline_period, intent.comparison_period),
        data_availability_cutoff=CUTOFF, source_basis_detail=BASIS,
    ).model_dump(mode="json")
    return intent, artifacts, metadata, declaration


def run(case, declaration="default"):
    intent, artifacts, metadata, original = case
    args = {} if declaration is None else {"coverage_declarations": original if declaration == "default" else declaration}
    return run_public_analysis(intent, artifact_store=artifacts, metadata_store=metadata, **args)


def blocked(outcome):
    assert not outcome.response.supported_claims
    assert not outcome.claim_decisions
    assert outcome.response.blocked or outcome.response.clarification_required


def test_valid_user_declared_chain_and_traceability(case):
    outcome = run(case)
    claim, = outcome.response.supported_claims
    assert str(claim.value) == "-120.00"
    assert claim.claim_state is ClaimState.ADMISSIBLE
    assert intake.DISCLOSURE in outcome.response.render_text()
    provenance, = outcome.response.coverage_provenance
    assert provenance["authority_type"] == "USER_DECLARED"
    assert provenance["declaration_id"] == "decl-1"
    assert provenance["policy_version"] == intake.POLICY_VERSION
    saved = case[1].safe_path(provenance["artifact"]["path"])
    assert json.loads(saved.read_text()) == case[3]
    assert outcome.analysis_result.run_status == "completed"


@pytest.mark.parametrize("metric,expected,state", [
    ("revenue", "0.00", MetricState.VALID), ("orders", "0", MetricState.VALID),
    ("aov", "None", MetricState.UNDEFINED),
])
def test_complete_zero(case, metric, expected, state):
    intent, artifacts, metadata, declaration = case
    intent = replace(intent, question_class="single_period_metric", metric_id=metric, result_period_role="comparison")
    outcome = run((intent, artifacts, metadata, declaration))
    claim, = outcome.response.supported_claims
    assert claim.value == (None if expected == "None" else Decimal(expected))
    assert claim.metric_state is state
    if metric == "aov":
        assert claim.undefined_reason == "orders_equals_zero"


def test_missing_declaration_cannot_turn_absent_rows_into_zero(case):
    blocked(run(case, None))


@pytest.mark.parametrize("field,value", [
    ("completeness_assertion", "probably complete"),
    ("completeness_assertion", "I think so"),
    ("completeness_assertion", "all recent orders"),
    ("completeness_assertion", "exported from Shopify"),
    ("completeness_assertion", "How did Revenue change from Q3 to Q4?"),
    ("dataset_id", "ds_wrong"), ("content_fingerprint", "0" * 64),
    ("selected_sheet", "wrong"), ("selected_table", "wrong"),
    ("source_type", "excel_xlsx"), ("source_type", "sqlite"),
    ("covered_end", "2026-12-30"), ("covered_start", "2026-07-02"),
    ("date_convention_ref", "order_date_local"),
    ("data_availability_cutoff", "2026-12-31T23:59:59Z"),
    ("data_availability_cutoff", "2027-01-04T00:00:00Z"),
    ("recorded_at", "2027-01-04T00:00:00Z"),
    ("recorded_at", "2027-01-03T00:00:00"),
    ("filters_status", "unknown"), ("filters_status", "explicit_filters"),
    ("context_fingerprint", "0" * 64),
    ("authority_type", "SOURCE_DECLARED"), ("authority_type", "EXTERNALLY_VERIFIED"),
    ("authority_type", "TEST_FIXTURE"), ("authority_type", None),
    ("policy_version", "future_policy"),
    ("source_basis_detail", "I think all pages were exported"),
    ("extracted_at", "2026-12-30T00:00:00Z"),
    ("extracted_at", "2027-01-04T00:00:00Z"),
])
def test_invalid_external_declarations_fail_closed(case, field, value):
    blocked(run(case, {**case[3], field: value}))


def test_changed_bytes(case):
    case[0].source.source_path.write_text(case[0].source.source_path.read_text().replace("120.00", "121.00"))
    blocked(run(case))


def test_filename_is_human_identification_only(case):
    renamed = case[0].source.source_path.with_name("renamed.csv")
    renamed.write_bytes(case[0].source.source_path.read_bytes())
    intent = replace(case[0], source=replace(case[0].source, source_path=renamed))
    assert run((intent, *case[1:])).response.supported_claims


def test_request_expanded_one_day(case):
    intent = replace(case[0], comparison_period=case[0].comparison_period.model_copy(update={"end_date": date(2027, 1, 1)}))
    blocked(run((intent, *case[1:])))


def test_open_period_actual_clock(case, monkeypatch):
    monkeypatch.setattr(intake, "utc_now", lambda: datetime(2026, 9, 18, tzinfo=UTC))
    blocked(run(case))


def test_min_max_never_establish_coverage(case):
    path = case[0].source.source_path
    path.write_text(path.read_text().replace("2026-07-15", "2026-07-01") + "o2,l2,2026-12-31,p1,1,1.00,USD,paid\n")
    blocked(run(case, None))


def test_explicit_scope_and_filters(case):
    intent, artifacts, metadata, declaration = case
    scope = ScopeDefinition(scope_id="USD", filters=(ScopeFilter(field="currency", operator="equals", value="USD"),))
    intent = replace(intent, scope=scope)
    declaration = {**declaration, "scope": scope.model_dump(mode="json"), "filters_status": "explicit_filters"}
    assert run((intent, artifacts, metadata, declaration)).response.supported_claims


def test_filters_omit_required_population(case):
    scope = ScopeDefinition(scope_id="only_cancelled", filters=(ScopeFilter(field="eligibility_status", operator="equals", value="Excluded"),))
    blocked(run(case, {**case[3], "scope": scope.model_dump(mode="json"), "filters_status": "explicit_filters"}))


def test_population_differs(case):
    blocked(run(case, {**case[3], "scope": {**case[3]["scope"], "population_ref": "other"}}))


def test_mapping_change_cannot_reuse_declaration(case):
    from commerce_lens.canonical.mapping import identity_mapping
    headers = tuple(case[0].source.source_path.read_text().splitlines()[0].split(","))
    mapping = identity_mapping(headers, require_eligibility=True).model_copy(update={"mapping_id": "changed-context"})
    intent = replace(case[0], source=replace(case[0].source, mapping=mapping, mapping_mode="confirmed_source_to_canonical_mapping"))
    blocked(run((intent, *case[1:])))


def test_conflicts_in_one_intake(case):
    blocked(run(case, [case[3], {**case[3], "declaration_id": "decl-2", "covered_start": "2026-06-01"}]))


def test_conflicts_with_retained_declaration(case):
    assert run(case).response.supported_claims
    blocked(run(case, {**case[3], "declaration_id": "decl-2", "covered_start": "2026-06-01"}))


def test_duplicate_identical_declarations_are_deterministic(case):
    assert run(case, [case[3], case[3]]).response.supported_claims


def test_missing_provenance_and_extra_bypass_keys(case):
    declaration = dict(case[3]); del declaration["authority_type"]
    blocked(run(case, declaration))
    blocked(run(case, {**case[3], "complete": True}))
    blocked(run(case, {**case[3], "satisfies_requirement_ids": ["req_revenue_change"]}))


def test_external_and_trusted_boundary_cannot_mix(case):
    intent, artifacts, metadata, declaration = case
    blocked(run_public_analysis(intent, artifact_store=artifacts, metadata_store=metadata,
                                coverage_declarations=declaration, available_evidence=()))


def test_coverage_only_satisfies_source_requirement(case):
    declaration = intake.CoverageDeclaration.model_validate(case[3])
    evidence, _ = intake.project_coverage(declaration, "artifact")
    assert evidence.satisfies_requirement_ids == ("req_global",)


@pytest.mark.parametrize("change", ["currency", "eligibility", "money"])
def test_valid_coverage_cannot_override_data_quality(case, change):
    intent, artifacts, metadata, declaration = case
    path = intent.source.source_path
    text = path.read_text()
    if change == "currency": text = text.replace(",USD,", ",,")
    if change == "eligibility": text = text.replace("paid", "unknown")
    if change == "money": text = text.replace("120.00", "unclear")
    path.write_text(text)
    template = prepare_public_coverage(intent, artifact_store=artifacts)["declaration_template"]
    declaration.update({key: template[key] for key in ("dataset_id", "content_fingerprint", "context_fingerprint")})
    blocked(run((intent, artifacts, metadata, declaration)))


@pytest.mark.parametrize("answer", ["", "probably", "I think so", "should be complete", "Correct", "I don't know"])
def test_only_explicit_confirmation_records_attestation(case, answer):
    with pytest.raises(ValueError, match="unconfirmed"):
        intake.confirm_declaration(case[3], response=answer, recorded_at=NOW, declaration_id="x",
                                   requested_periods=(case[0].baseline_period, case[0].comparison_period),
                                   data_availability_cutoff=CUTOFF, source_basis_detail=BASIS)


def test_complete_proposal_is_displayable_and_fingerprinted(case):
    intent, artifacts, _, _ = case
    prepared = prepare_public_coverage(
        intent,
        artifact_store=artifacts,
        coverage_context=PublicCoverageContext(
            all_pages_included=True,
            all_records_included=True,
            paid_included=True,
            cancelled_excluded=True,
            no_additional_hidden_filters=True,
            data_availability_cutoff=CUTOFF,
        ),
    )

    assert prepared["status"] == "coverage_confirmation_ready"
    assert prepared["missing_facts"] == ()
    assert prepared["coverage_proposal"]["data_availability_cutoff"] == "2027-01-01T00:00:00Z"
    assert prepared["confirmation_summary"]["completeness_basis"] == BASIS
    assert prepared["proposal_fingerprint"] == intake.coverage_proposal_fingerprint(
        prepared["declaration_template"],
        requested_periods=(intent.baseline_period, intent.comparison_period),
        data_availability_cutoff=CUTOFF,
    )


def test_missing_cutoff_is_the_only_unresolved_confirmation_fact(case):
    prepared = prepare_public_coverage(case[0], artifact_store=case[1])

    assert prepared["status"] == "coverage_confirmation_required"
    assert prepared["missing_facts"] == (
        "all_pages_included",
        "all_records_included",
        "paid_included",
        "cancelled_excluded",
        "no_additional_hidden_filters",
        "data_availability_cutoff",
    )
    assert prepared["confirmation_summary"]["completeness_basis"] is None


def test_canonical_confirmation_intent_requires_exact_proposal(case):
    intent, artifacts = case[0], case[1]
    template = prepare_public_coverage(intent, artifact_store=artifacts)["declaration_template"]
    periods = (intent.baseline_period, intent.comparison_period)
    fingerprint = intake.coverage_proposal_fingerprint(
        template, requested_periods=periods, data_availability_cutoff=CUTOFF,
    )

    declaration = intake.confirm_declaration(
        template,
        confirmation_intent=intake.CONFIRMED_INTENT,
        proposal_fingerprint=fingerprint,
        requested_periods=periods,
        recorded_at=NOW,
        declaration_id="canonical-intent",
        data_availability_cutoff=CUTOFF,
    )

    assert declaration.authority_type == "USER_DECLARED"
    assert declaration.source_basis_detail == BASIS


@pytest.mark.parametrize("alias", ["確認", "是", "沒問題", "正確", "照這個執行", "Yes", "Looks right"])
def test_natural_language_aliases_must_be_normalized_before_authority(case, alias):
    intent, artifacts = case[0], case[1]
    template = prepare_public_coverage(intent, artifact_store=artifacts)["declaration_template"]
    periods = (intent.baseline_period, intent.comparison_period)
    fingerprint = intake.coverage_proposal_fingerprint(
        template, requested_periods=periods, data_availability_cutoff=CUTOFF,
    )

    with pytest.raises(ValueError, match="normalized"):
        intake.confirm_declaration(
            template,
            response=alias,
            proposal_fingerprint=fingerprint,
            requested_periods=periods,
            recorded_at=NOW,
            declaration_id="alias-not-canonical",
            data_availability_cutoff=CUTOFF,
        )


def test_missing_proposal_fingerprint_cannot_create_authority(case):
    intent, artifacts = case[0], case[1]
    template = prepare_public_coverage(intent, artifact_store=artifacts)["declaration_template"]

    with pytest.raises(ValueError, match="fingerprint"):
        intake.confirm_declaration(
            template,
            response="Confirm",
            requested_periods=(intent.baseline_period, intent.comparison_period),
            recorded_at=NOW,
            declaration_id="no-displayed-proposal",
            data_availability_cutoff=CUTOFF,
        )


def test_changed_displayed_fact_invalidates_confirmation(case):
    intent, artifacts = case[0], case[1]
    template = prepare_public_coverage(intent, artifact_store=artifacts)["declaration_template"]
    periods = (intent.baseline_period, intent.comparison_period)
    fingerprint = intake.coverage_proposal_fingerprint(
        template, requested_periods=periods, data_availability_cutoff=CUTOFF,
    )

    with pytest.raises(ValueError, match="fingerprint"):
        intake.confirm_declaration(
            template,
            confirmation_intent=intake.CONFIRMED_INTENT,
            proposal_fingerprint=fingerprint,
            requested_periods=periods,
            recorded_at=NOW,
            declaration_id="stale-proposal",
            data_availability_cutoff=datetime(2027, 1, 2, tzinfo=UTC),
        )


def test_changed_requested_period_invalidates_confirmation(case):
    intent, artifacts = case[0], case[1]
    template = prepare_public_coverage(intent, artifact_store=artifacts)["declaration_template"]
    periods = (intent.baseline_period, intent.comparison_period)
    fingerprint = intake.coverage_proposal_fingerprint(
        template, requested_periods=periods, data_availability_cutoff=CUTOFF,
    )
    changed_periods = (periods[0].model_copy(update={"label": "Q3 revised"}), periods[1])

    with pytest.raises(ValueError, match="fingerprint"):
        intake.confirm_declaration(
            template,
            confirmation_intent=intake.CONFIRMED_INTENT,
            proposal_fingerprint=fingerprint,
            requested_periods=changed_periods,
            recorded_at=NOW,
            declaration_id="stale-period-proposal",
            data_availability_cutoff=CUTOFF,
        )


def test_correction_intent_does_not_confirm_previous_proposal(case):
    intent, artifacts = case[0], case[1]
    template = prepare_public_coverage(intent, artifact_store=artifacts)["declaration_template"]
    periods = (intent.baseline_period, intent.comparison_period)
    fingerprint = intake.coverage_proposal_fingerprint(
        template, requested_periods=periods, data_availability_cutoff=CUTOFF,
    )

    with pytest.raises(ValueError, match="unconfirmed"):
        intake.confirm_declaration(
            template,
            confirmation_intent="corrected",
            proposal_fingerprint=fingerprint,
            requested_periods=periods,
            recorded_at=NOW,
            declaration_id="corrected",
            data_availability_cutoff=CUTOFF,
        )


def test_bounded_json_and_duplicate_keys(tmp_path):
    path = tmp_path / "declaration.json"
    path.write_text('{"authority_type":"USER_DECLARED","authority_type":"EXTERNALLY_VERIFIED"}')
    with pytest.raises(ValueError, match="duplicate"): intake.load_declarations(path)
    path.write_bytes(b" " * (intake.MAX_DECLARATION_BYTES + 1))
    with pytest.raises(ValueError, match="64 KiB"): intake.load_declarations(path)
    with pytest.raises(ValueError): intake.parse_declarations([])


def test_skill_path_noncanonical_mapping_then_separate_confirmation(case, capsys):
    intent, artifacts, metadata, _ = case
    question = "How did revenue change from Q3 2026 to Q4 2026?"
    headers = ["Order ID", "Order Line ID", "Order Date", "Product ID", "Quantity", "Revenue", "Currency", "Order Status"]
    canonical = intent.source.source_path.read_text().splitlines()[0].split(",")
    path = intent.source.source_path
    path.write_text(",".join(headers) + "\no1,l1,2026-07-15,p1,1,120.00,USD,paid\n"
                    "o2,l2,2026-10-15,p1,1,180.00,USD,paid\n")
    intent = replace(intent, original_question_text=question)
    mapping_response = run_public_analysis(intent, artifact_store=artifacts, metadata_store=metadata)
    assert mapping_response.response.mapping_proposals
    mapping = dict(zip(headers, canonical))
    runner = load_public_runner()
    args = [*_args(path), "--original-question", question, "--mapping-json", json.dumps(mapping)]
    assert runner.main(args) == 0
    no_authority = json.loads(capsys.readouterr().out)
    assert no_authority["run_status"] == "blocked"
    assert runner.main([*args, "--prepare-coverage"]) == 0
    prepared = json.loads(capsys.readouterr().out)
    assert prepared["choices"] == ["Confirm", "Correct", "I don't know"]
    assert prepared["declaration_template"]["completeness_assertion"] is None
    with pytest.raises(ValueError):
        intake.confirm_declaration(prepared["declaration_template"], response="I don't know",
                                   requested_periods=(intent.baseline_period, intent.comparison_period),
                                   recorded_at=NOW, declaration_id="unknown", data_availability_cutoff=CUTOFF,
                                   source_basis_detail=BASIS)
    declaration = intake.confirm_declaration(
        prepared["declaration_template"], response="Confirm", recorded_at=NOW, declaration_id="skill-confirmed",
        proposal_fingerprint=intake.coverage_proposal_fingerprint(
            prepared["declaration_template"],
            requested_periods=(intent.baseline_period, intent.comparison_period),
            data_availability_cutoff=CUTOFF,
        ),
        requested_periods=(intent.baseline_period, intent.comparison_period),
        data_availability_cutoff=CUTOFF, source_basis_detail=BASIS,
    )
    declaration_file = path.with_name("coverage.json")
    declaration_file.write_text(declaration.model_dump_json())
    assert runner.main([*args, "--coverage-declaration", str(declaration_file)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["response"]["supported_claims"][0]["value"] == "60.00"
    assert intake.DISCLOSURE in result["rendered_text"]
    assert result["response"]["coverage_provenance"][0]["declaration_id"] == "skill-confirmed"
    assert result["claim_decisions"]


def test_xlsx_binding_and_execution(case):
    from openpyxl import Workbook
    intent, artifacts, metadata, declaration = case
    path = intent.source.source_path.with_suffix(".xlsx")
    wb = Workbook(); ws = wb.active; ws.title = "Orders"
    for line in intent.source.source_path.read_text().splitlines(): ws.append(line.split(","))
    wb.create_sheet("Other")
    wb.save(path); wb.close()
    intent = replace(intent, source=PublicSourceSelection(path, SourceType.EXCEL_XLSX, selected_sheet="Orders"))
    template = prepare_public_coverage(intent, artifact_store=artifacts)["declaration_template"]
    declaration.update({key: template[key] for key in ("dataset_id", "content_fingerprint", "context_fingerprint", "selected_sheet", "source_type")})
    assert run((intent, artifacts, metadata, declaration)).response.supported_claims
    blocked(run((intent, artifacts, metadata, {**declaration, "selected_sheet": "Other"})))


def test_changed_eligibility_semantics_invalidates_declaration(case, monkeypatch):
    import commerce_lens.skill.integration as integration
    from commerce_lens.canonical.models import EligibilityValueMapping, EligibilityState
    original = integration._canonicalization_request
    def changed(*args):
        context = original(*args)
        return context.model_copy(update={"eligibility_value_mapping": (
            EligibilityValueMapping(source_value="paid", normalized_status=EligibilityState.EXCLUDED),
        )})
    monkeypatch.setattr(integration, "_canonicalization_request", changed)
    blocked(run(case))


def test_extra_requirement_not_satisfied_by_coverage_or_mapping(case, monkeypatch):
    import commerce_lens.skill.integration as integration
    from commerce_lens.contracts.common import EvidenceRequirement
    original = integration._analysis_request
    def extra(*args):
        request = original(*args)
        return request.model_copy(update={"required_evidence": (*request.required_evidence,
            EvidenceRequirement(requirement_id="arbitrary_authority", description="independent extra authority"))})
    monkeypatch.setattr(integration, "_analysis_request", extra)
    outcome = run(case)
    blocked(outcome)
    assert "independent extra authority" in outcome.response.render_text()


@pytest.mark.parametrize("metric,expected", [("revenue", 0), ("orders", 0), ("aov", None)])
def test_complete_zero_with_only_excluded_rows(case, metric, expected):
    intent, artifacts, metadata, declaration = case
    source = intent.source.source_path
    source.write_text(source.read_text().replace("paid", "cancelled"))
    intent = replace(intent, question_class="single_period_metric", metric_id=metric, result_period_role="comparison")
    template = prepare_public_coverage(intent, artifact_store=artifacts)["declaration_template"]
    declaration.update({key: template[key] for key in ("dataset_id", "content_fingerprint", "context_fingerprint")})
    outcome = run((intent, artifacts, metadata, declaration))
    claim, = outcome.response.supported_claims
    assert claim.value == expected


def test_empty_source_without_authority_is_blocked(case):
    source = case[0].source.source_path
    source.write_text(source.read_text().splitlines()[0] + "\n")
    blocked(run(case, None))


def test_reconstructed_model_cannot_spoof_provenance(case):
    model = intake.CoverageDeclaration.model_validate(case[3]).model_copy(update={"authority_type": "TEST_FIXTURE"})
    blocked(run(case, (model,)))


def test_missing_mapping_cannot_be_repaired_by_coverage(case):
    from commerce_lens.canonical.mapping import identity_mapping
    headers = tuple(case[0].source.source_path.read_text().splitlines()[0].split(","))
    mapping = identity_mapping(tuple(h for h in headers if h != "line_revenue"), require_eligibility=True)
    intent = replace(case[0], source=replace(case[0].source, mapping=mapping, mapping_mode="confirmed_source_to_canonical_mapping"))
    # Bind the bad mapping faithfully; this must still fail the separate mapping gate.
    from commerce_lens.skill.integration import _canonicalization_request
    context = _canonicalization_request(intent, case[3]["dataset_id"], headers)
    declaration = {**case[3], "context_fingerprint": intake.context_fingerprint(context)}
    blocked(run((intent, *case[1:3], declaration)))


def test_real_cli_retains_user_provenance_or_cleans_temp(case, tmp_path):
    # Closed 2025 dates exercise the production clock in a fresh Python process.
    intent, artifacts, metadata, declaration = case
    source = intent.source.source_path
    source.write_text(source.read_text().replace("2026", "2025"))
    intent = replace(intent,
        baseline_period=intent.baseline_period.model_copy(update={"start_date": date(2025, 7, 1), "end_date": date(2025, 9, 30)}),
        comparison_period=intent.comparison_period.model_copy(update={"start_date": date(2025, 10, 1), "end_date": date(2025, 12, 31)}))
    template = prepare_public_coverage(intent, artifact_store=artifacts)["declaration_template"]
    declaration = intake.confirm_declaration(template, response="Confirm", declaration_id="production-clock",
        proposal_fingerprint=intake.coverage_proposal_fingerprint(
            template, requested_periods=(intent.baseline_period, intent.comparison_period),
            data_availability_cutoff=datetime(2026, 1, 1, tzinfo=UTC),
        ),
        requested_periods=(intent.baseline_period, intent.comparison_period),
        recorded_at=datetime.now(UTC), data_availability_cutoff=datetime(2026, 1, 1, tzinfo=UTC),
        source_basis_detail=BASIS)
    path = tmp_path / "coverage.json"; path.write_text(declaration.model_dump_json())
    args = [value.replace("2026", "2025") if value.startswith(("2026", "Q3", "Q4")) else value for value in _args(source)]
    args += ["--coverage-declaration", str(path)]
    runner = ROOT / "skills/commerce-lens/scripts/run_public_analysis.py"
    import os
    temp_root = tmp_path / "temp"; temp_root.mkdir()
    for retained in (False, True):
        retained_root = tmp_path / "retained"
        store_args = ["--artifact-store", str(retained_root / "artifacts"), "--metadata-store", str(retained_root / "metadata.sqlite")] if retained else []
        result = subprocess.run([sys.executable, str(runner), *args, *store_args], text=True, capture_output=True,
                                env={**os.environ, "TMPDIR": str(temp_root)})
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["run_status"] == "completed", payload["rendered_text"]
        assert intake.DISCLOSURE in payload["rendered_text"]
        assert not list(temp_root.iterdir())
        record = payload["response"]["coverage_provenance"][0]
        if retained:
            assert (retained_root / "artifacts" / record["artifact"]["path"]).exists()
            assert MetadataStore(retained_root / "metadata.sqlite").list_validation_records()
        else:
            assert not retained_root.exists()
