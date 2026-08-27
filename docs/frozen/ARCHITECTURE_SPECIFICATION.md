# CommerceLens AI Architecture Specification

**Version:** v1.0  
**Status:** Approved  
**State:** Frozen  
**Date:** 2026-08-24

---

## 1. Executive Architecture Summary

CommerceLens AI shall be implemented as a small, local-first, Skill-first analytical system consisting of one governed CommerceLens Skill and one reusable deterministic analytics package. The Skill interprets the user’s Business Question, establishes scope, requests clarification, identifies Required Evidence, constructs a structured analysis request, proposes structured Claim candidates, and renders deterministically authorized Claim decisions into Findings, Alternative Explanations, Recommendations, and limitations. The deterministic package inspects and canonicalizes data, checks Data Sufficiency, calculates approved Metrics, validates the results, produces immutable evidence and result records, and evaluates structured material Claim admissibility through governed policy.

The governing architectural rule is:

> No material claim without traceable evidence.

The principal boundary is therefore not “LLM versus database.” It is:

- probabilistic interpretation and communication by the Skill; and
- deterministic data processing, calculation, validation, and evidence generation by software.

The MVP is a single Python package, not a distributed platform. It uses:

- Python as the implementation language;
- DuckDB as the primary tabular execution engine for CSV, Excel-derived canonical tables, and SQLite-derived canonical tables;
- narrow Python intake adapters using DuckDB CSV ingestion, `openpyxl` for `.xlsx`, and the standard-library `sqlite3` module for SQLite;
- Pydantic models as the canonical runtime contracts, serialized as JSON-compatible records;
- plain deterministic Python validation functions kept logically separate from execution;
- SQLite for the local registry and run/evidence metadata, with immutable local files for source snapshots and larger generated artifacts;
- an in-process Python API as the primary Skill-to-engine interface, plus a thin CLI adapter for host independence and reproducible fixture execution;
- pytest for all deterministic and contract tests; and
- YAML fixture metadata plus tiny CSV inputs as the primary physical fixture representation.

No network service is required. Multi-Agent architecture, RAG, vector databases, microservices, external web research, enterprise connectors, and a separate Decision Reliability Benchmark product layer are excluded from the MVP.

The MVP is optimized for the approved canonical question:

> How did revenue performance change between two comparable periods, and which products or categories contributed most to that change?

This document translates the Frozen product, Skill, Evidence Contract, canonical dataset, Metric, and fixture semantics into implementable component boundaries. It does not authorize implementation and does not redefine those semantics.

---

## 2. Authority, Purpose, and Release Status

### 2.1 Authoritative governing documents

The following documents are authoritative and Frozen:

1. `PROJECT_MASTER_INSTRUCTIONS.md` v1.1
2. `PRD.md` v1.1
3. `CommerceLens_Skill_First_Scope_Migration_Analysis_v1.1.md`
4. `SKILL_SCOPE_SPECIFICATION.md` v1.0
5. `EVIDENCE_CONTRACT_SPECIFICATION.md` v1.0
6. `CANONICAL_DATASET_AND_METRIC_DICTIONARY.md` v1.0
7. `EVALUATION_FIXTURES_SPECIFICATION.md` v1.0

This Architecture Specification derives from those documents. It does not reopen them. Where an implementation convenience conflicts with a Frozen governing semantic, the governing semantic wins and the conflict must be surfaced for Main Project Review rather than silently resolved in code.

### 2.2 Purpose

This document defines the minimum implementable architecture required to execute the approved CommerceLens MVP reliably. It establishes:

- system boundaries;
- logical components and their ownership;
- structured request and result contracts;
- data, execution, validation, evidence, and failure flows;
- persistence and reproducibility requirements;
- fixture and testing boundaries;
- technology choices;
- repository structure; and
- implementation order.

It answers what must be built, what crosses each boundary, and which operations must remain deterministic. It does not propose a different product.

### 2.3 Release status

This document is **Approved** and **Frozen**. Implementation may begin only through separate Main Project direction and only according to the approved implementation sequence. This Architecture document itself does not authorize creation of runtime code, SQL, physical fixtures, tests, `SKILL.md`, UI, Benchmark scoring, or deployment infrastructure in this conversation.

---

## 3. Architectural Drivers and Priorities

Architecture decisions use the following priority order:

1. Analytical correctness
2. Evidence traceability
3. Reproducibility
4. Business value
5. Data safety
6. Transparent limitations
7. MVP depth
8. Maintainable architecture
9. Documentation
10. Visual polish

The architecture is not optimized for novelty, agent count, framework popularity, abstraction purity, distributed-system sophistication, infrastructure scale, or demo spectacle.

The main architectural drivers are:

- every material numerical result must come from deterministic execution;
- every result used as material Evidence must pass its required deterministic validation;
- each material Claim must link to Admissible Evidence;
- the engine must never infer analytical intent from free-form conversation;
- independent valid result chains must remain usable when unrelated chains fail;
- source data must remain immutable and distinguishable from canonical analytical data;
- approved Metric semantics must have one authority;
- the complete result must be reproducible from identified inputs, definitions, parameters, engine versions, and validation rules; and
- one developer must be able to implement, inspect, test, and operate the MVP.

---

## 4. Governing Boundaries

### 4.1 Approved end-to-end behavioral workflow

The architecture supports the following workflow without changing its meaning:

```text
Business Question
→ Metric Definition
→ Hypothesis / Required Evidence
→ Data Sufficiency Check
→ Analysis Plan
→ Deterministic Execution
→ Deterministic Validation
→ Interpretation
→ Findings
→ Alternative Explanations
→ Recommendation
→ Limitations
→ Evidence Contract
```

### 4.2 Host and LLM authority

The host LLM may:

- interpret user intent and map it to the approved canonical question;
- determine whether clarification is required;
- generate hypotheses and identify Required Evidence;
- select only approved Metrics and scopes;
- construct a governed `AnalysisRequest`;
- explain structured Data Sufficiency and failure outcomes;
- interpret only eligible Validated Results;
- assign a candidate Claim type from the governed descriptive, diagnostic, predictive, causal, or prescriptive taxonomy;
- propose structured Claim content and intended scope for deterministic admissibility evaluation;
- render an approved Claim decision into a user-facing Finding;
- keep unsupported possible explanations explicitly labeled as Alternative Explanations;
- produce proportional Recommendations linked to supporting Findings; and
- disclose assumptions, qualifications, and limitations.

The host LLM may not:

- fabricate source data, columns, identifiers, execution, or validation results;
- calculate material KPIs instead of invoking the deterministic engine;
- supply an unapproved formula or change a governed one;
- override, reinterpret, or hide a validation failure;
- infer missing currency, product identity, duplicate identity, refund semantics, eligibility, or period completeness;
- silently deduplicate, normalize unequal periods, or convert missing values to zero;
- treat an Executed Result as a Validated Result;
- convert contribution, association, or chronology into causation; or
- produce a material Finding from intuition without linked Admissible Evidence;
- act as the sole authority for the admissibility of its own material Claim; or
- render a Claim that the deterministic Claim Admissibility Evaluator has marked Inadmissible.

These restrictions are enforced by structured contracts and a lightweight deterministic Claim Admissibility Evaluator. Engine result objects expose eligibility and status explicitly; result records that have not passed required validation do not contain an admissible-evidence reference. The Skill submits structured `ClaimCandidate` records and may construct material Findings only from `ClaimDecision` records returned as Admissible or Qualified Admissible. It cannot self-grant material Claim permission from raw execution output or its own prose.

### 4.3 Skill-first product boundary

The current product consists of:

1. the CommerceLens Skill as governed analytical orchestration and interpretation; and
2. the reusable deterministic analytics engine and its contracts.

The Decision Reliability Benchmark is not a separate runtime layer in this release. Physical fixtures and a fixture runner are MVP quality controls for the product; they do not create Benchmark scoring or a benchmark product.

---

## 5. System Context

### 5.1 Context flow

```text
User
  ↓ Business Question + local dataset
Host LLM
  ↓ governed interaction
CommerceLens Skill
  ↓ structured AnalysisRequest
Deterministic Analytics Package
  ↓ AnalysisResult + evidence references
CommerceLens Skill
  ↓ evidence-governed response
User
```

### 5.2 Trust boundaries

| Boundary | Input is trusted for | Input is not trusted for | Required control |
|---|---|---|---|
| User → Skill | Stated business intent and explicitly authorized assumptions | Analytical validity, schema correctness, or numerical truth | Scope check, clarification, explicit assumption recording |
| Skill → Engine | Only fields accepted by the request contract | Free-form prose as executable intent | Contract validation and approved-value allowlists |
| Source → Canonicalization | Source bytes and observable source values | Canonical meaning, completeness, uniqueness, or eligibility | Immutable source registration, mapping checks, Data Quality checks |
| Execution → Validation | Executed values and execution records | Evidence admissibility | Independent validation rules |
| Engine → Skill | Structured status and eligible evidence references | Permission to ignore failures or qualifications | Fail-closed result contract |
| Skill → Claim Admissibility Evaluator | Structured Claim candidate, intended scope, and candidate Claim type | Permission to self-authorize material output | Deterministic policy evaluation |
| Claim Admissibility Evaluator → Skill | Claim decision, required qualification, and supporting Evidence refs | General understanding of arbitrary prose | Controlled decision contract and allowlisted policy rules |
| Skill → User | Rendering of authorized Claims and clearly labeled hypotheses | New numerical or admissibility authority | Claim linkage and qualification enforcement |

### 5.3 Deployment shape

The MVP runs locally in one process by default. The host or Skill calls a Python API. A thin CLI exposes the same application service for fixture execution, debugging, and hosts that cannot import Python directly. Both routes invoke the same contracts and orchestration service. No local HTTP server, message broker, event bus, or cloud service is required.

---

## 6. Logical Architecture

Logical separation exists to preserve authority and testability. It does not imply separate services.

| Logical layer | MVP implementation boundary | Primary responsibility |
|---|---|---|
| A. Host / LLM | External host boundary | Intent interpretation and user communication |
| B. CommerceLens Skill | `skill/` artifact and adapter boundary | Governed workflow, clarification, planning, Claim construction |
| C. Request / Contract | `contracts/` | Validate structured inputs, outputs, statuses, and references |
| D. Data Intake | `intake/` | Register and inspect CSV, Excel, and SQLite sources |
| E. Canonicalization / Sufficiency | `canonical/` and `sufficiency/` | Produce canonical data and determine execution eligibility |
| F. Deterministic Analytics Engine | `engine/` and `metrics/` | Execute approved population and Metric calculations |
| G. Deterministic Validation | `validation/` | Validate executed results and produce validation records |
| H. Evidence / Provenance / Claim Policy | `evidence/` | Create stable lineage records and Admissible Evidence links; deterministically evaluate structured material Claim admissibility |
| I. Result Contract | `contracts/results` conceptually | Return partial, qualified, failed, and completed outcomes safely |
| J. Fixture / Test Boundary | `fixtures/`, `fixture_runner/`, `tests/` | Check conformance to Frozen expected outcomes |
| K. Local Persistence | `persistence/` plus run artifact directory | Preserve registry, records, and immutable run artifacts |

