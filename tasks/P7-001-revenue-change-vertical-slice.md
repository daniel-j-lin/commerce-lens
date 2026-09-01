# P7-001 — Revenue Change Vertical Metric Slice

## Status

APPROVED / FROZEN

Formal Main Project decision:
P7-001 — APPROVED / FROZEN

Implementation:
COMPLETE

Final approved implementation commit:
f48b75eb0f67f5b14675886e6ce1749835d2dc16

Final verification evidence:

- Python 3.11.9
- DuckDB 1.5.5
- pytest 8.4.2
- MetadataStore schema v5
- validation: 71 passed
- engine: 144 passed
- evidence: 84 passed
- persistence: 16 passed
- metrics/sufficiency/contracts: 35 passed
- full suite: 398 passed
- final full rerun: 398 passed
- git diff --check passed
- material findings: NONE

Corrected blocker classes:

1. execution-stage Revenue dependency lineage;
2. Revenue Change scope provenance duplication;
3. validation-stage dependency ExecutionRecord lineage.

This task authorizes the next CommerceLens implementation slice after:

- Phase 1 — APPROVED / FROZEN;
- Phase 2 — APPROVED / FROZEN;
- P3-001 — APPROVED / FROZEN;
- P4-001 — APPROVED / FROZEN;
- P5-001 — APPROVED / FROZEN; and
- P6-001 — APPROVED / FROZEN.

Current verified full suite:

301 passed

Current MetadataStore schema:

5

This task changes the implementation cadence for narrow Metric additions:

Metric Registry
↓
ExecutionPlan
↓
deterministic execution
↓
ExecutionRecord
↓
ExecutedResult
↓
deterministic required validation
↓
ValidationRecords
↓
ValidatedResult
↓
deterministic Evidence admissibility
↓
EvidenceAdmissibilityRecord
↓
AdmissibleEvidence
↓
STOP

Execution, validation, and Evidence remain separate contracts, authorities, records, and tests.

---

## 1. Purpose

P7-001 implements one additional canonical Metric:

`revenue_change`

Display name:

Revenue Change

Revenue Change must be implemented as one complete vertical deterministic reliability slice on top of the existing P3-P6 infrastructure.

The future implementation must not split Revenue Change into separate execution-only, validation-only, or evidence-only phases unless a genuine Main Project STOP condition is discovered.

P7-001 must end at:

AdmissibleEvidence for Valid Revenue Change descriptive `metric_value` evidence.

P7-001 must not implement ClaimDecision, Findings, Recommendations, Contribution, rankings, Revenue Change Percentage, MCP, external executor work, Wren, or any other later capability.

---

## 2. Governing Principle

> No material claim without traceable evidence.

P7-001 must preserve:

- analytical correctness;
- Frozen Metric semantics;
- period-comparison authority;
- deterministic dependency authenticity;
- reproducibility;
- immutable artifact integrity;
- fail-closed behavior;
- independent valid analytical chains;
- separation of ExecutedResult from ValidatedResult;
- separation of ValidatedResult from AdmissibleEvidence; and
- separation of AdmissibleEvidence from ClaimDecision.

If implementation convenience conflicts with Frozen authority:

STOP and request Main Project review.

Do not reinterpret Revenue Change.

---

## 3. Governing Documents

This task is subordinate to the Approved / Frozen specifications under:

`docs/frozen/`

Especially:

- `PROJECT_MASTER_INSTRUCTIONS.md`
- `PRD.md`
- `SKILL_SCOPE_SPECIFICATION.md`
- `EVIDENCE_CONTRACT_SPECIFICATION.md`
- `CANONICAL_DATASET_AND_METRIC_DICTIONARY.md`
- `EVALUATION_FIXTURES_SPECIFICATION.md`
- `ARCHITECTURE_SPECIFICATION.md`

It is also subordinate to the Approved / Frozen behavior implemented by:

- `tasks/P3-001-metric-registry-population-plan.md`
- `tasks/P4-001-revenue-orders-aov-reference-execution.md`
- `tasks/P5-001-revenue-orders-aov-deterministic-validation.md`
- `tasks/P6-001-narrow-evidence-admissibility.md`

Do not modify Frozen specifications.

