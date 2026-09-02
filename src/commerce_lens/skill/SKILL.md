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

## Unsupported Handling

Reject or refuse unsupported requests, including:

- Revenue Change percentage;
- Product or Category analysis;
- contribution, ranking, Finding, AlternativeExplanation, or Recommendation;
- positive Diagnostic, Causal, Predictive, or Prescriptive conclusions;
- arbitrary tabular analytics; and
- external connectors, APIs, or web Evidence.

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