For MVP simplicity, intake, canonicalization, sufficiency, engine, validation, evidence, and persistence are subpackages of one installable Python package and execute in one process. Request and Result contracts may live in one `contracts` package. Logical separation between execution and validation is mandatory even though both ship in the same package.

---

## 7. Component Responsibilities

### 7.1 CommerceLens Skill

The Skill implements the approved behavioral state progression:

```text
Input Received
→ Scope Check
→ Clarification Required or Proceed
→ Metric Definition
→ Hypothesis / Required Evidence
→ Data Sufficiency Check
→ Analysis Plan
→ Deterministic Execution
→ Deterministic Validation
→ Interpretation
→ Completed
```

It owns:

- canonical-question matching and unsupported-scope handling;
- clarification dialogue;
- approved Metric selection by stable Metric references;
- hypothesis and Required Evidence articulation;
- construction of the governed request;
- presentation of Data Sufficiency and failure information;
- candidate Claim formulation, candidate Claim-type assignment, and intended-scope declaration;
- submission of structured Claim candidates for deterministic admissibility evaluation;
- rendering of Admissible or Qualified Admissible Claim decisions into Findings;
- Alternative Explanation, Recommendation, and limitation construction; and
- user-facing communication.

It does not own dataset arithmetic, canonical field repair, formulas, aggregation, validation, evidence lineage reconstruction, or final material Claim admissibility. The future `SKILL.md` belongs under `commerce_lens/skill/` and must reference capabilities and contracts rather than duplicate authoritative formulas in free-form instructions.

### 7.2 Request and Contract layer

This layer owns schema validation for all cross-boundary records. It rejects unknown enum values, missing required governed fields, invalid period structures, incompatible output requests, and unrecognized Metric references before execution begins.

Contracts are JSON-compatible and versioned. Pydantic is the runtime authority for validation and serialization; generated JSON Schema may be used for host integration and documentation. JSON Schema is derived output, not a second hand-maintained contract authority.

### 7.3 Data Intake

Data Intake owns:

- registration of CSV, Excel, and SQLite sources;
- safe file-type confirmation and source metadata capture;
- computation of a content fingerprint;
- assignment of a stable dataset reference;
- immutable source snapshot or immutable reference policy;
- schema and table/sheet inventory;
- controlled selection of one source table/sheet where required; and
- creation of an intake record.

It does not interpret business meaning beyond approved mapping inputs and does not mutate source files. The concrete MVP Excel adapter supports `.xlsx` through `openpyxl`. If `.xlsm` is deliberately enabled, macros remain non-executed and only governed stored cell values may be read. Legacy `.xls` is not supported unless a suitable reader is separately approved, added, and covered by adapter conformance tests. Excel formulas are ingested from stored cell values only under an explicit, recorded policy; the MVP does not recalculate workbooks. Ambiguous sheet selection, merged-cell layouts, multiple header rows, or stale/missing formula results must produce clarification or Data Quality failure rather than silent guessing.

### 7.4 Canonicalization

Canonicalization deterministically creates a canonical analytical dataset governed by the Frozen canonical dataset specification. It owns only approved transformations, including:

- authorized source-to-canonical field mapping;
- type normalization;
- governed date parsing;
- canonical field validation;
- governed `Unclassified` treatment;
- and application of eligibility only where authoritative eligibility evidence exists.

It records each applied mapping and transformation version. It must not invent currency, product IDs, duplicate identity, refund semantics, missing monetary values, complete periods, or unauthorized taxonomy mappings. An inability to establish the canonical contract produces a structured Data Sufficiency or Data Quality outcome.

### 7.5 Data Sufficiency evaluator

Data Sufficiency is a named pre-execution stage, not an incidental loader check. It compares Required Evidence from the request with Available Evidence observed after intake and canonicalization. It evaluates execution eligibility per requested Metric and scope across:

- required canonical fields;
- requested periods;
- analytical population and eligibility;
- currency authority;
- composite line identity and duplicate ambiguity;
- product identity;
- category attribution;
- attribution completeness and required qualifications;
- period completeness, equal duration, and non-overlap; and
- other governed Metric prerequisites.

It distinguishes:

- Required Evidence: what must exist for the intended Metric, Claim type, scope, and purpose;
- Available Evidence: what is present and accessible;
- Data Quality: whether present evidence satisfies governed structural and semantic conditions;
- Metric Undefined: a governed mathematical or semantic undefined state;
- Execution Eligibility: whether a specific calculation chain may run; and
- Claim Eligibility: determined later, after validation and admissibility evaluation.

Sufficiency is evaluated per Metric dependency chain so independent chains can proceed.

### 7.6 Metric Registry

The Metric Registry is the single runtime authority for approved Metric definitions. It contains stable identifiers and machine-readable governed metadata for the approved Metrics, including Revenue, Orders, AOV, Revenue Change, Revenue Change %, Product Revenue, Product Orders, Category Revenue, Category Orders, Absolute Contribution, and Contribution Share.

For each Metric, the registry represents:

- Metric reference and definition version;
- governed display name and meaning;
- required canonical inputs and evidence prerequisites;
- population and grouping dependencies;
- calculation implementation reference;
- precision and presentation rules;
- undefined conditions;
- required validation-rule references; and
- permitted dependency relationships.

The registry must encode, not reinterpret, the Frozen Metric Dictionary. Prompts, fixture metadata, and UI text reference Metric IDs; they do not restate separate formulas.

### 7.7 Execution-plan builder

The plan builder converts a valid `AnalysisRequest` and Sufficiency result into a small `ExecutionPlan`. It exists to separate user-approved analytical intent from operational ordering and to make the exact work reproducible.

The plan contains explicit Metric IDs, periods, population filter references, grouping, required result shapes, dependency order, and applicable validation-rule IDs. It is not a generic query planner or DSL. It cannot add a Metric, infer a filter, repair a period, or modify scope. If it cannot derive a plan without guessing, it returns a structured failure.

### 7.8 Deterministic Analytics Engine

The engine owns reusable deterministic computation for:

- period population construction;
- authoritative eligibility filtering;
- governed aggregation;
- distinct-order counting;
- AOV;
- Revenue Change and Revenue Change %;
- product and category grouping;
- entity union across periods and entry/exit handling;
- Absolute Contribution and Contribution Share;
- positive and negative rankings; and
- authoritative precision.

It produces Executed Results and an Execution Record. It does not produce causal explanations, business narrative, Recommendations, hypotheses, or user-facing prose.

### 7.9 Deterministic Validation

Validation is a distinct module and lifecycle stage. It consumes Executed Results and relevant records but does not reuse the same function as its only proof of correctness where an independent invariant can be checked.

It evaluates applicable governed invariants, including:

- formula and dependency consistency;
- population consistency;
- product contribution reconciliation to total Revenue Change;
- category contribution reconciliation to total Revenue Change;
- AOV population consistency;
- precision and ranking basis;
- zero-denominator behavior; and
- non-additive Orders behavior.

A result is not a Validated Result merely because execution completed. Failed required validation prevents creation of Admissible Evidence for that result. The LLM has no override field.

### 7.10 Evidence and Provenance

The Evidence component writes lineage records as execution and validation occur. It does not ask the Skill to reconstruct lineage afterward. It assigns stable IDs and links Dataset References, canonicalization, requests, execution, results, validations, admissibility, Findings, and Recommendations.

Within the same package, a lightweight deterministic Claim Admissibility Evaluator owns material Claim permission. It consumes a structured `ClaimCandidate`, the candidate Claim type and intended scope, Required Evidence rules, available Admissible Evidence, supporting Validated Result references, assumptions, limitations, required qualifications, and MVP Claim-type restrictions. It returns a structured `ClaimDecision` of Admissible, Qualified Admissible, or Inadmissible, including supporting Evidence references, required qualification, and reason.

The evaluator applies explicit governed policy only. It does not understand arbitrary prose, prove general natural-language truth, or use an LLM-as-judge. A candidate whose material meaning cannot be represented by the supported structured fields is Inadmissible until clarified or narrowed; the Skill cannot authorize it itself.

No graph database is required. Ordinary normalized SQLite records plus JSON-compatible immutable artifacts are sufficient for the MVP lineage:

```text
Claim
→ ClaimDecision
→ Admissible Evidence
→ Validated Result
→ Validation Record
→ Execution Record
→ Metric Reference
→ Dataset Reference
```

### 7.11 Persistence

Persistence owns local run metadata and artifacts. SQLite stores the dataset registry, canonicalization metadata, request/run index, execution records, validation records, evidence links, statuses, and artifact paths. Immutable source snapshots, canonical tabular artifacts, and full result bundles remain files referenced from SQLite.

This hybrid avoids storing large table blobs in the registry while keeping referential integrity and searchable provenance. A run artifact directory is append-only after finalization. Temporary files are created in a controlled run-scoped directory and deleted or retained according to an explicit completion policy.

### 7.12 Fixture runner

The future fixture runner loads one physical fixture, builds the declared `AnalysisRequest`, executes the same public application service used by the Skill, and compares actual structured outcomes with one authoritative expected outcome for that fixture variant.

It owns deterministic comparison of the separate Run Status, Metric State, Claim State, validation/failure details, numerical results at authoritative precision, evidence-link presence, required qualifications, blocked Metrics, and the fixture’s authoritative expected outcome. It does not rewrite expected outcomes, substitute runtime status vocabulary for fixture outcomes, or score a benchmark.

---

## 8. Core Contracts

The following contracts are conceptual data contracts, not programming-language implementations. Exact field syntax may be finalized during implementation, but the semantics below are architectural requirements.

### 8.1 `AnalysisRequest`

| Field group | Required content | Governance purpose |
|---|---|---|
| Identity | request ID, contract version, creation time | Stable run linkage |
| Question | canonical Business Question ID and user-question reference | Prevent engine interpretation of prose |
| Metrics | approved Metric references and requested output roles | Prevent formula or scope invention |
| Periods | explicit Baseline and Comparison boundaries, date convention | Make comparison reproducible |
| Scope | approved population and explicit filters | Prevent hidden filtering |
| Grouping | none, product, category, or approved combination | Bound contribution analysis |
| Required Evidence | prerequisite references per Metric/Claim intent | Drive sufficiency checks |
| Dataset | dataset reference and selected table/sheet where applicable | Identify immutable source |
| Assumptions | only explicitly authorized, typed assumptions | Prevent silent repair |
| Definition refs | canonical schema and Metric Registry versions | Bind semantics |
| Requested outputs | approved result shapes and ranking limits | Bound execution |

