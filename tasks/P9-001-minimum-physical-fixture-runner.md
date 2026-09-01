# P9-001 - Minimum Physical Fixture Runner

## Status

PROPOSED / NOT AUTHORIZED

Implementation:
NOT STARTED

Main Project Review:
CORRECTION REQUIRED APPLIED; RE-REVIEW REQUIRED BEFORE IMPLEMENTATION

This task is task specification only. It does not authorize implementation.

P9-001 must not be implemented until a separate Main Project Review approves
this corrected specification and explicitly authorizes implementation.

Current required correction baseline:

- branch: `main`
- starting HEAD: `84ab96227ea58353217d50b15a23a2051499f4bb`
- starting HEAD message: `Define P9-001 minimum physical fixture runner`
- MetadataStore schema: `v6`

Current approved implementation state ends at:

```text
AnalysisRequest
-> DataSufficiencyResult
-> ExecutionPlan
-> ExecutionRecord
-> ExecutedResult
-> ValidationRecord
-> ValidatedResult
-> EvidenceAdmissibilityRecord
-> AdmissibleEvidence
-> ClaimCandidate
-> ClaimDecision
-> STOP
```

Current governed Metrics:

- `revenue`
- `orders`
- `aov`
- `revenue_change`

Current positive Claim permission:

- `ClaimType.DESCRIPTIVE` only

P8-001 is APPROVED / FROZEN. Do not reopen P1-P8.

---

## 1. Read-Only Feasibility Audit

This correction inspected current repository state read-only before modifying
this task specification.

Inspected files and areas:

- `pyproject.toml`
- `src/commerce_lens/application/`
- current public/in-process application interfaces
- current P1-P8 production entry points under `src/commerce_lens/`
- `tests/intake/test_csv_adapter.py`
- `tests/intake/test_excel_adapter.py`
- `tests/intake/test_sqlite_adapter.py`
- `tests/canonical/test_canonicalization.py`
- `tests/sufficiency/test_evaluator.py`
- `tests/validation/test_validator.py`
- `tests/evidence/test_admissibility.py`
- `tests/evidence/test_claim_admissibility.py`

Factual audit findings:

- PyYAML is already present in approved dependencies as `PyYAML>=6,<7`.
- `src/commerce_lens/application/__init__.py` is a placeholder containing no
  public application service callable.
- `src/commerce_lens/contracts/results.py` defines `AnalysisResult`, but no
  current public service constructs it across the required P1-P8 path.
- Current lower-level production entry points include
  `DatasetRegistry.register_source`, `canonicalize_dataset`,
  `evaluate_data_sufficiency`, `build_execution_plan`, `execute_plan`,
  `validate_executed_result`, `evaluate_evidence_admissibility`,
  `persist_claim_candidate`, `evaluate_claim_admissibility`,
  `get_authoritative_claim_decision`, `list_authoritative_claim_decisions`, and
  `verify_claim_decision_artifact`.
- These lower-level entry points are not the Frozen Architecture public
  application service used by the Skill.
- Current CSV adapter conformance coverage is SATISFIED for controlled physical
  inspection and source preservation.
- Current XLSX adapter conformance coverage is SATISFIED for controlled physical
  inspection, governed sheet selection, source preservation, and formula
  fail-closed behavior.
- Current SQLite adapter conformance coverage is SATISFIED for controlled
  physical inspection, governed table selection, read-only access, and no SQL
  execution from table-name input.
- Current canonicalization tests also prove material CSV/XLSX/SQLite convergence
  for canonical monetary values.
- Current lower-level authority supports missing `line_revenue`
  (`canonical.line_revenue.invalid`), mixed currency (`canonical.currency.mixed`),
  duplicate order-line identity (`canonical.identity.duplicate`), and incomplete
  comparison coverage (`SufficiencyState.INSUFFICIENT_EVIDENCE`) as fail-closed
  semantics.
- Because the required public application service is missing, no Frozen Fixture
  variant is selected for `PHYSICALIZE NOW` in this corrected P9 inventory.

Explicit prerequisite blocker:

`P9_PREREQUISITE_PUBLIC_APPLICATION_SERVICE_MISSING`

P9 implementation must STOP until Main Project separately resolves the public
application-service prerequisite.

No PyYAML blocker is present because PyYAML is already an approved current
dependency.

---

## 2. Purpose

P9-001 defines the minimum deterministic semantic and evidence-governance
physical proof layer before the Public v0.1 Integration Gate.

The purpose is to prove that the implemented CommerceLens reliability chain can
be exercised against physical structured inputs and deterministic expected
outcomes through the same public application-service boundary the Skill uses.

