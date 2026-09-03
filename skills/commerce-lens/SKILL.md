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

## Deterministic Runner

Use `skills/commerce-lens/scripts/run_public_analysis.py` as the first-run
command surface. It translates structured arguments into:

- `PublicAnalysisIntent`
- `PublicSourceSelection`
- `run_public_analysis(...)`

The runner automatically creates temporary `ArtifactStore` and `MetadataStore`
locations when none are supplied. These are implementation details; the user
does not need to construct them.

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