Free-form user prose may be retained as contextual metadata, but it is not executable input. The request is rejected if a required governed field cannot be established.

### 8.2 `DataSufficiencyResult`

The result contains a request ID; dataset and canonical dataset references; Required and Available Evidence items; check results; per-Metric execution eligibility; Data Quality failures; clarification items; assumptions; qualifications; and overall status. The overall status never erases per-Metric outcomes.

### 8.3 `ExecutionPlan`

The plan contains a plan ID and version, request ID, ordered Metric dependency nodes, period/population references, grouping instructions, precision policy reference, required validation-rule IDs, and plan fingerprint. It contains no arbitrary executable code and no generic natural-language instructions.

### 8.4 `ExecutionRecord`

The record contains an execution ID; plan and request IDs; dataset and canonical dataset references; engine and dependency versions; Metric implementation references; applied periods, filters, and population IDs; start/end timestamps; output artifact references; row-count and grouping metadata where governed; and execution status/failure details.

### 8.5 `ExecutedResult`

Each result contains a result ID, execution ID, Metric reference, scope and period references, typed value or governed undefined state, authoritative precision, units/currency where supported, grouping/entity keys where applicable, and execution status. It does not assert validation or admissibility.

### 8.6 `ValidationRecord`

Each record contains:

- validation ID;
- target result ID or result-set ID;
- validation-rule ID and validation version;
- status (`passed`, `failed`, `not_applicable`, or governed blocked state);
- observed value or condition;
- expected constraint;
- authoritative precision;
- failure reason;
- Metric reference; and
- validation timestamp.

There is no confidence score. Deterministic validation remains deterministic.

### 8.7 `ValidatedResult`

A `ValidatedResult` references one Executed Result and every applicable required Validation Record for that result and intended material use. It may exist only when all such deterministic validation requirements have passed. Qualification never substitutes for, repairs, or bypasses failed required validation.

Qualification and limitation metadata is attached only after a Validated Result exists. A Validation Failure produces no `ValidatedResult` for the affected intended material use, no Admissible Evidence from that failed chain, and no permission for a dependent material Claim. An independently valid chain remains eligible when another chain fails.

### 8.8 `AdmissibleEvidence`

An Admissible Evidence record links a Validated Result to its supported Claim type, scope, Metric definition, dataset, assumptions, limitations, and any separately represented required qualification. It records the evidence admissibility state defined by the Frozen Evidence Contract. Availability alone does not create admissibility, and qualification cannot convert a failed validation chain into Admissible Evidence.

### 8.9 `AnalysisResult`

The engine returns one structured `AnalysisResult` containing:

- request, run, contract, and traceability IDs;
- overall Run Status;
- Data Sufficiency state;
- Metric results with independent Metric States and execution/validation failure details where applicable;
- Executed Result references;
- Validation states and records;
- Validated Result references;
- Admissible Evidence references;
- Claim Decisions with independent Claim States when Claim candidates have been evaluated;
- qualifications, assumptions, and limitations;
- blocked Metrics and reasons;
- failure details by stage; and
- artifact references sufficient for reproduction.

Run Status, Metric State, Claim State, validation records, failure details, and fixture expected outcomes are distinct domains. The Skill consumes this contract. It does not scrape stdout or infer success from textual logs.

### 8.10 Skill interpretation and deterministic policy artifacts

The Skill produces candidate interpretation metadata, and the deterministic Claim Admissibility Evaluator produces the material Claim decision before the Skill renders prose:

| Artifact | Required structured fields |
|---|---|
| Claim candidate | claim ID, claim type, intended scope, proposed meaning |
| Claim decision | evaluator/policy version, Claim State, qualification required, supporting evidence refs, validated-result refs, reason |
| Finding | finding ID, Claim decision, evidence refs, scope, qualification |
| Alternative Explanation | hypothesis ID, explicit unsupported/supported status, any separate evidence refs |
| Recommendation | recommendation ID, supporting Finding refs, proportionality/ownership note, limitations |

The Skill owns `ClaimCandidate`; the evaluator owns `ClaimDecision`; the Skill may render only an authorized decision. This is the minimum Claim-governance mechanism. It is not a theorem prover and does not attempt general verification of arbitrary language.

---

## 9. Data Architecture

### 9.1 Source registration and immutability

Every input source receives a Dataset Reference before canonicalization. The reference includes source type, original name, selected sheet/table if applicable, byte-level fingerprint, size, registration time, and source-snapshot location or immutable external-local reference.

The source file is never overwritten. When practical, the MVP copies it into a content-addressed local source area. If policy permits reference-only use, the stored fingerprint must be checked before reproduction; a mismatch requires re-registration.

### 9.2 Source and canonical separation

The lineage is:

```text
Source Dataset Reference
→ Canonicalization Record
→ Canonical Dataset Reference
```

The canonical dataset is a generated, versioned analytical artifact. It contains only governed canonical fields and records its source mapping, transformation configuration, canonical schema version, input fingerprint, output fingerprint, row counts, warnings, and failures. It never replaces or edits the source.

### 9.3 Intake adapters

| Source | MVP adapter behavior | Explicit limits |
|---|---|---|
| CSV | Detect and record encoding/delimiter policy, inspect header and types, load selected file | Ambiguous encoding/delimiter fails or requires explicit selection |
| Excel | Accept `.xlsx` through `openpyxl`; select explicit sheet, read governed stored values, inspect headers/types | No workbook recalculation or macro execution; `.xls` is unsupported; `.xlsm` requires deliberate enablement and conformance coverage |
| SQLite | Select explicit table/view, inspect declared and observed schema, read through controlled queries | No arbitrary user SQL; no write access to source database |

The adapters converge on a temporary tabular representation and then the same canonicalization path. No Shopify, Amazon, Stripe, warehouse, marketplace, or cloud connector is part of the MVP.

### 9.4 Data Quality checks

The deterministic quality suite is derived from the Frozen canonical and fixture specifications. It includes, where applicable:

- required canonical-field presence and types;
- composite line identity availability and uniqueness/ambiguity;
- positive whole-number quantity;
- missing `line_revenue` detection;
- supported and consistent currency evidence;
- authoritative eligibility evidence;
- product identity;
- category attribution and governed `Unclassified` handling;
- Baseline and Comparison period completeness;
- equal period duration;
- non-overlap;
- consistent and parseable order dates; and
- consistency of records used in Metric populations.

Checks return typed outcomes and affected dependencies. The architecture defines no aggregate or percentage Data Quality score.

### 9.5 Monetary and eligibility authority

Canonicalization and population construction preserve the governing separation between monetary authority and eligibility authority. A monetary value does not by itself establish that a line belongs to the eligible analytical population. The architecture applies monetary and eligibility semantics through separate governed references and records both in the execution lineage.

### 9.6 Periods and populations

Periods are explicit request objects using one date-boundary convention selected by the governed contract. Population construction is a deterministic engine operation. The resulting population reference records the period, eligibility rule reference, filters, canonical dataset, and row/order counts needed for validation and reproduction.

No period is silently extended, shortened, aligned, or imputed. Unequal duration, overlap, or incomplete-period conditions follow the approved failure or qualification semantics.

---

## 10. Execution Architecture

### 10.1 Execution path

```text
AnalysisRequest
→ Contract Validation
→ Intake and Canonicalization
→ DataSufficiencyResult
→ ExecutionPlan
→ DuckDB-backed Engine Operations
→ Executed Results + Execution Record
```

The engine executes only eligible plan nodes. A blocked node is represented explicitly and is not submitted for calculation.

### 10.2 SQL and Python responsibility

DuckDB is the primary tabular execution engine. It provides deterministic filtering, grouping, distinct counting, joins, period population construction, aggregation, and contribution tables over canonical data. Python owns intake adapters, canonicalization control, request/plan orchestration, validation, evidence records, persistence, and contract serialization.

Excel is first parsed by the Python intake adapter into the canonical tabular pipeline; it is not treated as an execution engine. SQLite sources are read-only inputs. Their selected data is canonicalized and registered in DuckDB for consistent execution semantics across all supported formats.

This division provides one analytical execution path while preserving CSV, Excel, and SQLite support. It also reduces differences between source types and avoids implementing the same Metrics separately in pandas, SQLite, and DuckDB.

### 10.3 Metric execution

Metric implementations are referenced by the Metric Registry and consume only governed canonical columns, population references, and plan parameters. The architecture does not duplicate formulas in the Skill, fixture runner, or narrative layer.

Calculation results retain authoritative precision internally. Presentation rounding occurs only according to the referenced Metric rule. Reconciliation uses the authoritative precision defined by the Frozen Metric specification, not arbitrary display strings.

### 10.4 Grouped contribution analysis

Product and category analysis uses the governed entity identity and attribution rules. The engine forms the required union of entities across both periods so entries, exits, positive contribution, and negative contribution are represented consistently. Product and category contribution chains remain separate and each has its own reconciliation validation.

Contribution describes allocation of observed Revenue Change. It does not create a causal result or causal Claim permission.

### 10.5 Engine output discipline

The engine writes structured records and artifacts only. Human-readable console output is operational convenience and never the Result Contract. Any implementation that requires the Skill to parse log lines or SQL text to identify values violates this architecture.

---

## 11. Validation Architecture

### 11.1 Executed Result is not Validated Result

Execution and validation are separate lifecycle states:

```text
Execution completed
→ Executed Result
→ Required validation rules run
→ Passed: Validated Result may be created
→ Failed: dependent Evidence and Claims are blocked
```

The two stages may run in the same process but must use separate modules, records, statuses, tests, and version references.

### 11.2 Validation-rule registry

Validation rules have stable IDs, versions, applicability conditions, target result types, and deterministic evaluators. The Metric Registry declares which validation rules are required for each Metric or result set. The executor cannot mark its own output admissible.

### 11.3 Required invariants

The validation layer enforces all applicable Frozen invariants, including:

- Metric dependency/formula consistency;
- Baseline/Comparison population consistency;
- product contribution sum equals total Revenue Change under authoritative precision;
- category contribution sum equals total Revenue Change under authoritative precision;
- AOV uses the governed Revenue and Orders populations;
- rankings use the governed basis and direction;
- zero-denominator behavior follows the Metric definition;
- Orders remains non-additive across product/category groups where governed; and
- precision and units/currency remain consistent.

### 11.4 Independent chains and partial validation

Validation is scoped to result dependencies. If Revenue Change is valid while Revenue Change % is Undefined because its governed denominator condition is not satisfied, the first chain remains eligible and the second is returned as Undefined. A failed category reconciliation blocks category contribution Findings but need not block an independently valid total Revenue Change or product contribution chain.

### 11.5 Fail-closed mechanics

The architecture enforces fail-closed behavior through these structures:

- `ExecutedResult` and `ValidatedResult` are separate contract types/status domains;
- only the evidence builder can create Admissible Evidence records;
- the evidence builder requires a Validated Result and applicable passed Validation Records;
- failed or absent required validation produces no admissible-evidence ID;
- the Claim Admissibility Evaluator creates Claim permission only from applicable Validated Result and admissible-evidence references;
- the Skill constructs Findings only from Admissible or Qualified Admissible `ClaimDecision` records;
- every blocked result has an explicit reason and dependency path; and
- there is no “force valid,” “LLM override,” or “ignore validation” request field.

Prompt instructions remain defense in depth, not the enforcement mechanism.

---

## 12. Evidence and Provenance Architecture

### 12.1 Operational Evidence Contract

The MVP represents:

- Dataset Reference;
- Canonical Dataset Reference and Canonicalization Record;
- Metric Reference;
- Analysis Request and Execution Plan;
- Execution Record and Executed Result;
- Validation Record and Validated Result;
- Admissible Evidence;
- Scope, assumptions, qualifications, and limitations;
- Claim and Finding linkage; and
- Recommendation linkage.

Evidence records arise during the relevant deterministic stage. They are not reconstructed from conversational memory.

### 12.2 Stable identifier strategy

Each record has a type-prefixed stable identifier. Content-derived fingerprints are used for immutable datasets, plans, and artifact integrity where useful; generated unique IDs are used for run events and interpretation artifacts. References are explicit fields, not embedded prose.

The exact identifier syntax is an implementation detail, but identifiers must be collision-resistant within the project, immutable after record finalization, and usable across JSON artifacts and SQLite rows.

### 12.3 Evidence lineage

```text
Source Dataset (deterministic artifact)
→ Dataset Reference (deterministic record)
→ Canonical Dataset (deterministic artifact)
→ Canonicalization Record (deterministic record)
→ AnalysisRequest (Skill-created governed record)
→ Execution Record (deterministic record)
→ Executed Result (deterministic record)
→ Validation Record (deterministic record)
→ Validated Result (deterministic record)
→ Admissible Evidence (rule-governed record)
→ Finding (LLM interpretation artifact with enforced references)
→ Recommendation (LLM interpretation artifact with Finding references)
```

Required Evidence identification, hypotheses, Claim candidates, Findings, Alternative Explanations, and Recommendations are Skill/LLM interpretation artifacts. Dataset, canonicalization, execution, result, validation, evidence-admissibility, and Claim-decision records are produced or gated deterministically. Candidate Claim type assignment is made by the Skill using the controlled taxonomy; final material Claim permission is produced by the deterministic Claim Admissibility Evaluator against governed policy and available Admissible Evidence.

### 12.4 Graph decision

The MVP does not require a graph database or dedicated evidence graph. The lineage is a small, acyclic set of typed references. SQLite foreign-key relationships and immutable JSON result bundles are easier to inspect, test, export, and maintain. A graph representation may be derived later without changing record identities if query complexity eventually justifies it.

### 12.5 Reproducing a material result

A material result is reproducible only when the record set identifies:

- source dataset identity and fingerprint;
- selected source sheet/table;
- canonical dataset fingerprint;
- canonicalization configuration and version;
- canonical schema version;
- AnalysisRequest and ExecutionPlan;
- Metric definition versions;
- exact periods, population, grouping, and filters;
- engine and relevant dependency versions;
- validation-rule versions;
- Executed and Validated Results;
- authoritative precision and unit/currency;
- artifact integrity references; and
- execution timestamps where operationally useful.

This is deterministic analytics provenance, not ML experiment tracking.

---

## 13. Claim, Finding, Alternative Explanation, and Recommendation Boundary

### 13.1 Claim taxonomy

The architecture preserves the Frozen taxonomy:

- Descriptive
- Diagnostic
- Predictive
- Causal
- Prescriptive

The MVP primarily supports descriptive and bounded diagnostic Claims. Predictive, causal, and stronger prescriptive Claims remain inadmissible unless their separately governed Required Evidence exists; this architecture does not add engines for them.

### 13.2 Claim decision path

```text
Skill
→ ClaimCandidate
→ Deterministic Claim Admissibility Evaluation
→ ClaimDecision: Admissible, Qualified Admissible, or Inadmissible
→ Skill rendering
```

The evaluator checks the candidate Claim type, intended and supported scope, Required Evidence, available Admissible Evidence, supporting Validated Result references, assumptions, limitations, required qualifications, and MVP Claim-type restrictions. The Claim decision record includes its policy version, supporting Evidence refs, required qualification, state, and reason.

The Skill may propose candidate content and type, but it cannot self-authorize a material Claim. An Inadmissible Claim is withheld from Findings or restated only as an explicitly labeled hypothesis when permitted by the governing Evidence Contract. Deterministic policy does not claim to understand arbitrary prose; an unsupported or structurally unrepresentable material Claim is blocked rather than passed to an LLM-as-judge.

### 13.3 Finding construction

A material Finding is eligible only through:

```text
Validated Result
→ Admissible Evidence
+ ClaimCandidate
→ Deterministic ClaimDecision
→ Admissible or Qualified Admissible Finding
```

Qualification is parallel metadata attached after validation; it cannot rescue failed required validation. An Executed Result without all applicable required validation cannot enter this path. LLM intuition and Skill self-authorization cannot substitute for any input.

### 13.4 Alternative Explanations

Alternative Explanations remain separate hypothesis artifacts unless supported by distinct Admissible Evidence. They must carry a status that prevents display as established fact. No external web search is required or automatically invoked to explain observed changes.

### 13.5 Recommendations

A Recommendation must reference one or more admissible Findings, include its limitations, and remain proportional to those Findings. Without causal evidence, acceptable actions emphasize investigate, review, verify, monitor, or inspect rather than autonomous causal intervention. Human Decision Ownership is included in the output contract and user-facing response.

---

## 14. Failure and Runtime State Model

The architecture uses separate domains for overall request lifecycle, Metric semantics, material Claim permission, failure detail, and Frozen fixture outcomes. Values from one domain must not be substituted into another.

### 14.1 Run Status

Run Status describes only the lifecycle and aggregate disposition of the analytical request:

- `clarification_required`: required request information is unresolved;
- `ready_for_execution`: the governed request is complete and pre-execution work may begin;
- `blocked`: no requested executable chain can proceed because the whole requested executable scope is unsupported, insufficient, or fails shared Data Quality requirements;
- `executing`: at least one eligible deterministic chain is running;
- `execution_failed`: no independently valid requested execution chain completed;
- `validation_failed`: execution produced results, but no independently valid requested material chain survived required validation;
- `partially_completed`: at least one requested material chain is usable and at least one other requested chain is Undefined, Inadmissible, blocked, or failed; and
- `completed`: all requested material chains reached their authoritative expected Metric disposition without a blocked or failed chain.

Clarification reason, Unsupported Scope, Insufficient Evidence, and shared Data Quality Failure are structured request/failure details attached to `clarification_required` or `blocked`; they are not additional peer Run Status values. Status transitions are append-only records for auditability, but the MVP does not require a workflow engine.

### 14.2 Metric State

Each requested Metric chain independently preserves the Frozen analytical state vocabulary:

- `Valid`
- `Qualified`
- `Undefined`
- `Inadmissible`

Execution Failure and Validation Failure are recorded as separate failure details on the affected Metric chain and determine whether any `ValidatedResult` can exist. `Undefined` is a governed analytical state, not a failure and never silently becomes zero. `Qualified` represents an otherwise valid chain with required qualification; it never means failed validation was bypassed.

### 14.3 Claim State

Each material `ClaimDecision` has exactly one deterministic policy state:

- `Admissible`
- `Qualified Admissible`
- `Inadmissible`

The Claim State is produced by the Claim Admissibility Evaluator, not selected by the Skill. Claim State does not replace Metric State or Run Status.

### 14.4 Failure detail and propagation

Failure details retain stage, target, reason, governing reference, dependency scope, and whether independent chains may continue:

| Failure detail | Domain and propagation |
|---|---|
| Unsupported Scope | Request-level reason; no unsupported execution is planned |
| Clarification Required | Request-level reason; execution pauses until governed fields are resolved |
| Insufficient Evidence | Request- or Metric-chain detail; blocks only affected chains unless shared prerequisites fail |
| Data Quality Failure | Dataset/population/Metric-chain detail; blocks its dependent chains |
| Execution Failure | Metric-chain detail; produces no Validated Result for that chain |
| Validation Failure | Metric-chain detail; produces no Validated Result or Admissible Evidence for the affected intended material use |
| Inadmissible Claim | Claim State/reason; prevents Finding rendering but does not rewrite upstream Metric State |

Failures do not collapse into generic `ERROR`. Independent valid chains survive unrelated failures.

### 14.5 Fail-closed behavior

Fail Closed is a governing behavior of a blocked analytical chain, not a peer Run Status. When Required Evidence, governed semantics, execution, required validation, or material Claim permission is absent, the system withholds the affected output and does not fabricate, infer, silently repair, weaken semantics, or substitute qualification for validation.

### 14.6 Permitted run transition outline

```text
Input
├─→ Clarification Required
└─→ Ready for Execution
      ├─→ Blocked
      └─→ Executing
            ├─→ Execution Failed
            └─→ Validation
                  ├─→ Validation Failed
                  ├─→ Partially Completed
                  └─→ Completed
```

The overall Run Status is derived deterministically from per-chain outcomes. Frozen fixture outcome vocabulary remains authoritative for fixtures and is compared separately; architecture Run Status does not replace or reinterpret it.

### 14.7 Partial-completion example

If Revenue Change is Valid while Revenue Change % is Undefined, `AnalysisResult` returns the Revenue Change value and admissible-evidence link, the percentage’s `Undefined` Metric State and governing reason, and separate Claim Decisions. The overall Run Status is `partially_completed`. The valid result remains usable. No zero, placeholder percentage, or global failure is introduced.

---

## 15. Skill-to-Engine Interface

### 15.1 Interface requirements

The boundary must be structured, explicit, reproducible, testable, and host-independent. The engine receives no conversational history. User prose may be stored for audit context but has no execution authority.

### 15.2 Selected interface

The primary interface is an in-process Python application API accepting a validated `AnalysisRequest` and returning an `AnalysisResult`. A thin CLI adapter accepts and emits the same JSON-compatible contracts.

The in-process API is selected because it has the fewest moving parts, preserves typed models, and supports direct Skill integration and fast tests. The CLI is included because it provides a stable process boundary for non-Python hosts, fixture runs, and reproducibility without requiring a network service.

Both call the same application service. The CLI contains no separate formulas, validation logic, or orchestration semantics.

### 15.3 Rejected interface options