P9-001 does not prove every Public v0.1 release requirement by itself. Source
adapter release readiness remains a separate release prerequisite recorded in
this task.

P9-001 is not:

- the full 40-family MVP fixture implementation;
- the Decision Reliability Benchmark;
- benchmark scoring;
- leaderboard infrastructure;
- a generic testing framework;
- a new analytics engine;
- a Skill;
- a CLI product;
- a UI;
- a synthetic data generator framework;
- source-adapter portability productization; or
- the Public v0.1 Integration Gate.

P9-001 does not begin the Public v0.1 Integration Gate.

---

## 3. Governing Authority

P9-001 is subordinate to all Approved / Frozen project authority under
`docs/frozen/`, especially:

- `PROJECT_MASTER_INSTRUCTIONS.md`
- `PRD.md`
- `CommerceLens_Skill_First_Scope_Migration_Analysis_v1.1.md`
- `SKILL_SCOPE_SPECIFICATION.md`
- `EVIDENCE_CONTRACT_SPECIFICATION.md`
- `CANONICAL_DATASET_AND_METRIC_DICTIONARY.md`
- `EVALUATION_FIXTURES_SPECIFICATION.md`
- `ARCHITECTURE_SPECIFICATION.md`

P9-001 also preserves all Approved / Frozen implementation task authority
through:

- `tasks/P3-001-metric-registry-population-plan.md`
- `tasks/P4-001-revenue-orders-aov-reference-execution.md`
- `tasks/P5-001-revenue-orders-aov-deterministic-validation.md`
- `tasks/P6-001-narrow-evidence-admissibility.md`
- `tasks/P7-001-revenue-change-vertical-slice.md`
- `tasks/P8-001-claim-decision-foundation.md`

If implementation convenience conflicts with Frozen authority or approved task
authority, implementation must STOP and request Main Project Review.

Do not modify Frozen specifications during P9-001.

---

## 4. Public Application-Service Authority

Frozen Architecture requires the P9 fixture runner to invoke the same public
application service used by the Skill.

The required conceptual path is:

```text
Physical Fixture
-> Declared AnalysisRequest
-> Public Engine Application Service
-> production deterministic pipeline
-> AnalysisResult / governed structured result
-> deterministic expected-outcome comparison
```

Current factual service status:

- Public application service currently exists: NO.
- Exact module/callable: NONE.
- Can the current public application service execute the required P1-P8 P9 path:
  NO.

The future runner must not independently orchestrate production internals by
directly stitching together:

```text
intake
-> canonicalization
-> sufficiency
-> executor
-> validator
-> evidence
-> Claim evaluator
```

as a runner-owned alternative application flow.

P9 implementation must STOP under
`P9_PREREQUISITE_PUBLIC_APPLICATION_SERVICE_MISSING` until Main Project provides
or authorizes the public application-service prerequisite.

Do not silently treat private production functions as the public application
service.

---

## 5. Critical Scope Rule

Do not physicalize a Frozen Fixture merely because it exists in
`EVALUATION_FIXTURES_SPECIFICATION.md`.

A P9 physical case is eligible only when every material expected behavior that
P9 claims to evaluate is already supported by current P1-P8 authority and can be
run through the required public application service.

Current implementation does not yet govern:

- Revenue Change Percentage;
- Product metrics;
- Category metrics;
- Product/Category Revenue Change;
- Contribution;
- Contribution Share;
- rankings;
- formal Findings;
- Alternative Explanation artifacts;
- Recommendation artifacts; or
- positive Qualified Admissible Claim paths.

Therefore P9-001 must not claim complete conformance for any Frozen Fixture whose
authoritative material outcome depends on those unimplemented capabilities.

No fixture projection may silently remove a material expected outcome and still
call itself complete conformance to that Frozen Fixture ID.

If only part of a Frozen Fixture is currently executable, implementation must
exclude it from Frozen Fixture physicalization and use a clearly identified
current-authority P9 conformance case instead.

Do not invent new Frozen Fixture IDs.

---

## 6. Physical Fixture Format

Frozen Architecture authority requires YAML metadata plus tiny CSV inputs as the
primary physical fixture representation.

P9-001 may introduce the smallest repository-local physical asset layout needed
to exercise current authority after the public application service prerequisite
is resolved. The preferred future shape is:

```text
tests/
  fixtures/
    p9/
      cases/
        <case-id>/
          input.csv
          manifest.yaml
```

An equivalent repository layout is acceptable only when it preserves YAML
metadata plus tiny CSV input as the primary representation.

