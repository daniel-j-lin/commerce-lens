# P4-001 — Revenue, Orders, and AOV Deterministic Reference Execution

## Status

AUTHORIZED SPECIFICATION

IMPLEMENTATION NOT YET STARTED

---

## 1. Purpose

P4-001 implements the first deterministic Metric execution slice on top of the Approved / Frozen CommerceLens pre-execution foundation.

The approved project state before this task is:

Phase 1:
APPROVED / FROZEN

Phase 2:
APPROVED / FROZEN

R-001 Wren Feasibility:
COMPLETED / CLOSED
Decision: KEEP DUCKDB

P3-001:
APPROVED / FROZEN

P3-001 provides:

Metric Registry
↓
Governed Population Definitions
↓
Data Sufficiency
↓
ExecutionPlan
↓
chain-level execution authorization

P4-001 continues:

Approved executable PlanMetricNode
↓
DuckDB deterministic execution
↓
ExecutionRecord
↓
ExecutedResult
↓
STOP

P4-001 does NOT perform deterministic result validation.

ExecutedResult
≠
ValidatedResult

---

## 2. Strategic Architecture Direction

CommerceLens is evolving toward:

Evidence Reliability Kernel
+
Evidence-first Agent
+
controlled deterministic executor boundary

However, P4-001 does NOT implement the future generic executor boundary.

For this slice:

DuckDB remains the single approved deterministic reference executor.

The purpose is to establish one correct, reproducible reference execution path that future external executor/tool feasibility experiments can be compared against.

Do NOT introduce:

- ExecutorAdapter;
- generic executor interfaces;
- MCP;
- external Skills;
- external services;
- Wren;
- plugin systems.

The future hybrid executor decision remains separate.

---

## 3. Governing Principle

> No material claim without traceable evidence.

P4-001 must preserve:

- deterministic execution;
- Metric Registry authority;
- governed population authority;
- Data Sufficiency gating;
- chain-level execution authorization;
- exact monetary semantics;
- reproducibility;
- execution provenance;
- fail-closed behavior;
- separation of execution from validation.

---

## 4. Governing Documents

This task is subordinate to the Approved / Frozen specifications under:

docs/frozen/

Especially:

- PROJECT_MASTER_INSTRUCTIONS.md
- PRD.md
- SKILL_SCOPE_SPECIFICATION.md
- EVIDENCE_CONTRACT_SPECIFICATION.md
- CANONICAL_DATASET_AND_METRIC_DICTIONARY.md
- EVALUATION_FIXTURES_SPECIFICATION.md
- ARCHITECTURE_SPECIFICATION.md

It is also subordinate to the Approved / Frozen P3-001 behavior already implemented.

If implementation convenience conflicts with Frozen semantics:

STOP and request Main Project review.

Do not reinterpret a Metric.

---

# PART A — AUTHORIZED METRICS

## 5. Metric Scope

P4-001 may execute ONLY:

- Revenue
- Orders
- AOV

Approved Metric IDs are the existing authoritative P3 Registry IDs:

- revenue
- orders
- aov

Do NOT execute any other Metric.

---

## 6. Explicitly Out-of-Scope Metrics

Do NOT implement execution for:

- Revenue Change
- Revenue Change Percentage
- Product Revenue
- Product Orders
- Product Revenue Change
- Product Revenue Change Percentage
- Category Revenue
- Category Orders
- Category Revenue Change
- Category Revenue Change Percentage
- Product Absolute Contribution
- Category Absolute Contribution
- Product Contribution Share
- Category Contribution Share
- positive contributor ranking
- negative contributor ranking.

Those remain later separately authorized slices.

---

# PART B — AUTHORITATIVE METRIC SEMANTICS

## 7. Revenue

Revenue must use the Frozen Metric Dictionary authority.

Conceptually:

Revenue
=
sum of authoritative line_revenue
over the governed eligible analytical population.

Requirements:

- execute only over the governed canonical population;
- monetary value authority is line_revenue;
- eligibility authority determines participation;
- a valid line_revenue does not override exclusion semantics;
- cancelled / fully refunded / otherwise ineligible rows remain excluded according to Frozen Phase 2 semantics;
- do not recompute Revenue from quantity × unit_price;
- unit_price is not Revenue authority;
- do not use raw source rows directly.

P4-001 must not redefine eligibility.

---

## 8. Orders

Orders must use the Frozen Metric Dictionary authority.

Conceptually:

Orders
=
distinct eligible order_id
with at least one eligible line
within the same governed analytical population.

Requirements:

- count distinct order_id;
- do NOT count order lines;
- multi-line orders count once;
- zero-value eligible orders still count;
- an order with no eligible line does not count;
- Revenue and Orders population semantics must remain aligned where required.

---

## 9. AOV

AOV must use the Frozen Metric Dictionary authority.

Conceptually:

AOV
=
Revenue / Orders

using the exact same governed:

- dataset;
- period;
- scope;
- eligibility basis;
- currency basis.

Requirements:

Orders > 0:
calculate exact governed AOV.

Orders = 0:
AOV is Undefined.

Do NOT:

- divide by zero;
- return infinity;
- return NaN as the governed Metric value;
- convert Undefined into zero;
- fabricate a numeric value.

AOV must depend on the executed Revenue and Orders results represented by the P3 dependency graph.

Do not independently re-query a materially different population for AOV.

---

# PART C — DECIMAL / NUMERICAL AUTHORITY

## 10. Exact Decimal Requirement

Material monetary Metrics must preserve exact Decimal semantics.

Revenue and AOV must never use binary floating point as their authoritative governed result representation.

Do not use Python float as the authoritative value.

Do not silently cast Decimal to double.

Do not round during calculation merely for display convenience.

Display rounding belongs later.

Use the existing canonical Decimal authority and the narrowest safe DuckDB representation consistent with the Frozen specification.

---

## 11. Orders Type

Orders is an exact integer count.

Do not represent Orders as:

- float;
- Decimal with fractional semantics;
- string as the authoritative value.

---

## 12. Null and Zero

Preserve:

Null
≠
Zero
≠
Undefined
≠
Missing

At minimum:

- zero line_revenue remains zero;
- missing required monetary data must not silently become zero;
- Revenue = 0 is a valid possible result when supported by a governed complete population;
- Orders = 0 is valid;
- Orders = 0 causes AOV Undefined.

Do not invent values.

---

# PART D — EXECUTION AUTHORIZATION

## 13. ExecutionPlan Authority

P4-001 must consume the Approved / Frozen P3 ExecutionPlan.

Do not construct a second planning path.

Only PlanMetricNodes marked executable by P3 chain-level execution authorization may execute.

Blocked nodes:

must NOT execute.

Do not treat the executor as permission to override Data Sufficiency.

---

## 14. Requested-Chain Authorization

The executor must preserve P3 semantics:

A node executable only because it belongs to at least one eligible requested Metric dependency closure may execute.

Nodes exclusive to blocked requested chains must not execute.

Do not recompute execution authorization independently unless required purely to verify the P3 contract.

The P3 plan remains authority.

---

## 15. Unsupported Metric Fail-Closed

If the executor receives a node for an unsupported P4-001 Metric:

FAIL CLOSED.

Do not:

- dynamically generate unknown SQL;
- fall back to generic Metric execution;
- guess a formula.

---

# PART E — GOVERNED POPULATION EXECUTION

## 16. Canonical Dataset Only

Execution must operate on the governed canonical dataset produced by Phase 2.

Do NOT query:

- original CSV directly;
- original Excel directly;
- original SQLite business tables directly.

The source-format differences must already have converged into canonical semantics before Metric execution.

This preserves CSV / Excel / SQLite conformance.

---

## 17. PopulationDefinition Authority

