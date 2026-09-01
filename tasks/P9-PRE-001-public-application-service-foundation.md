# P9-PRE-001 - Public Application Service Foundation

## Status

PROPOSED / NOT AUTHORIZED

Implementation:
NOT STARTED

Relationship:
BLOCKING PREREQUISITE FOR P9-001

This task is task specification only. It does not authorize implementation.

P9-001 must not be implemented until this prerequisite is separately specified,
reviewed, implemented, verified, and approved by Main Project Review.

This task is not:

- a new roadmap phase;
- P10;
- Public v0.1 Integration;
- Skill implementation;
- CLI implementation; or
- fixture runner implementation.

Do not modify Frozen specifications, `PROJECT_STATE.md`, roadmap, `README.md`,
production code, tests, dependencies, physical fixtures, fixture runner code,
CLI code, or `SKILL.md` under this task-creation scope.

---

## 1. Objective

P9-PRE-001 defines the smallest in-process public application service that
orchestrates already-approved P1-P8 capabilities through one production entry
point.

The purpose is not to add analytical functionality.

The purpose is to turn existing deterministic components into one governed
application-level operation suitable for:

1. the P9 physical fixture runner;
2. later CommerceLens Skill integration; and
3. later thin CLI adaptation.

This prerequisite clears only the missing public application-service foundation.
It does not authorize P9 implementation or Public v0.1 Integration.

---

## 2. Current Approved Reliability Authority

Current approved reliability authority already exists through:

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

P9-PRE-001 must orchestrate this authority.

It must not redefine, duplicate, bypass, or weaken this authority.

Current governed Metrics:

- `revenue`
- `orders`
- `aov`
- `revenue_change`

Current positive Claim permission:

- `ClaimType.DESCRIPTIVE` only

Preserve:

- AOV Undefined when Orders = 0;
- Revenue Change authority;
- descriptive ClaimDecision authority; and
- unsupported diagnostic, predictive, causal, and prescriptive Claims fail
  closed.

Do not add:

- `revenue_change_pct`;
- product/category Metrics;
- contribution;
- ranking;
- Findings;
- Alternative Explanations;
- Recommendations; or
- Qualified Admissible positive paths.

---

## 3. Governing Architecture Requirement

The Frozen Architecture requires the fixture runner to use the same public
application service used by the future Skill.

Required conceptual boundary:

```text
Physical Fixture
-> Declared AnalysisRequest
-> Public Engine Application Service
-> deterministic governed pipeline
-> structured application result
-> fixture comparison
```

The application service must also be suitable for later invocation by the
CommerceLens Skill.

It must not create separate analytical semantics for fixtures.

The P9 fixture runner must not call low-level production modules directly as a
substitute for the public application service.

---

## 4. Current Service Status

Current public application service exists:
NO

Current `src/commerce_lens/application/__init__.py` status:
placeholder only; no public application service callable.

Current `AnalysisResult` status:
`src/commerce_lens/contracts/results.py` defines `AnalysisResult`, but no
current public application service constructs it across the required P1-P8 path.

Blocking prerequisite:

`P9_PREREQUISITE_PUBLIC_APPLICATION_SERVICE_MISSING`

P9-001 remains blocked until this prerequisite is implemented, verified, and
approved.

---

## 5. Public Application-Service Boundary

Future implementation must define one obvious production application-level
callable.

The exact Python name may be selected during implementation after repository
inspection.

Frozen Architecture conceptually expects:

`src/commerce_lens/application/`

Prefer the smallest location consistent with the existing package structure.

Possible future conceptual file:

`src/commerce_lens/application/analysis_service.py`

Do not create multiple services or orchestration frameworks.

Conceptually, the callable must accept:

- a validated governed `AnalysisRequest`;
- explicit source/input reference required by the current intake path;
- explicit authorized mapping/canonicalization inputs where existing contracts
  require them; and
- local runtime/persistence context required to execute reproducibly.

It must not accept free-form prose as executable authority.

User prose may exist only as non-authoritative audit/context metadata if already
supported by existing contracts.

The service must return one structured application-level result representing the
material state of the requested governed analysis.

Prefer reuse of the existing `AnalysisResult` contract if it is sufficient.

If the current `AnalysisResult` contract is incomplete for this service, the
future implementation review must document the exact deficiency.

Do not silently redesign result contracts unless the implementation task
explicitly authorizes the minimum required change.