- A local HTTP API is rejected for MVP because networking, process lifecycle, authentication, ports, and serialization add risk without analytical value.
- Direct invocation of separate scripts is rejected because it encourages ad hoc parameters and stdout parsing.
- A free-form prompt-to-SQL interface is rejected because the deterministic engine must not infer analytical intent.

### 15.4 Reconsideration trigger

A local HTTP boundary may be reconsidered only when an approved deployment environment cannot use the Python API or CLI, multiple concurrent clients require isolation, or packaging evidence shows a service provides material integration value.

---

## 16. Persistence, Artifacts, Observability, and Logging

### 16.1 Persistence decision

The MVP uses one local SQLite metadata store and a deterministic artifact directory. SQLite records identities, relationships, statuses, versions, and paths. Files store source snapshots, canonical datasets, request/result bundles, and other larger immutable outputs.

No distributed database, cloud object store, or hosted lineage platform is required.

### 16.2 Artifact layout principles

Generated runtime artifacts are outside authoritative specifications, runtime source code, fixtures, tests, and demo data. Each finalized run directory contains a manifest tying all artifacts to the run and their fingerprints. Generated artifacts are never committed as authoritative definitions.

### 16.3 Minimal observability

A reviewer must be able to determine:

- which request was executed;
- which source and canonical dataset were used;
- which Metric definitions and periods/populations applied;
- which plan and engine version executed;
- what validation ran and with what outcome;
- what failed or became Undefined;
- which results became Admissible Evidence; and
- which Findings and Recommendations depended on them.

The registry and result bundle provide this view. Enterprise telemetry is unnecessary.

### 16.4 Operational logs versus Evidence Records

Operational logs record diagnostic events such as adapter selection, run stages, durations, and unexpected exceptions. They use structured fields including timestamp, run ID, component, event, severity, and safe details.

Logs are not Evidence Records. They may be rotated or redacted and cannot be the only location for parameters, results, validation outcomes, or lineage. Analytical records are durable, schema-validated artifacts with stable IDs.

### 16.5 Sensitive-data logging

Logs must not contain entire source rows, secrets, or unnecessary user content. Error records may include safe column names and governed check summaries but should avoid exposing raw sensitive values by default.

---

## 17. Physical Fixtures and Testing Architecture

### 17.1 Primary physical fixture representation

The MVP uses **YAML metadata plus tiny CSV input datasets** as its primary physical fixture representation.

Each fixture variant has its own YAML metadata file and one or more tiny CSV files. The metadata identifies:

- stable fixture and variant ID;
- applicable governing concept;
- dataset files and explicit mappings;
- canonical Business Question and `AnalysisRequest` fields;
- authoritative expected runtime and per-Metric outcomes;
- expected numerical values at governed precision where applicable;
- expected Data Sufficiency, validation, Evidence, qualification, and Claim metadata;
- prohibited outcome conditions; and
- fixture-format version.

One fixture variant has exactly one authoritative material expected outcome. Conditional phrases are not permitted in expected outcome fields.

### 17.2 Rationale

YAML is human-reviewable for structured expectations, while CSV is transparent for tiny tabular input data and directly exercises the primary intake path. The combination is easy to diff, inspect, hand-calculate, and execute. It avoids opaque binary fixture databases while allowing required source-adapter conformance cases for Excel and SQLite without duplicating the semantic suite.

JSON metadata is rejected as the primary format because governed fixture review benefits from concise comments-free but human-readable YAML structure. A single SQLite fixture database is rejected as primary because expected outcomes and source rows would be less reviewable. Excel and SQLite physical files are used for required adapter-conformance cases; they do not replace the primary representation.

No physical fixture is created by this document.

### 17.3 Testing layers

| Test layer | Purpose |
|---|---|
| Unit tests | Isolate pure contract, mapping, fingerprint, status, and helper behavior |
| Metric tests | Verify each approved Metric and governed edge conditions |
| Canonicalization tests | Confirm approved mappings/transforms and fail-closed ambiguity handling |
| Data Sufficiency tests | Verify prerequisite and per-Metric eligibility decisions |
| Validation tests | Verify every invariant independently from execution paths |
| Fixture conformance tests | Compare full output with the authoritative fixture variant outcome |
| Source-adapter conformance tests | Prove CSV, Excel, and SQLite converge to equivalent canonical semantics and deterministic results |
| Evidence traceability tests | Prove every admissible result has a complete, resolvable lineage |
| Skill/Engine contract tests | Ensure valid requests succeed structurally and invalid requests fail before execution |
| End-to-end tests | Exercise the canonical question from registered input through AnalysisResult and Claim metadata |

Pytest is the selected framework. Tests remain deterministic and local.

### 17.4 Source-adapter conformance coverage

Before MVP release, the test suite must include at least one controlled physical source-adapter conformance case for each approved MVP input type:

- CSV;
- Excel `.xlsx`; and
- SQLite.

Each case represents equivalent governed source data and must prove that its adapter converges to equivalent canonical semantics and deterministic analytical results. This is source-portability testing, not Metric duplication. The semantic fixture suite does not need to be duplicated across source types; most canonical analytical fixtures remain YAML metadata plus tiny CSV inputs.

If `.xlsm` is enabled, it requires its own controlled adapter-conformance coverage and must demonstrate that macros are not executed and only governed stored cell values are read. Legacy `.xls` remains unsupported unless a deliberate dependency and corresponding tests are separately approved.

### 17.5 Fixture runner flow

```text
Physical Fixture
→ Declared AnalysisRequest
→ Public Engine Application Service
→ Validation
→ AnalysisResult
→ Deterministic Expected-Outcome Comparison
→ Fixture Pass or Fail
```

The runner validates fixture schema, prohibits ambiguous expected outcomes, verifies stable identifiers, and reports exact mismatches. It compares Run Status, Metric State, Claim State, validation/failure details, and the Frozen fixture outcome as separate fields; it never substitutes the runtime vocabulary for the fixture’s authoritative outcome. It never edits a fixture, selects a more convenient expected outcome, or produces Benchmark scoring.

### 17.6 Narrative evaluation boundary

Deterministic fixture comparison covers structured behavior wherever possible: Claim type, admissibility, qualification requirement, supporting evidence references, failure state, and prohibited causal status. Narrative wording may require later semantic evaluation, but the architecture minimizes string matching by exposing these structured fields.

No LLM-as-judge benchmark is part of the MVP. A small number of exact required disclosures may later be tested through governed structured markers plus rendered-text presence, subject to separate approval.

---

## 18. Security and Data Safety

MVP security is proportional to local deterministic analysis:

- processing is local-first;
- no dataset is silently uploaded to an external service;
- source files are opened read-only and never overwritten;
- temporary files are isolated by run and cleaned according to explicit policy;
- dataset references and fingerprints prevent accidental source substitution;
- public fixtures and examples use only synthetic or publicly licensed data;
- secrets, credentials, proprietary datasets, and generated private artifacts are excluded from version control;
- SQLite sources are opened read-only;
- workbook macros are not executed;
- no arbitrary user-provided Python, SQL, shell, macro, or plugin code is executed;
- file paths are resolved within configured data/artifact roots;
- output rendering treats source text as data, not executable instructions; and
- operational logs minimize raw source content.

The LLM host’s handling of user data must be disclosed separately by the host integration. The deterministic engine does not create an external transfer path.

---

## 19. Versioning

The MVP uses a small set of coordinated version boundaries:

| Boundary | Versioned item | Why required |
|---|---|---|
| Contract | Request/result/evidence contract version | Parse and reproduce structured records |
| Canonical | Canonical schema and canonicalization rules version | Bind source-to-canonical meaning |
| Metric | Metric Registry release plus per-Metric definition refs | Bind formulas, dependencies, precision, undefined states |
| Engine | Package version | Identify execution behavior |
| Validation | Validation-rule-set release plus rule refs | Identify admissibility gates |
| Claim policy | Claim Admissibility Evaluator policy version | Reproduce material Claim permission and qualification decisions |
| Fixture | Fixture-format version and fixture variant version | Preserve authoritative expected outcomes |

These versions are recorded in each run manifest. The project should release compatible Metric, canonical, validation, and contract changes together where practical rather than creating excessive independent version streams.

A change that affects analytical meaning requires an approved governing-document change and a new relevant definition version. A refactor that preserves behavior may change the engine package version without changing Metric meaning.

---

## 20. Technology Stack

### 20.1 Selected stack

| Area | Decision | Rationale | Rejected alternatives | Reconsideration trigger |
|---|---|---|---|---|
| Language | Python | Strong tabular ecosystem, readable deterministic logic, simple packaging/testing, Skill integration | Multiple implementation languages | A required host cannot invoke Python/CLI or performance evidence requires a focused native component |
| Tabular engine | DuckDB | One reproducible SQL engine over canonical local data; strong grouping/join/CSV support; avoids source-specific Metric implementations | pandas-only, Polars, SQLite as universal engine | Measured incompatibility with governed semantics or deployment constraints |
| Intake | Narrow Python adapters using DuckDB CSV ingestion, `openpyxl` for `.xlsx`, and standard-library `sqlite3` in read-only mode | Keeps source quirks at the boundary and converges on one canonical path | Generic connector framework; pandas as a required execution layer | Approved new source types create repeated adapter requirements |
| Contracts | Pydantic models with derived JSON Schema | Runtime validation, explicit enums, JSON interoperability, host-independent serialization | Hand-written dictionaries, parallel manual JSON Schema, dataclasses alone | Dependency or packaging constraints outweigh validation benefits |
| Validation | Plain deterministic Python functions with a rule registry | Transparent, independently testable, no probabilistic behavior | Heavy data-quality framework, prompt validation | Rule scale or complexity demonstrably exceeds maintainable plain functions |
| Persistence | SQLite metadata registry plus immutable local artifacts | Local, inspectable, transactional references, minimal operations | Cloud database, graph database, file-only metadata | Concurrent multi-process workloads or approved deployment require stronger coordination |
| Primary API | In-process Python API plus thin CLI | Lowest complexity and strong testability with host-independent fallback | HTTP microservice, message bus | Approved packaging/client requirements demand a service |
| Fixtures | YAML metadata plus tiny CSV inputs | Human-reviewable, diffable, deterministic, easy to execute | SQLite-only, JSON-only, Excel-first | Source-format-specific coverage requires additional adapter fixtures |
| Testing | pytest | Standard, mature, simple parameterization and fixtures | Custom runner as sole test system | No expected trigger for MVP |
| Packaging | Single Python package | One developer, local runtime, clear module boundaries | Monorepo of services, containers as architecture | Distribution constraints later require additional packaging |

### 20.2 DuckDB and SQLite roles

DuckDB is the analytical execution engine. SQLite is the metadata/provenance store and one supported read-only source format. This separation prevents SQLite/DuckDB differences from producing separate Metric implementations. Any SQLite source data used for analysis passes through canonicalization into the DuckDB execution path.

