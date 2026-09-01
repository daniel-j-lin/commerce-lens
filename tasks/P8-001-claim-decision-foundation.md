# P8-001 — ClaimDecision Foundation

## Status

PROPOSED / NOT AUTHORIZED FOR IMPLEMENTATION

Implementation:
NOT STARTED

This task specification defines the next proposed CommerceLens implementation slice after:

- Phase 1 — APPROVED / FROZEN;
- Phase 2 — APPROVED / FROZEN;
- P3-001 — APPROVED / FROZEN;
- P4-001 — APPROVED / FROZEN;
- P5-001 — APPROVED / FROZEN;
- P6-001 — APPROVED / FROZEN; and
- P7-001 — APPROVED / FROZEN.

Current approved P7 implementation HEAD:

`f48b75eb0f67f5b14675886e6ce1749835d2dc16`

Current governance reconciliation baseline:

`23ff6738c072192f9e6e70a1f55f45f2f24437b4`

Current verified full suite at P7 governance integration:

398 passed

Current MetadataStore schema:

5

This task does not authorize implementation until Main Project approval is explicitly granted.

---

## 1. Objective

P8-001 defines the smallest CommerceLens reliability slice that proves:

> A numerically correct or validated result does not automatically authorize a material Claim.

A material Claim is authorized only when:

1. its material meaning is represented in an approved structured `ClaimCandidate`;
2. the requested Claim type is permitted;
3. authentic persisted `AdmissibleEvidence` exists;
4. the `ClaimCandidate` materially agrees with that Evidence;
5. all required provenance and authority checks pass; and
6. deterministic Claim policy permits the Claim.

The Skill or LLM may propose a structured `ClaimCandidate`.

The Skill or LLM may not produce authoritative material Claim permission.

P8-001 starts at persisted `AdmissibleEvidence` and ends at deterministic `ClaimDecision`:

```text
AdmissibleEvidence
+
structured ClaimCandidate
+
governed Claim policy
↓
Deterministic Claim Admissibility Evaluation
↓
ClaimDecision
↓
STOP
```

No Finding, Recommendation, narrative rendering, or downstream product output is authorized.

---

## 2. Why P8-001 Exists

CommerceLens already separates:

- `ExecutedResult` from `ValidatedResult`;
- `ValidatedResult` from `AdmissibleEvidence`; and
- `AdmissibleEvidence` from `ClaimDecision`.

P7 completed admissible descriptive evidence for Revenue, Orders, AOV, and Revenue Change. P8-001 adds the next deterministic boundary: structured material Claim permission.

P8-001 prevents:

- treating a valid Metric value as permission for any statement involving that number;
- substituting equal values across runs, requests, datasets, populations, or validation chains;
- letting arbitrary prose become authorization authority;
- relabeling descriptive evidence as diagnostic, predictive, causal, or prescriptive authority; and
- allowing the Skill or LLM to self-authorize material Claims.

---

## 3. Governing Authority

P8-001 is subordinate to the Approved / Frozen specifications under `docs/frozen/`, especially:

- `PROJECT_MASTER_INSTRUCTIONS.md`
- `PRD.md`
- `SKILL_SCOPE_SPECIFICATION.md`
- `EVIDENCE_CONTRACT_SPECIFICATION.md`
- `CANONICAL_DATASET_AND_METRIC_DICTIONARY.md`
- `EVALUATION_FIXTURES_SPECIFICATION.md`
- `ARCHITECTURE_SPECIFICATION.md`

P8-001 also preserves the approved behavior defined by:

- `tasks/P3-001-metric-registry-population-plan.md`
- `tasks/P4-001-revenue-orders-aov-reference-execution.md`
- `tasks/P5-001-revenue-orders-aov-deterministic-validation.md`
- `tasks/P6-001-narrow-evidence-admissibility.md`
- `tasks/P7-001-revenue-change-vertical-slice.md`

Relevant Frozen authority includes:

- the governing principle: no material claim without traceable evidence;
- the Claim taxonomy: descriptive, diagnostic, predictive, causal, prescriptive;
- the Claim states: `Admissible`, `Qualified Admissible`, `Inadmissible`;
- the requirement that `ClaimCandidate` be structured;
- the requirement that a deterministic Claim Admissibility Evaluator, not the Skill, owns material Claim permission;
- the requirement that arbitrary prose that cannot be structurally represented fails closed; and
- the MVP lineage path `Claim -> ClaimDecision -> Admissible Evidence -> Validated Result -> Validation Record -> Execution Record -> Metric Reference -> Dataset Reference`.

