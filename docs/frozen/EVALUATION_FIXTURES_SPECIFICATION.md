# CommerceLens AI Evaluation Fixtures Specification

**Version:** v1.0  
**Status:** Approved  
**State:** Frozen  
**Date:** 2026-08-20  
**Document:** `EVALUATION_FIXTURES_SPECIFICATION.md`

## 1. Purpose

This specification defines the authoritative Evaluation Fixture system for the first CommerceLens MVP analytical workflow. It converts approved analytical semantics and Evidence Contract requirements into deterministic cases against which a future implementation can be evaluated.

An Evaluation Fixture is not primarily an example, demo dataset, prompt, few-shot example, model-training record, or benchmark score. It is a governed evaluation contract: given the stated input condition, question, scope, and evidence, a conforming implementation must produce the specified analytical, validation, admissibility, qualification, and workflow behavior.

This specification defines fixture semantics only. It does not create physical fixture data, executable tests, Architecture, implementation, or benchmark scoring.

## 2. Authority and Governing Documents

This specification inherits, and must not reinterpret, the following approved and frozen documents:

1. `PROJECT_MASTER_INSTRUCTIONS.md` v1.1;
2. `PRD.md` v1.1;
3. `CommerceLens_Skill_First_Scope_Migration_Analysis_v1.1.md`;
4. `SKILL_SCOPE_SPECIFICATION.md` v1.0;
5. `EVIDENCE_CONTRACT_SPECIFICATION.md` v1.0; and
6. `CANONICAL_DATASET_AND_METRIC_DICTIONARY.md` v1.0.

The governing hierarchy remains authoritative. If a fixture conflicts with an approved semantic, the governing semantic wins and the fixture must be corrected through review. No fixture may create a local exception or alternative formula.

The derivation chain is:

Business Question → Canonical Dataset Semantics → Metric Dictionary → Evidence Contract → Fixture Input → Expected Deterministic Outcome → Expected Claim Behavior.

## 3. Evaluation Boundary

The suite is limited to the first canonical MVP Business Question:

> How did revenue performance change between two comparable periods, and which products or categories contributed most to that change?

Fixtures may evaluate only Revenue, Orders, AOV, Revenue Change, Revenue Change %, Product Revenue and Orders, Category Revenue and Orders, entity Revenue Change %, Absolute Contribution, Contribution Share of Net Revenue Change, positive and negative contribution ranking, comparable-period behavior, analytical population, data sufficiency, deterministic execution and validation, evidence traceability, claim admissibility, qualification, fail-closed behavior, and “Insufficient evidence to conclude.”

No fixture in this specification authorizes analysis of gross margin, discounts, Refund Rate, inventory, stockouts, retention, prediction, causation, or other non-canonical Metrics.

## 4. Fixture Definition and Authority

An **Evaluation Fixture** is an independently understandable and reproducible governed test case containing enough information to determine:

- the input condition and analytical request;
- applicable authoritative Metric definitions and canonical fields;
- required and available Evidence;
- expected Data Sufficiency and execution eligibility;
- an expected deterministic result or result constraint;
- expected validation and Metric-validity states;
- expected Claim admissibility and required qualification;
- prohibited interpretations;
- required Evidence Contract behavior; and
- the final workflow disposition.

Fixture labels do not themselves prove the condition being tested. For example, “product absent” is meaningful only when complete-period coverage proves genuine absence; “cancelled” requires governed eligibility evidence; and “duplicate” requires identity or provenance evidence.

## 5. Evaluation Fixture Specification vs Physical Fixture Data

This document is the **Evaluation Fixture Specification**. It may use conceptual rows, tiny synthetic arithmetic, expected constraints, and a conceptual fixture structure to make outcomes reviewable.

**Physical Fixture Data** means later serialized CSV, Excel, SQLite, JSON, YAML, database seeds, language objects, directories, or other executable assets. None are created or selected here. Physical serialization requires approved Architecture and later authorization, and must preserve the semantics in this specification.

## 6. Fixture Design Principles

1. **Determinism:** Two conforming evaluators must reach the same material judgment.
2. **Minimality:** Use the smallest synthetic case that proves the behavior.
3. **Isolation:** One primary contract behavior per fixture wherever practical; dependent Metrics may accompany it.
4. **Independence:** No fixture depends on execution order or state from another fixture.
5. **Reviewability:** A human can identify the rule, governing source, arithmetic, and Claim consequence.
6. **Public safety:** MVP fixtures are synthetic by preference and contain no proprietary seller, customer, URL, or confidential data.
7. **Implementation and host independence:** Expected behavior cannot depend on functions, queries, modules, prompts, agents, providers, storage engines, ChatGPT, Claude, Codex, CLI, or application host.
8. **Analytical correctness over plausibility:** A plausible but incorrectly derived value fails.
9. **Evidence traceability over coincidence:** An expected number without the required chain does not pass a material-Claim fixture.
10. **Reuse before rebuild:** Later implementation may reuse standard test and data libraries; this document prescribes no custom framework.
11. **One variant, one outcome:** One Fixture variant has one authoritative expected outcome. For every Fixture or stable subfixture, Expected Data Sufficiency, Execution Behavior, Validation State, Metric State, Claim State, required Qualification or Limitation, and Final Disposition must be fixed before evaluation. The evaluator applies that contract and does not choose among possible material outcomes.

Multiple input variants may share one Fixture ID only when they test the same governing contract and have the same expected Metric state, Claim admissibility, and final disposition. If any of those materially differ, the variants must receive separate Fixture IDs or stable subfixture identifiers such as `FX-XXX-001A` and `FX-XXX-001B`. Variant grouping must preserve fixture minimality and must never hide a different authoritative outcome.

## 7. Fixture Taxonomy

| Code | Category | Primary purpose |
|---|---|---|
| VALID | Positive / Valid | Prove the canonical happy path and valid controls |
| METRIC | Metric Edge Case | Prove zero-denominator, entry/exit, precision, and other governed Metric states |
| SUFF | Data Sufficiency Failure | Prove that missing Required Evidence blocks or narrows Claims |
| DQ | Data Quality Failure | Prove canonical-field, grain, identity, and mapping constraints |
| VAL | Validation Failure | Prove validation authority and reconciliation behavior |
| CLAIM | Claim Admissibility | Prove Claim type, strength, and prohibited interpretation behavior |
| QUAL | Qualification / Limitation | Prove admissible narrowed Claims and attached limitations |
| CONTRIB | Contribution Interpretation | Prove contribution arithmetic, ranking, and non-causal interpretation |
| CROSS | Cross-Metric Consistency | Prove shared population, non-additivity, formulas, and precision |
| CLOSED | Fail Closed | Prove that unavailable evidence, execution, or validation cannot be replaced by language |
| TRACE | Evidence Traceability | Prove the evidence-chain requirements for material Claims |

The categories may overlap, but each fixture has one primary category and one identifiable primary purpose.

## 8. Fixture Outcome Vocabulary

