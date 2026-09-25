# R7-001 — First Diagnostic Method Authority

Status: Owner-authorized R7 MVP authority  
Scope: exactly one private diagnostic method; no public or Claim permission  
Authority version: 1.0.0

## Authority identities

| Authority | ID | Version | Semantic fingerprint |
|---|---|---|---|
| Method | `weekly_product_presence_revenue_association` | `1.0.0` | `6bfabecae8a1c0ba57f9559dedafeed54fb201868af0e13d94542e219e843d15` |
| Support criterion | `weekly_product_presence_revenue_association_support` | `1.0.0` | `68496a1db32deab4f55156469b71365d513b8c00baa815218592adee43c9286f` |
| Validation profile | `weekly_product_presence_revenue_association_validation` | `1.0.0` | `9358e04c31ad63b09ade90fe047d10eb8f580f722a3c39352eced8d00b4d659d` |
| Implementation binding | `commerce_lens_r7_weekly_product_presence_revenue_association` | `1.0.0` | `253d92baa3a87aefdd037d306db068a328fc1932d28df7f5a89f895109eb7e3c` |

The method binds only `product_composition_association@1.0.0`, family fingerprint
`757eae48d3b72d2caa83e3d614b5fd50eccf34f1a4c9d11d0a24bdb06fadead2`.
Its relationship is a bounded, observed, non-causal association with expected
negative direction. It is private diagnostic execution authority, not Finding or
Claim authority.

## Inputs and observation construction

Required roles are observed outcome, explanatory variable, population
eligibility, completeness/coverage, source authority/provenance, identity/join,
and unit/currency. Inputs must be diagnostically admitted governed internal
canonical evidence with exact `product_id`, `line_revenue`, `order_date`,
eligibility, scope, period, population, currency, and provenance authority.

The observation unit is one ISO-8601 calendar week, Monday through Sunday,
derived directly from canonical `order_date`. Timestamp conversion is forbidden;
canonical upstream date/timezone authority remains controlling. A week is used
only when all seven dates lie wholly inside either the governed Baseline period or
the governed Comparison period. Partial weeks are excluded with a reason.

`baseline_product_set` is every distinct governed `product_id` on eligible lines
in the entire Baseline period. For valid week `w`, `weekly_product_set(w)` is every
distinct governed `product_id` with at least one eligible line in that week. No
Revenue, price, quantity, AOV, ranking, top-N, product name, or R4 contribution is
used to construct either set.

## Deterministic method

For each valid full week:

```text
JaccardDistance(w)
= 1 - |weekly_product_set(w) intersection baseline_product_set|
      / |weekly_product_set(w) union baseline_product_set|

WeeklyRevenue(w)
= sum governed eligible line_revenue in w

BaselineWeeklyRevenueReference
= median WeeklyRevenue across valid full Baseline weeks

WeeklyRevenueDeviation(w)
= WeeklyRevenue(w) - BaselineWeeklyRevenueReference
```

Two empty product sets make the observation invalid. Jaccard distance must be
finite and in `[0, 1]`. Revenue retains the frozen single-currency, eligible-line,
full-precision Decimal semantics. The median is the middle value for odd counts
and the exact Decimal average of the two middle values for even counts.

Rank each vector in ascending order using deterministic average ranks for ties.
Compute Pearson correlation over the two rank vectors. Spearman `rho` uses
Python/IEEE-754 binary64 arithmetic after exact deterministic ranks; no rounding
is applied before criterion evaluation. Output must be finite and within
`[-1, 1]` (allowing only machine-level clamping when recomputation differs from a
boundary by no more than `1e-15`). No p-value, interval, alpha, probability, or
statistical-significance claim exists.

## Parameters, missingness, weighting, and minimums

The method has no caller-configurable analytical parameters. Its fixed parameters
are ISO full weeks, minimum 8 valid weeks, minimum 4 Baseline weeks, minimum 4
Comparison weeks, negative support boundary `-0.50`, and positive contradiction
boundary `+0.50`.

No imputation, interpolation, forward fill, or manufactured zero-Revenue week is
permitted. A valid week requires authenticated date membership, constructible
eligible population, a non-empty product set, and calculable Revenue. Every
excluded week and reason is retained. Every valid week has weight one; Revenue,
orders, products, lines, and days never weight observations.

## Outcomes

After independent validation:

```text
rho <= -0.50              -> CRITERION_MET
-0.50 < rho < +0.50       -> CRITERION_NOT_MET
rho >= +0.50              -> PROPOSITION_CONTRADICTED
```

Use `NOT_EVALUATED` plus R7 state `INCONCLUSIVE` for fewer than 8 total valid
weeks, fewer than 4 valid weeks in either period, a constant vector, undefined
Spearman denominator, or method-required observation construction that cannot be
completed. Inconclusive is neither non-support nor Missing Evidence by default.

## Validation profile

Independent validation authenticates all authority/request/evidence bindings and
recomputes: ISO full-week membership; Baseline product set; weekly set
fingerprints; Jaccard values/domain; weekly Revenue and currency reconciliation;
Baseline median; deviations; average ranks and ties; Spearman numerator,
denominator, and rho; sample counts; vector variation; criterion boundary; and
semantic result fingerprint. Executed Result is never Validated Result.

## Interpretation boundary

Maximum meaning:

> Across the governed weekly observations, greater product-presence composition
> distance was associated with lower weekly Revenue performance under the
> approved R7 method. This supports product composition as one plausible
> contributor worth retaining in the diagnostic explanation.

It never means causality, sole/primary explanation, counterfactual effect,
customer preference, pricing/discount, demand, inventory, generalization,
statistical significance, Finding, or Claim permission. The method does not
control time trend, seasonality, promotion timing, inventory, external shocks,
customer mix, or other confounders. Alternative explanations remain
`NOT_COMPLETED`.

## Implementation and conformance authority

The implementation binding is the single static Python-standard-library plus
existing-DuckDB implementation. It permits no plugin discovery and no model/LLM
calculation. Changes to bucketing, formulas, ranks, arithmetic, thresholds,
minimums, exclusions, weighting, or meanings require a new authority version.

`FX-R7-PROD-001A` and all `fixtures/r7` chains are directly authorized **TEST /
CONFORMANCE AUTHORITY ONLY — NOT PRODUCTION R6 OUTPUT**. They may contain an
authenticated `ELIGIBLE_NOT_EXECUTED` handoff solely to exercise R7. Production
R6 remains unchanged and may produce zero executable hypotheses.
