# P9-PRE-001 - Public Application Service Foundation

## Status

PROPOSED / NOT AUTHORIZED

Implementation:
NOT STARTED

Relationship:
BLOCKING PREREQUISITE FOR P9-001

Main Project Review:
NARROW TASK CONTRACT CORRECTION REQUIRED APPLIED; RE-REVIEW REQUIRED BEFORE
IMPLEMENTATION

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

P9-PRE-001 defines the smallest in-process public application service boundary
that orchestrates already-approved P1-P8 capabilities through application-level
operations.

The purpose is not to add analytical functionality.

The purpose is to turn existing deterministic components into governed
application-level operations suitable for:

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

## 5. Read-Only Source Inspection

This correction inspected current repository state read-only before modifying
this task specification.

Inspected files and areas:

- `src/commerce_lens/contracts/requests.py`
- `src/commerce_lens/contracts/results.py`
- `src/commerce_lens/intake/registry.py`
- `src/commerce_lens/intake/csv_adapter.py`
- `src/commerce_lens/intake/excel_adapter.py`
- `src/commerce_lens/intake/sqlite_adapter.py`
- `src/commerce_lens/canonical/service.py`
- `src/commerce_lens/canonical/models.py`
- `src/commerce_lens/sufficiency/evaluator.py`
- `src/commerce_lens/engine/plan_builder.py`
- `src/commerce_lens/engine/execution.py`
- `src/commerce_lens/validation/validator.py`
- `src/commerce_lens/evidence/admissibility.py`
- `src/commerce_lens/evidence/claim_admissibility.py`
- `src/commerce_lens/persistence/metadata_store.py`
- `src/commerce_lens/application/__init__.py`
- `tests/contracts/test_contracts.py`
- relevant existing integration-style tests under `tests/intake/`,
  `tests/canonical/`, `tests/sufficiency/`, `tests/engine/`,
  `tests/validation/`, and `tests/evidence/`

Factual source-inspection findings:

- `AnalysisRequest` is defined in `commerce_lens.contracts.requests`.
- `AnalysisResult` and `MetricResult` are defined in
  `commerce_lens.contracts.results`.
- `src/commerce_lens/application/__init__.py` remains a placeholder containing
  no public application service callable or boundary implementation.
- Current intake/registration entry points are
  `DatasetRegistry.register_source`, `CsvInspectionAdapter.inspect`,
  `ExcelInspectionAdapter.inspect`, and `SQLiteInspectionAdapter.inspect`.
- Current canonicalization entry point is `canonicalize_dataset`.
- Current Data Sufficiency entry point is `evaluate_data_sufficiency`.
- Current plan builder entry point is `build_execution_plan`.
- Current execution entry point is `execute_plan`.
- Current validation entry point is `validate_executed_result`.
- Current Evidence admissibility entry point is
  `evaluate_evidence_admissibility`.
- Current ClaimCandidate persistence entry point is `persist_claim_candidate`.
- Current Claim evaluation entry point is `evaluate_claim_admissibility`.
- Current authoritative ClaimDecision retrieval entry points are
  `get_authoritative_claim_decision`, `verify_claim_decision_artifact`, and
  `list_authoritative_claim_decisions`.

---

## 6. Public Application-Service Boundary

Future implementation must define one public application service boundary with
the minimum application-level operations required by the Frozen lifecycle.

Exact Python callable or class names remain implementation details.

Do not require a specific class name.

Frozen Architecture conceptually expects:

`src/commerce_lens/application/`

Prefer the smallest location consistent with the existing package structure.

Possible future conceptual file:

`src/commerce_lens/application/analysis_service.py`

Both required operations belong to the same application boundary/module family.

Do not create a service framework.

The public application service boundary must expose conceptually:

### Operation A - Analysis

Input:

- a validated governed `AnalysisRequest`;
- explicit non-semantic source/runtime inputs required by current production
  contracts;
- explicit authorized canonicalization inputs required by current production
  contracts; and
- local runtime/persistence context required to execute reproducibly.

Output:

- `AnalysisResult`

### Operation B - Claim Evaluation

Input:

- caller-supplied complete schema-valid structured `ClaimCandidate`

Required path:

```text
caller-supplied ClaimCandidate
-> persist through approved authority path
-> existing deterministic P8 Claim evaluation
-> authoritative ClaimDecision retrieval/verification
```

