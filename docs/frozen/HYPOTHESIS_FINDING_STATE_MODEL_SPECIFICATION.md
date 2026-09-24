# CommerceLens AI Hypothesis / Finding State Model Specification

**Document:** `HYPOTHESIS_FINDING_STATE_MODEL_SPECIFICATION.md`  
**Milestone:** R2 — Hypothesis / Finding State Model  
**Version:** R2 v1.0  
**Status:** Approved  
**State:** Frozen  
**Date:** 2026-09-22  
**Project:** CommerceLens AI

---

## 1. Purpose

This specification defines the minimum sufficient runtime representation required to operationalize the frozen R1 Diagnostic Reasoning Specification without copying the R1 semantic taxonomy into a large software lifecycle state machine.

R2 answers this question:

> What is the smallest governed representation that preserves every material diagnostic distinction, binds each judgment to authentic evidence and deterministic authority, retains evaluation history, and keeps `ClaimDecision` as the sole material Claim-permission authority?

The required consistency property is:

```text
same authoritative Diagnostic Proposition
+ same evidence, method, validation, and policy bindings
+ same diagnostic-specific assessments
+ same authoritative ClaimDecision
============================================================
same Derived Material Disposition
```

R2 defines specification-level contracts and invariants. It does not implement those contracts.

---

## 2. Scope

R2 defines:

- Diagnostic Proposition semantics and identity;
- Diagnostic Evaluation semantics and identity;
- immutable finalized-evaluation history;
- the minimum bindings from a Diagnostic Evaluation to existing sufficiency, evidence, execution, validation, and Claim authorities;
- the diagnostic-specific assessments not already represented by existing authorities;
- bounded Analytical Outcome semantics;
- the mandatory Alternative Explanation Check representation;
- the `ClaimCandidate` / `ClaimDecision` boundary;
- deterministic, non-authoritative Derived Material Disposition;
- valid semantic evaluation progression;
- prohibited state combinations and authority substitutions;
- Missing Evidence and External Evidence Required representation;
- the two distinct contradiction semantics;
- causal-boundary representation;
- deterministic derivation precedence;
- fail-closed invariants;
- evaluator-conformance requirements; and
- compatibility with current v0.2.0 behavior.

R2 governs material diagnostic judgments. It does not require every transient operational event or user-interface condition to become a retained state.

---

## 3. Non-Scope

R2 does not:

- redesign, amend, or weaken frozen R1 semantics;
- define diagnostic Required Evidence matrices or hypothesis-family-specific field requirements;
- approve diagnostic tests, statistical methods, validation algorithms, or support thresholds;
- define hypothesis-generation logic;
- define automatic web research or external-evidence acquisition;
- create a causal identification or causal admission framework;
- change current Metric semantics;
- change the existing Evidence Contract;
- replace or expand the authority of `ClaimDecision`;
- change current v0.2.0 Claim policy or public behavior;
- define a mutable workflow engine, orchestration loop, or agent state machine;
- prescribe database tables, persistence schemas, migrations, runtime classes, Pydantic models, enums, APIs, or module layout;
- implement rendering or an LLM-as-judge post-render system;
- create tests or fixtures; or
- begin R3, R4, R5, or R6.

Semantic labels written in uppercase in this document identify governed meanings. They are not automatically approved runtime enum members.

---

## 4. Frozen Authorities

R2 is subordinate to all Approved / Frozen specifications under `docs/frozen/`, especially:

- `PROJECT_MASTER_INSTRUCTIONS.md`;
- `SKILL_SCOPE_SPECIFICATION.md`;
- `EVIDENCE_CONTRACT_SPECIFICATION.md`;
- `ARCHITECTURE_SPECIFICATION.md`;
- `CANONICAL_DATASET_AND_METRIC_DICTIONARY.md`;
- `EVALUATION_FIXTURES_SPECIFICATION.md`; and
- `DIAGNOSTIC_REASONING_SPECIFICATION.md` (R1).

When this specification uses an existing governed term, the existing definition remains authoritative. R2 allocates representation; it does not redefine the term.

The following frozen non-equivalences remain mandatory:

```text
Hypothesis != Finding
ExecutedResult != ValidatedResult
ValidatedResult != AdmissibleEvidence
AdmissibleEvidence != ClaimDecision
ClaimDecision != Finding
Mechanical Contribution != Causal Contribution
Supported Diagnostic Finding != Identified Cause
```

If implementation convenience conflicts with a frozen semantic, the frozen semantic controls and the affected implementation must fail closed.

---

## 5. Governing Principles

### 5.1 Reuse before duplication

Existing authoritative records remain authoritative. A Diagnostic Evaluation references or binds them; it does not recreate their states.

### 5.2 Material meaning before lifecycle vocabulary

R1 terms describe material semantic outcomes. Their existence does not imply that each term requires a persisted enum or a mutable transition.

### 5.3 Evaluation is a judgment record, not an orchestrator

A Diagnostic Evaluation binds the material inputs, authorities, diagnostic assessments, and decision associated with one governed judgment. It is not a workflow controller, step runner, or agent loop.

### 5.4 Analytical success is not permission

`CRITERION_MET` means only that the governed analytical criterion was met by a successfully executed and validated test. It does not authorize a Claim or Finding.

### 5.5 Claim permission has one authority

The existing deterministic `ClaimDecision` remains the sole material Claim-permission authority. No R2 assessment or disposition may approve, repair, or override a Claim.

### 5.6 Finalized history is immutable

A material Diagnostic Evaluation, once finalized, remains an accurate record of its original proposition, evidence, method, validation, policy, judgment, and decision. Later evidence or policy creates another evaluation rather than rewriting the earlier one.

### 5.7 Derivation is deterministic and fail-closed

The first controlling material blocker under the frozen precedence determines the disposition. Later conditions cannot repair an earlier failure.

### 5.8 Language cannot exceed authority

Rendering must remain within the exact proposition, claim class, scope, qualifications, limitations, causal boundary, and `ClaimDecision` authorization.

### 5.9 LLM confidence is not evidence

No probability, confidence label, plausibility judgment, disclaimer, or fluent wording may satisfy a required evidence, execution, validation, support, or permission condition.

---

## 6. Existing Runtime Authorities

R2 reuses the following current architecture authorities or their canonical successors:

