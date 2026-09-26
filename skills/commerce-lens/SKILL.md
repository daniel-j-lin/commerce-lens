---
name: commerce-lens
description: "Evidence-governed commerce and e-commerce analytics for supported Public v0.1 CSV/XLSX questions, including Revenue, Orders, AOV, absolute Revenue Change, and one bounded product-mix diagnostic."
---

# CommerceLens Public v0.1 Skill

Use this Skill as a governed orchestration boundary for bounded commerce and
e-commerce structured-data analysis.

The Skill may decide what to ask. It must not decide what is true.

## Workflow

1. Interpret the user question into structured Public v0.1 intent.
2. Validate that the intent is within the approved question, Metric, source,
   period, scope, grouping, and Claim boundaries.
3. Request clarification when periods, source selection, or mapping authority
   are materially ambiguous.
4. Construct the existing governed `AnalysisRequest`.
5. Invoke `run_analysis(...)` through the CommerceLens application service.
6. Bind `ClaimCandidate` authority only from exact `AnalysisResult` references
   and persisted kernel authority.
7. Invoke `evaluate_claim(...)` for every material supported public Claim.
8. For `diagnostic_revenue_drop`, request only
   `product_composition_association`, require production R6
   `ELIGIBLE_NOT_EXECUTED`, then invoke the existing R7 service.
9. Consume only the independently validated and recursively authenticated R7
   terminal lineage.
10. Render only the Public Response Projection.

## Supported Public v0.1 Questions

Supported Metrics are exactly:

- `revenue`
- `orders`
- `aov`
- `revenue_change`

Supported analytical classes are exactly:

- single governed-period Revenue;
- single governed-period Orders;
- single governed-period AOV; and
- Revenue Change between two explicitly governed comparable periods; and
- the bounded `product_composition_association` test for a Revenue decline,
  using only `weekly_product_presence_revenue_association@1.0.0`.

Grouping is `NONE`.

Headline source workflows are CSV and XLSX. SQLite may remain available in the
kernel but is not a headline Public v0.1 workflow.

## Structured Intent Responsibility

The host interprets natural language and passes structured intent to the
integration layer. The integration layer validates that already-interpreted
intent fail-closed.

Do not implement or rely on a Python natural-language parser, keyword matcher,
generic SQL generator, arbitrary Python execution, or LLM-generated analytical
authority.

Intent may carry only minimum transient concepts such as question class, Metric
ID, explicit governed periods, scope, grouping, source selection, mapping
selection, and Claim intent.

Intent must not carry Metric formulas, calculated values, Evidence refs,
fingerprints, ValidatedResult refs, or ClaimDecision permission.

## Natural-Language Mapping

Natural-language interpretation belongs to the agent. The deterministic runner
accepts only already-interpreted structured arguments.

Map supported user requests as follows:

- "What was revenue/orders/AOV in Q4 2026?" maps to
  `question-class=single_period_metric`, `metric=revenue|orders|aov`,
  `result-period-role=comparison`, and explicit governed baseline/comparison
  periods.
- "How did revenue change from Q3 2026 to Q4 2026?" maps to
  `question-class=revenue_change`, `metric=revenue_change`, explicit governed
  baseline/comparison periods, and a descriptive Claim intent.
- "Why did revenue drop from Q3 2026 to Q4 2026?" maps to
  `question-class=diagnostic_revenue_drop`, `metric=revenue_change`, explicit
  governed baseline/comparison periods,
  `diagnostic-family=product_composition_association`, and one descriptive Claim
  intent. The descriptive Revenue Change may be shown only if permitted by
  CommerceLens authority. The diagnostic outcome may be shown only from the
  authenticated R7 terminal lineage and remains non-causal.

If the user has not provided a source file, source type, selected XLSX sheet
when needed, or explicit governed periods, ask for clarification. Unsupported
requests must not be approximated.

## Schema Mapping UX

After the source file is available, inspect the source headers before running
material analysis.

If all canonical fields required by the requested supported analysis are
available as exact canonical column names, continue without asking for mapping
confirmation. Exact identity mapping is already explicit under the CommerceLens
canonical contract.

