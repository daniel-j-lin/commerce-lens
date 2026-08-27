# CommerceLens AI

CommerceLens AI is an evidence-first e-commerce analytics system. The governing rule is: no material claim without traceable evidence.

This repository currently implements Phase 1 foundations plus Phase 2 pre-Metric canonicalization support: deterministic contracts, stable identifiers and fingerprints, local artifacts, SQLite metadata, dataset registration, read-only inspection of CSV, `.xlsx`, and SQLite sources, explicit source-to-canonical mapping, canonical Data Quality checks, canonical artifact creation, and deterministic Data Sufficiency evaluation.

It does not yet implement Metric formulas, Revenue, Orders, AOV, period comparison Metric calculations, contribution analysis, deterministic Metric validation logic, admissible-evidence policy, Claim admissibility behavior, Evaluation Fixtures, `SKILL.md`, LLM integration, a UI, connectors, or an HTTP API.

## Frozen Specifications

Approved governing documents are kept in `docs/frozen/` and are treated as immutable implementation authority.

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Python 3.11 is selected for this slice because the local implementation environment provides Python 3.11.9 and not Python 3.12; the declared dependencies support Python 3.11 cleanly.

## Tests

```bash
python -m pytest
```