---

## 4. Current Baseline

The current deterministic reliability chain is:

AnalysisRequest
→ Required Evidence
→ Data Sufficiency
→ ExecutionPlan
→ deterministic execution
→ ExecutionRecord
→ ExecutedResult
→ required ValidationRules
→ ValidationRecords
→ ValidatedResult
→ deterministic Evidence admissibility
→ EvidenceAdmissibilityRecord
→ AdmissibleEvidence
→ immutable verified artifact

Current implemented Metrics:

- `revenue`
- `orders`
- `aov`

Current Evidence admissibility:

- descriptive only;
- `metric_value` for Valid Revenue / Orders / AOV;
- `metric_state` for governed AOV Undefined because Orders = 0.

Current dormant Registry support exists for `revenue_change`, but execution, validation, and Evidence admissibility are not implemented for it.

---

## 5. Authorized Metric

P7-001 may implement only:

- `revenue_change`

P7-001 must reuse the existing canonical Metric ID:

`revenue_change`

P7-001 must preserve the existing Metric definition version convention:

`metric_dictionary_v1`

P7-001 may update the machine-readable Metric Registry authority only as needed to bind Revenue Change execution and validation.

Because P7-001 materially changes the active Registry binding for `revenue_change`, the future implementation must advance:

`METRIC_REGISTRY_VERSION`

from:

`metric_registry_mvp_v2`

to:

`metric_registry_mvp_v3`

The Metric Dictionary definition version remains `metric_dictionary_v1` because the Frozen semantic meaning does not change.

Do not add a duplicate Metric ID.

Do not add Revenue Change Percentage.

---

## 6. Explicitly Out Of Scope

Do NOT implement:

- `revenue_change_pct`
- Product Revenue
- Product Orders
- Product Revenue Change
- Product Revenue Change Percentage
- Product Absolute Contribution
- Product Contribution Share
- Category Revenue
- Category Orders
- Category Revenue Change
- Category Revenue Change Percentage
- Category Absolute Contribution
- Category Contribution Share
- positive contributor ranking
- negative contributor ranking
- ClaimCandidate evaluation
- ClaimDecision
- ClaimState changes
- Findings
- Alternative Explanations
- Recommendations
- report rendering
- UI
- H-001
- MCP
- ExecutorAdapter
- external executor
- Wren

DuckDB / current deterministic executor authority remains unchanged.

---

## 7. Authoritative Metric Semantics

Revenue Change must use only the Frozen Canonical Dataset and Metric Dictionary definition:

Comparison Revenue
−
Baseline Revenue

Formula:

`RevenueChange(S) = Revenue_Comparison(S) - Revenue_Baseline(S)`

Requirements:

- use authoritative unrounded Decimal Revenue dependency values;
- do not compute from presentation-rounded Revenue;
- do not derive from AOV;
- do not derive from Orders;
- do not recalculate Revenue inside Revenue Change when authoritative Revenue dependency results exist;
- do not use percentage change as a substitute;
- do not interpret direction causally.

Revenue Change may be:

- positive;
- zero; or
- negative.

All three are valid numerical possibilities.

---

## 8. Period Authority

Revenue Change requires exactly:

- Baseline period; and
- Comparison period.

P7-001 must consume existing period authority from:

- `AnalysisRequest.baseline_period`
- `AnalysisRequest.comparison_period`
- `DataSufficiencyResult`
- `ExecutionPlan.period_refs`
- `PopulationDefinition.period`
- `PopulationDefinition.period_role`
- `PlanMetricNode.period_refs`
- dependency Revenue `ValidatedResult.period_ref`
- dependency Revenue `ValidatedResult.period_role`

Preserve Frozen comparison-period semantics:

- Baseline is the earlier period;
- Comparison is the later period;
- periods are complete;
- periods are equal-duration where required by the canonical comparison;
- periods are non-overlapping;
- periods use the same timezone/date convention;
- periods use the same governed eligibility semantics;
- periods use compatible governed population/scope.

Current Phase 2 Data Sufficiency already checks:

- date-convention equality;
- Baseline earlier than Comparison;
- non-overlap;
- equal inclusive duration;
- explicit coverage spanning the Baseline period;
- explicit coverage spanning the Comparison period.