If exact canonical fields are missing but semantically compatible source
headers appear available, propose a source-to-canonical mapping and ask the user
to confirm or correct it. The proposal is not authority. Do not run material
analysis until the user explicitly confirms or supplies the mapping.

The user may confirm all proposed mappings, correct one or more mappings,
decline the mapping, or supply a missing mapping. If ambiguity remains, ask a
targeted clarification such as which source column represents `line_revenue`.
Do not infer confirmation from silence.

When confirmed, hand the runner a structured source-to-canonical mapping with
source headers as keys and canonical fields as values. The runner converts this
to the existing `CanonicalMapping` contract, and CommerceLens deterministic
authority still validates it with `validate_mapping(...)` before analysis.

Fail closed when required mapping authority is unresolved, rejected, ambiguous,
or rejected by deterministic validation. Never fall back to LLM calculation,
silent renaming, guessed mapping, or generic dataframe analysis.

## Deterministic Runner

Missing evidence remains unknown. The existing Python `available_evidence` and
`period_coverage_evidence` inputs remain trusted programmatic-caller boundaries.
External user declarations use `--coverage-declaration path/to/coverage.json`
and the same deterministic validator for interactive confirmation and manifests.
Never construct trusted coverage/evidence objects from external user input.
Bare-file commands still block without accepted coverage. Request dates,
transaction min/max dates, mapping confirmation, and silence are not coverage.
The narrowly approved policy is documented in
`docs/amendments/F1-B-coverage-authority-v1.md`.

### Separate coverage confirmation

After identity mapping or explicit schema mapping confirmation, run the same
arguments with `--prepare-coverage`. This returns an unconfirmed template and a
confirmation summary; it does not execute analysis. For XLSX, explicitly select
the relevant sheet. Do not fill confirmation fields from the analytical question.
The proposed dates describe what to confirm, not evidence of completeness.

When the prompt or an attached participant/source context already supplies the
reviewed export facts, consume those facts as host context. In particular, do
not discard an explicit statement that the export has all pages and records,
includes paid orders, excludes cancelled orders, has no additional hidden
filters, and is complete through a stated UTC cutoff. Pass those facts to the
proposal preparation boundary as structured context (the runner accepts
`--coverage-context-json` or the equivalent `PublicCoverageContext` API). The
context is proposal input, not trusted Evidence.
Normalize an unambiguous explicit-timezone cutoff into the structured context;
for example, `2026-04-01 00:00 UTC` and `2026-04-01T00:00:00Z` denote the same
proposal fact and render canonically as `2026-04-01T00:00:00Z`. Never omit a
resolved cutoff merely because its source text is not already in canonical
rendering syntax. A timezone-free or otherwise ambiguous cutoff remains
unresolved and requires targeted clarification.

Assemble one complete proposal containing the actual source binding, requested
periods, population and eligibility semantics, explicit filters (including
none), all-pages/all-record completeness basis, data-availability cutoff, and
the disclosure that coverage authority is `USER_DECLARED` and source
completeness has not been independently verified by CommerceLens.
Do not infer facts from filenames, platforms, request dates, observed dates, or
current time. If a required fact is missing, ambiguous, contradictory, or
outside scope, ask only for that fact, rebuild the proposal, and show the
complete proposal again.

Present a concise separate coverage summary, for example:

> File: orders.csv; sheet: none. Period: 1 July–31 December 2026, inclusive UTC
> dates. Population: all eligible order lines (paid included; cancelled excluded).
> Additional filters: none. Data complete through: [user-supplied cutoff].
> Coverage is based on your declaration and has not been independently verified
> by CommerceLens. Choose **Confirm**, **Correct**, or **I don't know**.

Use actual values from the prepared summary and the user's cutoff/basis. For a
filtered scope enumerate the exact filters. Do not merge this question with
“This column means Revenue”. Source values must separately conform to the
canonical Revenue definition; coverage never establishes Revenue semantics.