| Existing authority | R2 use | R2 must not do |
|---|---|---|
| `DataSufficiencyResult` | Bind Required Evidence, Available Evidence, material gaps, clarification, and execution eligibility | Create a second diagnostic sufficiency status |
| `ExecutionRecord` | Prove whether governed execution was attempted, completed, blocked, or failed | Copy execution status into a new diagnostic authority |
| `ExecutedResult` | Bind actual deterministic output to execution, Metric, scope, period, unit, and currency | Treat execution as validation or permission |
| `ValidationRecord` | Bind applicable validation rule, outcome, version, and failure detail | Re-evaluate validation inside R2 disposition logic |
| `ValidatedResult` | Prove that an Executed Result passed all required validation for its intended use | Create a substitute validated-result flag |
| `EvidenceAdmissibilityRecord` | Bind proposition- and use-relevant admissibility evaluation and failure reason | Treat availability as admissibility |
| `AdmissibleEvidence` | Bind authentic evidence that may serve the specified claim type, scope, and intended use | Treat it as Claim permission |
| `ClaimCandidate` | Represent the exact structured material Claim proposed for permission evaluation | Treat candidate creation as permission |
| `ClaimDecision` | Provide the sole authoritative material Claim permission or denial | Create an R2 permission boolean or approval engine |
| Artifact references and fingerprints | Authenticate immutable authority and prevent substitution | Infer authority from equal values or similar prose |
| Versioned policy and method references | Preserve reproducibility and historical meaning | Resolve version changes by overwriting old records |
| Retained evidence and immutable artifacts | Preserve reviewable history | Rely on conversational memory or “latest” state |

Existing `RunStatus`, `MetricState`, `ClaimState`, execution status, validation status, evidence-admissibility status, and failure details remain separate domains. R2 does not merge them into a universal state.

### 6.1 Minimum new representation

The minimum R2 representation consists conceptually of:

1. one governed Diagnostic Proposition concept;
2. one immutable finalized Diagnostic Evaluation concept;
3. references to existing authorities;
4. an Evidence Conflict Assessment;
5. an Analytical Outcome;
6. an Alternative Explanation Check;
7. an authoritative `ClaimDecision` reference when Claim evaluation occurs; and
8. a deterministic Derived Material Disposition projection.

Only items 4–6 are new diagnostic-specific assessments. Item 8 is a projection, not an authority.

---

## 7. Diagnostic Proposition Contract

A Diagnostic Proposition is the exact structured material meaning submitted for diagnostic evaluation.

It must define or bind, as applicable:

- the claimed relationship, pattern, association, segment difference, or interpretation;
- the observed outcome being examined or explained;
- the intended claim class;
- governed analytical scope;
- relevant population or populations;
- period or periods and comparison basis;
- relevant variables and their governed semantics;
- authoritative Metric references and definition versions;
- materially relevant units and currencies;
- the direction and bounded strength of the proposed relationship;
- material semantic constraints needed to distinguish it from broader or stronger Claims; and
- references to the Business Question or supported sub-question when required by the Evidence Contract.

A Diagnostic Proposition may be a first-class governed interpretation artifact or an equivalent contract concept in a future implementation. R2 requires its semantics and stable referential identity; it does not prescribe its physical class or storage form.

A Diagnostic Proposition is not:

- evidence;
- a test result;
- a `ClaimDecision`;
- a Finding;
- a confidence assessment; or
- permission to render material wording.

Free-form prose may accompany the proposition as explanatory metadata, but prose alone cannot define the authority-bearing material meaning.

### 7.1 Representability

A proposition is representable only when its material meaning can be expressed through governed structured fields and references without unresolved ambiguity.

An unrepresentable or materially ambiguous proposition must fail closed before testing. Its disposition is controlled by clarification or insufficiency semantics, not by an invented test result.

### 7.2 Proposition family metadata

A future implementation may attach a non-authoritative family or category for organization, discovery, or method lookup. Family membership:

- is metadata only;
- does not establish Required Evidence;
- does not select evidence by itself;
- does not authorize a test;
- does not establish support; and
- does not authorize a Claim.

---

## 8. Proposition Identity

Proposition identity is determined by material meaning, not by display text, object location, or the evidence currently available.

### 8.1 Material identity dimensions

The following are part of proposition identity when material to the Claim:

- claimed relationship or pattern;
- relationship direction;
- observed target outcome;
- intended claim class;
- analytical scope;
- population;
- periods and comparison basis;
- relevant variables and their semantic meaning;
- authoritative Metric definitions;
- materially relevant units and currencies; and
- constraints that bound the proposition's strength, interpretation, or intended use.

### 8.2 Changes requiring a new proposition

A new Diagnostic Proposition is required when any material identity dimension changes, including:

- the relationship or its direction changes;
- the target outcome changes;
- a diagnostic proposition becomes causal, predictive, or otherwise changes claim class;
- material scope changes;
- material population changes;
- material period or comparison basis changes;
- the meaning of a relevant variable changes;
- the governing Metric semantics change; or
- the proposition is materially broadened, narrowed, or strengthened.

Changing a period or population normally changes the exact proposition because R1 defines those elements as part of the proposition. Related propositions may share non-authoritative family metadata, but they must not share material authority merely because they are comparable.

### 8.3 Changes not requiring a new proposition

The following do not create a new proposition when material meaning remains identical:

- display-label changes;
- grammar or formatting changes;
- translation that preserves exact meaning;
- explanatory notes that do not alter the governed Claim;
- ordering changes; and
- non-material organizational metadata.

### 8.4 Identity mechanism deferred

R2 does not prescribe identifier syntax, hashing, canonical serialization, or persistence keys. A future implementation must use the project's stable identifier and fingerprint patterns without making an opaque hash the only reviewable statement of proposition meaning.

---

## 9. Diagnostic Evaluation Contract

A Diagnostic Evaluation is one governed material-judgment instance applied to one exact Diagnostic Proposition using a specific set of authoritative inputs and versions. It becomes an immutable material-judgment record upon finalization.

It must bind or reference, as applicable:

- the exact Diagnostic Proposition;
- Required Evidence definition and version;
- evidence-package references and fingerprints;
- `DataSufficiencyResult` authority;
- evidence-admissibility authority and admitted evidence references;
- governed method or test definition and version;
- governed support criterion and version;
- applicable validation profile or validation requirements;
- `ExecutionRecord` and `ExecutedResult` authority;
- `ValidationRecord` and `ValidatedResult` authority;
- Evidence Conflict Assessment;
- Analytical Outcome;
- Alternative Explanation Check;
- applicable policy identity and version;
- `ClaimCandidate` reference when a candidate is created;
- authoritative `ClaimDecision` reference when evaluated;
- material assumptions, limitations, qualifications, and blocking reasons;
- the resulting Derived Material Disposition or the authoritative inputs from which it is recomputed; and
- finalization identity, timestamp, or equivalent governed event identity.

The Diagnostic Evaluation records its own diagnostic judgments, but primarily binds immutable references, fingerprints, and versions to upstream authority. It must not copy entire upstream artifacts merely for convenience.

Minimum duplicated material fields are permitted only when necessary to preserve stable historical interpretation, detect mismatched authority, or support deterministic derivation. Duplicated fields never outrank their authenticated authority.

### 9.1 Evaluation is not orchestration

A Diagnostic Evaluation does not command execution, advance through mutable steps, retry work, or select agents. Operational orchestration may construct the authoritative inputs, but it is outside R2.

### 9.2 Unfinalized evaluation assembly

Before finalization, one Diagnostic Evaluation may accumulate the authoritative bindings and diagnostic judgments required to form that single intended material judgment. Binding execution or validation authority, recording Analytical Outcome, completing the Alternative Explanation Check, attaching a `ClaimCandidate`, and attaching the authoritative `ClaimDecision` do not by themselves create a new evaluation identity when they belong to the same intended judgment and the evaluation has not yet been finalized.