Do not modify Frozen specifications during P8-001 implementation.

---

## 4. Current Approved Baseline

Current implemented and approved reliability chain:

```text
AnalysisRequest
→ DataSufficiencyResult
→ ExecutionPlan
→ ExecutionRecord
→ ExecutedResult
→ ValidationRecord
→ ValidatedResult
→ EvidenceAdmissibilityRecord
→ AdmissibleEvidence
→ STOP
```

Current implemented Metrics with complete evidence chains:

- `revenue`
- `orders`
- `aov`
- `revenue_change`

Current `AdmissibleEvidence` behavior:

- descriptive `metric_value` evidence for Valid Revenue;
- descriptive `metric_value` evidence for Valid Orders;
- descriptive `metric_value` evidence for Valid numeric AOV;
- descriptive `metric_state` evidence for governed AOV Undefined because Orders = 0; and
- descriptive `metric_value` evidence for Valid Revenue Change.

Current claim-related contracts exist but are not sufficient for P8-001 deterministic material binding:

- `ClaimCandidate` currently carries `claim_id`, `claim_type`, `intended_scope`, prose `proposed_meaning`, supporting references, materiality, and metadata.
- `ClaimDecision` currently carries `decision_id`, `claim_id`, `policy_version`, `claim_state`, reason, supporting references, required qualifications, and timestamp.

P8-001 must tighten or extend these contracts only as needed to make material meaning deterministic and structurally comparable. Do not use arbitrary prose as authorization authority.

---

## 5. Lifecycle

P8-001 must preserve this required lifecycle:

```text
AnalysisRequest
→ DataSufficiencyResult
→ ExecutionPlan
→ ExecutionRecord
→ ExecutedResult
→ ValidationRecord
→ ValidatedResult
→ EvidenceAdmissibilityRecord
→ AdmissibleEvidence
→ ClaimCandidate
→ ClaimDecision
→ STOP
```

These boundaries remain mandatory:

- `ExecutedResult != ValidatedResult`
- `ValidatedResult != AdmissibleEvidence`
- `AdmissibleEvidence != ClaimDecision`
- `ClaimDecision != Finding`

P8-001 must not bypass, reconstruct, or reinterpret earlier authority from conversational context.

---

## 6. In Scope

P8-001 may define and later implement only:

- minimum structured `ClaimCandidate` contract changes needed for supported descriptive Claims;
- minimum deterministic `ClaimDecision` contract changes needed for P8;
- a lightweight deterministic Claim Admissibility Evaluator;
- a narrow immutable/static Claim policy;
- persisted runtime authority for `ClaimCandidate`;
- persisted runtime authority for `ClaimDecision`;
- immutable artifacts for Claim candidates and Claim decisions;
- a narrow MetadataStore schema v6 migration to index ClaimCandidate and ClaimDecision authority;
- deterministic semantic decision fingerprints;
- failure-code behavior for fail-closed Claim evaluation; and
- tests required to prove this P8 slice.

---

## 7. Out of Scope

P8-001 must not implement or authorize:

- Findings;
- Alternative Explanations artifacts;
- Recommendations;
- diagnostic Claim permission;
- predictive Claim permission;
- causal Claim permission;
- prescriptive Claim permission;
- Revenue Change Percentage;
- Product metrics;
- Category metrics;
- Contribution;
- Contribution Share;
- rankings;
- physical fixture runner;
- `SKILL.md`;
- LLM orchestration;
- UI;
- benchmark scoring;
- MCP;
- external executor adapters;
- Wren;
- RAG;
- Vector Database;
- Multi-Agent;
- generic policy framework.

---

## 8. ClaimCandidate Contract Expectation

P8-001 must define the minimum structured `ClaimCandidate` contract required to represent the material meaning of supported descriptive Claims.

The future contract must preserve or adapt existing fields where compatible, and add only the minimum governed fields needed for deterministic authorization.

Required P8 fields:

- `claim_candidate_id` or a backwards-compatible replacement for current `claim_id`;
- `claim_type`: exact existing `ClaimType.DESCRIPTIVE` value `descriptive` for admissible P8 cases;
- `metric_ref`: one of `revenue`, `orders`, `aov`, `revenue_change`;
- `metric_definition_version`: currently `metric_dictionary_v1`;
- `intended_scope`: structured `ScopeDefinition`;
- `population_ref`;
- `population_fingerprint`;
- `period_ref`;
- `period_role`;
- `proposition_type`: controlled P8 value, either `metric_value_equals` or `metric_state_is`;
- `claimed_value`: required for `metric_value_equals`, absent for `metric_state_is`;
- `claimed_metric_state`: required for `metric_state_is`;
- `undefined_reason`: required only for governed Undefined state Claims;
- `unit`: required when represented by the supporting ValidatedResult and Evidence;
- `currency`: required for monetary Metrics;
- `supporting_evidence_refs`: one or more `AdmissibleEvidence.evidence_id` values;
- `supporting_validated_result_refs`: matching `ValidatedResult.validated_result_id` values;
- `intended_material_use`: a bounded descriptive material-use marker; and
- optional non-authoritative presentation text only if it is clearly metadata and is never used for permission.

Revenue Change candidates must also represent:

- `baseline_period_ref`;
- `comparison_period_ref`;
- `baseline_population_ref`;
- `comparison_population_ref`;
- `baseline_population_fingerprint`;
- `comparison_population_fingerprint`; and
- comparison direction semantics: Comparison Revenue minus Baseline Revenue.

The material meaning used for deterministic authorization must be structured.

If a material Claim cannot be represented by approved structured fields, P8-001 must fail closed with `unrepresentable_material_claim`.

Do not create a generic natural-language truth engine.

---

## 9. ClaimDecision Contract Expectation

P8-001 must define the minimum deterministic `ClaimDecision` contract.

The exact existing `ClaimState` domain must be preserved:

- `Admissible`
- `Qualified Admissible`
- `Inadmissible`

P8-001 must not invent new qualification semantics merely to exercise `Qualified Admissible`.

Because the current supported P8 descriptive cases do not introduce an already-governed non-blocking Claim qualification beyond existing evidence limitations, P8-001 must:

- retain `Qualified Admissible` in the contract state domain; and
- not newly authorize a positive Qualified Admissible case unless implementation discovers an already-governed qualification path in existing authority.

Required P8 fields:

- `claim_decision_id` or backwards-compatible `decision_id`;
- `claim_candidate_ref`;
- `claim_state`: exact `ClaimState`;
- `policy_id`;
- `policy_version`;
- `supporting_evidence_refs`;
- `supporting_validated_result_refs`;
- governed scope / population fields used by the decision;
- period context used by the decision;
- `reason`;
- `failure_code` when `claim_state` is `Inadmissible`;
- `required_qualification` or existing `required_qualifications` only when already governed;
- `decision_fingerprint`;
- `decided_at`.

Do not add confidence scores, completeness percentages, thresholds, or LLM-rating fields.

---

## 10. Supported Claim Type

P8-001 supports only:

- `ClaimType.DESCRIPTIVE`, value `descriptive`

P8-001 must fail closed as `Inadmissible` for:

- `ClaimType.DIAGNOSTIC`, value `diagnostic`;
- `ClaimType.PREDICTIVE`, value `predictive`;
- `ClaimType.CAUSAL`, value `causal`; and
- `ClaimType.PRESCRIPTIVE`, value `prescriptive`.

Unsupported Claim types must not be downgraded into descriptive Claims automatically.

The Skill or LLM must not override the decision.

---

## 11. Supported Metrics

P8-001 applies only to currently complete Evidence chains:

- `revenue`
- `orders`
- `aov`
- `revenue_change`

Do not add ClaimDecision support for:

- `revenue_change_pct`
- product Metrics
- category Metrics
- contribution
- ranking
- refund
- discount
- gross margin
- retention
- inventory

---

## 12. Supported Descriptive Claim Semantics

P8-001 may authorize only direct structured descriptive propositions supported by authentic Evidence.

Supported forms:

- Revenue: Revenue for governed scope and period equals X.
- Orders: Orders for governed scope and period equals X.
- AOV numeric: AOV for governed scope and period equals X.
- AOV state: AOV for governed scope and period is `Undefined` because Orders = 0.
- Revenue Change: Revenue Change from governed Baseline to Comparison equals X.

