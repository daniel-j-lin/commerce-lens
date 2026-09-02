# CommerceLens Public v0.1 Examples

These files are synthetic public examples for the structured Public v0.1 Skill
integration.

## Files

- `orders.csv`: normal CSV path for Revenue, Orders, numeric AOV, Revenue
  Change, Killer Demo 1, and Killer Demo 2.
- `aov_undefined.csv`: CSV path where all Q4 rows are excluded, so Orders equals
  zero and AOV is governed as Undefined.
- `orders.xlsx`: XLSX path using the same synthetic order shape as `orders.csv`;
  use sheet `Orders`.

## Normal CSV Demo

Use `orders.csv` for:

- Revenue in Q4 2026: 100.00 USD
- Orders in Q4 2026: 1
- AOV in Q4 2026: 100.00 USD
- Revenue Change from Q3 2026 to Q4 2026: -20.00 USD

The same file supports:

```text
How did revenue change from Q3 2026 to Q4 2026?
```

and the diagnostic-refusal demonstration:

```text
Why did revenue drop from Q3 2026 to Q4 2026?
```

The supported descriptive decline may be shown, but the diagnostic explanation
must be refused with:

```text
Insufficient evidence to conclude why Revenue declined.
```

## AOV Undefined Demo

Use `aov_undefined.csv` for:

```text
What was AOV in Q4 2026?
```

Q4 has zero eligible orders. Public v0.1 therefore reports AOV as Undefined with
value `None` and `undefined_reason=orders_equals_zero`; AOV is not represented
as numeric zero.

## XLSX Demo

Use `orders.xlsx` with `SourceType.EXCEL_XLSX` and `selected_sheet="Orders"`.
It demonstrates that the supported public source boundary includes XLSX as well
as CSV.

## Invocation Boundary

The examples are used through structured Python invocation:

- `PublicAnalysisIntent`
- `PublicSourceSelection`
- `run_public_analysis(...)`

Public v0.1 does not expose a CLI, GUI, REST endpoint, hosted SaaS workflow, or
general natural-language parser.
