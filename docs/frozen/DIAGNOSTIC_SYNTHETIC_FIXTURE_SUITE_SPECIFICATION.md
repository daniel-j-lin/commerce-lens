# CommerceLens AI Diagnostic Synthetic Fixture Suite Specification

**Document:** `DIAGNOSTIC_SYNTHETIC_FIXTURE_SUITE_SPECIFICATION.md`

**Milestone:** R5 — Diagnostic Synthetic Fixture Suite

**Version:** R5 v1.0

**Status:** Approved

**State:** Frozen

**Scope:** Specification and fixture-design authority only

---

## 1. Purpose

This specification defines the authoritative design for a future local synthetic conformance fixture suite that tests whether CommerceLens implementations preserve the frozen R1–R4 governance semantics.

R5 is a reliability and conformance milestone. It is not a product feature, implementation milestone, physical fixture package, or Decision Reliability Benchmark.

The governing rule is:

> ONE FIXTURE VARIANT = ONE AUTHORITATIVE EXPECTED MATERIAL OUTCOME.

R5 converts frozen governance into deterministic, traceable, human-reviewable fixture obligations. It must make incorrect stage selection, incorrect first-blocker selection, authority bypass, invalid promotion, R4 arithmetic errors, provenance failures, and diagnostic or causal overstatement observable.

---

## 2. Scope

R5 defines:

- the approved dual-axis fixture architecture;
- lifecycle-layer metadata and stable fixture families;
- fixture identity and version rules;
- active fixture variants and deferred fixture obligations;
- semantic input ingredients;
- the complete expected-material-path contract;
- first controlling blocker recording;
- exact frozen-authority mapping;
- evidence, measurement, admission, R4, diagnostic, Claim, causal, language, version, provenance, independent-chain, and precedence cases;
- synthetic and numerical data-design requirements;
- human-reviewability requirements;
- future deterministic evaluator requirements; and
- the handoff to a separately authorized physical-fixture phase.

---

## 3. Non-Scope

R5 does not:

- create YAML, JSON, CSV, XLSX, SQLite, or other physical fixture files;
- create physical manifests, fixture directories, tests, runners, validators, schemas, enums, classes, migrations, SQL, or Python;
- implement R1–R4 runtime behavior;
- define a diagnostic method, support threshold, contradiction threshold, causal method, or future Claim policy;
- implement or authorize public R4, diagnostic, or causal behavior;
- define fixture weights, aggregate scores, pass-rate targets, rankings, or production-readiness thresholds;
- modify any existing fixture expected outcome;
- modify Public v0.1 or v0.2.0 behavior; or
- begin R6.

---

## 4. Frozen Authorities

R5 is subordinate to the following Approved / Frozen authorities:

| Short reference | Governing document and version |
|---|---|
| Constitution | `PROJECT_MASTER_INSTRUCTIONS.md` v1.1 |
| Skill Scope | `SKILL_SCOPE_SPECIFICATION.md` v1.0 |
| Evidence Contract | `EVIDENCE_CONTRACT_SPECIFICATION.md` v1.0 |
| Architecture | `ARCHITECTURE_SPECIFICATION.md` v1.0 |
| Canonical / Metrics | `CANONICAL_DATASET_AND_METRIC_DICTIONARY.md` v1.0 |
| Evaluation Fixtures | `EVALUATION_FIXTURES_SPECIFICATION.md` v1.0 |
| R1 | `DIAGNOSTIC_REASONING_SPECIFICATION.md` R1 v1.0 |
| R2 | `HYPOTHESIS_FINDING_STATE_MODEL_SPECIFICATION.md` R2 v1.0 |
| R3 | `REQUIRED_EVIDENCE_MATRIX_SPECIFICATION.md` R3 v1.0 |
| R4 | `DETERMINISTIC_REVENUE_DECOMPOSITION_SPECIFICATION.md` R4 v1.0 |

Where an R5 fixture conflicts with frozen authority, frozen authority wins and the R5 specification must be corrected through governance review. R5 does not create local exceptions.

R5 cites actual document sections or section titles. It does not invent governance rule IDs.

---

## 5. Existing Fixture Infrastructure

The repository currently provides the following reusable conventions:

1. Architecture §17 selects human-readable metadata plus tiny tabular inputs as the primary future physical fixture representation, with one physical manifest per variant.
2. Evaluation Fixtures §§4–11 define fixtures as governed evaluation contracts, require minimality and stable IDs, and distinguish fixture outcome, Metric State, Claim State, validation, and workflow status.
3. The P9 fixture runner currently uses strict safe-YAML manifests, an explicit eight-case inventory, physical-input and harness-level cases, exact material-field comparison, and no benchmark scoring. These are implementation precedents, not R5 semantic authority.
4. P14 synthetic files characterize realistic source shapes and adapter robustness. They do not establish R1–R4 diagnostic outcomes.
5. Existing tests separately exercise canonicalization, Data Sufficiency, deterministic validation, Evidence Admissibility, ClaimDecision, persistence, fixture execution, Public v0.1 integration, and retained artifacts.
6. The Metric Registry contains the frozen Metric definitions. Current implemented public execution remains limited to Revenue, Orders, AOV, and Revenue Change.
7. Current Data Sufficiency preserves `not_evaluated`, `sufficient`, `clarification_required`, `insufficient_evidence`, `data_quality_failure`, and `partial`, with per-Metric eligibility retained independently.
8. Current Evidence Admissibility binds exact request, dataset, canonical dataset, population, period, Metric version, validation, intended use, and fingerprints.
9. Current Claim policy `commerce_lens_p8_claim_admissibility` / `p8_001_v1` permits the governed descriptive path only. Diagnostic candidates remain denied with `unsupported_claim_type`.
10. Existing integrity uses SHA-256 file fingerprints, canonical-JSON semantic fingerprints, content-derived stable IDs, immutable artifact references, and retained-run verification. `retained_complete` requires verified integrity and a completion marker bound to the manifest fingerprint.

The older outcome labels `PASS` and `PASS WITH QUALIFICATION` remain historical vocabulary of the frozen Evaluation Fixtures specification. They are not sufficient as the sole authoritative outcome for an R5 variant. R5 requires the exact material path and disposition.

---

## 6. Governing Fixture Principles

1. **One variant, one outcome.** No variant permits evaluator choice between materially different results.
2. **Frozen authority first.** Expected behavior is derived from governance, not copied from current implementation output.
3. **Exact path.** Availability, sufficiency, fitness, admission, execution, validation, analytical outcome, alternative check, Claim permission, and rendering remain distinct.
4. **Correct blocker.** A refusal for the wrong stage or reason is non-conforming.
5. **No unreachable results.** A blocked earlier stage does not fabricate later-stage records.
6. **Minimality.** One primary semantic distinction per isolated fixture.
7. **Precedence isolation.** Only explicit `PREC` fixtures deliberately combine defects.
8. **Positive controls.** Positive cases exist only where concrete frozen authority exists.
9. **Authority gate.** A required case lacking concrete upstream authority is deferred, not approximated.
10. **Local determinism.** Future execution is local, deterministic, reproducible, and independent of unrestricted LLM judgment.
11. **Independent chains.** Failure remains local to the affected chain.
12. **No scoring.** Fixture conformance is not benchmark scoring.

Prohibited expected-outcome forms include `PASS`, `PASS WITH QUALIFICATION`, “whichever applies,” “supported if material,” “valid if independently supported,” “Missing Evidence or External Evidence Required,” “Validation Failure or Claim Prohibited,” “evaluator decides,” and “depends on interpretation.”

---

## 7. Dual-Axis Architecture

The approved architecture has two axes.

### 7.1 Axis 1 — Lifecycle / governance layer

| Layer | Meaning |
|---|---|
| A — Evidence Eligibility | Required Evidence, measurement, sufficiency, fitness, and intended-use admission |
| B — Mechanical Method | R4 eligibility, execution, validation, trace, reconciliation, and determinism |
| C — Diagnostic / Claim | Diagnostic disposition, alternative check, ClaimDecision, and causal refusal |
| D — Language / Promotion | Controlled rendering, qualification, narrowing, and promotion boundaries |
| Cross-Cutting | Version, provenance, independent chains, and path-specific precedence |

Layer is organizational and coverage metadata only. It is not a runtime state, enum requirement, lifecycle authority, or Claim authority.

### 7.2 Axis 2 — Stable fixture family

Each fixture variant has exactly one primary family. Supporting rules may cross layers, but they do not change primary identity.

---

## 8. Fixture Families

| Family | Layer | Primary purpose |
|---|---|---|
| `EVID` | A | Required Evidence, sufficiency, evidence fitness, and admissibility failures or success |
| `MEAS` | A | Five-class measurement classification and role sensitivity |
| `ADMIT` | A | Descriptive-to-diagnostic intended-use admission boundary |
| `R4` | B | R4 mechanical method, trace, validation, and conformance |
| `DIAG` | C | R1/R2 diagnostic semantic disposition |
| `ALT` | C | Alternative Explanation Check |
| `CLAIM` | C | ClaimCandidate and ClaimDecision authority |
| `CAUSE` | C | Causal admission boundary |
| `NARROW` | D | Qualification versus material narrowing |
| `LANG` | D | Controlled wording and promotion boundary |
| `VERSION` | Cross-Cutting | Exact authority and historical-version binding |
| `PROV` | Cross-Cutting | Provenance, artifact, fingerprint, and retention integrity |
| `CHAIN` | Cross-Cutting | Independence and partial material completion |
| `PREC` | Cross-Cutting | First-blocker precedence under an exact frozen path |