P7-001 must not invent a second period-comparability system.

P7-001 validation must verify that the Revenue Change node and its dependency results preserve the existing governed Baseline/Comparison authority.

If current authority is not sufficient to determine comparability for Revenue Change:

STOP and request Main Project review.

Do not infer comparability.

---

## 9. Dependency Authority

Revenue Change must depend on authoritative Revenue results for:

- Baseline Revenue; and
- Comparison Revenue.

The dependencies must be authentic persisted `ValidatedResult` objects.

Caller-created Revenue result objects are not authority.

A Revenue Change dependency must prove:

- same `AnalysisRequest`;
- same `ExecutionPlan`;
- exact governed dependency `PlanMetricNode`;
- correct Revenue Metric ID `revenue`;
- correct Revenue Metric definition version `metric_dictionary_v1`;
- correct Baseline/Comparison period role;
- correct dataset;
- correct canonical dataset;
- correct canonical dataset fingerprint;
- same governed population/scope except period role;
- same grouping `none`;
- same currency;
- authentic persisted ExecutedResult artifact;
- authentic persisted ValidatedResult artifact;
- successful required Revenue validation;
- complete dependency ValidationRecord bundle;
- authentic dependency rule fingerprints; and
- authentic dependency validation-bundle fingerprint.

The P5 AOV dependency-authenticity model is the binding implementation pattern.

Do not accept:

- missing Baseline dependency;
- missing Comparison dependency;
- duplicate Baseline dependencies;
- duplicate Comparison dependencies;
- dependencies from another request;
- dependencies from another plan;
- dependencies from the wrong Plan node;
- dependencies with wrong period roles;
- dependencies with wrong Metric ID/version;
- caller-fabricated ValidatedResult objects;
- missing or tampered dependency artifacts;
- failed dependency ValidationRecords;
- incomplete dependency validation bundles; or
- forged dependency validation fingerprints.

All such cases fail closed.

---

## 10. Metric Registry Requirements

Extend the existing Metric Registry narrowly for `revenue_change`.

Do not create a second Registry.

The `revenue_change` Registry definition must use:

- `metric_id`: `revenue_change`
- `display_name`: `Revenue Change`
- `definition_version`: `metric_dictionary_v1`
- `metric_category`: `period_comparison`
- `period_requirement`: `baseline_and_comparison`
- `grouping_requirement`: `none`
- `additivity`: `additive`
- `output_shape`: `scalar_decimal`
- `currency_unit_semantics`: single governed currency for monetary metrics
- `precision_policy_ref`: existing `PRECISION_POLICY_REF`
- dependencies:
  - `revenue` with `DependencyPeriodRole.BASELINE`, grouping `none`
  - `revenue` with `DependencyPeriodRole.COMPARISON`, grouping `none`
- required canonical fields:
  - `order_date`
  - `line_revenue`
  - `currency`

The future implementation must add exactly one new execution implementation ref:

`p7_001:python_decimal_dependency_arithmetic:revenue_change_v1`

The future implementation must bind `revenue_change.execution_implementation_ref` to that ref.

The future implementation must replace the dormant Revenue Change validation refs with the following required validation-rule refs:

- `validation:revenue_change_from_validated_revenues`
- `validation:revenue_change_dependency_context`
- `validation:revenue_change_currency_consistency`

Do not keep `validation:revenue_change_direction` as a required Revenue Change validation rule. Direction is an observed sign of a valid result, not an independent validity condition.

Do not add validation refs for Revenue Change Percentage.

---

## 11. ExecutionPlan Requirements

Extend the existing P3 plan builder narrowly.

A `revenue_change` PlanMetricNode must:

- have `metric_ref == "revenue_change"`;
- have `metric_version == "metric_dictionary_v1"`;
- have `period_refs == (baseline_period.period_id, comparison_period.period_id)`;
- have exactly two `population_refs`, one Baseline and one Comparison, both grouping `none`;
- have exactly two dependency node IDs;
- depend on one Baseline Revenue node;
- depend on one Comparison Revenue node;
- carry the active Revenue Change implementation ref;
- carry exactly the active Revenue Change required validation rule refs;
- remain `not_executed` before execution;
- preserve chain authorization from eligible requested Metrics; and
- remain blocked when its own Data Sufficiency eligibility is blocked.