| Fixture outcome | Meaning |
|---|---|
| **PASS** | All material expected results, validation, Evidence, and Claim behavior conform without required qualification. |
| **PASS WITH QUALIFICATION** | A narrower result or Claim is valid and admissible only with an explicit, attached limitation. |
| **UNDEFINED METRIC** | Required inputs may be valid, but the authoritative Metric has no defined value under its formula or denominator rule. This is not missing Evidence. |
| **INSUFFICIENT EVIDENCE** | Material Required Evidence is absent for the intended Claim or scope; the affected Claim is blocked and the output must state “Insufficient evidence to conclude.” |
| **VALIDATION FAILURE** | Execution produced a result, but an applicable deterministic validation failed; the result cannot become a Validated Result for the intended use. |
| **INADMISSIBLE CLAIM** | A Claim exceeds the available Evidence, supported scope, Metric authority, validation state, or MVP Claim taxonomy. |
| **EXECUTION FAILURE** | Deterministic execution was attempted but did not produce a usable intended result. It is distinct from a failed validation of a produced result. |
| **PARTIAL COMPLETION** | One or more independent evidence chains completed while other requested components are Undefined, Inadmissible, unavailable, or failed. |
| **FAIL CLOSED** | The affected output is withheld without fabricated numbers, inferred missing values, narrative substitution, or weakened Metric definitions. |

These are evaluation concepts, not prescribed implementation enums. A fixture may require a fixed compound disposition, such as `INSUFFICIENT EVIDENCE + FAIL CLOSED`, when each component describes a different required aspect of the same single outcome.

## 9. Relationship to Metric Validity and Claim State

Metric validity remains **Valid**, **Qualified**, **Undefined**, or **Inadmissible** as defined by the Metric Dictionary. Fixture outcome and Metric state are related but not identical:

| Metric state | Typical fixture outcome | Claim consequence |
|---|---|---|
| Valid | PASS | May support an Admissible Claim when the full Evidence Contract is satisfied |
| Qualified | PASS WITH QUALIFICATION | Only the bounded Claim with its attached qualification is admissible |
| Undefined | UNDEFINED METRIC, possibly PARTIAL COMPLETION | No numeric value may be fabricated; independent valid Metrics may survive |
| Inadmissible | INSUFFICIENT EVIDENCE, INADMISSIBLE CLAIM, VALIDATION FAILURE, or FAIL CLOSED | Affected material Claim must be withheld |

Undefined Metric is not Insufficient Evidence. Validation Failure is not Execution Failure. A qualified Claim is not an inadmissible Claim rescued by wording.

### 9.1 Authoritative Outcome Profiles

The following profiles provide deterministic shorthand for the seven required expected-state elements. Every detailed Fixture or subfixture references exactly one profile. Row-specific Metric components or required wording refine the profile but may not introduce an alternative disposition.

| Profile | Expected Data Sufficiency | Expected Execution Behavior | Expected Validation State | Expected Metric State | Expected Claim State | Required Qualification / Limitation | Expected Final Disposition |
|---|---|---|---|---|---|---|---|
| **OP-PASS** | Sufficient | Successful | Passed | Valid | Admissible | None beyond ordinary scope disclosure | **PASS** |
| **OP-METRIC-QUAL** | Sufficient for the explicitly bounded analysis | Successful | Passed | The Fixture-identified Metric is Qualified; other identified Metrics are Valid | Qualified Admissibility | The Fixture-specific Metric/interpretation qualification must be attached to the affected Claim | **PASS WITH QUALIFICATION** |
| **OP-CLAIM-QUAL** | Sufficient for the explicitly bounded Claim | Successful | Passed | Valid | Qualified Admissibility | The Fixture-specific scope, presentation, or Recommendation limitation must be attached to the affected Claim | **PASS WITH QUALIFICATION** |
| **OP-PARTIAL-UNDEFINED** | Sufficient for defined Metrics | Successful | Passed for defined Metrics | Identified Metric Undefined; independent Metrics Valid | Admissible only for defined Metrics | Disclose the Undefined component and its governing reason | **PARTIAL COMPLETION** |
| **OP-INSUFF-CLOSED** | Insufficient for the affected requested scope | Must not proceed for the affected computation | Not reached | Inadmissible for the affected scope | Inadmissible | Identify the missing/invalid Evidence and state “Insufficient evidence to conclude.” | **INSUFFICIENT EVIDENCE + FAIL CLOSED** |
| **OP-VAL-CLOSED** | Sufficient to execute the intended governed operation | Successful, producing an Executed Result | Failed | Inadmissible for material use | Inadmissible | Disclose the failed validation; no narrative override | **VALIDATION FAILURE + FAIL CLOSED** |
| **OP-EXEC-CLOSED** | Sufficient to plan and attempt execution | Failed | Not reached | No usable Metric result; Inadmissible | Inadmissible | Disclose the execution failure; no numerical substitute | **EXECUTION FAILURE + FAIL CLOSED** |
| **OP-CLAIM-INAD** | Sufficient for the validated bounded analytical result, but insufficient for the stronger target Claim | Successful | Passed | Valid for the bounded analytical result | Target Claim Inadmissible | State the Claim boundary and retain only the explicitly identified weaker Claim, if required by the Fixture | **INADMISSIBLE CLAIM** |
| **OP-TRACE-CLOSED** | Insufficient for material Claim admissibility because required traceability is absent | Successful, with an Execution Record and numerical result | Not established for the intended material use | Inadmissible for material use | Inadmissible | Identify the missing evidence-chain element; do not treat the number as Admissible Evidence | **INADMISSIBLE CLAIM + FAIL CLOSED** |

`PASS WITH QUALIFICATION` means the governed workflow completed correctly while preserving a required Metric, Evidence, scope, or interpretation qualification. It does not mean that the workflow failed.

## 10. Standard Conceptual Fixture Structure

Every physical fixture derived later must represent, directly or by an unambiguous governed reference:

| Field | Required content |
|---|---|
| Fixture ID / Name / Category | Stable human-readable identity and primary taxonomy |
| Purpose | Single primary contract behavior |
| Business Question / Request | Canonical question or supported sub-request |
| Input Condition | Synthetic source/canonical conditions and the condition under test |
| Relevant Canonical Fields | Only fields material to the case |
| Baseline / Comparison Period | Explicit bounds and completeness/comparability evidence when applicable |
| Applicable Metrics | Approved Metrics exercised by the fixture |
| Required / Available Evidence | Claim- and scope-specific evidence expectations |
| Expected Data Sufficiency | Sufficient, qualifying, or insufficient, with reason |
| Expected Execution Behavior | Proceed, do not proceed, partial, unavailable, failed, or successful |
| Expected Result / Constraint | Exact value where needed; otherwise a deterministic constraint |
| Expected Validation | Applicable checks and their expected outcome |
| Expected Metric State | Valid, Qualified, Undefined, or Inadmissible per affected Metric |
| Expected Claim State | Admissible, Qualified Admissibility, or Inadmissible |
| Required Qualification / Limitation | Claim-attached wording requirement or semantic constraint |
| Prohibited Claim / Interpretation | Output that must not occur |
| Expected Final Disposition | Fixture outcome vocabulary from Section 8 |
| Governing Contract Reference | Document and semantic section/title; no fabricated requirement IDs |
| Notes | Only information necessary for independent review |

