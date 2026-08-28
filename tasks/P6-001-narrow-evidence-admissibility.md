# P6-001 — Narrow Evidence Admissibility for Revenue, Orders, and AOV

## Status

SPECIFICATION CREATED

Implementation:
NOT STARTED

Main Project Review:
REQUIRED BEFORE IMPLEMENTATION APPROVAL

Revenue / Orders / AOV deterministic validation:
IMPLEMENTED BY P5-001

Evidence admissibility:
AUTHORIZED ONLY BY THIS TASK WHEN SEPARATELY IMPLEMENTED

Admissible Evidence:
NOT YET IMPLEMENTED

ClaimDecision:
NOT PART OF P6-001

Revenue Change:
NOT PART OF P6-001

Next implementation after P6-001:
REQUIRES SEPARATE MAIN PROJECT AUTHORIZATION

---

## 1. Purpose

P6-001 defines the smallest CommerceLens implementation slice that establishes deterministic Evidence admissibility after P5-001 deterministic result validation.

Approved project state before this task:

Phase 1:
APPROVED / FROZEN

Phase 2:
APPROVED / FROZEN

P3-001:
APPROVED / FROZEN

P4-001:
APPROVED / FROZEN

P5-001:
APPROVED / FROZEN

Current reliability chain:

Metric Registry
↓
Governed Population
↓
Data Sufficiency
↓
ExecutionPlan
↓
deterministic execution
↓
ExecutionRecord
↓
ExecutedResult
↓
Required Validation Rules
↓
ValidationRecords
↓
complete validation bundle
↓
ValidatedResult
↓
durable persistence

P6-001 continues:

Persisted authoritative ValidatedResult
+
governed Required Evidence context
+
Data Sufficiency authority
↓
Deterministic Evidence Admissibility Evaluation
↓
AdmissibilityRecord
↓
AdmissibleEvidence
↓
STOP

P6-001 establishes whether a deterministically ValidatedResult is eligible to serve as Evidence for the governed analytical purpose.

P6-001 must preserve:

ValidatedResult
≠
Admissible Evidence

and:

Admissible Evidence
≠
ClaimDecision

Do not collapse these lifecycle stages.

---

## 2. Strategic Role

CommerceLens is an Evidence Reliability Kernel.

A result is not admissible Evidence merely because it is numerically validated.

Evidence admissibility depends on the Frozen Evidence Contract and the governed analytical context:

- Business Question or supported sub-question;
- Analytical Scope;
- Metric Reference;
- Required Evidence;
- Available Evidence;
- Data Sufficiency Assessment;
- Execution Record;
- Executed Result;
- Validation Records;
- Validated Result;
- intended claim type where required by Frozen authority; and
- provenance and reproducibility linkage.

P6-001 establishes the first:

ValidatedResult
→
AdmissibleEvidence

reference path.

It does not decide whether a Claim is supported.

---

## 3. Governing Principle

> No material claim without traceable evidence.

And specifically for P6-001:

> A ValidatedResult is not Admissible Evidence merely because validation passed.

Evidence admissibility must be deterministic.

The Skill / LLM must not self-authorize:

- which Required Evidence applies;
- whether Available Evidence satisfies Required Evidence;
- whether a ValidatedResult satisfies the required Evidence role;
- whether provenance is sufficient;
- whether Evidence is admissible;
- whether failed, undefined, blocked, or qualified states may satisfy a requirement.

---

## 4. Governing Documents

P6-001 is subordinate to the Approved / Frozen specifications under:

`docs/frozen/`

Especially:

- `PROJECT_MASTER_INSTRUCTIONS.md`
- `PRD.md`
- `SKILL_SCOPE_SPECIFICATION.md`
- `EVIDENCE_CONTRACT_SPECIFICATION.md`
- `CANONICAL_DATASET_AND_METRIC_DICTIONARY.md`
- `EVALUATION_FIXTURES_SPECIFICATION.md`
- `ARCHITECTURE_SPECIFICATION.md`

Also preserve all Approved / Frozen P3-001, P4-001, and P5-001 task contracts.

The Frozen Evidence Contract is authoritative.