If the complete proposal was assembled, display it once and ask only:
“請確認以上資訊是否正確。” A plain affirmative such as `確認` is sufficient
at the host layer; no special coverage phrase or repeated completeness question
is required. If a fact is genuinely missing, ask only for that fact and rebuild
the complete proposal before requesting confirmation.
Use the runner/API `confirmation_text` as the host-facing rendering of the
prepared proposal. Never iterate over `coverage_facts`, `missing_facts`, or
other proposal fields to create one yes/no/unknown question per field. A
complete context must render declarative statements once; an incomplete
context must mention only the genuinely missing facts and remain fail-closed
until they are supplied.

Only one explicit confirmation of the complete summary may record an attestation.
The host may normalize `確認`, `沒問題`, `照這個執行`, `Yes`, or `Looks right`
to the canonical structured intent `confirmation_intent="confirmed"`. Do not
pass arbitrary free-form language to the deterministic authority layer.
“Correct”, uncertainty, silence, or a negative response invalidates the prior
proposal and requires a rebuilt summary; none of these may confirm it.

After confirmation compute the proposal fingerprint with
`coverage_proposal_fingerprint(...)` over the exact complete proposal and use
`commerce_lens.skill.coverage_intake.confirm_declaration`
with the prepared `declaration_template`,
`confirmation_intent="confirmed"`, the exact requested baseline/comparison
periods, the fingerprint, a local unique declaration ID, actual UTC recorded
time, the user-supplied cutoff, optional extraction time and optional local
session ref. The canonical `SOURCE_BASIS_ASSERTION` is
derived from the displayed and confirmed completeness facts; the user does not
need to repeat a separate audit ritual.
Serialize the resulting untrusted declaration with `model_dump_json()` into a
local temporary file, then pass `--coverage-declaration` to the normal runner.
The helper rejects incomplete, stale, mismatched, or unbound proposals; the
runner independently validates current dataset bytes, sheet/type,
mapping/eligibility context, scope/filters, closed dates, cutoff and provenance
before projecting coverage into the existing engine.
A standalone manifest must provide the identical versioned declaration schema;
never accept a user assertion of EXTERNALLY_VERIFIED, SOURCE_DECLARED or TEST_FIXTURE.

`--prepare-coverage` leaves confirmation, ID, time, cutoff and basis unset on
purpose. Do not use its JSON as accepted evidence. No `--complete` bypass exists.
V1 supports only `order_date_utc` inclusive dates and a cutoff at/after the next
UTC midnight following coverage end, no later than the actual confirmation/run.
As of September 2026, Q4 2026 is open and cannot pass this check.

Render the runner's provenance disclosure alongside every dependent result.
Temporary runs delete local artifacts, including the declaration; remove the
Skill's temporary input file when finished.

Retention is a host orchestration decision that must be made before execution.
If the user explicitly asks in natural language to retain the full evidence for
later inspection, the host must pass the structured `--retain-evidence` control
and a configured local `--retention-root ROOT` to the runner. Do not infer this
from a request to merely show, summarize, or cite evidence, and do not parse
the prose inside the deterministic runner. The runner then enters the existing
F2-A lifecycle before analysis, finalizes its self-contained package, verifies it
from disk, and reports `retained_complete` only after the completion marker is
written. If finalization fails, report the retention failure and do not present
the result as retained. Without that explicit host control, keep the temporary
default unchanged. A retained package contains the manifest, raw snapshot,
canonical data, metadata, AnalysisResult, PublicResponse, and linkage. It has
no TTL and remains until the user deletes that selected run. Verification does
not replay analysis; deletion is not secure erase and never targets the
original source. See
`docs/amendments/F2-A-evidence-persistence-retention-v1.md`.

Use `skills/commerce-lens/scripts/run_public_analysis.py` as the first-run
command surface. It translates structured arguments into:

- `PublicAnalysisIntent`
- `PublicSourceSelection`
- `run_public_analysis(...)`

The runner automatically creates temporary `ArtifactStore` and `MetadataStore`
locations when none are supplied. These are implementation details; the user
does not need to construct them.