The runner must load YAML with safe YAML loading. Because `PyYAML>=6,<7` already
exists in approved dependencies, P9 must reuse that dependency and must not add a
new dependency for manifest parsing.

JSON is not the primary P9 fixture metadata format.

Physical assets must be:

- small synthetic structured input files;
- public-safe;
- deterministic;
- isolated;
- independently runnable;
- order-independent;
- reproducible from a clean checkout; and
- free of external network dependencies.

Do not require:

- SQLite fixture databases for the semantic P9 suite;
- XLSX fixture generation for the semantic P9 suite;
- physical customer, production, private, or scraped proprietary data;
- a new runtime dependency; or
- MetadataStore schema v7.

Existing intake and canonicalization tests may continue to cover format-specific
CSV, XLSX, and SQLite behavior. P9 is about integrated semantic and
evidence-governance conformance, not duplicating every source-adapter test.

Expected MetadataStore schema remains `v6`.

---

## 7. Source-Adapter Release Boundary

P9 semantic fixture suite is not the source-adapter conformance suite.

Do not duplicate the semantic fixture inventory across CSV, XLSX, and SQLite.

Current source-adapter conformance audit:

- CSV adapter physical conformance: SATISFIED.
- XLSX adapter physical conformance: SATISFIED.
- SQLite adapter physical conformance: SATISFIED.

Unsatisfied source-adapter coverage recorded as Public v0.1 release
prerequisite:

- NONE.

P9 completion must not be represented as the only Public v0.1 release
requirement. It covers the minimum semantic and evidence-governance physical
proof layer.

---

## 8. Physical Case Contract

Every P9 physical, runner-level, or harness-level conformance case must bind the
following machine-readable fields:

- stable case identity;
- governing Frozen Fixture ID when fully applicable;
- explicit implementation-conformance authority reference when no Frozen Fixture
  ID is fully applicable;
- purpose;
- source input path when the case consumes physical input;
- supported analytical request;
- applicable Metric or Metrics;
- expected Data Sufficiency state;
- expected execution disposition;
- expected deterministic result or governed Metric state;
- expected validation disposition;
- expected Metric state;
- expected Evidence disposition;
- expected Claim type;
- expected Claim state;
- expected failure code when fail-closed;
- expected final disposition;
- prohibited output or material Claim;
- governing authority reference; and
- whether the case is physical-input, runner-level, or harness-level.

Do not use arbitrary natural-language expected answers as correctness authority.

Exact numerical expected values must come from governing semantics and physical
fixture rows.

One case variant must encode exactly one authoritative expected material outcome.
The runner must not accept:

- PASS with qualification as an alternative to PASS;
- multiple allowable failure codes;
- `if material`;
- `as applicable`;
- fuzzy numerical tolerances that replace governed Decimal semantics; or
- dynamic snapshot rewriting.

---

## 9. Minimum Behavioral Coverage

The approved P9 implementation must target exactly 8 cases in its initial
inventory. It must not exceed 10 physical/conformance cases without a documented
Main Project reason.

The minimum suite must prove the following currently implemented behaviors after
the public application service prerequisite is resolved.

### A. Supported Positive Chain

At least one case must prove an authentic supported chain reaches:

```text
physical structured input
-> intake
-> canonicalization
-> Data Sufficiency
-> Public Engine Application Service
-> ExecutionPlan
-> deterministic execution
-> deterministic validation
-> AdmissibleEvidence
-> ClaimCandidate
-> authoritative Admissible ClaimDecision
```

This positive chain must use only currently governed Metrics and
`ClaimType.DESCRIPTIVE`.

Do not require Revenue Change Percentage.

### B. Data Sufficiency Fail-Closed

At least one physical case must prove materially missing or invalid Required
Evidence causes the affected chain to stop without fabricated result.

The exact initial fail-closed cases are:

- missing `line_revenue`, failure code `canonical.line_revenue.invalid`; and
- mixed currency, failure code `canonical.currency.mixed`.

Each required outcome must preserve:

```text
Insufficient evidence to conclude.
```

### C. Deterministic Validation Failure

One harness-level case must prove:

```text
ExecutedResult != ValidatedResult
```

The exact validation attack is:

- persist a `revenue_change` `ExecutedResult` with value `21.00` when authentic
  Baseline Revenue is `100.00` and authentic Comparison Revenue is `120.00`,
  recompute that artifact fingerprint, and invoke the existing production
  validator.

The exact validation rule is:

- `validation:revenue_change_from_validated_revenues`

