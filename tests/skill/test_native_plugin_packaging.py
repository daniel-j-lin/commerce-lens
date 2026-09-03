from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
MARKETPLACE = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
PLUGIN_MANIFEST = REPO_ROOT / ".codex-plugin" / "plugin.json"
SKILL = REPO_ROOT / "skills" / "commerce-lens" / "SKILL.md"
RUNNER = REPO_ROOT / "skills" / "commerce-lens" / "scripts" / "run_public_analysis.py"
ORDERS_CSV = REPO_ROOT / "examples" / "public_v0_1" / "orders.csv"
AOV_UNDEFINED_CSV = REPO_ROOT / "examples" / "public_v0_1" / "aov_undefined.csv"


def test_codex_repo_marketplace_exists_parses_and_exposes_commerce_lens() -> None:
    payload = json.loads(MARKETPLACE.read_text(encoding="utf-8"))

    assert payload["name"] == "commerce-lens"
    assert payload["interface"]["displayName"] == "CommerceLens"
    assert len(payload["plugins"]) == 1

    entry = payload["plugins"][0]
    assert entry["name"] == "commerce-lens"
    assert entry["source"] == {"source": "local", "path": "./"}
    assert entry["policy"] == {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }
    assert entry["category"] == "Productivity"


def test_marketplace_source_points_to_existing_plugin_root() -> None:
    entry = json.loads(MARKETPLACE.read_text(encoding="utf-8"))["plugins"][0]
    plugin_root = (MARKETPLACE.parent.parent.parent / entry["source"]["path"]).resolve()

    assert plugin_root == REPO_ROOT
    assert (plugin_root / ".codex-plugin" / "plugin.json").is_file()
    assert (plugin_root / "skills" / "commerce-lens" / "SKILL.md").is_file()


def test_codex_plugin_manifest_exists_parses_and_points_to_skills() -> None:
    payload = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))

    assert payload["name"] == "commerce-lens"
    assert payload["version"] == "0.1.1"
    assert payload["skills"] == "./skills/"
    assert "evidence-governed" in payload["description"].lower()
    assert payload["author"]["name"] == "CommerceLens"
    assert payload["interface"]["displayName"] == "CommerceLens"
    assert payload["interface"]["category"] == "Productivity"
    assert payload["interface"]["capabilities"] == ["Skills"]
    assert "deterministic governed runner" in payload["interface"]["longDescription"]
    assert "apps" not in payload
    assert "mcpServers" not in payload


def test_installable_skill_exists_and_frontmatter_parses() -> None:
    text = SKILL.read_text(encoding="utf-8")
    frontmatter = yaml.safe_load(text.split("---", 2)[1])

    assert frontmatter["name"] == "commerce-lens"
    assert "description" in frontmatter
    assert "e-commerce" in frontmatter["description"]
    assert "Insufficient evidence to conclude why Revenue declined." in text
    assert "Material Metric values must come from the deterministic runner" in text


def test_plugin_manifest_referenced_skill_path_exists() -> None:
    payload = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    skill_root = (PLUGIN_MANIFEST.parent.parent / payload["skills"]).resolve()

    assert skill_root == REPO_ROOT / "skills"
    assert (skill_root / "commerce-lens" / "SKILL.md").is_file()


def test_deterministic_runner_invokes_existing_public_integration() -> None:
    source = RUNNER.read_text(encoding="utf-8")

    assert "run_public_analysis" in source
    assert "PublicAnalysisIntent" in source
    assert "PublicSourceSelection" in source
    assert "line_revenue" not in source
    assert "SUM(" not in source.upper()


def test_no_second_independent_analytical_implementation_is_packaged() -> None:
    marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    plugins = marketplace["plugins"]

    assert len(plugins) == 1
    assert plugins[0]["source"]["path"] == "./"
    assert not (REPO_ROOT / "plugins").exists()


def test_runner_revenue_change_csv_preserves_expected_result() -> None:
    payload = _run_json(
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
        "How did revenue change from Q3 2026 to Q4 2026?",
    )

    rendered = payload["rendered_text"]
    claim = payload["response"]["supported_claims"][0]
    evidence = payload["response"]["evidence_summary"][0]
    validated = {
        (item["metric_ref"], item["period_role"]): item
        for item in payload["validated_results_summary"]
    }

    assert claim["metric_ref"] == "revenue_change"
    assert claim["value"] == "-20.00"
    assert claim["currency"] == "USD"
    assert validated[("revenue", "baseline")]["actual_value"] == "120.00"
    assert validated[("revenue", "comparison")]["actual_value"] == "100.00"
    assert validated[("revenue_change", "baseline_and_comparison")]["actual_value"] == "-20.00"
    assert evidence["source_filename"] == "orders.csv"
    assert payload["run_id"]
    assert "%" not in rendered
    assert "Recommendation" not in rendered


def test_runner_diagnostic_revenue_drop_preserves_bounded_refusal() -> None:
    payload = _run_json(
        "--source",
        str(ORDERS_CSV),
        "--source-type",
        "csv",
        "--question-class",
        "diagnostic_revenue_drop",
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
        "--claim-type",
        "diagnostic",
        "--original-question",
        "Why did revenue drop from Q3 2026 to Q4 2026?",
    )

    rendered = payload["rendered_text"]

    assert "Revenue Change for Q4 2026: -20.00 USD." in rendered
    assert "Insufficient evidence to conclude why Revenue declined." in rendered
    for prohibited in ("promotion", "seasonality", "competition", "traffic", "inventory", "demand"):
        assert prohibited not in rendered.lower()


def test_runner_zero_order_aov_preserves_metric_state_undefined() -> None:
    payload = _run_json(
        "--source",
        str(AOV_UNDEFINED_CSV),
        "--source-type",
        "csv",
        "--question-class",
        "single_period_metric",
        "--metric",
        "aov",
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
        "--result-period-role",
        "comparison",
        "--original-question",
        "What was AOV in Q4 2026?",
    )

    assert "MetricState=Undefined" in payload["rendered_text"]
    assert payload["response"]["supported_claims"][0]["metric_state"] == "Undefined"
    assert payload["response"]["supported_claims"][0]["value"] is None


def test_runner_unsupported_metric_fails_closed() -> None:
    payload = _run_json(
        "--source",
        str(ORDERS_CSV),
        "--source-type",
        "csv",
        "--question-class",
        "revenue_change",
        "--metric",
        "revenue_change_pct",
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
        "What was Revenue Change percentage from Q3 2026 to Q4 2026?",
    )

    assert payload["response"]["supported_claims"] == []
    assert "unsupported Public v0.1 Metric" in payload["rendered_text"]
    assert "%" not in payload["rendered_text"]


def test_runner_unsupported_question_does_not_produce_speculative_output() -> None:
    payload = _run_json(
        "--source",
        str(ORDERS_CSV),
        "--source-type",
        "csv",
        "--question-class",
        "category_ranking",
        "--metric",
        "revenue",
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
        "--result-period-role",
        "comparison",
        "--original-question",
        "Which category drove the change?",
    )

    rendered = payload["rendered_text"]

    assert payload["response"]["supported_claims"] == []
    assert "unsupported question class" in rendered
    assert "category" not in rendered.lower().replace("unsupported question class: category_ranking", "")
    assert "drove" not in rendered.lower()


def _run_json(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(RUNNER), *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)