Pre-execution validation must reject malformed Revenue Change dependency sets, including:

- missing dependency node;
- extra dependency node;
- wrong dependency Metric;
- wrong dependency grouping;
- wrong dependency period role;
- duplicate Baseline dependency;
- duplicate Comparison dependency;
- dependency populations incompatible with the Revenue Change populations;
- executable Revenue Change with blocked dependency node; and
- executable Revenue Change without eligible requested-chain authorization.

Do not introduce a generic DAG framework.

---

## 12. Deterministic Execution Requirements

Extend the existing deterministic executor narrowly.

Revenue Change execution must be authorized only for executable `revenue_change` PlanMetricNodes.

The execution must perform only:

`comparison_revenue.value - baseline_revenue.value`

using authoritative Decimal values from executed Revenue dependency results.

Execution may consume the in-memory dependency results produced earlier in the same `execute_plan` run, but the future validation stage must still require persisted validated dependency authority.

Execution requirements:

- add `revenue_change` to the approved executable Metric set;
- validate the node implementation ref against the Metric Registry;
- require exactly one Baseline Revenue dependency result and one Comparison Revenue dependency result;
- require both dependency values to be Decimal;
- require both dependency states to be `MetricState.VALID`;
- require matching dataset and canonical dataset lineage;
- require compatible population/scope with differing only governed period role;
- require matching currency;
- compute with an explicit local Decimal context/policy;
- do not depend on ambient Decimal context;
- produce `MetricState.VALID` for valid positive, zero, and negative Decimal results;
- produce no Undefined result for zero Baseline Revenue;
- persist an ExecutionRecord;
- persist an immutable ExecutedResult artifact; and
- preserve current event-ID vs semantic-fingerprint discipline.

Use this execution implementation ref:

`p7_001:python_decimal_dependency_arithmetic:revenue_change_v1`

Use this calculation policy ID:

`p7_revenue_change_decimal_calculation_policy_v1`

Use explicit Decimal policy metadata equivalent in spirit to AOV:

- precision: 38
- rounding: ROUND_HALF_EVEN
- operation: subtraction

The operation metadata must retain:

- Baseline Revenue result ref;
- Comparison Revenue result ref;
- Baseline period ref;
- Comparison period ref;
- calculation policy;
- formula string or deterministic operation representation.

Do not execute Revenue Change by running a separate Revenue SUM query.

---

## 13. Empty Period Semantics

Preserve Frozen Revenue empty-period semantics.

A complete governed period with no eligible Revenue may legitimately have:

Revenue = 0

Therefore the future implementation must support:

- Baseline Revenue 0 and Comparison Revenue greater than 0 -> positive Revenue Change;
- Baseline Revenue greater than 0 and Comparison Revenue 0 -> negative Revenue Change;
- both period Revenues 0 -> Revenue Change 0.

Do not make Revenue Change Undefined merely because one period Revenue is zero.

Revenue Change Percentage is out of scope, so its zero-baseline Undefined rule is irrelevant to P7-001.

---

## 14. MetricState Behavior

Use Frozen MetricState semantics.

For P7-001:

`MetricState.VALID`

Revenue Change is Valid when both period Revenue dependencies are valid, authentic, comparable, and compatible.

`MetricState.QUALIFIED`

Do not invent Qualified behavior. If Frozen authority and existing infrastructure provide a deterministic non-blocking comparison qualification, preserve it. If not, P7-001 may explicitly fail closed or defer Qualified handling, and must report that decision.

`MetricState.UNDEFINED`

Undefined is not ordinarily applicable for Revenue Change.

Do not use Undefined for zero Baseline Revenue.

`MetricState.INADMISSIBLE`

Revenue Change is Inadmissible or fails closed when:

- either Revenue dependency is inadmissible or unauthentic;
- periods are not comparable;
- population/scope is incompatible;
- currency is incompatible;
- dataset/canonical dataset authority mismatches;
- required evidence or Data Sufficiency authority is missing; or
- another blocking governed prerequisite fails.