---

## 6. Required Orchestration Responsibility

For eligible current requests, the service must orchestrate existing production
authority rather than reimplement it.

Conceptual path:

```text
input/source
-> existing intake
-> existing registration / immutable source authority
-> existing canonicalization
-> existing Data Quality / Data Sufficiency
-> existing ExecutionPlan builder
-> existing deterministic execution
-> existing deterministic validation
-> existing Evidence admissibility
-> persist ClaimCandidate
-> existing deterministic Claim admissibility evaluator
-> authoritative ClaimDecision
-> structured application result
```

The application service must not perform:

- Metric arithmetic;
- independent SQL formulas;
- evidence reconstruction;
- validation logic;
- Claim permission logic; or
- natural-language intent interpretation.

The application service orchestrates existing authorities.

---

## 7. No Semantic Duplication

Future implementation must not duplicate:

- Revenue formula;
- Orders formula;
- AOV formula;
- Revenue Change formula;
- population construction rules;
- validation rules;
- Data Sufficiency rules;
- Evidence admissibility rules; or
- Claim admissibility rules.

The service must call existing production modules.

---

## 8. Request And Claim Input Responsibility

The application service is not an LLM intent interpreter.

For P9 and deterministic programmatic callers, inputs must already provide the
governed structured request.

For Claim evaluation, the caller must provide a structured `ClaimCandidate` or
enough explicit governed structured fields for the application layer to
construct one without interpreting arbitrary prose.

Do not let the application service infer:

- Metric selection from natural language;
- period meaning from prose;
- diagnostic or causal intent from prose;
- mappings from vague column names; or
- missing business semantics.

Those responsibilities remain Skill or future integration concerns.

---

## 9. Claim Authority

The service must preserve the P8 boundary:

```text
ClaimCandidate != ClaimDecision
```

and:

```text
persisted ClaimDecision record != authoritative Claim permission
```

For Admissible decisions, downstream application output must use the
authoritative P8 retrieval/verification path.

Do not expose raw persistence-only Admissible `ClaimDecision` records as
application authority.

Do not duplicate the P8 policy.

---

## 10. Failure Propagation

Future implementation must define deterministic application behavior for the
current implemented failure classes needed by P9.

### A. Data Sufficiency Failure

Required behavior:

- do not execute the blocked Metric chain;
- do not fabricate an `ExecutedResult`;
- do not create `AdmissibleEvidence`;
- do not create an admissible material Claim; and
- keep structured blocker/failure information observable.

### B. Execution Failure

Execution failure must remain distinct from validation failure.

### C. Validation Failure

An `ExecutedResult` may exist.

A `ValidatedResult` for the failed intended use must not be created.

No `AdmissibleEvidence` or admissible material Claim may arise from that failed
chain.

### D. Undefined Metric

AOV with Orders = 0 remains a governed Undefined state.

```text
Undefined != failure != numeric zero
```

### E. Inadmissible Claim

An authentic descriptive Evidence chain may exist while the stronger diagnostic,
predictive, causal, or prescriptive `ClaimDecision` is Inadmissible.

These domains must not be collapsed.

---

## 11. Result Contract

Future implementation must determine the minimum application-level structured
result required for P9 and later Skill integration.

It must make the following distinguishable where applicable:

- request identity;
- dataset and canonical dataset authority refs;
- Data Sufficiency state;
- execution state;
- Metric state;
- deterministic result refs;
- validation state;
- `AdmissibleEvidence` refs;
- `ClaimCandidate` ref;
- authoritative `ClaimDecision`;
- failure code/details;
- Undefined reason; and
- provenance/artifact references necessary for traceability.

Do not create user-facing prose rendering.

Do not create Finding or Recommendation fields merely for future use.

Do not add confidence scores.

Do not add benchmark fixture state into the production application result unless
the Frozen Architecture explicitly requires a generic field already.

Fixture PASS/FAIL belongs to the fixture runner, not the application service.

---

## 12. Multi-Metric And Partial Completion Boundary

Before implementation authorization, inspect current P1-P8 interfaces and
determine whether the smallest correct service should:

1. execute one governed Metric chain per invocation; or
2. support the existing `AnalysisRequest` multi-Metric structure.

Do not invent a new batching model.

Prefer the model already implied and supported by existing request and plan
contracts.

If current interfaces cannot produce one coherent application result without
substantial architecture work, stop and request Main Project Review.

