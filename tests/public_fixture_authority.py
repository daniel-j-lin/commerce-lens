"""Explicit test declarations for complete synthetic Q3/Q4 2026 exports.

Only test authors call this helper to declare their generated fixture complete.
This is NOT a coverage discovery algorithm or a production trust policy. Dates,
convention, and requirement IDs are fixed independently of analysis requests.
Dataset registration binds the declaration to the selected fixture bytes/sheet.
"""
from datetime import date
import importlib.util
from pathlib import Path

from commerce_lens.canonical.models import PeriodCoverageEvidence
from commerce_lens.contracts.common import AvailableEvidence
from commerce_lens.intake.registry import DatasetRegistry
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.skill.integration import PublicSourceSelection


def q3_q4_fixture_authority(source: PublicSourceSelection, artifact_store: ArtifactStore) -> dict:
    dataset = DatasetRegistry(artifact_store).register_source(
        source.source_path,
        source.source_type,
        selected_sheet=source.selected_sheet,
        selected_table=source.selected_table,
    )
    return {
        "available_evidence": (
            AvailableEvidence(
                evidence_id="synthetic_fixture_declaration",
                description="Test-authored complete Q3/Q4 2026 fixture, not inferred coverage",
                source_ref=dataset.dataset_id,
                satisfies_requirement_ids=("req_global", "req_revenue", "req_orders", "req_aov", "req_revenue_change"),
            ),
        ),
        "period_coverage_evidence": (
            PeriodCoverageEvidence(
                coverage_ref_id="synthetic_q3_q4_2026_complete",
                dataset_ref_id=dataset.dataset_id,
                observed_start_date=date(2026, 7, 1),
                observed_end_date=date(2026, 12, 31),
                date_convention_ref="order_date_utc",
                governing_note_ref="test_author_declares_complete_synthetic_export",
            ),
        ),
    }


def load_public_runner():
    script = Path(__file__).resolve().parents[1] / "skills/commerce-lens/scripts/run_public_analysis.py"
    spec = importlib.util.spec_from_file_location("fixture_public_runner", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_fixture_runner(argv: list[str]) -> int:
    """Run the actual runner with test-only fixture authority at its API boundary.

The CLI has no external authority input yet. Positive runner component tests
explicitly opt into this harness; separate real-CLI tests require blocking.
Sufficiency, execution, validation, and claim decisions are never stubbed.
"""
    module = load_public_runner()
    runtime = module._import_runtime()
    real_run = runtime[-1]

    def run_declared_fixture(intent, **kwargs):
        authority = q3_q4_fixture_authority(intent.source, kwargs["artifact_store"])
        return real_run(intent, **kwargs, **authority)

    module._load_runtime = lambda: (*runtime[:-1], run_declared_fixture)
    return module.main(argv)