Do not silently convert Qualified to Valid.

---

## 15. Validation Requirements

Extend the existing deterministic validation authority narrowly for `revenue_change`.

Do not create a generic rule engine.

Do not create a second validation-only Metric Registry.

Validation must independently verify the Frozen invariant:

Comparison Revenue
−
Baseline Revenue
=
Revenue Change

at authoritative precision.

Revenue Change validation must consume:

- persisted ExecutionRecord;
- persisted ExecutedResult artifact;
- governed ExecutionPlan;
- CanonicalDatasetReference;
- ArtifactStore;
- MetadataStore;
- Baseline Revenue ValidatedResult;
- Comparison Revenue ValidatedResult.

Add Revenue Change to the supported validation Metric set.

Add the exact rule IDs below to the existing narrow validation-rule registry:

### 15.1 `validation:revenue_change_from_validated_revenues`

This rule must verify:

- ExecutedResult value is Decimal;
- ExecutedResult state is `MetricState.VALID`;
- ExecutedResult precision metadata matches `p7_revenue_change_decimal_calculation_policy_v1`;
- dependency values are Decimal;
- expected value equals Comparison Revenue minus Baseline Revenue under the explicit P7 Decimal policy;
- actual value equals expected value; and
- positive, zero, and negative values are all accepted when arithmetic is correct.

### 15.2 `validation:revenue_change_dependency_context`

This rule must verify:

- exactly two Revenue dependencies;
- one Baseline Revenue dependency and one Comparison Revenue dependency;
- dependencies correspond to exact governed Plan dependency nodes;
- dependencies belong to the same AnalysisRequest;
- dependencies belong to the same ExecutionPlan;
- dependency plan_node_id values match Revenue Change dependency_node_ids;
- dependency Metric refs are `revenue`;
- dependency Metric definition versions are `metric_dictionary_v1`;
- dependency MetricStates are `MetricState.VALID`;
- dependency validation bundles are complete;
- dependency ValidationRecords passed;
- dependency ValidationRecord rule IDs match the Revenue Registry authority;
- dependency rule fingerprints are authentic;
- dependency bundle fingerprints are authentic;
- dependency ValidatedResult artifacts exist and match supplied dependencies; and
- dependency ExecutedResult artifacts remain authentic through the existing P5/P6 artifact model.

### 15.3 `validation:revenue_change_currency_consistency`

This rule must verify:

- Baseline Revenue currency equals Comparison Revenue currency;
- Revenue Change currency equals the dependency currency;
- ExecutionRecord resolved currency equals the dependency currency;
- population currency bases are compatible;
- canonical dataset currency authority is not contradicted; and
- no FX conversion occurred.

The existing lineage and population checks must also verify:

- dataset identity;
- canonical dataset identity;
- canonical dataset fingerprint;
- population IDs;
- population fingerprints;
- scope filters;
- grouping `none`;
- Baseline/Comparison period refs;
- Baseline/Comparison period roles;
- implementation ref;
- result fingerprint; and
- required validation rule completeness.

A failed required validation:

no ValidatedResult

and therefore:

no AdmissibleEvidence.

---

## 16. ValidatedResult Requirements

ValidatedResult for Revenue Change must use the existing contract.

Do not invent a competing schema.

For Revenue Change:

- `metric_ref`: `revenue_change`
- `metric_definition_version`: `metric_dictionary_v1`
- `value`: Decimal
- `metric_state`: `MetricState.VALID`
- `undefined_reason`: None
- `precision`: `p7_revenue_change_decimal_calculation_policy_v1`
- `unit`: `money`
- `currency`: governed dependency currency
- `period_ref`: may be the existing comparison-node period representation only if it can represent both periods deterministically
- `period_role`: may be a comparison-node role representation only if it can represent both roles deterministically

If the current ValidatedResult contract cannot retain enough exact Baseline/Comparison context for Revenue Change without ambiguity:

STOP and request Main Project review.

Do not silently collapse the two-period context.

---

## 17. Result And Evidence Fingerprints

Preserve existing event-vs-semantic identity discipline.

Execution events:

unique IDs.

Validation events:

unique IDs.

Evidence admissibility events:

unique IDs.

