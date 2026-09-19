"""Independent-review F1/F2 regressions; no production authority fabrication."""
from dataclasses import replace
from datetime import date
from decimal import Decimal
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from commerce_lens.contracts.common import ClaimState, MetricState, PeriodDefinition, SourceType
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.skill.integration import (
    PublicAnalysisIntent, PublicQuestionClass, PublicSourceSelection, run_public_analysis,
)
from tests.public_fixture_authority import load_public_runner, q3_q4_fixture_authority

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "skills/commerce-lens/scripts/run_public_analysis.py"
FIXTURE_RUNNER = ROOT / "tests/fixture_authority_runner.py"


@pytest.fixture
def partial_export(tmp_path):
    source = tmp_path / "partial_export.csv"
    source.write_text(
        "order_id,order_line_id,order_date,product_id,quantity,line_revenue,currency,eligibility_status\n"
        "o1,l1,2026-07-15,p1,1,120.00,USD,paid\n", encoding="utf-8",
    )
    return source


def _intent(source):
    return PublicAnalysisIntent(
        question_class=PublicQuestionClass.REVENUE_CHANGE,
        metric_id="revenue_change",
        baseline_period=PeriodDefinition(
            period_id="baseline", label="Q3 2026", start_date=date(2026, 7, 1),
            end_date=date(2026, 9, 30), date_convention_ref="order_date_utc",
        ),
        comparison_period=PeriodDefinition(
            period_id="comparison", label="Q4 2026", start_date=date(2026, 10, 1),
            end_date=date(2026, 12, 31), date_convention_ref="order_date_utc",
        ),
        source=PublicSourceSelection(source, SourceType.CSV),
    )


@pytest.mark.parametrize("evidence_mode,coverage_mode", [
    ("omitted", "omitted"), ("none", "none"), ("empty", "empty"),
    ("valid", "omitted"), ("omitted", "valid"),
    ("valid", "none"), ("none", "valid"),
    ("valid", "empty"), ("empty", "valid"),
])
def test_partial_export_cannot_self_authorize(tmp_path, partial_export, evidence_mode, coverage_mode):
    intent = _intent(partial_export)
    artifacts = ArtifactStore(tmp_path / "artifacts")
    declared = q3_q4_fixture_authority(intent.source, artifacts)
    kwargs = {}
    for key, mode in (("available_evidence", evidence_mode), ("period_coverage_evidence", coverage_mode)):
        if mode != "omitted":
            kwargs[key] = declared[key] if mode == "valid" else (() if mode == "empty" else None)
    outcome = run_public_analysis(
        intent, artifact_store=artifacts, metadata_store=MetadataStore(tmp_path / "metadata.sqlite"), **kwargs,
    )
    assert outcome.analysis_result is not None  # existing sufficiency gate, not an adapter shortcut
    assert outcome.analysis_result.run_status == "blocked"
    assert outcome.response.supported_claims == ()
    assert outcome.claim_decisions == ()
    if coverage_mode != "valid":
        assert "coverage evidence" in outcome.response.render_text()
    if evidence_mode != "valid":
        assert "required evidence is missing" in outcome.response.render_text()


@pytest.mark.parametrize("metric,value,state", [
    ("revenue_change", Decimal("-120.00"), MetricState.VALID),
    ("revenue", Decimal("0.00"), MetricState.VALID),
    ("orders", 0, MetricState.VALID),
    ("aov", None, MetricState.UNDEFINED),
])
def test_explicit_complete_zero_preserves_positive_metrics(tmp_path, partial_export, metric, value, state):
    intent = _intent(partial_export)
    if metric != "revenue_change":
        intent = replace(intent, question_class=PublicQuestionClass.SINGLE_PERIOD_METRIC,
                         metric_id=metric, result_period_role="comparison")
    artifacts = ArtifactStore(tmp_path / "artifacts")
    outcome = run_public_analysis(
        intent, artifact_store=artifacts, metadata_store=MetadataStore(tmp_path / "metadata.sqlite"),
        **q3_q4_fixture_authority(intent.source, artifacts),
    )
    claim, = outcome.response.supported_claims
    assert claim.value == value
    assert claim.metric_state is state
    assert claim.claim_state is ClaimState.ADMISSIBLE
    if metric == "aov":
        assert claim.undefined_reason == "orders_equals_zero"


