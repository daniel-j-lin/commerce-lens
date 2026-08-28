# P5-001 — Revenue, Orders, and AOV Deterministic Result Validation

## Status

AUTHORIZED SPECIFICATION

IMPLEMENTATION NOT YET STARTED

---

## 1. Purpose

P5-001 implements the first deterministic result-validation slice on top of the Approved / Frozen CommerceLens execution foundation.

Approved project state before this task:

Phase 1:
APPROVED / FROZEN

Phase 2:
APPROVED / FROZEN

P3-001:
APPROVED / FROZEN

P4-001:
APPROVED / FROZEN

P4-001 provides:

Metric Registry
↓
Governed Population Definitions
↓
Data Sufficiency
↓
ExecutionPlan
↓
chain-level execution authorization
↓
direct DuckDB reference execution
↓
ExecutionRecord
↓
ExecutedResult
↓
durable persistence

P5-001 continues:

Persisted ExecutedResult
+
ExecutionRecord
+
governed execution context
↓
Deterministic Validation
↓
ValidationRecord
↓
ValidatedResult
↓
STOP

P5-001 does NOT implement:

Admissible Evidence
Claim admissibility
Findings
Recommendations

ValidatedResult
≠
Admissible Evidence

---

## 2. Strategic Role

CommerceLens is an Evidence Reliability Kernel.

Execution alone is insufficient.

The system must deterministically establish whether an ExecutedResult satisfies the governed Metric, population, provenance, numerical, lifecycle, and reproducibility contracts before later analytical Evidence may rely on it.

P5-001 establishes the first:

ExecutedResult
→
ValidatedResult

reference path.

This path becomes part of the future reference baseline used to evaluate any external executor or MCP feasibility experiment.

Do NOT implement external executor abstraction here.

---

## 3. Governing Principle

> No material claim without traceable evidence.

And specifically for P5-001:

> An ExecutedResult is not a ValidatedResult merely because execution completed successfully.

Validation must be deterministic.

The Skill / LLM must not self-authorize validation.

---

## 4. Governing Documents

P5-001 is subordinate to the Approved / Frozen specifications under:

docs/frozen/

Especially:

- PROJECT_MASTER_INSTRUCTIONS.md
- PRD.md
- SKILL_SCOPE_SPECIFICATION.md
- EVIDENCE_CONTRACT_SPECIFICATION.md
- CANONICAL_DATASET_AND_METRIC_DICTIONARY.md
- EVALUATION_FIXTURES_SPECIFICATION.md
- ARCHITECTURE_SPECIFICATION.md

Also preserve all Approved / Frozen P3-001 and P4-001 contracts.

If Frozen authority does not provide enough information to deterministically validate a material property:

STOP and request Main Project review.

Do not invent validation semantics.

---

# PART A — AUTHORIZED VALIDATION SCOPE

## 5. Metrics

P5-001 may validate ONLY ExecutedResults for:

- revenue
- orders
- aov

No execution or validation is authorized for:

- revenue_change
- revenue_change_pct
- product metrics
- category metrics
- contribution
- rankings

---

## 6. Lifecycle Scope

Authorized lifecycle:

ExecutionRecord
+
ExecutedResult
↓
ValidationRecord
↓
ValidatedResult
↓
STOP

Explicitly out of scope:

ValidatedResult
→
AdmissibleEvidence

and everything after Evidence admissibility.

---

# PART B — VALIDATION AUTHORITY

## 7. No Validation by Assertion

A completed ExecutionRecord is NOT sufficient proof of correctness.

Validation must independently verify all applicable governed properties.

Do not implement:

validated = execution_status == completed

Do not implement:

validated = tests_passed

Do not trust fields merely because they exist in ExecutedResult.

---

## 8. Deterministic Validator

The validator must be deterministic software.

No LLM judgment may decide:

- whether a numeric result is correct;
- whether provenance matches;
- whether a result type is valid;
- whether a population is valid;
- whether reconciliation passes;
- whether a result is ValidatedResult.

---

# PART C — INPUT INTEGRITY VALIDATION

## 9. ExecutionRecord / ExecutedResult Linkage

Before Metric-specific validation, confirm:

- ExecutionRecord exists;
- ExecutedResult exists where validation requires a completed result;
- ExecutedResult.execution_id matches the ExecutionRecord;
- Metric ID matches;
- Metric definition version matches;
- plan/node identity matches;
- canonical dataset identity/fingerprint matches;
- population identity/fingerprint matches;
- implementation ref matches;
- result artifact identity matches persisted metadata;
- persisted artifact content hash / fingerprint matches expected immutable artifact identity.

Any material mismatch:

VALIDATION FAILURE.

