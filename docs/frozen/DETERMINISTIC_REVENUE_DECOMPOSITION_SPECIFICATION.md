# CommerceLens AI Deterministic Revenue Decomposition Specification

**Document:** `DETERMINISTIC_REVENUE_DECOMPOSITION_SPECIFICATION.md`

**Milestone:** R4 — Deterministic Revenue Decomposition

**Method family:** Product-Level Revenue Decomposition

**Version:** R4 v1.0

**Status:** Approved

**State:** Frozen

**Date:** 2026-09-22

**Project:** CommerceLens AI

**Public-product compatibility:** CommerceLens AI v0.2.0 and Public v0.1 behavior unchanged

---

## 1. Purpose

This specification defines the minimum deterministic, mathematically exact, semantically bounded Revenue decomposition method that CommerceLens may later implement.

R4 answers one bounded question:

> How is an observed authoritative Revenue difference mechanically classified across products?

R4 v1 classifies an authoritative Revenue Change between an explicit Baseline Period and Comparison Period into three additive components over the complete governed product universe:

1. Entry Component;
2. Exit Component; and
3. Continuing-Product Revenue Change Component.

The method is deterministic arithmetic. It does not determine why Revenue changed. It does not identify a business driver, cause, root cause, motive, demand condition, pricing action, discounting behavior, assortment strategy, or intervention effect.

This specification establishes method semantics only. It does not make the method executable and does not authorize implementation.

---

## 2. Scope

R4 v1 defines:

- a separately identified and versioned Product-Level Revenue Decomposition method family;
- its authoritative inputs and mechanical execution-eligibility boundary;
- its period, population, scope, currency, and product-identity preconditions;
- the complete product universe and deterministic Entry, Exit, and Continuing partition;
- product-level and aggregate component semantics;
- the exact decomposition and reconciliation identities;
- central precision and rounding requirements applicable to the method;
- required product-level traceability;
- independent deterministic validation obligations;
- eligibility, execution, and validation failure distinctions;
- bounded mechanical wording;
- diagnostic reuse restrictions;
- method-versioning and evaluator-conformance requirements; and
- future R5 fixture obligations at specification level only.

R4 operates on frozen Revenue, Product Revenue, Product Revenue Change, and Product Absolute Contribution authority. It does not redefine those Metrics.

---

## 3. Non-Scope

R4 v1 does not define or authorize:

- Price × Quantity decomposition;
- Quantity × Realized Unit Value decomposition;
- `Revenue / Quantity` as an active method input;
- a quantity, volume, price, pricing, discount, demand, mix, unit-value, or interaction component;
- Shapley, symmetric, path-order, or other interaction allocation;
- a normal residual or unexplained component;
- diagnostic support or contradiction criteria;
- causal identification;
- `CRITERION_MET` or any other R2 Analytical Outcome;
- a Supported Diagnostic Finding;
- positive diagnostic or causal `ClaimDecision` permission;
- a new canonical field, dataset grain, population, Metric, refund model, product-master model, or currency-conversion model;
- a runtime contract, schema, enum, class, migration, SQL statement, Python implementation, validation implementation, fixture, or test;
- a new CLI command, dashboard, public Skill behavior, or response format;
- any v0.2.0 or Public v0.1 behavior change; or
- R5 or R6 execution.

R4 v1 may identify future extension boundaries. It must not define the deferred method behind those boundaries.

---

## 4. Frozen Authorities

R4 is subordinate to and preserves the Approved / Frozen authorities under `docs/frozen/`, especially:

- `PROJECT_MASTER_INSTRUCTIONS.md`;
- `DIAGNOSTIC_REASONING_SPECIFICATION.md` (R1);
- `HYPOTHESIS_FINDING_STATE_MODEL_SPECIFICATION.md` (R2);
- `REQUIRED_EVIDENCE_MATRIX_SPECIFICATION.md` (R3);
- `EVIDENCE_CONTRACT_SPECIFICATION.md`;
- `ARCHITECTURE_SPECIFICATION.md`;
- `CANONICAL_DATASET_AND_METRIC_DICTIONARY.md`; and
- `EVALUATION_FIXTURES_SPECIFICATION.md`.

R4 also preserves the current repository authorities for:

- the Metric Registry;
- canonical order-line records and canonicalization;
- governed population definitions;
- Revenue and Revenue Change execution and validation;
- execution, validation, evidence-admissibility, and `ClaimDecision` contracts;
- exact Decimal and presentation-rounding conventions;
- immutable retained artifacts, content fingerprints, and provenance; and
- current Public v0.1 scope.

If R4 text conflicts with a higher frozen authority, the higher authority controls and the conflicting R4 text is non-conforming.

The current Metric Registry includes Product Revenue, Product Revenue Change, and Product Absolute Contribution definitions. Current production execution, validation, evidence admission, and material Claim permission remain implemented only for Revenue, Orders, AOV, and Revenue Change. This specification does not convert registered-but-unimplemented product Metrics into executable capabilities.

---

## 5. Governing Distinctions

The following distinctions are binding:

```text
Mechanical Decomposition != Diagnostic Explanation
Mechanical Contribution != Causal Contribution
Mechanical Contribution != Diagnostic Driver
Product presence classification != product lifecycle fact
Validated Decomposition Result != Supported Diagnostic Finding
Method Result != Analytical Outcome
Method Result != Claim authorization
Mechanical execution eligibility != diagnostic-input admissibility
Validated R4 result != diagnostic-input admissibility
Diagnostic-input admissibility != diagnostic support
Executed Result != Validated Result
Validated Result != AdmissibleEvidence
AdmissibleEvidence != ClaimDecision
ClaimDecision != Finding
```

An R4 component states only how a defined arithmetic identity classifies an observed Revenue difference under R4 v1. No component establishes the underlying business reason.

The term **contribution** is permitted only in the method-relative mechanical sense defined here and by R1. It must not be used as a synonym for causal responsibility or diagnostic explanation.

---

## 6. Method Identity and Versioning Model

R4 defines a separate deterministic method family named **Product-Level Revenue Decomposition**.

The initial semantic version is **R4 v1.0**. This human-reviewable identity distinguishes the method from the frozen Metrics it consumes:

```text
Frozen Metric authorities
→ authoritative monetary and product-level inputs

R4 method identity and version
→ product-presence classification, component aggregation, traceability,
  reconciliation, and method-specific validation semantics
```

The method identity must be explicit in every future execution plan, execution record, result, validation record, retained trace, and material mechanical rendering that depends on this method.

An opaque fingerprint alone is insufficient method authority. A fingerprint may protect integrity, but a reviewer must also be able to resolve the human-readable method definition and version.

R4 v1.0 does not replace or revise the version of Revenue, Revenue Change, Product Revenue, Product Revenue Change, Product Absolute Contribution, canonical schema, population rules, precision policy, or validation policy. Each remains independently referenced.

---

## 7. Input Authority

R4 may consume only authenticated governed inputs. The authoritative input basis must identify or bind:

- Baseline Revenue authority;
- Comparison Revenue authority;
- authoritative Revenue Change authority;
- canonical eligible order-line evidence;
- authoritative Product Revenue semantics;
- authoritative Product Revenue Change and Product Absolute Contribution semantics;
- stable governed `product_id` values;
- explicit Baseline and Comparison Period definitions;
- the exact governed population and scope;
- one governed currency basis;
- the applicable governed evidence authority for the execution context;
- when R4 executes inside a diagnostic workflow, the exact R3 Resolved Required Evidence Profile and version for that Diagnostic Proposition;
- R4 method identity and version;
- the applicable central precision authority;
- the applicable validation authority;
- canonical dataset, mapping, transformation, and population references and fingerprints; and
- provenance sufficient to authenticate and reproduce the input basis.

Free-form user statements, filenames, apparent column names, narrative descriptions, observed minimum or maximum dates, model confidence, or prior prose are not authoritative method inputs.

User-provided declarations may participate only through the already governed intake, coverage, mapping, eligibility, evidence, and provenance authorities. R4 must not upgrade them by interpretation.

A standalone mechanical request does not require a fictitious Diagnostic Proposition merely to obtain a proposition-bound R3 profile. It still requires the existing canonical, sufficiency, validation, evidence, provenance, and artifact authorities plus every applicable R4 method-specific prerequisite. When the execution is part of an exact diagnostic workflow, the proposition-bound R3 profile is additionally mandatory.

---

## 8. Mechanical Execution Eligibility

R4 is a mechanical deterministic method. Eligibility to execute R4 is distinct from admission of its result for a diagnostic proposition.

Two execution contexts are governed separately.

### 8.1 Standalone mechanical execution

When no Diagnostic Proposition is being tested or evaluated, the conforming flow is:

```text
Standalone mechanical decomposition request
→ existing governed mechanical evidence prerequisites satisfied
→ R4 method-specific prerequisites satisfied
→ R4 executes
→ per-result R4 validation runs
→ authenticated Validated R4 mechanical result
```

R4 must not fabricate an R2 Diagnostic Proposition, create an artificial proposition-bound R3 profile, or redefine R3 as a universal execution contract merely to authorize standalone arithmetic.

No Diagnostic Proposition required does not mean no evidence governance required. Standalone execution must deterministically establish every materially applicable requirement through existing canonical, sufficiency, validation, evidence, provenance, artifact-integrity, precision, and method authorities.

### 8.2 R4 inside a governed diagnostic workflow

When R4 executes as part of testing or evaluating an exact Diagnostic Proposition, the conforming flow is:

```text
Exact R2 Diagnostic Proposition
→ exact applicable R3 Resolved Required Evidence Profile and version satisfied
→ R4 method-specific prerequisites satisfied
→ R4 executes
→ per-result R4 validation runs
→ authenticated Validated R4 mechanical result
→ R2 diagnostic evaluation path continues
```

R4 must not weaken, replace, bypass, or reinterpret the proposition-bound R3 profile.

### 8.3 Common execution boundary

Diagnostic-input admission is not required merely to perform standalone R4 mechanical execution. If a standalone result is later proposed for diagnostic use, proposition-, role-, and intended-use-specific diagnostic admission is required at that later boundary.

Mechanical execution eligibility requires all applicable pre-execution evidence and method prerequisites to pass. It does not establish that execution occurred, validation passed, a diagnostic criterion was met, or a Claim may be rendered.

```text
mechanically eligible != executed
executed != validated
validated mechanical result != diagnostic-input admissibility
diagnostic-input admissibility != diagnostic support
diagnostic support != Claim authorization
```

No diagnostic `ClaimDecision` permission is required to run the mechanical method.

---

## 9. Period Preconditions

R4 requires two explicit governed periods:

- **Baseline Period B:** the earlier reference period; and
- **Comparison Period C:** the later period evaluated against B.

R4 reuses the frozen comparison-period contract. B and C must:

- have explicit inclusive start and end dates;
- place B earlier than C;
- not overlap;
- contain the same number of governed calendar dates where required by frozen authority;
- each have independent, applicable completeness and coverage evidence;
- use the same governed date and timezone convention;
- use the same Revenue, eligibility, currency, scope, product-identity, and canonical semantics; and
- have unambiguous Baseline and Comparison identities.

R4 must not silently:

- normalize results per day;
- extend, shorten, shift, align, or impute a period;
- convert an incomplete period into a complete period;
- interpret an absent date as zero activity without coverage authority;
- change timezone or date-boundary policy; or
- change period direction.

An unresolved period or coverage defect is an execution-eligibility failure. It is not a valid decomposition with a qualification.

---

## 10. Population and Scope Preconditions

Every R4 anchor, product value, component, and validation must use the exact same governed:

- Revenue definition;
- eligibility definition;
- canonical dataset basis;
- scope;
- filters;
- population semantics;
- period basis;
- product-identity semantics; and
- currency basis.

The Baseline and Comparison populations may differ in their eligible rows because they cover different periods, but they must be constructed under identical material rules and compatible authority.

The decomposition must not combine:

- a broad total Revenue with narrow product components;
- filtered product results with an unfiltered Revenue Change;
- one eligibility rule in B with another in C;
- one store, channel, category, product, or other filter basis with another; or
- separately valid results whose scope or population fingerprints are materially incompatible.

When a narrower scope is validly requested, Baseline Revenue, Comparison Revenue, Revenue Change, the product universe, every Product Absolute Contribution, and all aggregate components must be recomputed or authoritatively resolved for that exact narrower scope.

A prose limitation cannot repair population or scope mismatch.

---

## 11. Currency Preconditions

One R4 decomposition operates on exactly one governed currency basis.

The following must be compatible:

- Baseline Revenue currency;
- Comparison Revenue currency;
- Revenue Change currency;
- every Product Revenue value;
- every Product Absolute Contribution;
- every aggregate component; and
- the product-level trace.

Missing, unknown, mixed, incompatible, or unresolved currency blocks mechanical execution.

R4 performs no FX lookup, conversion, translation, or historical exchange-rate reconciliation. If an upstream governed normalization to one currency already exists, R4 may reference that authority and provenance. It must not reconstruct or infer the normalization.

---

## 12. Product Identity

`product_id` is the sole authoritative product grouping key for R4 v1. `product_name` is descriptive only.

The following rules apply:

- a stable `product_id` with a changed product name remains one product unless separate authority establishes an identity defect;
- the same product name attached to different stable IDs represents different products;
- a missing, null, empty, invalid, or unresolved `product_id` blocks the decomposition;
- confirmed cross-period product-ID collision, reuse, or corruption blocks the decomposition;
- product names must not be used as fallback identity;
- no unknown-product or unclassified-product bucket is permitted; and
- R4 does not repair product master data.

Name variation may qualify presentation while leaving stable ID grouping intact. Name variation alone does not prove identity corruption. Conversely, an ID must not be treated as valid merely because names appear similar when separate governed evidence establishes collision or reuse.

Every eligible canonical line in the governed R4 population must resolve to exactly one valid product identity.

---

## 13. Product Universe and Partition

Let:

- \(P_B\) be the set of authoritative `product_id` values present in the governed Baseline population;
- \(P_C\) be the set of authoritative `product_id` values present in the governed Comparison population; and
- \(P = P_B \cup P_C\) be the complete governed product universe for the decomposition.

