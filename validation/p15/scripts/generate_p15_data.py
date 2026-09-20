#!/usr/bin/env python3
"""Generate the frozen synthetic P15 datasets with stable bytes."""

from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path


GENERATOR_VERSION = "p15-data-generator-v1"
HEADERS = (
    "Order Number",
    "Line Item ID",
    "Order Date",
    "SKU",
    "Product",
    "Category",
    "Quantity",
    "Net Merchandise Sales",
    "Currency",
    "Order Status",
    "Channel",
)

PRODUCTS = (
    ("SKU-TEA-001", "Everyday Tea", "Beverages"),
    ("SKU-MUG-002", "Ceramic Mug", "Home"),
    ("SKU-INF-003", "Steel Infuser", "Beverages"),
    ("SKU-TOW-004", "Kitchen Towel", "Home"),
    ("SKU-GFT-005", "Gift Set", "Gifts"),
    ("SKU-CND-006", "Candle", "Home"),
    ("SKU-SNK-007", "Snack Box", "Food"),
    ("SKU-BAG-008", "Canvas Tote", "Accessories"),
)
CHANNELS = ("web", "marketplace", "social")


def _amounts(count: int, target: Decimal, *, phase: int) -> list[Decimal]:
    values = [
        Decimal(180 + ((index + phase) % 6) * 20 + ((index * 3 + phase) % 4) * 10)
        for index in range(count)
    ]
    values[-1] += target - sum(values, Decimal("0.00"))
    if values[-1] <= 0:
        raise ValueError("target adjustment produced a non-positive order")
    return values


def _dates(start: date, end: date, count: int, *, phase: int) -> list[date]:
    span = (end - start).days + 1
    dates = [start + timedelta(days=((index * 11 + phase * 7) % span)) for index in range(count)]
    if count >= 2:
        dates[0] = start
        dates[1] = end
    return dates


def _eligible_rows(
    *,
    prefix: str,
    start: date,
    end: date,
    count: int,
    target: Decimal,
    multi_line_count: int,
    phase: int,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    amounts = _amounts(count, target, phase=phase)
    order_dates = _dates(start, end, count, phase=phase)
    for index, (amount, order_date) in enumerate(zip(amounts, order_dates, strict=True), start=1):
        order_number = f"{prefix}-{index:04d}"
        if index <= multi_line_count:
            line_values = (amount * Decimal("0.60")).quantize(Decimal("0.01"), rounding="ROUND_HALF_UP")
            line_values = (line_values, amount - line_values)
        else:
            line_values = (amount,)
        for line_index, line_value in enumerate(line_values, start=1):
            sku, product, category = PRODUCTS[(index + line_index + phase) % len(PRODUCTS)]
            rows.append(
                {
                    "Order Number": order_number,
                    "Line Item ID": f"{order_number}-L{line_index}",
                    "Order Date": order_date.isoformat(),
                    "SKU": sku,
                    "Product": product,
                    "Quantity": str(1 + ((index + line_index + phase) % 3)),
                    "Net Merchandise Sales": f"{line_value:.2f}",
                    "Currency": "USD",
                    "Order Status": "paid",
                    "Channel": CHANNELS[(index + phase) % len(CHANNELS)],
                }
            )
    return rows


def _cancelled_row(*, order_number: str, order_date: date, phase: int) -> dict[str, str]:
    sku, product, category = PRODUCTS[(phase + 3) % len(PRODUCTS)]
    return {
        "Order Number": order_number,
        "Line Item ID": f"{order_number}-L1",
        "Order Date": order_date.isoformat(),
        "SKU": sku,
        "Product": product,
        "Quantity": "1",
        "Net Merchandise Sales": "500.00",
        "Currency": "USD",
        "Order Status": "cancelled",
        "Channel": CHANNELS[phase % len(CHANNELS)],
    }


def build_dataset_a() -> list[dict[str, str]]:
    baseline = _eligible_rows(
        prefix="P15A-B", start=date(2025, 1, 1), end=date(2025, 3, 31),
        count=48, target=Decimal("12000.00"), multi_line_count=2, phase=1,
    )
    comparison = _eligible_rows(
        prefix="P15A-C", start=date(2026, 1, 1), end=date(2026, 3, 31),
        count=45, target=Decimal("10800.00"), multi_line_count=2, phase=2,
    )
    cancelled = [
        _cancelled_row(order_number="P15A-X-0001", order_date=date(2025, 2, 20), phase=1),
        _cancelled_row(order_number="P15A-X-0002", order_date=date(2026, 2, 14), phase=2),
        _cancelled_row(order_number="P15A-X-0003", order_date=date(2026, 3, 28), phase=3),
    ]
    return baseline + comparison + cancelled


def build_dataset_b() -> list[dict[str, str]]:
    baseline = _eligible_rows(
        prefix="P15B-B", start=date(2025, 1, 1), end=date(2025, 3, 31),
        count=39, target=Decimal("10000.00"), multi_line_count=1, phase=4,
    )
    comparison = _eligible_rows(
        prefix="P15B-C", start=date(2026, 1, 1), end=date(2026, 3, 31),
        count=39, target=Decimal("10000.00"), multi_line_count=0, phase=5,
    )
    cancelled = [_cancelled_row(order_number="P15B-X-0001", order_date=date(2026, 2, 8), phase=4)]
    return baseline + comparison + cancelled


def _write(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=HEADERS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parents[1] / "data")
    args = parser.parse_args()
    _write(args.output_dir / "P15-A-governed-marketplace.csv", build_dataset_a())
    _write(args.output_dir / "P15-B-coverage-unknown.csv", build_dataset_b())
    print(f"generated {GENERATOR_VERSION} in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