Stable semantic fingerprints must exclude event IDs and timestamps and include material authority.

Revenue Change result fingerprint must include:

- Metric ref/version;
- implementation ref or executor identity;
- canonical dataset ref/fingerprint;
- Baseline population ref/fingerprint;
- Comparison population ref/fingerprint;
- Baseline period ref/role;
- Comparison period ref/role;
- dependency result fingerprints or dependency result refs where semantically required;
- value;
- MetricState;
- precision;
- unit;
- currency; and
- executor/version authority.

Revenue Change validation fingerprint must include:

- validator identity/version;
- required rule IDs/versions;
- rule fingerprints;
- target ExecutedResult fingerprint;
- dependency ValidatedResult validation fingerprints;
- dependency result fingerprints;
- plan ID/fingerprint;
- dependency Plan node IDs;
- population/period/currency authority;
- expected value;
- actual value;
- actual state; and
- precision metadata.

Revenue Change Evidence fingerprint must include:

- P6/P7 evidence evaluator identity/version;
- claim type;
- EvidenceRole;
- AnalysisRequest fingerprint;
- Required Evidence IDs;
- DataSufficiencyResult fingerprint;
- ValidatedResult validation fingerprint;
- dataset and canonical dataset authority;
- Baseline/Comparison context;
- population/scope;
- currency;
- assumptions;
- qualifications;
- limitations; and
- no event IDs/timestamps except where already part of governed semantic authority.

Do not create an incompatible hashing convention.

---

## 18. Evidence Admissibility Requirements

Extend P6 only as much as necessary to admit:

Valid Revenue Change
→ descriptive
→ `EvidenceRole.METRIC_VALUE`

Do not add new EvidenceRole values.

P7-001 Evidence admissibility must require:

- persisted AnalysisRequest authority;
- persisted DataSufficiencyResult authority;
- applicable Required Evidence;
- Data Sufficiency MetricEligibility for `revenue_change`;
- authentic persisted Revenue Change ValidatedResult;
- complete Revenue Change ValidationRecord bundle;
- authentic Revenue Change validation fingerprint;
- authentic Revenue Change ExecutedResult artifact;
- request MetricReference for `revenue_change`;
- same Metric definition version;
- dataset and canonical dataset match;
- canonical dataset fingerprint match;
- population/scope match;
- exact Baseline/Comparison context;
- currency match;
- descriptive claim type only;
- `EvidenceRole.METRIC_VALUE`; and
- immutable AdmissibleEvidence artifact integrity.

Revenue Change Evidence must support bounded descriptive propositions such as:

- Revenue Change = X
- Revenue increased by X between governed periods
- Revenue decreased by X between governed periods

Do not implement natural-language ClaimDecision.

Do not implement diagnostic contribution interpretation.

Do not implement causal explanation.

ClaimDecision remains out of scope.

---

## 19. Required Evidence

Use existing Required Evidence and Data Sufficiency authorities.

Do not invent a second requirements registry.

P7-001 must use:

- `AnalysisRequest.required_evidence`
- `DataSufficiencyResult.required_evidence`
- `DataSufficiencyResult.available_evidence`
- `DataSufficiencyResult.metric_eligibility`
- `ExecutionPlan.sufficiency_id`
- `ExecutionPlan.eligible_requested_metric_refs`
- existing Required Evidence applicability by `metric_ref` and `claim_type`

Revenue Change must not execute or admit when applicable material prerequisites are missing.

If new Revenue Change-specific Required Evidence examples are needed in tests, they must use the existing `EvidenceRequirement` contract and derive directly from Frozen requirements. For example, a test may define a local requirement with:

- `metric_ref="revenue_change"`
- `claim_type=ClaimType.DESCRIPTIVE`
- description tied to governed comparison-period Revenue evidence

Do not invent external evidence.

---

## 20. Persistence Requirements

Reuse:

- ExecutionRecord persistence;
- ExecutedResult immutable artifact;
- ValidationRecord persistence;
- ValidatedResult immutable artifact;
- EvidenceAdmissibilityRecord persistence;
- AdmissibleEvidence immutable artifact.

Expected MetadataStore schema:

remain v5

Prefer no schema migration.