The exact validation failure code is:

- `value_mismatch`

The case must produce no authoritative `ValidatedResult`, no
`AdmissibleEvidence`, and no admissible material Claim permission for the failed
chain.

Do not invent a new validator.

### D. Claim Refusal

One P8 conformance case must prove that authentic descriptive Evidence cannot
authorize an unsupported stronger Claim.

The exact unsupported stronger Claim type is:

- `ClaimType.DIAGNOSTIC`

The exact public-v0.1-oriented question class is:

- `why_did_revenue_decline`

The exact expected `ClaimDecision` is:

- `ClaimState.INADMISSIBLE`

The exact failure code is:

- `unsupported_claim_type`

This case must end at `ClaimDecision`.

Do not implement AlternativeExplanation, Finding, or Recommendation.

### E. AOV Undefined

Include a current-authority conformance case proving:

```text
Orders = 0
-> AOV MetricState.UNDEFINED
-> undefined_reason = orders_equals_zero
-> metric_state Evidence
-> admissible descriptive AOV state Claim
```

The case must explicitly prove:

```text
AOV Undefined != numeric zero
```

This behavior is governed by Approved / Frozen P6/P8 task authority even though
the older Frozen Evaluation Fixture inventory does not contain a directly
matching dedicated physical Fixture ID.

Do not invent a Frozen FX ID for this case.

### F. Revenue Change

Include one physical case proving the current P7/P8 Revenue Change vertical
slice:

```text
Comparison Revenue - Baseline Revenue
```

with:

- complete governed periods;
- authentic Baseline and Comparison Revenue dependencies;
- deterministic Revenue Change validation;
- `AdmissibleEvidence`;
- descriptive Admissible `ClaimDecision`; and
- no formula duplication in the fixture runner.

The runner must consume production authority through the public application
service. It must not implement Revenue Change arithmetic itself.

### G. Provenance / Tamper Fail-Closed

One harness-level case must demonstrate that substituted authoritative lineage
cannot become authoritative material Claim permission.

The exact attack is:

- create an authentic Revenue descriptive candidate for one request, substitute
  same-valued Revenue `AdmissibleEvidence` and `ValidatedResult` references from
  a foreign request, persist the substituted candidate in the foreign authority
  context, and invoke `evaluate_claim_admissibility`.

The exact expected failure code is:

- `cross_request_substitution`

The exact expected `ClaimDecision` is:

- `ClaimState.INADMISSIBLE`

Do not build a security framework. Reuse current P8 ClaimDecision authority.

---

## 10. Exact Initial Case Inventory

The initial P9 inventory contains exactly 8 cases. Every case has one exact
material outcome.

| Field | `P9-CONF-POS-001` |
|---|---|
| Case class | Current-authority conformance |
| Frozen Fixture ID | NONE |
| Authority reference | P4/P5/P6/P8 Revenue, Orders, and AOV descriptive chain |
| Case level | physical-input |
| Source input path | `tests/fixtures/p9/cases/P9-CONF-POS-001/input.csv` |
| Metrics | `revenue`, `orders`, `aov` |
| Analytical request class | `describe_total_revenue_orders_aov_single_period` |
| Expected Data Sufficiency state | `SufficiencyState.SUFFICIENT` |
| Expected execution disposition | completed |
| Expected deterministic value / state | Revenue `10.00`; Orders `1`; AOV `10.00` |
| Expected validation disposition | passed |
| Expected Metric state | `MetricState.VALID` for all three Metrics |
| Expected Evidence disposition | `EvidenceAdmissibilityStatus.PASSED`, `EvidenceRole.METRIC_VALUE` |
| Expected ClaimType | `ClaimType.DESCRIPTIVE` |
| Expected ClaimState | `ClaimState.ADMISSIBLE` |
| Expected failure code | NONE |
| Expected final disposition | completed with authoritative descriptive ClaimDecision |
| Prohibited material output | diagnostic, causal, predictive, prescriptive, Finding, Recommendation |
| Governing authority | P4-001, P5-001, P6-001, P8-001 |