---

## 9. Fixture Identity and Versioning

### 9.1 Active fixture identity

Active fixture IDs use:

`FX-R5-<FAMILY>-<NNN><VARIANT>`

Examples include `FX-R5-EVID-007A`, `FX-R5-R4-014A`, and `FX-R5-PREC-003A`.

Identity binds:

- family, ID, and variant;
- exact material facts;
- exact governed question or proposition where applicable;
- execution context and intended use;
- scope, population, periods, currency, and canonical input identity;
- Metric, profile, method, validation, and policy versions where applicable; and
- one authoritative expected material path.

### 9.2 Stability rules

- Title, translation, and non-material prose cleanup do not change the ID.
- A material input change that changes the path or outcome requires a new variant.
- An authoritative expected-outcome change requires a new variant.
- A materially different version binding requires a new variant when it changes outcome.
- An ID is never reused for a different contract.

### 9.3 Deferred obligation identity

Deferred obligations use review identifiers of the form `DF-R5-<FAMILY>-<NNN>`. A deferred obligation ID is not an active fixture ID and must not be counted or executed as an active fixture.

---

## 10. Variant Semantics

Each variant fixes:

```text
fixed input facts
+ fixed authorities and versions
+ fixed execution context
+ fixed intended use
+ fixed requested claim or wording where applicable
→ one authoritative material path
```

Material fact changes may reuse a conceptual base dataset but require a separate variant whenever the authoritative path differs. One manifest must not branch to alternative expected results.

Only `PREC` variants may contain more than one deliberate defect. Their sole primary purpose is path-specific blocker precedence.

---

## 11. Active vs Deferred Status

### 11.1 Active

`ACTIVE` means concrete frozen authority exists to specify exactly one expected material outcome and the case is eligible for later physical instantiation.

### 11.2 Future-required / deferred

`FUTURE-REQUIRED / DEFERRED` means frozen governance requires the semantic case, but a concrete upstream authority needed to instantiate it does not yet exist.

Every deferred obligation must identify:

- the missing authority;
- why synthetic facts cannot substitute;
- the milestone or separately approved authority that could unlock activation; and
- the cases that must be added after activation.

Deferred obligations are not active fixtures, not executable cases, and not evidence of coverage completion.

---

## 12. Expected-Outcome Contract

R5 uses a small universal core plus conditional stage blocks.

### 12.1 Universal core

Every active variant must define:

- stable fixture identity and semantic version;
- active status;
- primary family and lifecycle layer;
- exact authoritative final material disposition;
- stages reached;
- first controlling blocker or explicit `NONE`;
- controlling reason;
- controlling frozen authority and version;
- permitted material meaning;
- prohibited material meaning; and
- why no other material disposition is authoritative.

### 12.2 Conditional stage blocks

Only reached or controlling stages are specified:

- Data Sufficiency;
- Required Evidence requirement judgments;
- Evidence Admissibility;
- R4 method eligibility;
- execution;
- validation;
- Evidence Conflict Assessment;
- Analytical Outcome;
- Alternative Explanation Check;
- ClaimCandidate / ClaimDecision;
- Derived Material Disposition;
- rendering/wording; and
- artifact/fingerprint integrity.

An unreachable stage must be marked “not reached due to” the controlling path. It must not contain a fabricated result.

The disposition labels used in this document specify fixture meaning. They do not require runtime enums with identical names.

---

## 13. First Controlling Blocker

The first controlling blocker is:

> The earliest authoritative blocker under the exact governed path exercised by the fixture.

It is mandatory expected metadata for every negative and precedence fixture. Positive fixtures record `NONE`.

R5 does not create a universal precedence policy. It preserves distinct paths:

```text
Standalone R4 path
!= Diagnostic Evaluation path
!= Claim rendering path
```

Diagnostic fixtures use the applicable order frozen in R1 §19.2, R2 §20, and R3 §29. Standalone R4 fixtures use R4 §§8, 23, 24, 29, and 30. Rendering fixtures evaluate only after the authority required by R1 §§20–22, R2 §28, or R4 §§31–32 exists for the exact content.

No `PREC` fixture may be generalized into precedence for another path.

### 13.1 First-blocker registry for active non-R4 families

The inventory tables define the material facts and disposition. The following registry makes the mandatory first blocker explicit for active variants outside the R4 and EVID tables, which already record it directly.

| Active variant(s) | First controlling blocker |
|---|---|
| `FX-R5-MEAS-001A`, `002A`, `006A` | `NONE` — the stated measurement-class judgment is valid, while other dimensions remain outside the positive assertion |
| `FX-R5-MEAS-004A`, `005A`, `006B` | Measurement validity for the exact proposition and intended use |
| `FX-R5-ADMIT-001A`, `003A` | Diagnostic intended-use admission |
| `FX-R5-R4-029A` | `NONE` |
| `FX-R5-R4-030A` | Execution-context classification: a standalone mechanical request must not enter a fabricated diagnostic path |
| `FX-R5-R4-032A` | Exact applicable R3 profile resolution for the diagnostic workflow |
| `FX-R5-R4-033A` through `036A` | `NONE` |
| `FX-R5-R4-037A` | Method/evaluator determinism conformance |
| `FX-R5-DIAG-001A`, `002A` | `NONE` — valid lower-authority result-level outcome; neither result is a Finding by itself |
| `FX-R5-DIAG-003A` | Governed diagnostic test and support definition absent; hypothesis cannot promote |
| `FX-R5-DIAG-005A` | Material internal evidence availability/fitness |
| `FX-R5-DIAG-006A` | Unmet external dependency |
| `FX-R5-DIAG-011A` | Requested claim-class restriction under current policy, followed by authoritative refusal |
| `FX-R5-DIAG-012A` | Causal claim-class restriction, followed by authoritative refusal |
| `FX-R5-ALT-006A` | Evidence authority for the asserted competitor is absent; alternative generation is unauthorized |
| `FX-R5-CLAIM-001A`, `002A` | Requested claim-class restriction, followed by the exact authoritative ClaimDecision refusal |
| `FX-R5-CLAIM-003A` | ClaimDecision claim-strength/scope binding |
| `FX-R5-CLAIM-004A` | Required authoritative ClaimDecision is absent |
| `FX-R5-CLAIM-005A` | Exact ClaimDecision claim class and permitted wording strength |
| `FX-R5-CLAIM-006A` | ClaimDecision-to-proposition binding |
| `FX-R5-CAUSE-001A` through `006A` | Causal claim-class restriction and absence of a separately governed causal admission standard |
| `FX-R5-NARROW-001A` | Material population coverage for the broad proposition; disclaimer is later and cannot repair it |
| Permitted `LANG` variants `001A`, `003A`, `005A`, `009A`–`011A`, `014A`–`016A` | `NONE` |
| Prohibited `LANG` variants `002A`, `004A`, `006A`–`008A`, `017A` | Rendering exceeds the exact authorized semantic or claim class |
| `FX-R5-VERSION-001A`, `006A` | `NONE` |
| `FX-R5-VERSION-003A`–`005A`, `007A`–`010A` | The exact version or historical binding named by the variant |
| `FX-R5-PROV-001A` | `NONE` |
| `FX-R5-PROV-002A`–`009A` | The exact provenance, artifact, fingerprint, or retention-integrity prerequisite named by the variant |
| `FX-R5-CHAIN-001A` | R4 trace completeness fails for the R4 chain; the independent Revenue chain records `NONE` |
| `FX-R5-CHAIN-002A` | Exact diagnostic profile is missing for the Product Mix chain; the independent Revenue Change descriptive chain records `NONE` |

This registry is part of each referenced variant's expected semantics. It does not create precedence outside that variant's exact path.

---

## 14. Authority Mapping

Every material expected outcome maps to:

- frozen document;
- section number and title;
- applicable version;
- governing rule;
- fixture scope and intended use; and
- whether the reference is controlling or supporting.

Family-level mappings may reduce duplication, but each variant retains its exact controlling authority. A generic reference such as “R1–R4” is insufficient when a specific section exists.

### 14.1 Normative variant-to-authority map

The following grouped mappings apply to every listed variant individually. A future manifest must copy or unambiguously resolve the applicable row and retain its own controlling section.

