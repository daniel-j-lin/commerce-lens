# P3-001 — Metric Registry, Governed Populations, and Execution Plan Foundation

## Status

AUTHORIZED SPECIFICATION

IMPLEMENTATION NOT YET STARTED

---

## 1. Purpose

This task defines the next CommerceLens implementation slice after:

- Phase 1 — APPROVED / FROZEN;
- Phase 2 — APPROVED / FROZEN; and
- R-001 Wren Foundation Feasibility — COMPLETED / CLOSED with decision KEEP DUCKDB.

The production execution foundation remains DuckDB under the Approved / Frozen Architecture.

This task establishes the deterministic pre-execution layer required before CommerceLens implements actual Revenue, Orders, AOV, Revenue Change, Product/Category performance, or Contribution calculations.

The implementation sequence for this task is:

Approved Metric Semantics
↓
Metric Registry
↓
Governed Population Definitions
↓
Execution Plan Construction
↓
Deterministic Pre-Execution Validation
↓
STOP

Actual Metric execution belongs to a later separately authorized task.

---

## 2. Governing Principle

> No material claim without traceable evidence.

The implementation must preserve:

- analytical correctness;
- evidence traceability;
- reproducibility;
- deterministic validation boundaries;
- fail-closed behavior;
- one authoritative Metric definition;
- separation of execution from validation;
- separation of execution eligibility from execution success;
- separation of Metric State from Run Status and Claim State.

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

The Frozen documents remain authoritative.

If implementation convenience conflicts with a Frozen semantic:

STOP the affected work and report the conflict.

Do not silently reinterpret a Metric.

---

## 4. Current Production Baseline

The production system already contains:

### Phase 1

- repository/package foundation;
- typed contracts;
- stable IDs/fingerprints;
- Artifact Store;
- SQLite metadata registry;
- Dataset registration;
- CSV / `.xlsx` / SQLite intake inspection.

### Phase 2

- explicit canonical mapping;
- canonicalization;
- canonical dataset references;
- Data Quality;
- governed Decimal handling;
- identity validation;
- eligibility semantics;
- currency checks;
- period/coverage prerequisites;
- Data Sufficiency;
- per-chain execution eligibility.

P3-001 must extend this baseline rather than duplicate it.

---

## 5. R-001 Decision Boundary

R-001 is complete.

Decision:

KEEP DUCKDB

Therefore:

- DuckDB remains the production execution foundation;
- Wren is NOT adopted;
- no Wren adapter belongs in this task;
- no Architecture Amendment is required;
- no Wren dependency may be added.

Do not reopen R-001.

---

# PART A — METRIC REGISTRY

## 6. Metric Registry Purpose

Create one deterministic runtime authority for approved CommerceLens MVP Metric semantics.

The Metric Registry must prevent Metric meaning from being scattered across:

- prompts;
- SQL strings;
- tests;
- reports;
- Skill instructions;
- execution code.

The Registry represents the Frozen Metric Dictionary in machine-readable form.

It does not create new Metrics.

---

## 7. Approved Metric Set

The Registry may represent only the current approved MVP Metrics:

### Core Metrics

- Revenue
- Orders
- AOV

### Period Comparison

- Revenue Change
- Revenue Change Percentage

### Product

- Product Revenue
- Product Orders
- Product Revenue Change
- Product Revenue Change Percentage
- Product Absolute Contribution
- Product Contribution Share

### Category

- Category Revenue
- Category Orders
- Category Revenue Change
- Category Revenue Change Percentage
- Category Absolute Contribution
- Category Contribution Share

### Ranking Concepts

- Leading Positive Contributors
- Leading Negative Contributors

Do not add:

- Gross Margin
- Gross Profit
- Discounts
- Refund Rate
- Inventory
- Stockout
- Retention
- CLV
- Conversion
- ROAS
- CAC
- Forecasting
- predictive Metrics
- causal Metrics
- experimental Metrics.

---

## 8. Metric Identity

Every approved Metric must have a stable machine-readable Metric ID.

IDs must be:

- deterministic;
- unique;
- human-reviewable;
- independent from display labels;
- version-bound where governed semantics require versioning.

Do not generate Metric IDs through an LLM.

Do not use arbitrary UUIDs as the semantic Metric authority.

---

## 9. Metric Registry Entry

Each Metric entry must represent only Frozen semantics.

At minimum include conceptually:

- Metric ID;
- definition version;
- display name;
- business definition;
- Metric category;
- required canonical fields;
- prerequisite Metric IDs;
- population-definition reference;
- grouping requirements;
- period requirements;
- currency/unit semantics;
- additive / non-additive classification;
- undefined conditions;
- qualification conditions where already Frozen;
- precision policy reference;
- required future validation-rule references;
- future execution implementation reference or declared `not_implemented`.

