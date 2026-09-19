---
name: commerce-lens
description: "Evidence-governed commerce and e-commerce analytics for supported Public v0.1 structured-data questions over CSV/XLSX files, including Revenue, Orders, AOV, and absolute Revenue Change."
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
8. Render only the Public Response Projection.

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
- Revenue Change between two explicitly governed comparable periods.

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
  governed baseline/comparison periods, one descriptive Claim intent, and one
  diagnostic Claim intent. The descriptive Revenue Change may be shown only if
  permitted by CommerceLens authority. The diagnostic explanation must be
  refused under Public v0.1.

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

Ask the user for the data-availability cutoff and how they know the export is
complete (reviewed export range, pagination and status/filter controls). Do not
infer these from filenames, platforms, observed dates, or current time. Unknown
cutoff or source basis requires clarification. No names, email, credentials or
identity verification are needed. Extraction time is optional when unknown.

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

Only an explicit **Confirm** to the complete summary may record an attestation.
“Correct” means revise the summary and ask again. “I don't know if this export is
complete”, silence, “probably”, “I think so” and “should be complete” leave coverage
unknown: report clarification/blocked and no material result. Do not translate
uncertainty into Confirm.

After confirmation use `commerce_lens.skill.coverage_intake.confirm_declaration`
with the prepared `declaration_template`, exact response `Confirm`, a local
unique declaration ID, actual UTC recorded time, the user-supplied cutoff,
source-basis detail, optional extraction time and optional local session ref.
Serialize the resulting untrusted declaration with `model_dump_json()` into a
local temporary file, then pass `--coverage-declaration` to the normal runner.
The helper rejects non-confirmation; the runner independently validates current
dataset bytes, sheet/type, mapping/eligibility context, scope/filters, closed dates,
cutoff and provenance before projecting coverage into the existing engine.
A standalone manifest must provide the identical versioned declaration schema;
never accept a user assertion of EXTERNALLY_VERIFIED, SOURCE_DECLARED or TEST_FIXTURE.

`--prepare-coverage` leaves confirmation, ID, time, cutoff and basis unset on
purpose. Do not use its JSON as accepted evidence. No `--complete` bypass exists.
V1 supports only `order_date_utc` inclusive dates and a cutoff at/after the next
UTC midnight following coverage end, no later than the actual confirmation/run.
As of September 2026, Q4 2026 is open and cannot pass this check.

Render the runner's provenance disclosure alongside every dependent result.
Temporary runs delete local artifacts, including the declaration; remove the
Skill's temporary input file when finished. Explicit paired stores preserve
local records only at the user's chosen location. Do not promise permanent
retention or cross-run auditability after temporary cleanup.

Use `skills/commerce-lens/scripts/run_public_analysis.py` as the first-run
command surface. It translates structured arguments into:

- `PublicAnalysisIntent`
- `PublicSourceSelection`
- `run_public_analysis(...)`

The runner automatically creates temporary `ArtifactStore` and `MetadataStore`
locations when none are supplied. These are implementation details; the user
does not need to construct them.

If explicit store paths are supplied, `--artifact-store` and `--metadata-store`
must be supplied together; one alone fails before analysis. Both preserve
results, while neither preserves the existing temporary cleanup behavior.

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

Diagnostic, causal, predictive, and prescriptive claims remain fail-closed
under Public v0.1. Unsupported requests must not be approximated.

For questions such as "Why did revenue drop from Q3 2026 to Q4 2026?", keep
the supported descriptive Revenue Change proposition separate from the
unsupported diagnostic proposition. The descriptive portion may proceed through
`run_analysis(...)` and `evaluate_claim(...)`. The diagnostic portion must be
submitted only as an unsupported Claim intent and rendered as refused if the
ClaimDecision is inadmissible.

Use this exact bounded refusal where applicable:

Insufficient evidence to conclude why Revenue declined.

Do not list speculative causes.

## Response Rendering

Render supported material Claims only when an authoritative `ClaimDecision`
permits them.

Keep Metric State, Claim State, and public support disposition distinct. AOV
with Orders equal to zero is MetricState `UNDEFINED`, value `None`, and
`undefined_reason` `orders_equals_zero`; this is not numeric zero.

The public response may include Supported Claims / Answer, Evidence Summary,
Metric State, Claim Status, Limitations, Unsupported Conclusions, Additional
Evidence Needed, Clarification Required, and Blocked / Insufficient Evidence.

Do not create new Metric values, formulas, Evidence, validation results,
Findings, Alternative Explanations, or Recommendations in the response.


V1's source basis is deliberately bounded: before confirmation, show the user
“I reviewed the export date range, population/status filters, all pages and export
completion status against this declaration.” Record the exact
`SOURCE_BASIS_ASSERTION` constant only if they explicitly confirm it. If this is
not their basis or they are uncertain, ask for clarification and remain blocked.
Do not paraphrase uncertain/free-form replies into the fixed assertion.