| Field | `P9-CONF-REVCHG-001` |
|---|---|
| Case class | Current-authority conformance |
| Frozen Fixture ID | NONE |
| Authority reference | P7/P8 Revenue Change descriptive authority |
| Case level | physical-input |
| Source input path | `tests/fixtures/p9/cases/P9-CONF-REVCHG-001/input.csv` |
| Metrics | `revenue_change` |
| Analytical request class | `describe_total_revenue_change_baseline_to_comparison` |
| Expected Data Sufficiency state | `SufficiencyState.SUFFICIENT` |
| Expected execution disposition | completed |
| Expected deterministic value / state | Baseline Revenue `100.00`; Comparison Revenue `120.00`; Revenue Change `20.00` |
| Expected validation disposition | passed |
| Expected Metric state | `MetricState.VALID` |
| Expected Evidence disposition | `EvidenceAdmissibilityStatus.PASSED`, `EvidenceRole.METRIC_VALUE` |
| Expected ClaimType | `ClaimType.DESCRIPTIVE` |
| Expected ClaimState | `ClaimState.ADMISSIBLE` |
| Expected failure code | NONE |
| Expected final disposition | completed with authoritative descriptive Revenue Change ClaimDecision |
| Prohibited material output | Revenue Change %, why/driver/cause, contribution, ranking, Finding, Recommendation |
| Governing authority | P7-001, P8-001 |

| Field | `P9-CONF-SUFF-MISSING-REVENUE-001` |
|---|---|
| Case class | Current-authority conformance |
| Frozen Fixture ID | NONE |
| Authority reference | Frozen `FX-SUFF-003` semantic reference without Frozen ID claim; Phase 2/P3 fail-closed authority |
| Case level | physical-input |
| Source input path | `tests/fixtures/p9/cases/P9-CONF-SUFF-MISSING-REVENUE-001/input.csv` |
| Metrics | `revenue` |
| Analytical request class | `describe_total_revenue_single_period` |
| Expected Data Sufficiency state | `SufficiencyState.DATA_QUALITY_FAILURE` |
| Expected execution disposition | not started |
| Expected deterministic value / state | no value; `MetricState.INADMISSIBLE` |
| Expected validation disposition | not started |
| Expected Evidence disposition | not started |
| Expected ClaimType | `ClaimType.DESCRIPTIVE` |
| Expected ClaimState | `NO_CLAIM_DECISION_AUTHORIZED` |
| Expected failure code | `canonical.line_revenue.invalid` |
| Expected final disposition | Insufficient evidence to conclude; fail closed |
| Prohibited material output | derived `quantity * unit_price`, zero-imputed Revenue, ExecutedResult, ValidatedResult, AdmissibleEvidence, ClaimDecision |
| Governing authority | Canonical Dataset and Metric Dictionary, Phase 2, P3-001 |

| Field | `P9-CONF-SUFF-MIXED-CURRENCY-001` |
|---|---|
| Case class | Current-authority conformance |
| Frozen Fixture ID | NONE |
| Authority reference | Frozen `FX-SUFF-001` mixed-currency semantic reference without Frozen ID claim; Phase 2/P3 fail-closed authority |
| Case level | physical-input |
| Source input path | `tests/fixtures/p9/cases/P9-CONF-SUFF-MIXED-CURRENCY-001/input.csv` |
| Metrics | `revenue` |
| Analytical request class | `describe_total_revenue_single_period` |
| Expected Data Sufficiency state | `SufficiencyState.DATA_QUALITY_FAILURE` |
| Expected execution disposition | not started |
| Expected deterministic value / state | no value; `MetricState.INADMISSIBLE` |
| Expected validation disposition | not started |
| Expected Evidence disposition | not started |
| Expected ClaimType | `ClaimType.DESCRIPTIVE` |
| Expected ClaimState | `NO_CLAIM_DECISION_AUTHORIZED` |
| Expected failure code | `canonical.currency.mixed` |
| Expected final disposition | Insufficient evidence to conclude; fail closed |
| Prohibited material output | FX conversion, inferred currency basis, aggregated monetary result, ExecutedResult, ValidatedResult, AdmissibleEvidence, ClaimDecision |
| Governing authority | Canonical Dataset and Metric Dictionary, Phase 2, P3-001 |

| Field | `P9-CONF-AOV-UNDEFINED-001` |
|---|---|
| Case class | Current-authority conformance |
| Frozen Fixture ID | NONE |
| Authority reference | P6/P8 AOV Undefined authority |
| Case level | physical-input |
| Source input path | `tests/fixtures/p9/cases/P9-CONF-AOV-UNDEFINED-001/input.csv` |
| Metrics | `orders`, `aov` |
| Analytical request class | `describe_aov_state_single_period_zero_orders` |
| Expected Data Sufficiency state | `SufficiencyState.SUFFICIENT` |
| Expected execution disposition | completed |
| Expected deterministic value / state | Orders `0`; AOV `MetricState.UNDEFINED`; `undefined_reason=orders_equals_zero`; AOV value `None` |
| Expected validation disposition | passed |
| Expected Metric state | Orders `MetricState.VALID`; AOV `MetricState.UNDEFINED` |
| Expected Evidence disposition | `EvidenceAdmissibilityStatus.PASSED`, `EvidenceRole.METRIC_STATE` |
| Expected ClaimType | `ClaimType.DESCRIPTIVE` |
| Expected ClaimState | `ClaimState.ADMISSIBLE` |
| Expected failure code | NONE |
| Expected final disposition | completed with authoritative descriptive AOV state ClaimDecision |
| Prohibited material output | numeric AOV zero, AOV metric-value Evidence, stronger Claim, Finding, Recommendation |
| Governing authority | P6-001, P8-001 |

