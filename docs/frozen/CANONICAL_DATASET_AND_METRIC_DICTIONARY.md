# CommerceLens AI Canonical Dataset and Metric Dictionary

**Document:** `CANONICAL_DATASET_AND_METRIC_DICTIONARY.md`  
**Version:** v1.0  
**Status:** Approved  
**State:** Frozen  
**Date:** 2026-08-20

---

## 1. Document Purpose

This specification defines the authoritative analytical semantics for the CommerceLens MVP. It establishes the minimum canonical logical dataset, the MVP Metric Dictionary, the analytical population, the comparison-period contract, product and category attribution, Contribution Analysis, Metric validity, and deterministic analytical invariants.

As an approved and frozen document, this specification is the authoritative source for MVP Metric meaning. Future SQL, Python, validation logic, Evaluation Fixtures, reports, and implementation must conform to these semantics and must not substitute materially different formulas, populations, exclusions, or aggregation rules.

This document defines analytical semantics only. It does not execute analysis and contains no CommerceLens Finding.

## 2. Authority and Governing Documents

This specification is subordinate to and must conform to:

1. `PROJECT_MASTER_INSTRUCTIONS.md` v1.1 — Approved / Frozen; Skill-first Strategy amendment.
2. `PRD.md` v1.1 — Approved / Frozen; Skill-first Strategy amendment.
3. `CommerceLens_Skill_First_Scope_Migration_Analysis_v1.1.md` — Approved / Frozen; migration decision: GO.
4. `SKILL_SCOPE_SPECIFICATION.md` v1.0 — Approved / Frozen.
5. `EVIDENCE_CONTRACT_SPECIFICATION.md` v1.0 — Approved / Frozen.

This document does not reinterpret or reopen their approved product direction, workflow, claim taxonomy, execution responsibility, Evidence Contract, or human decision ownership. Where a conflict exists, the higher governing document prevails.

## 3. Governing Analytical Boundary

The canonical MVP Business Question is unchanged:

> How did revenue performance change between two comparable periods, and which products or categories contributed most to that change?

The authoritative MVP analytical concepts are limited to:

- Revenue;
- Orders;
- Average Order Value (AOV);
- Revenue Change;
- Revenue Change Percentage;
- Product Revenue and Product Orders;
- Category Revenue and Category Orders;
- Product and Category Performance expressed through observable Metrics;
- Product and Category Absolute Contribution;
- Contribution Share of Net Revenue Change;
- separate positive and negative contribution rankings;
- bounded period-over-period Descriptive Analysis; and
- bounded Diagnostic Contribution Analysis.

Contribution describes mathematical attribution of observed Revenue change. It does not establish causation.

## 4. Explicit Non-MVP Boundary

This specification does not define production Metrics for Gross Margin, Gross Profit, COGS, Discounts, Refund Rate, Return Rate, Inventory, Stockouts, Repeat Purchase, Retention, Cohorts, Customer Lifetime Value, Conversion Rate, Marketing Attribution, ROAS, CAC, Forecasting, predictive analysis, causal analysis, or A/B testing.

Fields or upstream rules used solely to determine eligibility for Revenue, Orders, or AOV do not create new analytical capabilities. In particular, the treatment of cancellation and refund states in this document is an eligibility boundary, not Refund Analysis.

## 5. Authoritative Decisions Summary

| Decision area | Authoritative MVP decision |
|---|---|
| Canonical grain | One governed order line, uniquely identified within one order |
| Revenue input | Governed `line_revenue` is authoritative |
| Revenue meaning | Eligible post-discount merchandise sales value, excluding tax and shipping |
| Cancellation/refund boundary | Upstream-governed eligible sales population; cancelled and fully refunded transactions excluded; arbitrary partial refunds unsupported |
| Orders | Distinct eligible `order_id` values with at least one eligible canonical line |
| AOV | Revenue divided by Orders for the identical governed scope and population |
| Period assignment | Governed `order_date`; all lines in an order must have one consistent date |
| Comparable periods | Non-overlapping, equal-duration, complete, and governed under one date/timezone convention |
| Product identity | Stable `product_id`; `product_name` is descriptive only |
| Category identity | Stable `category_id`; `category_name` is descriptive only |
| Missing attribution | Explicit governed `Unclassified` analytical bucket; never silent exclusion |
| Currency | One governed currency per comparison; no FX conversion |
| Primary contribution measure | Entity Revenue Change, also called Absolute Contribution |
| Contribution share | Secondary contextual Metric; undefined when total Revenue Change is zero; never the default ranking basis |
| Rounding | Exact governed decimal arithmetic; rounding only at presentation boundaries |

## 6. Canonical Dataset Design Principle

The canonical dataset uses a minimum sufficient logical schema. Every selected field is necessary to establish row identity, period membership, product/category attribution, eligible merchandise Revenue, Orders, or validation of those semantics.

The schema is not an enterprise commerce warehouse. It contains no customer model, promotion model, inventory model, refund ledger, payment model, shipment model, taxonomy hierarchy, accounting ledger, or marketplace connector fields.

The same logical semantics apply to CSV, Excel, and SQLite. Physical column types, parsers, source mapping, and ingestion normalization are deferred to Architecture and implementation.

## 7. Canonical Analytical Grain

### 7.1 Selected Grain

The authoritative grain is **Order Line / Order Item**.

One canonical row represents one governed, uniquely identified merchandise line within one order for one product. The row records the product quantity and the authoritative merchandise sales value allocated to that line.

The authoritative row identity is the composite:

`order_id` + `order_line_id`

The composite must be unique within the governed canonical dataset scope.

### 7.2 Why This Grain Is Authoritative

Order grain cannot reliably support product or category contribution when one order contains multiple products. Product-period grain cannot reproduce distinct Orders or detect multi-product orders. Transaction-event grain would require refund and payment event modeling outside MVP.

Order Line grain is the narrowest grain that simultaneously supports:

- additive merchandise Revenue;
- distinct-order counting;
- AOV derived from the same eligible population;
- product attribution without allocation assumptions;
- category attribution through each line's product classification;
- entities entering or exiting between periods; and
- contribution reconciliation to total Revenue Change.

### 7.3 Grain Consequences

- An order containing multiple products has multiple canonical rows with the same `order_id` and different `order_line_id` values.
- Multiple units of the same product may be represented by one line with `quantity > 1`, provided that the line is a genuine source line and its `line_revenue` covers that quantity.
- Repeated appearances of the same product in one order may remain separate lines when their `order_line_id` values differ. Product Orders still count the order once for that product.
- Revenue is summed at line grain. Orders are counted as distinct `order_id`, never as line count.
- Category Revenue is derived by assigning each eligible line to exactly one category bucket for the analysis.
- Every line in one order must share the same governed `order_date`. Inconsistent dates create unresolved period-assignment ambiguity.

## 8. Requirement Levels

The Field Dictionary uses these requirement levels:

- **Required:** Must be present and valid for the canonical MVP analytical population.
- **Conditionally Required:** Must be present and valid when the associated capability or condition applies.
- **Optional:** May support interpretation or validation but does not control an authoritative Metric unless its semantics are separately governed.
- **Out of Scope:** Not part of the canonical MVP dataset and must not be required to answer the canonical Business Question.

## 9. Canonical Field Dictionary