This permitted assembly is construction of one judgment record. It does not make Diagnostic Evaluation a workflow controller, define operational sequencing, or authorize mutation after finalization.

### 9.3 Finalization

An evaluation becomes finalized when it is retained as the material judgment for its bound inputs, whether the outcome is promotional or non-promotional. Missing Evidence, Execution Failed, Validation Failed, Tested Unsupported, Tested Contradicted, and Claim denial may all be finalized evaluations.

Transient construction details need not become material evaluation history unless existing project governance requires them.

---

## 10. Evaluation Identity

`Diagnostic Proposition != Diagnostic Evaluation`.

One proposition may have multiple evaluations. Evaluation identity includes the proposition plus the material authority set used to judge it.

While one evaluation is unfinalized, the bindings and judgments belonging to its one intended material judgment may be assembled without creating successive evaluation identities. A new evaluation is required when an evaluation has been finalized and any materially relevant evaluation binding or judgment capable of changing its meaning or disposition changes, including:

- evidence package or evidence fingerprint;
- newly admitted external evidence;
- Required Evidence definition or version;
- sufficiency or admissibility authority;
- method or test version;
- support-criterion version;
- validation profile or rule version;
- execution or Validated Result authority;
- diagnostic-specific assessment;
- applicable Claim policy version;
- `ClaimCandidate` material meaning; or
- other authority references capable of changing the material judgment.

An operational retry that produces a new execution authority must not be silently substituted into an earlier finalized evaluation. It may support a new evaluation for the same proposition. Before finalization, attaching the intended execution authority to the evaluation being assembled does not by itself require another evaluation identity.

Authorities from different evaluation instances must not be merged unless a separately governed new evaluation explicitly binds and evaluates the combined authority set.

A material Finding must bind to the actual Diagnostic Evaluation and authoritative `ClaimDecision` that permitted it. “Latest evaluation” is a query convenience, never a material authority reference.

---

## 11. Evaluation Immutability and History

### 11.1 Unfinalized assembly boundary

An unfinalized Diagnostic Evaluation may be completed with the authority and judgments required for its one intended material judgment. Normal completion of execution/validation bindings, Analytical Outcome, Alternative Explanation Check, `ClaimCandidate`, and authoritative `ClaimDecision` is not historical mutation and must not cause evaluation-record explosion.

This assembly permission ends at finalization and does not define runtime orchestration.

### 11.2 Immutability rule

Once finalized, a Diagnostic Evaluation must not be mutated into a different material outcome.

After finalization, material changes require a new evaluation when the proposition remains materially identical. This includes:

- new admitted evidence;
- different method or test version;
- different support criterion;
- different validation profile;
- different policy version;
- newly admitted external evidence;
- changed diagnostic assessment or ClaimDecision authority;
- a materially different `ClaimCandidate`; and
- a different authoritative execution or result.

### 11.3 Historical example

```text
Diagnostic Proposition H1
├─ Evaluation E1 → Missing Evidence
├─ Evaluation E2 → Tested but Unsupported
└─ Evaluation E3 → Supported Diagnostic Finding
```

E3 does not replace, amend, or retroactively invalidate E1 or E2. Each remains traceable to its original evidence, method, validation, policy, assessment, and decision.

### 11.4 Historical authority

A historical Finding remains bound to the evaluation and decision that originally authorized it. A later evaluation may produce a different current judgment, but it does not silently rewrite the provenance of the earlier Finding.

Any future product presentation of supersession, recency, or current preferred evaluation must remain separate from authority identity and must preserve the complete record.

---

## 12. Reuse of Sufficiency and Evidence Authority

### 12.1 Required Evidence

Diagnostic Evaluation binds the proposition-specific Required Evidence definition and version. R2 does not encode the R3 Required Evidence matrix.

Required Evidence is not satisfied by field presence. Its authority must preserve applicable semantic validity, relevance, source authority, completeness, temporal alignment, population alignment, Metric compatibility, unit/currency compatibility, measurement validity, missingness, provenance, and validation requirements.

### 12.2 Availability and admissibility remain distinct

Evidence availability and evidence admissibility must remain semantically separate:

```text
Available Evidence != AdmissibleEvidence
```

Availability is represented through existing sufficiency and available-evidence authority. Admissibility is represented through existing evidence-admissibility authority. R2 must not collapse them into one diagnostic field.

### 12.3 Binding rather than duplication

The Diagnostic Evaluation should bind:

- the applicable sufficiency authority;
- relevant admissibility records;
- admitted evidence references;
- blocking evidence reasons; and
- relevant fingerprints and versions.

It must not restate upstream status as a competing source of truth.

### 12.4 Inadmissible evidence

Evidence that is present but inadmissible must remain distinguishable from absent evidence through the authoritative admissibility record and blocking reason. It may control a Missing Evidence, Insufficient Evidence, or applicable governed evidence-failure disposition under R1 precedence, but its presence and inadmissibility must remain reviewable.

---

## 13. Test / Method Binding

A hypothesis is testable only when the following are defined without material ambiguity for the exact proposition:

- proposition;
- observed outcome and governed scope;
- Required Evidence and semantic requirements;
- population and temporal alignment;
- governed deterministic method or test reference;
- support, non-support, and contradiction criteria;
- applicable validation and reconciliation requirements; and
- maximum claim class the method could support.

Testability is a deterministic condition derived from these bindings. It is not Claim support and need not be persisted as a standalone lifecycle state.

The Diagnostic Evaluation must bind the exact governed method/test and support-criterion versions used. R2 does not approve a method registry, test algorithm, threshold, or hypothesis family.

If the governed method or support criterion is undefined, the proposition remains non-promotional. The disposition is Hypothesis Only or an equivalent governed non-promotional result, not Tested Unsupported.

---

## 14. Execution / Validation Binding

Diagnostic Evaluation reuses existing execution and validation authority.

It must preserve:

```text
not run != execution failed
execution completed != result validated
validation passed for one use != validation passed for another use
```

### 14.1 Execution

- Test not executed is derived from the absence of an applicable completed execution authority or from applicable planned/pending authority.
- Execution Failed requires an authentic failed `ExecutionRecord` for the governed test and bound inputs.
- Failed execution cannot produce `CRITERION_MET`, `CRITERION_NOT_MET`, or `PROPOSITION_CONTRADICTED`.
- Unrelated successful execution cannot repair the failed chain.

### 14.2 Validation

- A tested analytical outcome requires applicable passed validation and a `ValidatedResult` for the intended diagnostic use.
- Validation Failed requires applicable failed validation authority.
- Failed validation cannot be repaired by qualification, disclaimer, or LLM interpretation.
- Validation of a different scope, population, period, method, result, or intended use cannot substitute.

### 14.3 Independent chains

An independently complete and valid evidence chain remains usable when another chain fails. Overall partial completion must not cause authority to cross between chains.

---

## 15. Evidence Conflict Assessment

Evidence Conflict Assessment records whether the admitted evidence bound to the evaluation contains an unresolved material contradiction before a valid support determination can be promoted.