Do not infer Evidence semantics from generic industry practice.

If Frozen authority does not deterministically define a material Evidence admissibility rule:

STOP and request Main Project review.

Do not invent the rule.

---

# PART A — AUTHORIZED P6 SCOPE

## 5. Metrics

P6-001 may evaluate Evidence admissibility ONLY for already implemented and validated Metric results for:

- `revenue`
- `orders`
- `aov`

No execution, validation, evidence admissibility, claim policy, or reporting behavior is authorized for:

- `revenue_change`
- `revenue_change_pct`
- product Metrics
- category Metrics
- contribution
- rankings

## 6. Lifecycle Scope

Authorized lifecycle:

Required Evidence
+
Available Evidence
+
Data Sufficiency Assessment
+
ValidatedResult
↓
Evidence Admissibility Evaluation
↓
AdmissibilityRecord
↓
AdmissibleEvidence
↓
STOP

Explicitly out of scope:

AdmissibleEvidence
→
ClaimDecision

and everything after ClaimDecision.

P6-001 must not create Findings, Alternative Explanations, Recommendations, report rendering, Skill output, UI, MCP, external executor adapters, Wren, or Revenue Change.

## 7. Evidence Lifecycle Terminology

Use only the Frozen lifecycle concepts below.

**Required Evidence**

Evidence that must exist for the intended claim type, Metric, scope, and analytical purpose.

**Available Evidence**

Evidence currently present and accessible for assessment or analysis. Availability alone does not establish admissibility.

**Validated Result**

An Executed Result that has satisfied all applicable deterministic validation requirements for its intended material use.

**Admissible Evidence**

Evidence that has satisfied all applicable requirements governing its intended role in a material Claim evidence chain, including provenance, authoritative definition, sufficiency, execution, validation, scope, and other applicable requirements.

Do not reintroduce obsolete or ambiguous lifecycle terminology.

Availability alone must not imply admissibility.

Validation alone must not imply admissibility.

---

# PART B — REQUIRED EVIDENCE AUTHORITY

## 8. Required Evidence Source of Authority

P6-001 must reuse existing Frozen authority and current governed contracts.

Do NOT create a second independent Required Evidence system.

Required Evidence for P6 must be resolved from the existing governed chain, as applicable:

- `AnalysisRequest.required_evidence`;
- `DataSufficiencyResult.required_evidence`;
- `DataSufficiencyResult.available_evidence`;
- `DataSufficiencyResult.metric_eligibility`;
- `ExecutionPlan.sufficiency_id`;
- `ExecutionPlan` Metric nodes;
- Metric Registry definition and version;
- P5 ValidatedResult intended use and validation fingerprint;
- Canonical Dataset and Population references; and
- Frozen Evidence Contract Sections 13, 14, 15, 17, 22, 23, 32, 33, 38, 39, and 42.

For P6, Required Evidence must be linked deterministically to:

- Business Question or supported sub-question;
- analytical purpose;
- Metric ID;
- Metric definition version;
- period and population;
- intended claim type where applicable;
- Required Evidence requirement;
- Data Sufficiency disposition;
- ValidatedResult;
- ValidationRecords;
- ExecutedResult;
- ExecutionRecord; and
- canonical dataset identity and fingerprint.

## 9. Required Evidence Grain

The Evidence Contract defines Required Evidence as claim-type, Metric, scope, and analytical-purpose dependent.

For the P6-001 narrow slice, the intended implementation grain must be:

one admissibility evaluation event
for one Required Evidence requirement
against one authoritative persisted ValidatedResult
within one governed analytical context.

If a future implementation determines from Frozen authority that the governed grain must instead be per result, per requirement group, per claim context, or another grain:

STOP and request Main Project review before implementation.

Do not resolve the grain by implementation convenience.

## 10. Multiple Requirement Satisfaction

P6-001 must not assume that one ValidatedResult can satisfy multiple Required Evidence requirements unless the Frozen Evidence Contract and existing governed context establish that deterministically.

If one ValidatedResult appears capable of satisfying multiple requirements:

- either create separate admissibility evaluations per requirement; or
- STOP if the resulting evidence semantics are ambiguous.

Do not silently treat a ValidatedResult as broadly reusable evidence for unrelated purposes, scopes, Metrics, periods, or claim types.

## 11. Analytical Purpose and Claim-Type Context

P6-001 is not ClaimDecision.

However, Evidence admissibility is evaluated for an intended role in a material Claim evidence chain. Therefore the P6 context must carry the intended claim type whenever it is material to the Frozen Evidence Contract.

Preserve the project taxonomy:

- descriptive
- diagnostic
- predictive
- causal
- prescriptive

For the P6-001 narrow Metrics:

- Revenue, Orders, and AOV ValidatedResults may be evaluated as evidence for bounded descriptive numerical Claims when all Required Evidence and traceability checks pass.
- They may serve as descriptive basis for a later bounded diagnostic chain only when the later task separately implements the additional diagnostic Evidence requirements.
- They must not be admitted as causal, predictive, or prescriptive Evidence for stronger claims in P6.

P6 must not upgrade descriptive Evidence into causal Evidence.

Contribution, association, sequence, or numerical validation must never be treated as causation.

If intended claim-type requirements cannot be resolved from current Required Evidence context:

STOP and request Main Project review.

---

# PART C — VALIDATEDRESULT AUTHENTICITY

## 12. Persisted ValidatedResult Authority

P6-001 must consume authoritative persisted ValidatedResult evidence.

Do not trust arbitrary caller-supplied ValidatedResult objects.

Before an admissibility evaluation may proceed, the implementation must verify, using P5 authority rather than duplicating validation:

- ValidatedResult artifact exists;
- ValidatedResult artifact content hash/fingerprint matches its immutable ArtifactStore reference;
- ValidatedResult artifact schema is valid;
- ValidatedResult is present in or linked from persisted P5 ValidationRecord metadata;
- source ExecutedResult linkage is present and consistent;
- source ExecutedResult artifact exists and matches its persisted artifact fingerprint;
- complete required ValidationRecord bundle exists;
- every required ValidationRecord status is `passed`;
- validation fingerprint matches the complete required validation bundle;
- Metric ID and Metric definition version match the Required Evidence requirement;
- canonical dataset ID and fingerprint match;
- population ID and fingerprint match;
- period reference and period role match where applicable;
- currency matches for monetary Metrics;
- MetricState and undefined reason are governed;
- validation intended use is compatible with the P6 analytical purpose; and
- no persisted failure or contradiction blocks use.

If any authenticity or lineage check fails:

- fail closed;
- persist a failed admissibility record where governed;
- produce no successful AdmissibleEvidence object; and
- preserve the exact reason/code.

Do not rerun P5 validation as a substitute for verifying persisted P5 authority unless the existing validation API explicitly owns that verification path.

## 13. Validation Authority Reuse

P6 must not create a second validation implementation.

P6 may inspect P5 artifacts and records, and may call existing P5 validation/authenticity helpers if available.

P6 must not decide that a result is valid by checking:

- `metric_state == Valid`;
- artifact presence alone;
- a single validation record alone;
- caller assertion;
- test fixture labels; or
- LLM/Skill text.

---

# PART D — DATA SUFFICIENCY AUTHORITY

## 14. Sufficiency Gate Preservation

P6-001 must preserve the existing Data Sufficiency gate.

A ValidatedResult must not become Admissible Evidence if the Required Evidence / Data Sufficiency contract for its intended analytical purpose is materially unsatisfied.

Do NOT interpret:

ValidatedResult

as evidence that all business-question-level Required Evidence exists.

Metric validation and analytical sufficiency are separate authorities.

## 15. Sufficiency Provenance

P6 must resolve sufficiency provenance deterministically.

At minimum, the admissibility evaluator must verify that:

- the DataSufficiencyResult corresponds to the same request ID, dataset, canonical dataset, Metric, period, population, and Required Evidence context as the ValidatedResult;
- sufficiency state permits the affected Metric chain to proceed;
- the relevant `MetricEligibility` for the Metric is eligible;
- no sufficiency failure detail blocks the affected Required Evidence requirement;
- Available Evidence satisfying the requirement is linked to governed source, dataset, canonicalization, execution, validation, or context records; and
- qualifications or limitations from sufficiency remain attached when material.

