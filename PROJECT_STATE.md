# CommerceLens AI — Project State

## Purpose

This file records the current implementation and governance state of CommerceLens AI.

It is an operational project-state ledger.

It does not replace, amend, reinterpret, or override any Approved / Frozen specification under `docs/frozen/`.

If this file conflicts with a Frozen governing document, the Frozen governing document prevails.

---

## Current Product Direction

CommerceLens AI remains:

> An evidence-driven e-commerce decision intelligence system that follows a structured analyst workflow and requires every material conclusion to be supported by reproducible evidence.

Governing principle:

> No material claim without traceable evidence.

Current delivery model:

CommerceLens Skill
↓
Reusable Deterministic Analytics Engine
↓
Decision Reliability Benchmark

The Decision Reliability Benchmark is not part of the current implementation phase except for governed MVP evaluation requirements.

---

## Frozen Governing Specifications

The following remain Approved / Frozen and must not be modified without Main Project approval:

1. PROJECT_MASTER_INSTRUCTIONS.md v1.1
2. PRD.md v1.1
3. CommerceLens_Skill_First_Scope_Migration_Analysis_v1.1.md
4. SKILL_SCOPE_SPECIFICATION.md v1.0
5. EVIDENCE_CONTRACT_SPECIFICATION.md v1.0
6. CANONICAL_DATASET_AND_METRIC_DICTIONARY.md v1.0
7. EVALUATION_FIXTURES_SPECIFICATION.md v1.0
8. ARCHITECTURE_SPECIFICATION.md v1.0

---

## Implementation Status

### Phase 1 — Deterministic Foundation

Status:

APPROVED

State:

FROZEN

Implemented foundation includes:

- repository/package structure;
- typed contracts;
- governed Run / Metric / Claim state separation;
- stable IDs and SHA-256 fingerprints;
- safe local artifact store;
- SQLite metadata registry;
- dataset registration;
- read-only CSV inspection;
- read-only `.xlsx` inspection;
- read-only SQLite inspection;
- source immutability and fail-closed intake behavior.

Phase 1 must not be reopened without a specific implementation defect or governing conflict.

---

### Phase 2 — Canonicalization, Data Quality, and Data Sufficiency

Status:

APPROVED

State:

FROZEN

Implemented foundation includes:

- explicit source-to-canonical mapping;
- canonical schema representation;
- deterministic canonicalization;
- canonical dataset references;
- canonicalization provenance;
- governed Decimal monetary normalization;
- exact supported monetary artifact semantics;
- composite order-line identity checks;
- product identity authority;
- governed `Unclassified` category handling;
- explicit eligibility semantics;
- currency checks;
- period and coverage prerequisites;
- Data Quality results;
- deterministic Data Sufficiency evaluation;
- per-chain execution eligibility;
- Phase 1 → Phase 2 metadata migration.

Phase 2 must not be reopened without a specific implementation defect or governing conflict.

---

## Current Production Execution Foundation

The currently Frozen Architecture specifies:

DuckDB

as the primary tabular execution engine and common canonical analytical execution path.

This remains the authoritative production architecture unless a formally approved Architecture Amendment changes it.

No alternative execution foundation is currently adopted.

---

## Completed Technical Decision

Decision ID:

R-001

Decision:

Wren Foundation Feasibility

Status:

COMPLETED / CLOSED

Independent review outcome:

REVIEW CONFIRMED

Final Main Project decision:

KEEP DUCKDB

Wren production status:

NOT ADOPTED

Wren future classification:

REFERENCE / FUTURE RE-EVALUATION CANDIDATE

Architecture Amendment:

NOT REQUIRED

The Frozen Architecture choice of DuckDB remains authoritative.

---

## R-001 Closure Summary

R-001 is complete and no longer blocks the next separately authorized implementation slice.

Wren demonstrated local Core isolation and semantic/execution capability, but the tested MVP path did not provide sufficient incremental value to justify adoption given derived-metric Decimal handling, tested relationship-path limitations, adapter/dependency surface, and the amount of CommerceLens governance that would remain necessary.

This conclusion does not claim Wren has no value.

DuckDB remains the production execution foundation.

Phase 3 may begin only through a separately authorized task.

---

## Explicitly Not Authorized by R-001

R-001 does not authorize:

- modification of Frozen Architecture;
- replacement of DuckDB in production code;
- modification of Phase 1 or Phase 2 production behavior;
- Wren GenBI integration;
- Wren LLM features;
- RAG;
- Multi-Agent product architecture;
- UI;
- marketplace/database connector expansion;
- Claim policy changes;
- Evidence Contract changes;
- physical Evaluation Fixture redesign;
- Metric semantic changes;
- Benchmark scoring.

Research must remain isolated from production implementation.

---

## Current Main-Branch Production State

The main CommerceLens implementation must remain based on the Approved / Frozen Phase 1 and Phase 2 implementation.

R-001 must not silently modify production execution architecture.

Any Wren experiment should be isolated in a research boundary or separate worktree/task.

---

## R-001 Architecture Consequence

No Architecture Amendment is required.

DuckDB remains the Frozen production execution foundation.

Wren is not adopted into production.

Wren may be reconsidered later if material capabilities or project requirements change.

---

## Next Authorized Work

R-001 no longer blocks the next separately authorized implementation slice.

Phase 3 implementation is NOT yet authorized.

Do not begin:

- Metric Registry production implementation;
- governed population execution;
- Revenue production execution;
- Orders production execution;
- AOV production execution;
- Contribution production execution;
- Metric validation implementation;

until the R-001 foundation decision has completed Main Project Review.

---

## Human / Main Project Approval Required Before

Codex must stop and request Main Project review before:

- modifying any Frozen governing document;
- changing Metric semantics;
- changing canonical analytical semantics;
- changing Evidence Contract semantics;
- changing fixture expected outcomes;
- replacing DuckDB production responsibilities;
- adopting Wren into production;
- adding a major runtime framework or dependency;
- beginning Phase 3 after the R-001 decision;
- merging a research result into the production execution path.

---

## Current Project State Summary

Phase 1:
APPROVED / FROZEN

Phase 2:
APPROVED / FROZEN

Production execution architecture:
DuckDB per Frozen Architecture v1.0

Current research decision:
R-001 Wren Foundation Feasibility

Wren status:
Foundation Candidate — Not Adopted

Current authorized implementation:
R-001 research only

Phase 3:
NOT AUTHORIZED