Every executed node must use its governed PopulationDefinition.

The executor must not:

- change period;
- change currency;
- add filters;
- remove filters;
- alter eligibility;
- alter scope;
- reinterpret grouping.

For P4-001 Revenue / Orders / AOV, execution is total-population execution only.

Product / Category grouped Metric execution remains out of scope.

---

## 18. Period Roles

P4-001 must be capable of executing approved Revenue / Orders / AOV nodes for the governed P3 period roles, including where structurally applicable:

- Baseline;
- Comparison.

This does NOT authorize:

Revenue Change.

It only means Revenue / Orders / AOV reference values may be executed independently for each authorized governed period node.

---

# PART F — DUCKDB REFERENCE EXECUTOR

## 19. DuckDB Responsibility

DuckDB is the approved deterministic computation engine for P4-001.

DuckDB may perform commodity operations such as:

- filtering;
- SUM;
- COUNT DISTINCT;
- governed relational operations necessary to execute the approved node.

CommerceLens remains authority for:

- Metric definition;
- population definition;
- execution authorization;
- required result type;
- precision policy;
- provenance requirements.

---

## 20. No Generic SQL Engine

Do not build:

- arbitrary Text-to-SQL;
- generic Metric compiler;
- generic semantic query language;
- user-provided SQL execution;
- LLM-generated SQL execution;
- general query builder framework.

Implement only the minimum deterministic execution required for:

Revenue
Orders
AOV.

---

## 21. SQL / Operation Traceability

Every material executed node must preserve the exact deterministic execution method.

Where DuckDB SQL is used, capture:

- exact SQL text or stable operation representation;
- parameters separately where parameterization is used;
- DuckDB version;
- Metric ID/version;
- population reference/fingerprint;
- canonical dataset reference/fingerprint;
- plan/node identity.

A future reviewer must be able to determine:

what was executed
against what
under which governed definition.

---

# PART G — EXECUTION RECORDS

## 22. Execution Lifecycle

Implement the Approved Architecture lifecycle boundary:

ExecutionPlan
↓
ExecutionRecord
↓
ExecutedResult

STOP before:

ValidationRecord
ValidatedResult
AdmissibleEvidence

Do not collapse these stages.

---

## 23. ExecutionRecord

Reuse existing Architecture contracts if they already exist structurally.

Do not create duplicate lifecycle models.

An ExecutionRecord must capture the minimum governed execution provenance required by Frozen Architecture / Evidence Contract.

Conceptually include where applicable:

- execution ID;
- plan ID/fingerprint;
- plan node ID;
- Metric ID;
- Metric definition version;
- canonical dataset reference/fingerprint;
- population reference/fingerprint;
- period role;
- executor ID;
- executor version;
- exact SQL / operation representation;
- execution status;
- error information;
- result reference where execution completed.

Do not add future Evidence admissibility fields.

---

## 24. ExecutedResult

ExecutedResult represents:

what the deterministic executor actually returned.

It is NOT:

ValidatedResult.

It must not claim:

- validation passed;
- Evidence admissible;
- Claim supported;
- Recommendation permitted.

For Revenue / Orders / AOV, the result must preserve appropriate governed type and state.

---

## 25. Undefined AOV

If Orders = 0:

the execution chain must represent AOV as Undefined using the existing governed MetricState / result-state semantics specified by Frozen architecture.

Do not represent it as an execution failure merely because no numeric AOV exists.

Distinguish:

successful execution that deterministically establishes Undefined

from:

execution failure.

Do not create a new state domain if existing contracts already support this.

---

# PART H — FAILURE BEHAVIOR

## 26. Execution Failures

If DuckDB execution fails:

record deterministic execution failure.

Do not fabricate ExecutedResult success.

Do not convert an exception to:

0
null
empty result
or Qualified result

unless explicitly governed.

---

## 27. Blocked Nodes

Blocked PlanMetricNode:

- must not invoke DuckDB;
- must not produce a fake ExecutedResult;
- remains a pre-execution blocked state.

---

## 28. Independent Nodes

Where multiple authorized Revenue / Orders / AOV nodes exist, execution behavior must remain deterministic.

Do not let a blocked node become executable.

Do not let execution of one node modify Metric semantics for another.

If the Architecture already defines partial execution behavior, follow it.

Do not invent a new run-level partial-failure model beyond current authority.

---

# PART I — REPRODUCIBILITY

## 29. Deterministic Reference Path

Equivalent governed:

- canonical dataset;
- Metric definition version;
- population;
- period;
- execution plan/node;
- DuckDB version;
- executor implementation version

must produce equivalent material ExecutedResult values.

Execution IDs / timestamps may differ where operationally appropriate, but must not alter semantic result identity.

---

## 30. Execution Fingerprints

Where the Approved Architecture already defines execution/result fingerprinting, use it.

If additional fingerprints are required, derive them only from material deterministic inputs.

Do not include nondeterministic timestamps in semantic fingerprints.

---

# PART J — TESTING

## 31. Revenue Tests

At minimum:

1. single eligible line;
2. multiple eligible lines;
3. multi-line order;
4. zero-value eligible line;
5. exact Decimal aggregation;
6. high-scale governed Decimal supported by canonical authority;
7. excluded/ineligible canonical rows not counted;
8. baseline execution;
9. comparison execution;
10. same governed input produces same value.

---

## 32. Orders Tests

At minimum:

1. one order / one line;
2. one order / multiple eligible lines -> Orders = 1;
3. multiple distinct eligible orders;
4. zero-value eligible order still counts;
5. order with no eligible lines does not count;
6. baseline;
7. comparison;
8. integer result type.

---

## 33. AOV Tests

At minimum:

1. Revenue / Orders normal case;
2. multi-line order confirms Orders distinct semantics;
3. Revenue = 0, Orders > 0 -> AOV = exact zero;
4. Orders = 0 -> Undefined;
5. exact Decimal division semantics;
6. no float result;
7. numerator/denominator use same population;
8. baseline;
9. comparison;
10. repeatability.

---

## 34. Authorization Tests

At minimum:

1. executable Revenue node executes;
2. blocked Revenue node does not execute;
3. executable Orders node executes;
4. blocked Orders node does not execute;
5. executable AOV chain executes only authorized dependencies;
6. AOV blocked chain triggers no hidden dependency execution;
7. unsupported Metric node fails closed.

---

## 35. Provenance Tests

At minimum confirm execution records contain traceable:

- plan identity;
- node identity;
- Metric identity/version;
- canonical dataset identity;
- population identity;
- executor identity/version;
- exact operation/query;
- result or error.

Do not test future Evidence admissibility.

---

## 36. Cross-Format Conformance

P4-001 must preserve the Approved Architecture requirement that equivalent governed CSV / XLSX / SQLite source data converge to equivalent canonical semantics and therefore equivalent Revenue / Orders / AOV results.

Do not add a second source-format-specific Metric implementation.

Use the canonicalized Phase 2 output.

If existing adapter-conformance fixtures are not yet physical, create only the minimum implementation test data needed for this task and do not expand into the complete Evaluation Fixture suite.

---

## 37. Existing Test Gate

All existing:

Phase 1
Phase 2
P3-001

tests must remain passing.

Do not weaken them.

---

# PART K — EXPLICITLY OUT OF SCOPE

## 38. Not Authorized

P4-001 does NOT authorize:

- Revenue Change;
- Revenue Change Percentage;
- Product Metrics;
- Category Metrics;
- Contribution;
- rankings;
- deterministic Metric result validation beyond structural execution-result contract checks;
- ValidationRecord;
- ValidatedResult;
- AdmissibleEvidence;
- Claim admissibility;
- Findings;
- Alternative Explanations;
- Recommendations;
- Evidence Contract rendering;
- physical full Evaluation Fixture suite;
- fixture runner product;
- SKILL.md;
- UI;
- Benchmark;
- statistical analysis;
- DataFrame framework;
- chart generation;
- MCP;
- generic ExecutorAdapter;
- external executor;
- Wren;
- new database connectors.