Minimum semantic conditions are equivalent to:

- `NOT_EVALUATED`;
- `NO_MATERIAL_CONFLICT`; and
- `UNRESOLVED_MATERIAL_CONFLICT`.

These labels define required meaning, not an approved runtime enum.

### 15.1 Required content

When a material conflict exists, the assessment must:

- reference the conflicting admissible evidence;
- identify the material proposition dimension affected;
- state why the conflict remains unresolved;
- preserve any governed narrowing that excludes the conflict; and
- prevent promotion of the affected proposition.

### 15.2 No silent selection

The evaluator must not choose the evidence that best supports a preferred narrative. A narrower proposition may proceed only when its scope genuinely excludes the conflict and the narrower meaning is represented as the exact proposition evaluated.

### 15.3 Distinction from tested contradiction

Evidence Conflict Assessment concerns incompatible admitted evidence before a valid support determination. It is not the Analytical Outcome `PROPOSITION_CONTRADICTED`.

---

## 16. Analytical Outcome

Analytical Outcome records the result of applying the governed support criterion to an authentic successfully executed and validated deterministic result.

Minimum semantic outcomes are equivalent to:

| Analytical Outcome | Meaning |
|---|---|
| `NOT_EVALUATED` | No valid support determination exists for the bound evaluation |
| `CRITERION_MET` | The validated deterministic result met the governed support criterion |
| `CRITERION_NOT_MET` | The validated deterministic result did not meet the governed support criterion and did not affirmatively contradict the proposition |
| `PROPOSITION_CONTRADICTED` | The validated deterministic result affirmatively contradicted the exact proposition under its governed contradiction criterion |

These are analytical results, not Claim states.

### 16.1 Preconditions

`CRITERION_MET`, `CRITERION_NOT_MET`, and `PROPOSITION_CONTRADICTED` each require:

- an exact governed test binding;
- successful deterministic execution;
- an authentic Executed Result;
- all applicable validation passed for the intended use;
- an authentic Validated Result; and
- application of the governed support/contradiction criterion version.

### 16.2 Exclusions

The following are not Analytical Outcomes:

- Missing Evidence;
- External Evidence Required;
- unresolved evidence conflict;
- test not executed;
- Execution Failed;
- Validation Failed;
- Claim Prohibited;
- Claim Not Authorized; and
- Supported Diagnostic Finding.

### 16.3 Permission boundary

```text
CRITERION_MET != Claim authorized
```

No analytical outcome may serve as permission without the exact authoritative `ClaimDecision` required by R1.

---

## 17. Alternative Explanation Check

Every proposed Supported Diagnostic Finding must complete an Alternative Explanation Check before promotion.

Minimum semantic conditions are equivalent to:

- `NOT_COMPLETED`;
- `COMPLETED_NO_MATERIAL_COMPETITOR_IDENTIFIED`; and
- `COMPLETED_MATERIAL_COMPETITOR_PRESENT`.

The check is a promotion prerequisite and diagnostic assessment. It is not a hypothesis lifecycle state and does not require mandatory alternative generation.

### 17.1 No competitor identified

Completion with no material competitor means that none was identified under the governed evidence and check. It is not proof of unique causality and does not authorize causal, primary, or “most likely” wording.

### 17.2 Material competitor present

When a material competing interpretation is present, the check must:

- retain references to each identified material competitor;
- preserve each competitor's actual evidence status;
- prevent unsupported uniqueness, primacy, and causal wording;
- preserve applicable limitations or qualifications; and
- provide the check result and references to `ClaimDecision`.

Material competitor presence does not automatically prohibit every bounded diagnostic Claim. The exact proposition and requested wording determine whether the competitor requires narrowing, qualification, or denial.

### 17.3 Existing Alternative Explanation contract

The existing Alternative Explanation evidence status describes an individual alternative. It does not by itself prove that the mandatory check occurred. R2 therefore requires a separate check disposition or equivalent governed record of completion.

### 17.4 Incomplete check

If the analytical criterion is met but the check is incomplete, promotion is blocked. The material record must explicitly preserve both `CRITERION_MET` and `Alternative Explanation Check = NOT_COMPLETED`, with `alternative_explanation_check_incomplete` or a semantically equivalent controlling reason.

This condition is materially distinct from an undefined test, an unexecuted test, or an ordinary untested Hypothesis Only outcome. A conforming implementation may use a more specific derived disposition, a generic non-promotional disposition with the mandatory controlling reason, or another minimal deterministic representation. It need not create a new runtime enum or persisted lifecycle state.

`CRITERION_MET` with an incomplete check is not eligible to proceed to promotional `ClaimCandidate` evaluation. The check must first be completed for the same intended material judgment. Completing it during assembly of that still-unfinalized evaluation does not by itself require a new evaluation identity.

---

## 18. `ClaimCandidate` / `ClaimDecision` Boundary

The mandatory authority path is:

```text
Diagnostic Evaluation
→ deterministic analytical result
→ governed support criterion
→ ClaimCandidate
→ authoritative ClaimDecision
→ Derived Material Disposition
→ bounded rendering
```

### 18.1 `ClaimCandidate`

`ClaimCandidate` is structured permission-evaluation input. For diagnostic use it must represent or bind the exact material proposition, requested claim class, scope, evidence and Validated Result references, method and criterion authority, Alternative Explanation Check, qualifications, limitations, and intended use required by the future approved diagnostic policy.

Current `ClaimPropositionType` supports narrow descriptive metric value/state propositions and may not represent diagnostic relationships. R2 records this compatibility requirement but does not change the contract.

The current `ClaimCandidate` semantic fingerprint also binds evidence references. It therefore must not automatically be treated as stable Diagnostic Proposition identity. Proposition identity and candidate evaluation-input identity serve different purposes.

### 18.2 `ClaimDecision`

The existing deterministic `ClaimDecision` remains the sole material permission authority. It must evaluate the exact structured ClaimCandidate under the applicable governed policy and authentic authority references.

Claim-class eligibility may be determined early to avoid unnecessary analysis. That analytical short-circuit does not constitute final material permission or refusal authority. Final Claim Prohibited semantics must remain traceable to authoritative `ClaimDecision` or to existing governed policy authority represented through `ClaimDecision`-compatible refusal semantics.

Under current v0.2.0, the canonical conceptual behavior is:

```text
requested diagnostic or causal ClaimCandidate
→ authoritative ClaimDecision
→ governed denial such as unsupported_claim_type
→ derived CLAIM_PROHIBITED
```

No unnecessary diagnostic analysis is required before that governed denial, and `ClaimDecision` does not become an orchestration controller.

An authorized diagnostic decision must bind the exact:

- proposition and claim class;
- scope, population, periods, variables, Metrics, units, and currencies;
- evidence and Validated Result authority;
- method, validation, and support-criterion authority;
- Alternative Explanation Check;
- assumptions, limitations, and qualifications; and
- policy identity and version.

### 18.3 Prohibited shortcut

The following is prohibited:

```text
CRITERION_MET → SUPPORTED_DIAGNOSTIC_FINDING
```