If a schema change appears necessary:

STOP and request Main Project review before implementation.

Do not add a new persistence framework.

---

## 21. Independent Chains

Preserve partial completion.

Failure of Revenue Change must not invalidate unrelated independently valid Revenue / Orders / AOV chains.

An unrelated Orders/AOV failure must not block Revenue Change when Revenue Change's own required Revenue dependencies remain valid and the request permits the independent chain.

Respect the actual ExecutionPlan dependency graph.

Do not introduce global failure propagation.

---

## 22. Required Success Cases

Future targeted implementation tests must include at minimum:

| Case | Baseline Revenue | Comparison Revenue | Expected Revenue Change |
| --- | ---: | ---: | ---: |
| A | 100 | 120 | +20 |
| B | 120 | 100 | -20 |
| C | 100 | 100 | 0 |
| D | 0 | 100 | +100 |
| E | 100 | 0 | -100 |
| F | 0 | 0 | 0 |

Use synthetic deterministic values only.

Do not rely on these illustrative numbers as production fixtures if Frozen fixture values differ.

Each success case must prove:

- Revenue dependency results are executed;
- Revenue dependencies are validated;
- Revenue Change executes;
- Revenue Change validates;
- Revenue Change becomes descriptive `metric_value` AdmissibleEvidence; and
- Revenue Change Percentage remains unimplemented.

---

## 23. Required Failure Cases

Future tests must include at minimum:

- missing Baseline Revenue dependency;
- missing Comparison Revenue dependency;
- wrong period roles;
- dependencies from different requests;
- dependencies from different plans;
- wrong Plan node;
- caller-fabricated Revenue result;
- missing dependency artifact;
- tampered dependency artifact;
- incomplete dependency ValidationRecord bundle;
- failed dependency validation;
- forged dependency validation fingerprint;
- different dataset;
- different canonical dataset;
- population mismatch;
- request scope mismatch;
- currency mismatch;
- period comparability failure;
- wrong Metric/version;
- malformed Revenue Change plan dependency set;
- tampered Revenue Change ExecutedResult;
- incorrect arithmetic;
- missing Revenue Change validation rule;
- forged Revenue Change validation record;
- Revenue Change evidence artifact tamper.

All fail closed.

---

## 24. Required Test Groups

The future implementation must run at minimum:

- new Revenue Change targeted tests;
- Metric Registry regressions;
- plan builder regressions;
- execution regressions;
- validation regressions;
- P6 evidence regressions;
- persistence regressions if touched;
- full repository suite;
- `git diff --check`.

All Phase 1 through P6 tests must remain passing.

Do not weaken existing tests.

Expected impacted test areas include:

- `tests/metrics/test_registry.py`
- `tests/engine/test_plan_builder.py`
- `tests/engine/test_execution.py`
- `tests/validation/test_validator.py`
- `tests/evidence/test_admissibility.py`
- `tests/persistence/test_metadata_store.py` only if persistence behavior is touched

---

## 25. Expected Implementation Areas

Future P7 implementation may modify only the minimum files required.

Expected production files:

- `src/commerce_lens/metrics/registry.py`
- `src/commerce_lens/engine/plan_builder.py`
- `src/commerce_lens/engine/execution.py`
- `src/commerce_lens/validation/rules.py`
- `src/commerce_lens/validation/validator.py`
- `src/commerce_lens/evidence/admissibility.py`

Expected contract changes:

Prefer none.

If the current result/evidence contracts cannot deterministically represent Baseline/Comparison context for Revenue Change, STOP and request Main Project review.

Expected persistence changes:

Prefer none.

Expected dependency changes:

None.

---

## 26. Dependencies

Expected new dependencies:

NONE.

Do not add packages.

If a new package is required:

STOP and request Main Project authorization.

---

## 27. Main Project STOP Conditions

STOP rather than inventing semantics if Frozen/current authority does not deterministically establish:

- exact Revenue Change Metric Registry ref/version;
- exact Baseline/Comparison dependency representation;
- period comparability authority;
- Revenue dependency authenticity;
- required Revenue Change validation-rule IDs;
- Revenue Change Required Evidence applicability;
- Qualified Revenue Change behavior if encountered;
- sufficient Baseline/Comparison context in ExecutedResult, ValidatedResult, EvidenceAdmissibilityRecord, or AdmissibleEvidence;
- any needed persistence schema change;
- any need to modify Frozen specifications;
- any need to add dependencies.