| Variant(s) | Controlling frozen authority |
|---|---|
| `EVID-001A` | R3 §13.1 — Semantic validity |
| `EVID-002A`, `004A` | R3 §§14, 22, and 25 — dependency class, missingness, and Data Sufficiency |
| `EVID-003A` | R3 §26 — Evidence Admissibility Boundary |
| `EVID-005A` | R3 §14 — Source Dependency Classification; R2 §24 — External Evidence Required |
| `EVID-006A`, `007A` | R3 §§18–19 — Temporal and Population Alignment |
| `EVID-008A`–`011A` | R3 §21 — Metric, Unit, Currency, and Denominator Compatibility |
| `EVID-012A`, `013A` | R3 §§17 and 22 — Completeness, Coverage, and Missingness |
| `EVID-014A` | R3 §15 — Granularity Governance |
| `EVID-015A`, `016A` | R3 §16 — Identity and Join Governance |
| `EVID-017A` | R3 §23 — Provenance |
| `EVID-018A` | R3 §24 — Validation Requirements |
| `EVID-019A`; all `MEAS` variants | R3 §20 — Measurement Classification |
| `EVID-020A` | R3 §§6.2–6.3 and §§9–10 — family template versus exact binding |
| `EVID-021A` | R3 §8 — Profile Identity and Versioning |
| `EVID-022A`; `NARROW-001A` | R3 §27 — Blocking, Qualification, and Narrowing |
| `EVID-023A` | Evidence Contract §§13–23 and current descriptive Evidence Admissibility authority preserved by R3 §§25–26 |
| `ADMIT-001A`, `003A` | R3 §26; R4 §§23.3 and 28 |
| `R4-001A`–`006A` | R4 §§13–21 — universe, partition, components, identity, precision, and reconciliation |
| `R4-007A`–`009A` | R4 §§13 and 22.1 — presence and complete empty-period semantics |
| `R4-010A`–`013A` | R4 §12 and §22.4 — Product Identity |
| `R4-014A` | R4 §9 — Period Preconditions |
| `R4-015A`, `016A` | R4 §11 — Currency Preconditions |
| `R4-017A` | R4 §10 — Population and Scope Preconditions |
| `R4-018A`–`025A` | R4 §§21, 25–26, 29, and 30.3 — independent result validation and trace authority |
| `R4-026A` | R4 §§6, 24, 30.1, and 36 — method identity and version eligibility |
| `R4-027A` | R4 §§6, 27, 29, and 36 — exact R4 method/version result binding and validation |
| `R4-028A` | R4 §30.2 — Method Execution Failure |
| `R4-029A`, `030A`, `032A` | R4 §§8 and 23 — standalone versus diagnostic execution context |
| `R4-033A`–`037A` | R4 §§30.4 and 35 — method/evaluator conformance and determinism |
| `DIAG-001A`–`003A`, `005A`, `006A`, `011A`, `012A` | R1 §§6–24 and the specific R2 disposition/precedence rules in §§19–27 |
| `ALT-006A` | R1 §15.2 and R2 §17 — check does not require invented alternatives |
| `CLAIM-001A`–`006A` | R1 §20; R2 §§18 and 27 |
| `CAUSE-001A`–`006A` | R1 §16; R2 §26 |
| All active `LANG` variants | R1 §§21–22, R2 §28, or R4 §§31–32 as identified by the wording class |
| `VERSION-001A`, `003A`–`010A` | Architecture §19; R2 §§10–11 and 20; R3 §8; R4 §36 |
| `PROV-001A`–`009A` | Evidence Contract §§12, 45–46; Architecture §§12 and 16; R3 §23; R4 §§25–26; approved F2-A retention authority |
| `CHAIN-001A`, `002A` | Architecture §11.4; R2 §14.3; R3 §27.4; R4 §30 |
| `PREC-001A`–`005A` | The exact per-variant authorities listed in §34 of this specification |

The short form omits only the common `FX-R5-` prefix. Deferred obligations retain the authority and missing-authority statements in their own sections and do not become active through this map.

---

## 15. Semantic Input Ingredients

A future fixture may conceptually bind only the ingredients needed by its path:

- canonical synthetic rows or a governed raw source shape;
- mapping and coverage authority;
- scope, population, period, eligibility, and currency definitions;
- canonical, Metric, and validation references;
- an exact R2 proposition and R3 profile/version when applicable;
- evidence requirement judgments and admission records;
- R4 method/version and precision authority;
- execution and validation results;
- complete R4 trace authority;
- Evidence Conflict Assessment;
- Analytical Outcome backed by an approved method/criterion;
- Alternative Explanation Check;
- ClaimCandidate and ClaimDecision;
- retained artifact and fingerprint state; and
- exact controlled candidate utterance.

This list is semantic. It does not prescribe serialization or a runtime contract.

---

## 16. Evidence Eligibility Fixtures

The following active inventory isolates one primary evidence distinction per variant. Authority references are R3 §§12–30, §38, §39, and §42 unless a narrower reference is shown.

| ID | Primary fact | Authoritative disposition | First blocker |
|---|---|---|---|
| `FX-R5-EVID-001A` | Field exists but semantics are invalid | `SEMANTICALLY_INVALID_EVIDENCE__TEST_NOT_ELIGIBLE` | Evidence fitness — semantic validity |
| `FX-R5-EVID-002A` | Required internal evidence is absent | `MISSING_INTERNAL_EVIDENCE__TEST_NOT_ELIGIBLE` | Available Evidence mapping / Data Sufficiency |
| `FX-R5-EVID-003A` | Evidence exists but is inadmissible for exact use | `PRESENT_BUT_INADMISSIBLE__TEST_NOT_ELIGIBLE` | Evidence Admissibility |
| `FX-R5-EVID-004A` | Material internal dependency is missing | `MISSING_INTERNAL_DEPENDENCY` | Dependency availability |
| `FX-R5-EVID-005A` | Material external dependency is unmet | `EXTERNAL_EVIDENCE_REQUIRED` | External dependency resolution |
| `FX-R5-EVID-006A` | Evidence covers the wrong period | `TEMPORALLY_MISALIGNED__TEST_NOT_ELIGIBLE` | Temporal alignment |
| `FX-R5-EVID-007A` | Evidence covers the wrong population | `POPULATION_MISMATCH__TEST_NOT_ELIGIBLE` | Population alignment |
| `FX-R5-EVID-008A` | Correct-looking value binds wrong Metric version | `METRIC_VERSION_INCOMPATIBLE__TEST_NOT_ELIGIBLE` | Metric compatibility |
| `FX-R5-EVID-009A` | Material unit is incompatible | `UNIT_INCOMPATIBLE__TEST_NOT_ELIGIBLE` | Unit compatibility |
| `FX-R5-EVID-010A` | Monetary evidence contains mixed currency | `MIXED_CURRENCY__TEST_NOT_ELIGIBLE` | Currency compatibility |
| `FX-R5-EVID-011A` | Currency is unknown | `UNKNOWN_CURRENCY__TEST_NOT_ELIGIBLE` | Currency compatibility |
| `FX-R5-EVID-012A` | Material coverage is incomplete | `INCOMPLETE_COVERAGE__TEST_NOT_ELIGIBLE` | Completeness / coverage |
| `FX-R5-EVID-013A` | Material coverage is unknown | `UNKNOWN_COVERAGE__TEST_NOT_ELIGIBLE` | Completeness / coverage |
| `FX-R5-EVID-014A` | Evidence is at the wrong grain | `GRAIN_INCOMPATIBLE__TEST_NOT_ELIGIBLE` | Granularity governance |
| `FX-R5-EVID-015A` | Required join has unresolved cardinality | `JOIN_CARDINALITY_UNRESOLVED__TEST_NOT_ELIGIBLE` | Identity / join governance |
| `FX-R5-EVID-016A` | Required join loses material records | `MATERIAL_JOIN_LOSS__TEST_NOT_ELIGIBLE` | Identity / join governance |
| `FX-R5-EVID-017A` | Provenance is missing | `PROVENANCE_INCOMPLETE__TEST_NOT_ELIGIBLE` | Provenance |
| `FX-R5-EVID-018A` | Required deterministic validation failed | `REQUIRED_VALIDATION_FAILED__TEST_NOT_ELIGIBLE` | Validation status |
| `FX-R5-EVID-019A` | Unsupported proxy offered as evidence | `UNSUPPORTED_PROXY__TEST_NOT_ELIGIBLE` | Measurement validity |
| `FX-R5-EVID-020A` | Family template exists without exact binding | `EXACT_PROPOSITION_BINDING_MISSING` | Exact Proposition Binding |
| `FX-R5-EVID-021A` | Bound profile version mismatches evaluation | `PROFILE_VERSION_MISMATCH` | Profile identity/version resolution |
| `FX-R5-EVID-022A` | Disclaimer attempts to waive blocking defect | `QUALIFICATION_CANNOT_REPAIR_BLOCKER` | Original evidence blocker |
| `FX-R5-EVID-023A` | Fully aligned current descriptive evidence | `DESCRIPTIVE_EVIDENCE_ELIGIBLE_FOR_OWN_GOVERNED_USE` | `NONE` |

The following positive requirements are deferred because no concrete frozen exact diagnostic profile/admission instance exists:

| Deferred ID | Required case | Missing authority |
|---|---|---|
| `DF-R5-EVID-001` | Explicit non-applicability inside a complete exact diagnostic profile | Concrete approved exact profile and binding |
| `DF-R5-EVID-002` | Valid diagnostic material narrowing through new proposition/binding/profile/evaluation | Concrete original and narrowed exact profiles plus evaluation authority |
| `DF-R5-EVID-003` | Fully aligned evidence admitted for exact diagnostic use | Concrete diagnostic admission authority and exact profile |

Isolated fixtures remain separate from §34 precedence fixtures.

---

## 17. Measurement Fixtures

Authority: R3 §20, §38, §39, and §42.