Current MetadataStore schema version 4 does not define a dedicated DataSufficiencyResult table. P6 implementation must first determine whether the current persisted artifacts and records can establish sufficiency authority without a second Required Evidence system.

If P6 cannot deterministically resolve sufficiency provenance from existing governed records/contracts, then:

STOP and request Main Project review.

Do not fabricate sufficiency authority.

Do not infer missing analytical purpose from a ValidatedResult.

---

# PART E — METRIC STATE AND ADMISSIBILITY

## 16. MetricState.VALID

A ValidatedResult with `MetricState.VALID` may become Admissible Evidence only when all P6 admissibility checks pass, including Required Evidence, sufficiency, provenance, scope, Metric authority, validation authority, and intended-use compatibility.

`MetricState.VALID` alone is insufficient.

## 17. MetricState.QUALIFIED

The Frozen Evidence Contract permits Qualified admissibility only when the core evidence chain is complete and validated, and a non-blocking assumption, limitation, or non-material gap constrains interpretation or generalization.

For P6-001, a `MetricState.QUALIFIED` ValidatedResult may become Admissible Evidence only when all of the following are deterministically established:

- the Metric Dictionary identifies the issue as qualifying rather than blocking;
- P5 validation passed for the governed qualified state;
- the associated qualification is persisted or otherwise authoritative;
- the qualification is linked to the affected Metric/result/scope;
- the Required Evidence requirement permits the narrowed qualified evidence role; and
- the intended claim type and analytical purpose do not require the missing or constrained evidence as blocking.

If exact admissibility semantics for a specific `MetricState.QUALIFIED` Revenue, Orders, or AOV case are not determined by Frozen authority and current governed context:

STOP and request Main Project review.

Do not use qualification to rescue failed validation or missing Required Evidence.

## 18. MetricState.UNDEFINED

Undefined is not validation failure.

For P6-001, the only currently governed Undefined behavior in scope is:

AOV Undefined because Orders = 0.

An AOV ValidatedResult with `MetricState.UNDEFINED`, `value = None`, and `undefined_reason = orders_equals_zero` may become Admissible Evidence only for the bounded descriptive proposition that AOV is undefined for the governed scope and period because Orders equals zero.

It must not become evidence for:

- AOV equals zero;
- a numeric AOV value;
- Revenue Change;
- Revenue Change Percentage;
- Product/Category claims;
- predictive claims;
- causal claims; or
- prescriptive claims.

If `MetricState.UNDEFINED` appears for Revenue or Orders in this narrow slice:

fail closed unless Frozen authority has explicitly defined that undefined state for the exact Metric and context.

If Frozen authority does not determine whether a specific Undefined state may satisfy the intended Required Evidence role:

STOP and request Main Project review.

## 19. MetricState.INADMISSIBLE

A ValidatedResult with `MetricState.INADMISSIBLE` must not become Admissible Evidence.

If such an object exists, P6 must treat it as a fail-closed condition and preserve a deterministic reason/code.

Do not create a successful AdmissibleEvidence object.

---

# PART F — DETERMINISTIC ADMISSIBILITY EVALUATOR

## 20. Evaluator Boundary

P6-001 must implement, when later authorized, deterministic software that evaluates whether a persisted ValidatedResult satisfies a specific Required Evidence role for the governed analytical purpose.

The evaluator is not:

- ClaimDecision;
- a generic Evidence engine;
- a policy DSL;
- a plugin framework;
- a rules engine dependency;
- an LLM judge;
- a report renderer; or
- a generic claim-understanding system.

The implementation must remain the smallest governed admissibility slice needed for Revenue, Orders, and AOV.

## 21. Required Checks

For each admissibility evaluation, apply deterministic checks for:

1. Required Evidence requirement existence.
2. Required Evidence requirement linkage to Business Question / analytical purpose.
3. Required Evidence requirement linkage to Metric ID and Metric definition version.
4. Intended claim type compatibility where material.
5. Data Sufficiency linkage and eligible disposition.
6. ValidatedResult artifact authenticity.
7. ValidationRecord bundle completeness and pass status.
8. Validation fingerprint match.
9. ExecutedResult and ExecutionRecord lineage.
10. Canonical dataset identity and fingerprint.
11. Population identity and fingerprint.
12. Period and period-role match where applicable.
13. Currency compatibility where applicable.
14. MetricState admissibility behavior.
15. Required qualifications/limitations retained where applicable.
16. Absence of blocking failure details or contradictions.

All material checks must pass for successful AdmissibleEvidence.

Any missing, failed, unresolved, or ambiguous material check fails closed.

## 22. Failure Codes

P6 implementation must define exact deterministic failure codes.

Minimum failure-code categories:

- `missing_required_evidence`
- `required_evidence_context_missing`
- `required_evidence_metric_mismatch`
- `claim_type_unsupported_for_evidence`
- `sufficiency_record_missing`
- `sufficiency_context_mismatch`
- `sufficiency_not_eligible`
- `validated_result_artifact_missing`
- `validated_result_artifact_hash_mismatch`
- `validated_result_schema_invalid`
- `validated_result_metadata_missing`
- `validation_bundle_incomplete`
- `validation_record_failed`
- `validation_fingerprint_mismatch`
- `executed_result_lineage_missing`
- `execution_record_lineage_missing`
- `metric_definition_mismatch`
- `dataset_mismatch`
- `population_mismatch`
- `period_mismatch`
- `currency_mismatch`
- `metric_state_not_admissible`
- `undefined_state_context_mismatch`
- `qualification_authority_missing`
- `blocking_limitation_present`
- `admissibility_grain_ambiguous`
- `frozen_authority_ambiguous`

Codes may be refined during implementation, but each failed evaluation must expose one deterministic primary code and a human-readable reason.

---

# PART G — ADMISSIBILITY RECORD

## 23. AdmissibilityRecord

P6-001 must introduce the minimum deterministic admissibility evaluation record required to preserve traceability.

Reuse existing Architecture contracts where governed.

Do not create duplicate lifecycle authorities.

An admissibility record should capture, at minimum:

- admissibility event ID;
- Required Evidence requirement ID/reference;
- ValidatedResult ID/reference;
- ValidatedResult artifact reference;
- ValidationRecord IDs/references;
- validation fingerprint;
- ExecutedResult ID/reference;
- ExecutionRecord ID/reference;
- Metric ID;
- Metric definition version;
- Business Question / analytical purpose reference;
- intended claim type when applicable;
- dataset/canonical dataset reference and fingerprint;
- population reference and fingerprint;
- period reference and role where applicable;
- currency where applicable;
- admissibility evaluator ID/version;
- checks performed;
- disposition;
- exact failure reason/code;
- qualifications and limitations retained where applicable;
- started_at;
- ended_at; and
- admitted Evidence artifact/reference when successful.

Do not add ClaimDecision fields.

Do not add Finding fields.

Do not add Recommendation fields.

## 24. Event Identity and Semantic Fingerprint

Admissibility evaluation is an event.

Use a generated unique admissibility event ID.

Repeated equivalent evaluations may have distinct IDs and timestamps.

If semantic Evidence equivalence requires a stable fingerprint, use a separate deterministic content-derived fingerprint based on the governed admissibility inputs and outcome.

Do not conflate event identity with semantic identity.

If Frozen authority does not determine evidence fingerprint semantics sufficiently for a material implementation decision:

STOP and request Main Project review.

---

# PART H — ADMISSIBLE EVIDENCE OBJECT

## 25. AdmissibleEvidence

P6-001 must reuse the existing `AdmissibleEvidence` contract where governed by the Frozen Architecture.

Do not invent a competing schema.

If the existing contract lacks fields required to preserve governed traceability, extend it only within the P6 scope and only when the extension is a direct implementation of Frozen Architecture and Evidence Contract requirements.

AdmissibleEvidence must remain traceably linked to:

Required Evidence requirement
↓
ValidatedResult
↓
ValidationRecords
↓
ExecutedResult
↓
ExecutionRecord
↓
Metric Reference
↓
canonical dataset
↓
population
↓
Business Question / analytical purpose

Successful AdmissibleEvidence must capture or reference:

- evidence ID;
- Required Evidence requirement/reference;
- ValidatedResult reference;
- Metric identity/version;
- dataset/canonical dataset reference;
- supported claim type if applicable;
- governed scope;
- assumptions;
- limitations;
- qualifications; and
- artifact/reference identity.

AdmissibleEvidence must NOT imply:

- claim is supported;
- claim is authorized;
- Finding is approved;
- Recommendation is permitted;
- causal inference is supported;
- predictive inference is supported; or
- prescriptive action is justified.

Those remain later lifecycle stages.

---

# PART I — PERSISTENCE

## 26. Durable Evidence Admissibility Records

Follow the existing local-first persistence architecture.

If P6 requires persistence, use:

AdmissibilityRecord
→
MetadataStore

Successful AdmissibleEvidence
→
immutable JSON-compatible ArtifactStore artifact

Metadata must link:

Required Evidence requirement
→
ValidatedResult artifact
→
ValidationRecords
→
ExecutedResult
→
ExecutionRecord
→
AdmissibilityRecord
→
AdmissibleEvidence artifact when successful

Failed admissibility must be durably traceable where governed and must produce no successful AdmissibleEvidence artifact.

## 27. Metadata Schema

Current MetadataStore schema version:

4

If MetadataStore schema expansion is required:

use version 5.

Preserve existing migration discipline:

- validate source schema;
- migrate transactionally;
- verify target schema;
- update schema_version only after verification;
- preserve Phase 1/2/P3/P4/P5 metadata;
- malformed legacy schema fails closed.

Do not use SQLAlchemy or Alembic.

Do not create Claim tables.

Do not create Benchmark tables.

Do not create Recommendation tables.

Do not create external-executor tables.

If required persistence grain cannot be determined from Frozen authority:

STOP and request Main Project review.

---

# PART J — REPRODUCIBILITY

## 28. Deterministic Reproducibility

Given equivalent:

- Business Question / analytical purpose;
- intended claim type where applicable;
- Required Evidence requirement;
- Data Sufficiency authority;
- canonical dataset;
- Metric definition/version;
- population;
- period;
- persisted ValidatedResult;
- ValidationRecord bundle;
- validation fingerprint;
- admissibility evaluator version; and
- material qualifications/limitations;

the admissibility disposition must be materially equivalent.

Event IDs and timestamps may differ.

If a semantic admissibility fingerprint is implemented, it must be stable for equivalent governed inputs and outcomes.

---

# PART K — REQUIRED TESTS

## 29. Test Scope

P6-001 tests must cover only Evidence admissibility for:

- Revenue;
- Orders; and
- AOV.

Do not add tests for Revenue Change, Product Metrics, Category Metrics, Contribution, rankings, ClaimDecision, Findings, Recommendations, MCP, external executor adapters, Wren, `SKILL.md`, or UI.

Only include tests whose expected outcome can be made authoritative from Frozen contracts.

If an expected disposition is ambiguous:

do not guess;

mark it as requiring Main Project review.

## 30. Required Positive Tests

At minimum, where supported by Frozen semantics:

1. Authentic persisted Revenue ValidatedResult satisfying Required Evidence becomes AdmissibleEvidence for bounded descriptive Revenue evidence.
2. Authentic persisted Orders ValidatedResult satisfying Required Evidence becomes AdmissibleEvidence for bounded descriptive Orders evidence.
3. Authentic persisted AOV ValidatedResult with Orders > 0 satisfying Required Evidence becomes AdmissibleEvidence for bounded descriptive AOV evidence.
4. Authentic persisted AOV Undefined ValidatedResult with Orders = 0 becomes AdmissibleEvidence only for the bounded proposition that AOV is undefined because Orders equals zero, if Frozen authority and current contracts deterministically support this.
5. Repeated equivalent admissibility evaluations produce materially equivalent dispositions while preserving distinct event IDs.
6. Persisted round-trip maintains complete lineage from AdmissibleEvidence to Required Evidence, ValidatedResult, ValidationRecords, ExecutedResult, ExecutionRecord, Metric, dataset, population, and period.