---

## 39. No Architecture Expansion

Do not introduce:

- plugin framework;
- semantic-layer framework;
- query DSL;
- generic execution framework;
- Multi-Agent runtime;
- RAG;
- vector database;
- HTTP service;
- microservices.

Use the Approved stack and narrow deterministic Python.

---

# PART L — DEPENDENCIES

## 40. Dependencies

Expected new dependencies:

NONE.

DuckDB is already the approved execution foundation.

Do not add another package unless absolutely required.

A new major dependency requires Main Project confirmation before adoption.

---

# PART M — DEFINITION OF DONE

## 41. P4-001 Is Complete Only When

- Revenue executes deterministically from approved executable plan nodes;
- Orders executes deterministically from approved executable plan nodes;
- AOV executes deterministically from executed Revenue + Orders dependencies;
- canonical governed populations remain authoritative;
- blocked nodes never execute;
- exact Decimal monetary behavior is preserved;
- Orders remains exact integer;
- Orders = 0 produces AOV Undefined;
- execution provenance is traceable;
- ExecutionRecord is distinct from ExecutedResult;
- ExecutedResult is distinct from ValidatedResult;
- no unsupported Metric executes;
- all existing and new tests pass;
- no future hybrid executor architecture is introduced.

---

## 42. Conditions Requiring Main Project Confirmation

STOP and request review if:

- Frozen Revenue / Orders / AOV semantics conflict;
- current canonical artifacts cannot safely support deterministic execution;
- existing P3 ExecutionPlan lacks material execution information and requires semantic redesign;
- exact Decimal semantics cannot be preserved with the approved DuckDB path;
- AOV cannot be represented without floating-point authority;
- an Architecture Amendment appears necessary;
- a new dependency appears necessary;
- actual deterministic validation must be implemented to make execution work;
- future external executor abstraction appears necessary to complete P4-001.

Do not solve these by guessing.

---

## 43. Required Future Implementation Report

When P4-001 is later implemented, the implementation agent must report:

A. Files created / modified

B. Revenue execution design

C. Orders execution design

D. AOV execution design

E. Population execution behavior

F. Execution authorization behavior

G. Decimal / numerical handling

H. ExecutionRecord behavior

I. ExecutedResult behavior

J. Provenance captured

K. Error / blocked behavior

L. Persistence/schema changes

M. Tests added / modified

N. Exact baseline suite command/result

O. Exact targeted suite command/result

P. Exact full suite command/result

Q. Dependencies changed

R. Existing tests modified and reason

S. Known limitations

T. Frozen conflicts / ambiguities

U. Confirmation Revenue Change was NOT implemented

V. Confirmation validation / ValidatedResult was NOT implemented

W. Confirmation MCP / external executor architecture was NOT implemented

X. Recommended next separately authorized slice

Then STOP.

---

## 44. Likely Next Step After P4-001

If P4-001 later passes Main Project Review, the project will possess its first complete deterministic reference execution path:

Metric authority
→ governed population
→ sufficiency
→ execution plan
→ DuckDB execution
→ ExecutedResult

This reference path may then support a separately authorized decision between:

1. implementing deterministic result validation next; or

2. running a narrow external-executor feasibility spike against the approved reference path.

That future decision is NOT authorized by P4-001.

---

## 45. Stop Boundary

After P4-001 implementation:

STOP.

Do NOT automatically begin:

- validation;
- Revenue Change;
- Contribution;
- external executor adapters;
- MCP;
- Evidence admissibility;
- Claim policy;
- SKILL.md;
- UI.

Wait for Main Project Review.
