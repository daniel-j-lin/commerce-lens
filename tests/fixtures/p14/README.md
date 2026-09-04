# P14 Realistic Synthetic Ecommerce Export Fixtures

P14 fixtures are controlled synthetic exports for evaluating whether the Public
v0.1.x governed workflow can handle realistic schema and format variation using
existing P12 mapping authority and P13 date/money normalization. They are not
vendor compatibility claims.

## Controlled Economics

All successful equivalent fixtures encode the same facts:

- Q3 2026 eligible rows: `70.00 USD` and `50.00 USD`
- Q4 2026 eligible rows: `40.00 USD` and `60.00 USD`
- Q4 2026 excluded control row: `999.00 USD`, status `cancelled`

Expected supported KPI calculations:

- `Revenue_Q3 = 70.00 + 50.00 = 120.00 USD`
- `Revenue_Q4 = 40.00 + 60.00 = 100.00 USD`
- `Revenue Change = Revenue_Q4 - Revenue_Q3 = 100.00 - 120.00 = -20.00 USD`
- `Orders_Q4 = count(distinct eligible order_id in Q4) = 2`
- `AOV_Q4 = Revenue_Q4 / Orders_Q4 = 100.00 / 2 = 50.00 USD`

`paid` is mapped to Eligible and `cancelled` is mapped to Excluded by the
existing Public v0.1 Skill integration. Monetary value alone is not eligibility
authority.

## Fixture Inventory

| Fixture ID | Family | File | Type | Grain | Mapping Contract | Required Confirmation | Date Format | Money Format | Expected Outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P14-A | Canonical control | `P14-A-canonical-control.csv` | CSV | Order line | Identity canonical columns | No | ISO date text | Decimal text | Governed Revenue Change `-20.00 USD`; Q4 Revenue `100.00 USD`; Q4 Orders `2`; Q4 AOV `50.00 USD`; ClaimDecision Admissible |
| P14-B | Generic marketplace-style | `P14-B-generic-marketplace.csv` | CSV | Order line | Confirm source headers including `Order Number`, `Line Item ID`, `Sales Amount`, `Order Status` to canonical fields | Yes | ISO date text | Decimal text | Same governed KPIs as P14-A after confirmation |
| P14-C | Shopify-like synthetic export | `P14-C-shopify-like-synthetic.csv` | CSV | Order line | Confirm source headers including `Name`, `Lineitem id`, `Created at`, `Lineitem total`, `Financial Status` | Yes | ISO date text | Decimal text | Same governed KPIs as P14-A after confirmation |
| P14-D | WooCommerce-like synthetic export | `P14-D-woocommerce-like-synthetic.csv` | CSV | Order line | Confirm source headers including `Order Item ID`, `Date Created`, `Line Total`, `Status` | Yes | ISO date text | Decimal text | Same governed KPIs as P14-A after confirmation |
| P14-E | ERP/back-office style | `P14-E-erp-back-office.csv` | CSV | Order line | Confirm source headers including `Document No`, `Line No`, `Posting Date`, `Net Amount`, `Document Status` | Yes | ISO date text | Decimal text | Same governed KPIs as P14-A after confirmation |
| P14-F | Messy-but-valid | `P14-F-messy-but-valid.csv` | CSV | Order line | Confirm whitespace/case-varied source headers to canonical fields | Yes | Supported P13 mix: long month date, `YYYY/MM/DD`, ISO timestamp at midnight | Supported P13 mix: `$`, `USD`, decimal text | Same governed KPIs as P14-A after confirmation |
| P14-G | XLSX-native export | `P14-G-xlsx-native-export.xlsx` | XLSX | Order line | Confirm spreadsheet headers including `Order Number`, `Line Item ID`, `Sales Amount`, `Order Status`; selected sheet `Orders` | Yes | Native spreadsheet datetime cells formatted `yyyy-mm-dd` | Native numeric cells formatted as currency | Same governed KPIs as P14-A after confirmation |
| P14-H | Insufficient/unsupported realistic export | `P14-H-insufficient-unsupported.csv` | CSV | Order line | Confirmed mapping can identify value fields, but status values `Complete`/`Voided` are not governed eligibility values | Yes, then deterministic block | ISO date text | Decimal text | Fail closed; no KPI; no material claim; limitation includes unresolved eligibility authority |
| P14-H2 | Order-grain insufficient export | `P14-H2-order-grain-insufficient.csv` | CSV | Order | Lacks line-level authority fields such as `order_line_id`, `product_id`, and `quantity` | Cannot complete safely | ISO date text | Decimal text | Fail closed at mapping authority; no KPI; no material claim |

## Mapping Details

Successful non-canonical fixtures use explicit source-to-canonical mappings in
`tests/p14/test_realistic_synthetic_ecommerce_fixtures.py`. The test suite also
verifies that these files do not execute before confirmation.

Known limitation: the deterministic P12 helper proposes only a narrow alias set.
For materially different export styles, the Codex Skill/agent may propose or
correct mappings, but deterministic execution still requires explicit confirmed
source-to-canonical mapping authority before any material result.

## Public Claim Boundary

Supported by these fixtures: CommerceLens can analyze supported CSV/XLSX
ecommerce exports with varying schemas and common formats after explicit schema
confirmation.

Not supported by these fixtures: universal ecommerce export compatibility,
automatic vendor compatibility, Shopify integration, WooCommerce integration,
ERP integration, arbitrary schema understanding, or product/category analysis.
