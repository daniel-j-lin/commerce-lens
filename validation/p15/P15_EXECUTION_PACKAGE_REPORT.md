# P15 Execution Package Report

## 1. Decision and scope

The equal-period fixture correction was already approved by the owner. This
work preserves equal-duration validation, Metric semantics, and F3 scope while
fixing the P00 S1 consolidated coverage rendering path.

- Starting HEAD: `0d4c92d3cfe50e723856b95a998bff6150014989`
- Branch: `codex/f1-b-governed-coverage-intake`
- Product behavior changed: yes — complete source context now renders as one
  declarative coverage proposal with one final confirmation prompt
- Human participant session: not run
- P00 protocol correction: participant/observer documentation and the
  host-facing coverage renderer updated; F1-B policy and dataset bytes unchanged
- P00 code-under-test commit: `07fbce38556e7eaccbbb4338ba7a8072cdff942c`
- Repository closeout: local commits only; no push/tag/release/deploy

### P00 protocol correction

The P00 rehearsal was classified as a test-protocol defect. CommerceLens
correctly proposed mapping, kept mapping confirmation separate from coverage
authority, requested explicit coverage confirmation, and remained blocked with
no Revenue Change claim when the participant truthfully lacked a completeness
basis. The defect was that the S1 participant task did not provide the factual
source-owner context or cutoff needed for a Dataset A owner to determine
completeness.

The S1 task now provides the dataset owner's reviewed statement that both
requested periods were closed before export, all pages and records for the
stated scope are included, paid orders are included, cancelled orders are
excluded under the stated scope, no additional hidden date/status filters were
applied, and the data is complete through at least `2026-04-01 00:00 UTC`.
This is a neutral source basis, not an instruction about the product action.
Dataset B's uncertain-source context remains unchanged. P01 has not been run.

## 2. Current frozen periods

- Baseline: 2025-01-01 through 2025-03-31 inclusive: 90 calendar days
- Comparison: 2026-01-01 through 2026-03-31 inclusive: 90 calendar days

Dataset A and Dataset B use these same comparison periods.

## 3. Dataset A

| Field | Value |
|---|---|
| Filename | `P15-A-governed-marketplace.csv` |
| SHA-256 | `1e60e229f302af0adfb5d4f9870dad50eb7a5498335d19a79399942c3bccc371` |
| Byte size | 8904 |
| Rows | 100 |
| Source type | CSV, order-line grain |
| Schema | Non-canonical marketplace-style headers |
| Eligibility | `paid` eligible; `cancelled` excluded |
| Currency | USD only; no FX conversion |
| Observed date range | 2025-01-01 through 2026-03-31 |
| Generator | `p15-data-generator-v1` |

Generator SHA-256: `89503095776f99ec071af074627ed56d64d7b794e248408d98e056570983b692`

The superseded Dataset A hash is:

`327d28767715dcb9aa4575039d72fc3642e889220154810ef991d67d392bd240`

It is historical provenance only and is not authoritative for P15 execution.

### Dataset A oracle

- Baseline Revenue: `12000.00 USD`
- Comparison Revenue: `10800.00 USD`
- Revenue Change: `-1200.00 USD`
- Baseline Orders: `48`
- Comparison Orders: `45`
- Baseline AOV: `250.00 USD`
- Comparison AOV: `240.00 USD`

Independent validation confirmed distinct-order counting, multi-line orders,
cancelled-row exclusion, USD-only semantics, synthetic identifiers, and exact
oracle values.

## 4. Dataset B

| Field | Value |
|---|---|
| Filename | `P15-B-coverage-unknown.csv` |
| SHA-256 | `c5ac7201ab1152e647ae7374efb391c8bebd6d83900950634c0a69c197ee3819` |
| Byte size | 7178 |
| Rows | 80 |
| Source type | CSV, order-line grain |
| Eligibility | `paid` eligible; `cancelled` excluded |
| Currency | USD only; no FX conversion |
| Observed date range | 2025-01-01 through 2026-03-31 |
| Generator | `p15-data-generator-v1` |

The superseded Dataset B hash is:

`4b3183c7256e8a43410d14be611721e8e9e1bb5c5e8f14ef24c5fa4f3c468c15`

It is historical provenance only and is not authoritative for P15 execution.

Dataset B has no accepted coverage declaration. Its governed expected outcome
is blocked or clarification-required, with zero supported material Revenue,
Orders, AOV, or Revenue Change claims.

## 5. Validation evidence

### Generation and hash identity

Passed. Regeneration produced byte-identical Dataset A and Dataset B files and
the new bytes match `DATASET_MANIFEST.json`.

### Independent oracle validation

Passed. The validator independently recalculated the exact Dataset A Revenue,
Orders, AOV, and Revenue Change oracle, verified both 90-day periods, eligibility
semantics, multi-line rows, cancelled controls, USD-only data, and synthetic
identifiers.

### Dataset A CommerceLens preflight

Passed through the actual governed public runner at P00 code-under-test commit
`07fbce38556e7eaccbbb4338ba7a8072cdff942c`:

1. confirmed non-canonical source mapping;
2. prepared and confirmed USER_DECLARED coverage;
3. completed current sufficiency checks;
4. executed deterministic analysis;
5. passed validation and ClaimDecision;
6. returned exit code `0`.

The preflight used separate public requests to verify all required oracle
metrics:

- Revenue: `12000.00 USD` → `10800.00 USD`
- Revenue Change: `-1200.00 USD`
- Orders: `48` → `45`
- AOV: `250.00 USD` → `240.00 USD`
- coverage authority remained `USER_DECLARED`

### Dataset B CommerceLens preflight

Passed. Running without a valid coverage declaration returned blocked status,
zero supported claims, zero coverage provenance records, and exposed missing
global source authority. Request dates and observed min/max dates did not create
coverage authority.

### Retention control

Passed using regenerated Dataset A and the corrected period definitions. The
retained run reached `retained_complete`; list, inspect, and verify all passed.
Retention did not upgrade USER_DECLARED authority.

### Oracle leakage

Passed. Participant-facing files do not expose expected values, expected
success/failure, expected refusal, Confirm/I don't know instructions, or
observer-only USER_DECLARED explanations.

The added S1 source-owner context contains only export conditions and the
completeness cutoff. It does not contain expected Revenue, Orders, AOV, or
Revenue Change values, nor does it identify which coverage response to select.

### Formatting and package review

Passed:

- `git diff --check`
- package whitespace/final-newline review
- required participant files
- required observer files
- manifest completeness

## 6. Readiness

**P00 INTERNAL REHEARSAL COMPLETE — READY FOR P01.**

This status is based on all required preparation gates above. It does not mean
P15 has passed and does not imply general usability or product-market fit.

P00 S1–S5 completed the internal expert rehearsal. The corrected task sheet
feeds complete structured context into the renderer, which shows one
declarative proposal and accepts plain `確認`. External participant contribution
remains zero. P01 has not been run, P15 is **NOT PASS**, and the moderator must
still use the separate moderator/product-session setup without exposing
observer-only material to the participant.