| Field | Meaning | Logical Type | Requirement Level | Row Grain | Null Policy | Uniqueness / Consistency | Metric Dependencies | Data Quality Consequence | Known Ambiguity / Governing Assumption |
|---|---|---|---|---|---|---|---|---|---|
| `order_id` | Stable identity of the commerce order containing the line | Identifier | Required | Repeats across lines of the same order | Null prohibited | Must identify one logical order consistently across the governed scope | Orders, AOV, Product Orders, Category Orders, period consistency | Missing or unstable identity blocks Orders, AOV, and order-based performance; it also blocks the complete canonical workflow | Assumes the source identity represents one logical order and is stable across extracts and periods |
| `order_line_id` | Stable identity of the source order line within its order | Identifier | Required | One value per row | Null prohibited | Composite (`order_id`, `order_line_id`) must be unique | Grain integrity, duplicate control, all line aggregations | Missing or non-unique composite creates blocking duplicate ambiguity unless provenance resolves it | Assumes the identifier distinguishes genuine repeated lines from duplicated extraction records |
| `order_date` | Governed transaction date used for period membership | Date | Required | Repeats identically across all lines of one order | Null prohibited | All rows with the same `order_id` must have the same date | All period Metrics and comparisons | Missing, invalid, or inconsistent date blocks affected period assignment and comparison | Assumes upstream governance has selected the intended transaction date and applied one declared timezone |
| `product_id` | Stable product identity used for grouping and reconciliation | Identifier | Required | One product per line | Null prohibited in the canonical product-capable dataset | Must refer to one product identity; names may vary but must not redefine identity | Product Revenue, Product Orders, Product Performance, Product Contribution | Missing identity blocks product claims; silent name-based substitution is prohibited | Assumes the same ID represents the same product across both periods; this document does not repair master-data corruption |
| `product_name` | Human-readable product label | Text | Optional | One observed label per line | Null allowed | Multiple names for one `product_id` may be retained as descriptive aliases but must be disclosed if presentation becomes ambiguous | Display only; never the primary grouping key | Does not block Metric calculation; ambiguous display labels qualify presentation | Labels may change, duplicate, or be localized; none of these changes product identity |
| `category_id` | Stable, single category identity assigned to the line for the governed analysis | Identifier | Conditionally Required for Category Performance or Category Contribution | One category or governed missing value per line | Null allowed only under the governed `Unclassified` rule | Each eligible line must resolve to exactly one category bucket; one-to-many assignment is prohibited | Category Revenue, Category Orders, Category Performance, Category Contribution | Missing values may be recovered into `Unclassified`; inconsistent or multiple assignment may block category claims | Assumes one flat governed category per line; taxonomy hierarchies and multi-label classification are outside MVP |
| `category_name` | Human-readable category label | Text | Optional | One observed label per line | Null allowed | Descriptive only; must not override `category_id` | Display only | Name inconsistency qualifies presentation but does not change grouping identity | Labels may change while the stable category ID remains authoritative |
| `quantity` | Count of merchandise units represented by the order line | Integer | Required | One value per line | Null prohibited | Must be a positive whole number | Grain interpretation and data-quality validation; not the authoritative Revenue formula | Missing, zero, negative, or fractional value blocks the affected line and may block scope-level claims if completeness cannot be established | Assumes discrete retail units; fractional units and return quantities are outside MVP |
| `line_revenue` | Authoritative post-discount eligible merchandise sales value allocated to the line, excluding tax and shipping | Decimal monetary value | Required | One value per line | Null prohibited | Must use governed exact decimal precision and the row's `currency`; must be non-negative | Revenue and every Revenue-derived Metric | Missing, invalid, or semantically ambiguous value blocks affected Revenue and derived claims | Assumes upstream allocation already reflects discounts and supported cancellation/full-refund treatment without tax or shipping |
| `currency` | Governed currency code for `line_revenue` | Categorical code | Required | One value per line | Null prohibited | Exactly one governed currency may appear in a comparison scope | Revenue and all monetary comparisons | Missing or mixed unnormalized currencies make monetary comparison inadmissible | Assumes any upstream normalization occurred before canonical analysis; no FX conversion occurs in CommerceLens MVP |
| `eligibility_status` | Normalized analytical eligibility indicator when a provided source contains both eligible and excluded transaction rows | Categorical / Boolean concept | Conditionally Required when ineligible rows remain in the provided source | One value per line | Null prohibited when field is required | Must unambiguously distinguish Eligible from Excluded; source-specific statuses require governed mapping | Population for every MVP Metric | Ambiguous or unsupported status mapping blocks affected rows and may block the analysis; this field is not a KPI | Assumes upstream governance can collapse supported source states into analytical eligibility without modeling partial refunds |
| `unit_price` | Optional governed unit monetary value used only for supporting validation when its relationship to discounts is declared | Decimal monetary value | Optional | One value per line | Null allowed | Must use the same currency as `line_revenue`; its pre/post-discount semantic must be declared before reconciliation | Validation support only | Must not replace `line_revenue`; inconsistency qualifies or blocks only when a declared invariant makes it material | May be list, pre-discount, or post-discount price; it has no authority until that semantic is declared |

### 9.1 Out-of-Scope Fields

Tax, shipping charge, discount amount, refund amount, return event, COGS, inventory, customer identity, channel attribution, campaign, payment status, shipment status, and exchange rate are outside the minimum canonical dataset. A source may contain them, but their presence does not authorize new Metrics or alter the authoritative definitions in this document.

## 10. Canonical Revenue Input Strategy

The authoritative strategy is **governed `line_revenue`**.

`line_revenue` is authoritative because `quantity × unit_price` cannot consistently represent post-discount merchandise sales when order-line discounts, bundled pricing, or governed upstream allocations exist. Requiring both fields as co-authoritative would permit conflicting production definitions. Therefore:

- `line_revenue` is required and controls Revenue;
- `quantity` is required to preserve order-line meaning and validate retail quantity semantics;
- `unit_price` is optional and validation-supporting only;
- `quantity × unit_price` must not overwrite, substitute for, or silently redefine `line_revenue`;
- if a source lacks governed `line_revenue`, upstream normalization may derive it only under an explicitly documented rule before the data becomes canonical; and
- this specification does not define that normalization implementation.

`line_revenue` is authoritative for the monetary value of a canonical line. Eligibility semantics are authoritative for determining whether that line participates in the governed analytical population. Monetary authority and population eligibility authority are distinct: a valid `line_revenue` value does not make a cancelled, fully refunded, excluded, or otherwise ineligible line part of Revenue. Where `eligibility_status` is required, it governs inclusion or exclusion before Revenue, Orders, AOV, Product Performance, Category Performance, or Contribution is computed.

## 11. Revenue Definition

### 11.1 Business Definition

MVP Revenue is a bounded analytical sales measure:

> The sum of authoritative post-discount eligible merchandise sales value across eligible canonical order lines within the governed scope and period, excluding tax and shipping.

It is not asserted to be accounting-recognized revenue, booked accounting revenue, cash collected, gross merchandise value across third parties, or fully realized net revenue after arbitrary later refund events.

### 11.2 Formula

For governed scope \(S\):

\[
\operatorname{Revenue}(S)=\sum_{i \in E(S)} \operatorname{line\_revenue}_i
\]

where \(E(S)\) is the set of canonical lines satisfying the common eligibility and scope rules.

### 11.3 Inclusion Rules

Include a line only when:

- its row identity is valid;
- its `order_date` is valid and belongs to the governed period;
- it is part of the governed eligible sales population;
- `quantity` is a positive integer;
- `line_revenue` is known, exact at governed decimal precision, and non-negative;
- `currency` matches the single governed comparison currency; and
- required scope filters and identity rules are satisfied.

Zero-value lines may be eligible when they are genuine governed merchandise lines. They contribute zero Revenue but remain part of the eligible order population. Their presence must be qualified when material to interpretation.

### 11.4 Exclusion Rules

Exclude:

- cancelled transactions;
- fully refunded transactions;
- rows explicitly governed as ineligible;
- tax amounts;
- shipping charges;
- unsupported transaction-event or partial-refund rows;
- invalid or unresolved duplicate rows;
- lines outside the governed period or scope; and
- rows with invalid required inputs.

Exclusion of an invalid row does not automatically make the remaining Revenue admissible. If the excluded amount is unknown or could materially change the requested result, the scope-level Revenue claim is inadmissible rather than merely reduced.

### 11.5 Negative, Zero, and Missing Values

- Negative `line_revenue` is invalid in the canonical MVP. Returns and refunds must not be modeled through negative sales lines.
- Zero `line_revenue` is valid only as a genuine eligible zero-value merchandise line.
- Missing `line_revenue` is unknown, not zero, and is blocking for the affected line.
- Missing quantity or invalid quantity prevents the line from becoming canonical even though Revenue is not derived from quantity.