P8-001 must not authorize:

- Product X drove the change.
- Revenue fell because demand weakened.
- The campaign caused growth.
- Pricing caused the decline.
- We should increase advertising.
- The result will continue next month.

Those are outside supported descriptive material semantics.

---

## 13. Evidence Authenticity

P8-001 must require authentic persisted `AdmissibleEvidence`.

A caller-supplied Pydantic object is not authority merely because it is schema-valid.

The evaluator must verify, at minimum:

- `EvidenceAdmissibilityRecord` exists;
- the record passed and links the expected `AdmissibleEvidence`;
- `AdmissibleEvidence` artifact exists;
- artifact reference metadata matches the metadata store;
- artifact hash / fingerprint matches;
- restored persisted artifact equals authoritative Evidence;
- `AdmissibleEvidence.evidence_id` matches its semantic `evidence_fingerprint`;
- evidence semantic fingerprint is authentic;
- request authority is authentic;
- `DataSufficiencyResult` authority is authentic;
- Metric and definition version match;
- canonical dataset identity and fingerprint match;
- source dataset authority matches;
- population identity and fingerprint match;
- governed scope matches;
- period and role match;
- `ValidatedResult` authority matches;
- required `ValidationRecord` records remain authentic;
- source `ExecutedResult` authority remains linked;
- Claim type and Evidence role compatibility passes.

P8-001 must reuse approved P6/P7 authority paths where appropriate.

Do not duplicate Revenue, Orders, AOV, or Revenue Change formulas in Claim policy.

`ClaimDecision` is not a second Metric validator.

---

## 14. Claim ↔ Evidence Semantic Binding

P8-001 must deterministically prove applicable equality and compatibility across:

- Claim type;
- Metric ref;
- Metric definition version;
- evidence role;
- proposition type;
- claimed value or governed metric state;
- population;
- population fingerprint;
- scope filters;
- period;
- period role;
- Baseline / Comparison context where applicable;
- unit;
- currency;
- canonical dataset;
- source dataset;
- request authority;
- supporting `ValidatedResult`;
- supporting `AdmissibleEvidence`.

Numerical equality alone is not sufficient.

Equivalent values from another:

- request;
- dataset;
- canonical dataset;
- population;
- period;
- execution run;
- validation chain;
- evidence record

must not substitute authority.

Material provenance difference must produce a different semantic decision fingerprint or fail closed.

---

## 15. Revenue Change Authority

Revenue Change descriptive `ClaimDecision` must preserve two-period semantics.

It must remain bound to:

- Baseline period;
- Comparison period;
- Baseline population;
- Comparison population;
- governed material scope;
- governed currency;
- Revenue Change metric definition/version;
- authentic Revenue Change `ValidatedResult`;
- authentic Revenue Change `AdmissibleEvidence`;
- authentic Baseline Revenue dependency lineage; and
- authentic Comparison Revenue dependency lineage.

The material Claim is only:

> what Revenue Change was.

P8-001 does not authorize why it changed.

No contribution, driver, causal, diagnostic, or recommendation semantics are allowed.

---

## 16. AOV Undefined Decision

Authoritative decision:

P8-001 must support a structured descriptive AOV state Claim only when current governed evidence supports AOV Undefined.

Current authority establishes:

- the Frozen Metric Dictionary defines AOV as `Undefined` when Orders = 0;
- P6-001 approved governed AOV Undefined behavior;
- current validation produces `ValidatedResult.metric_state = MetricState.UNDEFINED` with `undefined_reason = orders_equals_zero`;
- current evidence admissibility admits only AOV Undefined because Orders = 0 as `EvidenceRole.METRIC_STATE`; and
- current evidence admissibility rejects AOV Undefined as `metric_value` evidence.

Therefore P8-001 must implement this deterministic behavior:

- a structured descriptive `metric_state_is` ClaimCandidate for `aov` may be `Admissible` only when it claims `MetricState.UNDEFINED` with `undefined_reason=orders_equals_zero` and matches authentic persisted AOV `metric_state` AdmissibleEvidence;
- a numeric `metric_value_equals` AOV ClaimCandidate must be `Inadmissible` when no numeric AOV exists;
- a caller must not convert AOV Undefined into numeric zero or any other placeholder value;
- a non-AOV Undefined state Claim must fail closed; and
- an AOV Undefined state Claim with the wrong reason, population, period, scope, evidence role, or evidence authority must fail closed.