This is not a JSON schema and does not prescribe storage.

## 11. Fixture ID Convention

IDs use `FX-<CATEGORY>-<NNN>`, for example `FX-VALID-001`, `FX-METRIC-001`, and `FX-VAL-001`. Stable subfixtures append an uppercase letter, for example `FX-DQ-003A`. IDs are stable traceability labels. An ID must not be reused for a materially different contract. Minor wording corrections that preserve semantics do not require a new ID; semantic changes require governance review.

## 12. Foundational Valid Canonical Fixture

### FX-VALID-001 — Canonical Two-Period Revenue and Contribution

**Purpose:** Baseline positive control for the complete first workflow.

**Synthetic conceptual input:** Two complete, equal-duration, non-overlapping periods use one currency and valid eligibility. Every row has unique (`order_id`, `order_line_id`), one valid `product_id`, exactly one category, positive whole-number quantity, and governed `line_revenue`. Baseline lines are: B1/A/C1/60, B1/B/C2/40, B2/A/C1/50, B3/C/C2/50. Comparison lines are: C1/A/C1/80, C1/B/C2/20, C2/A/C1/60, C3/C/C2/20, C4/D/C3/60. Each tuple is `order/product/category/line_revenue`; B1 and C1 are multi-line orders. Values are synthetic and use authoritative decimal semantics.

**Expected results:**

- Baseline Revenue = 200; Orders = 3; AOV = 200/3.
- Comparison Revenue = 240; Orders = 4; AOV = 60.
- Revenue Change = +40; Revenue Change % = +20%.
- Product Revenue changes / Absolute Contributions: A +30, B -20, C -30, D +60.
- Positive ranking: D, then A. Negative ranking: C, then B.
- Category Absolute Contributions: C1 +30, C2 -50, C3 +60.
- Product and category contributions each reconcile exactly to +40.
- Contribution Shares are valid but qualified because positive and negative movements coexist; they use +40 as denominator and remain secondary to Absolute Contribution.

**Evidence and disposition (`OP-METRIC-QUAL`):** Period coverage, currency, dataset identity, Metric references, successful Execution Records, passing Validation Records, scope, assumptions, and limitations are available. Revenue, Orders, AOV, Revenue Change, Absolute Contribution, and rankings are Valid. Contribution Share is Qualified because positive and negative movements coexist. Material Claims are Qualified Admissible only to the extent that the approved Contribution Share interpretation qualification is attached. Final disposition: **PASS WITH QUALIFICATION**. This disposition confirms successful completion of the canonical workflow; it does not indicate workflow failure. No causal Claim is allowed.

## 13. Detailed Minimum Fixture Specifications

The following compact specifications are authoritative. “Evidence” identifies what must be established beyond the fixture label. “Expected” includes calculation, validation, Metric state, Claim behavior, qualification, and final disposition.

### 13.1 Grain, identity, and order behavior

| ID | Input condition and Required Evidence | Deterministic expected behavior |
|---|---|---|
| **FX-VALID-002 Multi-Line Order** | One eligible order contains lines for two products/categories; unique line identities and common order date are proven. | **OP-PASS.** Sum both lines for Revenue; total Orders = 1; each product/category has Product/Category Orders = 1. Never sum entity Orders to reconstruct total Orders. |
| **FX-DQ-001 Repeated Product Lines** | Same `product_id` occurs on two legitimate lines of one order with distinct `order_line_id`; provenance supports both lines. | **OP-PASS.** Retain both lines and both monetary values; Product Orders = 1 for that product. No false deduplication. |
| **FX-DQ-002 Exact Duplicate Identity** | Repeated (`order_id`, `order_line_id`) with no traceable resolution. | **OP-INSUFF-CLOSED.** Canonical uniqueness fails; no arbitrary row deletion or Revenue computation from a guessed representation. |
| **FX-DQ-003A Stable ID with Changed Name** | The same `product_id` has materially different names across periods; source identity is stable, and the naming ambiguity is documented. | **OP-CLAIM-QUAL.** Treat the rows as one product. Product Metrics remain Valid; the attached presentation limitation states that the label changed while ID continuity governed grouping. |
| **FX-DQ-003B Same Name with Different IDs** | Two different stable `product_id` values share one `product_name`; identities and periods are otherwise valid. | **OP-PASS.** Keep the products separate. Grouping by name is prohibited; no qualification is required because identity evidence is unambiguous. |
| **FX-DQ-004 Missing Product Identity** | An eligible monetary row lacks `product_id`; the row's known Revenue is material to the requested complete product-contribution workflow. | **OP-INSUFF-CLOSED.** Product Performance and Product Contribution are Inadmissible; `product_name` fallback is prohibited. The requested complete workflow must not proceed. Total-only analysis is outside this Fixture's request and is not an alternative disposition. |
| **FX-DQ-005 Silent Deduplication Trap** | Similar amounts, dates, and product values lack shared authoritative identity or provenance proving duplication; the unresolved ambiguity affects the requested scope. | **OP-INSUFF-CLOSED.** Do not delete duplicate-looking rows or invent a deduplicated result. |
| **FX-CROSS-001 Non-Additive Orders Trap** | Valid multi-product and multi-category orders are executed with a candidate total formed by summing entity Orders. | **OP-VAL-CLOSED.** Authoritative total is distinct `order_id` at target scope; the summed Product/Category Orders result fails validation. |

### 13.2 Zero, entry/exit, and contribution edge cases

| ID | Input condition and Required Evidence | Deterministic expected behavior |
|---|---|---|
| **FX-METRIC-001 Zero Baseline Revenue** | Complete Baseline Revenue = 0; valid Comparison Revenue > 0. | **OP-PARTIAL-UNDEFINED.** Absolute Revenue Change is Valid; Revenue Change % is Undefined. “Increase from zero” is admissible; any percentage is prohibited. |
| **FX-METRIC-002 Both Periods Zero** | Complete coverage proves both period Revenues = 0. | **OP-PARTIAL-UNDEFINED.** Revenue is Valid; Revenue Change = 0; Revenue Change % and all Contribution Shares are Undefined. No percentage or share may be generated. |
| **FX-CONTRIB-001 Zero Net Change with Offsets** | Complete partition has entity changes +50 and -50. | **OP-PARTIAL-UNDEFINED.** Absolute Contributions and separated rankings are Valid and reconcile to 0; Contribution Share is Undefined. “No product changed” is prohibited. |
| **FX-CONTRIB-002 Non-Zero Small Net with Offsets** | Complete partition has large positive and negative changes with non-zero small net; no threshold assumption. | **OP-METRIC-QUAL.** Contribution Share is Qualified; values may exceed 100% or be negative. Rank only by unrounded Absolute Contribution and attach the netting/denominator qualification. |
| **FX-METRIC-003A Entity Entry** | Product and category variants use complete periods to prove the entity genuinely absent in Baseline; category attribution is stable and exclusive. | **OP-PARTIAL-UNDEFINED.** Baseline entity Revenue = 0, Comparison Revenue and positive Absolute Contribution are Valid, and entity Revenue Change % is Undefined. Include the entity in the period union and reconcile. |
| **FX-METRIC-003B Entity Exit** | Product and category variants use complete periods to prove the entity genuinely absent in Comparison; Baseline entity Revenue is greater than zero and category attribution is stable and exclusive. | **OP-PASS.** Comparison entity Revenue = 0; entity Revenue Change, negative Absolute Contribution, and Revenue Change % are Valid. Include the entity in the period union and reconcile. |
| **FX-CONTRIB-003 Ranking Precision and True Ties** | Variant A has contributors differing below display precision. Variant B has contributors exactly equal at authoritative precision. | **OP-PASS for both variants.** A ranks by unrounded Absolute Contribution despite a displayed tie. B preserves the true tie. Both have the same Valid Metric state, Admissible Claim state, and PASS disposition. |