| ID/status | Case | Authoritative disposition |
|---|---|---|
| `FX-R5-MEAS-001A` — ACTIVE | Direct measurement of an existing governed concept | `MEASUREMENT_CLASS_DIRECT__DIMENSION_SATISFIED_ONLY`; other evidence dimensions remain independently required |
| `FX-R5-MEAS-002A` — ACTIVE | Governed transformed measurement with existing transformation lineage | `MEASUREMENT_CLASS_GOVERNED_TRANSFORMED__BOUNDED_USE_ELIGIBLE` |
| `DF-R5-MEAS-001` — DEFERRED | Positive Governed Proxy | Requires an approved bounded proxy definition, exact role/use, and maximum Claim boundary |
| `FX-R5-MEAS-004A` — ACTIVE | Inferred Construct without future method/admission | `INFERRED_CONSTRUCT__NOT_ELIGIBLE` |
| `FX-R5-MEAS-005A` — ACTIVE | Unsupported Proxy | `UNSUPPORTED_PROXY__NOT_ELIGIBLE` |
| `FX-R5-MEAS-006A` — ACTIVE | AOV used as direct AOV measurement | `DIRECT_FOR_AOV_ONLY` |
| `FX-R5-MEAS-006B` — ACTIVE | The same AOV decline offered as direct discounting evidence | `UNSUPPORTED_PROXY_FOR_DISCOUNTING__NOT_ELIGIBLE` |

The role-sensitive pair proves that classification follows the exact proposition and intended use rather than the field or value alone.

---

## 18. Admission Fixtures

Authority: R3 §26 and §39; R4 §§8.3, 23.3, and 28.

| ID/status | Case | Authoritative disposition | First blocker |
|---|---|---|---|
| `FX-R5-ADMIT-001A` — ACTIVE | Validated descriptive result; diagnostic admission absent | `AUTHENTICATED_CANDIDATE_ONLY__NOT_DIAGNOSTIC_INPUT_ADMISSIBLE` | Diagnostic intended-use admission |
| `DF-R5-ADMIT-001` — DEFERRED | Same evidence satisfies concrete exact proposition-, role-, profile-, scope-, period-, and use-specific admission | Requires a concrete frozen exact profile and diagnostic admission authority |
| `FX-R5-ADMIT-003A` — ACTIVE | Descriptive result copied directly into diagnostic output | `AUTHORITY_BYPASS__DIAGNOSTIC_OUTPUT_BLOCKED` | Diagnostic intended-use admission |

The deferred positive case, once unlocked, may authorize only progression to the next governed diagnostic stage. It may not imply support or Claim permission.

---

## 19. R4 Mechanical Fixtures

R4 v1.0 provides concrete method, arithmetic, eligibility, validation, trace, language, and conformance authority. The following cases are active specification variants.

| ID | Case | Layer | Authoritative disposition / blocker |
|---|---|---|---|
| `FX-R5-R4-001A` | Exact reconciliation happy path | Valid | `VALIDATED_R4_MECHANICAL_RESULT`; blocker `NONE` |
| `FX-R5-R4-002A` | Entry-only | Valid | Exact Entry component and zero Exit/Continuing; blocker `NONE` |
| `FX-R5-R4-003A` | Exit-only | Valid | Exact Exit component and zero Entry/Continuing; blocker `NONE` |
| `FX-R5-R4-004A` | Continuing-only | Valid | Exact Continuing component and zero Entry/Exit; blocker `NONE` |
| `FX-R5-R4-005A` | Entry + Exit + Continuing | Valid | All components exact and reconciled; blocker `NONE` |
| `FX-R5-R4-006A` | Zero net change with offsetting components | Valid | Components retained; net zero does not erase them; blocker `NONE` |
| `FX-R5-R4-007A` | Baseline complete and empty; Comparison nonempty | Valid | Every Comparison product is Entry; blocker `NONE` |
| `FX-R5-R4-007B` | Baseline nonempty; Comparison complete and empty | Valid | Every Baseline product is Exit; blocker `NONE` |
| `FX-R5-R4-008A` | Both periods complete and empty | Valid | Empty union and zero anchors/components; blocker `NONE` |
| `FX-R5-R4-009A` | Zero-Revenue product has an eligible line | Valid | Product remains present and is classified by presence; blocker `NONE` |
| `FX-R5-R4-010A` | Missing `product_id` | Eligibility | `R4_NOT_EXECUTED__PRODUCT_IDENTITY_MISSING` |
| `FX-R5-R4-011A` | Stable ID with changed name | Valid | One product by ID; name does not split identity; blocker `NONE` |
| `FX-R5-R4-012A` | Same name with different IDs | Valid | Distinct products by ID; blocker `NONE` |
| `FX-R5-R4-013A` | Confirmed ID collision/reuse | Eligibility | `R4_NOT_EXECUTED__PRODUCT_IDENTITY_CORRUPT` |
| `FX-R5-R4-014A` | Incomplete period | Eligibility | `R4_NOT_EXECUTED__PERIOD_COVERAGE_INCOMPLETE` |
| `FX-R5-R4-015A` | Mixed currency | Eligibility | `R4_NOT_EXECUTED__MIXED_CURRENCY` |
| `FX-R5-R4-016A` | Unknown currency | Eligibility | `R4_NOT_EXECUTED__UNKNOWN_CURRENCY` |
| `FX-R5-R4-017A` | Population mismatch | Eligibility | `R4_NOT_EXECUTED__POPULATION_MISMATCH` |
| `FX-R5-R4-018A` | Product Revenue sum mismatch | Validation | `EXECUTED_R4_RESULT_REJECTED__PRODUCT_REVENUE_SUM_MISMATCH` |
| `FX-R5-R4-019A` | Incomplete E/X/K partition | Validation | `EXECUTED_R4_RESULT_REJECTED__PARTITION_INCOMPLETE` |
| `FX-R5-R4-020A` | Overlapping E/X/K partition | Validation | `EXECUTED_R4_RESULT_REJECTED__PARTITION_OVERLAP` |
| `FX-R5-R4-021A` | Component-sum mismatch | Validation | `EXECUTED_R4_RESULT_REJECTED__COMPONENT_SUM_MISMATCH` |
| `FX-R5-R4-022A` | Nonzero authoritative reconciliation difference | Validation | `EXECUTED_R4_RESULT_REJECTED__NONZERO_RECONCILIATION_DIFFERENCE` |
| `FX-R5-R4-023A` | Display rounding appears non-additive; authoritative arithmetic reconciles | Valid | `VALIDATED_R4_MECHANICAL_RESULT__PRESENTATION_ROUNDING_DISCLOSED`; blocker `NONE` |
| `FX-R5-R4-024A` | Completed execution; trace incomplete | Validation | `EXECUTED_R4_RESULT_REJECTED__TRACE_INCOMPLETE` |
| `FX-R5-R4-025A` | Completed execution; trace tampered | Validation | `EXECUTED_R4_RESULT_REJECTED__TRACE_INTEGRITY_FAILURE` |
| `FX-R5-R4-026A` | Method version stale or unresolved before execution | Eligibility | `R4_NOT_EXECUTED__METHOD_VERSION_UNRESOLVED` |
| `FX-R5-R4-027A` | Produced R4 result bound to the wrong R4 method/version after execution | Validation | `EXECUTED_R4_RESULT_REJECTED__METHOD_AUTHORITY_BINDING_MISMATCH` |
| `FX-R5-R4-028A` | Eligible execution loses required runtime dependency before usable result | Execution | `R4_EXECUTION_FAILED__NO_USABLE_RESULT` |

Controlling authority: R4 §§8–26, §§29–30, §35, and §38. Pre-execution R4 method resolution and post-execution R4 method-authority binding mismatch are separate variants because their failure layers differ. `FX-R5-R4-027A` contains no Diagnostic Proposition or R3 profile defect.

### 19.1 Authoritative numerical anchors for valid R4 variants

Unless a variant states otherwise, the conceptual values below use one governed currency (`USD`), complete equal-duration non-overlapping periods, the same governed population and eligibility semantics, exact Decimal arithmetic, and one eligible line for every listed product-period presence. Omitted product-period values are genuine absence proven by complete coverage, not missing data.

| Variant | Baseline Product Revenue | Comparison Product Revenue | Exact authoritative result |
|---|---|---|---|
| `FX-R5-R4-001A` | A 100.00; B 40.00 | A 120.00; B 20.00 | Continuing `0.00`; Entry `0.00`; Exit `0.00`; Revenue Change `0.00`; Reconciliation Difference `0.00` |
| `FX-R5-R4-002A` | A 100.00 | A 100.00 | plus Comparison-only B 25.00; Entry `25.00`; Exit `0.00`; Continuing `0.00`; Change `25.00` |
| `FX-R5-R4-003A` | A 100.00; B 25.00 | A 100.00 | Entry `0.00`; Exit `-25.00`; Continuing `0.00`; Change `-25.00` |
| `FX-R5-R4-004A` | A 100.00 | A 130.00 | Entry `0.00`; Exit `0.00`; Continuing `30.00`; Change `30.00` |
| `FX-R5-R4-005A` | A 100.00; B 40.00; C 60.00 | A 120.00; B 20.00; D 100.00 | Entry `100.00`; Exit `-60.00`; Continuing `0.00`; Change `40.00` |
| `FX-R5-R4-006A` | A 100.00; B 50.00 | A 80.00; C 70.00 | Entry `70.00`; Exit `-50.00`; Continuing `-20.00`; Change `0.00` |
| `FX-R5-R4-007A` | Empty | A 40.00; B 60.00 | Entry `100.00`; Exit `0.00`; Continuing `0.00`; Change `100.00` |
| `FX-R5-R4-007B` | A 40.00; B 60.00 | Empty | Entry `0.00`; Exit `-100.00`; Continuing `0.00`; Change `-100.00` |
| `FX-R5-R4-008A` | Empty | Empty | Empty product universe; all components, Change, and Reconciliation Difference `0.00` |
| `FX-R5-R4-009A` | A 0.00, with an eligible line | A 10.00, with an eligible line | A is Continuing, contribution `10.00`; it is not Entry |
| `FX-R5-R4-011A` | A/name “Tea” 40.00 | A/name “Tea New Label” 60.00 | One Continuing product A; contribution `20.00` |
| `FX-R5-R4-012A` | A/name “Tea” 40.00 | B/name “Tea” 60.00 | A is Exit `-40.00`; B is Entry `60.00`; Change `20.00` |
| `FX-R5-R4-023A` | A 10.00 | A 10.40; plus Comparison-only B 0.40 | Continuing `0.40`; Entry `0.40`; exact Change `0.80`; exact Reconciliation Difference `0.00`; whole-unit display may show `0 + 0` while separately rounded total shows `1` |