Do not silently repair provenance.

---

## 10. Execution Status

Only a successfully completed execution with a valid ExecutedResult may proceed to normal value validation.

A failed ExecutionRecord:

must not become ValidatedResult.

A blocked PlanMetricNode:

has no execution result and therefore must not produce a fake validation success.

A deterministic Undefined Metric such as AOV when Orders = 0 is different:

execution may be completed
and
MetricState = Undefined

That may be a valid analytical result state if all applicable validation checks pass.

---

# PART D — METRIC AUTHORITY VALIDATION

## 11. Registry Authority

Validation must resolve the authoritative Metric definition from the Approved Metric Registry.

Validate:

- Metric ID;
- Metric definition version;
- approved implementation binding where relevant;
- dependency structure;
- governed result type/state requirements.

Do not create a validation-only Metric Registry.

---

## 12. Population Authority

Recompute and verify the authoritative PopulationDefinition semantic fingerprint.

Confirm:

- population ID;
- population fingerprint;
- period;
- scope filters;
- grouping;
- currency basis

match the governed ExecutionPlan / ExecutionRecord.

A stale or tampered population:

VALIDATION FAILURE.

Do not validate a value against a different population.

---

## 13. Canonical Dataset Integrity

Validation must verify the canonical dataset artifact/reference used during execution still matches its governed:

- dataset ID;
- artifact reference;
- fingerprint;
- schema/version where applicable.

Do not validate against raw source data directly.

Do not silently regenerate a different canonical dataset and treat it as the same execution evidence.

---

# PART E — VALUE VALIDATION

## 14. Revenue

For a Revenue ExecutedResult, deterministically verify:

- Metric state is governed for the observed condition;
- authoritative value type is Decimal;
- no float authority;
- currency is the governed resolved currency;
- precision metadata is valid;
- result corresponds to governed eligible line_revenue population;
- Revenue = 0 empty-population semantics remain valid where applicable.

Validation must not simply trust the original Revenue ExecutedResult value.

Use an independently defined deterministic validation operation sufficient to establish correctness.

Do not call the production execution function and declare its own output valid merely because it reproduces itself.

If an independent validation query/check is required, keep it narrow and Metric-specific.

---

## 15. Orders

For Orders, deterministically verify:

- exact integer type;
- non-negative governed count;
- distinct eligible order_id semantics;
- multi-line orders reconcile to one Order;
- zero Orders remains valid where governed;
- no float/Decimal fractional Orders authority.

Again, do not validate only by checking Python type.

The numeric value must be independently supported by governed canonical data.

---

## 16. AOV

AOV validation must verify its dependency relationship.

For Orders > 0:

Validated AOV must equal the governed Decimal calculation:

validated Revenue / validated Orders

using the Approved P4 AOV Decimal Calculation Policy.

Validation must confirm:

- Revenue dependency is itself valid for validation;
- Orders dependency is itself valid for validation;
- same population;
- same period;
- same governed currency basis;
- correct Decimal calculation policy;
- no float authority.

Do not validate AOV against unvalidated dependency values without explicit governed justification.

---

## 17. AOV Undefined

For Orders = 0:

AOV must validate as:

MetricState.UNDEFINED

with:

value = None

and governed:

undefined_reason = orders_equals_zero

and the resolved governed currency where applicable.

Validation must reject:

- AOV = 0;
- NaN;
- Infinity;
- arbitrary null without governed Undefined state;
- Undefined with Orders > 0.

---

# PART F — INDEPENDENT VALIDATION DESIGN

## 18. Avoid Circular Validation

The validation implementation must not merely invoke the same P4 executor implementation and compare the result to itself.

Validation must provide a materially independent deterministic check.

Examples of acceptable validation structure may include, if consistent with Frozen authority:

- separate fixed validation SQL;
- independent reconciliation query;
- deterministic aggregate cross-check;
- dependency arithmetic validation;
- invariant validation.

Do NOT create a second generic analytics engine.

Do NOT duplicate the full execution architecture.

Use the smallest independent validation mechanism required.

---

## 19. Revenue Validation Operation

For Revenue, validation should independently establish the governed aggregate from canonical data.

If DuckDB is used, use a validation-specific fixed operation/query rather than calling the P4 Revenue execution function.

Capture the validation operation in ValidationRecord.

---

## 20. Orders Validation Operation

Independently establish the governed distinct Order count.

Capture the validation method/query.

---

## 21. AOV Validation Operation

AOV should be validated primarily through validated dependencies and deterministic Decimal arithmetic.

Do not independently query a materially different AOV population.

---

# PART G — VALIDATION STATES

## 22. Validation Success