Promotion requires:

```text
CRITERION_MET
+ every other frozen R1 promotion prerequisite
+ exact valid ClaimCandidate
+ authoritative ClaimDecision authorization
================================================
SUPPORTED_DIAGNOSTIC_FINDING disposition
```

### 18.4 Current policy

Current v0.2.0 positive permission remains limited to the approved descriptive path. Diagnostic `ClaimCandidate` refusal with `unsupported_claim_type` remains correct and conforming. R2 does not authorize a policy change.

---

## 19. Derived Material Disposition

Derived Material Disposition is a deterministic read model that projects the controlling material outcome from authenticated immutable inputs.

It exists to:

- give evaluators and renderers one deterministic material interpretation of the bound authorities;
- preserve R1 precedence;
- prevent free-form interpretation of failure combinations; and
- expose the specific controlling non-promotional or promotional outcome.

It is not an authority.

### 19.1 Authority rule

Derived Material Disposition must not:

- approve a Claim;
- independently prohibit or refuse a Claim;
- replace `ClaimDecision`;
- recompute Metric, evidence, execution, or validation authority;
- override a decision;
- repair a denial;
- infer missing evidence;
- act as a second policy engine; or
- authorize wording stronger than the exact decision.

### 19.2 Recomputability and caching

The disposition should be deterministically recomputable from the authenticated Diagnostic Evaluation, upstream authority references, diagnostic-specific assessments, and `ClaimDecision`.

A future implementation may cache or store the projection. If cached content conflicts with authoritative recomputation:

```text
authoritative deterministic derivation wins
```

The cache must be treated as invalid, stale, or corrupt. It cannot become a dual source of truth.

### 19.3 Semantic disposition families

The minimum material families include:

- `CLARIFICATION_REQUIRED`;
- `HYPOTHESIS_ONLY`;
- `TESTABLE_NOT_EXECUTED`;
- `MISSING_EVIDENCE`;
- `EXTERNAL_EVIDENCE_REQUIRED`;
- `CONFLICTING_EVIDENCE`;
- `EXECUTION_FAILED`;
- `VALIDATION_FAILED`;
- `TESTED_UNSUPPORTED`;
- `TESTED_CONTRADICTED`;
- `CLAIM_NOT_AUTHORIZED`;
- `CLAIM_PROHIBITED`; and
- `SUPPORTED_DIAGNOSTIC_FINDING`.

In addition, `CRITERION_MET` with an incomplete Alternative Explanation Check must have an explicitly distinguishable non-promotional representation and mandatory controlling reason. These names and conditions specify material meanings. Implementations may use a smaller structure with reason codes when all distinctions, precedence, and rendering requirements remain deterministic and reviewable.

### 19.4 Controlling inputs

| Disposition family | Controlling authoritative condition |
|---|---|
| Clarification Required | Proposition or Required Evidence meaning is materially ambiguous or unrepresentable |
| Hypothesis Only | Proposition remains non-promotional because governed test/support definition is not established or the hypothesis is otherwise untested; it does not absorb a completed validated `CRITERION_MET` outcome whose Alternative Explanation Check is incomplete |
| Testable Not Executed | Proposition, Required Evidence, method, criterion, and validation requirements are defined, no earlier blocker controls, but the governed test was not run |
| Missing Evidence | Existing sufficiency/admissibility authority identifies a material internal evidence gap, invalidity, ambiguity, misalignment, or inadmissibility, with the specific blocking reason retained |
| External Evidence Required | An unmet material Required Evidence dependency is external and lacks governed admission |
| Conflicting Evidence | Evidence Conflict Assessment identifies unresolved material conflict within admissible evidence |
| Execution Failed | Applicable authentic execution authority failed |
| Validation Failed | Applicable execution succeeded but required validation failed or remained blocking |
| Tested Unsupported | Analytical Outcome is `CRITERION_NOT_MET` |
| Tested Contradicted | Analytical Outcome is `PROPOSITION_CONTRADICTED` |
| Claim Not Authorized | Analytical and promotion prerequisites permit Claim evaluation, but authoritative `ClaimDecision` denies the exact otherwise eligible Claim for a reason other than globally unavailable claim class |
| Alternative Check Incomplete, represented minimally | Analytical Outcome is `CRITERION_MET`, the mandatory check is `NOT_COMPLETED`, promotion is blocked, and the controlling reason explicitly identifies the incomplete check; no dedicated runtime enum is required |
| Claim Prohibited | Authoritative `ClaimDecision`, or existing governed policy authority represented through `ClaimDecision`-compatible refusal semantics, denies the restricted or unavailable claim class; current causal requests are included |
| Supported Diagnostic Finding | Every frozen R1 prerequisite passes and authoritative `ClaimDecision` authorizes the exact bounded diagnostic Claim |

### 19.5 Reason preservation

Disposition family alone may be insufficient. The material record must preserve the controlling reason, relevant authority references, and applicable versions. In particular, evidence absent and evidence present-but-inadmissible may share a broader non-promotional family only when the specific difference remains explicit and deterministic.

---

## 20. Deterministic Derivation Precedence

Derived disposition must follow this order, which allocates the frozen R1 precedence without redefining it:

1. requested claim-class restriction;
2. Diagnostic Proposition representability;
3. Required Evidence definition;
4. unresolved external dependency;
5. material evidence defect, including absence, invalidity, ambiguity, misalignment, or inadmissibility;
6. unresolved material conflict within admissible evidence;
7. governed test availability and execution eligibility;
8. execution outcome;
9. validation outcome;
10. Analytical Outcome;
11. Alternative Explanation Check;
12. authoritative `ClaimDecision`; and
13. final Derived Material Disposition.

The first controlling material blocker determines the disposition. Later facts may be retained for audit where authentic, but they must not repair or displace the earlier blocker.

For a claim-class restriction at step 1, the blocker controls analytical eligibility and the governed refusal reason; it does not itself issue final material permission/refusal. The final Claim Prohibited disposition still requires the authoritative refusal trace defined in Sections 18.2 and 20.1.

Each controlling step must be traceable to:

- a reason;
- authentic authority references;
- relevant scope, population, periods, and intended use; and
- applicable version or policy.

### 20.1 Claim-class restriction

Restricted claim class is evaluated first for analytical eligibility, so prohibited classes may short-circuit unnecessary analytical work. This early restriction is not final material permission/refusal authority. Claim Prohibited is derived only from an authoritative governed refusal traceable to `ClaimDecision` or existing policy authority represented through `ClaimDecision`-compatible refusal semantics. A causal request remains prohibited even if diagnostic evidence exists, and diagnostic authorization cannot be reused.

### 20.2 Alternative Check position

The mandatory check follows a valid analytical result and precedes promotional Claim permission. `CRITERION_MET` with an incomplete check blocks promotion and must retain the incomplete-check controlling reason rather than collapse into ordinary Hypothesis Only. A completed check with a competitor supplies constraints and references to `ClaimDecision` rather than automatically producing denial.

### 20.3 Decision position