Presence is established by at least one eligible canonical line assigned to the product in the period. Presence is not determined by positive Revenue. A genuine eligible zero-Revenue line still makes its product present.

The complete product universe is partitioned into:

\[
E = P_C \setminus P_B
\]

\[
X = P_B \setminus P_C
\]

\[
K = P_B \cap P_C
\]

where:

- \(E\) contains Comparison-only products;
- \(X\) contains Baseline-only products; and
- \(K\) contains products present in both periods.

The partition must be complete, mutually exclusive, and deterministic:

\[
E \cup X \cup K = P
\]

and:

\[
E \cap X = E \cap K = X \cap K = \varnothing
\]

A product must not be omitted because its contribution is zero, its name is missing, it is not displayed publicly, or it falls outside a presentation ranking.

Genuine absence may be represented as zero Product Revenue only when applicable period and population coverage proves absence. Unknown or incomplete coverage must remain unknown and blocks the affected decomposition.

---

## 14. Entry Component

For every product \(i \in E\), the product is present only in the Comparison Period. Its Baseline Product Revenue is genuine zero under complete governed coverage.

The product-level Entry contribution is:

\[
EntryContribution_i = Revenue_{i,C}
\]

The aggregate Entry Component is:

\[
EntryComponent = \sum_{i \in E} Revenue_{i,C}
\]

This component means only:

> The arithmetic contribution assigned by R4 v1 to products observed in the complete governed Comparison population and not observed in the complete governed Baseline population.

The classification does not establish that a product was newly launched, acquired, successfully introduced, added through an assortment strategy, or responsible for Revenue growth.

A Comparison-only product with zero Product Revenue remains in \(E\) and contributes zero. R4 must not redefine presence as positive Revenue.

---

## 15. Exit Component

For every product \(i \in X\), the product is present only in the Baseline Period. Its Comparison Product Revenue is genuine zero under complete governed coverage.

The product-level Exit contribution is:

\[
ExitContribution_i = -Revenue_{i,B}
\]

The aggregate Exit Component is:

\[
ExitComponent = \sum_{i \in X} (-Revenue_{i,B})
\]

This component means only:

> The arithmetic contribution assigned by R4 v1 to products observed in the complete governed Baseline population and not observed in the complete governed Comparison population.

The classification does not establish that a product was discontinued, delisted, unavailable, strategically removed, or responsible for Revenue decline.

A Baseline-only product with zero Product Revenue remains in \(X\) and contributes zero.

---

## 16. Continuing-Product Revenue Change Component

For every product \(i \in K\), the product is present in both periods.

The product-level Continuing contribution is:

\[
ContinuingContribution_i = Revenue_{i,C} - Revenue_{i,B}
\]

The aggregate Continuing-Product Revenue Change Component is:

\[
ContinuingComponent =
\sum_{i \in K}(Revenue_{i,C} - Revenue_{i,B})
\]

This component means only:

> The aggregate Product Revenue Change of governed product identities present in both periods.

It does not further decompose the difference within a product.

---

## 17. Continuing Component Semantic Boundary

The Continuing-Product Revenue Change Component is an arithmetic classification bucket. It is not a driver or explanation.

```text
Continuing-Product Revenue Change Component
!= Within-product diagnostic explanation
```

It must not be represented as:

- existing products drove growth;
- continuing products explain the decline;
- core products were the main reason;
- core assortment performance;
- a quantity or volume effect;
- a price or pricing effect;
- a product-mix effect;
- a discount effect;
- a demand effect; or
- a cause, root cause, mechanism, motive, or intervention effect.

Positive, negative, or zero Continuing contribution establishes only arithmetic direction and magnitude under R4 v1.

---

## 18. Authoritative Decomposition Identity

For each product \(i \in P\), frozen Product Absolute Contribution authority gives:

\[
ProductAbsoluteContribution_i = Revenue_{i,C} - Revenue_{i,B}
\]

with genuine absence represented as zero only under complete governed coverage.

R4 v1 classifies that atomic contribution by membership in \(E\), \(X\), or \(K\). Therefore:

\[
Revenue_C - Revenue_B
=
\sum_{i \in E} Revenue_{i,C}
+
\sum_{i \in X} (-Revenue_{i,B})
+
\sum_{i \in K}(Revenue_{i,C} - Revenue_{i,B})
\]

Equivalently:

\[
ObservedRevenueChange
=
EntryComponent
+ ExitComponent
+ ContinuingComponent
\]

and:

\[
\sum_{i \in P} ProductAbsoluteContribution_i
= ObservedRevenueChange
\]

All equalities operate at authoritative precision and on the identical governed population, scope, period, product-identity, and currency basis.

R4 classifies the frozen Product Absolute Contributions. It does not redefine their formula or create an alternative Revenue Change.

---

## 19. Component Taxonomy

R4 v1 uses the following minimum taxonomy.

### 19.1 Authoritative anchors

- Baseline Revenue;
- Comparison Revenue; and
- Observed Revenue Change.

Anchors identify the authoritative monetary comparison. They are not additional decomposition components.

### 19.2 Additive decomposition components

- Entry Component;
- Exit Component; and
- Continuing-Product Revenue Change Component.

### 19.3 Product presence classifications

- Comparison-only;
- Baseline-only; and
- Continuing.

### 19.4 Validation concepts

- Component Sum;
- Reconciliation Difference; and
- Reconciliation Status.

R4 v1 has no quantity, volume, unit-value, price, pricing, discount, interaction, mix, demand, residual, unexplained, or other normal component.

---

## 20. Precision and Numerical Governance

R4 reuses the central frozen precision authority.

Authoritative method calculation and validation must:

- use exact governed Decimal monetary semantics;
- retain source and governed precision during Product Revenue and component aggregation;
- prevent binary floating-point approximation from controlling equality or reconciliation;
- use deterministic aggregation semantics;
- perform no presentation rounding before validation;
- derive rankings or signs, if later displayed, from unrounded authoritative values;
- introduce no arbitrary epsilon, near-zero threshold, or R4-specific tolerance;
- round only at the presentation boundary after authoritative values and validation are finalized; and
- fail closed when required values cannot be represented at the applicable exact governed precision.

R4 does not duplicate a hard-coded implementation precision. A future implementation must bind the central precision-policy reference and its version.

Presentation strings must never be used as reverse-reconciliation inputs. A difference visible only after independent presentation rounding is a presentation artifact; it does not change the authoritative identity.

---

## 21. Reconciliation Policy

The Component Sum is:

\[
ComponentSum = EntryComponent + ExitComponent + ContinuingComponent
\]

The Reconciliation Difference is:

\[
ReconciliationDifference = ObservedRevenueChange - ComponentSum
\]

A valid R4 decomposition requires:

\[
ReconciliationDifference = 0
\]

at authoritative precision.

R4 v1 does not recognize residual as a valid component. A nonzero authoritative Reconciliation Difference is Result Validation Failure. It must not be:

- ignored;
- rounded away at the authority level;
- assigned to Entry, Exit, or Continuing;
- relabeled as Other, Unclassified, Residual, Unexplained, or Reconciliation Adjustment and treated as valid;
- force-balanced by changing a product value; or
- repaired by qualification or narrative.

A presentation-rounding artifact is distinct from authoritative reconciliation failure. Presentation tooling may disclose that separately rounded displayed components do not visually add to a separately rounded displayed total, but the authoritative unrounded identity must already have passed.

---

## 22. Zero, Missing, Negative, and Invalid Handling

R4 preserves frozen canonical semantics.

### 22.1 Zero Revenue

A genuine eligible line may have zero `line_revenue`. It contributes zero Revenue but still establishes product presence. A product's period Revenue may therefore be zero while the product remains present.

An empty governed population may have authoritative Revenue zero only when completeness and coverage establish that no eligible lines exist. If both complete periods are empty, \(P\), \(E\), \(X\), and \(K\) are empty and all three components and Observed Revenue Change are zero. If only one complete period is empty, the nonempty period's products fall into Entry or Exit as defined above.

### 22.2 Missing Revenue

Missing `line_revenue` is unknown, not zero. It blocks the affected canonical line and, where the affected population or amount may be material, blocks R4 execution.

### 22.3 Negative Revenue

Negative `line_revenue` is invalid under the canonical MVP. R4 must not reinterpret a negative line as an Exit, refund, return, or offset.

### 22.4 Missing or invalid product identity

Missing or invalid `product_id` blocks the product partition. The affected Revenue must not be silently omitted, assigned by product name, or placed in an unknown bucket.

### 22.5 Eligibility, cancellation, and refund boundary

Cancelled, fully refunded, explicitly excluded, invalid, or out-of-scope lines are excluded under existing governed eligibility authority before the product universe is formed.

Partial refunds, refund timing, return events, and arbitrary post-sale adjustments remain unsupported where no governed final eligible `line_revenue` exists. R4 does not create a refund ledger, negative-line convention, or adjustment component.

### 22.6 Quantity boundary

Quantity is not an R4 v1 decomposition variable. Existing canonical validation still requires every canonical sales line to have valid positive whole-number quantity. That upstream line-validity requirement does not make quantity an R4 component and does not authorize volume decomposition.

---

## 23. R3 Integration

Frozen R3 defines proposition-specific Required Evidence authority around an exact Diagnostic Proposition. R4 must not silently generalize that authority into a universal execution contract for all standalone analytical methods.

### 23.1 Standalone mechanical execution

A purely mechanical R4 request with no Diagnostic Proposition does not require an invented R2 proposition or artificial R3 profile.

Standalone execution nevertheless remains fully governed. Existing canonical, Data Quality, Data Sufficiency, validation, evidence, provenance, precision, population, and artifact authorities, together with R4 method-specific prerequisites, must deterministically establish all materially applicable conditions, including:

- authoritative Revenue inputs;
- period completeness and comparability;
- population, scope, filters, and eligibility semantics;
- stable product identity and complete product coverage;
- semantic validity and missingness treatment;
- one governed currency;
- provenance and artifact integrity;
- method identity and version;
- precision authority; and
- method-specific validation prerequisites.

R4 may reuse R3-compatible evidence dimensions and terminology to maintain governance consistency. It must not create a second Required Evidence system, duplicate R3 authority, or represent an R3-compatible checklist as a proposition-bound Resolved Required Evidence Profile when no Diagnostic Proposition exists.

### 23.2 R4 inside a diagnostic workflow

If R4 executes as part of testing or evaluating an exact Diagnostic Proposition:

- the exact R2 Diagnostic Proposition must exist;
- the applicable R3 Resolved Required Evidence Profile and version must be satisfied;
- every frozen R1 minimum dimension and triggered conditional dimension must be resolved through that profile at the proper applicability level; and
- every R4 method-specific prerequisite must also pass.

The R3 profile remains requirement authority. It does not become execution, validation, Analytical Outcome, or Claim authority. R4 may tighten method prerequisites but must not waive, weaken, replace, reinterpret, or duplicate the profile.

If the applicable diagnostic profile is missing, mismatched, blocked, materially incomplete, unresolved, or version-incompatible, R4 must not execute within that diagnostic workflow.

### 23.3 Downstream diagnostic use

Whether originally executed standalone or inside a diagnostic workflow, a Validated R4 result does not inherit diagnostic-input admissibility or diagnostic support. Its use for a diagnostic proposition remains subject to the exact R3 profile, proposition-, role-, and intended-use-specific admission, and the complete R2 evaluation path.

---

## 24. Method-Specific Preconditions

R4 v1 requires all of the following before execution. For standalone mechanical execution, they operate with the existing upstream governed evidence authorities described in Section 23.1. For execution inside a diagnostic workflow, they apply in addition to the satisfied exact R3 profile described in Section 23.2.

1. Baseline and Comparison Revenue authorities are authentic and resolvable.
2. Authoritative Revenue Change is authentic and bound to those period Revenue authorities.
3. Baseline and Comparison Period definitions satisfy frozen comparison rules.
4. The governed population, scope, filters, and eligibility semantics are explicit and compatible.
5. One governed currency basis applies throughout.
6. The canonical product-capable order-line population is complete for the intended scope.
7. Every eligible line resolves to exactly one valid `product_id`.
8. Product identity semantics are stable across periods, with no confirmed unresolved collision or reuse.
9. Genuine product absence is distinguishable from missing or incomplete coverage.
10. The complete product universe can be formed without omission or overlap.
11. R4 method identity and version are resolved.
12. Central precision authority and version are resolved.
13. Applicable method-validation authority and versions are resolved.
14. Product-level trace and integrity requirements are resolved.
15. Required canonical, population, Metric, plan, evidence, and artifact references and fingerprints are authentic.
16. No earlier evidence or method-eligibility blocker remains.

These prerequisites do not require positive diagnostic Claim permission.

---

## 25. Product-Level Traceability

R4 requires retained product-level traceability. Aggregate components alone are insufficient.

For every product in \(P\), the trace must make reviewable:

- authoritative `product_id`;
- Baseline Product Revenue;
- Comparison Product Revenue;
- Comparison-only, Baseline-only, or Continuing classification;
- Product Absolute Contribution;
- assigned aggregate component;
- currency;
- Baseline and Comparison Period references;
- population and scope references;
- canonical dataset and relevant fingerprint authority;
- R4 method identity and version; and
- applicable execution and validation lineage.

The aggregate Entry, Exit, and Continuing components must be deterministically reproducible from the complete trace. A displayed Top N or filtered presentation is not a substitute for retained full-partition traceability.

Product names are not required for authority. If retained for display, they remain descriptive and must not control grouping.

---

## 26. Trace Artifact Boundary

R4 prefers a local immutable retained artifact for the complete product-level trace, consistent with the frozen local persistence and artifact architecture.

The aggregate decomposition result may conceptually reference:

- trace artifact identity;
- content fingerprint;
- integrity and provenance references;
- product row count;
- partition counts;
- aggregate totals;
- method identity and version; and
- validation references.

This section defines required meaning, not a physical schema, serialization format, file layout, database table, retention duration, or API contract.