A ValidatedResult may be produced only when all applicable material validation checks pass.

---

## 23. Validation Failure

If a material validation check fails:

- create deterministic ValidationRecord;
- do NOT produce successful ValidatedResult;
- preserve exact failure reason/code;
- do NOT downgrade failure into Qualified merely to continue.

Qualification cannot bypass failed validation.

---

## 24. Undefined Is Not Validation Failure

AOV Undefined because Orders = 0 may be a successfully validated result.

Therefore distinguish:

MetricState.UNDEFINED

from:

validation failure.

Do not collapse lifecycle states.

---

# PART H — VALIDATION RECORD

## 25. ValidationRecord

Reuse existing Architecture contract if already defined.

Do not create duplicate lifecycle authority.

ValidationRecord should capture at minimum where governed:

- validation ID;
- execution ID;
- ExecutedResult ID;
- result fingerprint;
- Metric ID/version;
- plan/node identity;
- canonical dataset identity/fingerprint;
- population identity/fingerprint;
- validator identity/version;
- validation operation/method;
- validation checks performed;
- expected/recomputed value where appropriate;
- actual ExecutedResult value/state;
- validation status;
- failure code/details;
- started_at;
- ended_at;
- validated result linkage where successful.

Do not add Evidence or Claim fields.

---

# PART I — VALIDATED RESULT

## 26. ValidatedResult

ValidatedResult represents a deterministically validated ExecutedResult.

It must retain linkage to:

- source ExecutedResult;
- ExecutionRecord;
- ValidationRecord;
- Metric identity/version;
- canonical dataset;
- population;
- governed value/state;
- currency;
- precision/calculation policy where relevant;
- validation fingerprint if governed.

ValidatedResult must NOT imply:

AdmissibleEvidence
Claim support
Recommendation permission.

---

## 27. Event Identity

ValidationRecord is an event.

Use a generated unique validation event ID.

Repeated validation attempts may have distinct validation IDs/timestamps.

If deterministic validation-result equivalence requires a stable fingerprint, use a separate content-derived fingerprint.

Do not conflate event identity with semantic identity.

---

# PART J — PERSISTENCE

## 28. Durable Validation Evidence

P5-001 must persist validation evidence in the approved local-first architecture.

Minimum:

ValidationRecord
→ MetadataStore

ValidatedResult
→ immutable JSON-compatible ArtifactStore artifact

Metadata must link:

ExecutionRecord
→ ExecutedResult
→ ValidationRecord
→ ValidatedResult artifact

Do not implement Evidence persistence yet.

---

## 29. Metadata Schema

If MetadataStore schema expansion is required:

use the next explicit schema version.

Preserve existing migration discipline:

- validate source schema;
- migrate transactionally;
- verify target schema;
- update schema_version only after verification;
- preserve Phase 1/2/P4 metadata;
- malformed legacy schema fails closed.

Do not use SQLAlchemy or Alembic.

Do not add Evidence/Claim tables.

---

# PART K — REPRODUCIBILITY

## 30. Deterministic Validation

Given equivalent:

- canonical dataset;
- Metric definition/version;
- population;
- ExecutionRecord material provenance;
- ExecutedResult material content;
- validator version;

validation disposition must be materially equivalent.

Event IDs/timestamps may differ.

---

# PART L — REQUIRED TESTS

## 31. Revenue Validation Tests

At minimum:

1. correct Revenue passes;
2. tampered Revenue value fails;
3. Decimal type preserved;
4. float Revenue fails;
5. wrong currency fails;
6. stale population fingerprint fails;
7. wrong canonical dataset fingerprint fails;
8. empty complete Revenue zero validates;
9. persisted ExecutedResult round-trip validates;
10. mismatched execution/result linkage fails.

---

## 32. Orders Validation Tests

At minimum:

1. correct Orders passes;
2. tampered Orders count fails;
3. multi-line order distinct-count validation;
4. zero Orders validates;
5. float Orders fails;
6. negative Orders fails;
7. population mismatch fails;
8. dataset mismatch fails.

---

## 33. AOV Validation Tests

At minimum:

1. correct AOV passes;
2. tampered AOV fails;
3. validated Revenue / Orders dependency arithmetic matches;
4. ambient Decimal context cannot alter validation;
5. wrong calculation-policy metadata fails;
6. Orders = 0 + Undefined passes;
7. Orders = 0 + AOV zero fails;
8. Orders > 0 + Undefined fails;
9. currency mismatch fails;
10. dependency population mismatch fails.

---

## 34. Provenance Tampering Tests

At minimum fail closed on tampered:

- execution_id linkage;
- result_id;
- Metric version;
- implementation ref;
- dataset fingerprint;
- population fingerprint;
- result fingerprint;
- immutable artifact content/hash.

