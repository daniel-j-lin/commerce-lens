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

## Unsupported Handling

Reject or refuse unsupported requests, including:

- Revenue Change percentage;
- Product or Category analysis;
- ranking, Finding, AlternativeExplanation, or Recommendation;
- Diagnostic `ClaimDecision` promotion, Causal, Predictive, or Prescriptive conclusions;
- arbitrary tabular analytics; and
- external connectors, APIs, or web Evidence.

For questions such as "Why did revenue drop from Q3 2026 to Q4 2026?", keep
the supported descriptive Revenue Change Claim separate from the R7 analytical
outcome. The descriptive portion proceeds through `run_analysis(...)` and
`evaluate_claim(...)`. The diagnostic portion proceeds only through production
R6 eligibility, the approved R7 method, independent R7 validation, and complete
lineage authentication. It is not a Claim or Finding.

Retention is decided by the host before execution. When the user explicitly
asks to retain the full evidence for later inspection, the host passes the
structured `--retain-evidence` control together with a configured
`--retention-root`; the deterministic runner does not parse natural-language
retention requests. Without that explicit control, the temporary default is
unchanged. A failed retained finalization must be surfaced as a retention
failure and never presented as `retained_complete`.

Formal retained mode writes the completion marker only after persistence
integrity passes. A completed retained run must remain available across
processes through the governed `list`, `inspect`, and `verify` operations.
These operations establish persistence integrity only: retention never upgrades
`USER_DECLARED`, changes a `ClaimDecision`, or makes an analytical claim more
correct. Without an explicit retention request, use temporary mode and create no
retained run.

If R6 is not eligible or authentication fails, use this bounded refusal and
identify the exact blocker:

Insufficient evidence to conclude.

Do not list speculative causes.

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

## Consolidated coverage confirmation

Schema mapping confirmation and coverage confirmation remain separate. After
mapping is resolved, the host assembles one complete structured coverage
proposal containing the source binding, requested periods, scope, population and
eligibility, explicit filters, completeness basis, data-availability cutoff, and the
USER_DECLARED disclosure. The host displays that proposal once and may
normalize ordinary affirmative language to the canonical
`confirmation_intent="confirmed"` value. Corrections, uncertainty, negatives,
missing facts, ambiguity, contradiction, and scope mismatch invalidate the prior
proposal and require a rebuilt proposal.

The deterministic intake layer is language-agnostic. It requires the exact
proposal fingerprint and validates the proposal against the current dataset,
mapping context, scope, periods, cutoff, and clock before creating
`USER_DECLARED` authority. A generic affirmative, request dates, or dataset
min/max dates never supply missing coverage facts. Coverage remains
`USER_DECLARED`, never `EXTERNALLY_VERIFIED`, and retains the existing
disclosure that source completeness has not been independently verified by
CommerceLens.

When the host already has reviewed source context, it must pass that context to
proposal preparation and render one complete proposal containing all-pages/all-
records completeness, paid-included and cancelled-excluded status semantics, no
additional hidden filters, the UTC cutoff, source/scope binding, and the
independent-verification disclosure. Once complete, the only follow-up is
`請確認以上資訊是否正確。`; ordinary `確認` is normalized to the canonical
confirmation intent. If a required fact is absent, ask only for that fact.
Normalize an unambiguous explicit-timezone cutoff into the structured context;
for example, `2026-04-01 00:00 UTC` and `2026-04-01T00:00:00Z` denote the same
proposal fact and render canonically as `2026-04-01T00:00:00Z`. A timezone-free
or otherwise ambiguous cutoff remains unresolved and requires clarification.
Use the prepared `confirmation_text` as the single host-facing rendering. Do
not turn `coverage_facts` or `missing_facts` into separate yes/no/unknown
questions. Complete context is rendered as declarative statements once;
genuinely missing context is listed narrowly and remains fail-closed.