For the positive diagnostic path, `ClaimDecision` evaluates an exact candidate with all applicable promotion prerequisites represented. A restricted claim class may instead reach governed `ClaimDecision`-compatible refusal without unnecessary diagnostic analysis. In both cases, authoritative governed policy controls material permission/refusal; Derived Material Disposition may classify the result but cannot independently decide or reinterpret it.

---

## 21. Valid Evaluation Progression

The following describes semantic progression, not a mutable FSM or orchestration implementation:

```text
requested restricted claim class
→ analytical eligibility denied without unnecessary analysis
→ ClaimCandidate / ClaimDecision-compatible governed refusal
→ Claim Prohibited disposition

Diagnostic Hypothesis
→ exact proposition, Required Evidence, method, criterion, and validation requirements defined
→ testable condition can be derived

testable condition
├─ material internal evidence gap → Missing Evidence
├─ unresolved external dependency → External Evidence Required
├─ unresolved admissible-evidence conflict → Conflicting Evidence
├─ governed test not run → Testable Not Executed
└─ governed test executed
   ├─ execution failed → Execution Failed
   └─ execution succeeded
      ├─ validation failed → Validation Failed
      └─ validation passed
         ├─ criterion not met → Tested Unsupported
         ├─ proposition contradicted → Tested Contradicted
         └─ criterion met
            → Alternative Explanation Check
            ├─ not completed
            │  → non-promotional
            │  → controlling reason: Alternative Explanation Check incomplete
            └─ completed
               → ClaimCandidate
               → authoritative ClaimDecision
               ├─ claim class prohibited → Claim Prohibited
               ├─ exact claim denied → Claim Not Authorized
               └─ exact claim authorized → Supported Diagnostic Finding
```

This progression defines valid material dependencies. Completing these bindings and judgments within one unfinalized evaluation is normal evaluation assembly, not a requirement to create an evaluation at each line. The progression does not require a central transition method, mutable current-state field, or sequential runtime controller.

---

## 22. Prohibited Combinations / Transitions

R2 prohibits any representation or derivation equivalent to:

- Hypothesis directly becoming Supported Diagnostic Finding;
- Missing Evidence becoming Supported without new governed admitted evidence and a new evaluation;
- external evidence being found and therefore treated as admitted;
- execution success becoming support without validation;
- validation success becoming support without applying the governed criterion;
- `CRITERION_MET` becoming Supported Diagnostic Finding without `ClaimDecision`;
- Alternative Explanation Check not completed while promotion is permitted;
- unresolved material evidence conflict coexisting with promotion of the affected proposition;
- execution or validation failure coexisting with a tested analytical outcome for the same chain and intended use;
- `ClaimDecision` denial followed by renderer assertion of the denied Finding;
- diagnostic authorization carrying into a causal Claim;
- one proposition's `ClaimDecision` authorizing a materially different proposition;
- one scope, population, period, method, result, or policy being silently substituted for another;
- evidence or decision authority being assembled from different evaluations without a new governed evaluation;
- LLM confidence, intuition, repetition, or user insistence causing promotion;
- a disclaimer repairing unsupported material content;
- qualification repairing failed required validation;
- a cached disposition overriding authoritative derivation; or
- normal assembly of one unfinalized material judgment being fragmented into multiple evaluation identities; or
- a new evaluation overwriting prior finalized evaluation history.

Invalid combinations must fail closed and identify the controlling inconsistency or authority mismatch.

---

## 23. Missing Evidence

Missing Evidence is a material disposition derived from existing Required Evidence, sufficiency, and admissibility authority plus a specific blocking reason. It is not an Analytical Outcome.

The representation must preserve whether evidence is:

- absent;
- present but semantically invalid;
- ambiguous;
- temporally misaligned;
- population-misaligned;
- incompatible in Metric, unit, or currency semantics;
- not valid for the intended measurement;
- insufficiently complete;
- inadequately traceable; or
- present but inadmissible for the exact proposition and intended use.

These differences need not each become an enum member. They must remain deterministically visible through the controlling reason and authority references.

Missing Evidence must not be used for:

- test not executed;
- execution failure;
- validation failure;
- unresolved conflict among admissible evidence;
- criterion not met; or
- validated proposition contradiction.

If a narrower independently complete proposition avoids the missing evidence, it must be represented and evaluated as that exact narrower proposition.

---

## 24. External Evidence Required

R2 preserves ordinary internal Missing Evidence and External Evidence Required as materially distinct.

External Evidence Required is derived when:

- an applicable Required Evidence dependency is classified as external to the current governed evidence package;
- the dependency is material to the proposition;
- no governed admitted external evidence satisfies it; and
- no earlier claim-class or representability blocker controls.

The minimum conceptual representation uses:

- Required Evidence dependency/source classification;
- evidence availability and admission authority;
- a blocking reason; and
- the External Evidence Required disposition.

R2 does not authorize automatic browsing, acquisition, admission, or trust of public or user-provided external information.

```text
external information found != governed external evidence admitted
```

If external evidence is later admitted, the same proposition receives a new Diagnostic Evaluation. The earlier External Evidence Required evaluation remains immutable.

---

## 25. Contradiction Semantics

R2 preserves two distinct material meanings.

### 25.1 Unresolved evidence conflict

This occurs when admissible evidence contains unresolved material conflict that prevents a valid support determination for the exact proposition.

Representation:

- Evidence Conflict Assessment = unresolved material conflict;
- references to the conflicting evidence; and
- Derived Material Disposition = Conflicting Evidence or semantically equivalent.

It must not be represented as Missing Evidence or Tested Contradicted.

### 25.2 Proposition contradicted by test

This occurs when:

- the governed test executed successfully;
- all applicable validation passed;
- an authentic Validated Result exists; and
- the governed contradiction criterion affirmatively contradicts the exact proposition.

Representation:

- Analytical Outcome = `PROPOSITION_CONTRADICTED`; and
- Derived Material Disposition = Tested Contradicted or semantically equivalent.

It must not be represented as evidence conflict, missing evidence, non-execution, validation failure, or ordinary lack of support.

### 25.3 Tested unsupported

`CRITERION_NOT_MET` means that the specific validated test did not support the proposition within the tested scope, without affirmatively satisfying the contradiction criterion. It is distinct from both contradiction forms.

---

## 26. Causal Boundary

R2 defines no `CAUSAL_SUPPORTED` state because R1 defines no causal admission framework.

A causal request is represented through:

- requested claim class = causal; and
- causal admission authority unavailable under current governance.

The claim-class restriction may stop unnecessary diagnostic analysis, but it is not final refusal authority. The restricted causal `ClaimCandidate` must receive an authoritative governed denial through `ClaimDecision` or existing policy authority represented through `ClaimDecision`-compatible refusal semantics. Claim Prohibited is then derived from that refusal.

No combination of the following authorizes causality:

- diagnostic `CRITERION_MET`;
- statistical association;
- temporal sequence;
- significance;
- concentration or segment difference;
- mechanical decomposition;
- elimination of some alternatives;
- diagnostic `ClaimDecision`; or
- LLM confidence.