Do not execute the Metric in P3-001.

---

## 10. Single Authority Rule

There must be exactly one runtime Metric Registry authority.

Do NOT create parallel Metric definitions in:

- execution-plan code;
- population modules;
- tests;
- README;
- SQL templates.

Tests may reference expected governed semantics, but production authority must remain the Metric Registry.

---

## 11. Formula Boundary

P3-001 may encode enough structured semantic metadata to faithfully represent the Frozen Metric definition and dependencies.

However, it must NOT implement executable Metric calculations.

Examples:

Revenue may declare dependencies such as:

- canonical `line_revenue`;
- governed eligible population;
- one currency.

Orders may declare:

- distinct governed `order_id`;
- governed eligible population.

AOV may declare:

- dependency on Revenue;
- dependency on Orders;
- denominator condition.

But P3-001 must NOT execute:

SUM(line_revenue)

COUNT(DISTINCT order_id)

Revenue / Orders

or any equivalent analytical calculation as production behavior.

Actual calculation belongs to the next separately authorized task.

---

# PART B — GOVERNED POPULATIONS

## 12. Population Purpose

Create deterministic definitions for the analytical populations that future Metric execution will consume.

Population definition is distinct from Metric calculation.

A population determines:

> which canonical rows are eligible for a particular analytical scope.

---

## 13. Population Authority

The governed base population must inherit Phase 2 canonical and eligibility semantics.

Future population construction must never independently reinterpret:

- cancellation;
- full refund exclusion;
- partial refund support;
- currency;
- product identity;
- category identity;
- quantity validity;
- date assignment;
- duplicate identity;
- source completeness.

Phase 2 remains authoritative for canonical/data eligibility.

---

## 14. Base Population Definition

Define a structured base population specification that can reference:

- CanonicalDatasetReference;
- requested period;
- governed eligibility rule;
- currency basis;
- explicit supported scope filters;
- grouping mode;
- population-definition version.

Do not materialize analytical results.

---

## 15. Period Populations

Support structural definitions for:

- Baseline population;
- Comparison population.

They must reference Phase 2-validated period semantics.

Do not silently:

- change dates;
- normalize unequal periods;
- extend periods;
- shorten periods;
- impute missing dates.

P3-001 consumes sufficiency-approved period definitions.

It does not re-decide period completeness independently.

---

## 16. Total Population

Define the future total analytical population:

all eligible canonical order lines

within:

- governed dataset;
- governed period;
- governed currency;
- governed scope.

Do not calculate Revenue or Orders.

---

## 17. Product Population

Define product grouping structurally using:

`product_id`

as authority.

`product_name` remains descriptive only.

Do not group by product name.

Do not calculate Product Revenue or Product Orders.

---

## 18. Category Population

Define category grouping structurally using:

`category_id`

plus governed:

`Unclassified`

where Phase 2 permits Category analysis.

Do not silently drop `Unclassified`.

Do not create multi-label category allocation.

Do not calculate Category Revenue or Category Orders.

---

## 19. Scope Filters

Reuse the Phase 2 supported scope-filter contract.

Do not create a generic query language.

Population construction may only accept explicitly supported governed filters.

Unsupported fields/operators must remain fail closed.

Do not introduce arbitrary SQL predicates from user strings.

---

## 20. Population Identity

Every deterministic population specification must have a stable fingerprint/ID derived from material population inputs.

Material inputs include, where applicable:

- canonical dataset identity;
- period;
- eligibility semantics/version;
- currency;
- scope;
- grouping;
- filter configuration;
- population-definition version.

Equivalent population definitions must produce equivalent fingerprints.

Materially different population definitions must not collide.

---

## 21. Population Materialization Boundary

P3-001 may establish the structure/interface needed for future deterministic materialization.

It must NOT yet execute the population against DuckDB as analytical production behavior unless strictly necessary for contract-level validation and no Metric values are produced.

Preferred boundary:

PopulationDefinition
→ future PopulationBuilder
→ future PopulationReference

P3-001 should stop before real analytical population execution where possible.

If a minimal deterministic row-selection materialization is architecturally required to validate the interface, it must:

- produce no Metric result;
- remain narrowly scoped;
- be explicitly justified;
- not become hidden Metric execution.

---

# PART C — EXECUTION PLAN FOUNDATION

## 22. Execution Plan Purpose

Build the deterministic planner that converts:

AnalysisRequest
+
DataSufficiencyResult
+
Metric Registry
+
Population Definitions

into a structured:

ExecutionPlan

without executing it.

---

## 23. Planner Authority

The planner must not infer analytical intent from free-form text.

It consumes already structured approved request inputs.

It must not:

- add Metrics;
- change periods;
- change grouping;
- repair insufficiency;
- reinterpret scope;
- invent filters;
- invent currency;
- choose unsupported calculations.