@pytest.mark.parametrize("mutation", ["dataset", "convention", "start", "end", "expanded_request", "changed_bytes"])
def test_explicit_coverage_cannot_change_dataset_or_expand_with_request(tmp_path, partial_export, mutation):
    intent = _intent(partial_export)
    artifacts = ArtifactStore(tmp_path / "artifacts")
    authority = q3_q4_fixture_authority(intent.source, artifacts)
    coverage, = authority["period_coverage_evidence"]
    updates = {
        "dataset": {"dataset_ref_id": "ds_other"},
        "convention": {"date_convention_ref": "different_convention"},
        "start": {"observed_start_date": date(2026, 7, 2)},
        "end": {"observed_end_date": date(2026, 12, 30)},
    }
    if mutation in updates:
        authority["period_coverage_evidence"] = (coverage.model_copy(update=updates[mutation]),)
    elif mutation == "expanded_request":
        intent = replace(intent, comparison_period=intent.comparison_period.model_copy(update={
            "start_date": date(2026, 10, 2), "end_date": date(2027, 1, 1),
        }))
    else:
        other = tmp_path / "different_dataset.csv"
        other.write_text(partial_export.read_text().replace("120.00", "121.00"))
        intent = replace(intent, source=PublicSourceSelection(other, SourceType.CSV))
    outcome = run_public_analysis(
        intent, artifact_store=artifacts, metadata_store=MetadataStore(tmp_path / "metadata.sqlite"), **authority,
    )
    assert outcome.analysis_result.run_status == "blocked"
    assert outcome.response.supported_claims == ()
    assert "coverage evidence" in outcome.response.render_text()


def _args(source):
    return [
        "--source", str(source), "--source-type", "csv", "--question-class", "revenue_change",
        "--metric", "revenue_change", "--baseline-label", "Q3 2026", "--baseline-start", "2026-07-01",
        "--baseline-end", "2026-09-30", "--comparison-label", "Q4 2026", "--comparison-start", "2026-10-01",
        "--comparison-end", "2026-12-31",
    ]


@pytest.mark.parametrize("flag", ["--artifact-store", "--metadata-store"])
def test_single_store_rejected_before_runtime_or_analysis(tmp_path, partial_export, monkeypatch, capsys, flag):
    runner = load_public_runner()
    def forbidden_runtime():
        pytest.fail("unpaired stores must fail before loading or invoking analysis")
    monkeypatch.setattr(runner, "_load_runtime", forbidden_runtime)
    with pytest.raises(SystemExit) as exc:
        runner.main([*_args(partial_export), flag, str(tmp_path / "requested")])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "--artifact-store and --metadata-store must be supplied together" in captured.err
    assert captured.out == ""
    assert not (tmp_path / "requested").exists()


@pytest.mark.parametrize("flag", ["--artifact-store", "--metadata-store"])
@pytest.mark.parametrize("empty_value", [False, True])
def test_single_store_cli_exits_nonzero_without_success(tmp_path, partial_export, flag, empty_value):
    value = "" if empty_value else str(tmp_path / "requested")
    result = subprocess.run([sys.executable, str(RUNNER), *_args(partial_export), flag, value],
                            text=True, capture_output=True)
    assert result.returncode == 2
    assert "--artifact-store and --metadata-store must be supplied together" in result.stderr
    assert result.stdout == ""
    assert not (tmp_path / "requested").exists()


@pytest.mark.parametrize("retain", [False, True])
def test_real_cli_without_authority_is_blocked_and_retention_modes_unchanged(tmp_path, partial_export, retain):
    _check_runner_modes(tmp_path, partial_export, retain, fixture_authority=False)


@pytest.mark.parametrize("retain", [False, True])
def test_declared_fixture_runner_positive_and_retention_modes_unchanged(tmp_path, partial_export, retain):
    _check_runner_modes(tmp_path, partial_export, retain, fixture_authority=True)


def _check_runner_modes(tmp_path, source, retain, *, fixture_authority):
    temp = tmp_path / "tmp"
    temp.mkdir()
    artifacts, metadata = tmp_path / "kept" / "artifacts", tmp_path / "kept" / "metadata.sqlite"
    args = _args(source)
    if retain:
        args += ["--artifact-store", str(artifacts), "--metadata-store", str(metadata)]
    command = FIXTURE_RUNNER if fixture_authority else RUNNER
    result = subprocess.run([sys.executable, str(command), *args], text=True, capture_output=True,
                            env={**os.environ, "TMPDIR": str(temp)})
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["run_status"] == ("completed" if fixture_authority else "blocked")
    if fixture_authority:
        assert payload["response"]["supported_claims"][0]["value"] == "-120.00"
    else:
        assert payload["response"]["supported_claims"] == []
        assert "coverage evidence" in payload["rendered_text"]
    assert list(temp.iterdir()) == []
    assert metadata.exists() is retain
    assert artifacts.exists() is retain
    if retain:
        # A new process opens the persisted metadata, rather than trusting stdout IDs.
        code = (
            "import json,sqlite3,sys; "
            "from commerce_lens.persistence.metadata_store import MetadataStore; "
            "c=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro',uri=True); "
            "records=MetadataStore(sys.argv[1]).list_validation_records(); "
            "print(json.dumps({'integrity':c.execute('PRAGMA integrity_check').fetchone()[0],"
            "'refs':sorted({r.validated_result_ref for r in records if r.validated_result_ref})}))"
        )
        reload = subprocess.run(
            [sys.executable, "-c", code, str(metadata)], text=True, capture_output=True, check=True,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        )
        persisted = json.loads(reload.stdout)
        assert persisted["integrity"] == "ok"
        assert set(persisted["refs"]) == {
            item["validated_result_ref"] for item in payload["validated_results_summary"]
        }
        if fixture_authority:
            assert persisted["refs"]  # The retained DB contains the actual run's evidence.
        assert any(artifacts.rglob("*"))