The trace artifact must not be reconstructed later from conversational memory or public prose. Once finalized, its content and identity must not be silently mutated.

R4 does not authorize automatic public disclosure of product-level detail. Retention and authority are distinct from public presentation.

---

## 27. Result Semantics

An executed R4 result is deterministic output produced by actual method execution. It is not automatically a Validated Decomposition Result.

A Validated R4 Decomposition Result exists only after all applicable independent method validations pass for the intended mechanical use.

It is bound to:

- exact canonical input authority;
- exact Baseline and Comparison Periods;
- exact population, scope, eligibility rules, and filters;
- exact currency;
- exact product universe and partition;
- exact Product Revenue and Product Absolute Contribution values;
- exact R4 method identity and version;
- exact precision authority;
- exact trace artifact and integrity authority; and
- exact validation authority.

An R4 result is not:

- a Finding;
- a business explanation;
- a cause or driver;
- a Product Mix conclusion;
- an Analytical Outcome;
- `CRITERION_MET`;
- an Alternative Explanation Check;
- diagnostic support;
- a ClaimCandidate permission; or
- a `ClaimDecision`.

Accurate process statements may report that execution or validation succeeded or failed. Such statements do not transform the result into a diagnostic Finding.

---

## 28. Diagnostic Reuse Boundary

Whether produced by standalone mechanical execution or within a governed diagnostic workflow, a Validated R4 result is authenticated mechanical authority only. When proposed as evidence for a diagnostic proposition, it becomes authenticated candidate evidence and no more.

It must still undergo:

- exact Diagnostic Proposition binding;
- role-specific evidence mapping;
- proposition- and intended-use-specific admission;
- a compatible R3 Resolved Required Evidence Profile and all applicable requirement judgments;
- R2 Diagnostic Evaluation;
- Evidence Conflict Assessment;
- a governed method or diagnostic-test binding where applicable;
- a governed support or contradiction criterion;
- Analytical Outcome determination;
- Alternative Explanation Check; and
- authoritative `ClaimDecision` evaluation before material Finding wording.

Mechanical validation authenticates the mechanical result. It does not prove that the result measures a diagnostic construct, supports a diagnostic proposition, or excludes competing interpretations.

Current descriptive or mechanical admissibility must not be inherited as diagnostic-input admissibility.

```text
Validated R4 result
→ authenticated candidate evidence for diagnostic use

NOT

Validated R4 result
→ diagnostic-input admissibility
→ diagnostic support
→ Finding
```

---

## 29. Independent Validation Obligations

R4 requires independent deterministic validation. Execution must not serve as its own sole proof where an independent invariant can be checked.

At minimum, validation must establish:

1. Baseline Revenue matches the authoritative Baseline Revenue result.
2. Comparison Revenue matches the authoritative Comparison Revenue result.
3. Observed Revenue Change matches the authoritative Revenue Change result and the governed Comparison-minus-Baseline direction.
4. Baseline Product Revenue sums to Baseline Revenue.
5. Comparison Product Revenue sums to Comparison Revenue.
6. Every eligible line belongs to exactly one valid product identity.
7. The product universe equals the complete governed union \(P_B \cup P_C\).
8. \(E\), \(X\), and \(K\) are complete, mutually exclusive, and classification-correct.
9. Every product contribution equals Comparison Product Revenue minus Baseline Product Revenue under governed genuine-zero semantics.
10. Entry Component equals the sum of all and only \(E\) product contributions.
11. Exit Component equals the sum of all and only \(X\) product contributions.
12. Continuing Component equals the sum of all and only \(K\) product contributions.
13. Component Sum equals the sum of every Product Absolute Contribution in the complete product universe.
14. Component Sum equals authoritative Observed Revenue Change.
15. Reconciliation Difference equals zero at authoritative precision.
16. Period, population, scope, eligibility, currency, product identity, method, Metric, precision, and validation bindings match their authenticated authorities.
17. The complete product trace reproduces every aggregate component and anchor.
18. Trace artifact identity, content fingerprint, and integrity references validate.
19. No presentation-rounded value controlled an authoritative calculation or reconciliation.

Validation of a different dataset, scope, population, period, product universe, method version, result, trace artifact, precision policy, or intended use cannot substitute.

Failed required validation produces no Validated R4 result for the affected use and cannot be repaired by qualification.

These obligations apply to each actual Executed R4 Result. They validate the result against its authenticated inputs, bindings, trace, and deterministic invariants.

```text
Per-result validation
!= Determinism conformance testing
```

Ordinary per-result validation does not require executing every production request twice. A single production result may become a Validated R4 Result when every applicable result invariant above passes through the governed independent validation path.

Deterministic repeatability remains mandatory for the method implementation and evaluator. It is established separately through controlled repeated-run testing, evaluator conformance, implementation validation, and future R5 fixtures as defined in Sections 35, 38, and 42.

---

## 30. Failure Semantics

R4 preserves four distinct failure meanings.

### 30.1 Evidence or method-eligibility failure

This occurs before valid execution may begin. Examples include:

- missing or failed standalone governed evidence prerequisite;
- when executing inside a diagnostic workflow, a missing, mismatched, blocked, or unresolved exact R3 profile;
- incomplete or non-comparable periods;
- population or scope mismatch;
- missing, mixed, unknown, or incompatible currency;
- missing or invalid product identity;
- confirmed unresolved cross-period product-ID collision or reuse;
- incomplete product or transaction coverage;
- unsupported eligibility, refund, or monetary semantics;
- missing provenance or artifact authority;
- unresolved method, precision, validation, or trace prerequisite; or
- inability to distinguish genuine absence from missing evidence.

No intended R4 method execution occurs for the blocked chain.

### 30.2 Method execution failure

This occurs when an eligible governed execution is attempted but fails to produce a usable intended result. Examples include:

- method or dependency version cannot be resolved at runtime;
- required canonical or trace-supporting artifact is unavailable or fails integrity checks before result production;
- aggregation or classification operation fails;
- execution is interrupted;
- required exact precision cannot be represented; or
- execution produces only a partial, dependency-incomplete output.

Execution failure is evidence that execution failed. It is not evidence for the intended component values.

### 30.3 Result validation failure

This occurs after execution produces an Executed Result that fails an applicable validation. Examples include:

- Product Revenue sum mismatch;
- incomplete or overlapping partition;
- invalid presence classification;
- incorrect product contribution;
- component aggregate mismatch;
- Component Sum mismatch;
- nonzero authoritative Reconciliation Difference;
- trace artifact integrity or completeness failure;
- authority-binding mismatch.

### 30.4 Method or evaluator conformance failure

This occurs when controlled conformance evidence demonstrates that the method implementation or evaluator does not preserve R4 semantics across the required conformance cases. Examples include:

- repeated controlled execution with identical authoritative inputs and versions produces materially different product universes, classifications, values, aggregates, reconciliation, or dispositions;
- two purportedly conforming evaluators disagree materially under identical governed inputs and versions; or
- implementation behavior depends on nondeterministic ordering, unrestricted LLM discretion, or another uncontrolled factor.

