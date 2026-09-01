# P9-001 - Minimum Physical Fixture Runner

## Status

PROPOSED / NOT AUTHORIZED

Implementation:
NOT STARTED

Main Project Review:
REQUIRED BEFORE IMPLEMENTATION

This task is task creation only. It does not authorize implementation.

P9-001 must not be implemented until a separate Main Project Review approves
this specification and explicitly authorizes implementation.

Current required baseline:

- branch: `main`
- starting HEAD: `6117b07303daa60f06a8786dc58a8fee62494861`
- starting HEAD message: `Accelerate roadmap toward public v0.1 Skill`
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

## 1. Purpose

P9-001 defines the smallest physical fixture runner that converts a deliberately
small, currently executable subset of the Frozen Evaluation Fixture Specification
and current P1-P8 conformance cases into reproducible physical evaluation assets.

The purpose is to prove that the implemented CommerceLens reliability chain can
be exercised against physical structured inputs and deterministic expected
outcomes.

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
- a synthetic data generator framework; or
- the Public v0.1 Integration Gate.

P9-001 is the final deterministic behavioral proof layer immediately before the
approved Public v0.1 Integration Gate, but it does not begin that gate.

---

## 2. Governing Authority

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

## 3. Critical Scope Rule

Do not physicalize a Frozen Fixture merely because it exists in
`EVALUATION_FIXTURES_SPECIFICATION.md`.

A P9 physical case is eligible only when every material expected behavior that
P9 claims to evaluate is already supported by current P1-P8 authority.

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
either:

1. exclude it from P9; or
2. define a clearly non-authoritative implementation conformance case that
   references the governing semantic but does not falsely claim full conformance
   to the Frozen Fixture ID.

Do not invent new Frozen Fixture IDs.

---

## 4. Authorized Physical Asset Shape

P9-001 may introduce the smallest repository-local physical asset layout needed
to exercise current authority. The preferred future shape is:

```text
tests/
  fixtures/
    p9/
      cases/
        <case-id>/
          input.csv
          manifest.json
```

An equivalent small layout under an existing test fixture convention is
acceptable if repository inspection during implementation shows a better current
pattern.

Physical assets must be:

- small synthetic structured input files;
- public-safe;
- deterministic;
- isolated;
- independently runnable;
- order-independent;
- reproducible from a clean checkout; and
- free of external network dependencies.

CSV should be the default first physical source format unless implementation
inspection proves another existing path is materially smaller and more
consistent. JSON is acceptable for fixture metadata because it requires no new
runtime dependency.

Do not require:

- SQLite fixture databases;
- XLSX fixture generation;
- physical customer, production, private, or scraped proprietary data;
- a new runtime dependency; or
- MetadataStore schema v7.

Existing intake unit tests may continue to cover format-specific CSV, XLSX, and
SQLite inspection behavior. P9 is about integrated physical behavioral
conformance, not duplicating every intake-format test.

Expected MetadataStore schema remains `v6`.

---

## 5. Physical Case Contract

Every P9 physical or harness-level conformance case must bind the following
machine-readable fields:

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
- expected deterministic result or governed Metric state where applicable;
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

- PASS or PASS WITH QUALIFICATION;
- one of several failure codes;
- `if material`;
- `as applicable`;
- fuzzy numerical tolerances that replace governed Decimal semantics; or
- dynamic snapshot rewriting.

---

## 6. Minimum Behavioral Coverage

The approved P9 implementation must target approximately 6-8 cases total. It
must not exceed 10 physical/conformance cases without a documented Main Project
reason.

The minimum suite must prove the following currently implemented behaviors.

### A. Supported Positive Chain

At least one case must prove an authentic supported chain reaches:

```text
physical structured input
-> intake
-> canonicalization
-> Data Sufficiency
-> ExecutionPlan
-> deterministic execution
-> deterministic validation
-> AdmissibleEvidence
-> ClaimCandidate
-> authoritative Admissible ClaimDecision
```

This positive chain may use Revenue, Orders, numeric AOV, Revenue Change, or a
minimal combination of those Metrics. It must use only currently governed Metrics
and `ClaimType.DESCRIPTIVE`.

Do not require Revenue Change Percentage.

### B. Data Sufficiency Fail-Closed

At least one physical case must prove materially missing or invalid Required
Evidence causes the affected chain to stop without fabricated result.

Preferred currently executable semantics include:

- missing `line_revenue`;
- invalid or mixed currency;
- incomplete comparison period; or
- unresolved duplicate identity.