Do not solve this by creating a generic workflow framework.

---

## 13. Reproducibility

The same governed request and same immutable source/canonical authority must
produce materially equivalent analytical semantics across repeated runs.

Event IDs and timestamps may differ where current contracts intentionally model
events.

Semantic authority must remain reproducible through existing fingerprints and
persisted lineage.

The application service must not introduce hidden global state.

---

## 14. Local-First Boundary

The service remains:

- local;
- in-process;
- deterministic for material analytical operations; and
- network-free.

Do not create:

- HTTP API;
- local web server;
- REST layer;
- RPC;
- queue;
- message bus; or
- background worker.

---

## 15. CLI Boundary

Do not implement or require CLI in P9-PRE-001.

Frozen Architecture permits a thin CLI over the same application service, but
P9 currently requires only the production in-process application service needed
by the fixture runner.

CLI remains a later thin adapter unless Main Project separately authorizes it.

The application service design must not prevent a future CLI adapter.

---

## 16. Public v0.1 Relationship

This prerequisite is reusable by:

1. P9 physical fixture runner;
2. later CommerceLens Skill integration; and
3. later thin CLI.

This task does not implement:

- Skill;
- `SKILL.md`;
- host adapter;
- user-facing renderer;
- CLI;
- Public v0.1 release; or
- GitHub packaging.

This is application orchestration only.

---

## 17. Expected Test Strategy For Future Implementation

The future implementation task should require tests for at least:

1. positive Revenue request through application service;
2. Orders;
3. numeric AOV;
4. AOV Undefined when Orders = 0;
5. Revenue Change;
6. insufficiency stops before execution;
7. validation failure cannot become Evidence;
8. descriptive Claim reaches authoritative Admissible `ClaimDecision`;
9. diagnostic Claim becomes Inadmissible;
10. cross-request or forged authority cannot bypass Claim permission;
11. repeated invocation preserves material semantics;
12. application service does not mutate input source;
13. no network dependency; and
14. full P1-P8 regression remains passing.

Do not duplicate all lower-level tests.

Tests should prove orchestration integration.

---

## 18. Protected Boundaries

Future implementation must not change without separate Main Project Review:

- Frozen specs;
- Metric formulas;
- canonical semantics;
- Data Sufficiency semantics;
- P5 validation semantics;
- P6 Evidence semantics;
- P7 Revenue Change semantics;
- P8 ClaimDecision semantics;
- MetadataStore schema;
- dependencies;
- roadmap;
- `README.md`; or
- `SKILL.md`.

Expected MetadataStore schema:

`v6`

Expected new dependencies:

NONE

If implementation believes schema v7 or a new dependency is required, stop and
request Main Project Review.

---

## 19. P9 Dependency Exit Condition

`P9_PREREQUISITE_PUBLIC_APPLICATION_SERVICE_MISSING` is cleared only when:

- one production in-process public application service exists;
- it invokes current production P1-P8 authority;
- supported current Metric chains work through that service;
- failure, Undefined, and Claim states remain structurally distinct;
- authoritative ClaimDecision retrieval is preserved;
- no duplicated analytical semantics exist;
- targeted integration tests pass;
- full repository regression passes; and
- Main Project independently reviews and approves the implementation.

Only after this prerequisite is APPROVED / FROZEN may P9-001 be authorized.

---

## 20. Task-Creation Scope

During task creation, modify only:

`tasks/P9-PRE-001-public-application-service-foundation.md`

Do not modify:

- `tasks/P9-001-minimum-physical-fixture-runner.md`;
- `PROJECT_STATE.md`;
- roadmap;
- `README.md`;
- `docs/frozen/`;
- production code;
- tests; or
- dependencies.

Do not create an implementation branch.

---

## 21. Self-Review Checklist

Before committing, verify:

- this is orchestration, not new analytics;
- public application service is the single production entry point for P9;
- no direct fixture-to-low-level-module path is authorized;
- no Skill behavior is implemented;
- no CLI is implemented;
- no Findings or Recommendations are added;
- only `revenue`, `orders`, `aov`, and `revenue_change` are in scope;
- positive Claims remain descriptive-only;
- AOV Undefined is preserved;
- P8 authoritative Claim retrieval is preserved;
- no Metric formula is duplicated;
- no schema change is made;
- no dependency change is made; and
- P9 remains blocked.
