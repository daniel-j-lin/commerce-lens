# CommerceLens Public Usage

This document keeps operational details out of the main README while preserving
the current Public v0.1.3 usage surface.

## Install The Codex Plugin

Verify that Codex CLI is available:

```bash
codex --version
```

If the command is unavailable and Node/npm are already installed:

```bash
npm install -g @openai/codex
codex --version
```

Add this repository as a Codex marketplace source and install the plugin:

```bash
codex plugin marketplace add daniel-j-lin/commerce-lens
codex plugin marketplace list
codex plugin add commerce-lens --marketplace commerce-lens
codex plugin list
```

The repository distribution files are:

- `.agents/plugins/marketplace.json`
- `.codex-plugin/plugin.json`
- `skills/commerce-lens/SKILL.md`
- `skills/commerce-lens/scripts/run_public_analysis.py`

After installation, restart or reload Codex if your surface requires it. In a
fresh Codex session, provide a CSV or XLSX file and ask a supported Public
v0.1.3 question.

## Local Checkout Installation

For local repository testing, add the checkout root as the marketplace source:

```bash
codex plugin marketplace add .
codex plugin add commerce-lens --marketplace commerce-lens
```

For release verification, prefer the GitHub marketplace source. Local checkout
installation copies the checkout tree, so ignored development artifacts such as
`.venv`, `.pytest_cache`, or runtime output can make installation slow. Use a
clean checkout when testing the local marketplace path.

## Supported Questions

Supported first-run questions include:

```text
How did revenue change from Q3 2026 to Q4 2026?
Why did revenue drop from Q3 2026 to Q4 2026?
What was AOV in Q4 2026?
```

Public v0.1.3 supports:

- single-period Revenue;
- single-period Orders;
- single-period AOV;
- Revenue Change between two explicitly governed comparable periods.

Grouping is `NONE`. Positive material claims are descriptive only.

## Schema Mapping

When source headers differ from the CommerceLens canonical schema, the Skill may
propose a source-to-canonical mapping and must ask the user to confirm or
correct it. Confirmed mappings can be handed to the deterministic runner as
JSON without renaming or editing the source file.

Example mapping:

```text
Order Number -> order_id
Line Item ID -> order_line_id
Order Date   -> order_date
SKU          -> product_id
Quantity     -> quantity
Sales Amount -> line_revenue
Currency     -> currency
Order Status -> eligibility_status
```

Mapping proposal is not mapping authority. Material analysis requires explicit
confirmation and deterministic validation.

## Deterministic Runner

CommerceLens does not expose a standalone `commerce-lens` shell CLI or hosted
API in Public v0.1.3. The repository includes a deterministic runner script used
by the Skill and developer verification.

Canonical CSV example:

```bash
python3.11 skills/commerce-lens/scripts/run_public_analysis.py \
  --source examples/public_v0_1/orders.csv \
  --source-type csv \
  --question-class revenue_change \
  --metric revenue_change \
  --baseline-label "Q3 2026" \
  --baseline-start 2026-07-01 \
  --baseline-end 2026-09-30 \
  --comparison-label "Q4 2026" \
  --comparison-start 2026-10-01 \
  --comparison-end 2026-12-31 \
  --original-question "How did revenue change from Q3 2026 to Q4 2026?"
```

Confirmed non-canonical mapping example:

```bash
python3.11 skills/commerce-lens/scripts/run_public_analysis.py \
  --source tests/fixtures/p14/P14-B-generic-marketplace.csv \
  --source-type csv \
  --question-class revenue_change \
  --metric revenue_change \
  --baseline-label "Q3 2026" \
  --baseline-start 2026-07-01 \
  --baseline-end 2026-09-30 \
  --comparison-label "Q4 2026" \
  --comparison-start 2026-10-01 \
  --comparison-end 2026-12-31 \
  --original-question "How did revenue change from Q3 2026 to Q4 2026?" \
  --mapping-json '{"Order Number":"order_id","Line Item ID":"order_line_id","Order Date":"order_date","SKU":"product_id","Product":"product_name","Category":"category_name","Quantity":"quantity","Sales Amount":"line_revenue","Currency":"currency","Unit Price":"unit_price","Order Status":"eligibility_status"}'
```

The runner translates already-interpreted structured arguments into
`PublicAnalysisIntent`, `PublicSourceSelection`, and `run_public_analysis(...)`.
It does not independently calculate Revenue, Orders, AOV, or Revenue Change.

## Date And Money Formats

Supported date and monetary representations are normalized deterministically.

Dates may be native XLSX dates, `YYYY-MM-DD`, `YYYY/MM/DD`, `Jul 15 2026`,
`July 15, 2026`, or ISO midnight timestamp strings without timezone
information. Numeric slash dates such as `01/02/2026`, non-midnight timestamps,
and timestamp strings with timezone information are rejected unless upstream
governed conversion supplies an order date.

Money values may be plain decimals, valid US-style thousands grouping such as
`1,200.00`, leading `$` notation, leading ISO currency text such as
`USD 120.00`, and negative input notation such as `-120.00` or `($120.00)`.
Currency notation is reconciled against the authoritative canonical `currency`
field; CommerceLens does not infer USD merely from `$`, and conflicting
explicit currency text fails closed.

Locale-ambiguous forms such as `1.200,00` and malformed thousands grouping are
rejected.

## Fail-Closed Fixture Example

The P14 insufficient fixture
`tests/fixtures/p14/P14-H-insufficient-unsupported.csv` contains realistic
status values `Complete` and `Voided`, but those values are not governed
eligibility authority under Public v0.1. Even if the user confirms the column
mapping, CommerceLens refuses to produce material KPIs.

Executed P14 evidence for this fixture produced no supported claim and included:

```text
Insufficient evidence to conclude.
source eligibility value is not explicitly mapped
```

This is expected evidence governance, not a crash.
