# P9-001 - Minimum Physical Fixture Runner

## Status

APPROVED / FROZEN

Implementation:
COMPLETE

P9-PRE-001:
APPROVED / FROZEN

Public v0.1 Integration:
NOT STARTED

Main Project Review:
SOURCE REVIEW PASS

Independent runtime verification:
APPROVE

Approved implementation HEAD:

`ba72e2b658b854b0e45ba51a3273f9e4e5a593bd`

Implementation lineage:

- authorization baseline:
  `0355a0698c968e87481e8a30cbc8198cee7dd880`
- original implementation commit:
  `9671b6030da196b40f6d344f3c6c3fd9b80ead5d`
- final corrected implementation HEAD:
  `ba72e2b658b854b0e45ba51a3273f9e4e5a593bd`

Fresh post-fast-forward verification:

- focused P9 suite: 35 passed in 6.94s
- Public Application Service regression: 21 passed in 3.13s
- complete repository suite: 511 passed in 60.52s
- git diff --check: clean

Preserved independent verification evidence:

- focused P9 suite: 35 passed
- Public Application Service regression: 21 passed
- relevant P1-P8 regression: 417 passed
- complete repository suite: 511 passed
- source review: PASS
- independent runtime verification: APPROVE

P9-001 is approved and frozen after successful governance integration. This
freeze does not begin Public v0.1 Integration.

Frozen P9-001 provides:

- deterministic physical fixture execution;
- exactly eight initial P9 conformance cases;
- YAML fixture metadata;
- tiny synthetic CSV physical inputs;
- safe YAML loading;
- strict fixture contract validation;
- deterministic expected-vs-actual comparison;
- public `run_analysis(...)` path for normal analysis;
- public `evaluate_claim(...)` path for Claim evaluation;
- exactly one narrow Revenue Change direct-validator hostile exception;
- case isolation;
- order independence;
- repeat-run material reproducibility;
- source fixture integrity; and
- fail-closed YAML/case authority behavior.

Exact initial P9 cases:

- `P9-CONF-POS-001`
- `P9-CONF-REVCHG-001`
- `P9-CONF-SUFF-MISSING-REVENUE-001`
- `P9-CONF-SUFF-MIXED-CURRENCY-001`
- `P9-CONF-AOV-UNDEFINED-001`
- `P9-CONF-VAL-REVCHG-WRONG-VALUE-001`
- `P9-CONF-CLAIM-DIAGNOSTIC-REFUSAL-001`
- `P9-CONF-TAMPER-CROSS-REQUEST-001`

Frozen Fixture PHYSICALIZE NOW:

NONE

Frozen Fixture IDs claimed:

NONE

P9 conformance IDs are not Frozen FX IDs.

Frozen P9 proof points:

- positive: Revenue `10.00`; Orders `1`; AOV `10.00`; descriptive
  ClaimDecision `Admissible`;
- Revenue Change: baseline Revenue `100.00`; comparison Revenue `120.00`;
  Revenue Change `20.00`; descriptive ClaimDecision `Admissible`;
- missing Revenue: `canonical.line_revenue.invalid`; fail closed; no downstream
  authority;
- mixed currency: `canonical.currency.mixed`; fail closed; no FX conversion; no
  downstream authority;
- AOV Undefined: Orders `0`; AOV value `None`; MetricState `Undefined`;
  `undefined_reason=orders_equals_zero`; metric_state Evidence; descriptive
  Claim `Admissible`;
- hostile Revenue Change: submitted `21.00`; governed expected authority
  `20.00`; validation failure `value_mismatch`; failed state `Inadmissible`; no
  ValidatedResult; no AdmissibleEvidence; no ClaimDecision;
- diagnostic refusal: `ClaimType.DIAGNOSTIC`; `ClaimState.INADMISSIBLE`;
  failure `unsupported_claim_type`;
- cross-request substitution: equal-valued original Revenue `10.00`; foreign
  Revenue `10.00`; distinct request authority; `ClaimState.INADMISSIBLE`;
  failure `cross_request_substitution`.

Hostile authority freeze:

- case: `P9-CONF-VAL-REVCHG-WRONG-VALUE-001`
- Metric: `revenue_change`
- baseline: `100.00`
- comparison: `120.00`
- authoritative Revenue Change: `20.00`
- submitted Revenue Change: `21.00`
- rule: `validation:revenue_change_from_validated_revenues`
- expected failure: `value_mismatch`
- expected failed MetricState: `Inadmissible`

The fixed hostile contract rejects material mutation including Decimal-scale
drift. This is the one authorized hostile validation case and is not a
generalized tamper framework.

Non-blocking maintainability note:

Current hostile validation implementation reuses private Application Service
helper `_metric_state`. Independent runtime verification confirmed correct
current behavior. This is a non-blocking maintainability observation only.

Authorization review baseline:

- branch: `main`
- starting review HEAD:
  `d940ed2b480508d07ffa1e1f2941da1ce3a1fc25`
- HEAD message: `Align P9 fixture runner with frozen application service`
- MetadataStore schema: `v6`
- current full-suite authority: 476 passed

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

P9-PRE-001 Public Application Service Foundation is APPROVED / FROZEN.

P9-PRE-001 implementation:
COMPLETE

P9-PRE-001 approved implementation HEAD:

`2ac5d1cf114ffc28c8019440b3e460f60459bc1a`

P9-PRE-001 governance freeze commit:

`6688e8268e04ae270b36ec2736121d648435cc10`

`P9_PREREQUISITE_PUBLIC_APPLICATION_SERVICE_MISSING`:
RESOLVED

Public Application Service prerequisite:
SATISFIED

---

## 1. Current-State Audit

This correction inspected current repository state read-only before modifying
this task specification.

Inspected files and areas:

- `pyproject.toml`
- `src/commerce_lens/application/`
- `src/commerce_lens/application/analysis_service.py`
- current public/in-process application interfaces
- current P1-P8 and P9-PRE-001 production entry points under
  `src/commerce_lens/`
- `src/commerce_lens/fixture_runner/__init__.py`
- `tests/application/test_analysis_service.py`
- `tests/intake/test_csv_adapter.py`
- `tests/intake/test_excel_adapter.py`
- `tests/intake/test_sqlite_adapter.py`
- `tests/canonical/test_canonicalization.py`
- `tests/sufficiency/test_evaluator.py`
- `tests/validation/test_validator.py`
- `tests/evidence/test_admissibility.py`
- `tests/evidence/test_claim_admissibility.py`
- `tasks/P9-PRE-001-public-application-service-foundation.md`
- `PROJECT_STATE.md`

Factual audit findings:

- PyYAML is already present in approved dependencies as `PyYAML>=6,<7`.
- The public application service exists in
  `commerce_lens.application.analysis_service`.
- The public analysis callable is `run_analysis(...)`.
- The public Claim evaluation callable is `evaluate_claim(...)`.
- `src/commerce_lens/application/__init__.py` exports `run_analysis`,
  `evaluate_claim`, `ApplicationServiceError`, and
  `SUPPORTED_APPLICATION_METRICS`.
- `run_analysis(...)` implements the public analysis operation:
  `AnalysisRequest` plus governed source, runtime, and canonicalization context
  produces `AnalysisResult`.
- `evaluate_claim(...)` implements the public Claim evaluation operation:
  caller-supplied complete `ClaimCandidate` produces deterministic P8 evaluation
  and authoritative `ClaimDecision`.
- P9-PRE-001 was independently verified and frozen with a 476-passed full suite.
- The public service has already been independently verified to preserve
  DatasetReference durable authority, request sheet/table authority, multi-Metric
  execution, independent per-chain outcomes, validation authority, Revenue Change
  dependency validation ordering, `ExecutedResult != ValidatedResult`, Evidence
  admissibility boundary, AOV Undefined, authoritative P8 ClaimDecision
  retrieval, cross-request fail-closed behavior, and artifact/provenance
  references.
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
- Existing fixture-runner package state is a placeholder at
  `src/commerce_lens/fixture_runner/__init__.py`; no implemented fixture runner
  exists.