---

## 24. Plan Node Structure

Each future execution node should represent conceptually:

- node ID;
- Metric ID;
- Metric version;
- dependency node IDs;
- population-definition reference;
- period reference;
- grouping;
- required canonical inputs;
- required validation-rule IDs;
- output shape/type expectation;
- precision policy reference;
- deterministic execution implementation reference;
- execution status initially `not_executed`.

Do not embed arbitrary natural-language executable instructions.

---

## 25. Dependency Graph

The plan builder must represent approved Metric dependency relationships.

Examples conceptually:

Revenue
→ base population

Orders
→ same governed population

AOV
→ Revenue + Orders

Revenue Change
→ Baseline Revenue + Comparison Revenue

Revenue Change %
→ Baseline Revenue + Comparison Revenue

Contribution
→ entity period Revenue + total Revenue Change

Do not execute these dependencies.

---

## 26. Population Consistency

The planner must guarantee that dependent Metrics requiring identical populations reference identical governed population definitions.

Example:

AOV numerator and denominator must reference the same:

- dataset;
- scope;
- period;
- eligibility basis;
- currency basis.

The planner should fail before execution if incompatible population references are supplied.

---

## 27. Undefined Is Not Pre-Execution Failure

Do not incorrectly mark a Metric as Undefined before its governed denominator/result is known unless the undefined condition is already deterministically established by available pre-execution Evidence.

Examples:

Orders = 0

is generally an execution result condition.

Therefore P3-001 must not fabricate future MetricState outcomes.

Keep:

execution eligibility

separate from:

executed Metric state.

---

## 28. Sufficiency Gate

No plan node may be created as executable when its corresponding Phase 2 MetricEligibility is ineligible.

Blocked chains must remain represented structurally with reason where the current Architecture requires it.

Independent eligible chains must remain plannable.

Do not convert one blocked chain into total failure when unrelated chains are valid.

---

## 29. Plan Determinism

Equivalent:

- AnalysisRequest;
- Metric Registry version;
- population definitions;
- sufficiency result;
- planner version

must produce an equivalent ExecutionPlan fingerprint.

Material scope/Metric changes must change the plan fingerprint.

Do not include nondeterministic timestamps in the semantic plan fingerprint.

---

## 30. Execution Plan Is Not Execution

Creating an ExecutionPlan must not create:

- ExecutionRecord;
- ExecutedResult;
- ValidationRecord;
- ValidatedResult;
- AdmissibleEvidence.

The lifecycle remains:

ExecutionPlan
↓
future deterministic execution
↓
ExecutionRecord
↓
ExecutedResult
↓
future deterministic validation
↓
ValidatedResult

P3-001 stops at ExecutionPlan.

---

# PART D — PERSISTENCE / CONTRACTS

## 31. Contract Extensions

Extend existing Pydantic contracts only where necessary.

Reuse existing:

- AnalysisRequest;
- DataSufficiencyResult;
- ExecutionPlan concepts;
- stable identifiers;
- Dataset / CanonicalDataset references.

Avoid duplicate contracts.

Do not introduce a second ExecutionPlan model.

---

## 32. Persistence

Add persistence only if necessary for:

- Metric Registry version metadata;
- population-definition metadata;
- ExecutionPlan metadata.

Do not add future:

- ExecutionRecord tables;
- ValidationRecord tables;
- ValidatedResult tables;
- Evidence tables;
- Claim tables.

If SQLite schema changes:

- increment schema version;
- implement explicit migration from the current approved schema;
- validate actual source schema before migration;
- migrate transactionally;
- verify target schema before updating version;
- preserve immutable/idempotent stable-record behavior.

Do not add SQLAlchemy or Alembic.

---

# PART E — TESTING

## 33. Required Metric Registry Tests

At minimum test:

- all approved MVP Metric IDs are present;
- unsupported Metric ID rejected;
- IDs unique;
- definitions versioned;
- required canonical inputs correct;
- dependency references resolve;
- no circular dependency;
- additive/non-additive classifications preserved;
- undefined conditions represented where Frozen;
- registry cannot silently redefine a Metric.

---

## 34. Required Population Tests

At minimum test:

- deterministic population fingerprint;
- different periods → different population identity;
- different currency → different population identity;
- different scope → different population identity;
- product grouping uses product_id;
- category grouping preserves Unclassified;
- unsupported scope/filter blocked;
- Baseline and Comparison remain distinct;
- population semantics reuse Phase 2 governance rather than reimplementing it.

---

## 35. Required Execution Plan Tests

At minimum test:

- valid Metric request → deterministic plan structure;
- dependencies ordered correctly;
- AOV depends on Revenue + Orders;
- comparison Metrics depend on Baseline/Comparison nodes;
- incompatible populations fail closed;
- ineligible Metric chain not marked executable;
- independent eligible chain survives unrelated blocked chain;
- same semantic request → same plan fingerprint;
- material request difference → different fingerprint;
- no execution/result objects created.

---

## 36. Cross-Layer Tests

Test:

AnalysisRequest
+
DataSufficiencyResult
+
Metric Registry
+
Population Definitions
→
ExecutionPlan

without Metric execution.

Ensure Phase 2 linkage checks remain intact.

Do not bypass Data Sufficiency.

---

## 37. Existing Test Gate

All existing Phase 1 and Phase 2 tests must remain passing.

Do not weaken existing tests.

Do not rewrite Frozen Evaluation Fixtures.

Physical fixture realization remains later.

---

# PART F — EXPLICITLY OUT OF SCOPE

## 38. Do Not Implement

P3-001 does NOT authorize:

- Revenue execution;
- Orders execution;
- AOV execution;
- Revenue Change execution;
- Revenue Change Percentage execution;
- Product Revenue execution;
- Category Revenue execution;
- Product Orders execution;
- Category Orders execution;
- Contribution execution;
- Contribution Share execution;
- ranking execution;
- analytical SQL Metric execution;
- ExecutionRecord creation behavior;
- ExecutedResult creation behavior;
- deterministic Metric validation;
- ValidationRecord generation;
- ValidatedResult creation;
- Admissible Evidence;
- Claim admissibility policy;
- Findings;
- Recommendations;
- physical Evaluation Fixtures;
- fixture runner execution;
- SKILL.md;
- LLM integration;
- UI;
- Benchmark scoring;
- Wren integration;
- new database connectors.

---

## 39. No Framework Expansion

Do not introduce:

- semantic-layer framework;
- generic SQL compiler;
- query DSL;
- plugin framework;
- RAG;
- vector database;
- Multi-Agent runtime;
- microservices;
- HTTP API;
- orchestration framework.

Use plain deterministic Python plus the existing approved stack.

---

## 40. Dependencies

Expected new dependencies:

NONE.

Use the current approved stack.

Do not add a package unless implementation demonstrates it is strictly necessary.

A new major dependency requires Main Project confirmation before adoption.

---

# PART G — DEFINITION OF DONE

## 41. P3-001 Is Complete Only When

- Metric Registry exists as one runtime authority;
- every approved MVP Metric has a governed registry entry;
- no unsupported Metric is added;
- Metric dependencies are deterministic;
- population definitions are governed and fingerprinted;
- total/product/category/period population semantics are represented;
- ExecutionPlan can be built deterministically;
- sufficiency gates plan eligibility;
- independent chains are preserved;
- no Metric execution occurs;
- no execution/validation/evidence lifecycle stage is skipped;
- persistence changes, if any, are safely migrated;
- all existing and new tests pass;
- production semantics remain aligned with Frozen documents.

---

## 42. Conditions Requiring Main Project Confirmation

Stop and request Main Project review if:

- Frozen Metric semantics conflict internally;
- Architecture would need to change;
- Phase 2 contracts are insufficient in a way requiring semantic redesign;
- Metric Registry would require duplicate Metric authority;
- population semantics cannot be represented without changing canonical rules;
- a major new dependency appears necessary;
- Metric execution appears necessary to complete this task;
- Frozen fixture expected outcomes would need to change.

Do not solve these cases by guessing.

Ordinary implementation details do not require confirmation.

---

## 43. Required Final Implementation Report

When P3-001 is later executed, the implementation agent must report:

A. Files created / modified

B. Metric Registry design implemented

C. Complete Metric IDs represented

D. Population-definition design

E. ExecutionPlan design

F. Sufficiency integration

G. Persistence/schema changes

H. Tests added / modified

I. Exact baseline test command/result

J. Exact targeted test command/result

K. Exact complete-suite test command/result

L. Dependencies added/changed

M. Known limitations

N. Frozen-spec conflicts/ambiguities

O. Explicit confirmation that Metric execution was NOT implemented

P. Recommended next separately authorized implementation slice

After reporting:

STOP.

Do not begin actual Metric execution.

---

## 44. Expected Next Slice

If P3-001 later completes Main Project Review successfully, the likely next separately authorized implementation slice is:

Revenue
+
Orders
+
AOV

using:

Metric Registry
→ Governed Population
→ ExecutionPlan
→ DuckDB deterministic execution

This section is informational only.

It does not authorize that implementation.

---

## 45. Stop Boundary

After P3-001 implementation:

STOP.

Do NOT automatically begin:

- Revenue;
- Orders;
- AOV;
- period comparison;
- contribution;
- validation;
- Evidence admissibility;
- Claim policy;
- SKILL.md;
- UI.

Wait for Main Project Review.