Diagnostic authorization must not be inherited, upgraded, or relabeled across the causal boundary. Diagnostic `contributed to` remains prohibited. Mechanical contribution language remains separately governed and method-relative.

---

## 27. Claim Prohibited vs Claim Not Authorized

These dispositions preserve different material reasons.

### 27.1 Claim Prohibited

Claim Prohibited means authoritative governed policy, expressed by `ClaimDecision` or `ClaimDecision`-compatible refusal semantics, refused the requested claim class because it is unavailable or restricted. Current causal claims are the canonical example because no causal admission authority exists. Early claim-class eligibility may short-circuit unnecessary analysis, but it does not itself own final material refusal semantics.

### 27.2 Claim Not Authorized

Claim Not Authorized means the claim class may exist conceptually and the analytical path reached permission evaluation, but authoritative `ClaimDecision` did not authorize the exact material Claim.

The denial may concern exact representation, evidence binding, scope, intended use, qualifications, policy, or another governed Claim condition.

### 27.3 Representation rule

These meanings may later be represented through disposition family, `ClaimDecision` reason/failure code, or another minimal structure. Separate runtime enums are not required, but a reasonless generic refusal is non-conforming.

The renderer must preserve the authoritative denial reason at the appropriate user-facing level and must not imply that analytical non-support caused a policy denial, or vice versa.

---

## 28. Rendering Boundary

R2 defines only the minimum rendering contract necessary to preserve authority.

Rendered material content must not exceed:

- the exact authorized proposition;
- authorized claim class;
- governed scope, population, periods, variables, Metrics, units, and currencies;
- required qualifications;
- material limitations;
- Alternative Explanation Check constraints;
- causal boundary; and
- authoritative `ClaimDecision`.

Rendering must distinguish Findings from hypotheses, tested non-support, contradiction, evidence defects, execution/validation failures, and policy refusal.

The exact proposition evaluated must match the proposition rendered. Material paraphrase that changes relationship direction, scope, strength, uniqueness, primacy, or claim class requires a different candidate and decision.

A disclaimer appended after an unauthorized assertion does not repair it. R2 does not authorize an LLM-as-judge renderer or post-render semantic approval system.

---

## 29. Fail-Closed Invariants

R2 requires all of the following:

1. A Supported Diagnostic Finding requires an authoritative `ClaimDecision` authorizing the exact Claim.
2. `CRITERION_MET`, `CRITERION_NOT_MET`, and `PROPOSITION_CONTRADICTED` require successful execution and passed validation for the intended use.
3. Tested Contradicted requires an authentic validated deterministic result and governed contradiction criterion.
4. Missing Evidence must not be represented as tested.
5. External Evidence Required cannot become supported without governed external-evidence admission and a new evaluation.
6. Diagnostic authorization cannot authorize causal wording.
7. Material evidence, method, validation, criterion, or policy changes cannot overwrite a prior finalized evaluation.
8. The proposition evaluated must materially match the proposition rendered.
9. Alternative Explanation Check must be completed before promotion.
10. Unresolved material conflict within admissible evidence blocks promotion of the affected proposition.
11. `ClaimDecision` denial cannot be repaired by renderer, qualification, or disposition derivation.
12. Authority references must match governed scope, population, periods, method, intended use, versions, and fingerprints.
13. The earliest controlling material blocker determines disposition.
14. Later conditions cannot repair an earlier material failure.
15. Independently complete valid chains survive unrelated failures.
16. Derived Material Disposition cannot override `ClaimDecision`.
17. Cached or stored disposition cannot override deterministic derivation from authoritative references.
18. Equal values, similar prose, or shared family metadata cannot substitute authority across evaluations.
19. A Finding must bind to the exact evaluation and decision that authorized it, not a dynamic latest evaluation.
20. LLM confidence, intuition, ranking, or disclaimer cannot satisfy or override any material gate.
21. Claim Prohibited must be derived from authoritative governed refusal semantics; early claim-class eligibility restriction is not final material permission/refusal authority.
22. Assembly of bindings and judgments within one unfinalized evaluation does not require a new evaluation identity; a material change after finalization does.
23. `CRITERION_MET` with an incomplete Alternative Explanation Check remains explicitly non-promotional and materially distinguishable from an untested hypothesis.

Any unresolved invariant violation produces a non-promotional fail-closed outcome for the affected chain.

---

## 30. v0.2.0 Compatibility

Current v0.2.0 behavior remains conforming and unchanged.

In particular:

- current positive `ClaimDecision` permission remains bounded to approved descriptive Claims;
- diagnostic Claim candidates remain unsupported by current policy;
- `unsupported_claim_type` diagnostic refusal remains correct;
- the public conclusion “Insufficient evidence to conclude why Revenue declined.” remains conforming;
- an independently authorized descriptive Revenue Change may still be rendered while the diagnostic explanation is refused;
- no R2 semantic disposition authorizes public diagnostic expansion; and
- no future representation requirement retroactively makes current refusal defective.

R2 specifies the contract a future separately approved diagnostic implementation must satisfy. It does not authorize that implementation or policy update.

---

## 31. Evaluator Conformance Requirements

Two conforming evaluators receiving materially identical authoritative inputs must agree on:

- proposition identity;
- whether a new proposition or new evaluation is required;
- the controlling evidence, execution, validation, conflict, analytical, alternative-check, and policy condition;
- the first controlling blocker under precedence;
- the Derived Material Disposition;
- whether Claim permission evaluation is eligible;
- whether the exact `ClaimDecision` authorizes rendering; and
- the maximum permitted claim strength and wording class.

Conformance concerns material judgment, not identical internal object layout or prose.

### 31.1 Required conformance cases

The future evaluation suite must cover at least:

1. proposition unrepresentable;
2. proposition defined but governed test undefined;
3. testable but not executed;
4. ordinary internal evidence missing;
5. external evidence required;
6. evidence present but inadmissible;
7. unresolved material conflict within admissible evidence;
8. execution failure;
9. execution success plus validation failure;
10. validated criterion not met;
11. validated proposition contradicted;
12. criterion met plus Alternative Explanation Check incomplete, with a distinct non-promotional controlling reason rather than ordinary Hypothesis Only;
13. criterion met plus material competing interpretation present;
14. analytical conditions pass plus `ClaimDecision` denial;
15. `ClaimDecision` authorization of a bounded diagnostic Finding;
16. diagnostic authorization reused for a causal candidate, requiring authoritative governed refusal and a derived Claim Prohibited disposition;
17. one proposition with multiple immutable evaluations;
18. material proposition change requiring a new proposition;
19. old `ClaimDecision` incorrectly rebound to a new proposition;
20. cached disposition conflicting with authoritative derivation; and
21. LLM confidence or disclaimer used in a promotion attempt.

### 31.2 Judgment record

For each case, conformance review must be able to identify:

- exact proposition;
- exact evaluation inputs and versions;
- applicable authoritative references;
- diagnostic-specific assessments;
- Analytical Outcome;
- controlling precedence step and reason;
- whether the record is an unfinalized assembly or finalized immutable evaluation where identity is material to the case;
- `ClaimCandidate` and `ClaimDecision` where applicable;
- Derived Material Disposition; and
- permitted and prohibited rendering class.

