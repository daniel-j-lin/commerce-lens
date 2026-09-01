# CommerceLens AI

CommerceLens AI is an evidence-first e-commerce analytics system. The governing rule is: no material claim without traceable evidence.

This repository is currently governed through P7-001 APPROVED / FROZEN. It implements deterministic contracts, stable identifiers and fingerprints, local artifacts, SQLite metadata, dataset registration, read-only inspection of CSV, `.xlsx`, and SQLite sources, explicit source-to-canonical mapping, canonical Data Quality checks, canonical artifact creation, deterministic Data Sufficiency evaluation, governed Metric execution, deterministic validation, and evidence admissibility.

The current approved kernel supports Revenue, Orders, AOV, and Revenue Change through complete deterministic evidence chains. The post-P7 state includes MetadataStore schema v5 and a full-suite verification record of 398 passed tests. The next roadmap direction begins with ClaimDecision governance: a numerically correct result does not automatically authorize a material claim.

It does not yet implement ClaimDecision, Findings, Alternative Explanations, Recommendations, Evaluation Fixtures runner, `SKILL.md`, LLM integration, a UI, connectors, or an HTTP API.

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