### 11.6 Tax, Shipping, and Discounts

Revenue excludes tax and shipping because product/category contribution must reconcile through merchandise lines without arbitrary allocation of order-level charges.

Revenue is post-discount. Any discount already reflected in `line_revenue` remains embedded in the eligible merchandise sales value. Discount amount and Discount Analysis are outside MVP.

## 12. Cancellation and Refund Boundary

The canonical MVP uses an **upstream-governed eligible sales population**.

Before CommerceLens Metric computation, the source must either:

1. already contain only eligible sales lines after governed cancellation and full-refund treatment; or
2. contain an unambiguous `eligibility_status` mapping that allows ineligible rows to be excluded deterministically.

Cancelled and fully refunded transactions are excluded from all MVP Metrics. Partial refunds, refund timing, return events, restocking, and arbitrary post-sale adjustments are not supported. If such events exist and the source cannot provide a governed final eligible `line_revenue`, CommerceLens cannot claim net realized Revenue and must state **“Insufficient evidence to conclude.”** for affected Revenue conclusions.

This boundary defines eligibility only and does not create Refund Analysis.

## 13. Orders Definition

### 13.1 Business Definition and Formula

An Order is one distinct, non-null `order_id` with at least one eligible canonical line in the governed scope and period.

\[
\operatorname{Orders}(S)=\left|\left\{\operatorname{order\_id}_i : i \in E(S)\right\}\right|
\]

### 13.2 Rules

- A multi-line order counts once.
- The number of rows or order lines is never Orders.
- Exact or identity-level duplicates must not increase Orders or Revenue; unresolved duplicate ambiguity blocks admissibility.
- An eligible order whose eligible lines sum to zero Revenue still counts once.
- Cancelled and fully refunded orders do not count because they have no eligible lines.
- An order with no valid `order_id` cannot be counted or silently assigned an identity.
- When a scope selects products or categories, Orders means distinct eligible orders containing at least one eligible line in that selected scope.

## 14. Average Order Value Definition

AOV is a derived, non-additive Metric:

\[
\operatorname{AOV}(S)=\frac{\operatorname{Revenue}(S)}{\operatorname{Orders}(S)}
\]

The numerator and denominator must use the identical governed scope, period, eligibility rules, and currency basis.

- If Orders is greater than zero, AOV is valid when Revenue and Orders are valid.
- If Orders equals zero, AOV is undefined, including when Revenue also equals zero.
- AOV must be derived directly from authoritative Revenue and Orders using the governed calculation precision.
- Validation must use the governed calculation precision. If multiplication is used as a reconciliation check, it must account for governed computational precision and must not treat finite representation alone as a semantic mismatch.
- Presentation-rounded AOV must not be used for reverse reconciliation. A difference caused only by presentation rounding must not create a false validation failure.
- Subgroup AOVs must not be averaged to obtain total AOV. Total AOV must be recomputed from total Revenue divided by distinct eligible Orders. A weighted reconstruction is valid only when it mathematically reproduces the authoritative numerator and distinct-order denominator without overlap.
- Product or Category AOV is not an authoritative MVP Metric because distinct Orders overlap across entities and would invite invalid aggregation.

## 15. Comparison Period Contract

### 15.1 Terminology

- **Baseline Period:** The earlier reference period.
- **Comparison Period:** The later period evaluated against the Baseline Period.

These terms and direction are used consistently throughout this specification.

### 15.2 Mandatory Comparability Rules

For the canonical MVP, periods must:

- be explicitly bounded with inclusive start and end dates;
- be non-overlapping;
- contain the same number of governed calendar dates;
- be complete according to the declared data-availability cutoff;
- use the same governed timezone/date-boundary convention;
- use the same schema semantics, eligibility rules, currency basis, product identity rules, and category identity rules; and
- have labels that unambiguously identify Baseline and Comparison.

Equal duration and complete-period coverage are mandatory, not optional overrides. Partial-period comparison is outside the canonical MVP. Seasonal adjustment, forecasting, causal controls, and econometric comparability are not implied.

### 15.3 Missing Dates and Coverage

The absence of eligible transactions on a date may represent a genuine zero-activity date only when independent source-coverage evidence establishes that the date was observed completely. A date absent because extraction or source coverage is incomplete is unknown, not zero. Unresolved incomplete coverage blocks the period comparison.

## 16. Period Assignment Rule

`order_date` is the sole authoritative date for period membership.

If a source begins with timestamps, an upstream governed transformation must derive `order_date` under one declared timezone before the data becomes canonical. This specification does not define timestamp conversion implementation.

All lines sharing one `order_id` must share one `order_date`. If an order has inconsistent dates:

- CommerceLens must not split the order across periods;
- the affected order cannot be assigned until the inconsistency is resolved through traceable source evidence; and
- if unresolved affected records could change the period result, the comparison is inadmissible.

## 17. Revenue Change

For any governed scope \(S\):

\[
\operatorname{RevenueChange}(S)=\operatorname{Revenue}_{Comparison}(S)-\operatorname{Revenue}_{Baseline}(S)
\]

- Positive: Revenue is higher in the Comparison Period.
- Negative: Revenue is lower in the Comparison Period.
- Zero: Revenue is equal across the two periods at authoritative precision.

Revenue Change is additive only across valid mutually exclusive and collectively exhaustive partitions of eligible Revenue.

## 18. Revenue Change Percentage

\[
\operatorname{RevenueChangePct}(S)=
\frac{\operatorname{Revenue}_{Comparison}(S)-\operatorname{Revenue}_{Baseline}(S)}
{\operatorname{Revenue}_{Baseline}(S)}\times 100
\]

Validity rules:

- Baseline Revenue greater than zero: valid when both period Revenues are valid and comparable.
- Baseline Revenue equals zero and Comparison Revenue greater than zero: undefined; it may be described factually as an increase from zero, but no percentage may be asserted.
- Both period Revenues equal zero: undefined; absolute Revenue Change is zero.
- Missing or inadmissible period Revenue: inadmissible.
- Negative Baseline Revenue is impossible under canonical rules; its presence indicates invalid canonical data and makes the percentage inadmissible.

Revenue Change Percentage is non-additive and must not be summed or averaged across products or categories to obtain an overall percentage.

## 19. Product Identity Contract

`product_id` is the authoritative product grouping key. `product_name` is descriptive only.

- Duplicate product names do not merge different `product_id` values.
- A changing name does not split one stable `product_id` into multiple products.
- Missing `product_id` must not be replaced silently with `product_name`.
- One `product_id` with materially conflicting names qualifies presentation and may require clarification, but the ID remains the grouping authority unless evidence shows the ID itself is corrupted.
- If identity corruption prevents stable cross-period grouping, product comparison and contribution are inadmissible.
- This specification does not create product master-data management.

For product reconciliation, every eligible line must resolve to one product identity. Because `product_id` is required, an unresolved missing identity blocks the affected line and may block product and total claims when the omitted Revenue is material or unknown.

## 20. Category Identity Contract

`category_id` is the authoritative category grouping key. `category_name` is descriptive only. No category hierarchy is defined.

For Category Performance or Category Contribution:

- each eligible line must resolve to exactly one `category_id` or the governed analytical bucket `Unclassified`;
- one line must never be allocated to multiple categories;
- missing category identity is assigned analytically to `Unclassified` rather than silently dropped;
- `Unclassified` participates in Revenue and contribution reconciliation;
- a comprehensive named-category ranking or conclusion is inadmissible whenever `Unclassified` could change the claimed ordering, leader, or completeness conclusion; claim sensitivity, rather than an arbitrary percentage threshold, governs this boundary;
- a product observed in different categories across rows or periods is classified by its row-level observed `category_id` only when each line still has exactly one valid category and the semantic change is disclosed; and
- if category changes reflect unresolved mapping inconsistency rather than a governed observed classification, Category Performance and Contribution are inadmissible until resolved.

This narrow row-level rule avoids taxonomy infrastructure while preserving deterministic attribution.

## 21. Product Performance

Product Performance is not a composite score. It consists only of the following observable Metrics at `product_id` grain:

- Product Revenue by period;
- Product Orders by period;
- Product Revenue Change;
- Product Revenue Change Percentage when defined;
- Product Absolute Contribution; and
- Product Contribution Share of Net Revenue Change when defined and properly qualified.

No weighted score, grade, index, or inferred quality ranking is authorized.

## 22. Category Performance

Category Performance is not a composite score. It consists only of:

- Category Revenue by period;
- Category Orders by period;
- Category Revenue Change;
- Category Revenue Change Percentage when defined;
- Category Absolute Contribution; and
- Category Contribution Share of Net Revenue Change when defined and properly qualified.

The `Unclassified` bucket is part of reconciliation but must be visibly labeled and must not be presented as a named business category.

## 23. Product Revenue and Product Orders

### 23.1 Product Revenue

Product Revenue is Revenue aggregated by authoritative `product_id` under the common eligible population.

Products with the same name but different IDs remain separate. Products present in only one period remain in the union of period product identities and receive zero Revenue for the genuinely absent period, subject to verified period completeness.

### 23.2 Product Orders

Product Orders is the number of distinct eligible `order_id` values containing at least one eligible line for the product in the governed period.

Product Orders is non-additive across products because one order may contain multiple products. Summing Product Orders can exceed total Orders and is prohibited as a reconstruction of total Orders.

## 24. Category Revenue and Category Orders

### 24.1 Category Revenue

Category Revenue is Revenue aggregated by authoritative `category_id`, with missing identities assigned to `Unclassified` when category analysis is admissible.

Every eligible line contributes to exactly one category bucket. No allocation across multiple categories is permitted.

### 24.2 Category Orders

Category Orders is the number of distinct eligible `order_id` values containing at least one eligible line in the category during the governed period.

Category Orders is non-additive across categories because one order may contain lines from multiple categories. The `Unclassified` bucket follows the same distinct-order rule.

## 25. Contribution Analysis

### 25.1 Entity Set

For product analysis, the entity set is the union of valid `product_id` values observed across both periods. For category analysis, it is the union of valid `category_id` values plus `Unclassified` when applicable.

Genuine absence in one complete period is treated as zero entity Revenue for that period. Unknown or incomplete coverage must not be converted to zero.

### 25.2 Absolute Contribution

For entity \(e\):

\[
\operatorname{AbsoluteContribution}_e=
\operatorname{EntityRevenue}_{e,Comparison}-
\operatorname{EntityRevenue}_{e,Baseline}
\]

Absolute Contribution is identical to Entity Revenue Change.

- Positive values contribute positively to net Revenue change.
- Negative values contribute negatively.
- Zero indicates no net contribution at authoritative precision.

Absolute Contribution is the primary contribution measure and the sole default ranking basis.

### 25.3 Contribution Accounting Identity

When entities form a mutually exclusive and collectively exhaustive partition of eligible Revenue:

\[
\sum_e \operatorname{AbsoluteContribution}_e
=
\operatorname{TotalRevenueChange}
\]

This identity must hold separately for products and categories.

Product reconciliation requires every eligible line to have one valid `product_id`. Category reconciliation requires every eligible line to map to exactly one valid category or `Unclassified`. Eligible Revenue must never be silently dropped to make a ranking appear clean. An unexplained residual is a validation failure.

### 25.4 Contribution Share of Net Revenue Change

When Total Revenue Change is non-zero:

\[
\operatorname{ContributionShare}_e=
\frac{\operatorname{AbsoluteContribution}_e}
{\operatorname{TotalRevenueChange}}\times 100
\]

This Metric is authoritative only as a secondary contextual measure.

- If Total Revenue Change equals zero, every entity Contribution Share is undefined.
- When the denominator is non-zero, shares sum to 100% at full precision under a complete valid partition.
- Positive and negative entity changes may offset. Individual shares may be negative or exceed 100% in magnitude.
- When both positive and negative contributors exist, Contribution Share is mathematically valid but interpretively qualified because netting can make the denominator small relative to gross movements.
- No universal “near-zero” threshold is invented here. Therefore Contribution Share must never be the default ranking basis, even when non-zero.
- Reports must show Total Revenue Change and Absolute Contribution with any Contribution Share so the denominator and sign are visible.

If Total Revenue Change is negative, an entity with negative Absolute Contribution has a positive share because it moves in the same direction as the net decline; an entity with positive Absolute Contribution has a negative share because it offsets the decline. This sign behavior must not be rewritten as causal or evaluative language.

### 25.5 Positive and Negative Ranking

Contribution rankings are separated:

- **Leading positive contributors:** entities with Absolute Contribution greater than zero, ordered from largest positive value to smallest positive value.
- **Leading negative contributors:** entities with Absolute Contribution less than zero, ordered from most negative value to least negative value.
- Zero contributors are not included in either ranking but may be reported separately.

No default Top N is defined at the analytical-semantics level. Presentation policy may choose a bounded display only if it preserves the full reconciliation basis and does not imply omitted entities do not exist.

### 25.6 Entry and Exit

- Comparison-only entity: Baseline entity Revenue is genuine zero; its Comparison Revenue is a positive entry contribution when greater than zero.
- Baseline-only entity: Comparison entity Revenue is genuine zero; its negative Revenue Change is an exit contribution.
- Entity in both periods: contribution is the difference between its two valid period Revenues.

These rules apply only when both periods are complete and identity semantics are stable. Absence caused by missing or incomplete data is unknown, not zero.

## 26. Additivity and Aggregation Rules

| Metric | Classification | Permitted aggregation | Prohibited aggregation |
|---|---|---|---|
| `line_revenue` | Additive within one currency and governed population | Sum across eligible lines | Sum across mixed currencies or incompatible populations |
| Revenue | Additive across mutually exclusive scopes | Sum valid non-overlapping partitions | Double-count overlapping scopes |
| Orders | Distinct-count, non-additive across overlapping groups | Recompute distinct `order_id` at target scope | Sum Product Orders or Category Orders to obtain total Orders |
| AOV | Derived, non-additive | Recompute Revenue / Orders at target scope | Average subgroup AOVs without a mathematically valid reconstruction |
| Revenue Change | Additive across valid partitions | Sum entity changes under complete partition semantics | Sum overlapping segment changes |
| Revenue Change % | Derived, non-additive | Recompute from target-scope period Revenues | Sum or average entity percentages to obtain total percentage |
| Absolute Contribution | Additive under complete valid partition | Sum across product partition or category partition | Combine overlapping or non-exhaustive groupings without residual disclosure |
| Contribution Share | Derived, non-additive outside one common denominator | Sum to 100% only within one complete partition and one non-zero total change denominator | Compare or sum shares built on different total-change denominators |

## 27. Analytical Population Contract

The common eligible analytical population is the set of canonical lines that satisfy row identity, date, eligibility, quantity, monetary, currency, and requested-scope rules.

The same eligible population governs:

- Revenue: sum eligible `line_revenue`;
- Orders: distinct orders represented by eligible lines;
- AOV: Revenue and Orders from that identical population;
- Product Performance: eligible lines grouped by `product_id`;
- Category Performance: the same eligible lines grouped by `category_id` or `Unclassified`; and
- Contribution Analysis: the same population evaluated across Baseline and Comparison Periods.

No Metric may silently use a different cancellation rule, refund rule, date field, currency, or source filter. If a legitimate narrower scope is requested, all dependent Metrics must be recomputed for that same scope and the scope must be explicit.

## 28. Comparison Population Consistency

Baseline and Comparison Periods must use the same:

- eligibility definition;
- Revenue definition;
- date and timezone convention;
- schema and field semantics;
- currency basis;
- product identity semantics;
- category identity semantics; and
- requested filters.

Material semantic drift blocks ordinary period comparison. A narrower unaffected comparison may proceed only when independently complete, explicitly bounded, and traceable. Schema drift that is deterministically normalized before canonicalization is permitted only when the resulting semantic equivalence is documented as evidence.

## 29. Missing Data Semantics

Null, missing, unknown, and zero are not interchangeable.

### 29.1 Blocking Missingness

