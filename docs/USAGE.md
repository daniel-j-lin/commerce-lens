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

## Revenue Meaning

Revenue means **post-discount eligible merchandise value**, excluding **tax and
shipping**, for the governed scope and period. It is **not accounting revenue
or cash collected**. The authoritative semantics remain in the
[Frozen Metric Dictionary §11](frozen/CANONICAL_DATASET_AND_METRIC_DICTIONARY.md#11-revenue-definition).
A canonical field name or confirmed source-to-canonical mapping does not mean
CommerceLens independently verified upstream business semantics. Source values
must conform to the canonical definition; renaming a field does not establish
that conformity.

## Evidence Required Before Material Claims

The existing Python `run_public_analysis` API accepts `available_evidence` and
`period_coverage_evidence`. Omitted or `None` inputs remain unknown and reach the
existing sufficiency gate as empty evidence. A requested period, required ID,
or earliest/latest transaction date does not establish source completeness.

The CLI accepts a bounded external declaration via `--coverage-declaration` under
the owner-approved F1-B policy below. Without it, the examples remain blocked.
Mapping confirmation alone does not establish coverage. Existing trusted Python
callers may continue supplying evidence separately; do not mix those inputs with
external declarations.

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

For retained local results, supply `--artifact-store` and `--metadata-store`
together. Supplying only one fails before analysis with a nonzero exit code.
Supplying neither retains the existing temporary mode: stores are removed when
the runner exits. Supplying both retains them. This does not change the default
retention policy or make stdout summaries a complete evidence bundle.

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

## F1-B USER_DECLARED coverage intake

Authority: [versioned owner amendment](amendments/F1-B-coverage-authority-v1.md).
Use the normal runner arguments plus `--prepare-coverage` after schema mapping
is resolved (select an XLSX sheet explicitly). The returned template binds the
DatasetRegistry ID and SHA-256 source bytes to the actual mapping/eligibility
context. Filename is for identification only. Preview never executes analysis.

The Skill separately asks for cutoff/source basis and shows file/sheet, inclusive
UTC dates, population, eligibility and exact filters. Only explicit Confirm of
that complete summary records the assertion. Correct requires another summary;
I don't know, vague replies and silence remain blocked. For programmatic Skill
hosts, call `coverage_intake.confirm_declaration(template, response="Confirm",
recorded_at=actual_utc_time, declaration_id=local_unique_id,
data_availability_cutoff=user_cutoff, source_basis_detail=user_basis)` and write
`model_dump_json()` to a temporary file. This helper records a declaration, not
trusted evidence; the runner still validates it. No personal identity is needed.

Add `--coverage-declaration /path/to/coverage.json` to the normal invocation.
The same validator accepts a manifest; v1 accepts one declaration or up to 16
consistent declarations, at most 64 KiB with duplicate keys rejected. Unknown
fields/provenance/policy and unresolved conflicting declarations fail closed.
A retained store also checks prior accepted declarations for that dataset.
There is no latest-wins or supersession policy in v1.

The schema is `CoverageDeclaration` in `commerce_lens.skill.coverage_intake`.
Policy `public_user_declared_coverage_v1` permits only USER_DECLARED. Explicit
`no_additional_filters` is required for an empty filter set. Filtered scopes must
match exactly; semantic subset inference is not supported. The declaration must
contain both required AnalysisRequest periods. Cutoff is an exclusive UTC instant
at/after midnight following coverage end and at/before recorded confirmation and
the current runtime clock. Known extraction must be between cutoff and recording.
Future/open periods cannot be attested as complete. Optional unknown extraction
requires a reviewed-export basis, not source min/max inference.

Coverage supplies only source authority. Separate mapping input authority and
existing canonicalization, currency, eligibility, sufficiency, execution,
validation and ClaimDecision checks remain mandatory. The trusted Python API
remains compatible. No new ClaimDecision state or permanent retention is added.

Results include `response.coverage_provenance` with the declaration and artifact
reference, and the visible disclosure: Coverage is based on a user-provided
declaration and has not been independently verified by CommerceLens.
Temporary store cleanup deletes that artifact; stdout carries the record but
does not establish persistent auditability. Use paired explicit stores only when
retention is wanted. Delete temporary declaration-input files after use.


V1's source basis is deliberately bounded: before confirmation, show the user
“I reviewed the export date range, population/status filters, all pages and export
completion status against this declaration.” Record the exact
`SOURCE_BASIS_ASSERTION` constant only if they explicitly confirm it. If this is
not their basis or they are uncertain, ask for clarification and remain blocked.
Do not paraphrase uncertain/free-form replies into the fixed assertion.