For every row, Component Sum equals the listed Revenue Change and Reconciliation Difference is exactly zero. `FX-R5-R4-001A` is the smallest no-change positive control; `FX-R5-R4-005A` is the simultaneous-component control, so their primary purposes remain distinct.

---

## 20. R4 Standalone / Diagnostic Context Fixtures

| ID/status | Context | Authoritative disposition |
|---|---|---|
| `FX-R5-R4-029A` — ACTIVE | Standalone request with all mechanical prerequisites | `R4_MAY_EXECUTE_WITHOUT_DIAGNOSTIC_PROPOSITION`; blocker `NONE` |
| `FX-R5-R4-030A` — ACTIVE | Implementation fabricates proposition/profile solely to run standalone R4 | `NON_CONFORMING_ORCHESTRATION__ARTIFICIAL_DIAGNOSTIC_AUTHORITY` |
| `DF-R5-R4-001` — DEFERRED | R4 inside exact diagnostic workflow with satisfied concrete exact R3 profile | No concrete approved exact diagnostic profile with complete method binding currently exists |
| `FX-R5-R4-032A` — ACTIVE | Diagnostic workflow attempts R4 without exact applicable R3 profile | `R4_DIAGNOSTIC_WORKFLOW_NOT_ELIGIBLE__PROFILE_MISSING` |

Authority: R4 §§7–8 and §23. The deferred positive case, once unlocked, authorizes R4 execution only; it does not establish diagnostic admission, support, or Claim permission.

---

## 21. R4 Determinism Fixtures

Authority: R4 §§30.4, 35, 38, and 42.

| ID | Controlled comparison | Authoritative disposition |
|---|---|---|
| `FX-R5-R4-033A` | Same evaluator, identical authoritative inputs and versions, repeated runs | `MATERIAL_OUTPUT_IDENTICAL__CONFORMING`; blocker `NONE` |
| `FX-R5-R4-034A` | Two conforming evaluators, identical governed inputs | `MATERIAL_PARTITION_VALUES_RECONCILIATION_AND_DISPOSITION_IDENTICAL`; blocker `NONE` |
| `FX-R5-R4-035A` | Canonical row order shuffled | `AUTHORITATIVE_RESULT_UNCHANGED`; blocker `NONE` |
| `FX-R5-R4-036A` | Presentation product order differs only | `NON_MATERIAL_ORDER_DIFFERENCE__CONFORMING`; blocker `NONE` |
| `FX-R5-R4-037A` | Component assignment or value changes nondeterministically | `METHOD_OR_EVALUATOR_CONFORMANCE_FAILURE` |

Material comparison excludes timestamps, generated event IDs, internal query plans, storage layout, and presentation-only ordering.

```text
Per-result validation != Determinism conformance testing
```

---

## 22. R4 Language Fixtures

Authority: R4 §§31–32 and R1 §§8, 21–22.

| ID | Exact controlled form | Authoritative classification |
|---|---|---|
| `FX-R5-LANG-001A` | “Comparison-only products account for USD 100.00 of the mechanical Revenue difference under Product-Level Revenue Decomposition R4 v1.0.” | `PERMITTED_MECHANICAL` |
| `FX-R5-LANG-002A` | “New products caused Revenue growth of USD 100.00.” | `PROHIBITED_CAUSAL` |
| `FX-R5-LANG-003A` | “The Continuing-Product Revenue Change Component is USD −20.00 under Product-Level Revenue Decomposition R4 v1.0.” | `PERMITTED_MECHANICAL` |
| `FX-R5-LANG-004A` | “Existing products drove the USD 20.00 decline.” | `PROHIBITED_DIAGNOSTIC_OR_CAUSAL` |
| `FX-R5-LANG-005A` | “Under Product-Level Revenue Decomposition R4 v1.0, the Entry Component mechanically contributed USD 100.00.” | `PERMITTED_METHOD_RELATIVE_MECHANICAL` |
| `FX-R5-LANG-006A` | “Entry products were the main reason Revenue increased by USD 100.00.” | `PROHIBITED_PRIMACY_AND_EXPLANATION` |
| `FX-R5-LANG-007A` | “New products likely caused Revenue growth of USD 100.00.” | `PROHIBITED_CAUSAL__SOFTENER_NO_REPAIR` |
| `FX-R5-LANG-008A` | “Continuing products appear to explain the USD 20.00 decline.” | `PROHIBITED_DIAGNOSTIC__SOFTENER_NO_REPAIR` |

These are controlled conformance cases only. Passing them is not evidence of a general natural-language classifier, complete keyword policy, semantic parser, or Claim authorization engine. Simplistic keyword matching is not normative.

---

## 23. Diagnostic Semantic Fixtures

| ID/status | Case | Authoritative disposition |
|---|---|---|
| `FX-R5-DIAG-001A` — ACTIVE | Validated descriptive result only | `VALIDATED_DESCRIPTIVE_RESULT_ONLY__NO_DIAGNOSTIC_MEANING`; authentic validated descriptive authority only, not an Observed Finding or Claim permission |
| `FX-R5-DIAG-002A` — ACTIVE | Validated R4 result only | `VALIDATED_R4_MECHANICAL_RESULT_ONLY__NO_DIAGNOSTIC_MEANING`; exact mechanical decomposition authority only, not a Mechanical Finding, Diagnostic Finding, or Claim permission |
| `FX-R5-DIAG-003A` — ACTIVE | Plausible proposed explanation with no promotion basis | `DIAGNOSTIC_HYPOTHESIS_ONLY` |
| `DF-R5-DIAG-001` — DEFERRED | Fully specified Testable Hypothesis | Requires concrete approved diagnostic method plus support and contradiction criteria |
| `FX-R5-DIAG-005A` — ACTIVE | Material internal evidence missing | `MISSING_EVIDENCE` |
| `FX-R5-DIAG-006A` — ACTIVE | Material dependency is external and unadmitted | `EXTERNAL_EVIDENCE_REQUIRED` |
| `DF-R5-DIAG-006` — DEFERRED | Two or more concrete diagnostic-use-admitted evidence inputs contain unresolved material conflict | Future disposition `CONFLICTING_EVIDENCE`; requires exact proposition, exact R3 profile/binding, diagnostic intended-use admission authority, at least two admitted inputs, and conflict-assessment authority |
| `DF-R5-DIAG-002` — DEFERRED | Governed test validated; support criterion not met | Requires concrete approved diagnostic method/criterion |
| `DF-R5-DIAG-003` — DEFERRED | Governed test validated; contradiction criterion met | Requires concrete approved diagnostic method/criterion |
| `DF-R5-DIAG-004` — DEFERRED | Otherwise eligible diagnostic Claim denied for a non-class reason | Requires an approved available diagnostic Claim class and policy |
| `FX-R5-DIAG-011A` — ACTIVE | Requested claim class unavailable under current policy | `CLAIM_PROHIBITED` |
| `FX-R5-DIAG-012A` — ACTIVE | Direct causal request under current governance | `CLAIM_PROHIBITED__CAUSAL_AUTHORITY_UNAVAILABLE` |
| `DF-R5-DIAG-005` — DEFERRED | Supported Diagnostic Finding | Requires all authorities listed in §36 |
| `DF-R5-DIAG-007` — DEFERRED | Positive Mechanical Finding rendered from a validated R4 result | Requires a separately governed positive ClaimDecision/rendering path for R4 mechanical Finding wording |

Authority: R1 §§6–24 and R2 §§15–29. Semantic distinctions do not require separate runtime enums.

`FX-R5-DIAG-001A` and `FX-R5-DIAG-002A` are result-level fixtures. They preserve:

```text
Validated Result != Finding
Validated R4 Result != Mechanical Finding
Validated R4 Result != Diagnostic Finding
```

If material Observed Finding wording is requested, exact descriptive ClaimDecision and rendering authority must separately authorize it. Current-authority Observed Finding coverage is retained only through `FX-R5-LANG-009A`, whose input explicitly includes that authority. Positive Mechanical Finding coverage remains deferred under `DF-R5-DIAG-007`.

---

## 24. Unsupported vs Contradicted

The required future cases remain separate:

- `DF-R5-DIAG-002`: successful execution and validation; support criterion not met; contradiction criterion not met → `TESTED_UNSUPPORTED`.
- `DF-R5-DIAG-003`: successful execution and validation; affirmative contradiction criterion met → `TESTED_CONTRADICTED`.

R1 §11 and R2 §§16 and 25 establish the distinction. R1–R4 do not approve a concrete diagnostic support or contradiction method. R5 therefore does not create thresholds, mock authority, or active end-to-end variants.

---

## 25. Conflict vs Contradiction