---

## 28. Definition Of Done

P7-001 future implementation is complete only when:

- Revenue Change remains the single canonical `revenue_change` Metric in the Metric Registry;
- Metric Registry version advances to `metric_registry_mvp_v3`;
- Metric definition version remains `metric_dictionary_v1`;
- Registry binds Revenue Change to `p7_001:python_decimal_dependency_arithmetic:revenue_change_v1`;
- P3 plan authority represents exact Baseline and Comparison Revenue dependencies;
- malformed Revenue Change dependency graphs fail closed;
- deterministic execution computes Comparison Revenue minus Baseline Revenue;
- execution is durably traceable;
- positive, zero, and negative Revenue Change values are valid when dependencies are valid;
- zero Revenue in either period does not make Revenue Change Undefined;
- deterministic validation independently verifies arithmetic, dependency authenticity, period roles, population/scope compatibility, currency, Metric/version, and artifact integrity;
- complete validation bundle is durable;
- ValidatedResult exists only after all required validations pass;
- P6 Evidence admissibility accepts authentic Valid Revenue Change for descriptive `metric_value` use;
- AdmissibleEvidence is immutable and independently verifiable;
- tampering at dependency/result/validation/evidence stages fails closed;
- existing Revenue / Orders / AOV behavior remains unchanged;
- all tests pass;
- `git diff --check` passes;
- no dependency is added;
- no Frozen file is changed;
- no scope expansion occurs.

---

## 29. Future Implementation Report

The future P7 implementation report must include:

A. Files created/modified

B. Revenue Change Metric Registry definition

C. Exact dependency graph

D. Baseline/Comparison authority

E. Revenue dependency authenticity

F. Decimal/precision policy

G. Execution design

H. ExecutedResult design

I. Validation rule IDs

J. Validation design

K. Population/scope comparability

L. Currency behavior

M. MetricState behavior

N. Evidence admissibility extension

O. Evidence fingerprint behavior

P. Persistence changes

Q. Metadata schema version

R. Tests added/modified

S. Targeted result

T. Registry/plan regression result

U. Execution regression result

V. Validation regression result

W. Evidence regression result

X. Full-suite result

Y. `git diff --check`

Z. Dependencies changed

AA. Frozen files changed

AB. ClaimDecision implemented

Expected:

NO

AC. Revenue Change Percentage implemented

Expected:

NO

AD. Contribution implemented

Expected:

NO

AE. MCP / external executor / Wren implemented

Expected:

NO

AF. Known limitations

AG. Frozen conflicts / ambiguity

Then STOP.

---

## 30. P7-001 Implementation Boundary

When implementation is later authorized:

Do NOT modify:

- `docs/frozen/`
- unrelated tasks
- decisions
- README
- dependency manifests except under explicit Main Project authorization

Do NOT implement beyond this task.

When P7-001 implementation is complete:

STOP and wait for Main Project Review or a new explicit task.

---

## 31. Formal Approval And Freeze Record

Formal Main Project decision:

P7-001 — APPROVED / FROZEN

Final approved implementation commit:

f48b75eb0f67f5b14675886e6ce1749835d2dc16

Final verification evidence:

- Python 3.11.9
- DuckDB 1.5.5
- pytest 8.4.2
- MetadataStore schema v5
- validation: 71 passed
- engine: 144 passed
- evidence: 84 passed
- persistence: 16 passed
- metrics/sufficiency/contracts: 35 passed
- full suite: 398 passed
- final full rerun: 398 passed
- git diff --check passed
- material findings: NONE

Corrected blocker classes:

1. execution-stage Revenue dependency lineage;
2. Revenue Change scope provenance duplication;
3. validation-stage dependency ExecutionRecord lineage.

ClaimDecision implemented:

NO

Revenue Change Percentage implemented:

NO

MCP / external executor / Wren implemented:

NO

P7-001 is closed and Frozen. Do not begin P8 without separate Main Project authorization.
