# R-001 — Wren Foundation Decision

## Status

COMPLETED / CLOSED

## Decision

KEEP DUCKDB

## Decision Basis

- Wren Core ran locally without GenBI, LLM, RAG, UI, Docker, or persistent Wren server.
- Revenue and Orders matched the research reference on the tested path.
- Tested Wren AOV execution produced double semantics; casting afterward did not restore exact pre-rounding Decimal semantics.
- Independent review determined this was not proven as a universal Wren limitation, but using Wren did not remove CommerceLens-owned exact derived-metric handling.
- Relationship traversal failed on the tested wrenai 0.13.3 Python SDK / DuckDB path despite targeted controls.
- CommerceLens can construct sufficient execution provenance around Wren; provenance was therefore not treated as a decisive negative.
- Wren provided semantic compilation above DuckDB rather than replacing the physical DuckDB backend in the tested path.
- Research adapter/tests/collector were approximately 734 LOC.
- Research environment was approximately 586 MB with approximately 110 top-level site-package entries and substantial additional dependencies.
- Independent review outcome was REVIEW CONFIRMED.
- No production or Frozen files were changed by the research.

## Interpretation

Wren demonstrated real reusable semantic/execution capability.

The decision is not that Wren is technically unusable.

The evidence indicates that for the current CommerceLens MVP, Wren does not provide enough incremental benefit to justify the added dependency, adapter, precision-handling, and tested relationship-path complexity.

## Architecture Consequence

- DuckDB remains the Frozen production execution foundation.
- No Architecture Amendment is required.
- Wren is not adopted into production.
- Wren may be reconsidered later if material capabilities or project requirements change.

## Next Project State

R-001 no longer blocks the next separately authorized implementation slice.

Phase 3 is NOT implemented by this decision-record task.
