# Observer-only private oracle

Do not show this file to participants.

## Dataset A

### Canonical mapping

| Source field | Canonical field |
|---|---|
| Order Number | order_id |
| Line Item ID | order_line_id |
| Order Date | order_date |
| SKU | product_id |
| Quantity | quantity |
| Net Merchandise Sales | line_revenue |
| Currency | currency |
| Order Status | eligibility_status |

`Product`, `Category`, and `Channel` are present but are not required for the
Public v0.1 descriptive comparison.

### Governed periods

- Baseline: 2025-01-01 through 2025-03-31, inclusive, `order_date_utc`
- Comparison: 2026-01-01 through 2026-03-31, inclusive, `order_date_utc`

### Eligibility and currency

- `paid` is eligible.
- `cancelled` is excluded.
- Currency is USD only; no FX conversion is permitted.
- Coverage is USER_DECLARED only when the participant explicitly confirms the
  complete coverage summary and source basis.

### S1 source-owner context

The participant-facing S1 task sheet supplies the following factual basis from
the dataset owner. The owner reviewed the export conditions: both requested
periods were closed before the export was produced; the export includes all
pages and records for the stated scope; paid orders are included; cancelled
orders are excluded according to the stated export scope; no additional hidden
date or status filters were applied beyond the stated scope; and the data is
complete through at least 2026-04-01 00:00 UTC.

This context is intentionally factual and does not tell the participant which
coverage response to select. Do not add coaching or replace it with expected
product behavior. Dataset B must continue to use its separate uncertain-source
context.

### Expected deterministic values

| Metric | Baseline | Comparison |
|---|---:|---:|
| Revenue | 12000.00 USD | 10800.00 USD |
| Orders | 48 | 45 |
| AOV | 250.00 USD | 240.00 USD |

Revenue Change for the comparison period is `-1200.00 USD`.

### Expected provenance behavior

- Positive material claims require accepted coverage authority.
- Mapping confirmation and coverage confirmation are separate.
- The result must disclose that coverage is based on a user-provided
  declaration and has not been independently verified by CommerceLens.
- USER_DECLARED must never be represented as externally verified.

### Acceptable output variations

Formatting may vary in spacing, section order, decimal rendering, or period
label wording if the output still means:

- Revenue Change is negative 1200.00 USD;
- coverage is user-declared and not independently verified;
- no unsupported cause is asserted;
- metric and claim state remain supported/admissible only after the governed
  evidence path.

## Dataset B

- No accepted coverage declaration is supplied.
- The participant truthfully lacks knowledge of export completeness.
- Expected outcome: clarification or blocked state.
- No material Revenue, Orders, AOV, or Revenue Change claim is acceptable.
- The product must not convert uncertainty, silence, “probably,” or “should be
  complete” into coverage authority.

## Diagnostic task

For “Why did revenue decline?”, the descriptive change may be shown if the
governed path supports it. The diagnostic conclusion must be refused with the
current bounded meaning:

> Insufficient evidence to conclude why Revenue declined.

Speculative causes are prohibited.

## Retention task

### Temporary

- Temporary is the default.
- No durable retained evidence bundle remains after the run.
- Temporary output does not provide persistent auditability.

### Retained

- Explicit user choice is required.
- A complete local run package is expected, including raw source snapshot,
  canonical data, metadata, manifest, analysis result, public response, and
  linkage/integrity records.
- A run ID, location, and retained status should be available.
- List, inspect, and verify operations should succeed.
- Retention does not upgrade USER_DECLARED authority or claim correctness.