- Missing `order_id`: blocks Orders, AOV, Product Orders, and Category Orders; blocks the complete canonical workflow.
- Missing `order_line_id`: creates unresolved grain and duplicate risk.
- Missing `order_date`: blocks period assignment.
- Missing `product_id`: blocks product attribution and violates the canonical product-capable row contract.
- Missing `quantity`: blocks the line.
- Missing `line_revenue`: blocks Revenue for the line and every derived monetary Metric.
- Missing `currency`: blocks monetary aggregation and comparison.
- Missing required eligibility mapping when ineligible rows remain: blocks determination of the analytical population.

Blocking row missingness blocks the scope-level claim when the affected population or amount is unknown or potentially material. It must not be handled by treating the field as zero or inventing a value.

### 29.2 Recoverable Classification Missingness

Missing `category_id` may be assigned to the explicit `Unclassified` analytical bucket. This preserves Revenue and contribution accounting identity. Category results are qualified, and a comprehensive named-category conclusion is blocked when unclassified Revenue could change that conclusion.

Missing optional descriptive names does not block calculations.

## 30. Duplicate Data Semantics

Duplicate risk exists when multiple rows may represent the same logical order line or when repeated extraction has reproduced previously observed lines.

- Exact duplicate rows can multiply Revenue even if Orders remains unchanged.
- Repeated (`order_id`, `order_line_id`) identities violate canonical grain uniqueness.
- Similar product, amount, and date values without shared authoritative identity are not sufficient evidence of duplication.
- CommerceLens must not silently delete “duplicate-looking” rows.
- Deduplication is legitimate only when source identity, extraction metadata, or another traceable rule establishes that records are the same logical line and documents which representation is retained.
- Unresolved identity-level duplication is Blocking for Revenue and all derived Metrics in the affected scope.
- Suspected but unproven duplication is a qualifying limitation only when an independently valid bounded scope excludes the suspected records without changing the requested claim; otherwise it is Blocking.

## 31. Quantity Semantics

Canonical MVP quantity must be a positive whole number.

- Positive integer: valid.
- Zero: invalid canonical sales line, even if `line_revenue` is zero.
- Negative: invalid; returns must not be modeled as negative quantity.
- Fractional: unsupported for the retail/e-commerce MVP.
- Missing: invalid and Blocking for the line.

The quantity rule preserves a clear merchandise-line contract. It does not authorize unit-volume Metrics beyond the approved scope.

## 32. Monetary and Currency Semantics

### 32.1 Monetary Values

Authoritative monetary values use exact governed decimal semantics. Binary floating-point approximation must not determine authoritative equality or reconciliation.

- `line_revenue` must be non-negative.
- Zero is permitted for a genuine eligible zero-value line.
- Negative values are invalid.
- Missing values are unknown and Blocking.
- Calculations retain source/governed precision; rounding occurs only at presentation boundaries.
- Presentation rounding must not be fed back into downstream calculations or invariants.

### 32.2 Currency Contract

One governed comparison uses exactly one currency. Every eligible line must provide evidence of the same governed currency, such as a consistent normalized currency code and source declaration.

Mixed currencies are inadmissible unless the data was already normalized upstream to one governed currency under a traceable process before CommerceLens analysis. CommerceLens MVP does not perform exchange-rate conversion, web-based FX lookup, or historical FX reconciliation.

## 33. Null Versus Zero

- Null or missing means unknown, unavailable, or not observed.
- Zero is an observed value with a defined numeric meaning.
- Missing Revenue input must not become zero Revenue.
- A genuine zero-value eligible line contributes zero Revenue.
- Zero quantity is invalid, not equivalent to missing quantity and not a valid sales line.
- Missing category is a classification gap recoverable as `Unclassified`; it is not a numeric zero.
- Genuine entity absence in a complete period creates zero entity Revenue for contribution analysis. Uncertain absence from incomplete data remains unknown.

## 34. Data Type and Precision Rules

- Identifiers are opaque logical identifiers. Numeric-looking IDs must not be arithmetically transformed, rounded, or stripped of meaningful leading characters.
- `order_date` is a governed calendar date. Timestamp-to-date conversion occurs before canonical analysis under one declared timezone.
- Quantity is an exact integer.
- Monetary values are exact decimals at governed precision.
- Percentages are derived from unrounded authoritative monetary results and rounded only for display.
- Equality and reconciliation tests operate at authoritative precision. A separately declared presentation tolerance must not conceal semantic mismatch.

No programming-language or database-specific type is prescribed.

## 35. Data Quality Gates

### 35.1 Blocking Issues

A Blocking issue prevents the affected Metric or claim from becoming admissible. Blocking conditions include:

- missing or invalid authoritative Revenue inputs;
- missing order identity when Orders or AOV is required;
- missing or inconsistent period date;
- non-comparable or incomplete periods;
- mixed unnormalized currencies;
- unresolved canonical line duplication;
- invalid quantity;
- unsupported cancellation/refund semantics that prevent eligibility determination;
- unstable product identity for Product Performance or Contribution;
- non-exclusive or unreconcilable category assignment for Category Contribution;
- failure of a required analytical invariant; and
- material semantic drift between periods.

### 35.2 Qualifying Issues

A Qualifying issue permits a narrower valid result but constrains interpretation. Examples include:

- a visible `Unclassified` category bucket that does not prevent total reconciliation and permits only an explicitly narrower classified-category Claim;
- descriptive product/category names that vary while stable IDs remain valid;
- genuine zero-value eligible orders that materially affect AOV interpretation;
- simultaneous positive and negative contributions making Contribution Share unstable as an intuitive percentage; and
- a non-material optional-field gap.

Qualification must be attached to the affected Metric or Finding. It must not be used to excuse a failed required invariant.

### 35.3 Non-Material Issues

An issue is Non-material only when it cannot change the Metric, population, scope, identity, comparison, interpretation, or decision relevance. Missing optional display names may be Non-material when stable IDs are available and outputs remain understandable.

No data-quality score, confidence percentage, or arbitrary quality threshold is authorized.

## 36. Metric Validity Contract

The following conceptual states govern Metric use:

- **Valid:** All authoritative inputs, population rules, period rules, and required invariants are satisfied.
- **Qualified:** The Metric is valid for a clearly bounded scope, but a disclosed non-blocking issue materially constrains interpretation.
- **Undefined:** The formula has no defined result under an explicitly governed edge case, even though its inputs may otherwise be valid.
- **Inadmissible:** Required evidence, semantic authority, comparability, execution, validation, or reconciliation is missing or failed.

These are analytical concepts, not implementation enums.

| Metric | Valid | Qualified | Undefined | Inadmissible |
|---|---|---|---|---|
| Revenue | Eligible lines, valid `line_revenue`, one currency, valid period and reconciliation | Valid bounded population with disclosed non-blocking issue | Not ordinarily applicable; a valid empty population has Revenue zero only when complete coverage proves no eligible lines | Missing/ambiguous Revenue input, mixed currency, unresolved duplicates, unsupported eligibility, incomplete period |
| Orders | Valid distinct order identities in complete eligible population | Genuine zero-value eligible orders materially affect interpretation | Valid empty population yields Orders zero | Missing/unstable IDs, duplicate ambiguity affecting population, invalid eligibility |
| AOV | Valid Revenue and Orders > 0 from identical population | Valid but zero-value orders materially affect interpretation | Orders = 0 | Invalid numerator/denominator or population mismatch |
| Revenue Change | Both period Revenues valid and comparable | Valid comparison with disclosed non-blocking constraint | Not applicable | Either period inadmissible or periods not comparable |
| Revenue Change % | Baseline Revenue > 0 and both period Revenues valid | Valid but interpretation constrained by disclosed context | Baseline Revenue = 0 | Invalid period Revenue, negative baseline, or incompatible populations |
| Product Revenue / Orders | Valid product identities and common population | Display-name inconsistency with stable IDs | Product Orders zero only for genuine absence in a requested complete scope; no per-entity AOV defined | Missing/corrupt identity or unreconciled population |
| Category Revenue / Orders | Exclusive category assignment or `Unclassified`; common population | `Unclassified` remains visible and the Claim is explicitly limited to classified categories without implying complete category coverage; governed category changes may also constrain interpretation | Not ordinarily applicable | Multi-category duplication, unstable mapping, failure to reconcile, or a comprehensive named-category Claim whose ordering, leader, or completeness could be changed by `Unclassified` |
| Absolute Contribution | Valid entity period Revenues and complete partition | Valid partition with disclosed classification constraint | Not applicable | Failure to reconcile with total Revenue Change |
| Contribution Share | Total Revenue Change non-zero; valid Absolute Contribution | Positive/negative offsets make intuitive interpretation unstable | Total Revenue Change = 0 | Invalid denominator, invalid contribution, or incomplete partition |

