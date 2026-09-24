# R5-PF Conformance Harness

This directory contains the PF0 harness, the seven approved PF1 representative
ACTIVE bundles, the corrected 25-fixture PF2 current-runtime Class A tranche,
two physical bundles transferred to PF3 controlled Class C scope, the four
PF3-1 governance-boundary controlled fixtures, the nine PF3-2 claim/causal
boundary controlled fixtures, and the seven PF3-3 version/provenance/chain
boundary controlled fixtures.

- Frozen R5 v1.0 is the semantic authority.
- `inventory/active.yaml` and `inventory/deferred.yaml` are derived implementation indexes only. A mismatch with the frozen specification makes the registry invalid.
- Semantic ACTIVE, physical implementation coverage, and executable conformance coverage are separate states.
- DEFERRED obligations are non-executable and are never discovered from `active/`.
- PF1 contains exactly seven bundles under `active/<FAMILY>/<FX-R5-ID>/`: six executable against code-owned production subjects and one dependency-blocked precedence case.
- PF2 adds exactly 25 executable bundles backed by existing deterministic production subjects.
- Owner amendment: `FX-R5-CLAIM-004A` Class A → Class C.
- Owner amendment: `FX-R5-PREC-002A` Class A → Class C.
- The transferred bundles remain physical; `FX-R5-PREC-002A` is executable in
  PF3-4 and `FX-R5-CLAIM-004A` is executable in PF3-2.
- PF3-1 implements exactly four `CONTROLLED_CASE` governance-boundary bundles.
- PF3-2 implements exactly nine `CONTROLLED_CASE` claim/causal-boundary bundles;
  PF3-3 implements exactly seven `CONTROLLED_CASE` version/provenance/chain
  boundary bundles; PF3-4 implements exactly three `CONTROLLED_CASE`
  precision/precedence boundary bundles; PF3-5 implements exactly fourteen
  `CONTROLLED_CASE` exact-form language-corpus bundles. PF3-1 through PF3-5
  are implemented and owner-approved; the PF3 controlled tranche contains 37
  executable `CONTROLLED_CASE` fixtures.
- Combined Class C contains 38 executable fixtures when including the
  pre-existing `FX-R5-LANG-014A` case. PF4-0 and PF4-1 are approved and closed.
  PF4-2 through PF4-5 implement the remaining 33 authorized ordinary-PF4
  fixtures and are ready for owner review. Ordinary PF4 now contains exactly
  40 executable fixtures; `FX-R5-R4-034A` remains NOT_IMPLEMENTED for PF6.
- Implementation-readiness counts are A31 / B59 / C38 / D1. The PF3 controlled Class C tranche is 37.
- The combined state is 109 physical bundles: 108 executable, no physical-ready
  bundles, one dependency-blocked, and 20 not implemented.
- Fixture input plus expected output cannot self-certify: no independent actual-output producer means `DEPENDENCY_BLOCKED`, never PASS.
- Counts are reporting facts, not scores, percentages, reliability measures, or production-readiness claims.