Output:

- authoritative `ClaimDecision`

The application service must not accept free-form prose as executable authority.

User prose may exist only as non-authoritative audit/context metadata if already
supported by existing contracts.

P9 fixture runner must use these application-level operations.

It must not call canonicalizer, executor, validator, Evidence evaluator, or Claim
evaluator directly as a substitute for the application service.

---

## 7. Future-Compatible Lifecycle

Required future Skill-compatible sequence:

```text
Skill / structured caller
-> AnalysisRequest
-> Application Service ANALYSIS operation
-> AnalysisResult
-> Skill / structured caller constructs ClaimCandidate
-> Application Service CLAIM EVALUATION operation
-> deterministic P8 Claim policy
-> authoritative ClaimDecision
```

Required P9 sequence:

```text
Fixture
-> AnalysisRequest
-> Application Service ANALYSIS operation
-> AnalysisResult
-> fixture-supplied structured ClaimCandidate
-> Application Service CLAIM EVALUATION operation
-> authoritative ClaimDecision
-> fixture comparator later in P9
```

The application service itself must not act as the Skill.

---

## 8. Current AnalysisRequest Implementation Assessment

Current exact model/module:

- `commerce_lens.contracts.requests.AnalysisRequest`

Exact current field representing requested Metrics:

- `metrics: tuple[MetricReference, ...] = Field(min_length=1)`

Multiple requested Metrics are structurally supported:

- YES. `AnalysisRequest.metrics` is a tuple with minimum length 1, not a
  single-Metric field.

Exact current period, scope, dataset, and request authority relevant to the
service:

- `request_id`
- `canonical_business_question_id`
- `original_question_text`
- `metrics`
- `baseline_period`
- `comparison_period`
- `scope`
- `grouping`
- `required_evidence`
- `dataset_ref_id`
- `selected_sheet`
- `selected_table`
- `assumptions`
- `canonical_schema_version`
- `metric_registry_version`
- `requested_outputs`

`original_question_text` is non-authoritative context only. It must not become
executable authority.

Source path / dataset registration is already represented in `AnalysisRequest`:

- PARTIAL. `AnalysisRequest.dataset_ref_id` identifies the governed dataset
  authority, and `selected_sheet` / `selected_table` can bind governed selection
  to the request. The local source path and source type used for current intake
  and registration are not represented in `AnalysisRequest`.

Additional non-semantic execution-context arguments the application service must
receive separately where current contracts require them:

- local source path for intake/registration when a registered `DatasetReference`
  is not already supplied by the caller;
- `SourceType` for registration/adapter selection when not already represented
  by a supplied `DatasetReference`;
- selected sheet/table values for intake/registration only to bind physical
  source access to already-declared governed request authority;
- `ArtifactStore`;
- `MetadataStore`; and
- local runtime directory/context needed by those stores.

Additional governed non-`AnalysisRequest` inputs the ANALYSIS operation may
require because current production contracts require them:

- `CanonicalizationRequest`, including the caller-authorized canonical mapping
  and canonicalization options;
- `AvailableEvidence` values for Data Sufficiency where required;
- `PeriodCoverageEvidence` values for Data Sufficiency where required; and
- `ClarificationItem` values only where current sufficiency contracts already
  support them.

Do not invent `AnalysisRequest` fields.

Current `AnalysisRequest` can support the Frozen multi-Metric interface without
a material redesign.

---

## 9. Current AnalysisResult Implementation Assessment

Current exact model/module:

- `commerce_lens.contracts.results.AnalysisResult`

Current related per-Metric model/module:

- `commerce_lens.contracts.results.MetricResult`

Current `AnalysisResult` fields:

- `request_id`
- `run_id`
- `contract_version`
- `traceability_id`
- `run_status`
- `data_sufficiency_ref`
- `data_sufficiency_state`
- `metric_results`
- `failure_details`
- `executed_result_refs`
- `validation_record_refs`
- `validated_result_refs`
- `admissible_evidence_refs`
- `claim_decisions`
- `qualifications`
- `assumptions`
- `limitations`
- `blocked_metric_refs`
- `artifacts`

Current `MetricResult` fields:

- `metric_ref`
- `metric_state`
- `executed_result_refs`
- `validation_record_refs`
- `validated_result_refs`
- `admissible_evidence_refs`
- `failure_details`
- `qualifications`
- `limitations`

Contract assessment:

CURRENT CONTRACT SUFFICIENT

Current `AnalysisResult` supports the minimum P9-PRE-001 application result
without contract extension because it already carries:

- request/run identity through `request_id` and `run_id`;
- Data Sufficiency state/ref through `data_sufficiency_state` and
  `data_sufficiency_ref`;
- independent per-chain Metric states through `metric_results`;
- execution refs through top-level and per-Metric `executed_result_refs`;
- validation refs through top-level and per-Metric `validation_record_refs` and
  `validated_result_refs`;
- `AdmissibleEvidence` refs through top-level and per-Metric
  `admissible_evidence_refs`;
- blocked Metric refs through `blocked_metric_refs`;
- failure details by stage through `failure_details` and
  `MetricResult.failure_details`;
- Undefined reasons through `MetricResult.failure_details`, existing
  `FailureDetail`, and referenced `ExecutedResult` authority;
- authoritative ClaimDecision objects through `claim_decisions` after separate
  Claim Evaluation; and
- provenance/artifact references through `artifacts` and the referenced
  persisted authority records.

Minimum authorized contract extension:

- NONE

Do not modify `src/commerce_lens/contracts/results.py` for P9-PRE-001 unless a
separate Main Project Review changes this assessment.

ClaimDecision association behavior from current source inspection:

- `AnalysisResult.claim_decisions` exists as
  `tuple[ClaimDecision, ...] = ()`.
- Base analysis does not require or construct a `ClaimCandidate`.
- Optional subsequent Claim Evaluation may return an authoritative
  `ClaimDecision`.
- If an application result is returned after Claim Evaluation, it may associate
  the authoritative `ClaimDecision` through existing `claim_decisions`.
- This field does not authorize application-layer ClaimCandidate construction or
  natural-language interpretation.

---

## 10. Required Orchestration Responsibility

For eligible current requests, the service must orchestrate existing production
authority rather than reimplement it.

Conceptual ANALYSIS path:

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
-> AnalysisResult
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

## 11. Multi-Metric And Partial Completion Boundary

P9-PRE-001 preserves the existing governed `AnalysisRequest` multi-Metric
semantics.

The public ANALYSIS operation must:

- accept the existing governed `AnalysisRequest` structure;
- support only currently implemented Metrics: `revenue`, `orders`, `aov`, and
  `revenue_change`;
- execute only eligible plan nodes;
- preserve dependencies such as Revenue Change Baseline/Comparison Revenue;
- return one `AnalysisResult` containing the applicable per-chain outcomes;
- preserve independent Metric states;
- preserve blocked, failed, Undefined, and valid chains without collapsing them;
  and
- preserve partial-completion semantics where current governed cases produce
  it.

Do not invent a new batching model.

Do not create a single-Metric-only public API.

A caller may request only one governed Metric.

The application contract must not be restricted to exactly one Metric.

A failure on one dependent chain must not automatically erase an independently
valid chain unless current shared dataset/population authority requires the
block.

Do not invent new `RunStatus` or `MetricState` values.

---

## 12. ClaimCandidate Ownership

The caller owns material `ClaimCandidate` formulation and Claim type assignment.

The caller must supply a complete schema-valid structured `ClaimCandidate`.

The application layer may:

- persist the supplied `ClaimCandidate`;
- submit it to the existing P8 deterministic evaluator; and
- return authoritative `ClaimDecision`.

The application layer must not:

- infer a material `ClaimCandidate` from partial semantic fields;
- formulate a material `ClaimCandidate`;
- upgrade or downgrade Claim type;
- construct Claim type or proposition semantics from `AnalysisResult`;
- interpret arbitrary prose into Claim semantics; or
- duplicate P8 semantics.

For P9 fixtures, the fixture manifest/harness acts as the deterministic caller
supplying an already-structured `ClaimCandidate`.

For future Skill integration, the Skill constructs the `ClaimCandidate`.

Preserve:

```text
ClaimCandidate != ClaimDecision
```

---

## 13. No Semantic Duplication

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

## 14. Request And Claim Input Responsibility

The application service is not an LLM intent interpreter.