### 13.3 Category attribution and claim sensitivity

| ID | Input condition and Required Evidence | Deterministic expected behavior |
|---|---|---|
| **FX-QUAL-001 Missing Category to Unclassified** | Otherwise valid eligible line lacks `category_id`. | **OP-METRIC-QUAL.** Map exactly once to visible `Unclassified`; retain it in total and category reconciliation. The attached limitation states that category analysis includes unclassified attribution. |
| **FX-CLAIM-001 Unclassified Claim-Sensitive** | Valid category results include `Unclassified`; its contribution/revenue could change the requested comprehensive named-category leader or ordering Claim. | **OP-CLAIM-INAD.** The comprehensive Claim is Inadmissible. `Unclassified` remains visible. The required weaker output is a Qualified Admissible statement explicitly bounded as “Among classified categories…”. No arbitrary threshold applies. |
| **FX-QUAL-002 Unclassified Non-Blocking** | `Unclassified` exists, and the request is expressly bounded to a statement among classified categories. | **OP-CLAIM-QUAL.** Category Metrics for the stated scope are Valid; the bounded Claim is Qualified Admissible with “Among classified categories…” attached. An unqualified complete-category Claim is prohibited. |
| **FX-DQ-006A Governed Category Classification Change** | A documented row-level observed category change preserves exactly one category per line and a complete reconciliation partition. | **OP-METRIC-QUAL.** Category Performance and Contribution are Qualified; the attached limitation discloses the governed classification change. |
| **FX-DQ-006B Unresolved Category Mapping Inconsistency** | Conflicting mapping evidence cannot establish one governed category per affected line, and the affected Revenue is material to Category Performance/Contribution. | **OP-INSUFF-CLOSED.** Category Performance and Contribution are Inadmissible. No taxonomy repair is invented. |

### 13.4 Monetary, eligibility, refund, and quantity boundaries

| ID | Input condition and Required Evidence | Deterministic expected behavior |
|---|---|---|
| **FX-SUFF-001 Currency Insufficiency Variants** | Variant A contains multiple currencies not normalized upstream. Variant B has authoritative monetary rows without governed currency evidence. | **OP-INSUFF-CLOSED for both variants.** A performs no aggregation, FX conversion, web lookup, or approximation. B does not infer currency from symbols, locale, or geography. The variants share the same Inadmissible Metric state, Claim state, and final disposition. |
| **FX-DQ-007 Invalid Quantity Variants** | Four isolated variants have quantity zero, negative, fractional, or missing; each affected line has unknown or material impact on the requested scope. | **OP-INSUFF-CLOSED for every variant.** Each line is invalid because quantity must be a positive whole number. Negative is not a return; missing is not zero. |
| **FX-METRIC-005 Material Zero-Value Eligible Line** | A genuine eligible `line_revenue = 0` line has valid positive quantity, identities, and currency; its order materially affects AOV interpretation. | **OP-CLAIM-QUAL.** Revenue, Orders, and AOV are Valid. The line adds zero Revenue, its eligible order counts once, and the attached interpretation limitation discloses the material zero-value-order effect. |
| **FX-SUFF-003 Missing Revenue Input** | Required `line_revenue` is null; optional quantity/unit price exists but no governed upstream canonicalization has occurred. | **OP-INSUFF-CLOSED.** Unknown is not zero; do not derive `quantity × unit_price`. |
| **FX-METRIC-006A Undeclared Unit-Price Semantic Conflict** | Governed `line_revenue` differs from `quantity × unit_price`; unit-price semantics and any validation relationship are undeclared. | **OP-PASS.** `line_revenue` controls Revenue. The mismatch does not redefine or invalidate Revenue, and `unit_price` does not become co-authoritative. |
| **FX-METRIC-006B Declared Unit-Price Validation Failure** | A separately governed, material validation relationship between `line_revenue` and `unit_price` is declared, and the Executed Result violates that exact relationship. | **OP-VAL-CLOSED.** `line_revenue` remains monetary authority, but the declared supporting validation fails for the intended material use. |
| **FX-VALID-003 Cancelled and Fully Refunded Exclusion** | Valid-looking monetary rows are unambiguously governed as cancelled or fully refunded; eligible control rows exist. | **OP-PASS.** Exclude those rows before every MVP Metric. Revenue, Orders, AOV, entity performance, and contribution use only eligible lines. |
| **FX-CLOSED-001 Unsupported Partial Refund** | Partial-refund effects exist, but no governed final eligible `line_revenue` is provided. | **OP-INSUFF-CLOSED.** Do not reconstruct net Revenue, create negative lines, or invent a refund ledger. |

### 13.5 Comparable periods and date integrity

| ID | Input condition and Required Evidence | Deterministic expected behavior |
|---|---|---|
| **FX-SUFF-004 Incomplete Period** | One period lacks source coverage and has no independent completeness evidence. | **OP-INSUFF-CLOSED.** Missing dates remain unknown, not zero-activity dates. Normal comparison must not proceed. |
| **FX-SUFF-005 Invalid Period Bounds Variants** | Variant A has unequal governed calendar-date counts. Variant B has overlapping period bounds. | **OP-INSUFF-CLOSED for both variants.** Canonical comparability fails. Do not normalize per day, invent another comparison, or alter dates. Both variants share the same Inadmissible Metric and Claim states and final disposition. |
| **FX-DQ-008 Inconsistent Order Dates** | Lines of one order have different `order_date`; source evidence does not resolve assignment, and the affected order can change the comparison result. | **OP-INSUFF-CLOSED.** Do not split the order or choose the first/last date. |

### 13.6 Validation, execution, consistency, and precision

