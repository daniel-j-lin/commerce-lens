#!/usr/bin/env python3
"""Command surface for the native CommerceLens Public v0.1 Skill."""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
import tempfile
from dataclasses import asdict, is_dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < (3, 11):
        print("CommerceLens requires Python >=3.11.", file=sys.stderr)
        return 2

    runtime = _load_runtime()
    if runtime is None:
        return 2
    (
        ClaimType,
        PeriodDefinition,
        SourceType,
        ArtifactStore,
        MetadataStore,
        PublicAnalysisIntent,
        PublicClaimIntent,
        PublicSourceSelection,
        confirmed_mapping_from_source_to_canonical,
        run_public_analysis,
    ) = runtime

    parser = _parser()
    args = parser.parse_args(argv)

    try:
        source_type = _source_type(args.source_type, SourceType)
        claim_intents = tuple(
            PublicClaimIntent(claim_type=_claim_type(item, ClaimType), proposed_meaning=_claim_meaning(item))
            for item in args.claim_type
        )
        source = PublicSourceSelection(
            source_path=Path(args.source),
            source_type=source_type,
            selected_sheet=args.selected_sheet,
            mapping=_mapping(args, confirmed_mapping_from_source_to_canonical),
            mapping_mode=(
                "confirmed_source_to_canonical_mapping"
                if args.mapping_json or args.mapping_file
                else "identity_canonical_columns"
            ),
        )
        intent = PublicAnalysisIntent(
            question_class=args.question_class,
            metric_id=args.metric,
            baseline_period=_period(
                PeriodDefinition,
                "baseline",
                args.baseline_label,
                args.baseline_start,
                args.baseline_end,
                args.date_convention_ref,
            ),
            comparison_period=_period(
                PeriodDefinition,
                "comparison",
                args.comparison_label,
                args.comparison_start,
                args.comparison_end,
                args.date_convention_ref,
            ),
            source=source,
            original_question_text=args.original_question,
            result_period_role=args.result_period_role,
            claim_intents=claim_intents,
        )
        with _runtime_paths(args) as (artifact_path, metadata_path):
            metadata_store = MetadataStore(metadata_path)
            outcome = run_public_analysis(
                intent,
                artifact_store=ArtifactStore(artifact_path),
                metadata_store=metadata_store,
            )
            payload = _outcome_payload(outcome, metadata_store)
        print(json.dumps(payload, indent=2, sort_keys=True, default=_json_default))
        return 0
    except Exception as exc:
        print(f"CommerceLens runner failed: {exc}", file=sys.stderr)
        return 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run CommerceLens Public v0.1 governed analysis.")
    parser.add_argument("--source", required=True, help="CSV or XLSX source path.")
    parser.add_argument("--source-type", required=True, choices=("csv", "xlsx", "excel_xlsx"))
    parser.add_argument("--selected-sheet", help="Required when an XLSX file needs explicit sheet selection.")
    parser.add_argument("--question-class", required=True)
    parser.add_argument("--metric", required=True)
    parser.add_argument("--baseline-label", required=True)
    parser.add_argument("--baseline-start", required=True)
    parser.add_argument("--baseline-end", required=True)
    parser.add_argument("--comparison-label", required=True)
    parser.add_argument("--comparison-start", required=True)
    parser.add_argument("--comparison-end", required=True)
    parser.add_argument("--date-convention-ref", default="order_date_utc")
    parser.add_argument("--result-period-role", choices=("baseline", "comparison"))
    parser.add_argument("--claim-type", action="append", default=["descriptive"])
    parser.add_argument("--original-question")
    parser.add_argument(
        "--mapping-json",
        help='Confirmed source-to-canonical mapping JSON, e.g. {"Order ID":"order_id"}.',
    )
    parser.add_argument("--mapping-file", help="Path to a JSON file containing confirmed source-to-canonical mapping.")
    parser.add_argument("--artifact-store")
    parser.add_argument("--metadata-store")
    return parser


def _load_runtime() -> tuple[Any, ...] | None:
    try:
        return _import_runtime()
    except ImportError as first_error:
        repo_root = _repo_root()
        if repo_root is None:
            print(
                "CommerceLens runtime is not importable and no local pyproject.toml was found for bootstrap.",
                file=sys.stderr,
            )
            print(str(first_error), file=sys.stderr)
            return None
        src_path = repo_root / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        try:
            return _import_runtime()
        except ImportError:
            pass
        installed = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", str(repo_root)],
            text=True,
            capture_output=True,
        )
        if installed.returncode != 0:
            print("CommerceLens bootstrap install failed.", file=sys.stderr)
            print(installed.stderr, file=sys.stderr)
            return None
        importlib.invalidate_caches()
        try:
            return _import_runtime()
        except ImportError as second_error:
            print("CommerceLens runtime remains unavailable after bootstrap install.", file=sys.stderr)
            print(str(second_error), file=sys.stderr)
            return None


def _import_runtime() -> tuple[Any, ...]:
    from commerce_lens.contracts.common import ClaimType, PeriodDefinition, SourceType
    from commerce_lens.persistence.artifact_store import ArtifactStore
    from commerce_lens.persistence.metadata_store import MetadataStore
    from commerce_lens.skill.integration import (
        PublicAnalysisIntent,
        PublicClaimIntent,
        PublicSourceSelection,
        run_public_analysis,
    )
    from commerce_lens.skill.schema_mapping import confirmed_mapping_from_source_to_canonical

    return (
        ClaimType,
        PeriodDefinition,
        SourceType,
        ArtifactStore,
        MetadataStore,
        PublicAnalysisIntent,
        PublicClaimIntent,
        PublicSourceSelection,
        confirmed_mapping_from_source_to_canonical,
        run_public_analysis,
    )


