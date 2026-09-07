# CommerceLens

**Evidence-governed analytics for AI agents.**

CommerceLens turns supported commerce data into validated, traceable analytical
claims and refuses conclusions the available evidence cannot support.

```text
No material claim without traceable evidence.
```

CommerceLens Public v0.1.3 is a local, open-source Codex Skill/plugin workflow
for bounded commerce analytics over CSV and XLSX files. It is designed around a
specific reliability problem: a system can execute a calculation correctly and
still make an analytically unsupported claim about what the result means.

CommerceLens governs the step between computation and material claims.

## Why It Is Different

CommerceLens separates the parts of analytics that are often blurred together:

```text
Executed Result != Validated Result
Validated Result != Admissible Evidence
Admissible Evidence != ClaimDecision
```

Successful computation does not by itself justify an analytical conclusion.
CommerceLens keeps computed results, validated evidence, and supported claims
separate. Unsupported gaps fail closed instead of being filled with plausible
explanations.

The deterministic runtime is the authority for KPI values, validation, Evidence,
and ClaimDecision outcomes. The agent may interpret the business question,
inspect source schemas, propose mappings, ask for clarification, and explain the
validated output. It may not turn a plausible narrative into a supported
material claim.

## Governed Refusal Demo

Question:

```text
Why did revenue drop from Q3 2026 to Q4 2026?
```

With the public synthetic example data, CommerceLens can support the descriptive
result:

```text
Revenue Change for Q4 2026: -20.00 USD.
```

It cannot support the requested diagnostic explanation. The governed response
includes:

```text
Insufficient evidence to conclude why Revenue declined.
```

That refusal is intentional. Public v0.1.3 can report the validated change; it
does not infer drivers, causes, recommendations, or forecasts from the same
evidence.

## Public v0.1.3 Scope

| Supported now | Not supported in Public v0.1.3 |
| --- | --- |
| CSV files with canonical columns | Positive diagnostic explanations |
| XLSX files with canonical columns | Causal inference |
| Explicitly confirmed source-to-canonical mappings | Forecasting |
| Revenue | Recommendations |
| Orders | Revenue Change Percentage |
| AOV | Product/category analysis |
| Absolute Revenue Change | Contribution/ranking analysis |
| Descriptive positive material claims | Marketplace/vendor connectors |
| Fail-closed unsupported conclusions | Hosted SaaS or REST API |

Important governed behaviors:

- `AOV` is `Undefined` when `Orders = 0`; it is not reported as numeric zero.
- `Revenue Change` is absolute change only.
- `Revenue Change Percentage` is not currently supported.
- Positive material claims are descriptive only in Public v0.1.3.
- Why and diagnostic requests are governed-refused.
- Causal, predictive, and prescriptive claims are not supported in Public
  v0.1.3.
- Non-canonical source mappings require explicit confirmation and deterministic
  validation before material analysis.
- SQLite exists in the lower-level kernel, but CSV/XLSX are the headline Public
  v0.1.3 workflow.

## How It Works

The public workflow follows the same governed chain used by the deterministic
runtime:

```text
Business Question
-> Metric Definition
-> Required Evidence
-> Data Sufficiency
-> Deterministic Execution
-> Deterministic Validation
-> Evidence
-> ClaimDecision
-> Supported Answer / Governed Refusal
```

The Codex Skill turns supported natural-language requests into a structured
`PublicAnalysisIntent`. The runner invokes the CommerceLens application service,
which performs canonicalization, KPI execution, validation, evidence binding,
and claim admissibility checks.

## Quick Start

Prerequisite:

```bash
codex --version
```

If Codex CLI is unavailable and Node/npm are already installed:

```bash
npm install -g @openai/codex
```

Install CommerceLens from the repository marketplace:

```bash
codex plugin marketplace add daniel-j-lin/commerce-lens
codex plugin add commerce-lens --marketplace commerce-lens
```

Then start a fresh Codex session, provide a CSV or XLSX file, and ask a
supported question such as:

```text
How did revenue change from Q3 2026 to Q4 2026?
What was AOV in Q4 2026?
Why did revenue drop from Q3 2026 to Q4 2026?
```

End-user workflow:

```text
Install/enable CommerceLens
-> provide a CSV or XLSX file
-> ask a supported natural-language question
-> CommerceLens inspects source headers
-> confirm or correct any proposed mapping
-> receive governed analysis with Evidence and ClaimDecision status
```

For detailed runner usage, local checkout notes, and supported format examples,
see [docs/USAGE.md](docs/USAGE.md).

## Schema Mapping Example

If a file uses non-canonical source headers, CommerceLens may propose a mapping:

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

The proposal is not authority. The user must explicitly confirm or correct the
mapping, and the deterministic `validate_mapping(...)` authority must pass
before CommerceLens can produce material analysis.

The P14 generic marketplace-style synthetic fixture verifies this behavior:
without confirmation it blocks; with confirmed mapping it produces the same
governed KPIs as the canonical control fixture.

## Public Examples

Synthetic public examples are available in
[examples/public_v0_1/](examples/public_v0_1/):

- `orders.csv` demonstrates Revenue, Orders, numeric AOV, Revenue Change, the
  supported descriptive answer, and the diagnostic refusal demo.
- `aov_undefined.csv` demonstrates AOV as `Undefined` when Orders equals zero.
- `orders.xlsx` demonstrates the XLSX source path with the same synthetic order
  shape as `orders.csv`.

With `examples/public_v0_1/orders.csv`, Q3 2026 Revenue is `120.00 USD` and Q4
2026 Revenue is `100.00 USD`, so the supported absolute Revenue Change is
`-20.00 USD`.

## Engineering Credibility

CommerceLens Public v0.1.3 is intentionally narrow, but the supported path is
backed by deterministic contracts, validation, fixtures, and tests:

- Pydantic contracts for requests, results, validation, Evidence, and
  ClaimDecision structures.
- Governed Metric Registry entries for supported public metrics.
- Deterministic CSV/XLSX intake, canonical mapping validation, KPI execution,
  result validation, Evidence binding, and public response projection.
- Fail-closed behavior for unsupported metrics, unsupported question classes,
  unresolved mappings, unsupported eligibility semantics, and unsupported claim
  types.
- Native Codex Skill/plugin packaging files:
  `.agents/plugins/marketplace.json`, `.codex-plugin/plugin.json`, and
  `skills/commerce-lens/SKILL.md`.
- Realistic synthetic ecommerce fixture coverage for canonical,
  marketplace-style, Shopify-like, WooCommerce-like, ERP/back-office, messy-but-valid,
  XLSX-native, and insufficient-source cases. These are fixture families, not
  vendor compatibility claims.

For the v0.1.3 verification run on 2026-09-04 with Python 3.11.9, the full
repository suite reported `601 passed`. Test counts describe that specific
verification run; they are not a permanent contract.

Developer setup and verification commands are in
[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Documentation

- [Public usage](docs/USAGE.md)
- [Developer notes](docs/DEVELOPMENT.md)
- [Public examples](examples/public_v0_1/README.md)
- [P14 synthetic fixture evidence](tests/fixtures/p14/README.md)
- [Frozen project instructions](docs/frozen/PROJECT_MASTER_INSTRUCTIONS.md)
- [Frozen PRD](docs/frozen/PRD.md)
- [Frozen Skill scope](docs/frozen/SKILL_SCOPE_SPECIFICATION.md)
- [Frozen Evidence contract](docs/frozen/EVIDENCE_CONTRACT_SPECIFICATION.md)
- [Frozen canonical dataset and metric dictionary](docs/frozen/CANONICAL_DATASET_AND_METRIC_DICTIONARY.md)
- [Frozen architecture specification](docs/frozen/ARCHITECTURE_SPECIFICATION.md)

The frozen documents are historical governance authority for the project. This
README summarizes the current public v0.1.3 surface; it does not replace those
documents.

## Data Safety

The public example and fixture files are synthetic. Do not commit secrets,
private customer data, confidential employer data, API keys, credentials,
private URLs, or local runtime artifacts.

CommerceLens Public v0.1.3 does not claim enterprise security certification.

## License And Release

CommerceLens is licensed under the MIT License. See [LICENSE](LICENSE).

Package version: `0.1.3`

Public release: `CommerceLens v0.1.3`

Git tag: `v0.1.3`

CommerceLens is not currently published to PyPI and does not provide a hosted
SaaS product, REST API, or production cloud service.