## 37. Central Authoritative Metric Dictionary

| Metric Name | Business Definition | Authoritative Formula / Derivation | Analytical Grain | Required Inputs | Inclusion Rules | Exclusion Rules | Additivity | Period Dependency | Validation / Invariant Requirements | Undefined / Insufficient Conditions | Claim Types Supported |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Revenue | Eligible post-discount merchandise sales value excluding tax and shipping | Sum eligible `line_revenue` | Requested total scope; derived from order lines | `line_revenue`, `currency`, `order_date`, valid row identity, eligibility; valid quantity | Common eligible canonical population | Cancelled, fully refunded, ineligible, invalid, out-of-scope, tax, shipping, unsupported adjustments | Additive within compatible mutually exclusive scope | Single period or bounded scope | Must equal sum of eligible line Revenue at full precision | Inadmissible for missing/ambiguous inputs, mixed currency, unresolved duplicates, unsupported eligibility, incomplete coverage | Descriptive; basis for bounded Diagnostic contribution |
| Orders | Distinct eligible orders represented in scope | Count distinct `order_id` among eligible lines | Requested scope | `order_id`, eligible canonical lines, `order_date` | Orders with at least one eligible line; zero-Revenue eligible orders included | Orders with no eligible lines; cancelled/fully refunded | Non-additive across overlapping product/category groups | Single period or bounded scope | Must equal distinct eligible order identities | Valid zero for proven empty population; inadmissible for missing/unstable IDs or population ambiguity | Descriptive |
| AOV | Eligible merchandise Revenue per eligible Order | Revenue / Orders | Requested scope | Valid Revenue and Orders from identical population | Same as Revenue and Orders | Any row/order excluded from common population | Derived; non-additive | Single period | Must be derived directly from authoritative Revenue and Orders at governed calculation precision; presentation-rounded AOV is not a reverse-reconciliation input | Undefined when Orders = 0; inadmissible for population mismatch or invalid components | Descriptive |
| Revenue Change | Absolute Revenue difference from Baseline to Comparison | Comparison Revenue − Baseline Revenue | Requested total or entity scope | Valid comparable period Revenues | Same governed population semantics in both periods | Incompatible periods/populations | Additive under valid partitions | Requires Baseline and Comparison | Formula and period direction must reconcile | Inadmissible if either period is invalid or non-comparable | Descriptive; bounded Diagnostic basis |
| Revenue Change % | Relative Revenue change using Baseline as denominator | (Comparison Revenue − Baseline Revenue) / Baseline Revenue × 100 | Requested total or entity scope | Valid period Revenues; Baseline Revenue > 0 | Same as Revenue Change | Same as Revenue Change | Derived; non-additive | Requires Baseline and Comparison | Recompute from unrounded authoritative values | Undefined when Baseline Revenue = 0; inadmissible for invalid periods or negative baseline | Descriptive |
| Product Revenue | Eligible Revenue assigned to one product | Sum eligible `line_revenue` grouped by `product_id` | Product | Revenue inputs and valid `product_id` | Every eligible line assigned to one product | Invalid/unresolved product identity | Additive across complete exclusive product partition | Per period | Sum Product Revenue = total Revenue | Inadmissible if product partition cannot reconcile | Descriptive |
| Product Orders | Distinct eligible orders containing a product | Distinct `order_id` grouped by `product_id` | Product | Valid `order_id`, `product_id`, eligible lines | Eligible orders containing product | Ineligible lines/orders | Non-additive across products | Per period | Each product count uses distinct orders | Inadmissible for identity/population ambiguity | Descriptive |
| Product Revenue Change | Product's absolute Revenue difference | Product Comparison Revenue − Product Baseline Revenue | Product | Valid Product Revenue in both periods; genuine absence becomes zero | Union of products across complete periods | Unknown absence from incomplete data | Additive across complete product partition | Two periods | Sum equals total Revenue Change | Inadmissible if identity unstable or partition fails | Descriptive; bounded Diagnostic contribution |
| Product Revenue Change % | Product's relative Revenue change | Product Revenue Change / Product Baseline Revenue × 100 | Product | Valid Product period Revenues; baseline > 0 | Same as Product Revenue Change | Same as Product Revenue Change | Non-additive | Two periods | Recompute from product period Revenues | Undefined when product baseline is zero | Descriptive |
| Category Revenue | Eligible Revenue assigned to one category | Sum eligible `line_revenue` grouped by `category_id` or `Unclassified` | Category | Revenue inputs and exclusive category attribution | Every eligible line assigned to one category bucket | Invalid multi-assignment | Additive across complete exclusive category partition | Per period | Sum Category Revenue = total Revenue | Inadmissible when attribution cannot reconcile | Descriptive |
| Category Orders | Distinct eligible orders containing a category | Distinct `order_id` grouped by category bucket | Category | Valid order and category identity | Eligible orders containing category | Ineligible lines/orders | Non-additive across categories | Per period | Distinct count within each category | Inadmissible for population or attribution ambiguity | Descriptive |
| Category Revenue Change | Category's absolute Revenue difference | Category Comparison Revenue − Category Baseline Revenue | Category | Valid Category Revenue in both periods | Union of category buckets across complete periods | Unknown absence from incomplete data | Additive across complete category partition | Two periods | Sum equals total Revenue Change | Inadmissible if mapping or reconciliation fails | Descriptive; bounded Diagnostic contribution |
| Category Revenue Change % | Category's relative Revenue change | Category Revenue Change / Category Baseline Revenue × 100 | Category | Valid Category period Revenues; baseline > 0 | Same as Category Revenue Change | Same as Category Revenue Change | Non-additive | Two periods | Recompute from category period Revenues | Undefined when category baseline is zero | Descriptive |
| Product Absolute Contribution | Product's additive contribution to net Revenue change | Product Revenue Change | Product | Valid Product Revenue Change | Complete product partition | Unresolved product identity | Additive across product partition | Two periods | Sum = total Revenue Change | Inadmissible if product reconciliation fails | Bounded Diagnostic; not causal |
| Category Absolute Contribution | Category's additive contribution to net Revenue change | Category Revenue Change | Category | Valid Category Revenue Change | Complete category partition including `Unclassified` | Unresolved or overlapping category assignment | Additive across category partition | Two periods | Sum = total Revenue Change | Inadmissible if category reconciliation fails | Bounded Diagnostic; not causal |
| Product Contribution Share of Net Revenue Change | Product contribution relative to total net change | Product Absolute Contribution / Total Revenue Change × 100 | Product | Valid product contribution and non-zero total change | Complete product partition | Invalid/unreconciled entities | Derived; sums to 100% only for one complete partition and denominator | Two periods | Full-precision shares reconcile to 100% | Undefined when total change = 0; qualified with opposing signs | Secondary bounded Diagnostic context; never causal |
| Category Contribution Share of Net Revenue Change | Category contribution relative to total net change | Category Absolute Contribution / Total Revenue Change × 100 | Category | Valid category contribution and non-zero total change | Complete category partition | Invalid/unreconciled entities | Derived; sums to 100% only for one complete partition and denominator | Two periods | Full-precision shares reconcile to 100% | Undefined when total change = 0; qualified with opposing signs | Secondary bounded Diagnostic context; never causal |
| Positive Contribution Ranking | Ordering of positive entity Revenue Changes | Sort entities with Absolute Contribution > 0 descending | Product or Category | Valid Absolute Contributions | Positive contributors only | Zero and negative contributors | Not additive | Two periods | Ordering must use unrounded Absolute Contribution | Inadmissible if contributions invalid; ties remain ties at authoritative precision | Bounded Diagnostic presentation |
| Negative Contribution Ranking | Ordering of negative entity Revenue Changes | Sort entities with Absolute Contribution < 0 ascending, most negative first | Product or Category | Valid Absolute Contributions | Negative contributors only | Zero and positive contributors | Not additive | Two periods | Ordering must use unrounded Absolute Contribution | Inadmissible if contributions invalid; ties remain ties at authoritative precision | Bounded Diagnostic presentation |