### 20.3 Dependency discipline

Major dependencies are limited to those needed for:

- Pydantic contract validation;
- DuckDB deterministic tabular execution;
- `openpyxl` for stored-value `.xlsx` intake without macro execution;
- PyYAML using safe loading for fixture metadata; and
- pytest for tests.

The Python standard library handles hashing, SQLite metadata access, paths, timestamps, and JSON where sufficient. Dependency versions are locked for reproducible development and fixture runs. LangChain, LangGraph, CrewAI, AutoGen, LlamaIndex, RAG frameworks, vector databases, and generic plugin frameworks are unnecessary.

---

## 21. Repository and Module Structure

```text
ARCHITECTURE_SPECIFICATION.md
docs/
    frozen/
        PROJECT_MASTER_INSTRUCTIONS.md
        PRD.md
        CommerceLens_Skill_First_Scope_Migration_Analysis_v1.1.md
        SKILL_SCOPE_SPECIFICATION.md
        EVIDENCE_CONTRACT_SPECIFICATION.md
        CANONICAL_DATASET_AND_METRIC_DICTIONARY.md
        EVALUATION_FIXTURES_SPECIFICATION.md
    architecture_decisions/

src/
    commerce_lens/
        __init__.py
        application/
            analysis_service.py
            status_flow.py
        skill/
            SKILL.md                  # future artifact; not created by 09
            adapter.py
        contracts/
            requests.py
            sufficiency.py
            plans.py
            execution.py
            validation.py
            evidence.py
            results.py
            interpretation.py
        intake/
            registry.py
            csv_adapter.py
            excel_adapter.py
            sqlite_adapter.py
            inspection.py
        canonical/
            schema.py
            mappings.py
            canonicalizer.py
            quality_checks.py
        sufficiency/
            evaluator.py
            requirements.py
        metrics/
            registry.py
            definitions/
        engine/
            plan_builder.py
            populations.py
            executor.py
            comparisons.py
            contributions.py
            rankings.py
        validation/
            registry.py
            rules/
            validator.py
        evidence/
            identifiers.py
            records.py
            lineage.py
            admissibility.py
            claim_admissibility.py
        persistence/
            metadata_store.py
            artifact_store.py
            manifests.py
        fixture_runner/
            loader.py
            comparator.py
            runner.py
        cli/
            main.py

fixtures/
    metadata/                       # future YAML fixture variants
    data/                           # future tiny synthetic CSV inputs
    schemas/                        # derived/approved fixture-format schemas

tests/
    unit/
    contracts/
    intake/
        adapter_conformance/
    canonical/
    sufficiency/
    metrics/
    validation/
    evidence/
    fixtures/
    skill_engine/
    end_to_end/

examples/
    synthetic_data/
    requests/

runtime/                            # ignored generated local state
    registry/
    sources/
    canonical/
    runs/
    temporary/
```

The tree is a proposed implementation guide, not a requirement to create a file per concept. Small modules may be combined when ownership remains clear. Authoritative specifications, runtime code, physical fixtures, tests, examples, and generated runtime artifacts remain separate.

The future `SKILL.md` must not carry duplicated KPI formulas. It invokes the application service using governed contracts and refers to Metric IDs and engine capabilities.

---

## 22. Component and Capability Classification

| Component or capability | Classification | Decision |
|---|---|---|
| Governed Skill workflow | Core | Required orchestration and interpretation boundary |
| Structured request/result contracts | Core | Required fail-closed interface |
| Metric Registry | Core | Single authority for approved Metric definitions |
| Canonicalization and Data Sufficiency | Core | Required before deterministic execution |
| Deterministic Analytics Engine | Core | Required numerical authority |
| Deterministic Validation | Core | Required Evidence gate |
| Evidence/provenance records | Core | Required traceability |
| Deterministic Claim Admissibility Evaluator | Core | Prevents the Skill from self-authorizing material Claims |
| CSV, Excel, SQLite intake | MVP | Approved source formats |
| CSV/Excel/SQLite adapter-conformance coverage | MVP | Required source-portability proof before release |
| Local SQLite/artifact persistence | MVP | Reproducibility and auditability |
| YAML + CSV physical fixtures | MVP | Implementation conformance |
| Fixture runner | MVP | Deterministic product quality control |
| Thin CLI | MVP | Reuse and host independence without services |
| Product/category contribution | MVP | Required canonical-question depth |
| Additional approved Metrics/questions | Phase 2 | Only after separate approval and validation |
| Additional input adapters | Phase 2 | Add only from demonstrated use |
| External Evidence sources | Phase 3 | Requires Evidence governance extension |
| Enterprise connectors | Backlog | Not needed for current validation |
| Separate Decision Reliability Benchmark layer | Backlog | Fixtures first; no current product layer |
| Multi-Agent architecture | Rejected for MVP / Research | No correctness need demonstrated |
| RAG and vector database | Rejected for MVP | Small governed specification set and deterministic contracts |
| Network microservices | Rejected for MVP | Adds operations without analytical value |
| Automatic web explanation lookup | Rejected for MVP | Risks unsupported causal/external claims |
| Forecasting, causal inference, optimizer | Rejected for MVP | Outside approved analytical scope |
| Generic connector/plugin framework | Rejected for MVP | Premature platform abstraction |

---

## 23. Architecture Decisions

### ADR-01 — Skill-first architecture

**Status:** Approved  
**Context:** The approved direction is CommerceLens Skill plus reusable deterministic engine.  
**Choice:** Keep orchestration/interpretation in one governed Skill and analytical authority in one deterministic package.  
**Rationale:** Directly implements approved behavior while keeping the differentiating Claim-governance layer visible.  
**Rejected alternatives:** Standalone dashboard-first product; generic Chat-with-Data platform; separate Benchmark product layer now.  
**Consequences:** Skill and engine contracts become the critical integration surface.  
**Reconsideration trigger:** Main Project Review changes the approved product direction.

### ADR-02 — Deterministic numerical boundary

**Status:** Approved  
**Context:** Material numerical Claims require reproducible execution and validation.  
**Choice:** All governed KPI/population arithmetic, checks, and evidence generation run in deterministic software.  
**Rationale:** Prevents LLM arithmetic and semantic invention from becoming authority.  
**Rejected alternatives:** LLM-only calculation; prompt-only validation; arbitrary generated SQL as authority.  
**Consequences:** Every result requires a request, plan, execution, and validation record.  
**Reconsideration trigger:** None within the governing principle.

### ADR-03 — Engine interface

**Status:** Approved  
**Context:** Integration must be simple, testable, reproducible, and host-independent.  
**Choice:** In-process Python API with a thin JSON-compatible CLI adapter.  
**Rationale:** Minimal operational complexity with both typed integration and process-boundary reuse.  
**Rejected alternatives:** Local HTTP API; direct scripts; natural-language engine interface.  
**Consequences:** Non-Python hosts use the CLI until a service is justified.  
**Reconsideration trigger:** Approved deployment requirements demonstrate a network API need.

### ADR-04 — Tabular execution technology

**Status:** Approved  
**Context:** CSV, Excel, and SQLite must share consistent computation.  
**Choice:** DuckDB executes canonical tabular analysis; Python controls intake and orchestration.  
**Rationale:** One local SQL execution path supports transparent, testable grouping and reconciliation.  
**Rejected alternatives:** pandas-only, Polars, source-native execution, SQLite as both registry and universal analytical engine.  
**Consequences:** All source adapters must converge on governed canonical tables.  
**Reconsideration trigger:** Verified semantic, packaging, or performance limitations against approved fixtures.

### ADR-05 — Contract representation

**Status:** Approved  
**Context:** Fail-closed behavior requires explicit typed statuses and references.  
**Choice:** Pydantic runtime models serialized to JSON-compatible records; derive JSON Schema.  
**Rationale:** Strong boundary validation and straightforward host/CLI interchange.  
**Rejected alternatives:** Unvalidated dictionaries, duplicated manual schemas, prompt-only contracts.  
**Consequences:** Contract version changes must be explicit and tested.  
**Reconsideration trigger:** A target environment cannot support the dependency.

### ADR-06 — Local persistence

**Status:** Approved  
**Context:** Runs and Evidence must be reproducible without enterprise infrastructure.  
**Choice:** SQLite metadata registry plus immutable local artifact files.  
**Rationale:** Minimal, inspectable, transactional linkage without large database blobs.  
**Rejected alternatives:** File-only metadata, graph database, cloud database, distributed storage.  
**Consequences:** One local writer is the default; artifact paths and fingerprints are first-class.  
**Reconsideration trigger:** Approved concurrency, collaboration, or deployment requirements exceed local storage.

### ADR-07 — Physical fixture representation

**Status:** Approved  
**Context:** Fixtures need one authoritative outcome, tiny inputs, human review, and deterministic execution.  
**Choice:** YAML metadata plus tiny CSV inputs.  
**Rationale:** Clear diffs and hand-reviewable data/expectations.  
**Rejected alternatives:** SQLite-only, Excel-first, opaque binary bundles, narrative-only expected outcomes.  
**Consequences:** Adapter-specific SQLite/Excel fixtures may supplement but do not replace the primary format.  
**Reconsideration trigger:** A governed fixture cannot be represented without material ambiguity.

### ADR-08 — No Multi-Agent architecture

**Status:** Rejected for MVP; Research only  
**Context:** The workflow needs governance, deterministic calculation, and validation, not multiple conversational actors.  
**Choice:** One Skill/orchestration layer plus deterministic engine and validation/evidence contracts.  
**Rationale:** Multiple agents add nondeterminism, coordination cost, duplicated authority, and harder auditability without improving required arithmetic correctness.  
**Rejected alternatives:** Planner/executor/reviewer agent swarm; autonomous self-review agents.  
**Consequences:** Review is implemented through deterministic validation and fixtures.  
**Reconsideration trigger:** Controlled experiments show a specific approved task cannot meet quality requirements with one Skill and deterministic tools.

### ADR-09 — No RAG or vector database

**Status:** Rejected for MVP  
**Context:** The authoritative knowledge base is a small Frozen document set and governed machine contracts.  
**Choice:** Package approved definitions directly as versioned deterministic registries and references.  
**Rationale:** Retrieval adds ranking uncertainty and infrastructure while formula authority must be exact.  
**Rejected alternatives:** Vector retrieval of KPI definitions; general project-document RAG.  
**Consequences:** Approved definition changes require explicit package/version updates.  
**Reconsideration trigger:** The approved corpus grows beyond direct governed packaging and retrieval accuracy can be validated without weakening authority.

### ADR-10 — No network microservices