`DF-R5-DIAG-006` will test unresolved disagreement among two or more concrete diagnostic-use-admitted evidence inputs before a valid support determination. It remains deferred until exact diagnostic proposition, R3 profile/binding, intended-use admission, multiple admitted inputs, and conflict-assessment authority exist. Synthetic fixture facts must not self-declare admissibility.

`DF-R5-DIAG-003` will test a validated governed test that affirmatively contradicts the exact proposition. Its only authoritative disposition will be `TESTED_CONTRADICTED` once concrete method authority exists.

Authority: R2 §15 and §25. Both cases are deferred for different missing authorities and remain semantically distinct:

```text
Evidence Conflict != Test Contradiction
Evidence Conflict != Missing Evidence
Test Contradiction != Ordinary Tested Unsupported
```

Neither case may collapse into missing evidence, ordinary non-support, execution failure, or validation failure merely because both are deferred.

---

## 26. Alternative Explanation Fixtures

Authority: R1 §15 and §19; R2 §17 and §20.2.

| ID/status | Case | Authoritative disposition |
|---|---|---|
| `DF-R5-ALT-001` — DEFERRED | Criterion met; check incomplete | Requires concrete criterion-met authority; expected future disposition is non-promotional with `alternative_explanation_check_incomplete` |
| `DF-R5-ALT-002` — DEFERRED | Check complete; no material competitor identified | Requires concrete diagnostic evaluation authority; does not authorize uniqueness or causality |
| `DF-R5-ALT-003` — DEFERRED | Check complete; material competitor present | Requires concrete diagnostic evaluation authority; competitor remains at actual evidence status |
| `DF-R5-ALT-004` — DEFERRED | Competitor present; bounded non-unique Claim may remain eligible | Requires future diagnostic Claim policy |
| `DF-R5-ALT-005` — DEFERRED | Competitor present; unique/primary wording denied | Requires future diagnostic Claim candidate/policy context |
| `FX-R5-ALT-006A` — ACTIVE | System invents a competitor without evidence | `NON_CONFORMING_ALTERNATIVE_GENERATION` |

Mandatory check does not mean mandatory generation. “No competitor identified” never means “unique cause proven.”

---

## 27. ClaimDecision Fixtures

Authority: R1 §20, R2 §18 and §27, and current P8 policy authority.

| ID/status | Case | Authoritative disposition |
|---|---|---|
| `FX-R5-CLAIM-001A` — ACTIVE | Diagnostic candidate under current policy | `CLAIM_PROHIBITED__UNSUPPORTED_CLAIM_TYPE` |
| `FX-R5-CLAIM-002A` — ACTIVE | Causal candidate under current governance | `CLAIM_PROHIBITED__CAUSAL_AUTHORITY_UNAVAILABLE` |
| `FX-R5-CLAIM-003A` — ACTIVE | Lower-authority decision reused for stronger wording | `CLAIMDECISION_SCOPE_OR_STRENGTH_MISMATCH__RENDER_BLOCKED` |
| `FX-R5-CLAIM-004A` — ACTIVE | Finding rendered without ClaimDecision | `AUTHORITY_BYPASS__FINDING_BLOCKED` |
| `FX-R5-CLAIM-005A` — ACTIVE | Descriptive authorization stretched to diagnostic/causal wording | `RENDER_EXCEEDS_CLAIMDECISION__BLOCKED` |
| `FX-R5-CLAIM-006A` — ACTIVE | Decision for stale/different proposition rebound | `CLAIMDECISION_BINDING_MISMATCH__BLOCKED` |
| `DF-R5-CLAIM-001` — DEFERRED | All promotion conditions pass and future diagnostic policy authorizes | Requires approved diagnostic Claim representation and policy |

ClaimDecision remains the sole material Claim-permission authority. Derived disposition may classify but never authorize or repair.

---

## 28. Causal Boundary Fixtures

Authority: R1 §16 and §§21–24; R2 §26.

| ID | Candidate basis | Authoritative disposition |
|---|---|---|
| `FX-R5-CAUSE-001A` | Historical transactional correlation rendered as cause | `CLAIM_PROHIBITED__CAUSAL_STANDARD_ABSENT` |
| `FX-R5-CAUSE-002A` | R4 decomposition rendered as cause | `CLAIM_PROHIBITED__MECHANICAL_IS_NOT_CAUSAL` |
| `FX-R5-CAUSE-003A` | Diagnostic association rendered as cause | `CLAIM_PROHIBITED__ASSOCIATION_IS_NOT_CAUSATION` |
| `FX-R5-CAUSE-004A` | Statistical significance rendered as cause | `CLAIM_PROHIBITED__SIGNIFICANCE_IS_NOT_CAUSAL_AUTHORITY` |
| `FX-R5-CAUSE-005A` | Some alternatives removed, causal claim asserted | `CLAIM_PROHIBITED__CAUSAL_STANDARD_ABSENT` |
| `FX-R5-CAUSE-006A` | Direct causal request without causal-identification standard | `CLAIM_PROHIBITED__CAUSAL_AUTHORITY_UNAVAILABLE` |

R5 defines no causal inference method.

---

## 29. Qualification / Narrowing Fixtures

| ID/status | Case | Authoritative disposition |
|---|---|---|
| `FX-R5-NARROW-001A` — ACTIVE | Broad proposition lacks material population coverage; warning/disclaimer appended | `BROAD_PROPOSITION_BLOCKED__DISCLAIMER_NO_REPAIR` |
| `DF-R5-NARROW-001` — DEFERRED | Evidence supports a narrower diagnostic population/scope/period | Requires concrete original and narrowed proposition/binding/profile/evaluation authority |

The future valid narrowing path is:

```text
new exact proposition
→ new exact binding and resolved profile
→ new Diagnostic Evaluation
→ bounded result only if all remaining authorities pass
```

The original broad evaluation remains immutable historical authority. Qualification cannot waive a blocking failure.

---

## 30. Claim-Language Fixtures

Authority: R1 §§21–22, R2 §28, and R4 §§31–32.

| ID/status | Wording class | Expected classification |
|---|---|---|
| `FX-R5-LANG-009A` — ACTIVE | Validated descriptive result plus exact current descriptive ClaimDecision and bounded rendering authority | `PERMITTED_OBSERVED_FINDING_WORDING` |
| `FX-R5-LANG-010A` — ACTIVE | Exact method-relative mechanical wording | `PERMITTED_MECHANICAL_WORDING` |
| `FX-R5-LANG-011A` — ACTIVE | Explicitly labeled diagnostic hypothesis | `PERMITTED_HYPOTHESIS_WORDING__NO_FINDING` |
| `DF-R5-LANG-001` — DEFERRED | Tested unsupported wording | Requires concrete governed test/criterion authority |
| `DF-R5-LANG-002` — DEFERRED | Supported diagnostic association wording | Requires concrete supported diagnostic authority and ClaimDecision |
| `FX-R5-LANG-014A` — ACTIVE | Exact insufficient-evidence wording | `PERMITTED_INSUFFICIENCY_WORDING` |
| `FX-R5-LANG-015A` — ACTIVE | Exact external-evidence-required wording | `PERMITTED_EXTERNAL_EVIDENCE_WORDING` |
| `FX-R5-LANG-016A` — ACTIVE | Exact causal refusal wording | `PERMITTED_CAUSAL_REFUSAL` |
| `FX-R5-LANG-017A` — ACTIVE | Softer equivalent retains unsupported meaning | `PROHIBITED_MEANING__SOFTENER_NO_REPAIR` |

Language fixtures evaluate only listed controlled utterances or semantic forms. They do not define general natural-language authorization.

---

## 31. Versioning Fixtures

Authority: Architecture §19, R2 §§10–11 and §20, R3 §8, and R4 §36.

| ID/status | Case | Authoritative disposition |
|---|---|---|
| `FX-R5-VERSION-001A` — ACTIVE | All exact versions correctly bound | `BOUND_AUTHORITY_CURRENT_AND_RESOLVABLE`; blocker `NONE` |
| `DF-R5-VERSION-001` — DEFERRED | Stale concrete R3 profile | Requires concrete approved exact profile versions |
| `DF-R5-VERSION-002` — DEFERRED | Post-execution diagnostic result bound to the wrong exact R3 profile/version | Requires concrete approved exact profile versions, diagnostic workflow authority, and result-to-profile binding authority |
| `FX-R5-VERSION-003A` — ACTIVE | Stale/unresolved R4 method before execution | `METHOD_VERSION_MISMATCH__NOT_ELIGIBLE` |
| `FX-R5-VERSION-004A` — ACTIVE | Mismatched Metric version | `METRIC_VERSION_MISMATCH__AFFECTED_CHAIN_BLOCKED` |
| `FX-R5-VERSION-005A` — ACTIVE | Changed Claim policy applied to old decision | `POLICY_BINDING_MISMATCH__DECISION_NOT_REUSABLE` |
| `FX-R5-VERSION-006A` — ACTIVE | Historical result remains bound to original versions | `HISTORICAL_AUTHORITY_PRESERVED`; blocker `NONE` |
| `FX-R5-VERSION-007A` — ACTIVE | Later authority silently rewrites historical evaluation | `NON_CONFORMING_HISTORICAL_REWRITE` |
| `FX-R5-VERSION-008A` — ACTIVE | Dynamic `latest` replaces exact binding | `DYNAMIC_AUTHORITY_LOOKUP__BLOCKED` |
| `FX-R5-VERSION-009A` — ACTIVE | Old ClaimDecision rebound to new proposition | `CLAIMDECISION_BINDING_MISMATCH__BLOCKED` |
| `FX-R5-VERSION-010A` — ACTIVE | Cached derived disposition conflicts with recomputation | `CACHE_INVALID__AUTHORITATIVE_DERIVATION_WINS` |