## 31. Required Fail-Closed Tests

At minimum, where supported by Frozen semantics:

1. Numerically valid but wrong Metric for Required Evidence fails closed.
2. Wrong period fails closed.
3. Wrong population fails closed.
4. Missing Required Evidence reference/context fails closed.
5. Data Sufficiency unsatisfied fails closed.
6. Missing Data Sufficiency authority fails closed unless a Frozen-governed persisted authority exists.
7. Tampered ValidatedResult artifact fails closed.
8. Schema-invalid ValidatedResult artifact fails closed.
9. Missing ValidatedResult metadata linkage fails closed.
10. Incomplete validation bundle fails closed.
11. Failed validation record in the required bundle fails closed.
12. Validation fingerprint mismatch fails closed.
13. ExecutedResult lineage mismatch fails closed.
14. ExecutionRecord lineage mismatch fails closed.
15. Wrong intended claim type where material fails closed.
16. Unsupported causal use of descriptive Evidence fails closed.
17. Unsupported predictive use of descriptive Evidence fails closed.
18. Unsupported prescriptive use of descriptive Evidence fails closed.
19. AOV Undefined used as AOV zero fails closed.
20. AOV Undefined used as numeric AOV evidence fails closed.
21. Failed admissibility produces no successful AdmissibleEvidence artifact.

## 32. Persistence Tests

At minimum:

- successful AdmissibilityRecord persists;
- failed AdmissibilityRecord persists where governed;
- successful AdmissibleEvidence artifact persists immutably;
- AdmissibleEvidence artifact tamper detection fails closed;
- failed admissibility creates no successful AdmissibleEvidence;
- repeated evaluation events persist separately;
- semantic fingerprint, if implemented, remains stable for equivalent governed inputs;
- old schema version 4 metadata survives migration to version 5 if schema expansion is required;
- malformed legacy admissibility schema fails closed if migration is required.

## 33. Regression Gate

All existing Phase 1, Phase 2, P3-001, P4-001, and P5-001 tests must remain passing.

Do not weaken them.

## 34. One Authoritative Outcome

Preserve Evaluation Fixture governance:

ONE FIXTURE VARIANT
=
ONE AUTHORITATIVE EXPECTED OUTCOME

Do not write P6 acceptance tests with outcomes such as:

- PASS or QUALIFIED
- "if material"
- "as applicable"
- evaluator-dependent alternatives

Every authorized test fixture must have one deterministic material disposition.

---

# PART L — FAILURE BEHAVIOR

## 35. Fail Closed

Material admissibility failure must:

- fail closed;
- persist the deterministic admissibility evaluation/failure record where governed;
- produce NO successful AdmissibleEvidence object;
- preserve exact reason/code;
- never fabricate missing Required Evidence;
- never downgrade failed requirements merely to continue;
- never infer analytical purpose from result shape alone;
- never treat validation success as business-question-level sufficiency; and
- never authorize a Claim, Finding, or Recommendation.

The canonical user-facing semantic remains:

Insufficient evidence to conclude

when material Required Evidence is unavailable or inadmissible for the intended conclusion.

P6 itself does NOT implement final natural-language rendering.

---

# PART M — EXPLICITLY OUT OF SCOPE

## 36. Not Authorized

P6-001 does NOT authorize:

- ClaimDecision;
- claim admissibility;
- Findings;
- Alternative Explanations;
- Recommendations;
- Revenue Change;
- Revenue Change Percentage;
- Product Metrics;
- Category Metrics;
- Contribution;
- rankings;
- predictive analysis;
- causal analysis implementation;
- prescriptive recommendation engine;
- Benchmark scoring;
- H-001;
- MCP;
- generic ExecutorAdapter;
- external executor;
- Wren;
- `SKILL.md`;
- UI;
- RAG;
- vector database;
- multi-agent runtime.

## 37. No Architecture Expansion

Do not add:

- generic Evidence engine;
- policy DSL;
- plugin architecture;
- generic rule framework;
- network service;
- multi-agent system;
- RAG;
- vector database;
- external execution boundary.

If the Frozen Architecture already defines a generic interface, reuse it without expanding it.

Implement only the smallest governed admissibility slice needed for Revenue / Orders / AOV.

---

# PART N — DEPENDENCIES

## 38. Dependencies

Expected new dependencies:

NONE.

Use:

- Python stdlib;
- existing Pydantic;
- existing MetadataStore;
- existing ArtifactStore;
- existing CommerceLens contracts and deterministic authorities.

Do not add a policy/rule framework dependency.

A new dependency requires Main Project authorization.

---

# PART O — CONDITIONS REQUIRING MAIN PROJECT REVIEW

## 39. STOP Conditions

STOP and request Main Project review if any of the following are unresolved by Frozen authority or current governed contracts:

- exact Required Evidence requirements for the intended P6 analytical purpose;
- exact admissibility semantics for `MetricState.QUALIFIED`;
- exact admissibility semantics for `MetricState.UNDEFINED`;
- intended claim-type requirement;
- whether one ValidatedResult can satisfy multiple Required Evidence requirements;
- whether admissibility is per result, per requirement, per claim context, or another governed grain;
- required persistence grain;
- evidence fingerprint semantics;
- Evidence contract fields required by Frozen Architecture;
- whether P5 currently persists enough Data Sufficiency / analytical-purpose authority;
- whether the current `AdmissibleEvidence` contract can carry all required traceability without semantic loss;
- any need to modify Frozen specs;
- any need for a new dependency;
- any need for ClaimDecision to complete P6;
- any need to implement Revenue Change;
- any need to implement external executor/MCP/Wren behavior.

Do not resolve these by implementation convenience.

---

# PART P — DEFINITION OF DONE

## 40. P6-001 Complete Only When

P6-001 may be considered implementation-complete only when, within the exact Frozen scope:

- authentic persisted ValidatedResult is consumed;
- Required Evidence authority is resolved;
- Data Sufficiency authority is preserved;
- deterministic admissibility checks are applied;
- admissible vs inadmissible disposition is reproducible;
- successful AdmissibleEvidence is durably traceable;
- failed admissibility is durably traceable where governed;
- MetricState Valid, Qualified, Undefined, and Inadmissible behavior follows Frozen authority;
- no claim authorization is implied;
- unsupported analytical use fails closed;
- unsupported causal/predictive/prescriptive use fails closed;
- all new targeted P6 tests pass;
- all prior Phase 1-P5 tests remain passing;
- no dependency/frozen scope expansion occurs.

---

# PART Q — REQUIRED FUTURE IMPLEMENTATION REPORT

## 41. Future Report

When P6-001 is later implemented, report:

A. Files created / modified

B. Exact Evidence admissibility grain

C. Required Evidence authority

D. Data Sufficiency authority

E. ValidatedResult authenticity mechanism

F. Admissibility evaluator design

G. Metric-state admissibility behavior

H. Claim-type context behavior

I. Admissibility failure codes

J. Evidence/admissibility record design

K. Admissible Evidence object design

L. Event identity/fingerprint behavior

M. Persistence/schema changes

N. Migration behavior

O. Tests added / modified

P. Exact targeted result

Q. Exact persistence/migration result

R. Exact P5 regression result

S. Exact full-suite result

T. `git diff --check`

U. Dependencies changed

V. Existing tests modified and reason

W. Known limitations

X. Frozen ambiguities/conflicts

Y. ClaimDecision implemented

Expected:
NO

Z. Revenue Change implemented

Expected:
NO

AA. MCP / external executor / Wren implemented

Expected:
NO

Then STOP.

---

# PART R — STOP BOUNDARY

## 42. Stop Boundary

After future P6-001 implementation:

STOP.

Do NOT automatically begin:

- ClaimDecision;
- Findings;
- Recommendations;
- Revenue Change;
- H-001;
- MCP;
- external executor;
- Wren;
- `SKILL.md`;
- UI.

Wait for Main Project Review.