Method or evaluator conformance failure is distinct from failure of one actual production result's deterministic invariants. A production result is not invalid merely because it was not redundantly executed twice. If controlled conformance testing establishes nondeterministic behavior, however, the implementation is non-conforming and must not remain governed for material R4 execution until corrected and revalidated.

Evidence or method-eligibility failure, method execution failure, result validation failure, and method or evaluator conformance failure must not collapse into one generic meaning. This distinction does not require new runtime enums. Qualification, prose, a plausible value, or an independently valid unrelated result cannot repair the affected chain.

Independent valid chains may remain valid only when their own scope and evidence are complete and their meaning does not depend on the failed R4 chain.

---

## 31. Permitted Mechanical Language

Material wording must identify the method-relative mechanical meaning and remain within the validated scope.

Permitted forms include:

> Under R4 Product-Level Revenue Decomposition method version M, the Entry Component is +X in currency C.

> Comparison-only products account for +X of the mechanical Revenue difference under method M.

> Baseline-only products account for −X of the mechanical Revenue difference under method M.

> The Continuing-Product Revenue Change Component is −Y under method M.

> The component sum reconciles exactly to the authoritative Revenue Change at authoritative precision.

The word **contributed** may be used only when explicitly qualified as mechanical and method-relative, for example:

> Under method M, the Entry Component mechanically contributed +X to the defined Revenue decomposition.

The wording must retain the applicable periods, scope, currency, qualifications, and method version where material.

No wording template creates permission by itself. Material rendering remains subject to applicable evidence and `ClaimDecision` authority.

---

## 32. Prohibited and Restricted Language

Without separate later frozen authority for the exact proposition, R4 output must not use or materially imply:

- price effect;
- pricing effect;
- discount effect;
- demand effect;
- volume effect;
- product mix explains;
- existing products drove growth;
- continuing products explain the decline;
- new products caused growth;
- discontinued products caused decline;
- core products were the main reason;
- root cause;
- reason;
- main reason;
- primary reason;
- primary driver;
- caused;
- drove;
- led to;
- resulted in;
- due to;
- responsible for;
- explains; or
- equivalent causal, diagnostic, motive, mechanism, uniqueness, or primacy wording.

R4 v1 should avoid the unqualified word **driver** even when intended mechanically because the approved taxonomy already provides precise component names.

Softening unsupported content with words such as “may,” “likely,” “appears,” or “suggests” does not make it admissible.

---

## 33. Product Mix Boundary

R4 v1 classifies product presence and Product Revenue Change. It does not automatically establish a Product Mix diagnostic proposition.

```text
Product-level Revenue decomposition
!= Product Mix Finding
```

The Entry, Exit, and Continuing partition may later be relevant to a separately governed Product Mix proposition. R4 does not define that proposition's composition measure, diagnostic test, support criterion, contradiction criterion, Alternative Explanation requirements, or Claim policy.

The frozen R3 Product Mix profile example remains non-authorizing. A future Product Mix workflow must satisfy R1–R3 and any later approved diagnostic method governance independently.

---

## 34. R2 Integration

R4 produces deterministic executed and, after passing validation, validated mechanical method authority.

R2 remains solely responsible for:

- Diagnostic Proposition identity;
- Diagnostic Evaluation identity and history;
- Evidence Conflict Assessment;
- Analytical Outcome;
- Alternative Explanation Check;
- `ClaimCandidate` binding;
- authoritative `ClaimDecision` references;
- Derived Material Disposition; and
- Finding history and immutability.

Successful R4 execution or validation must not automatically set:

- `CRITERION_MET`;
- `CRITERION_NOT_MET`;
- `PROPOSITION_CONTRADICTED`;
- Supported Diagnostic Finding; or
- any other R2 material disposition.

R4 does not create a parallel Claim-approval path. `ClaimDecision` remains the sole material Claim-permission authority.

---

## 35. Determinism and Reproducibility

Two conforming evaluators given identical authoritative material inputs must agree on the material R4 result.

The controlled input basis includes:

- canonical evidence and fingerprints;
- applicable standalone governed evidence authority or, inside a diagnostic workflow, the satisfied exact R3 profile identity and version;
- Baseline and Comparison Periods;
- population, scope, eligibility, and filter authority;
- currency basis;
- product-identity authority;
- frozen Metric definition versions;
- R4 method identity and version;
- precision authority; and
- validation policy and rule versions.

They must agree materially on:

- \(P_B\), \(P_C\), and the complete product universe;
- \(E\), \(X\), and \(K\) classification;
- Baseline and Comparison Product Revenue values;
- every Product Absolute Contribution;
- Entry, Exit, and Continuing component values;
- Component Sum;
- Reconciliation Difference;
- reconciliation validity;
- the controlling eligibility, execution, or validation failure layer; and
- the maximum permitted mechanical meaning.

Conformance does not require identical implementation code, internal query plans, physical storage layout, generated IDs, or narrative wording. It does require reproducibility of material values, classifications, authority bindings, validation judgments, and semantic boundaries.

Deterministic repeatability is a method and evaluator conformance obligation. It must be demonstrated through controlled repeated-run testing and applicable conformance cases, including identical inputs under the same evaluator and materially equivalent governed inputs across conforming evaluators.

It is not an ordinary per-result validation requirement:

```text
same authoritative inputs + same versions
→ same material result

AND

per-result validation
!= mandatory duplicate production execution
```

A conforming production path may validate one actual result through all Section 29 invariants without running the request twice. Failure of controlled repeatability testing makes the implementation non-conforming even if an isolated result happened to satisfy its per-result invariants.

LLM discretion must not affect product identity, presence classification, arithmetic, aggregation, reconciliation, validation, or material permission.

---

## 36. Method Versioning

A new R4 method version is required whenever a material method semantic changes, including:

- Entry definition;
- Exit definition;
- Continuing definition;
- component taxonomy;
- product presence classification;
- product-universe or partition rule;
- genuine-zero treatment;
- product-identity prerequisite;
- population, scope, period, or currency prerequisite;
- reconciliation identity or validity rule;
- precision or rounding semantics;
- retained trace completeness requirement;
- method-specific validation obligation;
- maximum permitted mechanical meaning;
- addition of Quantity × Realized Unit Value decomposition;
- addition or allocation of an interaction term; or
- addition of a normal residual component.

Changing physical storage, refactoring implementation, or improving performance without changing material behavior need not create a new method-semantic version, though implementation or package versions may still change under Architecture authority.

Historical results remain bound to their original:

- method identity and version;
- applicable standalone governed evidence authority or, when produced inside a diagnostic workflow, the exact R3 profile identity and version;
- Metric definitions;
- canonical dataset and fingerprint;
- periods and population fingerprints;
- precision policy;
- validation policy and rules;
- product trace artifact; and
- execution and validation records.

No later method version may silently reinterpret or overwrite a historical result.

---

## 37. Human-Reviewable Result View

A future R4 result must make the following concepts reviewable without requiring access to implementation source code.