Do not silently repair any field.

---

## 35. Persistence Tests

At minimum:

- successful ValidationRecord persists;
- failed ValidationRecord persists;
- ValidatedResult artifact persists;
- valid Decimal Revenue round-trips;
- Undefined AOV round-trips;
- repeated validation events persist separately;
- old P4 execution metadata survives schema migration;
- malformed legacy validation schema fails closed.

---

## 36. Regression Gate

All existing:

Phase 1
Phase 2
P3-001
P4-001

tests must remain passing.

Do not weaken them.

---

# PART M — EXPLICITLY OUT OF SCOPE

## 37. Not Authorized

P5-001 does NOT authorize:

- Revenue Change execution;
- Revenue Change validation;
- Product Metrics;
- Category Metrics;
- Contribution;
- rankings;
- Evidence admissibility;
- AdmissibleEvidence;
- claim admissibility;
- ClaimDecision;
- Findings;
- Alternative Explanations;
- Recommendations;
- Benchmark scoring;
- MCP;
- generic ExecutorAdapter;
- external executor;
- Wren;
- SKILL.md;
- UI.

---

## 38. No Architecture Expansion

Do not add:

- generic validation framework;
- plugin framework;
- validation DSL;
- semantic query language;
- generic rule engine;
- multi-agent system;
- RAG;
- vector database;
- network service.

Implement only the smallest deterministic Revenue / Orders / AOV validation slice.

---

# PART N — DEPENDENCIES

## 39. Dependencies

Expected new dependencies:

NONE.

Use:

- Python stdlib;
- existing DuckDB;
- existing Pydantic;
- existing MetadataStore;
- existing ArtifactStore.

A new dependency requires Main Project authorization.

---

# PART O — DEFINITION OF DONE

## 40. P5-001 Complete Only When

- Revenue ExecutedResult is independently deterministically validated;
- Orders ExecutedResult is independently deterministically validated;
- AOV is validated from validated dependencies;
- AOV Undefined is validated correctly;
- provenance and linkage integrity are checked;
- tampered values/provenance fail closed;
- ValidationRecord exists and persists;
- successful ValidatedResult exists and persists;
- failed validation does not create successful ValidatedResult;
- event identity and timestamps are correct;
- validation is reproducible;
- no Evidence / Claim authority is introduced;
- all existing and new tests pass.

---

## 41. Conditions Requiring Main Project Review

STOP if:

- Frozen specifications do not define a material validation requirement sufficiently;
- independent deterministic Revenue/Orders validation cannot be performed without changing Metric semantics;
- P4 persisted artifacts lack required validation inputs;
- validation requires modifying Frozen Metric definitions;
- exact Decimal validation cannot be preserved;
- an Architecture Amendment appears necessary;
- a new dependency appears necessary;
- Evidence admissibility must be implemented to complete validation;
- external executor abstraction appears necessary.

Do not guess.

---

## 42. Required Future Implementation Report

When P5-001 is later implemented, report:

A. Files created / modified

B. Revenue validation design

C. Orders validation design

D. AOV validation design

E. Independence from P4 execution implementation

F. Input/provenance integrity checks

G. ValidationRecord behavior

H. ValidatedResult behavior

I. Validation event IDs/fingerprints

J. Persistence/schema changes

K. Validation failure behavior

L. Undefined AOV validation behavior

M. Tests added / modified

N. Exact baseline suite result

O. Exact targeted validation test result

P. Exact persistence/migration result

Q. Exact full-suite result

R. git diff --check

S. Dependencies changed

T. Existing tests modified and reasons

U. Known limitations

V. Frozen conflicts/ambiguities

W. Evidence admissibility implemented

Expected:
NO

X. Revenue Change implemented

Expected:
NO

Y. MCP / external executor / Wren implemented

Expected:
NO

Then STOP.

---

## 43. Likely Next Step After P5-001

If P5-001 passes Main Project Review, CommerceLens will possess:

Metric authority
→ governed population
→ sufficiency
→ execution plan
→ deterministic execution
→ persisted ExecutedResult
→ deterministic validation
→ persisted ValidatedResult

At that point Main Project should decide between:

1. implementing the narrow Evidence admissibility layer; or

2. running H-001 external executor feasibility against the complete execution + validation reference path.

That decision is NOT authorized by P5-001.

---

## 44. Stop Boundary

After P5-001 implementation:

STOP.

Do NOT automatically begin:

- Evidence admissibility;
- Claim policy;
- Revenue Change;
- external executor adapters;
- MCP;
- H-001;
- SKILL.md;
- UI.

Wait for Main Project Review.
