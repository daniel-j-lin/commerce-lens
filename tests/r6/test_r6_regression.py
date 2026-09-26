from __future__ import annotations

from collections import Counter
from dataclasses import fields
from pathlib import Path
import shutil

from commerce_lens.contracts.results import AnalysisResult
from commerce_lens.evidence.identifiers import sha256_file
from commerce_lens.fixture_runner.r5_discovery import discover_r5_fixtures
from commerce_lens.fixture_runner.r5_inventory import ImplementationStatus, load_r5_inventory
from commerce_lens.persistence.artifact_store import ArtifactStore
from commerce_lens.persistence.metadata_store import MetadataStore
from commerce_lens.skill.integration import run_public_analysis
from tests.end_to_end.test_public_v0_1 import _intent, _row, _write_csv
from tests.public_fixture_authority import q3_q4_fixture_authority


ROOT = Path(__file__).resolve().parents[2]
ACTIVE_SHA256 = "1923467ec4c9750440b6eee5529feba59d13dbbb436e8d65dd4828834cf10e20"
DEFERRED_SHA256 = "1dc26969766834840648ed2f6b67d9000b018ff0ae4fd618d3648df02875c93f"


def test_public_revenue_change_schema_and_behavior_remain_unchanged(tmp_path: Path) -> None:
    source = _write_csv(
        tmp_path / "public.csv",
        [
            _row(order_id="q3-o1", order_date="2026-07-15", line_revenue="120.00"),
            _row(order_id="q4-o1", order_date="2026-10-15", line_revenue="100.00"),
        ],
    )
    artifacts = ArtifactStore(tmp_path / "artifacts")
    outcome = run_public_analysis(
        _intent(source, "How did revenue change from Q3 2026 to Q4 2026?"),
        artifact_store=artifacts,
        metadata_store=MetadataStore(tmp_path / "metadata.sqlite"),
        **q3_q4_fixture_authority(_intent(source, "x").source, artifacts),
    )

    claim = outcome.response.supported_claims[0]
    assert claim.metric_ref == "revenue_change"
    assert str(claim.value) == "-20.00"
    response_fields = {item.name for item in fields(outcome.response)}
    assert response_fields == {
        "supported_claims",
        "evidence_summary",
        "mapping_proposals",
        "required_mapping_fields",
        "limitations",
        "unsupported_conclusions",
        "additional_evidence_needed",
        "clarification_required",
        "blocked",
        "insufficient_evidence_message",
        "coverage_provenance",
        "diagnostic_analysis",
    }
    assert outcome.response.diagnostic_analysis is None
    forbidden = {
        "hypothesis",
        "hypotheses",
        "diagnostic_family",
        "diagnostic_families",
        "evidence_readiness",
        "first_blocker",
        "first_controlling_blocker",
        "r6_to_r7_handoff",
        "r6_handoffs",
    }
    assert not forbidden & {item.lower() for item in response_fields}
    assert not {"hypotheses", "diagnostic_families", "r6_handoffs"} & set(AnalysisResult.model_fields)


def test_frozen_r5_inventory_counts_states_special_cases_and_hashes(tmp_path: Path) -> None:
    isolated = tmp_path / "r5"
    shutil.copytree(ROOT / "fixtures/r5", isolated, ignore=shutil.ignore_patterns(".DS_Store"))
    inventory = load_r5_inventory(ROOT, isolated)
    fixtures = discover_r5_fixtures(isolated, inventory)
    statuses = Counter(item.implementation_status for item in inventory.active.entries)
    by_id = {item.fixture_id: item for item in inventory.active.entries}

    assert len(inventory.active.entries) == 129
    assert len(inventory.deferred.entries) == 25
    assert len(fixtures) == 109
    assert statuses == {
        ImplementationStatus.EXECUTABLE: 108,
        ImplementationStatus.DEPENDENCY_BLOCKED: 1,
        ImplementationStatus.NOT_IMPLEMENTED: 20,
    }
    assert by_id["FX-R5-PREC-003A"].implementation_status is ImplementationStatus.DEPENDENCY_BLOCKED
    assert by_id["FX-R5-R4-034A"].implementation_status is ImplementationStatus.NOT_IMPLEMENTED
    assert sha256_file(ROOT / "fixtures/r5/inventory/active.yaml") == ACTIVE_SHA256
    assert sha256_file(ROOT / "fixtures/r5/inventory/deferred.yaml") == DEFERRED_SHA256


def test_r6_fixture_surface_contains_no_benchmark_scoring() -> None:
    source = (ROOT / "fixtures/r6/cases.json").read_text(encoding="utf-8").lower()
    prohibited = ("accuracy_score", "precision", "recall", "leaderboard", "weighted_benchmark", "quality_score")
    assert not any(item in source for item in prohibited)