| Review concept | Required meaning |
|---|---|
| Method authority | Product-Level Revenue Decomposition identity and exact version |
| Input authority | Canonical dataset, Revenue authorities, applicable standalone governed evidence authority or exact diagnostic R3 profile, and relevant fingerprints/references |
| Comparison basis | Explicit Baseline and Comparison Periods, population, scope, eligibility, filters, and currency |
| Revenue anchors | Baseline Revenue, Comparison Revenue, and Observed Revenue Change |
| Product coverage | Complete product-universe count and Entry/Exit/Continuing counts |
| Components | Entry, Exit, and Continuing-Product Revenue Change values |
| Product trace | Immutable trace reference, fingerprint, integrity status, and row count |
| Reconciliation | Component Sum, Reconciliation Difference, and validation outcome |
| Execution | Actual execution reference and outcome |
| Validation | Applicable rule/version references and outcomes |
| Limitations | Non-blocking limitations that remain after all required validations pass |
| Semantic boundary | Explicit statement that the result is mechanical and not diagnostic or causal |

This table defines a human-reviewable projection, not a runtime model or physical schema.

---

## 38. Future R5 Fixture Requirements

R5, if separately authorized, must later define deterministic fixtures covering at least:

1. exact-reconciliation happy path;
2. Entry-only change;
3. Exit-only change;
4. Continuing-only Revenue change;
5. simultaneous Entry, Exit, and Continuing components;
6. a complete zero-Revenue period;
7. both periods empty and complete;
8. zero net Revenue Change with offsetting components;
9. zero-Revenue product presence without false Entry or Exit classification;
10. missing product ID;
11. stable ID with changed product name;
12. same product name with different IDs;
13. confirmed cross-period product-ID collision or reuse;
14. missing Revenue;
15. negative Revenue;
16. mixed or unknown currency;
17. incomplete period coverage;
18. overlapping periods;
19. unequal-duration periods where prohibited;
20. population, scope, eligibility, or filter mismatch;
21. deliberate Product Revenue sum mismatch;
22. incomplete or overlapping \(E/X/K\) partition;
23. deliberate component-sum mismatch;
24. nonzero authoritative Reconciliation Difference;
25. presentation-rounding edge with authoritative exact reconciliation;
26. repeated execution with identical authoritative inputs and versions under one evaluator;
27. two conforming evaluators producing materially identical product partitions, component values, reconciliation, and dispositions;
28. deterministic product-universe and \(E/X/K\) classification under controlled repeat runs;
29. deterministic component values and reconciliation outcome under controlled repeat runs;
30. trace artifact omission, incompleteness, or tampering;
31. method/profile/version mismatch;
32. standalone mechanical execution incorrectly forced to invent a Diagnostic Proposition;
33. diagnostic-workflow execution attempted without the applicable exact R3 profile;
34. mechanical contribution incorrectly rendered as diagnostic cause;
35. Continuing Component incorrectly labeled as a driver or explanation; and
36. R4 result proposed diagnostically without intended-use-specific admission.

Fixture specifications must distinguish evidence/method-eligibility failure, method execution failure, result validation failure, and method/evaluator conformance failure. No fixtures or executable tests are created by R4.

---

## 39. Public Product Boundary

This specification does not authorize:

- any CommerceLens v0.2.0 behavior change;
- any Public v0.1 behavior change;
- public execution or display of Revenue decomposition;
- product grouping in the public Skill;
- a new public Metric or question class;
- a CLI command;
- a dashboard;
- a new Skill response format;
- Product Mix runtime behavior;
- positive diagnostic Claim permission;
- Quantity × Realized Unit Value decomposition; or
- a change to `ClaimDecision` policy.

Current public behavior remains bounded to its already approved Revenue, Orders, AOV, and Revenue Change workflows and existing diagnostic refusal behavior.

---

## 40. Risks and Controls

| Risk | R4 control |
|---|---|
| Entry interpreted as new-product launch | Define only Comparison-period presence; prohibit launch and strategy inference |
| Exit interpreted as discontinuation | Define only Baseline-period presence; prohibit discontinuation inference |
| Continuing interpreted as a driver | Define arithmetic bucket only; prohibit driver and explanation wording |
| Product Mix inferred automatically | Preserve explicit Product-Level Decomposition != Product Mix Finding boundary |
| Missing coverage converted to absence | Require applicable complete-period coverage before genuine zero |
| Zero Revenue treated as absence | Define presence by eligible line, not positive Revenue |
| Product names replace identity | Require `product_id`; prohibit name fallback |
| ID corruption ignored | Block confirmed unresolved collision or reuse |
| Revenue redefined through quantity or price | Use frozen `line_revenue` authority only; defer Q × V |
| Mixed currencies are summed | Require one governed currency; no FX logic |
| Population or scope drift | Require common authority and recomputation for exact narrowed scope |
| Residual is hidden or allocated | Require zero authoritative Reconciliation Difference; otherwise validation failure |
| Presentation rounding controls validation | Validate unrounded authoritative Decimal values only |
| Standalone execution fabricates a Diagnostic Proposition | Use existing governed mechanical evidence authorities and R4 prerequisites; do not invent proposition-bound R3 authority |
| R4 broadens or duplicates R3 | Require the exact R3 profile only inside the applicable diagnostic workflow; otherwise reuse compatible dimensions without creating a second Required Evidence system |
| Mechanical result inherits diagnostic authority | Require later proposition- and intended-use-specific admission and R2 evaluation |
| Registry definition mistaken for executable capability | Preserve current implementation boundary explicitly |
| Traceability exposes product details publicly | Retain locally; public exposure remains separately unauthorized |
| Result promoted after failed validation | No Validated R4 result; qualification cannot repair failure |
| Every production request is run twice | Keep repeatability in controlled method/evaluator conformance testing, not ordinary per-result validation |
| Nondeterministic implementation escapes governance | Treat demonstrated repeat-run or cross-evaluator material disagreement as method/evaluator non-conformance |
| Method semantics drift without version change | Require new version for every material semantic change |

---

## 41. Open Implementation-Allocation Questions

No unresolved semantic question blocks R4 v1.0 review. The following matters are intentionally deferred because they concern physical implementation allocation rather than method meaning.

### 41.1 Physical method-contract placement

**Question:** Which future contract or registry owns the physical R4 method identity, version, prerequisites, and validation-rule references?

**Why it matters:** The method must be reviewable and reproducible without duplicating Metric Registry or R3 authority.

**Downstream ownership:** Separately authorized implementation planning after R4 approval.

### 41.2 Physical result-contract shape

**Question:** How should aggregate components, product trace references, reconciliation, and authority bindings be represented in runtime contracts?

**Why it matters:** Current scalar result contracts do not by themselves establish the complete governed R4 result projection.

**Downstream ownership:** Future contract and implementation milestone; not R4 semantics.

### 41.3 Independent validator placement

**Question:** Which future validation module and rule registry own R4-specific independent checks?

**Why it matters:** Validation must remain separate from execution and must bind method, trace, product partition, and reconciliation authority.

**Downstream ownership:** Future implementation architecture within the existing deterministic validation boundary.

### 41.4 Trace-artifact physical format and retention duration

**Question:** Which serialization, artifact path convention, metadata projection, and retention duration should be used for the complete product trace?

**Why it matters:** The artifact must remain immutable, auditable, reproducible, locally safe, and available for required review without unnecessary retention.