| Field | `P9-CONF-VAL-REVCHG-WRONG-VALUE-001` |
|---|---|
| Case class | Current-authority conformance |
| Frozen Fixture ID | NONE |
| Authority reference | P5/P7 Revenue Change validation authority |
| Case level | harness-level |
| Source input path | NONE |
| Metrics | `revenue_change` |
| Analytical request class | `validate_total_revenue_change_baseline_to_comparison` |
| Expected Data Sufficiency state | `SufficiencyState.SUFFICIENT` |
| Expected execution disposition | tampered ExecutedResult exists with value `21.00` |
| Expected deterministic value / state | authoritative expected Revenue Change `20.00`; submitted value `21.00` |
| Expected validation disposition | failed by `validation:revenue_change_from_validated_revenues` |
| Expected Metric state | `MetricState.INADMISSIBLE` for the failed chain |
| Expected Evidence disposition | no AdmissibleEvidence authorized |
| Expected ClaimType | `ClaimType.DESCRIPTIVE` |
| Expected ClaimState | `NO_CLAIM_DECISION_AUTHORIZED` for the failed chain |
| Expected failure code | `value_mismatch` |
| Expected final disposition | validation failure; fail closed |
| Prohibited material output | ValidatedResult, AdmissibleEvidence, admissible ClaimDecision, narrative repair |
| Governing authority | P5-001, P7-001 |

| Field | `P9-CONF-CLAIM-DIAGNOSTIC-REFUSAL-001` |
|---|---|
| Case class | Current-authority conformance |
| Frozen Fixture ID | NONE |
| Authority reference | P8 unsupported stronger Claim authority |
| Case level | harness-level |
| Source input path | NONE |
| Metrics | `revenue_change` |
| Analytical request class | `why_did_revenue_decline` |
| Expected Data Sufficiency state | `SufficiencyState.SUFFICIENT` |
| Expected execution disposition | completed |
| Expected deterministic value / state | Revenue Change `-20.00` |
| Expected validation disposition | passed |
| Expected Metric state | `MetricState.VALID` |
| Expected Evidence disposition | `EvidenceAdmissibilityStatus.PASSED`, `EvidenceRole.METRIC_VALUE` |
| Expected ClaimType | `ClaimType.DIAGNOSTIC` |
| Expected ClaimState | `ClaimState.INADMISSIBLE` |
| Expected failure code | `unsupported_claim_type` |
| Expected final disposition | Inadmissible ClaimDecision |
| Prohibited material output | diagnostic answer, causal explanation, Finding, AlternativeExplanation artifact, Recommendation |
| Governing authority | P8-001 |

| Field | `P9-CONF-TAMPER-CROSS-REQUEST-001` |
|---|---|
| Case class | Current-authority conformance |
| Frozen Fixture ID | NONE |
| Authority reference | P8 cross-request substitution authority |
| Case level | harness-level |
| Source input path | NONE |
| Metrics | `revenue` |
| Analytical request class | `describe_total_revenue_single_period_with_foreign_evidence_substitution` |
| Expected Data Sufficiency state | `SufficiencyState.SUFFICIENT` |
| Expected execution disposition | completed for original and foreign contexts |
| Expected deterministic value / state | original Revenue `10.00`; foreign Revenue `10.00`; substituted foreign Evidence refs |
| Expected validation disposition | passed for original and foreign contexts |
| Expected Metric state | `MetricState.VALID` |
| Expected Evidence disposition | foreign Evidence rejected for original Claim authority |
| Expected ClaimType | `ClaimType.DESCRIPTIVE` |
| Expected ClaimState | `ClaimState.INADMISSIBLE` |
| Expected failure code | `cross_request_substitution` |
| Expected final disposition | Inadmissible ClaimDecision; fail closed |
| Prohibited material output | authoritative admissible ClaimDecision from substituted Evidence, equal-value provenance bypass |
| Governing authority | P8-001 |

