# VAL-FIRSTUSER-01 / P15 Execution Package

This directory is the frozen preparation package for external first-user
validation of CommerceLens Public v0.1.3.

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