| ID | Input condition and Required Evidence | Deterministic expected behavior |
|---|---|---|
| **FX-VAL-001 Product and Category Reconciliation** | Valid complete product partition and category partition including `Unclassified`. | **OP-PASS.** Each sum of Absolute Contributions equals Total Revenue Change at authoritative precision. No residual is permitted. |
| **FX-VAL-002 Deliberate Reconciliation Failure** | Execution successfully returns entity results with an unexplained residual against total change. | **OP-VAL-CLOSED.** No Validated Result or material Finding may arise from that chain; narrative cannot repair it. |
| **FX-CLOSED-002 Execution Failure** | The requested deterministic operation is attempted, produces no usable result, and no independent requested evidence chain completes. | **OP-EXEC-CLOSED.** Record Execution Failure distinctly; fabricate no result and perform no language-model substitute. |
| **FX-CROSS-002 Population Mismatch** | Execution produces Revenue excluding cancelled rows while Orders includes them, creating incompatible AOV inputs. | **OP-VAL-CLOSED.** Common-population and AOV consistency validation fail. |
| **FX-CROSS-003 Presentation Precision Variants** | Variant A has AOV requiring more precision than displayed. Variant B has display-rounded period Revenues that yield a different Revenue Change % than full precision. | **OP-PASS for both variants.** A calculates and validates AOV from unrounded Revenue/Orders; B computes percentage from unrounded period Revenues. Both variants have Valid Metrics, Admissible Claims, no required qualification, and PASS disposition. |
| **FX-VAL-003 Wrong AOV Formula** | Execution produces a candidate result by averaging subgroup AOVs rather than target-scope Revenue/distinct Orders. | **OP-VAL-CLOSED.** Reject the result even when plausible or coincidentally close. |

### 13.7 Claims, recommendations, and evidence chain

| ID | Input condition and Required Evidence | Deterministic expected behavior |
|---|---|---|
| **FX-CLAIM-002 Contribution Is Not Causation** | A Validated Result identifies the largest negative Absolute Contribution, and the requested target Claim states that the product caused the decline. | **OP-CLAIM-INAD.** The causal Claim is Inadmissible. The required weaker output states only that the product was the leading negative contributor to observed Revenue Change. |
| **FX-CLAIM-003 Unsupported External Explanation** | A Validated Result shows Revenue decline, and the requested target Claim attributes it to an external explanation without supporting Evidence. | **OP-CLAIM-INAD.** The external causal Claim is Inadmissible. The explanation must remain an Alternative Explanation rather than a Finding. |
| **FX-CLAIM-004 Bounded Recommendation and Human Ownership** | Valid descriptive/diagnostic Findings support only a bounded recommendation to review or investigate the validated high-contribution segment; causal/predictive support is absent. | **OP-CLAIM-QUAL.** The underlying Metrics are Valid. The Recommendation is Qualified Admissible only when traceable, proportional, attached to the material assumptions/limitations, framed as investigation, and explicit that the human retains decision ownership. Autonomous or causally certain prescription is prohibited. |
| **FX-TRACE-001 Missing Evidence Chain** | A successful Execution Record and numerically correct value exist, but the required Metric Reference and Validation Record are absent for the intended material use. | **OP-TRACE-CLOSED.** The number cannot become Admissible Evidence or a material Finding. Both missing chain elements must be identified. |
| **FX-CROSS-005 Wrong Contribution Ranking** | Execution ranks entities by Contribution Share rather than unrounded Absolute Contribution. | **OP-VAL-CLOSED.** Ranking validation fails; Contribution Share remains secondary context. |
| **FX-CROSS-006 Silent Missing-to-Zero** | Source evidence contains missing `line_revenue` in the requested scope; the system must decide eligibility before execution, and no independently valid requested scope remains. | **OP-INSUFF-CLOSED.** Unknown remains unknown; execution must not convert it to zero. Genuine zero and proven absence remain distinct but are not alternative outcomes in this Fixture. |

## 14. Partial Completion Contract

Fixtures must preserve independent valid results. For example, under `FX-METRIC-001`, valid absolute Revenue Change survives while Revenue Change % remains Undefined. A fixture passes only if the implementation:

- identifies completed evidence chains separately from blocked or incomplete chains;
- reports only independently Validated Results as material Findings;
- labels the overall workflow as partial when required portions remain blocked;
- withholds the unsupported component; and
- does not convert one valid component into false full success or one failed component into unnecessary total failure.

## 15. Evidence and Claim Evaluation Requirements

The Evidence Contract requirement is fixture- and Claim-specific; not every fixture must exercise every entity. At minimum:

- material KPI, period-comparison, contribution, and ranking Claims require the Business Question, scope, authoritative Metric Reference, Dataset Reference, Data Sufficiency assessment, successful Execution Record, applicable passing Validation Record, and traceability to a Validated Result;
- a fixture testing insufficiency requires the relevant Required Evidence, Available Evidence, identified gap, affected scope/Claim, and correct fail-closed conclusion;
- a fixture testing execution failure requires an Execution Record that distinguishes attempted failure from absence of execution and from validation failure;
- a fixture testing validation failure requires an Executed Result and a Validation Record identifying the failed invariant;
- a qualified fixture requires a complete core evidence chain plus an attached, Claim-specific non-blocking limitation;
- Recommendation fixtures additionally require admissible supporting Findings, proportionality, assumptions/limitations where material, and explicit Human Decision Ownership.

Required Evidence, Available Evidence, Validated Result, and Admissible Evidence remain distinct. Not every Evidence item undergoes deterministic validation, but every material numerical Finding must trace to an appropriately Validated Result.

## 16. Deterministic Validation Requirements

When applicable, fixtures must test:

1. canonical composite identity uniqueness;
2. valid required fields and positive-whole-number quantity;
3. one governed currency and common eligible population;
4. equal-duration, complete, non-overlapping periods with consistent order dates;
5. Revenue from governed `line_revenue` only;
6. Orders as distinct eligible `order_id` at target scope;
7. AOV as unrounded Revenue / Orders for the same population;
8. Revenue Change and percentage from authoritative unrounded period values;
9. product grouping by `product_id` and exclusive category attribution including `Unclassified`;
10. product and category contribution accounting identities at authoritative precision;
11. Contribution Share only with non-zero total change and as secondary qualified context when offsets exist; and
12. rankings from unrounded Absolute Contribution with separated positive/negative lists and genuine ties preserved.

Executed Result does not equal Validated Result. A failed invariant cannot be repaired by explanation, prose, confidence, or a coincidentally plausible number.

## 17. Fail-Closed Requirements

Where a fixture expects fail-closed behavior, a conforming output must:

- produce no fabricated numerical result;
- issue no unsupported material Claim;
- use no language-based replacement for deterministic execution;
- apply no silent imputation, deduplication, date alteration, FX conversion, population change, or Metric weakening;
- prevent failed or unvalidated results from becoming Findings or Recommendation support; and
- state “Insufficient evidence to conclude.” when Required Evidence is materially absent for the affected conclusion.

Fail closed applies to the affected evidence chain, not automatically to unrelated, independently complete chains.

## 18. Deterministic Fixture Conformance

A future implementation passes a fixture only when **all material expectations** match, including those applicable to:

- execution eligibility and execution state;
- exact number or deterministic result constraint;
- Metric validity and undefined behavior;
- validation outcome;
- Claim classification and admissibility;
- required qualification and limitation;
- fail-closed and partial-completion behavior;
- evidence traceability; and
- absence of prohibited Claims or interpretations.

