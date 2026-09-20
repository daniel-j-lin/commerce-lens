# P00 Internal Protocol Rehearsal Closeout

## Classification and decision

- Protocol: **P00**
- Classification: **Internal expert protocol rehearsal**
- External participant contribution: **0**
- Code under test: `07fbce38556e7eaccbbb4338ba7a8072cdff942c`
- Final P00 status: **PASS**
- P15 status: **NOT PASS**
- P01 status: **NOT RUN**
- Next gate: **P01 external first-user pilot**

P00 exercised the protocol and deterministic product paths before exposing the
package to an external participant. It is internal rehearsal evidence only. It
does not establish external validation, usability, production readiness,
enterprise readiness, or product-market fit, and it does not count toward the
three-participant P15 threshold.

## Purpose and environment

The rehearsal verified the S1–S5 protocol paths, including consolidated
coverage confirmation, unknown-coverage refusal, bounded diagnostic refusal,
explicit retained evidence, and the temporary default. Verification ran on
macOS 15.7.4 with Python 3.11.9 from branch
`codex/f1-b-governed-coverage-intake`. Only synthetic P15 fixtures were used.

## Scenario results

### S1 — Dataset A governed Revenue Change

**PASS**

- Revenue: `12000.00` → `10800.00 USD`
- Revenue Change: `-1200.00 USD`
- MetricState: `Valid`
- ClaimState: `Admissible`
- Coverage authority: `USER_DECLARED`
- Disclosure: source completeness has **not been independently verified** by CommerceLens
- Consolidated coverage confirmation: **PASS**
- Plain `確認`: accepted through canonical `confirmation_intent="confirmed"`
- Availability cutoff: `2026-04-01T00:00:00Z`

The complete proposal displayed resolved facts once and requested one final
confirmation. No special phrase such as `確認完整性`, `確認完整匯出`, `Confirm
coverage`, or `Confirm complete export` was required.

### S2 — Dataset B unknown coverage

**PASS**

Dataset B remained blocked with unknown coverage, no manufactured coverage
authority, and **0 supported material Revenue Change claims**. Requested dates
and observed dataset dates did not supply coverage authority.

### S3 — diagnostic refusal

**PASS**

The descriptive Revenue Change was supported. The diagnostic explanation was
refused with the governed wording:

> Insufficient evidence to conclude why Revenue declined.

No speculative cause was presented.

### S4 — explicit retained evidence

**PASS**

An explicit natural-language retention request routed through the formal
retained workflow. Finalization reached `retained_complete` only after
persistence integrity succeeded. Cross-process `list`, `inspect`, and `verify`
all passed. Retention did not change `ClaimDecision` or upgrade
`USER_DECLARED` authority.

### S5 — temporary default

**PASS**

With no retention request, execution remained temporary and created no retained
run.

## Defects and corrective actions

| Defect observed during P00 | Classification | Corrective action | Rerun result |
|---|---|---|---|
| Initial participant source-context defect | Protocol defect | Added neutral reviewed Dataset A export context without oracle values or response coaching | PASS |
| Retained-mode host routing defect | Host integration defect | Added explicit host retention control and formal retained finalization path | PASS |
| Repetitive coverage confirmation UX | Host rendering defect | Consolidated resolved facts into one declarative proposal and one confirmation prompt | PASS |
| Known-vs-missing fact renderer defect | Host rendering defect | Rendered resolved facts once and limited clarification to genuinely missing facts | PASS |
| Cutoff propagation defect | Integration defect | Propagated explicit UTC cutoff through structured context and canonicalized equivalent UTC forms | PASS |
| Special-phrase / stale installed Skill mismatch | Distribution defect | Made plain affirmative normalization canonical, persisted behavior in repository Skills, and added behavioral parity coverage | PASS in canonical/runtime source; isolated installed verification remains a v0.2.0 release gate |

## Verification evidence

- Focused P00 gate: `159 passed` after commit `07fbce3`; exit code `0`.
- P15 preflight: exit code `0`.
- Dataset A temporary: PASS.
- Dataset A retained: PASS; `retained_complete`; `list` / `inspect` / `verify` PASS.
- Dataset B: blocked; supported claims `0`.
- Diagnostic refusal regression: PASS.

## Remaining non-blocking observations

- P01 must validate the fresh first-user experience with an external participant.
- P15 cannot be marked PASS until its unchanged external-participant thresholds are met.
- Isolated v0.2.0 installation and final release-candidate verification are separate release gates.

## Closeout

P00 is formally closed as a completed internal rehearsal. P01 has not been run,
and P15 remains incomplete.