For P9 and deterministic programmatic callers, inputs must already provide the
governed structured request.

For Claim evaluation, the caller must provide a complete schema-valid structured
`ClaimCandidate`.

Do not let the application service infer:

- Metric selection from natural language;
- period meaning from prose;
- diagnostic or causal intent from prose;
- mappings from vague column names;
- missing business semantics; or
- material ClaimCandidate semantics from partial fields.

Those responsibilities remain Skill or future integration concerns.

---

## 15. Claim Authority

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

The application service must never treat a MetadataStore persistence-only
`ClaimDecision` record as equivalent to authoritative material Claim permission.

Do not expose raw persistence-only Admissible `ClaimDecision` records as
application authority.

Do not duplicate the P8 policy.

---

## 16. Failure Propagation

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

## 17. Result Contract

Future implementation must use the current `AnalysisResult` contract as the
minimum application-level structured result required for P9 and later Skill
integration.

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

Current `AnalysisResult` is sufficient for this purpose.

No `AnalysisResult` contract extension is authorized by P9-PRE-001.

Do not create user-facing prose rendering.

Do not create Finding or Recommendation fields merely for future use.

Do not add confidence scores.

Do not add benchmark fixture state into the production application result unless
the Frozen Architecture explicitly requires a generic field already.

Fixture PASS/FAIL belongs to the fixture runner, not the application service.

---

## 18. Reproducibility

The same governed request and same immutable source/canonical authority must
produce materially equivalent analytical semantics across repeated runs.

Event IDs and timestamps may differ where current contracts intentionally model
events.

Semantic authority must remain reproducible through existing fingerprints and
persisted lineage.

The application service must not introduce hidden global state.

---

## 19. Local-First Boundary

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

## 20. CLI Boundary

Do not implement or require CLI in P9-PRE-001.

Frozen Architecture permits a thin CLI over the same application service, but
P9 currently requires only the production in-process application service needed
by the fixture runner.

CLI remains a later thin adapter unless Main Project separately authorizes it.

The application service design must not prevent a future CLI adapter.

---

## 21. Public v0.1 Relationship

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

## 22. Expected Future Implementation File Scope

Expected future production files:

- create `src/commerce_lens/application/analysis_service.py`
- modify `src/commerce_lens/application/__init__.py`

Expected future contract files:

- NONE

Expected focused future test files/directories:

- create `tests/application/test_analysis_service.py`

Future implementation may also need to extend existing test fixtures/helpers
inside focused test scope, but must not modify existing production contracts
unless separate Main Project Review authorizes it.

If source inspection during future implementation shows a materially different
file structure is required, stop and request Main Project Review.

---

## 23. Expected Test Strategy For Future Implementation

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
13. no network dependency;
14. multi-Metric `AnalysisRequest` accepted through the public service;
15. independent per-chain Metric states preserved;
16. valid plus Undefined/blocked combination does not collapse into one generic
    state;
17. caller-supplied `ClaimCandidate` evaluated after `AnalysisResult`;
18. application service does not construct `ClaimCandidate`;
19. authoritative P8 `ClaimDecision` retrieval used;
20. P9-style caller can execute analysis then evaluate a structured diagnostic
    `ClaimCandidate` and receive Inadmissible; and
21. full P1-P8 regression remains passing.

Do not duplicate all lower-level tests.

Tests should prove orchestration integration.

---

## 24. Protected Boundaries

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

## 25. P9 Dependency Exit Condition

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

## 26. Task-Creation Scope

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

## 27. Self-Review Checklist

Before committing, verify:

- this is orchestration, not new analytics;
- public application service is the single production boundary for P9;
- no direct fixture-to-low-level-module path is authorized;
- no Skill behavior is implemented;
- no CLI is implemented;
- application service does not own ClaimCandidate semantics;
- analysis and Claim Evaluation are separate operations in one service boundary;
- the public service is not restricted to one Metric only;
- no Findings or Recommendations are added;
- only `revenue`, `orders`, `aov`, and `revenue_change` are in scope;
- positive Claims remain descriptive-only;
- AOV Undefined is preserved;
- P8 authoritative Claim retrieval is preserved;
- no Metric formula is duplicated;
- no schema change is made;
- no dependency change is made; and
- P9 remains blocked.