def _mapping(args: argparse.Namespace, factory) -> Any | None:
    if args.mapping_json and args.mapping_file:
        raise ValueError("use either --mapping-json or --mapping-file, not both")
    if not args.mapping_json and not args.mapping_file:
        return None
    raw = args.mapping_json
    if args.mapping_file:
        raw = Path(args.mapping_file).read_text(encoding="utf-8")
    assert raw is not None
    parsed = json.loads(raw)
    if _looks_like_canonical_mapping(parsed):
        return _canonical_mapping_from_runtime_payload(parsed)
    if not isinstance(parsed, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in parsed.items()):
        raise ValueError("mapping JSON must be a source-to-canonical object with string keys and values")
    return factory(parsed)


def _looks_like_canonical_mapping(parsed: Any) -> bool:
    return isinstance(parsed, dict) and "entries" in parsed


def _canonical_mapping_from_runtime_payload(parsed: dict[str, Any]) -> Any:
    from commerce_lens.canonical.mapping import CanonicalMapping

    return CanonicalMapping.model_validate(parsed)


def _repo_root() -> Path | None:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "pyproject.toml").is_file() and (candidate / "src" / "commerce_lens").is_dir():
            return candidate
    return None


def _source_type(value: str, source_type_cls) -> Any:
    if value == "csv":
        return source_type_cls.CSV
    return source_type_cls.EXCEL_XLSX


def _claim_type(value: str, claim_type_cls) -> Any:
    normalized = value.lower()
    if normalized == "descriptive":
        return claim_type_cls.DESCRIPTIVE
    if normalized == "diagnostic":
        return claim_type_cls.DIAGNOSTIC
    if normalized == "causal":
        return claim_type_cls.CAUSAL
    if normalized == "predictive":
        return claim_type_cls.PREDICTIVE
    if normalized == "prescriptive":
        return claim_type_cls.PRESCRIPTIVE
    raise ValueError(f"unsupported Claim type argument: {value}")


def _claim_meaning(value: str) -> str:
    if value.lower() == "diagnostic":
        return "Diagnostic explanation requested by the user"
    return "Public v0.1 governed descriptive Metric claim"


def _period(
    period_cls,
    period_id: str,
    label: str,
    start: str,
    end: str,
    date_convention_ref: str,
) -> Any:
    return period_cls(
        period_id=period_id,
        label=label,
        start_date=date.fromisoformat(start),
        end_date=date.fromisoformat(end),
        date_convention_ref=date_convention_ref,
    )


class _runtime_paths:
    def __init__(self, args: argparse.Namespace) -> None:
        self._args = args
        self._temporary: tempfile.TemporaryDirectory[str] | None = None

    def __enter__(self) -> tuple[Path, Path]:
        if self._args.artifact_store and self._args.metadata_store:
            return Path(self._args.artifact_store), Path(self._args.metadata_store)
        self._temporary = tempfile.TemporaryDirectory(prefix="commerce_lens_public_v0_1_")
        root = Path(self._temporary.name)
        return root / "artifacts", root / "metadata.sqlite"

    def __exit__(self, *exc_info) -> None:
        if self._temporary is not None:
            self._temporary.cleanup()


def _outcome_payload(outcome, metadata_store) -> dict[str, Any]:
    return {
        "rendered_text": outcome.response.render_text(),
        "response": asdict(outcome.response),
        "request_id": outcome.request.request_id if outcome.request is not None else None,
        "run_id": outcome.analysis_result.run_id if outcome.analysis_result is not None else None,
        "run_status": outcome.analysis_result.run_status if outcome.analysis_result is not None else None,
        "claim_decisions": tuple(outcome.claim_decisions),
        "validated_results_summary": (
            _validated_results_summary(metadata_store) if outcome.analysis_result is not None else ()
        ),
    }


def _validated_results_summary(metadata_store) -> tuple[dict[str, Any], ...]:
    summaries: dict[str, dict[str, Any]] = {}
    for record in metadata_store.list_validation_records():
        if record.validated_result_ref is None:
            continue
        candidate = {
            "validated_result_ref": record.validated_result_ref,
            "metric_ref": record.metric_ref,
            "period_ref": record.period_ref,
            "period_role": record.period_role,
            "actual_value": record.actual_value,
            "actual_state": record.actual_state,
            "currency": record.observed.get("currency"),
            "validation_status": record.status,
            "validation_rule_id": record.validation_rule_id,
        }
        existing = summaries.get(record.validated_result_ref)
        if existing is not None and not _prefer_validation_record(candidate, existing):
            continue
        summaries[record.validated_result_ref] = candidate
    return tuple(summaries.values())


def _prefer_validation_record(candidate: dict[str, Any], existing: dict[str, Any]) -> bool:
    preferred_rules = (
        "validation:revenue_sum",
        "validation:orders_count",
        "validation:aov_from_validated_revenue_and_orders",
        "validation:revenue_change_from_validated_revenues",
    )
    candidate_rank = (
        preferred_rules.index(candidate["validation_rule_id"])
        if candidate["validation_rule_id"] in preferred_rules
        else len(preferred_rules)
    )
    existing_rank = (
        preferred_rules.index(existing["validation_rule_id"])
        if existing["validation_rule_id"] in preferred_rules
        else len(preferred_rules)
    )
    return candidate_rank < existing_rank


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return value.to_eng_string()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