## 38. Metric Dependency Graph

Canonical eligible order lines  
↓  
Authoritative eligible `line_revenue`  
↓  
Revenue by period and entity  
↓  
Revenue Change  
↓  
Product / Category Absolute Contribution  
↓  
Separate positive and negative Contribution Rankings

Valid eligible `order_id` values  
↓  
Orders  

Revenue + Orders from the same population  
↓  
AOV

Absolute Contribution + non-zero Total Revenue Change  
↓  
Contribution Share of Net Revenue Change

## 39. Deterministic Analytical Invariants

Future deterministic validation must be able to test the following mathematical and business invariants without changing their meaning:

1. **Row identity:** (`order_id`, `order_line_id`) is unique for canonical lines.
2. **Order date consistency:** every line of one `order_id` has one `order_date`.
3. **Revenue:** total Revenue equals the sum of eligible canonical `line_revenue` within the same scope, period, and currency.
4. **Orders:** Orders equals the count of distinct eligible `order_id` values within scope.
5. **AOV:** when Orders > 0, AOV is derived directly as authoritative Revenue divided by authoritative Orders for the identical population. Validation uses governed calculation precision; any multiplication-based reconciliation must account for that precision and must never use presentation-rounded AOV.
6. **Product Revenue:** the sum of Product Revenue equals total Revenue when every eligible line has one valid product identity.
7. **Category Revenue:** the sum of Category Revenue, including `Unclassified`, equals total Revenue when every eligible line has one exclusive category bucket.
8. **Revenue Change:** Comparison Revenue − Baseline Revenue equals Total Revenue Change.
9. **Product Contribution:** the sum of Product Absolute Contributions equals Total Revenue Change.
10. **Category Contribution:** the sum of Category Absolute Contributions equals Total Revenue Change.
11. **Contribution Share:** when Total Revenue Change is non-zero and the partition is complete, entity shares sum to 100% at full precision.
12. **Population consistency:** Revenue, Orders, AOV, period comparison, and contribution use compatible governed eligibility and scope semantics.
13. **Currency consistency:** every monetary value in one comparison uses the same governed currency.
14. **Entity exclusivity:** each eligible line contributes to exactly one product and one category bucket in their respective reconciliations.

Failure of a required invariant is a Validation Failure, not a narrative limitation that may be ignored.

## 40. Cross-Metric Consistency

A report must not present Revenue, Orders, AOV, comparison, or contribution Metrics derived from materially different populations as if they were directly compatible.

Specifically:

- AOV numerator and denominator must match.
- Total and entity Revenues must share eligibility and currency rules.
- Baseline and Comparison Periods must share semantic rules.
- Product and Category contribution each reconcile independently to the same total Revenue Change.
- A filtered product or category analysis must recompute total-scope dependent Metrics for that filter rather than reuse an incompatible denominator.
- Presentation rounding must not create or conceal population drift.

Any justified difference must be explicit, separately named, and outside the canonical Metric if it changes the definition in this document.

## 41. Attribution Completeness

### 41.1 Product

Product Contribution requires 100% of eligible Revenue to reconcile through valid product identities. Because `product_id` is required, an unresolved product attribution gap blocks Product Contribution and may block total Revenue if the affected lines cannot be treated canonically.

### 41.2 Category

Category Contribution may reconcile missing classifications through `Unclassified`. This preserves mathematical completeness but qualifies business interpretation.

A comprehensive named-category ranking or conclusion is inadmissible whenever `Unclassified` could change the claimed ordering, leader, or completeness conclusion. This decision uses claim sensitivity and does not depend on an arbitrary percentage threshold.

A narrower qualified Claim may remain admissible using wording such as **“Among classified categories...”** only when:

- the scope qualification is explicit;
- the classified-category calculation is valid;
- `Unclassified` remains visible; and
- the wording does not imply complete category coverage.

No unexplained residual bucket is permitted.

## 42. Ranking Contract

Absolute Revenue Change is the primary and only default ranking measure. Positive and negative rankings are always separate.

Contribution Share is a display/context Metric, not a ranking Metric. It must not determine rank because its sign and magnitude depend on the net total-change denominator and can become misleading under offsetting entity movements.

Ties are evaluated at authoritative, unrounded precision. Presentation rounding must not manufacture an ordering between equal values.

## 43. Contribution Interpretation Boundary

Contribution is mathematical attribution, not causal explanation.

CommerceLens may state that a product or category was a leading positive or negative contributor to observed Revenue Change. It must not state, solely from these Metrics, that the entity caused the business outcome, that changing it will reverse the outcome, or that an external factor explains its movement.

Alternative explanations remain hypotheses unless separately supported by admissible Evidence. Contribution supports bounded Diagnostic claims only.

## 44. Metric-Specific Insufficiency Conditions

CommerceLens must state **“Insufficient evidence to conclude.”** for the affected requested conclusion when:

- authoritative `line_revenue` is missing, semantically ambiguous, or cannot be governed;
- eligible population cannot be determined because transaction states are unsupported or ambiguous;
- order identity is unavailable when Orders or AOV is required;
- canonical line duplicates cannot be resolved with traceable evidence;
- periods overlap, differ in duration, are incomplete, or use inconsistent date/timezone semantics;
- currency is missing or mixed without upstream governed normalization;
- required quantity is invalid or missing and affected completeness is unknown;
- product identity is insufficient for the requested Product Performance or Contribution claim;
- category attribution is not exclusive or cannot reconcile for requested Category Contribution;
- `Unclassified` category data prevents the requested comprehensive named-category conclusion;
- comparison semantics materially drift between periods;
- a required invariant fails;
- Revenue Change Percentage is requested with zero Baseline Revenue and the user requires a numeric percentage;
- Contribution Share is requested with zero Total Revenue Change and the user requires a numeric share;
- a Metric has no authority under this dictionary; or
- the available data supports only a narrower claim than requested and no independently valid narrower conclusion answers the question.

Not every issue blocks every output. Independently complete and valid narrower Metrics may be reported when their scope and qualification are explicit and their Evidence Contract chains remain complete.

## 45. Canonical Logical Schema Example

The canonical row shape contains:

| Field | Logical meaning |
|---|---|
| `order_id` | Order identity |
| `order_line_id` | Unique line identity within the order |
| `order_date` | Governed period-assignment date |
| `product_id` | Stable product identity |
| `product_name` | Optional product display label |
| `category_id` | Stable category identity when category analysis applies |
| `category_name` | Optional category display label |
| `quantity` | Positive whole-number units on the line |
| `line_revenue` | Authoritative post-discount merchandise sales value excluding tax and shipping |
| `currency` | Governed currency of `line_revenue` |
| `eligibility_status` | Conditional eligibility field when excluded rows remain present |
| `unit_price` | Optional validation-supporting unit value with declared semantics |

No fabricated business results or physical dataset are included.

## 46. Source Portability

CSV, Excel, and SQLite representations must produce identical logical Metrics when they represent the same canonical records and governed scope. Source type must not change grain, field meaning, Revenue definition, exclusions, period assignment, identity, contribution formulas, or validity rules.

Source-specific ingestion, parsing, workbook selection, table selection, encoding, SQL access, and type coercion are implementation responsibilities and are not defined here.

## 47. Synthetic and Public Data Boundary

Public CommerceLens development, demos, future Evaluation Fixtures, and portfolio artifacts may use only synthetic or openly licensed data. Proprietary seller data, private marketplace data, customer data, confidential source URLs, and copied private datasets are prohibited.