The selected case must be fully supported by current implementation. Required
outcome must preserve:

```text
Insufficient evidence to conclude.
```

### C. Deterministic Validation Failure

At least one case must prove:

```text
ExecutedResult != ValidatedResult
```

and that a deterministic validation failure cannot produce `AdmissibleEvidence`
or an admissible material Claim.

Use an already implemented P5/P6 validation behavior. Do not invent a new
validator. If production execution cannot naturally produce the invalid
candidate, the implementation may use a harness-level case that persists or
substitutes an intentionally invalid `ExecutedResult` artifact and then invokes
the existing production validator and evidence APIs.

### D. Claim Refusal

At least one P8 conformance case must prove that authentic descriptive Evidence
cannot authorize an unsupported stronger Claim.

The minimum public-v0.1-oriented scenario is:

- Revenue decline is supported descriptively; and
- a Claim about why Revenue declined is rejected because current Evidence does
  not support diagnostic, causal, predictive, or prescriptive authority.

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

This behavior is governed by Approved / Frozen P6/P8 task authority even if the
older Frozen Evaluation Fixture inventory does not contain a directly matching
dedicated physical Fixture ID.

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

The runner must consume production authority. It must not implement Revenue
Change arithmetic itself.

### G. Provenance / Tamper Fail-Closed

At least one runner-level or harness-level case must demonstrate that a
tampered/substituted authoritative artifact or lineage cannot become an
authoritative material Claim.

Do not build a security framework. Reuse current P6-P8 artifact verification,
lineage, and ClaimDecision APIs.

---

## 7. Initial Case Plan

The following case plan is intentionally small. Final implementation may adjust
case IDs and exact row values during Main Project-approved implementation, but it
must preserve the coverage and boundary rules above.

| Case ID | Class | Frozen Fixture ID | Purpose | Metrics | Expected final disposition |
|---|---|---:|---|---|---|
| `P9-CONF-POS-001` | Current-authority conformance | None | Physical positive same-period chain through descriptive ClaimDecision | `revenue`, `orders`, `aov` | Admissible descriptive ClaimDecision |
| `P9-CONF-REVCHG-001` | Current-authority conformance | None | Physical Revenue Change vertical slice with authentic period Revenue dependencies | `revenue_change` | Admissible descriptive ClaimDecision |
| `P9-FX-SUFF-003-001` | Physicalize now if implementation confirms full current support | `FX-SUFF-003` | Missing `line_revenue` fails Data Sufficiency closed | `revenue` | Insufficient evidence to conclude |
| `P9-FX-SUFF-001A-001` | Physicalize now if implementation confirms full current support | `FX-SUFF-001` variant A | Mixed unnormalized currency fails closed without conversion | `revenue` or `revenue_change` | Insufficient evidence to conclude |
| `P9-CONF-VAL-AOV-001` | Harness-level current-authority conformance | None | Existing AOV validation rejects wrong executed value/formula | `aov` | Validation failure, no AdmissibleEvidence, no admissible Claim |
| `P9-CONF-CLAIM-REFUSAL-001` | Current-authority conformance | None | Descriptive Revenue decline evidence cannot authorize why/diagnostic Claim | `revenue_change` or `revenue` | Inadmissible ClaimDecision |
| `P9-CONF-AOV-UNDEFINED-001` | Current-authority conformance | None | Orders zero makes AOV Undefined with `orders_equals_zero`, not numeric zero | `orders`, `aov` | Admissible descriptive metric-state ClaimDecision |
| `P9-CONF-TAMPER-001` | Runner/harness-level current-authority conformance | None | Tampered or substituted lineage fails closed before material Claim permission | Any current governed Metric | Inadmissible ClaimDecision or fail-closed verification outcome |

The implementation must not treat this table as authorization to overclaim full
Frozen Fixture conformance. For each Frozen Fixture row, implementation must
first prove every material expected behavior for the selected fixture variant is
currently executable without omitting unimplemented scope.

---

## 8. Frozen Fixture Compatibility Matrix

This planning matrix establishes how P9 distinguishes full Frozen Fixture
physicalization from implementation-level conformance cases. It is not a full
40-family fixture plan.

