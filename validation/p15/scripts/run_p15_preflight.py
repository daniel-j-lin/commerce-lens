#!/usr/bin/env python3
"""Run non-human P15 product preflight checks against the frozen datasets."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path

from commerce_lens.contracts.common import PeriodDefinition

ROOT = Path(__file__).parents[3]
DATA = ROOT / "validation" / "p15" / "data"
RUNNER = ROOT / "skills" / "commerce-lens" / "scripts" / "run_public_analysis.py"
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
DATASET_A_COVERAGE_CONTEXT = {
    "all_pages_included": True,
    "all_records_included": True,
    "paid_included": True,
    "cancelled_excluded": True,
    "no_additional_hidden_filters": True,
    # Keep the source-owner representation from task-s1.md. The generic runner
    # must normalize this explicit UTC form rather than requiring the
    # participant to restate it in canonical ISO syntax.
    "data_availability_cutoff": "2026-04-01 00:00 UTC",
}


def _period_from_payload(payload: dict) -> PeriodDefinition:
    return PeriodDefinition(
        period_id=payload["period_id"],
        label=payload["label"],
        start_date=date.fromisoformat(payload["start_date"]),
        end_date=date.fromisoformat(payload["end_date"]),
        date_convention_ref=payload["date_convention_ref"],
    )


def _base_args(
    source: Path, *, question_class: str = "revenue_change", metric: str = "revenue_change",
    result_period_role: str | None = None, original_question: str = "How did revenue change between the two periods?",
) -> list[str]:
    args = [
        sys.executable, str(RUNNER), "--source", str(source), "--source-type", "csv",
        "--question-class", question_class, "--metric", metric,
        "--baseline-label", "Q1 2025", "--baseline-start", "2025-01-01",
        "--baseline-end", "2025-03-31", "--comparison-label", "Q1 2026",
        "--comparison-start", "2026-01-01", "--comparison-end", "2026-03-31",
        "--original-question", original_question,
        "--mapping-json", json.dumps(MAPPING, sort_keys=True),
    ]
    if result_period_role is not None:
        args.extend(["--result-period-role", result_period_role])
    return args


def _run(args: list[str]) -> tuple[int, dict, str]:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    payload = json.loads(result.stdout) if result.stdout.strip() else {}
    return result.returncode, payload, result.stderr.strip()


def _assert_summary(payload: dict) -> None:
    if payload.get("run_status") != "completed":
        raise AssertionError(f"Dataset A did not complete: {payload}")
    response = payload.get("response", {})
    if not response.get("coverage_provenance"):
        raise AssertionError("Dataset A coverage provenance missing")
    claims = response.get("supported_claims", [])
    if len(claims) != 1 or claims[0].get("value") not in ("-1200.00", -1200.0):
        raise AssertionError(f"Dataset A Revenue Change oracle mismatch: {payload}")
    provenance = response["coverage_provenance"][0]
    if provenance.get("authority_type") != "USER_DECLARED":
        raise AssertionError(f"Dataset A coverage authority changed: {provenance}")
    summary = payload.get("validated_results_summary", [])
    observed = {(item.get("metric_ref"), item.get("period_role")): item.get("actual_value") for item in summary}
    expected = {
        ("revenue", "baseline"): "12000.00",
        ("revenue", "comparison"): "10800.00",
        ("revenue_change", "baseline_and_comparison"): "-1200.00",
    }
    for key, value in expected.items():
        actual = observed.get(key)
        if str(actual) != str(value):
            raise AssertionError(f"Dataset A validated result mismatch for {key}: {actual!r} != {value!r}")


def _assert_single_metric(payload: dict, metric: str, expected: dict[str, str | int]) -> None:
    if payload.get("run_status") != "completed":
        raise AssertionError(f"Dataset A {metric} request did not complete: {payload}")
    summary = payload.get("validated_results_summary", [])
    observed = {(item.get("metric_ref"), item.get("period_role")): item.get("actual_value") for item in summary}
    for period_role, value in expected.items():
        actual = observed.get((metric, period_role))
        if str(actual) != str(value):
            raise AssertionError(f"Dataset A {metric} mismatch for {period_role}: {actual!r} != {value!r}")
    provenance = payload.get("response", {}).get("coverage_provenance", [])
    if not provenance or provenance[0].get("authority_type") != "USER_DECLARED":
        raise AssertionError(f"Dataset A {metric} coverage authority changed: {provenance}")


def main() -> int:
    a_source = DATA / "P15-A-governed-marketplace.csv"
    b_source = DATA / "P15-B-coverage-unknown.csv"
    with tempfile.TemporaryDirectory(prefix="p15_preflight_") as temp:
        temp_root = Path(temp)
        revenue_args = _base_args(a_source)
        prepare_code, preview, prepare_error = _run(
            revenue_args + [
                "--prepare-coverage",
                "--coverage-context-json",
                json.dumps(DATASET_A_COVERAGE_CONTEXT, sort_keys=True),
            ]
        )
        if prepare_code != 0 or preview.get("status") != "coverage_confirmation_ready":
            raise AssertionError(f"Dataset A coverage preparation failed: {prepare_error or preview}")
        if preview.get("confirmation_prompt") != "請確認以上資訊是否正確。":
            raise AssertionError(f"Dataset A did not render the consolidated confirmation prompt: {preview}")
        if preview.get("missing_facts"):
            raise AssertionError(f"Dataset A still has missing coverage facts: {preview}")
        confirmation_text = preview.get("confirmation_text", "")
        if confirmation_text.count("Coverage proposal:") != 1:
            raise AssertionError(f"Dataset A proposal was not rendered once: {preview}")
        if confirmation_text.count("請確認以上資訊是否正確。") != 1:
            raise AssertionError(f"Dataset A confirmation prompt was duplicated: {preview}")
        if "yes/no" in confirmation_text.lower() or "unknown" in confirmation_text.lower():
            raise AssertionError(f"Dataset A rendered field questions instead of a proposal: {preview}")
        if "Data available through: 2026-04-01T00:00:00Z." not in confirmation_text:
            raise AssertionError(f"Dataset A cutoff was not rendered canonically: {preview}")
        if "Authority: USER_DECLARED" not in confirmation_text:
            raise AssertionError(f"Dataset A authority disclosure was omitted: {preview}")
        if "not independently verified by CommerceLens" not in confirmation_text:
            raise AssertionError(f"Dataset A verification disclosure was omitted: {preview}")
        if "確認完整性" in confirmation_text or "確認完整匯出" in confirmation_text:
            raise AssertionError(f"Dataset A rendered a special confirmation phrase: {preview}")
        if "data-availability cutoff (UTC)" in confirmation_text:
            raise AssertionError(f"Dataset A cutoff was re-requested: {preview}")

        from commerce_lens.skill.coverage_intake import confirm_declaration

        declaration = confirm_declaration(
            preview["declaration_template"], response="Confirm",
            proposal_fingerprint=preview["proposal_fingerprint"],
            requested_periods=(
                _period_from_payload(preview["confirmation_summary"]["requested_periods"][0]),
                _period_from_payload(preview["confirmation_summary"]["requested_periods"][1]),
            ),
            declaration_id="p15_preflight_declaration",
            recorded_at=datetime.now(UTC),
            data_availability_cutoff=datetime(2026, 4, 1, tzinfo=UTC),
            source_basis_detail=(
                "I reviewed the export date range, population/status filters, all pages "
                "and export completion status against this declaration."
            ),
        )
        declaration_path = temp_root / "coverage.json"
        declaration_path.write_text(declaration.model_dump_json(), encoding="utf-8")
        a_args = revenue_args + ["--coverage-declaration", str(declaration_path)]

        a_code, a_payload, a_error = _run(a_args)
        if a_code != 0:
            raise AssertionError(f"Dataset A temporary runner failed: {a_error or a_payload}")
        _assert_summary(a_payload)

        orders_code, orders_payload, orders_error = _run(
            _base_args(
                a_source, question_class="single_period_metric", metric="orders",
                result_period_role="comparison", original_question="What were the orders in the two periods?",
            ) + ["--coverage-declaration", str(declaration_path)]
        )
        if orders_code != 0:
            raise AssertionError(f"Dataset A Orders runner failed: {orders_error or orders_payload}")
        _assert_single_metric(orders_payload, "orders", {"baseline": 48, "comparison": 45})

        aov_code, aov_payload, aov_error = _run(
            _base_args(
                a_source, question_class="single_period_metric", metric="aov",
                result_period_role="comparison", original_question="What was AOV in the two periods?",
            ) + ["--coverage-declaration", str(declaration_path)]
        )
        if aov_code != 0:
            raise AssertionError(f"Dataset AOV runner failed: {aov_error or aov_payload}")
        _assert_single_metric(aov_payload, "aov", {"baseline": "250.00", "comparison": "240.00"})

        retained_root = temp_root / "retained"
        retained_code, retained_payload, retained_error = _run(
            a_args + ["--retention-root", str(retained_root)]
        )
        if retained_code != 0 or retained_payload.get("retention_status") != "retained_complete":
            raise AssertionError(f"Dataset A retained dry run failed: {retained_error or retained_payload}")
        retained_run_id = retained_payload.get("retained_run_id")
        if not retained_run_id:
            raise AssertionError("Dataset A retained run ID missing")
        for operation in (("--list-retained",), ("--inspect-run", retained_run_id), ("--verify-run", retained_run_id)):
            code, payload, error = _run([
                sys.executable, str(RUNNER), "--retention-root", str(retained_root), *operation,
            ])
            if code != 0:
                raise AssertionError(f"retention operation {operation} failed: {error or payload}")

        b_code, b_payload, b_error = _run(_base_args(b_source))
        b_response = b_payload.get("response", {})
        if b_code != 0 or b_payload.get("run_status") != "blocked":
            raise AssertionError(f"Dataset B dry run did not block: {b_error or b_payload}")
        if b_response.get("supported_claims"):
            raise AssertionError(f"Dataset B produced a material claim: {b_payload}")
        if b_response.get("coverage_provenance"):
            raise AssertionError(f"Dataset B silently created coverage authority: {b_payload}")
        if not any("global source authority" in item for item in b_response.get("limitations", [])):
            raise AssertionError(f"Dataset B did not expose missing source authority: {b_payload}")

        report = {
            "dataset_a_temporary": {
                "status": "passed",
                "exit_code": a_code,
                "run_status": a_payload.get("run_status"),
                "supported_claims": len(a_payload["response"].get("supported_claims", [])),
                "coverage_authority": a_payload["response"]["coverage_provenance"][0]["authority_type"],
                "validated_results_summary_count": len(a_payload.get("validated_results_summary", [])),
                "orders_request_exit_code": orders_code,
                "aov_request_exit_code": aov_code,
                "oracle": {
                    "baseline_revenue": "12000.00",
                    "comparison_revenue": "10800.00",
                    "revenue_change": "-1200.00",
                    "baseline_orders": 48,
                    "comparison_orders": 45,
                    "baseline_aov": "250.00",
                    "comparison_aov": "240.00",
                },
            },
            "dataset_a_retained": {
                "status": "passed",
                "retention_status": retained_payload.get("retention_status"),
                "run_id_present": bool(retained_run_id),
                "list_inspect_verify": "passed",
            },
            "dataset_b_without_declaration": {
                "status": "passed",
                "exit_code": b_code,
                "run_status": b_payload.get("run_status"),
                "supported_claims": len(b_response.get("supported_claims", [])),
                "coverage_provenance": len(b_response.get("coverage_provenance", [])),
                "missing_source_authority_observed": True,
            },
        }
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