A numerically correct output fails when its formula, population, evidence chain, validation state, Claim strength, or qualification is non-conforming. A well-written narrative fails when the Metric calculation or validation is wrong. No scores, weights, percentages, grades, partial credit, leaderboard values, or pass thresholds are defined here.

## 19. Minimum MVP Fixture Inventory

| Fixture ID | Fixture Name | Primary Category | Primary contract tested | Expected high-level outcome | MVP? |
|---|---|---|---|---|---|
| FX-VALID-001 | Canonical Two-Period Revenue and Contribution | VALID | Complete happy path with qualified Contribution Share | PASS WITH QUALIFICATION | Yes |
| FX-VALID-002 | Multi-Line Order | VALID | Line grain and distinct Orders | PASS | Yes |
| FX-DQ-001 | Repeated Product Lines | DQ | Legitimate repeated lines | PASS | Yes |
| FX-DQ-002 | Exact Duplicate Identity | DQ | Grain uniqueness | INSUFFICIENT EVIDENCE + FAIL CLOSED | Yes |
| FX-DQ-003A | Stable ID with Changed Name | DQ | ID continuity and presentation ambiguity | PASS WITH QUALIFICATION | Yes |
| FX-DQ-003B | Same Name with Different IDs | DQ | ID authority over name | PASS | Yes |
| FX-DQ-004 | Missing Product Identity | DQ | Product-capable canonical contract | INSUFFICIENT EVIDENCE + FAIL CLOSED | Yes |
| FX-DQ-005 | Silent Deduplication Trap | DQ | Provenance before deletion | INSUFFICIENT EVIDENCE + FAIL CLOSED | Yes |
| FX-CROSS-001 | Non-Additive Orders Trap | CROSS | Entity Orders not additive | VALIDATION FAILURE + FAIL CLOSED | Yes |
| FX-METRIC-001 | Zero Baseline Revenue | METRIC | Undefined percentage | PARTIAL COMPLETION | Yes |
| FX-METRIC-002 | Both Periods Zero | METRIC | Undefined percent/share | PARTIAL COMPLETION | Yes |
| FX-CONTRIB-001 | Zero Net Change with Offsets | CONTRIB | Valid absolute movement, undefined share | PARTIAL COMPLETION | Yes |
| FX-CONTRIB-002 | Non-Zero Small Net with Offsets | CONTRIB | Share sign/magnitude qualification | PASS WITH QUALIFICATION | Yes |
| FX-METRIC-003A | Entity Entry | METRIC | Entity union and genuine baseline absence | PARTIAL COMPLETION | Yes |
| FX-METRIC-003B | Entity Exit | METRIC | Entity union and genuine comparison absence | PASS | Yes |
| FX-CONTRIB-003 | Ranking Precision and True Ties | CONTRIB | Unrounded ranking | PASS | Yes |
| FX-QUAL-001 | Missing Category to Unclassified | QUAL | Recoverable attribution | PASS WITH QUALIFICATION | Yes |
| FX-CLAIM-001 | Unclassified Claim-Sensitive | CLAIM | Claim sensitivity | INADMISSIBLE CLAIM | Yes |
| FX-QUAL-002 | Unclassified Non-Blocking | QUAL | Bounded classified claim | PASS WITH QUALIFICATION | Yes |
| FX-DQ-006A | Governed Category Classification Change | DQ | Disclosed exclusive row-level change | PASS WITH QUALIFICATION | Yes |
| FX-DQ-006B | Unresolved Category Mapping Inconsistency | DQ | Inadmissible category mapping | INSUFFICIENT EVIDENCE + FAIL CLOSED | Yes |
| FX-SUFF-001 | Currency Insufficiency Variants | SUFF | Single-currency and currency-evidence contract | INSUFFICIENT EVIDENCE + FAIL CLOSED | Yes |
| FX-DQ-007 | Invalid Quantity Variants | DQ | Positive whole number | INSUFFICIENT EVIDENCE + FAIL CLOSED | Yes |
| FX-METRIC-005 | Material Zero-Value Eligible Line | METRIC | Zero ≠ missing and AOV interpretation | PASS WITH QUALIFICATION | Yes |
| FX-SUFF-003 | Missing Revenue Input | SUFF | `line_revenue` authority | INSUFFICIENT EVIDENCE + FAIL CLOSED | Yes |
| FX-METRIC-006A | Undeclared Unit-Price Semantic Conflict | METRIC | Monetary authority | PASS | Yes |
| FX-METRIC-006B | Declared Unit-Price Validation Failure | VAL | Declared validation authority | VALIDATION FAILURE + FAIL CLOSED | Yes |
| FX-VALID-003 | Cancelled and Fully Refunded Exclusion | VALID | Eligibility authority | PASS | Yes |
| FX-CLOSED-001 | Unsupported Partial Refund | CLOSED | Refund boundary | INSUFFICIENT EVIDENCE + FAIL CLOSED | Yes |
| FX-SUFF-004 | Incomplete Period | SUFF | Coverage ≠ zero activity | INSUFFICIENT EVIDENCE + FAIL CLOSED | Yes |
| FX-SUFF-005 | Invalid Period Bounds Variants | SUFF | Equal duration and non-overlap | INSUFFICIENT EVIDENCE + FAIL CLOSED | Yes |
| FX-DQ-008 | Inconsistent Order Dates | DQ | One order date | INSUFFICIENT EVIDENCE + FAIL CLOSED | Yes |
| FX-VAL-001 | Product and Category Reconciliation | VAL | Accounting identities | PASS | Yes |
| FX-VAL-002 | Deliberate Reconciliation Failure | VAL | Executed ≠ Validated | VALIDATION FAILURE + FAIL CLOSED | Yes |
| FX-CLOSED-002 | Execution Failure | CLOSED | Execution vs validation | EXECUTION FAILURE + FAIL CLOSED | Yes |
| FX-CROSS-002 | Population Mismatch | CROSS | Common population / AOV | VALIDATION FAILURE + FAIL CLOSED | Yes |
| FX-CROSS-003 | Presentation Precision Variants | CROSS | AOV and percentage precision | PASS | Yes |
| FX-VAL-003 | Wrong AOV Formula | VAL | Metric formula authority | VALIDATION FAILURE + FAIL CLOSED | Yes |
| FX-CLAIM-002 | Contribution Is Not Causation | CLAIM | Diagnostic boundary | INADMISSIBLE CLAIM | Yes |
| FX-CLAIM-003 | Unsupported External Explanation | CLAIM | Hypothesis vs Finding | INADMISSIBLE CLAIM | Yes |
| FX-CLAIM-004 | Bounded Recommendation and Human Ownership | CLAIM | Proportional decision support | PASS WITH QUALIFICATION | Yes |
| FX-TRACE-001 | Missing Evidence Chain | TRACE | Traceability over coincidence | INADMISSIBLE CLAIM + FAIL CLOSED | Yes |
| FX-CROSS-005 | Wrong Contribution Ranking | CROSS | Absolute Contribution ranking | VALIDATION FAILURE + FAIL CLOSED | Yes |
| FX-CROSS-006 | Silent Missing-to-Zero | CROSS | Unknown ≠ zero | INSUFFICIENT EVIDENCE + FAIL CLOSED | Yes |

