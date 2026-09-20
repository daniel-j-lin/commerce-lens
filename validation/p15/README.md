# VAL-FIRSTUSER-01 / P15 Execution Package

This directory is the frozen preparation package for external first-user
validation of CommerceLens v0.2.0 while preserving the Public v0.1 analytical contract.

This package does not modify product behavior and does not run a participant
session. It contains synthetic data, private observer material, participant
task sheets, and reproducibility checks.

## Package status

- Protocol version: `p15-execution-package-v1`
- Dataset generator: `p15-data-generator-v1`
- Primary surface: fresh Codex conversation
- Pilot sequence: P01 first; proceed toward P02/P03 only after the P01 gate
- F3 is out of scope and does not block this package
- Single-period KPI is excluded from the P15 pass gate
- P00 protocol correction applied: S1 now includes neutral, reviewed
  Dataset A source-owner context sufficient to assess export completeness;
  the internal S1–S5 rehearsal is complete; P01 has not been run
- P00: **PASS** as an internal expert protocol rehearsal with 0 external participants
- P15: **NOT PASS**
- Current readiness: **READY FOR P01**
- Approved period correction: baseline 2025-01-01–2025-03-31 and comparison
  2026-01-01–2026-03-31; both are 90 calendar days inclusive.

## Package layout

- `protocol.md` — scope, procedure, measures, gates, and freeze rules
- `participant/` — material safe to show to participants
- `observer/` — observer-only oracle, scripts, rubrics, and forms
- `data/` — frozen synthetic datasets and manifest
- `scripts/` — deterministic generation and validation

## Reproduce and validate

From the repository root:

```bash
python3.11 validation/p15/scripts/generate_p15_data.py
python3.11 validation/p15/scripts/validate_p15_data.py \
  --manifest validation/p15/data/DATASET_MANIFEST.json
```

The validator independently recalculates Dataset A Revenue, Orders, AOV, and
Revenue Change. It also records bytes, hashes, schema, date range, status
semantics, and row counts.

The current bytes and manifest are frozen for P15 execution. Do not edit the
CSV bytes after freeze. If a dataset or approved period changes, increment the
protocol version and regenerate the manifest.

## Participant safety boundary

Only files under `participant/` and the selected dataset should be shown to a
participant. Do not show `observer/oracle.md`, the manifest, scripts, or
internal project material.

No participant data, credentials, customer data, or employer-confidential data
may be collected.

## P00 protocol correction

The P00 rehearsal confirmed that CommerceLens correctly kept mapping
confirmation separate from coverage authority and correctly remained blocked
when the participant could not establish source completeness. The failure was
in the S1 protocol materials: the participant had no factual source-owner basis
or cutoff for deciding whether Dataset A was complete.

S1 now provides the dataset owner's reviewed export conditions in plain
language. This context describes the closed periods, all-pages/all-records
scope, paid and cancelled status treatment, absence of additional hidden
date/status filters, and completeness through at least `2026-04-01 00:00 UTC`.
It contains no expected metric values and no instruction about which product
choice to make. Dataset B's unknown-coverage context is unchanged.

The corrected S1–S5 paths passed the internal P00 rehearsal. This result does
not count as external participant evidence. P01 remains the next gate, and P15
remains incomplete until the unchanged external-participant thresholds are met.