**Downstream ownership:** Future persistence and retention planning under frozen Architecture and retention authority.

### 41.5 Future Q × V milestone identity

**Question:** If separately approved later, should Quantity × Realized Unit Value be a new R4 major version or a separate method family?

**Why it matters:** It would add new measurement, denominator, interaction, terminology, evidence, precision, and validation semantics.

**Downstream ownership:** A future separately authorized governance milestone. R4 v1 does not define that method.

### 41.6 Diagnostic admission contract allocation

**Question:** Which future physical evidence contract represents proposition-, role-, profile-, and intended-use-specific admission of an authenticated R4 result into a diagnostic evaluation?

**Why it matters:** Current descriptive result admission must not be inherited, while R3 intentionally leaves physical diagnostic-input admission allocation open.

**Downstream ownership:** Future R2/R3-compatible diagnostic implementation planning, not R4 execution semantics.

---

## 42. Evaluator Conformance

A future evaluator conforms to R4 only when a reviewer can determine that it:

1. resolves the exact R4 method identity and version;
2. authenticates the frozen Metric, canonical, period, population, currency, evidence, precision, and artifact authorities;
3. permits standalone mechanical execution without fabricating a Diagnostic Proposition, but only after all applicable governed mechanical evidence prerequisites pass;
4. requires the satisfied exact R3 profile when R4 executes inside a governed diagnostic workflow;
5. does not redefine R3 as a universal analytics execution contract or create a second Required Evidence system;
6. does not require diagnostic-input admission merely for ordinary standalone mechanical execution;
7. blocks missing, mismatched, or unresolved material prerequisites;
8. forms the complete governed product union;
9. uses only authoritative `product_id` identity;
10. classifies every product into exactly one of Entry, Exit, or Continuing;
11. preserves zero-Revenue product presence;
12. distinguishes genuine absence from unknown coverage;
13. computes every Product Absolute Contribution using frozen authority;
14. aggregates exactly the three approved components;
15. validates every required per-result invariant independently without requiring every production request to run twice;
16. requires zero authoritative Reconciliation Difference;
17. retains and authenticates the complete product-level trace;
18. distinguishes eligibility, execution, result-validation, and method/evaluator-conformance failure meanings;
19. proves through controlled conformance testing that identical authoritative inputs and versions produce materially identical results;
20. does not create price, discount, quantity, unit-value, interaction, mix, demand, or residual components;
21. does not convert the result into an R2 Analytical Outcome or Finding;
22. requires separate intended-use admission for later diagnostic reuse; and
23. restricts material wording to method-relative mechanical meaning.

Two conforming evaluators need not share code or physical storage. They must materially agree on the product universe, partition, product values, contributions, aggregate components, reconciliation, failure layer, and permitted meaning.

---

## 43. Success Criteria and Conformance Checklist

R4 v1 is semantically complete only when all of the following are true:

- [x] Revenue is not redefined.
- [x] Frozen Revenue, Revenue Change, Product Revenue, Product Revenue Change, and Product Absolute Contribution authority is preserved.
- [x] Product-Level Revenue Decomposition is the only active R4 v1 architecture.
- [x] R4 is separately identified and versioned.
- [x] Mechanical execution eligibility is distinct from diagnostic-input admissibility.
- [x] Standalone mechanical execution does not require a fabricated Diagnostic Proposition or artificial R3 profile.
- [x] Standalone mechanical execution still requires complete governed evidence prerequisites and all R4 method-specific prerequisites.
- [x] R4 does not redefine R3 as a universal analytics execution contract or create a second Required Evidence system.
- [x] R4 execution inside a diagnostic workflow requires the satisfied exact R3 profile and version for that Diagnostic Proposition.
- [x] Later diagnostic use requires proposition-, role-, and intended-use-specific admission.
- [x] Baseline and Comparison Period rules are preserved.
- [x] Population, scope, eligibility, filters, and currency must align.
- [x] One governed currency is required and no FX logic is introduced.
- [x] Frozen `product_id` identity is preserved.
- [x] No product-name fallback or unknown-product bucket is introduced.
- [x] The complete product union is required.
- [x] Entry is formally defined.
- [x] Exit is formally defined.
- [x] Continuing-Product Revenue Change is formally defined.
- [x] Continuing is explicitly not a driver or explanation.
- [x] Product presence is not determined by positive Revenue.
- [x] Product-level traceability is required.
- [x] Exact arithmetic reconciliation is required.
- [x] Authoritative nonzero Reconciliation Difference is validation failure.
- [x] No normal residual component exists.
- [x] Central exact Decimal and presentation-only rounding authority is preserved.
- [x] No arbitrary epsilon or tolerance is introduced.
- [x] Quantity remains a canonical line-validity input but not an R4 v1 decomposition variable.
- [x] Q × V, price, unit-value, and interaction methods are deferred.
- [x] Result semantics remain mechanical and non-causal.
- [x] An R4 result is not a Finding, Analytical Outcome, or Claim permission.
- [x] R4 does not set `CRITERION_MET`.
- [x] `ClaimDecision` authority and policy are unchanged.
- [x] Independent deterministic validation obligations are explicit.
- [x] Per-result validation is distinct from method and evaluator determinism conformance testing.
- [x] Every production result must pass its applicable deterministic invariants but need not be executed twice.
- [x] Deterministic repeatability remains mandatory through controlled implementation/evaluator conformance and future R5 cases.
- [x] Evidence/method eligibility, execution, result-validation, and method/evaluator-conformance failure meanings remain distinct.
- [x] Method-version change conditions are explicit.
- [x] R5 fixture obligations are specified but not implemented.
- [x] Current v0.2.0 and Public v0.1 behavior is unchanged.
- [x] No implementation, runtime contract, schema, enum, class, migration, SQL, Python, test, or fixture is authorized by this document.
- [x] R5 and R6 are not started.

---

## 44. Dependencies and Next Milestone

R4 depends on the frozen authorities in Section 4 and the current repository authority they govern.

This document is Approved / Frozen and is the authoritative R4 v1.0 method-governance baseline.

Approval and freezing of R4 establishes method-governance authority only. It does not authorize:

- runtime implementation;
- R3 profile implementation;
- diagnostic admission implementation;
- `ClaimDecision` expansion;
- public behavior changes;
- physical R5 fixtures or tests;
- R5 execution; or
- R6 execution.

Any subsequent milestone requires separate explicit authorization. R4 closeout does not automatically begin R5 or R6.

---

## 45. Release Boundary

R4 v1 defines the Product-Level Revenue Decomposition method as:

```text
Authoritative Observed Revenue Change
= Entry Component
+ Exit Component
+ Continuing-Product Revenue Change Component
```

over the complete governed product universe, with exact product-level traceability and zero authoritative Reconciliation Difference.

It preserves the controlling boundary:

```text
mechanical arithmetic classification
!= diagnostic explanation
!= causal attribution
!= Claim authorization
```

No runtime or public capability exists merely because this specification exists.

R4 v1.0 is Approved / Frozen. Its substantive method semantics may not be silently redefined downstream.

---

**End of R4 Deterministic Revenue Decomposition Specification**