Required AOV Undefined tests:

- authentic AOV Undefined `metric_state_is` descriptive Claim becomes `Admissible`;
- numeric AOV value Claim against Undefined evidence becomes `Inadmissible`;
- AOV Undefined with wrong `undefined_reason` becomes `Inadmissible`;
- AOV Undefined using `metric_value` evidence role becomes `Inadmissible`;
- non-AOV Undefined state Claim becomes `Inadmissible`;
- AOV Undefined with wrong period, population, scope, dataset, ValidatedResult, or Evidence becomes `Inadmissible`.

---

## 17. Persistence / Schema Decision

Authoritative decision:

MetadataStore schema v6 is required for P8-001.

ClaimCandidate persistence decision:

- `ClaimCandidate` must be persisted as authoritative runtime/run state before Claim evaluation.
- The persisted candidate, not a caller-supplied object alone, is the authority evaluated by the deterministic policy.
- The candidate must have an immutable JSON artifact and a MetadataStore index row.

ClaimDecision persistence decision:

- `ClaimDecision` must be persisted.
- The persisted decision is the authoritative material Claim permission record.
- The decision must have an immutable JSON artifact and a MetadataStore index row.

Immutable artifact decision:

- Immutable artifacts are required for both `ClaimCandidate` and `ClaimDecision`.
- SQLite rows may index searchable fields and contain cached JSON, but artifact references and fingerprints remain first-class authority.

Schema v6 justification:

- schema v5 has no `claim_candidates` table;
- schema v5 has no `claim_decisions` table;
- schema v5 has no indexed candidate artifact reference;
- schema v5 has no indexed decision artifact reference;
- schema v5 has no durable policy ID/version index for Claim decisions;
- schema v5 has no durable `ClaimState` index;
- schema v5 has no durable decision fingerprint index; and
- Frozen Architecture requires MVP lineage through `Claim -> ClaimDecision -> Admissible Evidence`.

Minimum schema v6 expectation:

- add `SCHEMA_VERSION = 6`;
- add migration from v5 to v6 only;
- add `claim_candidates` table;
- add `claim_decisions` table;
- preserve all v5 tables and migrations;
- verify schema v6 column sets explicitly;
- store full JSON payloads;
- index stable IDs, request/evidence/result links, policy, state, fingerprint, artifact IDs, and timestamps needed for review;
- add get/list helpers needed by the evaluator and tests;
- do not design unrelated new tables.

No schema v6 migration is implemented during task creation.

---

## 18. Deterministic Policy

P8-001 must define a narrow immutable/static policy authority.

Policy ID:

`commerce_lens_p8_claim_admissibility`

Policy version:

`p8_001_v1`

The policy must define:

- supported Claim type: `descriptive`;
- supported Metrics: `revenue`, `orders`, `aov`, `revenue_change`;
- supported proposition types: `metric_value_equals`, `metric_state_is`;
- evidence-role requirements;
- ClaimCandidate persistence requirements;
- ClaimDecision persistence requirements;
- evidence authenticity requirements;
- deterministic semantic binding requirements;
- fail-closed failure codes;
- semantic decision fingerprint requirements.

Do not create:

- a generic policy DSL;
- rules engine framework;
- plugin system;
- arbitrary expression evaluator;
- LLM-as-judge path.

Equivalent authoritative semantic input must produce:

- a distinct event/decision ID where required by the event model; and
- the same material semantic decision fingerprint.

Unique event identity remains distinct from semantic decision identity.

Material provenance difference must produce a different semantic decision fingerprint or fail closed.

---

## 19. Failure Codes / Fail-Closed Behavior

P8-001 must fail closed for applicable:

- `claim_candidate_missing`
- `claim_candidate_not_persisted`
- `claim_candidate_artifact_missing`
- `claim_candidate_artifact_hash_mismatch`
- `claim_candidate_fingerprint_mismatch`
- `unsupported_claim_type`
- `unsupported_metric`
- `unsupported_proposition_type`
- `unrepresentable_material_claim`
- `missing_supporting_evidence`
- `duplicate_or_ambiguous_supporting_evidence`
- `forged_evidence_object`
- `missing_persisted_evidence_authority`
- `tampered_evidence_artifact`
- `evidence_fingerprint_mismatch`
- `wrong_evidence_role`
- `wrong_metric`
- `wrong_metric_definition_version`
- `wrong_claimed_value`
- `wrong_metric_state`
- `wrong_undefined_reason`
- `wrong_period`
- `wrong_period_role`
- `wrong_baseline_comparison_context`
- `wrong_population`
- `wrong_population_fingerprint`
- `wrong_scope`
- `wrong_dataset`
- `wrong_canonical_dataset`
- `wrong_currency`
- `wrong_unit`
- `wrong_validated_result`
- `missing_validation_record`
- `tampered_validation_record`
- `mismatched_executed_result_lineage`
- `cross_request_substitution`
- `cross_run_equal_value_substitution`
- `policy_version_mismatch`
- `unsupported_material_claim_strength`

Failure must create no admissible material Claim permission.

Failed Claim evaluation may persist an `Inadmissible` `ClaimDecision` with reason and failure code, but it must not create a Finding.

No LLM override is permitted.

---

## 20. Independent-Chain Behavior

P8-001 must preserve per-Claim and per-Evidence independence.

An `Inadmissible` `ClaimCandidate` must not globally invalidate otherwise authentic:

- Revenue Evidence;
- Orders Evidence;
- AOV Evidence;
- Revenue Change Evidence; or
- unrelated `ClaimCandidate` records.

Only shared prerequisite failure may affect multiple dependent chains.

An invalid causal Claim about Revenue Change must not invalidate a separate authentic descriptive Revenue Change Claim.

A failed AOV numeric Claim against Undefined evidence must not invalidate the authentic AOV Undefined state evidence or unrelated Revenue/Orders evidence.

---

## 21. Required Tests

No tests are implemented during this task-creation step.

Future P8-001 implementation must include deterministic tests at minimum.

Positive:

1. Revenue descriptive Claim -> `Admissible`.
2. Orders descriptive Claim -> `Admissible`.
3. Valid numeric AOV descriptive Claim -> `Admissible`.
4. Revenue Change descriptive Claim -> `Admissible`.
5. AOV Undefined structured state descriptive Claim -> `Admissible`.
6. Semantically equivalent authoritative Claim evaluation repeated: unique decision/event IDs where required and stable semantic decision fingerprint.

Negative / fail closed:

7. diagnostic ClaimCandidate from descriptive Revenue Evidence.
8. causal ClaimCandidate.
9. prescriptive ClaimCandidate.
10. predictive ClaimCandidate.
11. wrong claimed value.
12. wrong Metric.
13. wrong Metric version.
14. wrong period.
15. wrong period role.
16. wrong population.
17. wrong population fingerprint.
18. wrong scope.
19. wrong currency.
20. wrong unit.
21. wrong canonical dataset.
22. wrong source dataset / request authority where represented.
23. missing supporting Evidence.
24. duplicate / ambiguous supporting Evidence.
25. caller-forged Evidence object.
26. tampered Evidence artifact.
27. forged Evidence fingerprint.
28. wrong ValidatedResult.
29. missing required ValidationRecord.
30. failed required ValidationRecord.
31. tampered required ValidationRecord.
32. mismatched ExecutedResult lineage.
33. cross-run numerically equal Evidence substitution.
34. cross-request Evidence substitution.
35. arbitrary material prose that cannot be represented structurally.
36. ClaimDecision failure does not invalidate unrelated authentic Evidence.
37. numeric AOV value Claim against Undefined evidence -> `Inadmissible`.
38. AOV Undefined with wrong `undefined_reason` -> `Inadmissible`.
39. AOV Undefined using wrong evidence role -> `Inadmissible`.
40. non-AOV Undefined state Claim -> `Inadmissible`.
41. Revenue Change Claim with wrong Baseline / Comparison context -> `Inadmissible`.
42. unsupported `revenue_change_pct` Claim -> `Inadmissible`.

Persistence / artifact integrity:

43. ClaimCandidate must be persisted before evaluation.
44. caller-supplied ClaimCandidate differing from persisted candidate fails closed.
45. missing ClaimCandidate artifact fails closed.
46. tampered ClaimCandidate artifact fails closed.
47. ClaimDecision is persisted with immutable artifact.
48. tampered ClaimDecision artifact is detectable through verification helper.
49. MetadataStore migrates v5 to v6 preserving v5 authority.
50. MetadataStore rejects incompatible or unknown schema versions.
51. schema v6 indexes policy ID/version, `ClaimState`, decision fingerprint, candidate artifact, and decision artifact.

No test may create Findings, Recommendations, later Metrics, fixture runner behavior, or LLM orchestration.

---

## 22. Acceptance Criteria

P8-001 implementation is successful only if:

- supported descriptive Claims with authentic matching Evidence are deterministically `Admissible`;
- unsupported Claim types are `Inadmissible`;
- unsupported Metrics are `Inadmissible`;
- unsupported material semantics are `Inadmissible`;
- numerical equality cannot bypass provenance;
- caller-created Evidence cannot create Claim authority;
- caller-created ClaimCandidate cannot bypass persisted candidate authority;
- evidence artifacts are re-authenticated;
- ClaimCandidate artifacts are re-authenticated;
- ClaimDecision artifacts are persisted and verifiable;
- Claim to Evidence semantic mismatch fails closed;
- AOV Undefined behavior follows the governed `metric_state_is` decision in this task;
- Revenue Change retains two-period authority;
- policy ID/version and semantic decision identity are reproducible;
- failure creates no material Claim permission;
- unrelated authentic evidence chains remain valid;
- no downstream Finding is created;
- MetadataStore schema advances to v6 for the narrow ClaimCandidate/ClaimDecision authority indexes; and
- all required future tests pass.

---

## 23. Protected Boundaries

During P8-001 task creation and future implementation, do not modify:

- `docs/frozen/`
- existing Approved / Frozen P1-P7 task semantics
- Metric definitions
- Evidence Contract semantics
- fixture expected outcomes
- unrelated implementation phases
- dependency files
- `README.md` unless separately authorized
- `PROJECT_STATE.md` unless explicitly authorized after Main Project approval

During this task-creation step specifically, modify only:

- `tasks/P8-001-claim-decision-foundation.md`

---

## 24. STOP Condition

STOP and request Main Project review if future implementation discovers:

- Frozen authority materially conflicts with current implementation;
- the structured ClaimCandidate fields cannot represent a supported P8 descriptive Claim without inventing unapproved semantics;
- AOV Undefined behavior differs from the authority summarized here;
- schema v6 is insufficient for required Claim lineage without broader architecture changes;
- implementing P8 requires changing Metric formulas;
- implementing P8 requires changing Evidence admissibility semantics;
- implementing P8 requires a generic policy framework;
- implementing P8 requires LLM judgment for material permission;
- implementing P8 requires Revenue Change Percentage or later Metrics;
- implementing P8 requires Finding or Recommendation behavior; or
- any material ambiguity remains about supported Claim type, supported Metrics, AOV Undefined behavior, persistence, schema version, or phase boundary.

If any STOP condition is reached, do not repair, reinterpret, or continue into implementation.

---

## 25. Self-Review Checklist

Before P8-001 implementation can be submitted for review, verify:

- no ambiguity remains about supported Claim type;
- no ambiguity remains about supported Metrics;
- no ambiguity remains about AOV Undefined behavior;
- no ambiguity remains about schema v5 vs v6;
- `ClaimDecision` is not conflated with Finding;
- Claim policy is not a second Metric validation layer;
- caller-supplied Evidence is not treated as authority;
- caller-supplied ClaimCandidate is not treated as authority;
- cross-run equal-value substitution is covered;
- cross-request substitution is covered;
- no later-phase functionality has entered P8;
- no production code outside the minimum P8 boundary changed;
- no tests outside the minimum P8 boundary changed;
- no dependencies changed; and
- all changed artifacts are reviewed with `git diff --check`.

---

## 26. Task-Creation Boundary

This task specification was created only to define P8-001.

Task creation must not:

- implement P8;
- modify production code;
- modify tests;
- create the implementation branch;
- modify Frozen specifications;
- modify `AGENTS.md`;
- modify `PROJECT_STATE.md`;
- modify `decisions/`;
- modify dependencies;
- begin P9;
- begin Revenue Change Percentage.

After this file is committed, STOP.
