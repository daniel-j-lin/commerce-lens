from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from commerce_lens.persistence.retention import RetainedRunSession, RetentionError, RetentionStore


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_RUNNER = REPO_ROOT / "tests" / "fixture_authority_runner.py"
RUNNER = REPO_ROOT / "skills" / "commerce-lens" / "scripts" / "run_public_analysis.py"
ORDERS_CSV = REPO_ROOT / "examples" / "public_v0_1" / "orders.csv"


def _analysis_args(*, retention_root: Path | None = None, retain_evidence: bool = False) -> list[str]:
    args = [
        "--source",
        str(ORDERS_CSV),
        "--source-type",
        "csv",
        "--question-class",
        "revenue_change",
        "--metric",
        "revenue_change",
        "--baseline-label",
        "Q3 2026",
        "--baseline-start",
        "2026-07-01",
        "--baseline-end",
        "2026-09-30",
        "--comparison-label",
        "Q4 2026",
        "--comparison-start",
        "2026-10-01",
        "--comparison-end",
        "2026-12-31",
        "--original-question",
        "Please retain the full evidence so I can inspect it later.",
    ]
    if retention_root is not None:
        args.extend(["--retention-root", str(retention_root)])
    if retain_evidence:
        args.append("--retain-evidence")
    return args


def _run_fixture(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(FIXTURE_RUNNER), *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


def _run_operation(*args: str) -> dict | list:
    completed = subprocess.run(
        [sys.executable, str(RUNNER), *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


def test_explicit_natural_language_retention_control_uses_formal_workflow(tmp_path: Path) -> None:
    retention_root = tmp_path / "retained"
    payload = _run_fixture(
        *_analysis_args(retention_root=retention_root, retain_evidence=True),
    )

    assert payload["retention_status"] == "retained_complete"
    assert payload["raw_source_retained"] is True
    assert payload["canonical_data_retained"] is True
    runs = RetentionStore(retention_root).list_runs()
    assert len(runs) == 1
    assert runs[0]["retention_status"] == "retained_complete"


def test_retained_run_is_cross_process_listable_inspectable_and_verifiable(tmp_path: Path) -> None:
    retention_root = tmp_path / "retained"
    payload = _run_fixture(
        *_analysis_args(retention_root=retention_root, retain_evidence=True),
    )
    run_id = payload["retained_run_id"]

    listed = _run_operation("--retention-root", str(retention_root), "--list-retained")
    inspected = _run_operation("--retention-root", str(retention_root), "--inspect-run", run_id)
    verified = _run_operation("--retention-root", str(retention_root), "--verify-run", run_id)

    assert listed[0]["run_id"] == run_id
    assert listed[0]["retention_status"] == "retained_complete"
    assert inspected["retention_status"] == "retained_complete"
    assert inspected["analysis_result_artifact"]
    assert inspected["public_response_artifact"]
    assert verified["valid"] is True
    assert verified["errors"] == []


def test_temporary_default_does_not_create_retained_run(tmp_path: Path) -> None:
    payload = _run_fixture(*_analysis_args())

    assert payload["retention_status"] == "temporary"
    assert payload["raw_source_retained"] is False
    assert not (tmp_path / "retained").exists()


def test_coverage_insufficient_retained_request_stays_blocked(tmp_path: Path) -> None:
    retention_root = tmp_path / "retained"
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            *_analysis_args(retention_root=retention_root, retain_evidence=True),
        ],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["run_status"] == "blocked"
    assert payload["response"]["supported_claims"] == []
    assert payload["response"]["blocked"] is True
    assert payload["retention_status"] == "retained_complete"
    assert RetentionStore(retention_root).verify_run(payload["retained_run_id"])[1] == []


def test_retention_finalization_failure_is_explicit_and_never_claims_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("public_runner_failure_test", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def fail_finalize(self, outcome, *, public_payload, plugin_version=None):
        raise RetentionError("injected finalization failure")

    monkeypatch.setattr(RetainedRunSession, "finalize", fail_finalize)
    retention_root = tmp_path / "retained"
    result = module.main(
        _analysis_args(retention_root=retention_root, retain_evidence=True)
    )
    captured = capsys.readouterr()

    assert result == 1
    assert "Retention failed" in captured.err
    assert "retained_complete" not in captured.out
    assert RetentionStore(retention_root).list_runs()[0]["retention_status"] != "retained_complete"


def test_retained_mode_requires_a_persisted_analysis_result_before_completion(
    tmp_path: Path,
) -> None:
    session = RetainedRunSession.begin(tmp_path / "retained")
    with pytest.raises(RetentionError, match="persisted AnalysisResult"):
        session.finalize(object(), public_payload={})
    assert RetentionStore(tmp_path / "retained").list_runs()[0]["retention_status"] == "retention_failed"