---

## 11. Frozen Fixture Compatibility Matrix

This planning matrix establishes how P9 distinguishes full Frozen Fixture
physicalization from implementation-level conformance cases. It is not a full
40-family fixture plan.

| Class | Examples | P9 treatment |
|---|---|---|
| PHYSICALIZE NOW | NONE | No Frozen Fixture ID is selected while `P9_PREREQUISITE_PUBLIC_APPLICATION_SERVICE_MISSING` remains unresolved |
| CURRENT-AUTHORITY CONFORMANCE CASE | `P9-CONF-POS-001`; `P9-CONF-REVCHG-001`; `P9-CONF-SUFF-MISSING-REVENUE-001`; `P9-CONF-SUFF-MIXED-CURRENCY-001`; `P9-CONF-AOV-UNDEFINED-001`; `P9-CONF-VAL-REVCHG-WRONG-VALUE-001`; `P9-CONF-CLAIM-DIAGNOSTIC-REFUSAL-001`; `P9-CONF-TAMPER-CROSS-REQUEST-001` | Use stable P9 conformance IDs; do not invent Frozen FX IDs |
| DEFER | `FX-VALID-001` complete canonical workflow; `FX-SUFF-003`; `FX-SUFF-001`; `FX-DQ-002`; `FX-SUFF-004`; `FX-METRIC-001` when evaluating Revenue Change %; `FX-CLAIM-002`; `FX-CLAIM-003`; `FX-CLAIM-004`; contribution, ranking, product/category, Finding, Alternative Explanation, Recommendation, positive Qualified Admissible fixtures | Defer Frozen Fixture ID physicalization until the public application service exists and Main Project confirms complete material conformance for each selected Frozen Fixture |

The full Frozen fixture suite is not required for P9.

---

## 12. Runner Responsibility

The future P9 runner must be thin and must invoke the public application service
once the service prerequisite is resolved.

It may:

- discover approved P9 case manifests;
- load physical fixture data;
- load `manifest.yaml` with safe YAML loading;
- submit the declared `AnalysisRequest` to the public application service;
- collect the governed structured `AnalysisResult`;
- compare actual material outputs against expected contracts;
- emit deterministic per-case PASS/FAIL; and
- emit failure detail useful for review.

It must not:

- calculate Metrics independently;
- reproduce Metric formulas;
- independently orchestrate production internals as an alternative application
  flow;
- repair production results;
- synthesize missing Evidence;
- use LLM judgment;
- rewrite expected outcomes dynamically;
- choose among multiple acceptable material outcomes;
- silently update snapshots;
- score model quality;
- weight fixture importance;
- produce percentage scores;
- produce aggregate benchmark grades;
- rank models, vendors, or runs;
- create leaderboards; or
- create confidence scores.

The production engine remains authoritative through the public application
service. The runner is an evaluator, not a second analytics implementation.

Physical Fixture Runner is not the Decision Reliability Benchmark.

---

## 13. Public v0.1 Relationship

P9-001 must provide the deterministic physical evidence layer that allows the
later Public v0.1 Integration Gate to demonstrate:

```text
supported descriptive answer
+
unsupported stronger-Claim refusal
+
AOV Undefined
+
fail-closed provenance
```

using reproducible physical cases.

P9-001 itself must not create:

- `SKILL.md`;
- a user-facing response renderer;
- a thin application/invocation boundary;
- public README changes;
- a GitHub release;
- frontend;
- benchmark scoring; or
- Decision Reliability Benchmark productization.

---

## 14. Test Strategy

Future P9 implementation tests must cover at least:

- safe YAML manifest/case schema validation;
- case discovery;
- independent case execution through the public application service;
- deterministic expected-vs-actual comparison;
- one-case-one-outcome enforcement;
- unknown fixture/conformance type rejection;
- missing physical asset failure;
- unexpected result failure;
- unexpected Metric state failure;
- unexpected Claim state failure;
- unexpected failure code failure;
- prohibited material output detection where structurally representable;
- fixture order independence;
- repeat-run deterministic result identity where semantics require it;
- runner behavior without duplicating Metric formulas;
- rejection of benchmark scoring output; and
- hard failure when the public application service callable is unavailable.

Do not duplicate every P1-P8 unit test. P9 tests must focus on integrated
physical behavior and runner contract behavior.

---

## 15. Acceptance Criteria

P9-001 implementation is successful only if:

1. `P9_PREREQUISITE_PUBLIC_APPLICATION_SERVICE_MISSING` has been resolved by
   Main Project before implementation authorization;