The suite retains 40 base Fixture families. Four families use stable A/B subfixtures because their variants have materially different Metric states, Claim states, or final dispositions: `FX-DQ-003`, `FX-METRIC-003`, `FX-DQ-006`, and `FX-METRIC-006`. `FX-DQ-007` retains four quantity variants, while `FX-SUFF-001`, `FX-SUFF-005`, `FX-CROSS-003`, and `FX-CONTRIB-003` retain grouped variants because every variant within each family has the same authoritative state and final disposition. This identifier clarification does not expand analytical scope or add a new contract case.

## 20. Coverage Matrix

`✓` means primary or direct coverage; `○` means dependent or supporting coverage. Blank cells are intentionally not exercised.

| Fixture group / IDs | Grain | Rev | Ord | AOV | ΔRev / % | Prod ID | Cat ID | Prod/Cat contrib | Share/rank | Period | Curr | Elig | Missing | Dup | Prec | Suff | Exec | Val | Claim | Qual | Closed | Trace | ≠ Cause |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| VALID-001 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |  | ✓ | ✓ | ○ | ✓ | ✓ | ✓ | ✓ |  | ✓ | ○ |
| VALID-002, DQ-001, CROSS-001 | ✓ | ○ | ✓ | ○ |  | ○ | ○ |  |  |  |  | ✓ |  | ○ |  |  | ✓ | ✓ | ○ |  |  | ○ |  |
| DQ-002, DQ-005 | ✓ | ✓ | ○ | ○ | ○ |  |  | ○ |  |  |  |  |  | ✓ |  | ✓ | ○ | ✓ | ✓ |  | ✓ | ✓ |  |
| DQ-003A, DQ-003B, DQ-004 | ○ | ○ | ○ |  | ○ | ✓ |  | ✓ | ✓ | ○ |  |  | ✓ |  |  | ✓ | ○ | ✓ | ✓ | ✓ | ✓ | ✓ |  |
| METRIC-001, METRIC-002 |  | ✓ | ○ | ○ | ✓ |  |  | ○ | ✓ | ✓ | ✓ | ✓ |  |  | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ○ | ✓ |  |
| CONTRIB-001, CONTRIB-002, CONTRIB-003 |  | ✓ |  |  | ✓ | ○ | ○ | ✓ | ✓ | ✓ | ○ | ○ |  |  | ✓ | ○ | ✓ | ✓ | ✓ | ✓ |  | ✓ | ✓ |
| METRIC-003A, METRIC-003B |  | ✓ | ○ |  | ✓ | ✓ | ✓ | ✓ | ○ | ✓ | ○ | ○ | ✓ |  | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |  | ✓ |  |
| QUAL-001, CLAIM-001, QUAL-002, DQ-006A, DQ-006B | ○ | ✓ | ○ |  | ○ |  | ✓ | ✓ | ✓ | ○ |  | ○ | ✓ |  |  | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ○ |
| SUFF-001 |  | ✓ |  | ✓ | ✓ |  |  | ✓ | ✓ | ○ | ✓ | ○ | ✓ |  |  | ✓ |  | ○ | ✓ |  | ✓ | ✓ |  |
| DQ-007, METRIC-005, SUFF-003, CROSS-006 | ○ | ✓ | ✓ | ✓ | ○ | ○ | ○ | ○ |  | ○ | ○ | ✓ | ✓ |  | ○ | ✓ | ○ | ✓ | ✓ | ✓ | ✓ | ✓ |  |
| METRIC-006A, METRIC-006B, VALID-003, CLOSED-001 | ○ | ✓ | ✓ | ✓ | ✓ | ○ | ○ | ○ |  | ○ | ○ | ✓ | ✓ |  | ○ | ✓ | ○ | ✓ | ✓ | ✓ | ✓ | ✓ |  |
| SUFF-004, SUFF-005, DQ-008 | ○ | ✓ | ✓ | ✓ | ✓ | ○ | ○ | ○ | ○ | ✓ | ○ | ○ | ✓ |  |  | ✓ |  | ✓ | ✓ |  | ✓ | ✓ |  |
| VAL-001, VAL-002 | ○ | ✓ |  |  | ✓ | ✓ | ✓ | ✓ | ○ | ○ | ○ | ○ |  |  | ✓ | ○ | ✓ | ✓ | ✓ |  | ✓ | ✓ | ○ |
| CLOSED-002 |  | ○ | ○ | ○ | ○ |  |  | ○ |  |  |  |  |  |  |  | ○ | ✓ |  | ✓ |  | ✓ | ✓ |  |
| CROSS-002, CROSS-003, VAL-003 | ○ | ✓ | ✓ | ✓ | ✓ |  |  |  |  | ○ | ○ | ✓ |  |  | ✓ | ○ | ✓ | ✓ | ✓ | ○ | ○ | ✓ |  |
| CLAIM-002, CLAIM-003, CLAIM-004 |  | ○ |  |  | ○ | ○ | ○ | ✓ | ✓ | ○ |  |  |  |  |  | ○ | ○ | ○ | ✓ | ✓ | ○ | ✓ | ✓ |
| TRACE-001, CROSS-005 |  | ○ | ○ | ○ | ○ | ○ | ○ | ✓ | ✓ | ○ | ○ | ○ | ○ |  | ✓ | ✓ | ✓ | ✓ | ✓ | ○ | ✓ | ✓ | ○ |

This matrix is a coverage map only. It creates no score, weight, grade, or benchmark threshold.

## 21. Positive and Negative Controls

The suite includes positive controls (`FX-VALID-001`, `FX-VALID-002`, `FX-DQ-001`, `FX-VALID-003`, and precision controls) that must succeed, and negative controls that must become Undefined, Qualified, Inadmissible, failed, partial, or fail closed. A suite containing only successful arithmetic is non-conforming because it cannot prove claim discipline or failure behavior.

## 22. High-Value Semantic Mutations for Future Detection

Without defining mutation-testing infrastructure, future execution against this suite must be capable of exposing these semantic mutations:

- counting rows as Orders;
- deriving Revenue from `unit_price` rather than governed `line_revenue`;
- including cancelled or fully refunded rows;
- averaging subgroup AOVs;
- reversing Baseline and Comparison;
- computing a percentage with zero denominator;
- grouping products by name;
- assigning one line to multiple categories or dropping `Unclassified`;
- ranking by Contribution Share;
- converting missing values or incomplete coverage to zero;
- silently deleting suspected duplicates;
- using display-rounded values in calculation or validation;
- summing Product or Category Orders into total Orders; and
- issuing Findings after failed execution or validation.

Detection means the mutated behavior fails the applicable deterministic fixture criteria; no mutation framework is selected here.

## 23. Cross-Fixture Consistency Rules

Across every fixture:

- zero Baseline Revenue makes the relevant Revenue Change % Undefined;
- zero Total Revenue Change makes every corresponding Contribution Share Undefined;
- mixed unnormalized or missing currency prevents admissible monetary comparison;
- cancelled and fully refunded lines are excluded before all MVP Metrics;
- `line_revenue` controls monetary value while eligibility controls population;
- `product_id` outranks `product_name` for grouping;
- missing category maps to visible `Unclassified`, never silent exclusion;
- Contribution ranking uses authoritative unrounded Absolute Contribution;
- presentation rounding never controls authoritative calculation or validation;
- Orders uses distinct eligible `order_id` and entity Orders remain non-additive;
- missing and unknown never become zero without evidence; and
- failed execution or validation never becomes a material Finding through narrative.

No fixture may override these rules locally.

## 24. Future Physical Fixture Requirements

When authorized after approved Architecture, physical fixtures must be small, deterministic, version-controlled, public-safe, human-readable where practical, machine-executable, traceable to this specification, independently runnable, and stable unless governing semantics change. Each must carry explicit synthetic or openly licensed provenance and enough evidence to establish the condition it tests.

Physical representation, directory structure, loader, execution interface, evidence-record representation, validation implementation, test runner, and CI integration remain undecided.

## 25. Boundaries with Architecture, Implementation, and Benchmark

Future Architecture may choose storage, serialization, loaders, interfaces, validation modules, test harness, and CI integration. It may not change fixture analytical semantics, Metric validity, Claim admissibility, or fail-closed expectations.

The future Decision Reliability Benchmark may select and group fixtures, define dimensions, measure behavior, report results, and create scoring rules. This specification does none of those things. Evaluation Fixtures are deterministic cases, not scores.

The approved project sequence remains:

CommerceLens Skill → Reusable Deterministic Analytics Engine → Decision Reliability Benchmark.

This document does not accelerate or reorder that sequence.

## 26. Non-Responsibilities

This specification does not define or create physical fixture files, serialization, CSV, Excel, SQLite, JSON, YAML, executable tests, SQL, Python, R, Architecture, database or ingestion implementation, validation code, test harness, CI/CD, benchmark scoring, leaderboard design, `SKILL.md`, prompts, agent architecture, UI, or marketplace connectors.

## 27. Change Governance

After approval and Freeze, implementation may not silently change an expected outcome. When an expected outcome conflicts with an approved governing semantic, the governing semantic wins and the fixture must be corrected through explicit review. Any change to Metric meaning, population, validity, Claim admissibility, qualification, or fail-closed behavior requires governance review rather than implementation convenience.

## 28. Traceability

| Governing document | Conceptual derivation in this specification |
|---|---|
| `PROJECT_MASTER_INSTRUCTIONS.md` v1.1 | Evidence-first rule, deterministic validation, reproducibility, transparent limitations, Human Decision Ownership, three-layer direction, reuse before rebuild |
| `PRD.md` v1.1 | Product question, MVP business value, supported structured inputs, insufficient-evidence and workflow expectations |
| `CommerceLens_Skill_First_Scope_Migration_Analysis_v1.1.md` | Approved GO decision, Skill-first constraints, reusable deterministic engine boundary, Benchmark sequencing |
| `SKILL_SCOPE_SPECIFICATION.md` v1.0 | Canonical question, workflow states, Skill/Engine responsibilities, fail-closed and partial completion behavior |
| `EVIDENCE_CONTRACT_SPECIFICATION.md` v1.0 | Evidence entities, execution/validation distinction, Claim taxonomy and admissibility, traceability, Recommendations, fail-closed behavior |
| `CANONICAL_DATASET_AND_METRIC_DICTIONARY.md` v1.0 | Canonical grain, fields, population, Metric formulas and validity, periods, identity, contribution, currency, precision, zero/null, duplicate and refund boundaries |

No requirement IDs are invented.

## 29. Acceptance Criteria

This specification passes Main Project Review only if:

1. it remains limited to the canonical MVP Business Question and approved Metrics;
2. fixture semantics derive from the six governing documents;
3. specification, physical data, implementation, Architecture, and Benchmark are explicitly separated;
4. taxonomy, structure, stable IDs, outcome vocabulary, Metric states, and Claim states are defined;
5. the valid canonical case deterministically covers Revenue, Orders, AOV, changes, contributions, rankings, and reconciliation;
6. multi-line orders, repeated legitimate product lines, duplicate identity, product identity, category attribution, and Orders non-additivity are tested;
7. zero baseline, both-zero, zero-net offsets, non-zero offsets, entry/exit, Contribution Share, and authoritative ranking precision are tested;
8. missing product identity, missing category, `Unclassified` claim sensitivity, and category mapping drift are tested without invented fallback or thresholds;
9. mixed/missing currency, invalid quantity, genuine zero, missing Revenue, unit-price conflict, cancellation, full refund, and unsupported partial refund are tested under the approved population and monetary authority;
10. incomplete, unequal, overlapping periods and inconsistent order dates are tested without unauthorized normalization or date repair;
11. product and category reconciliation, deliberate validation failure, execution failure, partial completion, population mismatch, AOV/percentage precision, and wrong formulas are distinguishable;
12. contribution-versus-causation, unsupported external explanations, Recommendation proportionality, Human Decision Ownership, and missing evidence-chain behavior are tested;
13. silent deduplication and missing-to-zero behavior are rejected;
14. positive and negative controls, fixture isolation, independence, minimality, cross-fixture consistency, and deterministic pass criteria are explicit;
15. material Claims require appropriate evidence traceability, and numerical coincidence cannot replace it;
16. fail-closed behavior blocks affected Claims while preserving independently valid chains;
17. all examples are synthetic/public-safe and no project evidence is invented;
18. no physical format, code, Architecture, `SKILL.md`, scoring, weight, grade, threshold, or leaderboard is introduced; and
19. the suite is comprehensive but remains a narrow MVP semantic contract rather than an enterprise benchmark.

## 30. Open Questions Reserved for Later Artifacts

Only the following remain open:

- physical fixture serialization and directory structure;
- fixture loader, execution interface, and test runner;
- validation implementation and physical evidence-record representation;
- CI integration; and
- future Benchmark selection, grouping, scoring, and reporting.

Fixture semantics, expected outcomes, Metric authority, Claim admissibility, fail-closed expectations, and minimum coverage are not open questions.

## 31. Release Boundary and Document Status

This document is **v1.0 — Approved / Frozen** dated **2026-08-20**. These Main Project Review corrections form the first approved release and do not create v1.1.

Approval and Freeze authorize progression only to the next approved project artifact: **ARCHITECTURE**. This document does not create Architecture in this release.

Approval does not authorize direct creation of physical CSV, Excel, or SQLite fixtures; JSON/YAML fixture bundles; executable tests; fixture loaders; test runners; SQL; Python; `SKILL.md`; implementation; or Decision Reliability Benchmark scoring. Physical fixture representation, execution interface, validation implementation, test harness, and related implementation decisions must follow the approved Architecture.