If explicit component store paths are supplied, `--artifact-store` and
`--metadata-store` must be supplied together; one alone fails before analysis.
They preserve low-level component records for compatibility but are not a
`retained_complete` F2-A package. Use `--retention-root` for explicit retained
evidence and the list/inspect/verify/delete operations.

Example:

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
  --source path/to/orders.csv \
  --source-type csv \
  --question-class revenue_change \
  --metric revenue_change \
  --baseline-label "Q3 2026" \
  --baseline-start 2026-07-01 \
  --baseline-end 2026-09-30 \
  --comparison-label "Q4 2026" \
  --comparison-start 2026-10-01 \
  --comparison-end 2026-12-31 \
  --mapping-json '{"Order ID":"order_id","Order Line ID":"order_line_id","Order Date":"order_date","Product ID":"product_id","Quantity":"quantity","Revenue":"line_revenue","Currency":"currency","Order Status":"eligibility_status"}'
```

For first use, verify Python >=3.11. If CommerceLens cannot be imported, create
an isolated environment, install the local package, and invoke the runner from
that environment:

```bash
python3.11 -m venv .venv-commerce-lens-skill
.venv-commerce-lens-skill/bin/python -m pip install --upgrade pip
.venv-commerce-lens-skill/bin/python -m pip install -e "."
.venv-commerce-lens-skill/bin/python skills/commerce-lens/scripts/run_public_analysis.py ...
```

Do not hide bootstrap failures. If Python >=3.11 or package dependencies cannot
be installed, report the installation/runtime failure. Never respond by having
the LLM calculate material metrics itself.

## Evidence and Claim Authority

No material claim may be presented without traceable evidence from the
deterministic CommerceLens engine.

Material Metric values must come from the deterministic runner. The Skill must
not calculate Revenue, Orders, AOV, Revenue Change, or any derivative value.

Diagnostic `ClaimDecision` promotion, causal, predictive, and prescriptive
claims remain fail-closed under Public v0.1. The one supported R7 analytical
outcome is not a Claim or Finding. Unsupported requests must not be approximated.

For questions such as "Why did revenue drop from Q3 2026 to Q4 2026?", keep
the supported descriptive Revenue Change Claim separate from the R7 analytical
outcome. The descriptive portion proceeds through `run_analysis(...)` and
`evaluate_claim(...)`. The diagnostic portion proceeds only through production
R6 eligibility, the approved R7 method, independent R7 validation, and complete
lineage authentication. If R6 is not eligible or authentication fails, return
“Insufficient evidence to conclude.” and identify the exact blocker. Do not list
speculative causes.

## Response Rendering

Render supported material Claims only when an authoritative `ClaimDecision`
permits them.

Keep Metric State, Claim State, and public support disposition distinct. AOV
with Orders equal to zero is MetricState `UNDEFINED`, value `None`, and
`undefined_reason` `orders_equals_zero`; this is not numeric zero.

The public response may include Supported Claims / Answer, bounded Diagnostic
Analysis, Evidence Summary, Metric State, Claim Status, Limitations, Unsupported
Conclusions, Additional Evidence Needed, Clarification Required, and Blocked /
Insufficient Evidence.

For `CRITERION_MET`, state that larger product-mix changes and lower weekly
revenue show a consistent relationship and that product mix is one possible
explanation under the current test. Immediately state that this does not prove
causation or establish the only or primary reason. For `CRITERION_NOT_MET`, say
the method did not reach its support threshold; do not say there was no effect.
For `PROPOSITION_CONTRADICTED`, describe only the opposite direction of the
tested relationship. For `NOT_EVALUATED`, name the exact inconclusive reason.

Do not create new Metric values, formulas, Evidence, validation results,
Findings, Alternative Explanations, or Recommendations in the response.


V1's source basis remains deliberately bounded: display the governed
completeness basis as part of the proposal and record the exact
`SOURCE_BASIS_ASSERTION` constant only when the complete proposal is explicitly
confirmed. If the basis is missing or uncertain, ask for clarification and
remain blocked. Do not paraphrase uncertain/free-form replies into the fixed
assertion.