2. the approved minimum physical/conformance suite exists;
3. every case is synthetic and public-safe;
4. every case has one deterministic expected outcome;
5. every manifest uses YAML metadata loaded safely;
6. every semantic physical fixture input uses tiny CSV;
7. the runner invokes the public application service rather than duplicating
   Metric logic or stitching private internals;
8. a supported positive chain reaches authoritative `ClaimDecision`;
9. insufficiency fails closed;
10. deterministic validation failure remains distinct from execution failure;
11. AOV Undefined remains Undefined and not zero;
12. an unsupported diagnostic Claim becomes `Inadmissible`;
13. Revenue Change reaches authoritative descriptive `ClaimDecision`;
14. cross-request substituted provenance cannot create authoritative Claim
    permission;
15. cases are isolated and order-independent;
16. no scoring or benchmark productization exists;
17. no future Metric, Finding, Alternative Explanation, Recommendation, or
    positive Qualified Admissible behavior is introduced;
18. MetadataStore schema remains `v6`;
19. no new dependency is added;
20. no Frozen file is modified;
21. no P1-P8 task semantics are reopened; and
22. the full repository regression suite passes.

---

## 16. Protected Boundaries

Future P9 implementation must not modify unless separately reviewed:

- `docs/frozen/`;
- Metric formulas;
- canonical semantics;
- P1-P8 Approved / Frozen task semantics;
- Claim policy semantics;
- Evidence admissibility semantics;
- MetadataStore schema;
- roadmap;
- `README.md`;
- `SKILL.md`;
- dependencies;
- production analytical semantics; or
- Public v0.1 integration artifacts.

If implementation believes schema v7 or a new dependency is required, STOP and
request Main Project Review.

---

## 17. Stop Conditions

Implementation must STOP if:

- `P9_PREREQUISITE_PUBLIC_APPLICATION_SERVICE_MISSING` remains unresolved;
- PyYAML is removed from approved dependencies before P9 implementation, in
  which case record `P9_PREREQUISITE_PYYAML_MISSING` and request Main Project
  review;
- a selected Frozen Fixture cannot be fully represented without omitting a
  material expected behavior;
- a physical case would require inventing new analytical semantics;
- the runner needs to duplicate Metric formulas;
- the runner needs LLM judgment;
- the runner needs to orchestrate private production internals instead of the
  public application service;
- P9 requires Revenue Change %;
- P9 requires Product/Category Metrics;
- P9 requires Contribution/ranking;
- P9 requires Findings;
- P9 requires Alternative Explanations;
- P9 requires Recommendations;
- P9 requires positive Qualified Admissible behavior;
- schema v7 appears necessary;
- a new runtime dependency appears necessary; or
- a Frozen authority conflict is discovered.

Do not silently solve a STOP condition.

---

## 18. Non-Authorization

This task specification does not authorize:

- creating fixture directories;
- creating physical CSV/YAML fixture assets;
- writing a fixture runner;
- writing a public application service;
- writing production code;
- modifying tests;
- modifying Frozen specifications;
- modifying `PROJECT_STATE.md`;
- modifying the roadmap;
- modifying `README.md`;
- creating an implementation branch;
- beginning P10;
- beginning the Public v0.1 Integration Gate;
- creating benchmark scoring; or
- pushing commits.

After this task specification is corrected and committed, STOP.

---

## 19. Self-Review Checklist

Before implementation authorization, Main Project Review must verify:

- primary metadata format is YAML, not JSON;
- tiny CSV remains the primary semantic fixture input;
- no new dependency was added;
- current PyYAML status is factual;
- runner authority explicitly requires the public application service;
- missing application service is a STOP prerequisite;
- exact case inventory contains no conditional case selection;
- every case has one exact material outcome;
- no outcome contains multiple acceptable alternatives;
- Frozen FX IDs are not used while the public application service prerequisite is
  unresolved;
- AOV Undefined uses a P9 current-authority identity;
- tamper case has one exact attack and failure result;
- Claim refusal has one exact unsupported Claim type;
- validation failure has one exact validator/failure;
- adapter release prerequisite status is recorded;
- P9 is not Benchmark;
- P9 does not begin Skill integration;
- no requirement says all 40 Frozen fixture families must be implemented;
- no unimplemented Metric is required;
- supported Claim permission is descriptive only;
- no positive Qualified Admissible path is invented;
- Revenue Change formula is not duplicated;
- the runner is thin;
- expected outcomes are deterministic;
- physical cases are synthetic/public-safe; and
- Public v0.1 Integration Gate remains after P9.
