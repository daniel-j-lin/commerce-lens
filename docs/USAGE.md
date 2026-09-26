# CommerceLens Public Usage

This document keeps operational details out of the main README while preserving
the current CommerceLens v0.3.1 usage surface while preserving the Public v0.1
analytical contract.

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
fresh Codex session, provide a CSV or XLSX file and ask a supported question.

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

CommerceLens v0.3.1 supports:

- single-period Revenue;
- single-period Orders;
- single-period AOV;
- Revenue Change between two explicitly governed comparable periods.
- the bounded `product_composition_association` diagnostic for Revenue decline,
  using `weekly_product_presence_revenue_association@1.0.0` when the governed
  evidence and full-week requirements are met.

Grouping is `NONE`. Positive material claims remain descriptive. A validated
diagnostic outcome is rendered only as a bounded non-causal possible
explanation; it is not a `ClaimDecision`, sole/primary-cause finding,
statistical-significance claim, confidence score, or recommendation.

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
API in CommerceLens v0.3.1. The repository includes a deterministic runner script used
by the Skill and developer verification.

The default is temporary: without `--retention-root`, isolated stores are
removed when the runner exits. When a user explicitly asks the host to retain
the full evidence for later inspection, the host passes `--retain-evidence`
and `--retention-root ROOT` before analysis. The package is written under
`ROOT/<run_id>/` with `manifest.json`, `complete.marker`, `artifacts/`, and
`metadata.sqlite`; finalization failure exits nonzero and is never reported as
complete. The deterministic runner does not parse the user's prose; the host
must make the explicit retention decision before invoking it.

`--artifact-store` and `--metadata-store` remain a paired low-level component
store interface for compatibility. They are not the F2-A retained-run package
and are reported as legacy/incomplete for retention purposes. Supplying only
one fails before analysis.

Use `--list-retained`, `--inspect-run RUN_ID`, `--verify-run RUN_ID`, and
`--delete-run RUN_ID` with `--retention-root` for cross-process operations.
Verification reads stored data only; it does not replay or rerun analysis.
Retention is local plaintext storage without TTL, encryption, or secure erase.

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

For the supported diagnostic, use `--question-class diagnostic_revenue_drop`,
`--metric revenue_change`, and optionally
`--diagnostic-family product_composition_association`. The runner preserves the
descriptive Revenue Change answer, calls the governed R6 and R7 services, and
renders only the independently validated and recursively authenticated terminal
result. Missing `product_id`, incomplete weekly evidence, non-eligible R6
handoffs, unsupported families, or failed lineage authentication fail closed.

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

The Skill assembles one complete proposal showing file/sheet, inclusive UTC
dates, population, eligibility, exact filters, all-pages/all-records
completeness basis, and cutoff. Only one explicit confirmation of that exact
summary records the assertion. Missing, ambiguous, or contradictory facts
trigger targeted clarification only. Host language such as `確認`, `沒問題`, or
`Yes` is normalized to `confirmation_intent="confirmed"`; arbitrary free-form
text is not sent to deterministic intake. For programmatic Skill hosts, compute
`coverage_intake.coverage_proposal_fingerprint(template,
requested_periods=(baseline_period, comparison_period),
data_availability_cutoff=user_cutoff)`, then call
`coverage_intake.confirm_declaration(template,
confirmation_intent="confirmed", proposal_fingerprint=proposal_fingerprint,
requested_periods=(baseline_period, comparison_period),
recorded_at=actual_utc_time, declaration_id=local_unique_id,
data_availability_cutoff=user_cutoff)` and write `model_dump_json()` to a
temporary file. This helper records a declaration, not trusted evidence; the
runner still validates it. No personal identity is needed.

For a reviewed export, proposal preparation may receive structured host context:

```bash
python3.11 skills/commerce-lens/scripts/run_public_analysis.py \
  --source validation/p15/data/P15-A-governed-marketplace.csv \
  --source-type csv \
  --question-class revenue_change \
  --metric revenue_change \
  --baseline-label "Q1 2025" \
  --baseline-start 2025-01-01 \
  --baseline-end 2025-03-31 \
  --comparison-label "Q1 2026" \
  --comparison-start 2026-01-01 \
  --comparison-end 2026-03-31 \
  --mapping-file path/to/confirmed-mapping.json \
  --prepare-coverage \
  --coverage-context-json '{"all_pages_included":true,"all_records_included":true,"paid_included":true,"cancelled_excluded":true,"no_additional_hidden_filters":true,"data_availability_cutoff":"2026-04-01T00:00:00Z"}'
```

A complete response contains one declarative `confirmation_text` ending in
`請確認以上資訊是否正確。`. Plain `確認` is sufficient at the host layer. The host
must not ask for `確認完整性`, `確認完整匯出`, `Confirm coverage`, or `Confirm
complete export`. If only the cutoff is missing, ask only for the cutoff; do not
repeat already resolved pages, records, status, or filter questions. A
timezone-free or contradictory cutoff fails closed.

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
remains compatible. No new ClaimDecision state is added. Explicit retained mode
uses the separate F2-A lifecycle; temporary remains the default.

Results include `response.coverage_provenance` with the declaration and artifact
reference, and the visible disclosure: Coverage is based on a user-provided
declaration and has not been independently verified by CommerceLens.
Temporary store cleanup deletes that artifact; stdout carries the record but
does not establish persistent auditability. Use the explicit F2-A retention
root when a self-contained local evidence package is wanted. Delete temporary
declaration-input files after use. See the [F2-A amendment](amendments/F2-A-evidence-persistence-retention-v1.md).


V1's source basis is deliberately bounded: show the governed completeness basis
inside the consolidated proposal and derive the exact `SOURCE_BASIS_ASSERTION`
from that confirmed proposal. The user does not need to repeat the same audit
wording separately. If the basis is missing or uncertain, ask for clarification
and remain blocked. Do not paraphrase uncertain/free-form replies into the fixed
assertion.

## Common blocked outcomes and diagnostic limits

- Missing or unconfirmed mapping: clarify or confirm the mapping; do not run
  material analysis.
- Missing coverage facts: ask only for the unresolved facts; do not infer them
  from request dates, observed dates, row count, or filename.
- Stale proposal fingerprint: rebuild and redisplay the complete proposal.
- Unknown Dataset B-style coverage: remain blocked with zero supported material
  claims.
- Retention finalization failure: report the failure; never emit
  `retained_complete`.
- Diagnostic “why” request: the descriptive Revenue Change may still be supported.
  The diagnostic explanation proceeds only when production R6 returns an
  authenticated `ELIGIBLE_NOT_EXECUTED` handoff and the approved R7 result
  passes independent validation and lineage authentication. If those
  requirements are not met, CommerceLens returns
  `Insufficient evidence to conclude.` and identifies the blocking evidence
  or eligibility requirement.