This specification does not source or create any dataset.

## 48. Relationship to the Evidence Contract

This artifact supplies authoritative semantics for Evidence Contract dependencies including:

- Metric Definition and Metric Reference;
- Required Fields;
- analytical grain;
- aggregation and exclusion rules;
- eligible analytical population;
- comparison-period semantics;
- product/category attribution;
- Metric validity;
- insufficiency conditions; and
- deterministic analytical invariants.

These semantics become Required Evidence dependencies for material Metric Claims.

`EVIDENCE_CONTRACT_SPECIFICATION.md` remains authoritative for claim admissibility, Available Evidence, Validated Results, Admissible Evidence, execution evidence, validation evidence, provenance, Finding traceability, Recommendation traceability, Assumptions, Alternative Explanations, Limitations, failure states, and Human Decision Ownership.

The specifications remain separate. A correct Metric formula does not by itself make a claim admissible, and an Evidence Contract cannot make a Metric valid when its authoritative semantic requirements fail.

## 49. Relationship to Future Evaluation Fixtures

This specification establishes semantics from which future fixtures may be derived. Natural fixture categories include:

- valid canonical case;
- multi-line and multi-product order;
- repeated product lines with distinct line identities;
- Product Contribution reconciliation;
- Category Contribution reconciliation including `Unclassified`;
- zero Baseline Revenue;
- zero Total Revenue Change;
- positive and negative contribution offsetting;
- product present in only one period;
- category present in only one period;
- missing product identity;
- missing category attribution;
- duplicate identity ambiguity;
- mixed currency;
- invalid quantity;
- missing Revenue input;
- incomplete period;
- inconsistent order dates;
- cancelled or fully refunded exclusion when eligibility status is supplied; and
- unsupported partial-refund semantics.

This document does not create fixtures or specify fixture outputs.

## 50. Reuse Before Rebuild

CommerceLens preserves the governing principle:

> Reuse before rebuild.

The differentiated value of this specification is authoritative analytical semantics, evidence discipline, deterministic reconciliation, and claim reliability. It does not prescribe custom infrastructure for commodity file handling, tabular computation, distinct counting, grouping, or decimal arithmetic.

Any reused capability must still conform to these semantics and produce traceable, reproducible, deterministically validated results.

## 51. Host Independence

Metric meaning is host-independent. Revenue, Orders, AOV, comparison, and Contribution must retain identical semantics whether CommerceLens later runs through ChatGPT, Claude, Codex, another LLM host, a CLI, or an application.

AI behavior, prompting style, model selection, or host tool availability must not redefine a Metric. If deterministic execution or validation is unavailable, the result is unavailable or inadmissible; the host must not approximate it through language reasoning.

## 52. Human Decision Ownership

This specification supports evidence-based human decision-making. It does not authorize autonomous business decisions. Metric validity and contribution ranking identify observed analytical relationships only. Recommendations must remain proportional to admissible Findings, and final decision ownership remains with the human user.

## 53. Non-Responsibilities

This specification does not define:

- SQL, Python, or R implementation;
- ingestion pipelines or normalization implementation;
- a physical database schema or storage;
- APIs, execution runtime, or validation code;
- report rendering or UI;
- benchmark scoring;
- Evaluation Fixtures or expected fixture outputs;
- `SKILL.md`;
- prompt engineering or agent design;
- marketplace connectors;
- FX conversion;
- a refund ledger; or
- an actual CSV, Excel file, or SQLite database.

## 54. Open Questions Reserved for Later Artifacts

The analytical-semantic questions are resolved in this document. Later approved artifacts may determine only:

- how the logical schema is physically represented in CSV, Excel, and SQLite;
- how source columns and statuses are normalized into canonical fields;
- how deterministic validation is implemented and recorded;
- how Evaluation Fixtures are constructed and serialized;
- how execution, storage, and interfaces are implemented; and
- how evidence references are physically linked without changing the Evidence Contract.

These questions do not authorize implementation before this specification is approved and frozen.

## 55. Traceability

| Governing document | Conceptual derivation preserved here |
|---|---|
| `PROJECT_MASTER_INSTRUCTIONS.md` v1.1 | Evidence First; analytical correctness; deterministic computation and validation; reproducibility; Data Sufficiency; transparent Limitations; claim discipline; Human Decision Ownership; Reuse Before Rebuild; host-independent Skill-first direction |
| `PRD.md` v1.1 | Canonical Business Question; narrow e-commerce MVP; Revenue, Orders, AOV, product/category performance and contribution; CSV, Excel, SQLite; public-data boundary; executable evidence-backed workflow |
| `CommerceLens_Skill_First_Scope_Migration_Analysis_v1.1.md` | GO decision; Skill → Reusable Deterministic Analytics Engine → Decision Reliability Benchmark; narrow first workflow; engine authority; contribution boundary; sequential development |
| `SKILL_SCOPE_SPECIFICATION.md` v1.0 | Metric-before-analysis requirement; canonical workflow; supported inputs; clarification and insufficiency behavior; bounded Descriptive and Diagnostic claims; deterministic delegation; fail-closed behavior |
| `EVIDENCE_CONTRACT_SPECIFICATION.md` v1.0 | Required Evidence, Available Evidence, Validated Result, Admissible Evidence; execution/validation distinction; Metric Reference; claim admissibility; provenance and traceability; failure and partial-completion behavior |

No governing requirement IDs are invented.

## 56. Acceptance Criteria

This specification satisfied Main Project Review only when all of the following were true:

1. The canonical Business Question is unchanged.
2. No unrelated KPI or analytical capability is introduced.
3. Order Line grain and one-row meaning are explicit.
4. The minimum logical fields and requirement levels are explicit.
5. `line_revenue` is the sole authoritative Revenue input.
6. Revenue is defined as post-discount eligible merchandise sales value excluding tax and shipping.
7. Cancellation and refund eligibility boundaries are explicit without creating Refund Analysis.
8. Orders and AOV use one common eligible population.
9. Comparable periods are non-overlapping, equal-duration, complete, and semantically consistent.
10. `order_date` is the sole period-assignment field, with order-level date consistency.
11. Product and Category Performance are observable Metrics, not composite scores.
12. Stable product and category IDs govern identity.
13. Product and Category Revenue and Orders are defined with correct non-additivity rules.
14. Absolute Contribution, Contribution Share, reconciliation, entry, exit, and ranking are deterministic.
15. Contribution Share is undefined at zero net change and never the default ranking basis.
16. Missingness, duplicates, quantity, monetary precision, currency, null, and zero semantics are explicit.
17. Blocking, Qualifying, and Non-material data-quality consequences are distinguished without scores.
18. Metric states of Valid, Qualified, Undefined, and Inadmissible are specified.
19. The central Field Dictionary and Metric Dictionary prevent materially different conforming formulas.
20. Deterministic invariants and cross-Metric consistency are testable conceptually.
21. Product and category contribution reconcile to total Revenue Change under their valid partition rules.
22. Contribution remains non-causal.
23. Insufficient-evidence conditions are concrete and Metric-specific.
24. CSV, Excel, and SQLite semantics are identical.
25. The Evidence Contract relationship remains separate and explicit.
26. No implementation, code, Architecture, physical dataset, or Evaluation Fixture is included.
27. Public data remains synthetic or openly licensed.
28. Metric semantics remain host-independent.
29. The document remains v1.0 and is marked Approved / Frozen.

## 57. Release Boundary

Main Project approval and Freeze of this specification authorize progression only to the next approved artifact:

`EVALUATION_FIXTURES_SPECIFICATION.md`

This approval does not authorize progression beyond that artifact to:

- physical production dataset implementation;
- Architecture;
- `SKILL.md`;
- SQL;
- Python;
- code; or
- implementation.

The physical representation of synthetic datasets and fixtures will be determined by later approved work. No Evaluation Fixtures are created by this specification.

---

**End of `CANONICAL_DATASET_AND_METRIC_DICTIONARY.md` v1.0 — Approved / Frozen**