---

## 32. Future Fixture Requirements

Future synthetic fixtures should prove the conformance cases in Section 31 using local deterministic evidence only.

Fixture design must later include positive and negative cases that demonstrate:

- identical material inputs derive identical disposition;
- different evidence/method/policy bindings create separate evaluations;
- materially changed proposition meaning creates a new proposition;
- old authority cannot be rebound;
- history remains intact across Missing Evidence, Tested Unsupported, and later authorization;
- the two contradiction semantics do not collapse;
- Claim Prohibited and Claim Not Authorized retain distinct reasons;
- Alternative Explanation Check completion is mandatory;
- a material competitor constrains wording without automatically denying every bounded Claim;
- cached projection disagreement is detected and authority wins; and
- current v0.2.0 diagnostic refusal remains unchanged.

R2 does not create these fixtures. Their implementation belongs to a later separately authorized milestone.

---

## 33. Risks

| Risk | Required R2 control |
|---|---|
| State explosion | Reuse existing authorities; add only three narrow diagnostic assessments and one derived projection |
| Duplicate authority | References and bindings, not copied execution/validation/admissibility/permission status |
| Disposition becomes second `ClaimDecision` | Explicitly prohibit approval, repair, or override; require authoritative decision for support |
| Proposition identity depends on prose | Require structured material dimensions; prose remains non-authoritative metadata |
| Identity hashing is over-engineered | Defer syntax and hashing; require reviewable meaning and existing identifier conventions |
| Availability and admissibility collapse | Bind separate sufficiency and admissibility authorities |
| Evidence conflict and tested contradiction collapse | Use Evidence Conflict Assessment versus Analytical Outcome |
| Alternative Check becomes lifecycle state | Treat it as a promotion-prerequisite assessment |
| Evaluation history is overwritten | Finalized evaluation immutability and new evaluation on material input change |
| Generic refusal hides material reason | Preserve Claim Prohibited versus Claim Not Authorized and controlling reasons |
| Descriptive behavior changes accidentally | Keep v0.2.0 policy and public behavior unchanged |
| R2 drifts into R3 | Do not define evidence matrices, methods, thresholds, or hypothesis families |
| Evaluation becomes workflow orchestrator | Define immutable judgment record only |
| Cached projection becomes authority | Require deterministic recomputation to prevail |
| “Latest evaluation” becomes dynamic authority | Bind every Finding to its exact evaluation and decision |
| Cross-evaluation authority assembly | Require a new governed evaluation for any combined authority set |

---

## 34. Open Questions

The major R2 architecture choices are resolved. The following implementation-allocation questions remain intentionally deferred and do not block R2 semantic completion.

### 34.1 Physical contract allocation

Should future `DiagnosticProposition` and `DiagnosticEvaluation` contracts reside with interpretation contracts, evidence contracts, or another existing package boundary?

This matters for ownership and dependency direction but does not change their R2 semantics. It affects a future implementation milestone and must be resolved without creating circular authority.

### 34.2 Production ownership of Evidence Conflict Assessment

Which deterministic component produces the assessment for each future approved diagnostic method family?

This matters because the assessment cannot depend on unrestricted LLM judgment. It affects R3 method/evidence allocation and later implementation, not R2 representation.

### 34.3 Minimum retained projection fields

If Derived Material Disposition is cached, which fingerprint, derivation-policy version, and invalidation metadata are sufficient to detect staleness without duplicating authority?

This affects future persistence design. R2 already resolves that authoritative recomputation wins.

### 34.4 Render enforcement allocation

Which future deterministic templates or structured checks enforce that rendering does not exceed the decision?

This affects later integration. R2 defines the boundary but does not design an LLM-as-judge or rendering implementation.

No open question authorizes code, schema, policy, R3, R4, R5, or R6 work.

---

## 35. Success Criteria

R2 conforms only when all statements below are true:

- [x] The minimum sufficient runtime representation is defined.
- [x] Existing governed authorities are reused rather than duplicated.
- [x] R1 taxonomy is not copied into a large lifecycle state machine.
- [x] Diagnostic Proposition and Diagnostic Evaluation are materially distinct.
- [x] Finalized evaluations are immutable.
- [x] Evaluation history remains traceable.
- [x] Proposition identity and new-proposition rules are explicit.
- [x] Evaluation identity and new-evaluation rules are explicit.
- [x] Analytical Outcome is distinct from Claim permission.
- [x] `CRITERION_MET` does not mean Claim authorized.
- [x] Missing Evidence remains distinct from test non-execution, execution failure, and validation failure.
- [x] unresolved Evidence Conflict remains distinct from Proposition Contradicted.
- [x] Tested Unsupported remains distinct from Tested Contradicted.
- [x] External Evidence Required remains distinct from ordinary Missing Evidence.
- [x] Alternative Explanation Check is represented as a mandatory promotion prerequisite.
- [x] `CRITERION_MET` with an incomplete Alternative Explanation Check is explicitly non-promotional and materially distinct from an untested Hypothesis Only outcome.
- [x] Alternative Explanation Generation remains conditional.
- [x] `ClaimDecision` remains the sole material permission authority.
- [x] Supported Diagnostic Finding exists only downstream of an authorized exact `ClaimDecision`.
- [x] Causal requests cannot inherit diagnostic authorization.
- [x] Claim Prohibited remains distinguishable from Claim Not Authorized.
- [x] Claim Prohibited is a derived disposition reflecting authoritative governed refusal, not an independent R2 refusal authority.
- [x] Derived Material Disposition is deterministic and non-authoritative.
- [x] Derived Material Disposition is recomputable from authoritative references.
- [x] Cached disposition cannot override authority.
- [x] Diagnostic Evaluation is not a mutable workflow orchestrator.
- [x] Unfinalized evaluation assembly is distinct from mutation of a finalized immutable evaluation.
- [x] Normal completion of bindings and judgments within one unfinalized evaluation does not create additional evaluation identities.
- [x] Deterministic derivation precedence is explicit.
- [x] Fail-closed invariants are explicit.
- [x] Current v0.2.0 behavior remains unchanged.
- [x] R3–R6 are not started.

---

## 36. Dependencies / Next Milestone

R2 depends on:

- frozen R1 Diagnostic Reasoning Specification;
- frozen Evidence Contract;
- frozen Architecture;
- current Metric, execution, validation, evidence, persistence, and `ClaimDecision` authority; and
- current retained-evidence and fail-closed rules.

This specification is Approved / Frozen and is the authoritative R2 baseline for downstream milestones.

Approval and freeze of R2 do not by themselves authorize:

- runtime implementation of R2;
- diagnostic `ClaimDecision` policy expansion;
- public diagnostic behavior;
- R3 evidence-requirement work;
- R4 method/test design;
- R5 fixtures; or
- R6 governed hypothesis generation.

Any future material change to this frozen specification, implementation plan, or next-phase goal requires explicit owner authorization.

---

**End of R2 Hypothesis / Finding State Model Specification**