P9 no longer stops on the previously missing public application-service
prerequisite.

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
- `tasks/P9-PRE-001-public-application-service-foundation.md`

P9-PRE-001 Public Application Service Foundation is APPROVED / FROZEN and is
the satisfied public application service prerequisite for P9 planning.

If implementation convenience conflicts with Frozen authority or approved task
authority, implementation must STOP and request Main Project Review.

Do not modify Frozen specifications during P9-001.

---

## 4. Public Application-Service Authority

Frozen Architecture requires the P9 fixture runner to invoke the same public
application service used by the Skill.

Public application module:

`commerce_lens.application.analysis_service`

Public analysis operation:

`run_analysis(...)`

Conceptual public analysis contract:

```text
AnalysisRequest
+ governed source/runtime/canonicalization context
-> AnalysisResult
```

Public Claim evaluation operation:

`evaluate_claim(...)`

Conceptual public Claim evaluation contract:

```text
caller-supplied complete ClaimCandidate
-> deterministic P8 evaluation
-> authoritative ClaimDecision
```

The governing P9 execution path is:

```text
Physical Fixture
-> Declared AnalysisRequest
-> run_analysis(...)
-> AnalysisResult
-> fixture / harness constructs complete structured ClaimCandidate when the case requires Claim evaluation
-> evaluate_claim(...)
-> authoritative ClaimDecision
-> deterministic expected-outcome comparison
```

The future runner must not independently orchestrate production internals by
directly stitching together:

```text
intake
canonicalization
sufficiency
plan
execution
validation
Evidence
```

as a runner-owned alternative application flow.

P9 fixture and harness code may construct the already-declared complete
structured `ClaimCandidate` required by the case manifest. The application
service must not construct material `ClaimCandidate` semantics. P9 case metadata
determines the expected structured Claim intent.

For Claim evaluation cases, use `evaluate_claim(...)`.

For `P9-CONF-CLAIM-DIAGNOSTIC-REFUSAL-001` and
`P9-CONF-TAMPER-CROSS-REQUEST-001`, if implementation needs authentic
`AnalysisResult`, `ValidatedResult`, or `AdmissibleEvidence` authority before
constructing the fixture-declared `ClaimCandidate`, it must use the frozen
public `run_analysis(...)` path or already-authentic persisted authority
produced through that path.

Do not directly stitch private P1-P8 production stages merely as Claim-case
setup convenience. This clarification does not prohibit reading authoritative
refs or artifacts returned by `run_analysis(...)` or `MetadataStore` retrieval
required to construct the complete structured `ClaimCandidate`.

Do not directly treat persistence records as Claim authority.

---

## 5. Critical Scope Rule

Do not physicalize a Frozen Fixture merely because it exists in
`EVALUATION_FIXTURES_SPECIFICATION.md`.

A P9 physical case is eligible only when every material expected behavior that
P9 claims to evaluate is already supported by current P1-P8 and P9-PRE-001
authority.

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
to exercise current authority. The preferred future shape is:

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

The minimum suite must prove the following currently implemented behaviors
through the frozen public application service, except for the one explicitly
authorized hostile validation harness exception.

### A. Supported Positive Chain

At least one case must prove an authentic supported chain reaches:

```text
physical structured input
-> intake
-> canonicalization
-> Data Sufficiency
-> run_analysis(...)
-> AnalysisResult
-> fixture-declared ClaimCandidate
-> evaluate_claim(...)
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

Normal physical analysis cases must use `run_analysis(...)`.

### C. Deterministic Validation Failure

One harness-level case must prove:

```text
ExecutedResult != ValidatedResult
```

The exact validation attack is:

- persist a `revenue_change` `ExecutedResult` with value `21.00` when authentic
  Baseline Revenue is `100.00` and authentic Comparison Revenue is `120.00`,
  recompute that artifact fingerprint, and invoke the existing production
  validator directly.

The exact validation rule is:

- `validation:revenue_change_from_validated_revenues`

The exact validation failure code is:

- `value_mismatch`

The exact failed-chain Metric state is:

- `MetricState.INADMISSIBLE`

The case must produce no authoritative `ValidatedResult`, no
`AdmissibleEvidence`, and no admissible material Claim permission for the failed
chain.

This is the one explicitly authorized lower-level hostile validation harness
exception in the initial P9 inventory. It may invoke the existing deterministic
production validator directly only because correct `run_analysis(...)` execution
must not naturally manufacture an invalid `ExecutedResult`.

This exception:

- is not a second application flow;
- must not duplicate validation logic;
- must not duplicate Revenue Change arithmetic;
- must not be generalized into runner-owned orchestration; and
- must not authorize other cases to bypass `run_analysis(...)`.

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

This case must use `evaluate_claim(...)` and end at authoritative
`ClaimDecision`.

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

This behavior is governed by Approved / Frozen P6/P8/P9-PRE task authority even
though the older Frozen Evaluation Fixture inventory does not contain a directly
matching dedicated physical Fixture ID.

Do not invent a Frozen FX ID for this case.

### F. Revenue Change

Include one physical case proving the current P7/P8/P9-PRE Revenue Change
vertical slice:

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

The runner must consume production authority through `run_analysis(...)` and
`evaluate_claim(...)`. It must not implement Revenue Change arithmetic itself.

### G. Provenance / Tamper Fail-Closed

One harness-level case must demonstrate that substituted authoritative lineage
cannot become authoritative material Claim permission.

The exact attack is:

- create an authentic original Revenue analysis;
- create an authentic foreign Revenue analysis;
- substitute equal-valued foreign Revenue `AdmissibleEvidence` and
  `ValidatedResult` references into a `ClaimCandidate` intended for the original
  authority context; and
- evaluate the substituted candidate through `evaluate_claim(...)`.

The exact expected failure code is:

- `cross_request_substitution`

The exact expected `ClaimDecision` is:

- `ClaimState.INADMISSIBLE`

This case must prove that the frozen public Claim Evaluation operation does not
weaken P8 authority.

Do not build a security framework. Reuse current P8 ClaimDecision authority.

---

## 10. Exact Initial Case Inventory

The initial P9 inventory contains exactly 8 cases. Every case has one exact
material outcome.

| Field | `P9-CONF-POS-001` |
|---|---|
| Case class | Current-authority conformance |
| Frozen Fixture ID | NONE |
| Authority reference | P4/P5/P6/P8/P9-PRE Revenue, Orders, and AOV descriptive chain |
| Case level | physical-input |
| Source input path | `tests/fixtures/p9/cases/P9-CONF-POS-001/input.csv` |
| Public operation | `run_analysis(...)`, then `evaluate_claim(...)` |
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
| Governing authority | P4-001, P5-001, P6-001, P8-001, P9-PRE-001 |

| Field | `P9-CONF-REVCHG-001` |
|---|---|
| Case class | Current-authority conformance |
| Frozen Fixture ID | NONE |
| Authority reference | P7/P8/P9-PRE Revenue Change descriptive authority |
| Case level | physical-input |
| Source input path | `tests/fixtures/p9/cases/P9-CONF-REVCHG-001/input.csv` |
| Public operation | `run_analysis(...)`, then `evaluate_claim(...)` |
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
| Governing authority | P7-001, P8-001, P9-PRE-001 |

| Field | `P9-CONF-SUFF-MISSING-REVENUE-001` |
|---|---|
| Case class | Current-authority conformance |
| Frozen Fixture ID | NONE |
| Authority reference | Frozen `FX-SUFF-003` semantic reference without Frozen ID claim; Phase 2/P3/P9-PRE fail-closed authority |
| Case level | physical-input |
| Source input path | `tests/fixtures/p9/cases/P9-CONF-SUFF-MISSING-REVENUE-001/input.csv` |
| Public operation | `run_analysis(...)` |
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
| Governing authority | Canonical Dataset and Metric Dictionary, Phase 2, P3-001, P9-PRE-001 |

| Field | `P9-CONF-SUFF-MIXED-CURRENCY-001` |
|---|---|
| Case class | Current-authority conformance |
| Frozen Fixture ID | NONE |
| Authority reference | Frozen `FX-SUFF-001` mixed-currency semantic reference without Frozen ID claim; Phase 2/P3/P9-PRE fail-closed authority |
| Case level | physical-input |
| Source input path | `tests/fixtures/p9/cases/P9-CONF-SUFF-MIXED-CURRENCY-001/input.csv` |
| Public operation | `run_analysis(...)` |
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
| Governing authority | Canonical Dataset and Metric Dictionary, Phase 2, P3-001, P9-PRE-001 |

| Field | `P9-CONF-AOV-UNDEFINED-001` |
|---|---|
| Case class | Current-authority conformance |
| Frozen Fixture ID | NONE |
| Authority reference | P6/P8/P9-PRE AOV Undefined authority |
| Case level | physical-input |
| Source input path | `tests/fixtures/p9/cases/P9-CONF-AOV-UNDEFINED-001/input.csv` |
| Public operation | `run_analysis(...)`, then `evaluate_claim(...)` |
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
| Governing authority | P6-001, P8-001, P9-PRE-001 |

| Field | `P9-CONF-VAL-REVCHG-WRONG-VALUE-001` |
|---|---|
| Case class | Current-authority conformance |
| Frozen Fixture ID | NONE |
| Authority reference | P5/P7 Revenue Change validation authority |
| Case level | harness-level |
| Source input path | NONE |
| Public operation | ONE hostile direct-validator harness exception |
| Metrics | `revenue_change` |
| Analytical request class | `validate_total_revenue_change_baseline_to_comparison` |
| Expected Data Sufficiency state | `SufficiencyState.SUFFICIENT` |
| Expected execution disposition | hostile submitted ExecutedResult exists with value `21.00` |
| Expected deterministic value / state | authoritative expected Revenue Change `20.00`; submitted value `21.00`; failed-chain `MetricState.INADMISSIBLE` |
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
| Authority reference | P8/P9-PRE unsupported stronger Claim authority |
| Case level | harness-level |
| Source input path | NONE |
| Public operation | `evaluate_claim(...)` |
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
| Governing authority | P8-001, P9-PRE-001 |

| Field | `P9-CONF-TAMPER-CROSS-REQUEST-001` |
|---|---|
| Case class | Current-authority conformance |
| Frozen Fixture ID | NONE |
| Authority reference | P8/P9-PRE cross-request substitution authority |
| Case level | harness-level |
| Source input path | NONE |
| Public operation | `evaluate_claim(...)` |
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
| Governing authority | P8-001, P9-PRE-001 |

---

## 11. Frozen Fixture Compatibility Matrix

This planning matrix establishes how P9 distinguishes full Frozen Fixture
physicalization from implementation-level conformance cases. It is not a full
40-family fixture plan.

| Class | Examples | P9 treatment |
|---|---|---|
| PHYSICALIZE NOW | NONE | P9-001 initial inventory intentionally uses current-authority P9 conformance cases only; no Frozen Fixture ID is claimed as fully physicalized in this initial P9 suite |
| CURRENT-AUTHORITY CONFORMANCE CASE | `P9-CONF-POS-001`; `P9-CONF-REVCHG-001`; `P9-CONF-SUFF-MISSING-REVENUE-001`; `P9-CONF-SUFF-MIXED-CURRENCY-001`; `P9-CONF-AOV-UNDEFINED-001`; `P9-CONF-VAL-REVCHG-WRONG-VALUE-001`; `P9-CONF-CLAIM-DIAGNOSTIC-REFUSAL-001`; `P9-CONF-TAMPER-CROSS-REQUEST-001` | Use stable P9 conformance IDs; cite Frozen semantic references as supporting authority without claiming the Frozen Fixture ID itself |
| DEFER | `FX-VALID-001` complete canonical workflow; `FX-SUFF-003`; `FX-SUFF-001`; `FX-DQ-002`; `FX-SUFF-004`; `FX-METRIC-001` when evaluating Revenue Change %; `FX-CLAIM-002`; `FX-CLAIM-003`; `FX-CLAIM-004`; contribution, ranking, product/category, Finding, Alternative Explanation, Recommendation, positive Qualified Admissible fixtures | Defer Frozen Fixture ID physicalization until a separate Main Project decision re-establishes every material variant-level expected outcome for each selected Frozen Fixture |

The full Frozen fixture suite is not required for P9.

---

## 12. Authorized Implementation File Scope

Implementation completed the fixture-runner package:

- `src/commerce_lens/fixture_runner/__init__.py`

The approved implementation also added the scoped helper modules, fixtures, and
focused tests listed below.

Production/evaluation helper files authorized for P9 implementation:

- `src/commerce_lens/fixture_runner/__init__.py`
- `src/commerce_lens/fixture_runner/cases.py`
- `src/commerce_lens/fixture_runner/runner.py`
- `src/commerce_lens/fixture_runner/hostile_validation.py`
- `tests/fixtures/p9/cases/<case-id>/input.csv`
- `tests/fixtures/p9/cases/<case-id>/manifest.yaml`

Focused test files authorized for P9 implementation:

- `tests/fixture_runner/test_cases.py`
- `tests/fixture_runner/test_runner.py`
- `tests/fixture_runner/test_hostile_validation.py`

No other production file is pre-authorized.

Expected conceptual needs are only:

- manifest/case contract loading;
- safe YAML parsing;
- case discovery;
- physical-input invocation through `run_analysis(...)`;
- Claim invocation through `evaluate_claim(...)`;
- the one exact hostile validation harness exception;
- deterministic expected-vs-actual comparison; and
- per-case PASS/FAIL.

Do not introduce a generic framework.

P9 implementation created only the authorized implementation files, fixture
assets, and focused tests listed above.

---

## 13. Runner Responsibility

The P9 runner must be thin and must invoke the public application service
for normal analysis and Claim paths.

It may:

- discover the exact eight manifests;
- safe-load `manifest.yaml`;
- load tiny CSV inputs;
- build or use the already-declared structured `AnalysisRequest` and
  canonicalization context from deterministic manifest mappings;
- call `run_analysis(...)`;
- construct only the complete structured `ClaimCandidate` declared by the case
  when Claim evaluation is required;
- call `evaluate_claim(...)`;
- perform the exact authorized hostile validation harness case;
- compare governed structured actual state against exact expected state; and
- emit per-case PASS/FAIL with structured mismatch detail.

It must not:

- calculate Metrics;
- recalculate expected Revenue Change from production output;
- repair production output;
- create Evidence;
- decide Claim admissibility;
- infer analytical intent;
- use natural-language judgment;
- dynamically rewrite snapshots;
- select among alternate expected outcomes;
- score cases; or
- aggregate benchmark scores.

Expected numeric fixture values must be manifest authority derived during task
definition from fixed synthetic input semantics. They must not be recomputed by
runner logic as an alternate formula engine.

Expected values and expected states in `manifest.yaml` are fixed fixture
authority. The runner compares actual governed output against manifest expected
output. It must not independently calculate expected `revenue`, `orders`, `aov`,
or `revenue_change` from production results, and in particular it must not
compute Revenue Change as an alternate formula engine.

Fixture CSV rows and manifest expected values are deliberately authored together
during implementation from the approved task semantics. At runtime, expected
values are loaded from manifest authority and are not regenerated by analytical
formulas.

The production engine remains authoritative through the public application
service. The runner is an evaluator, not a second analytics implementation.

Physical Fixture Runner is not the Decision Reliability Benchmark.

---

## 14. Public v0.1 Relationship

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

## 15. Test Strategy

P9 implementation tests cover:

- safe YAML manifest/case schema validation;
- case discovery;
- independent case execution through `run_analysis(...)`;
- Claim evaluation through `evaluate_claim(...)`;
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
- hard failure if the frozen public application service operations become
  unavailable or materially diverge from P9-PRE authority.

Do not duplicate every P1-P8 unit test. P9 tests must focus on integrated
physical behavior and runner contract behavior.

---

## 16. Acceptance Criteria

P9-001 implementation is successful only if:

1. P9-PRE-001 remains APPROVED / FROZEN;
2. `run_analysis(...)` is used for normal physical analysis paths;
3. `evaluate_claim(...)` is used for Claim evaluation paths;
4. only `P9-CONF-VAL-REVCHG-WRONG-VALUE-001` receives the narrow direct-validator
   hostile harness exception;
5. all eight exact cases pass;
6. every case is synthetic and public-safe;
7. every case has one deterministic expected outcome;
8. every manifest uses YAML metadata loaded safely;
9. every semantic physical fixture input uses tiny CSV;
10. the runner invokes the public application service rather than duplicating
    Metric logic or stitching private internals;
11. a supported positive chain reaches authoritative `ClaimDecision`;
12. insufficiency fails closed;
13. deterministic validation failure remains distinct from execution failure;
14. AOV Undefined remains Undefined and not zero;
15. an unsupported diagnostic Claim becomes `Inadmissible`;
16. Revenue Change reaches authoritative descriptive `ClaimDecision`;
17. cross-request substituted provenance cannot create authoritative Claim
    permission;
18. cases are isolated and order-independent;
19. no scoring or benchmark productization exists;
20. no future Metric, Finding, Alternative Explanation, Recommendation, or
    positive Qualified Admissible behavior is introduced;
21. MetadataStore schema remains `v6`;
22. no new dependency is added;
23. no Frozen file is modified;
24. no P1-P8 or P9-PRE task semantics are reopened; and
25. the full repository regression suite passes.

---

## 17. Protected Boundaries

P9 implementation did not modify:

- `docs/frozen/`;
- Metric formulas;
- canonical semantics;
- P1-P8 Approved / Frozen task semantics;
- P9-PRE-001 Approved / Frozen application-service semantics;
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

## 18. Stop Conditions

Implementation must STOP if:

- P9-PRE-001 is no longer APPROVED / FROZEN;
- the frozen public application service becomes unavailable;
- `run_analysis(...)` is no longer exposed;
- `evaluate_claim(...)` is no longer exposed;
- the public application service cannot execute the approved required P9 paths;
- the public application service materially diverges from the frozen P9-PRE
  boundary;
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

## 19. Freeze Boundary

This governance integration records approval and freeze of P9-001 within the
exact scope of this task.

This freeze does not authorize:

- creating additional fixture directories;
- creating additional physical CSV/YAML fixture assets;
- expanding the fixture runner;
- writing another public application service;
- modifying production analytical semantics;
- modifying tests beyond the approved P9 implementation commits;
- modifying Frozen specifications;
- modifying `PROJECT_STATE.md` beyond this governance integration;
- modifying the roadmap;
- modifying `README.md`;
- modifying dependencies;
- creating CLI;
- creating `SKILL.md`;
- creating an implementation branch;
- beginning Public v0.1 Integration;
- beginning the Public v0.1 Integration Gate;
- creating benchmark scoring; or
- pushing commits.

P9 is frozen at approved implementation HEAD
`ba72e2b658b854b0e45ba51a3273f9e4e5a593bd`.

---

## 20. Self-Review Checklist

Main Project Review verified before implementation authorization:

- P9-PRE-001 is recorded as APPROVED / FROZEN;
- the public application service prerequisite is recorded as RESOLVED /
  SATISFIED;
- public analysis uses `run_analysis(...)`;
- public Claim evaluation uses `evaluate_claim(...)`;
- normal physical cases use `run_analysis(...)`;
- Claim cases use `evaluate_claim(...)`;
- exactly one hostile direct-validator exception exists;
- the hostile validation case is `P9-CONF-VAL-REVCHG-WRONG-VALUE-001`;
- the cross-request tamper case uses `evaluate_claim(...)`;
- primary metadata format is YAML, not JSON;
- tiny CSV remains the primary semantic fixture input;
- no new dependency was added;
- current PyYAML status is factual;
- exact case inventory contains no conditional case selection;
- every case has one exact material outcome;
- no outcome contains multiple acceptable alternatives;
- Frozen FX IDs are not used in the initial P9 inventory;
- AOV Undefined uses a P9 current-authority identity;
- tamper case has one exact attack and failure result;
- Claim refusal has one exact unsupported Claim type;
- validation failure has one exact validator/failure;
- adapter release prerequisite status is recorded;
- approved implementation file scope is recorded;
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
