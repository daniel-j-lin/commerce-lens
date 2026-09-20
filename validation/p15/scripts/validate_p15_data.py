#!/usr/bin/env python3
"""Independently validate P15 data and write the frozen dataset manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from generate_p15_data import GENERATOR_VERSION, HEADERS


PERIODS = {
    "baseline": ("2025-01-01", "2025-03-31"),
    "comparison": ("2026-01-01", "2026-03-31"),
}
EXPECTED_A = {
    "rows": 100,
    "orders": {"baseline": 48, "comparison": 45},
    "revenue": {"baseline": Decimal("12000.00"), "comparison": Decimal("10800.00")},
}


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != HEADERS:
            raise AssertionError(f"{path.name}: schema mismatch")
        rows = list(reader)
    return rows


def _period(value: str) -> str:
    for name, (start, end) in PERIODS.items():
        if start <= value <= end:
            return name
    raise AssertionError(f"date outside frozen periods: {value}")


def _summary(path: Path, rows: list[dict[str, str]]) -> dict:
    if not rows:
        raise AssertionError(f"{path.name}: empty dataset")
    statuses = Counter(row["Order Status"] for row in rows)
    currencies = {row["Currency"] for row in rows}
    if currencies != {"USD"}:
        raise AssertionError(f"{path.name}: currency semantics are not USD-only")
    if not set(statuses).issubset({"paid", "cancelled"}):
        raise AssertionError(f"{path.name}: unsupported eligibility value")
    if not statuses["cancelled"]:
        raise AssertionError(f"{path.name}: missing cancelled control row")
    if any(not re.fullmatch(r"P15[AB]-[BCX]-\d{4}", row["Order Number"]) for row in rows):
        raise AssertionError(f"{path.name}: non-synthetic order identifier")
    for row in rows:
        Decimal(row["Net Merchandise Sales"])
        if row["Order Status"] == "paid" and Decimal(row["Net Merchandise Sales"]) <= 0:
            raise AssertionError(f"{path.name}: non-positive eligible sales")

    by_period: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_period[_period(row["Order Date"])].append(row)
    eligible_orders = {}
    revenue = {}
    aov = {}
    for period in PERIODS:
        eligible = [row for row in by_period[period] if row["Order Status"] == "paid"]
        orders = {row["Order Number"] for row in eligible}
        eligible_orders[period] = len(orders)
        revenue[period] = sum((Decimal(row["Net Merchandise Sales"]) for row in eligible), Decimal("0.00"))
        aov[period] = (revenue[period] / eligible_orders[period]).quantize(Decimal("0.01"))
    multi_line_orders = sum(
        1 for count in Counter(row["Order Number"] for row in rows if row["Order Status"] == "paid").values() if count > 1
    )
    if multi_line_orders < 1:
        raise AssertionError(f"{path.name}: no multi-line orders")
    return {
        "rows": len(rows),
        "schema": list(HEADERS),
        "source_type": "csv",
        "date_range": {"min": min(row["Order Date"] for row in rows), "max": max(row["Order Date"] for row in rows)},
        "eligibility_semantics": {"paid": "eligible", "cancelled": "excluded"},
        "currency_semantics": "USD only; no FX conversion",
        "status_counts": dict(statuses),
        "eligible_orders": eligible_orders,
        "revenue": {key: str(value) for key, value in revenue.items()},
        "aov": {key: str(value) for key, value in aov.items()},
        "multi_line_order_count": multi_line_orders,
    }


def _file_meta(path: Path, summary: dict) -> dict:
    raw = path.read_bytes()
    return {
        "filename": path.name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "byte_size": len(raw),
        "generation_script": GENERATOR_VERSION,
        "validation": summary,
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(data_dir: Path) -> dict:
    a_path = data_dir / "P15-A-governed-marketplace.csv"
    b_path = data_dir / "P15-B-coverage-unknown.csv"
    a_rows = _read(a_path)
    b_rows = _read(b_path)
    a = _summary(a_path, a_rows)
    b = _summary(b_path, b_rows)
    if a["rows"] != EXPECTED_A["rows"]:
        raise AssertionError(f"Dataset A row count is {a['rows']}, expected 100")
    if a["eligible_orders"] != EXPECTED_A["orders"]:
        raise AssertionError(f"Dataset A order oracle mismatch: {a['eligible_orders']}")
    if {key: Decimal(value) for key, value in a["revenue"].items()} != EXPECTED_A["revenue"]:
        raise AssertionError(f"Dataset A revenue oracle mismatch: {a['revenue']}")
    if b["rows"] != 80:
        raise AssertionError(f"Dataset B row count is {b['rows']}, expected 80")
    revenue_change = Decimal(a["revenue"]["comparison"]) - Decimal(a["revenue"]["baseline"])
    oracle = {
        "baseline_revenue": a["revenue"]["baseline"],
        "comparison_revenue": a["revenue"]["comparison"],
        "revenue_change": f"{revenue_change:.2f}",
        "baseline_orders": a["eligible_orders"]["baseline"],
        "comparison_orders": a["eligible_orders"]["comparison"],
        "baseline_aov": a["aov"]["baseline"],
        "comparison_aov": a["aov"]["comparison"],
    }
    manifest = {
        "protocol": "VAL-FIRSTUSER-01 / P15",
        "protocol_version": "p15-execution-package-v1",
        "generator": {
            "version": GENERATOR_VERSION,
            "filename": "generate_p15_data.py",
            "sha256": _sha256(Path(__file__).with_name("generate_p15_data.py")),
        },
        "tested_periods": PERIODS,
        "datasets": {
            "A": _file_meta(a_path, a),
            "B": _file_meta(b_path, b),
        },
        "private_oracle": oracle,
        "dataset_b_expected_authority_outcome": {
            "status": "blocked_or_clarification_required",
            "coverage_authority": "unknown",
            "prohibited_material_claims": ["revenue", "orders", "aov", "revenue_change"],
        },
    }
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).parents[1] / "data")
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    manifest = validate(args.data_dir)
    if args.manifest:
        args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