---

## 32. Provenance / Integrity Fixtures

Authority: Evidence Contract §§12, 45–46; Architecture §§12 and 16; R3 §23; R4 §§25–26; and approved F2-A retention authority.

| ID | Case | Authoritative disposition |
|---|---|---|
| `FX-R5-PROV-001A` | Correct artifact and semantic fingerprints | `INTEGRITY_VERIFIED`; blocker `NONE` |
| `FX-R5-PROV-002A` | Retained artifact tampered | `ARTIFACT_INTEGRITY_FAILURE__AFFECTED_AUTHORITY_BLOCKED` |
| `FX-R5-PROV-003A` | Required artifact missing | `REQUIRED_ARTIFACT_MISSING__AFFECTED_AUTHORITY_BLOCKED` |
| `FX-R5-PROV-004A` | Metadata fingerprint mismatches content | `FINGERPRINT_MISMATCH__AFFECTED_AUTHORITY_BLOCKED` |
| `FX-R5-PROV-005A` | Equivalent copied values lack lineage | `VALUE_EQUIVALENCE_WITHOUT_AUTHORITY__INADMISSIBLE` |
| `FX-R5-PROV-006A` | Conversational memory offered as evidence | `NON_AUTHORITATIVE_MEMORY__INADMISSIBLE` |
| `FX-R5-PROV-007A` | Public prose substitutes for retained artifact | `PUBLIC_PROSE_NOT_RETAINED_AUTHORITY` |
| `FX-R5-PROV-008A` | Incomplete retained run claims `retained_complete` | `RETENTION_COMPLETION_FALSE__INTEGRITY_FAILURE` |
| `FX-R5-PROV-009A` | Completion marker mismatches manifest fingerprint | `RETENTION_MARKER_MISMATCH__INTEGRITY_FAILURE` |

---

## 33. Independent Chain Fixtures

Authority: Architecture §§11.4 and 14.7; R1 §4.2 and §24; R2 §14.3; R3 §27.4; R4 §30.

| ID | Case | Authoritative disposition |
|---|---|---|
| `FX-R5-CHAIN-001A` | R4 completed execution fails trace-completeness validation; independent Revenue descriptive chain is valid | `PARTIAL_MATERIAL_RESULT__REVENUE_VALID__R4_WITHHELD` |
| `FX-R5-CHAIN-002A` | Product Mix diagnostic chain lacks an exact applicable R3 profile; Revenue Change descriptive Claim has its own valid decision | `PARTIAL_MATERIAL_RESULT__DESCRIPTIVE_CLAIM_RENDERABLE__DIAGNOSTIC_WITHHELD` |

Neither variant may collapse to global success or global failure. Authority must not cross between chains.

---

## 34. Precedence Fixtures

Each fixture below cites the exact path whose precedence it tests. None establishes universal precedence.

| ID/status | Combined facts | First controlling blocker | Authority |
|---|---|---|---|
| `FX-R5-PREC-001A` — ACTIVE | Diagnostic R4 workflow lacks exact R3 profile; later hypothetical method defect exists | Missing exact profile; later method stage not reached | R3 §29; R4 §§8.2, 23.2, 30.1 |
| `FX-R5-PREC-002A` — ACTIVE | Evidence inadmissible; a later hypothetical support assertion is supplied | Evidence Admissibility; analytical support is unreachable | R1 §19.2; R2 §20; R3 §29 |
| `FX-R5-PREC-003A` — ACTIVE | Executed result fails validation; later permissive ClaimDecision-like input is supplied | Validation failure; Claim permission stage is unreachable | R1 §19.2; R2 §§14, 20 |
| `FX-R5-PREC-004A` — ACTIVE | Causal class requested with strong diagnostic evidence | Claim-class restriction plus authoritative governed refusal | R1 §19.2; R2 §§18.2, 20.1, 26 |
| `FX-R5-PREC-005A` — ACTIVE | External dependency unmet plus later internal defect | External dependency under the exact R1/R2 diagnostic path | R1 §19.2; R2 §§20, 24 |
| `DF-R5-PREC-001` — DEFERRED | Concrete profile-version mismatch plus otherwise complete diagnostic evidence | Requires concrete approved profile versions; future blocker is profile resolution under R3 §29 |

Later supplied facts are retained only for audit and cannot repair or displace the earlier blocker.

---

## 35. Happy Paths

The active positive inventory is:

- `FX-R5-EVID-023A` — current descriptive evidence eligible for its own governed use;
- `FX-R5-MEAS-001A` and `002A` — direct and governed transformed measurement classification only;
- `FX-R5-R4-001A` through `009A`, `011A`, `012A`, and `023A` — valid R4 method cases;
- `FX-R5-R4-029A` — standalone R4 without fabricated diagnostic authority;
- `FX-R5-R4-033A` through `036A` — deterministic conformance controls;
- permitted controlled language cases in §§22 and 30;
- `FX-R5-VERSION-001A` and `006A` — exact and historical version binding;
- `FX-R5-PROV-001A` — verified integrity; and
- `FX-R5-CHAIN-001A` and `002A` — independent valid chains survive local failure.

Positive diagnostic admission, Tested Unsupported, Tested Contradicted, Supported Diagnostic Finding, positive diagnostic ClaimDecision, and positive competitor-constrained Finding remain authority-gated and deferred.

`FX-R5-DIAG-001A` and `FX-R5-DIAG-002A` are valid result-level controls, not Finding happy paths. Observed Finding wording is active only in `FX-R5-LANG-009A` with exact descriptive ClaimDecision/rendering authority. Positive Mechanical Finding coverage is deferred as `DF-R5-DIAG-007`.

---

## 36. Diagnostic Authority Gaps

Current frozen authority is insufficient to instantiate an active positive `SUPPORTED_DIAGNOSTIC_FINDING` fixture.

The missing authorities are:

1. a concrete approved diagnostic method for an exact proposition family;
2. governed support and contradiction criteria;
3. a concrete exact R3 profile and binding for that proposition and method;
4. concrete diagnostic intended-use admission authority;
5. a ClaimCandidate representation capable of the exact diagnostic relationship; and
6. a frozen diagnostic Claim policy capable of positive authorization.

R1 §19.1 requires all promotion conditions and states that current policy is not authorized to approve diagnostic Claims. R2 §18.4 preserves descriptive-only positive permission. R3 does not define a support threshold. R4 §§27–28 and §34 state that an R4 result is not an Analytical Outcome, does not set `CRITERION_MET`, and is not Claim permission.

Accordingly:

- `DF-R5-DIAG-005`, `DF-R5-DIAG-006`, `DF-R5-DIAG-007`, `DF-R5-CLAIM-001`, and `DF-R5-LANG-002` remain deferred;
- no placeholder support criterion is permitted;
- no synthetic `ClaimDecision` may self-authorize the missing policy; and
- later activation requires separate frozen authority and R5 governance review.

The same authority gate applies to positive diagnostic-input admission. Conceptual distinction from support is insufficient; `DF-R5-ADMIT-001` remains deferred until concrete exact admission authority exists.

Diagnostic conflict specifically remains deferred because R5 has no authority to self-declare two inputs diagnostic-use admissible. Positive Mechanical Finding coverage remains deferred because a validated R4 result alone has no Claim or rendering permission.

---

## 37. R4-as-Diagnostic-Evidence Boundary

The required boundary is:

```text
Validated R4 result
→ authenticated mechanical candidate evidence

exact proposition/profile/role/intended-use admission
→ admitted diagnostic input, only when concrete authority exists

admitted diagnostic input without governed diagnostic method/criterion
→ no CRITERION_MET and no Supported Diagnostic Finding
```

Active `FX-R5-ADMIT-001A` proves the first-to-second boundary fails closed without admission. Deferred `DF-R5-ADMIT-001` will prove positive admission once authority exists. `FX-R5-DIAG-002A` proves a valid R4 result remains result-level mechanical authority and is not a Finding. `FX-R5-CLAIM-001A` proves current policy still denies diagnostic promotion.

---

## 38. Synthetic Data Requirements

Future datasets must be:

- entirely synthetic and non-sensitive;
- tiny, deterministic, self-contained, and human-auditable;
- free of real company, customer, seller, URL, credential, or confidential data;
- minimally different between variants;
- explicit about zero, null, unknown, absence, exclusion, and non-applicability;
- sufficient to establish the intended period, population, scope, identity, currency, and coverage facts;
- resistant to accidental alternative interpretation; and
- immutable once bound to an active fixture version.

A conceptual base dataset may be reused. Each material variant retains its own ID, manifest, exact bindings, and expected outcome.

---

## 39. Numerical Fixture Requirements

R4 fixtures must prefer integers or exact finite Decimals that are easy to verify manually. Authoritative calculations must not use binary floating-point tolerance, arbitrary epsilon, or rounded display values.

Every numerical fixture must make the following manually reviewable where applicable:

- Baseline and Comparison Revenue;
- product universe and E/X/K membership;
- each Product Absolute Contribution;
- Entry, Exit, and Continuing components;
- Component Sum; and
- Reconciliation Difference.