| Class | Examples | P9 treatment |
|---|---|---|
| PHYSICALIZE NOW | `FX-SUFF-003 Missing Revenue Input`; `FX-SUFF-001` mixed-currency variant; possibly `FX-DQ-002 Exact Duplicate Identity` or `FX-SUFF-004 Incomplete Period` if implementation inspection confirms full current support | May use the Frozen Fixture ID only when the complete material expected outcome is executable with P1-P8 authority |
| CURRENT-AUTHORITY CONFORMANCE CASE | supported physical positive descriptive chain; Revenue Change descriptive ClaimDecision; AOV Undefined because Orders = 0; descriptive Evidence refusing diagnostic/causal/predictive/prescriptive Claim; P6-P8 tamper/substitution fail-closed cases | Use stable P9 conformance IDs; do not invent or reuse Frozen FX IDs |
| DEFER | `FX-VALID-001` complete canonical workflow; `FX-METRIC-001` when evaluating Revenue Change %; `FX-CLAIM-002`; `FX-CLAIM-003`; `FX-CLAIM-004`; contribution, ranking, product/category, Finding, Alternative Explanation, Recommendation, or positive Qualified Admissible fixtures | Do not physicalize in P9 unless a later Main Project-approved task implements the missing authority |

The full Frozen fixture suite is not required for P9.

---

## 9. Runner Responsibility

The future P9 runner must be thin.

It may:

- discover approved P9 case manifests;
- load physical fixture data;
- invoke existing production CommerceLens interfaces;
- collect deterministic artifacts and results;
- compare actual material outputs against expected contracts;
- emit deterministic per-case PASS/FAIL; and
- emit failure detail useful for review.

It must not:

- calculate Metrics independently;
- reproduce Metric formulas;
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

The production engine remains authoritative. The runner is an evaluator, not a
second analytics implementation.

Physical Fixture Runner is not the Decision Reliability Benchmark.

---

## 10. Public v0.1 Relationship

P9-001 must make it possible for the later Public v0.1 Integration Gate to
demonstrate:

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

## 11. Test Strategy

Future P9 implementation tests must cover at least:

- manifest/case schema validation;
- case discovery;
- independent case execution;
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
- runner behavior without duplicating Metric formulas; and
- rejection of benchmark scoring output.

Do not duplicate every P1-P8 unit test. P9 tests must focus on integrated
physical behavior and runner contract behavior.

---

## 12. Acceptance Criteria

P9-001 implementation is successful only if:

1. the approved minimum physical/conformance suite exists;
2. every case is synthetic and public-safe;
3. every case has one deterministic expected outcome;
4. the runner invokes production CommerceLens authority rather than duplicating
   Metric logic;
5. a supported positive chain reaches authoritative `ClaimDecision`;
6. insufficiency fails closed;
7. deterministic validation failure remains distinct from execution failure;
8. AOV Undefined remains Undefined and not zero;
9. an unsupported stronger Claim becomes `Inadmissible`;
10. Revenue Change reaches authoritative descriptive `ClaimDecision`;
11. tampered/substituted provenance cannot create authoritative Claim
    permission;
12. cases are isolated and order-independent;
13. no scoring or benchmark productization exists;
14. no future Metric, Finding, Alternative Explanation, Recommendation, or
    positive Qualified Admissible behavior is introduced;
15. MetadataStore schema remains `v6`;
16. no new dependency is added unless a Main Project STOP review authorizes it;
17. no Frozen file is modified;
18. no P1-P8 task semantics are reopened; and
19. the full repository regression suite passes.

---

## 13. Protected Boundaries

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

## 14. Stop Conditions

Implementation must STOP if:

- a selected Frozen Fixture cannot be fully represented without omitting a
  material expected behavior;
- a physical case would require inventing new analytical semantics;
- the runner needs to duplicate Metric formulas;
- the runner needs LLM judgment;
- current production interfaces cannot execute a required P9 case without
  architecture redesign;
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

## 15. Non-Authorization

This task specification does not authorize:

- creating fixture directories;
- creating physical CSV/JSON fixture assets;
- writing a fixture runner;
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

After this task specification is created and committed, STOP.

---

## 16. Self-Review Checklist

Before implementation authorization, Main Project Review must verify:

- P9 is minimum physical proof, not full benchmark;
- no requirement says all 40 Frozen fixture families must be implemented;
- no unimplemented Metric is required;
- no Frozen Fixture ID is reused for a materially partial outcome;
- AOV Undefined is represented through current authority without inventing a
  Frozen FX ID;
- supported Claim permission is descriptive only;
- no positive Qualified Admissible path is invented;
- Revenue Change formula is not duplicated;
- the runner is thin;
- expected outcomes are deterministic;
- physical cases are synthetic/public-safe;
- P9 ends before Skill integration; and
- Public v0.1 Integration Gate remains next after P9.