**Status:** Rejected for MVP  
**Context:** One developer and a local-first analytical workflow do not require distributed deployment.  
**Choice:** One process and one package with logical module boundaries.  
**Rationale:** Reduces failure modes, security surface, serialization drift, and operations.  
**Rejected alternatives:** API gateway, separate execution/validation services, event bus.  
**Consequences:** Scaling and remote concurrency are deferred.  
**Reconsideration trigger:** Approved production usage demonstrates multi-user isolation, remote execution, or independent scaling needs.

---

## 24. End-to-End MVP Flow

1. The user provides a Business Question and a local CSV, Excel, or SQLite source.
2. The Skill performs a scope check against the approved canonical question.
3. If required scope, periods, mapping, or source selection is missing, the Skill returns Clarification Required and does not execute.
4. The Skill identifies approved Metrics, hypotheses, Required Evidence, scope, grouping, and requested outputs.
5. The Skill creates a schema-valid `AnalysisRequest`; free-form prose remains non-executable context.
6. Intake registers the immutable source, fingerprints it, inspects schema/sheets/tables, and creates a Dataset Reference.
7. Canonicalization applies only authorized mappings and transformations and creates a Canonical Dataset Reference plus Canonicalization Record.
8. Data Quality checks and Data Sufficiency compare Required and Available Evidence per Metric chain.
9. Blocked chains receive explicit Insufficient Evidence, Data Quality, or Undefined states. If every chain is blocked, execution stops fail-closed.
10. The plan builder derives a small `ExecutionPlan` for eligible chains only.
11. The engine constructs governed populations and deterministically calculates approved total, period-comparison, product, and category Metrics.
12. Execution produces an Execution Record and Executed Results.
13. The validation layer independently runs required invariants and reconciliation checks.
14. Passing results become Validated Results; failed results remain blocked and cannot become Evidence.
15. The evidence builder creates Admissible Evidence records for eligible validated chains and completes traceability links.
16. The application service returns one `AnalysisResult` containing valid, Undefined, blocked, and failed chains without collapsing them.
17. The Skill creates structured Claim candidates with candidate type and intended scope.
18. The deterministic Claim Admissibility Evaluator checks governed policy, Required Evidence, available Admissible Evidence, supporting Validated Results, assumptions, limitations, and required qualifications, then returns a `ClaimDecision`.
19. The Skill renders only Admissible or Qualified Admissible Claims as Findings. Unsupported causal possibilities remain Alternative Explanations.
20. The Skill creates only bounded Recommendations linked to Findings and preserves Human Decision Ownership.
21. The final response includes Findings, qualifications, Alternative Explanations, Recommendations, assumptions, limitations, and traceable Evidence references appropriate to the host.

At every stage, a failure blocks only dependent downstream paths unless the failed condition affects the shared dataset or population required by all requested Metrics.

---

## 25. Conceptual Architectural Walkthrough

The following values are synthetic and illustrate architecture only; they do not change any Frozen fixture or Metric semantics.

1. A user asks how Revenue changed between two explicitly supplied comparable periods and which products or categories contributed most.
2. The Skill recognizes the canonical supported question, selects the approved Revenue Change and contribution Metrics, records the two periods and product/category grouping, and creates an `AnalysisRequest`.
3. Intake fingerprints a synthetic CSV and records its schema. Canonicalization applies an authorized mapping to the approved canonical fields without changing the source.
4. Data Sufficiency verifies the governed requirements for periods, currency, line identity, monetary value, eligibility, product identity, and category attribution. The applicable checks pass.
5. The plan builder creates explicit total, product, and category calculation nodes plus required validation-rule references.
6. The engine constructs the two eligible populations. It calculates synthetic Baseline Revenue of 1,000 units and Comparison Revenue of 1,120 units, then produces a synthetic Revenue Change of 120 units and grouped contribution results.
7. The validator checks that the product contributions reconcile to 120 units and that the category contributions reconcile to 120 units at authoritative precision. All required checks pass.
8. The evidence builder links the synthetic source fingerprint, canonicalization, Metric references, execution, validations, and Validated Results. It creates Admissible Evidence for the descriptive Revenue Change and contribution Findings.
9. The Skill proposes structured descriptive Claim candidates. The deterministic Claim Admissibility Evaluator confirms their supported scope, Admissible Evidence, required qualification, and Claim State. The Skill may then render the authorized Finding that Revenue increased by the validated amount and identify the authorized leading positive/negative contributors within the governed scope.
10. A statement that a promotion caused the increase lacks causal Evidence. It remains a labeled Alternative Explanation, not a Finding. Any Recommendation is bounded—for example, inspect the contributing products and verify promotional context before acting—and remains subject to human decision.

---

## 26. Architectural Invariants

1. No material numerical Finding exists without deterministic execution.
2. No Executed Result becomes material Evidence without all required validation.
3. No material Claim exists without traceable Admissible Evidence.
4. The LLM cannot override validation failure.
5. The Skill cannot self-authorize the admissibility of its own material Claim.
6. Qualification cannot substitute for failed required validation.
7. Metric formulas have one governed authority.
8. Source data is not silently modified.
9. Missing values are not silently converted to zero.
10. Unknown currency is not inferred.
11. Duplicate ambiguity is not silently resolved.
12. Contribution is not causation.
13. Independent valid chains survive unrelated failures.
14. Host choice cannot change analytical semantics.
15. Fixture expected outcomes cannot change for implementation convenience.
16. The engine does not parse conversational history as analytical intent.
17. Data Sufficiency occurs before affected deterministic execution.
18. Executed Result and Validated Result remain distinct types/states.
19. Every admissible result resolves to dataset, Metric, execution, and validation records.
20. Alternative Explanations remain distinct from Findings unless separately supported.
21. Recommendations resolve to supporting Findings and preserve Human Decision Ownership.
22. One fixture variant has one authoritative material expected outcome.

---

## 27. Rejected MVP Architecture Patterns

| Pattern | Decision | Reason |
|---|---|---|
| LLM-only calculation | Rejected | Not reproducible or an acceptable numerical authority |
| Prompt-only validation | Rejected | Cannot structurally block invalid Evidence |
| Generic Text-to-SQL as core product | Rejected | Generates execution syntax but does not govern Metrics, sufficiency, validation, or Claims |
| Autonomous Multi-Agent swarm | Rejected | Adds nondeterminism and authority ambiguity without required analytical value |
| RAG/vector database | Rejected | Small governed corpus requires exact references, not approximate retrieval |
| Microservices | Rejected | Operational complexity without MVP value |
| Distributed event bus | Rejected | No asynchronous distributed workflow requirement |
| Cloud-first infrastructure | Rejected | Conflicts with local-first simplicity and data-safety priorities |
| Custom database engine | Rejected | Existing deterministic tabular engines are sufficient |
| Custom query language | Rejected | A small explicit plan structure is sufficient |
| Enterprise semantic layer | Rejected | Exceeds current Metric/question scope |
| Arbitrary plugin framework | Rejected | Approved fixed adapters and capabilities are sufficient |
| Automatic web explanation lookup | Rejected | External explanations would remain ungoverned hypotheses and may imply causality |
| Benchmark infrastructure inside runtime | Rejected | Fixtures test the product; separate Benchmark product/scoring is not authorized |
| Multiple Metric implementations by source type | Rejected | Creates semantic drift across CSV, Excel, and SQLite |

---

## 28. Architecture Risks

| Risk | Impact | Mitigation | Residual limitation |
|---|---|---|---|
| Skill/Engine contract drift | Skill requests or interprets fields the engine does not govern | Versioned contracts, generated JSON Schema, contract tests, reject unknown values | Coordinated releases remain necessary |
| Duplicated Metric logic | Different formulas in prompts, fixtures, and engine | Single Metric Registry; reference IDs everywhere; review forbids formula duplication | Human documentation can still become stale |
| Canonicalization ambiguity | Incorrect field meaning corrupts every downstream result | Explicit mappings, fail-closed checks, immutable records, fixture coverage | Some real datasets will require clarification or remain unsupported |
| Host coupling | One host’s prompt/tool conventions leak into engine | Host-independent JSON contracts, in-process service plus CLI | Skill packaging remains host-specific at the outer adapter |
| Evidence-record complexity | Excess records slow implementation or become inconsistent | Minimal normalized record types, one lineage builder, run manifest, evidence tests | Traceability adds unavoidable implementation overhead |
| Fixture/implementation divergence | Code passes unit tests but violates authoritative scenarios | Public application service used by fixture runner; frozen expected outcomes; conformance tests | Narrative nuances still need later review |
| DuckDB/SQLite semantic differences | Source-specific behavior changes results | SQLite is intake-only; canonical data always uses DuckDB; adapter tests | Type/date conversion differences must still be surfaced during intake |
| Excel ingestion ambiguity | Stale formulas, merged headers, or sheet ambiguity can mislead | Stored-value policy, explicit sheet selection, schema inspection, fail closed | Some workbooks cannot be supported without preprocessing |
| Precision inconsistency | Reconciliation or rankings disagree across stages | Central precision rules; validation at authoritative precision; no prose-derived values | Display tooling must respect result metadata |
| Excessive abstraction | One developer spends time on framework rather than validation | Single package, no services/DSL/plugins, implementation sequence begins with contracts and Metrics | Some refactoring may be needed after MVP learning |
| LLM exceeds Evidence | Unsupported causal or prescriptive language reaches users | Deterministic Claim Admissibility Evaluator, structured Claim decisions, authorized-decision-only Finding path, narrative contract tests | Deterministic policy cannot fully understand arbitrary prose; unsupported structures remain fail-closed and continued evaluation is required |
| Dependency behavior changes | Updated parsers or engine versions alter outcomes | Locked versions, engine/dependency capture, fixture suite | Security updates may require controlled revalidation |
| Local artifact mutation | Reproduction fails if generated files are edited | Fingerprints, append-only finalized run directories, manifest checks | Local filesystem access cannot be made tamper-proof in MVP |
| Per-Metric failure propagation bug | One failure incorrectly blocks or permits another result | Explicit dependency graph in simple plan, per-Metric statuses, partial-completion fixtures | Dependency definitions require careful review |

---

## 29. Implementation Sequence After Approval

Implementation may begin only after Main Project Review approves and Freezes this Architecture. The recommended order is:

1. Establish package skeleton, version policy, and contract models.
2. Implement stable identifiers, fingerprints, local artifact layout, and SQLite metadata registry.
3. Implement Dataset Registration and read-only CSV, Excel, and SQLite intake inspection.
4. Implement the governed canonical schema, explicit mapping contract, and canonicalization records.
5. Implement deterministic Data Quality and Data Sufficiency checks before Metric execution.
6. Encode the approved Metric Registry and validation-rule references without semantic changes.
7. Implement period and eligible-population construction.
8. Implement Revenue, Orders, and AOV deterministic calculations with Metric tests.
9. Implement period comparisons, including governed Undefined behavior.
10. Implement product/category grouping, entity union, contribution, and rankings.
11. Implement the distinct deterministic validation layer and reconciliation records.
12. Implement Validated Result, Admissible Evidence, and complete lineage generation.
13. Implement `AnalysisResult`, partial completion, failure propagation, and run manifests.
14. Materialize the approved physical fixtures as YAML plus tiny CSV without changing expected outcomes.
15. Implement the fixture loader, comparator, and conformance runner without Benchmark scoring.
16. Add evidence traceability, contract, and end-to-end canonical workflow tests.
17. Add controlled CSV, `.xlsx`, and SQLite source-adapter conformance cases without duplicating the semantic fixture suite.
18. Implement the deterministic Claim Admissibility Evaluator and `ClaimDecision` contract.
19. Implement the public in-process application API and thin CLI over the same service.
20. Write the separate governed `SKILL.md` and host adapter against the frozen contracts.
21. Validate structured Claim/Finding/Alternative Explanation/Recommendation behavior.
22. Build the minimum product demo or UI last.

This order first proves analytical semantics and traceability, then integration, then presentation.

---

## 30. Architecture Traceability Matrix

No requirement IDs are invented. The matrix maps architecture areas to governing document concepts.

| Architecture area | Governing document concept(s) |
|---|---|
| Priority order and governing principle | `PROJECT_MASTER_INSTRUCTIONS.md`: Evidence First, analytical correctness, traceability, reproducibility, limitations, Human Decision Ownership |
| Canonical Business Question and MVP boundary | `PRD.md`: product vision, Product Success Definition, MVP scope and user journey |
| Skill-first plus reusable engine | `CommerceLens_Skill_First_Scope_Migration_Analysis_v1.1.md`: Skill-first migration and retained deterministic capability |
| Skill behavioral states and LLM boundary | `SKILL_SCOPE_SPECIFICATION.md`: behavioral workflow, scope, clarification, Metric definition, Required Evidence, execution/validation, failure branches |
| Claim taxonomy, admissibility, Evidence lifecycle, Findings and Recommendations | `EVIDENCE_CONTRACT_SPECIFICATION.md`: Required Evidence, Available Evidence, Validated Result, Admissible Evidence, Claim governance and traceability |
| Canonical schema, population, identity, monetary/eligibility authority, Metrics and precision | `CANONICAL_DATASET_AND_METRIC_DICTIONARY.md`: canonical contract and approved Metric authority |
| Data Quality and deterministic validation checks | `CANONICAL_DATASET_AND_METRIC_DICTIONARY.md` plus `EVALUATION_FIXTURES_SPECIFICATION.md`: governed edge conditions and expected material outcomes |
| Partial completion, separated status domains, and fail-closed behavior | `SKILL_SCOPE_SPECIFICATION.md` failure branches and `EVIDENCE_CONTRACT_SPECIFICATION.md` admissibility boundary |
| Physical fixture format and runner | `EVALUATION_FIXTURES_SPECIFICATION.md`: fixture variants, deterministic evaluation, one authoritative expected outcome |
| No separate Benchmark scoring/product layer | `PROJECT_MASTER_INSTRUCTIONS.md`, `PRD.md`, and Skill-first migration analysis: staged product layers and current scope |
| Repository and technology decisions | Derived implementation requirements needed to operationalize all seven Frozen documents without changing their semantics |

---

## 31. Acceptance Criteria

Main Project Review approved and Froze this Architecture after confirming all of the following:

1. It derives from the seven Frozen governing artifacts and does not reopen product, Metric, Claim-admissibility, or fixture-outcome decisions.
2. It preserves the Skill-first direction and current canonical MVP Business Question.
3. Skill, host LLM, deterministic engine, validation, evidence, and deterministic Claim-admissibility responsibilities are explicit.
4. The LLM has no numerical authority and cannot override deterministic failures.
5. The Skill-to-engine boundary uses a structured, host-independent `AnalysisRequest` and `AnalysisResult`.
6. Source and canonical data are separate, immutable, fingerprinted, and linked through a Canonicalization Record.
7. Canonicalization owns only approved transformations and propagates ambiguity rather than guessing.
8. Data Sufficiency is an explicit stage that evaluates Required Evidence, Available Evidence, Data Quality, Metric Undefined conditions, and per-Metric execution eligibility.
9. Data Quality checks derive from the Frozen canonical and fixture semantics and do not invent quality scores.
10. Approved Metric authority is centralized in a versioned Metric Registry rather than prompts.
11. The deterministic engine owns population, aggregation, comparison, contribution, ranking, and precision operations while excluding causal explanation and narrative.
12. The `ExecutionPlan` is small and explicit, not a generic planner or DSL.
13. DuckDB and Python responsibilities are unambiguous and provide one canonical execution path for all source formats.
14. Execution and validation are separate stages and records; Executed Result is not Validated Result.
15. Required invariants, reconciliation, zero-denominator, precision, and non-additive Orders behavior are validation concerns.
16. Validation outcomes are structured and contain no invented confidence score.
17. Evidence and provenance records are generated structurally during execution and validation.
18. Simple stable references replace a graph database for MVP lineage.
19. `AnalysisResult` keeps Run Status, Metric State, Claim State, validation/failure details, and fixture outcomes in separate domains.
20. Claim governance operationalizes descriptive, diagnostic, predictive, causal, and prescriptive distinctions through a lightweight deterministic Claim Admissibility Evaluator without a theorem prover or LLM-as-judge.
21. Findings require an Admissible or Qualified Admissible `ClaimDecision`; Executed-but-unvalidated output, LLM intuition, and Skill self-authorization cannot become Findings.
22. Alternative Explanations remain hypotheses unless separately evidenced.
23. Recommendations link to Findings, remain proportional, and preserve Human Decision Ownership.
24. Unsupported Scope, Clarification Required, Insufficient Evidence, Data Quality Failure, Undefined Metric, execution failure, validation failure, Inadmissible Claim, and partial completion remain represented at their correct request, Metric, Claim, Run Status, or failure-detail level.
25. Fail Closed is a structural behavior of blocked analytical chains through typed boundaries and absent admissible-evidence/Claim permission, not a flat peer status or prompt-only instruction.
26. Provenance identifies datasets, definitions, requests, plans, execution, validation, precision, versions, and artifacts needed for reproduction.
27. Local-first data-safety boundaries prohibit silent upload, source mutation, arbitrary code, and proprietary public fixtures.
28. The primary engine interface is an in-process Python API with a thin CLI; no network service is required.
29. The repository structure separates Frozen specifications, runtime code, fixtures, tests, examples, and generated artifacts.
30. The future `SKILL.md` is located but not written and cannot duplicate authoritative KPI formulas.
31. The physical fixture strategy remains YAML metadata plus tiny CSV inputs, with one authoritative outcome per variant.
32. Unit, Metric, canonicalization, sufficiency, validation, fixture, evidence, contract, source-adapter conformance, and end-to-end test layers are defined; CSV, `.xlsx`, and SQLite each require at least one controlled conformance case before MVP release.
33. The fixture runner uses the public application service and produces deterministic pass/fail without Benchmark scoring.
34. Narrative evaluation is separated from deterministic structured evaluation and no LLM-as-judge system is introduced.
35. Minimal observability and structured logging are defined, and logs do not substitute for Evidence Records.
36. Version boundaries are sufficient to reproduce authoritative semantics without excessive version fragmentation.
37. A minimal concrete stack is selected: Python, DuckDB, Pydantic, deterministic Python validation, SQLite/local artifacts, pytest, and a simple package.
38. Major dependencies are justified and unnecessary agent/RAG/framework dependencies are excluded.
39. Multi-Agent architecture is explicitly rejected for MVP and retained only as Research subject to evidence.
40. RAG and vector databases are explicitly rejected for MVP.
41. Current analysis does not depend on external web search or external explanations.
42. Major components are classified as Core, MVP, later phase, Research, Backlog, or Rejected.
43. Material decisions are recorded with context, rationale, rejected alternatives, consequences, and reconsideration triggers.
44. End-to-end data flow, evidence lineage, deterministic Claim-decision flow, and separated runtime status domains are explicit.
45. The conceptual walkthrough uses synthetic values and preserves causal boundaries.
46. Architectural invariants explicitly protect numerical authority, Evidence, source immutability, missingness, currency, duplicates, contribution semantics, partial completion, host independence, and fixture authority.
47. Major rejected MVP patterns are documented.
48. Material architecture risks include impact, mitigation, and residual limitation.
49. The implementation sequence proves contracts, data, Metrics, validation, and Evidence before Skill polish or UI.
50. An engineer can identify required modules, ownership, inputs/outputs, deterministic operations, failure propagation, fixture testing, approved technologies, and excluded capabilities.
51. No runtime code, implementation SQL, physical fixture, test, `SKILL.md`, UI, deployment infrastructure, or Benchmark scoring is included.
52. The architecture remains implementable by one developer and appropriately small for MVP.
53. It does not become a universal analytics platform or AI-engineering showcase.
54. Analytical correctness remains the primary design criterion.
55. Every material result remains reproducible and evidence-traceable.

---

## 32. Open Questions Reserved for Later Work

The architectural fundamentals are resolved in this document. The following details may be settled during implementation or later approved artifacts without changing architecture semantics:

- exact Python function, class, and CLI command names;
- exact locked package versions after compatibility testing;
- exact YAML key names and generated schema layout for physical fixtures;
- installation and deployment packaging for the selected host;
- UI framework and visual presentation after end-to-end correctness is proven;
- marketplace packaging requirements for the CommerceLens Skill;
- retention duration and cleanup controls for local run artifacts;
- future Benchmark scoring, only in a separately approved Benchmark phase; and
- exact extension process for newly approved Metrics, questions, adapters, or external Evidence.

None of these questions permits changing Frozen Metric semantics, Evidence admissibility, or fixture expected outcomes.

---

## 33. Definition of Architecture Complete

This Architecture is complete when an implementation engineer can answer:

- which modules must be built and what each owns or must not own;
- which structured data enters and exits every material boundary;
- where canonicalization, sufficiency, deterministic execution, and deterministic validation occur;
- how Validated Results become Admissible Evidence;
- how the Skill invokes the engine, proposes Claim candidates, and receives deterministic material Claim decisions;
- how each failure propagates and how partial completion is preserved;
- how every material result can be reproduced;
- how physical fixtures will test authoritative outcomes;
- which technologies are approved; and
- which tempting but unnecessary systems are explicitly excluded.

A component diagram alone is not sufficient.

---

## 34. Release Boundary

This Architecture Specification is **v1.0 — Approved — Frozen — 2026-08-24**.

Implementation may begin only according to the approved implementation sequence and only when separately directed by the Main Project. No runtime Python, SQL, physical fixtures, tests, `SKILL.md`, UI, Benchmark scoring, network service, or deployment infrastructure is created in this Architecture conversation.

After delivery of this Frozen document, work stops at the Architecture boundary.