`FX-R5-R4-023A` must use authoritative unrounded values that reconcile exactly while separately rounded display values appear visually non-additive. The display artifact cannot control validation.

---

## 40. Manifest Semantics

Every active variant must eventually have its own human-readable manifest exposing:

- fixture ID, version, title, and purpose;
- active status;
- primary family and layer metadata;
- primary and supporting authorities;
- input artifact references;
- exact question or proposition where applicable;
- execution context and intended use;
- scope, population, periods, currency, and version bindings;
- complete expected material path;
- first blocker or `NONE`;
- exact final disposition;
- permitted and prohibited material meaning;
- expected trace/integrity state; and
- rationale for the unique outcome.

Family metadata may reduce duplication but must not hide, alter, or substitute for variant outcome, blocker, scope, intended use, version, or controlling authority.

This specification does not choose YAML, JSON, or another physical schema.

---

## 41. Authority-to-Fixture Coverage Matrix

The future physical inventory must maintain a reviewable matrix with this conceptual relation:

```text
Frozen authority requirement
→ fixture family
→ active variant(s)
→ deferred obligation(s)
→ specification coverage status
```

Minimum coverage rows include:

| Authority area | Active coverage | Deferred gap |
|---|---|---|
| R1 diagnostic taxonomy and wording | Result-level DIAG controls, CAUSE, and current-authority Observed Finding wording in LANG | Positive Mechanical Finding and supported diagnostic path |
| R1/R2 promotion and Claim boundary | CLAIM, PREC | Positive diagnostic ClaimDecision |
| R2 conflict, analytical outcome, alternative check | PREC and non-conflict DIAG controls | Diagnostic Evidence Conflict, Tested outcomes, and most ALT cases |
| R3 evidence dimensions and admission | EVID, MEAS, ADMIT | Concrete positive diagnostic profile/admission |
| R4 arithmetic and validation | R4 | None for standalone mechanical semantics |
| R4 diagnostic context | R4, ADMIT | Positive exact-profile diagnostic workflow |
| Version and history | VERSION | Concrete stale and post-execution R3 profile-version cases |
| Provenance and retention | PROV | None at specification level |
| Independent chains | CHAIN | None at specification level |

Coverage status reports specification coverage only. It has no weight, percentage, score, or benchmark meaning.

---

## 42. Human Reviewability

A reviewer must be able to determine without implementation source code:

- the exact frozen rule being tested;
- the one primary material distinction;
- every material fact and authority binding;
- which stage is reached;
- the first controlling blocker and reason;
- why alternative dispositions are not authoritative;
- the exact permitted and prohibited meaning;
- how numerical results reconcile;
- how provenance and integrity are authenticated; and
- whether missing future authority makes the case deferred.

Opaque hashes alone are insufficient. Human-readable identity, version, scope, and rule references remain mandatory.

---

## 43. Future Automation Boundary

A separately authorized implementation may provide:

- strict manifest validation;
- stable-ID and version-binding checks;
- deterministic fixture discovery;
- local deterministic execution;
- exact Decimal and structured-field comparison;
- artifact and fingerprint verification;
- controlled repeat-run and cross-evaluator comparison;
- controlled candidate-utterance comparison; and
- exact mismatch reporting.

It must not introduce an LLM test oracle, probabilistic scorer, multi-agent fixture generation, custom DSL, vector database, generic plugin framework, or automatic authority generation.

---

## 44. Evaluator Conformance

A future conforming fixture evaluator must:

1. resolve the exact fixture and variant identity;
2. reject deferred obligations as non-executable;
3. authenticate all exact version and artifact bindings;
4. follow only the governed path applicable to the fixture;
5. identify the authoritative first blocker;
6. avoid executing or fabricating unreachable downstream stages;
7. compare the universal core and only applicable conditional blocks;
8. distinguish material differences from timestamps, generated IDs, internal query plans, storage layout, and presentation-only ordering;
9. preserve exact R4 arithmetic, partition, trace, and reconciliation semantics;
10. preserve evidence, diagnostic, Claim, and causal boundaries;
11. evaluate language fixtures only as controlled cases;
12. avoid unrestricted LLM judgment; and
13. produce deterministic fixture-level pass/fail plus exact mismatches against the authoritative material path.

Fixture-level pass/fail is conformance comparison, not an aggregate benchmark score.

---

## 45. Benchmark Boundary

```text
Fixture Suite != Decision Reliability Benchmark
```

R5 defines no fixture weight, aggregate score, weighted reliability measure, leaderboard, model ranking, pass-rate target, production-readiness threshold, or comparative model framework.

---

## 46. Public Product Boundary

R5 authorizes no public R4 execution, positive diagnostic Claim, causal Claim, new Metric, new grouping, CLI behavior, dashboard, Skill behavior, API, benchmark claim, production-readiness claim, or external-validation claim.

Public v0.1 and v0.2.0 remain unchanged. Positive material public Claims remain descriptive under current policy.

---

## 47. Risks and Controls

| Risk | Required control |
|---|---|
| Ambiguous expected outcome | Complete per-variant material path and exact disposition |
| Combined defects hide blocker | Isolated cases separated from `PREC` cases |
| Fixture-count explosion | One primary distinction; reuse conceptual base facts without sharing authority outcome |
| Insufficient semantic coverage | Authority-to-fixture coverage matrix |
| Implementation behavior copied as authority | Derive every expectation from frozen sections |
| Invented diagnostic criterion | Authority gate and deferred obligation |
| Language fixtures mistaken for NLP | Controlled-input boundary stated in every language family |
| Unstable IDs | Hierarchical immutable IDs and new variant on material change |
| Stale authority bindings | Exact versions; prohibit dynamic `latest` |
| Accidental synthetic facts change meaning | Tiny data and one reviewed mutation per isolated variant |
| R4 result treated as diagnostic support | Explicit candidate/admission/support/permission fixtures |
| R5 becomes universal precedence authority | Path-specific citations and prohibition on generalization |
| Deferred case treated as active | Separate `DF-` identity and evaluator rejection |
| Benchmark scoring leakage | No weights, aggregation, targets, or rankings |
| Physical work begins early | Separate authorization required after R5 approval |

---

## 48. Open Questions

The following implementation-allocation questions remain deliberately open:

1. How much non-authoritative family metadata may be inherited without obscuring variant authority?
2. Which governance role approves and versions the controlled candidate-utterance corpus?
3. How will deferred obligations appear beside active variants in a future physical inventory without becoming executable?
4. What physical manifest format will be selected?
5. How will base-dataset reuse be represented physically while preserving independent variant identity?
6. Which review process distinguishes a non-material prose correction from a material fixture-version change?

These questions do not reopen the dual-axis architecture, one-outcome rule, active/deferred distinction, or frozen analytical semantics.

---

## 49. Success Criteria

R5 is specification-complete only when:

- every active variant has exactly one authoritative material outcome;
- every expected material field maps to frozen authority;
- stable hierarchical identity is defined;
- every active variant requires an independent human-readable manifest;
- the complete material path and first blocker are explicit;
- no universal precedence policy is created;
- isolated and precedence fixtures remain distinct;
- evidence availability, sufficiency, fitness, admission, validation, support, and Claim permission remain distinct;
- the five measurement classes remain distinguishable;
- descriptive and diagnostic admission remain distinct;
- Validated Result does not automatically become a Finding;
- a Validated R4 Result does not automatically become a Mechanical or Diagnostic Finding;
- R4 eligibility, execution, result validation, and conformance remain distinct;
- exact R4 partition and reconciliation are testable;
- standalone and diagnostic R4 contexts remain distinct;
- controlled determinism and language cases are defined;
- Tested Unsupported and Tested Contradicted remain distinct;
- Evidence Conflict and Test Contradiction remain distinct;
- diagnostic Evidence Conflict remains deferred until concrete diagnostic-use admission and conflict-assessment authority exist;
- R4 method/version binding and diagnostic R3 profile/version binding remain separate fixture contracts;
- Alternative Explanation, ClaimDecision, causal, narrowing, provenance, version, and independent-chain boundaries are covered;
- unsupported diagnostic authority remains deferred;
- no support criterion, causal method, universal precedence, or future Claim policy is invented;
- no benchmark scoring is defined;
- no physical fixture or implementation is created;
- public behavior remains unchanged; and
- R6 is not started.

---

## 50. Physical Fixture Handoff

After R5 is approved and only through separate authorization, a physical-fixture phase may create:

- one physical manifest per active `FX-R5-*` variant;
- tiny synthetic source/canonical datasets;
- exact authority and version bindings;
- expected-result records;
- active and deferred inventory views;
- deterministic runner integration;
- controlled candidate-utterance assets; and
- the authority-to-fixture coverage matrix.

That phase must not silently activate a `DF-R5-*` obligation. Activation requires the missing authority to be approved, the R5 specification to be reviewed, and a new active fixture ID to be assigned.

---

## 51. Dependencies / Next Milestone

R5 depends on the frozen authorities in §4 and the current repository evidence, validation, Claim, artifact, and public-product boundaries.

R5 v1.0 is Approved / Frozen and is the authoritative R5 fixture-governance baseline.

Any next work requires separate explicit authorization. R5 approval does not automatically authorize physical fixture creation, runtime implementation, diagnostic Claim-policy expansion, public behavior changes, benchmark scoring, or R6.

A separately scoped next milestone may plan physical fixture implementation only after explicit authorization. This closeout does not begin that milestone.

---

**End of R5 Diagnostic Synthetic Fixture Suite Specification**
