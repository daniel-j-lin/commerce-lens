# CommerceLens AI Diagnostic Reasoning Specification

**Document:** `DIAGNOSTIC_REASONING_SPECIFICATION.md`

**Milestone:** R1 — Diagnostic Reasoning Specification

**Version:** R1 v1.0

**Status:** Approved

**State:** Frozen

**Scope:** Semantic and governance specification only

---

## 1. Purpose

This specification defines how CommerceLens may reason after a validated deterministic result exists without converting a plausible explanation, mathematical decomposition, association, or language-model judgment into an unsupported business cause.

The governing rule remains:

> No material claim without traceable evidence.

R1 operationalizes that rule for diagnostic reasoning. It defines diagnostic claim classes, evidence burdens, promotion rules, wording boundaries, fail-closed outcomes, and evaluator-conformance requirements. It extends the existing Evidence Contract by defining how already-governed evidence constrains diagnostic claims. It does not create a second evidence system or replace the existing deterministic `ClaimDecision` authority.

The intended result is material-decision consistency: given the same material claim, evidence package, intended scope, and policy version, two conforming evaluators MUST reach the same material judgment about what may be stated, what must remain a hypothesis, whether additional evidence is required, whether causal language is prohibited, and whether the affected chain must fail closed.

## 2. Scope

R1 defines semantic and governance rules for:

- Observed Findings;
- Mechanical Drivers and Mechanical Contributions;
- Diagnostic Hypotheses;
- Testable Hypotheses;
- hypotheses that cannot be evaluated because evidence is missing;
- Tested but Unsupported Hypotheses;
- Supported Diagnostic Findings;
- Unsupported Explanations;
- External Hypotheses;
- Alternative Explanations;
- Restricted Causal Claims;
- diagnostic evidence requirements and admissibility;
- diagnostic promotion and non-promotion;
- diagnostic `ClaimDecision` behavior;
- allowed, restricted, and prohibited wording;
- fail-closed behavior;
- integration with the existing Evidence Contract and `ClaimDecision`; and
- future evaluator and fixture requirements.

R1 uses **Supported Diagnostic Finding** as the principal term because it preserves the existing Evidence Contract term **Finding**. **Supported Diagnostic Pattern** and **Supported Diagnostic Association** are permitted user-facing descriptions when they more precisely name the authorized content. None of these terms means that a cause has been identified.

## 3. Non-Scope

R1 does not:

- implement hypothesis generation or decomposition;
- define an LLM prompt system, multi-agent system, RAG system, vector database, or plugin orchestration;
- write SQL, Python analysis code, runtime code, tests, or fixtures;
- define a final Revenue decomposition formula;
- implement product-mix, discount, refund, stockout, or other diagnostic analyses;
- build the R3 Required Evidence Matrix;
- build the R4 decomposition capability;
- build the R5 synthetic benchmark or fixtures;
- define the final R2 runtime state model, enums, transitions, persistence, or schemas;
- acquire external evidence or authorize automatic web research;
- design or implement causal inference;
- change public CommerceLens behavior, v0.2.0, release tags, Metric semantics, or fixture outcomes;
- redesign the Evidence Contract or replace `ClaimDecision`; or
- design R6 Governed Hypothesis Generation.

The semantic vocabulary in this document is intentionally richer than a future minimum runtime model may need. A semantic class defined here MUST NOT be interpreted as a requirement for a runtime enum, persisted value, software branch, or public response section. R2 owns that implementation decision.

## 4. Governing Authority and Principles

### 4.1 Existing authority

This specification is subordinate to the Approved / Frozen documents under `docs/frozen/`, especially the Product Constitution, Skill Scope Specification, Evidence Contract Specification, and Architecture Specification. It also preserves the approved P6 evidence-admissibility boundary, the P8 `ClaimDecision` foundation, and current v0.2.0 public behavior.

Where R1 uses an existing governed term, that term retains its existing meaning. In particular:

- **Required Evidence**, **Available Evidence**, **Validated Result**, and **Admissible Evidence** remain distinct;
- `Executed Result != Validated Result`;
- `Validated Result != AdmissibleEvidence`;
- `AdmissibleEvidence != ClaimDecision`;
- `ClaimDecision != Finding`;
- `ClaimCandidate` is evaluation input, not permission;
- a material Finding requires an authorized `ClaimDecision`;
- qualification cannot repair failed required validation; and
- independently valid chains survive unrelated failures.

### 4.2 Diagnostic governing principles

The following rules are normative:

1. **Hypothesis is not Finding.** Plausibility, model confidence, business familiarity, and fluent explanation are not evidence.
2. **Mechanical contribution is not causal contribution.** An identity-based allocation describes the defined arithmetic, not the underlying business cause.
3. **Supported Diagnostic Finding is not Identified Cause.** Diagnostic support authorizes only the bounded pattern, association, relationship, or interpretation actually tested.
4. **Association is not automatic promotion.** A statistical association is an executed result; it becomes an admissible diagnostic basis only after all claim-specific evidence, validation, alignment, and policy requirements pass.
5. **Causality has a separate admission boundary.** Causal claims are not the next state after diagnostic support.
6. **Language cannot exceed evidence.** A response renderer MUST use wording no stronger than the authorized semantic class.
7. **LLM confidence is not evidence.** R1 authorizes no confidence score, probability, evidence-strength rating, or likelihood label generated by an LLM.
8. **Field presence is not evidence sufficiency.** A named column does not establish its semantics, measurement validity, population, completeness, or admissibility.
9. **Alternative review is required when relevant; invention is forbidden.** The system MUST check for material competing interpretations but MUST NOT generate alternatives merely to fill a format.
10. **Failure is explicit and local.** A blocked diagnostic chain fails closed without silently invalidating an unrelated independently valid observed or mechanical chain.

## 5. Normative Language and Terminology

**MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, and **SHALL NOT** express conformance requirements. **MAY** expresses permission within those requirements.

**Material claim** retains its Evidence Contract meaning: an assertion about data, performance, relationship, interpretation, or recommended response that could materially affect the answer or a decision.

**Diagnostic proposition** means the exact structured material meaning proposed for diagnostic evaluation. It includes the claimed relationship or pattern, governed scope, comparison basis, population, period, relevant Metrics or variables, and intended claim class.

**Evidence package** means the governed collection of Required Evidence definitions, Available Evidence, Data Sufficiency result, provenance, execution and validation records, Validated Results, Admissible Evidence, assumptions, limitations, and applicable policy references used to evaluate one diagnostic proposition. It is a logical package, not a new storage object.

**Materially available** means present, accessible, sufficiently complete for the claim, and not missing a component whose absence could change the diagnostic judgment.

**Admissible test** means a pre-specified or governed deterministic analytical method appropriate to the proposition and evidence, executable against the aligned governed population and periods, with deterministic result and validation criteria. R1 does not define the method itself.

**Promotion** means permission to render a hypothesis as a Supported Diagnostic Finding after deterministic `ClaimDecision` authorization. It does not mean causal promotion.

**Non-promotional outcome** means a governed result that withholds a Supported Diagnostic Finding, such as Hypothesis Only, Missing Evidence, External Evidence Required, Tested but Unsupported, Validation Failed, Insufficient Evidence, or Claim Prohibited.

## 6. Diagnostic Claim Taxonomy

The classes below describe semantic meaning, not mandatory runtime states.

| Semantic class | Meaning | Minimum disposition |
|---|---|---|
| Observed Finding | Direct statement of what a validated deterministic result shows within governed scope | May be rendered only through the existing descriptive claim path |
| Mechanical Driver / Contribution | Identity-based or formally defined mathematical decomposition of a measured change | May describe only the governed arithmetic and method |
| Diagnostic Hypothesis | Plausible explanation candidate not yet satisfying promotion requirements | Label as hypothesis; never render as Finding |
| Testable Hypothesis | Hypothesis with defined Required Evidence and an admissible deterministic test | Remains a hypothesis until the test is executed, validated, and authorized |
| Missing-Evidence Hypothesis | Hypothesis whose required material evidence is absent, invalid, ambiguous, or inadmissible | Non-promotional; state the missing or defective evidence |
| Tested but Unsupported Hypothesis | Hypothesis tested with sufficient admissible aligned evidence whose validated result does not meet its governed support criterion | Non-promotional; state that the test did not support it |
| Supported Diagnostic Finding | Bounded diagnostic proposition supported by admissible evidence, an executed and validated deterministic test, and authoritative `ClaimDecision` | May use only bounded non-causal diagnostic language |
| Unsupported Explanation | Explanation lacking one or more required promotion conditions | Must not be written as a Finding |
| External Hypothesis | Hypothesis requiring evidence outside the governed evidence package | External Evidence Required unless governed external evidence is separately admitted |
| Alternative Explanation | Material competing interpretation compatible with current evidence | Preserve its actual evidence status; do not elevate it by format |
| Restricted Causal Claim | Proposition asserting that one factor produced, changed, or uniquely explains another outcome | Prohibited absent a separately governed causal admission standard |

These classes are mutually constraining, not necessarily mutually exclusive labels. For example, an External Hypothesis may also be a Diagnostic Hypothesis; the external-evidence constraint controls its disposition.

## 7. Observed Findings

An Observed Finding states what a validated deterministic result establishes without explaining why it occurred.

Example:

> Revenue decreased from USD 12,000 to USD 10,800.

An Observed Finding MUST:

- use the existing descriptive evidence and `ClaimDecision` path;
- preserve governed Metric, period, population, scope, currency, unit, provenance, and validation semantics;
- make no implicit explanation, customer-intent inference, or causal attribution; and
- remain independently renderable when a downstream diagnostic chain is blocked.

A correct observed result does not satisfy diagnostic Required Evidence by itself.

## 8. Mechanical Findings

### 8.1 Mechanical Driver

A Mechanical Driver is a component of a governed mathematical identity or decomposition. For example, an identity may relate Revenue, Orders, and AOV. Merely observing that Orders and AOV changed is descriptive or mechanical context; it does not identify a business cause.

### 8.2 Mechanical Contribution

A Mechanical Contribution is a value allocated to a component by a formally defined deterministic decomposition method. It MUST:

- reference the authoritative decomposition definition and version;
- preserve the exact scope, comparison periods, population, units, currency, and interaction treatment required by that method;
- originate from deterministic execution and validation;
- reconcile as required by the governed method; and
- be described as method-relative arithmetic.

Permitted form:

> Under the defined decomposition method, the Orders component accounts for X of the measured Revenue change.

The word **contributed** MAY be used only when the statement explicitly identifies a governed mathematical or mechanical decomposition, such as:

> Under the defined decomposition method, the Orders component contributed X to the measured Revenue change.

The following inference is prohibited:

> The decline in Orders caused the Revenue decline.

Mechanical Contribution does not establish motive, market mechanism, intervention effect, causal responsibility, or the underlying reason.

## 9. Diagnostic Hypotheses

A Diagnostic Hypothesis is a candidate explanation proposed before all required support is established.

A hypothesis MUST include or be linkable to:

- a precise proposed relationship or pattern;
- the observed result it seeks to explain;
- intended scope, population, periods, and comparison basis;
- candidate Required Evidence;
- material assumptions and known limitations; and
- its current evidence status.

A hypothesis MUST NOT be presented as a Finding, as the most likely reason, or as a conclusion merely because it is plausible, common in e-commerce, user-suggested, or generated with high model confidence.

Permitted form:

> One possible explanation is a shift toward lower-priced products. This remains a hypothesis until the required product-level evidence is admitted and the specified test is executed and validated.

## 10. Testable Hypotheses

A hypothesis is Testable only when all of the following are defined without material ambiguity:

1. the proposition to be evaluated;
2. the observed result and scope it concerns;
3. the Required Evidence and semantic requirements for every material field;
4. the population and temporal alignment rules;
5. the admissible deterministic test or method reference;
6. the test's governed support and non-support criteria;
7. required validation and reconciliation checks; and
8. the claim class the test could support.

Testability does not establish evidence availability, successful execution, support, admissibility, or permission. If a deterministic test cannot be specified, the hypothesis is not testable and MUST remain non-promotional.

## 11. Tested but Unsupported Hypotheses

CommerceLens MUST distinguish these three states:

| State | Evidence condition | Required statement |
|---|---|---|
| Could not be evaluated | Required material evidence, admissibility, alignment, test, execution, or validation is missing or failed | State why evaluation could not establish a result; do not say the hypothesis was disproved |
| Tested but Unsupported | Sufficient admissible aligned evidence existed, the governed deterministic test executed, its result validated, and the governed support criterion was not met | State that the test did not support the hypothesis within the tested scope; do not say evidence was missing |
| Tested but Unsupported: Contradicted | Sufficient admissible aligned evidence existed, the governed deterministic test executed, its result validated, and the result affirmatively contradicted the proposition | State that the validated test contradicted the proposition within the tested scope; do not classify the outcome as missing evidence, non-execution, or validation failure |

Tested but Unsupported does not necessarily mean false in every population, period, or formulation. It means the specific governed test did not support the specific proposition within its governed scope. Evidence that affirmatively contradicts a proposition MUST be reported as contradiction rather than merely missing support.

## 12. Supported Diagnostic Findings

A Supported Diagnostic Finding is a bounded diagnostic-level material claim whose exact proposition has satisfied the promotion rule in Section 19 and received authoritative deterministic `ClaimDecision` permission.

It may establish only the diagnostic pattern, relationship, association, segment difference, or interpretation actually supported by the governed method and evidence.

> Supported Diagnostic Finding != Identified Cause

A Supported Diagnostic Finding MUST:

- retain its observed descriptive basis;
- name or trace to the tested diagnostic proposition;
- remain within the tested population, periods, scope, Metrics, and method;
- disclose material qualifications and limitations attached by `ClaimDecision`;
- preserve materially admissible competing interpretations; and
- use non-causal wording.

Permitted forms include:

> The observed product-mix shift is consistent with the decline in AOV.

> The available evidence supports a diagnostic association between the product-mix shift and the observed AOV decline.

> A product-mix pattern was observed alongside the decline in AOV within the tested scope.

A Supported Diagnostic Finding MUST NOT be rendered as the reason, main reason, primary cause, most likely reason, or identified cause unless a separate future causal admission standard explicitly authorizes that distinct claim.

## 13. Unsupported Explanations

An explanation is Unsupported when any required promotion condition is false, failed, unresolved, or not applicable in a way that blocks the claim. This includes explanations based only on plausibility, generic business knowledge, user expectation, field names, raw correlations, unvalidated outputs, or LLM confidence.

An Unsupported Explanation MAY be retained as an explicitly labeled hypothesis when doing so is useful and its provenance and evidence status remain clear. It MUST NOT:

- be placed under Findings;
- be phrased as an established explanation;
- justify a stronger claim or Recommendation;
- inherit support from a different proposition; or
- be rescued by a disclaimer after causal or factual wording has already been asserted.

## 14. External Hypotheses

An External Hypothesis depends materially on evidence outside the current governed evidence package, such as competitor promotions, macroeconomic conditions, consumer confidence, external demand shifts, or competitor pricing.

The default transition is:

```text
External Hypothesis
→ External Evidence Required
→ remains unsupported
```

CommerceLens MUST NOT automatically browse, acquire, admit, or treat public information as governed evidence. External evidence acquisition and its future admission standard are outside R1.

Permitted form:

> This hypothesis requires governed external evidence that is not currently available.

User-provided external context remains User-provided Context unless it independently satisfies the applicable governed evidence requirements. It MUST NOT silently become a validated diagnostic Finding.

## 15. Alternative Explanations

### 15.1 Mandatory check

Every proposed Supported Diagnostic Finding MUST undergo an Alternative Explanation Check before promotion:

> Does the current admissible evidence materially permit another competing interpretation of the same observed result?

A competing interpretation is material when accepting it could change the claim's meaning, strength, uniqueness, decision relevance, or required next evidence.

### 15.2 Conditional generation

If the answer is **yes**, CommerceLens MUST preserve each identified material competing interpretation at its actual evidence status, weaken uniqueness or primacy language as needed, and refuse to declare one unique or primary cause without separate justification.

If the answer is **no**, the check is complete when CommerceLens records or can establish that no material competing interpretation was identified under the governed evidence. CommerceLens MUST NOT invent an alternative merely to populate a response format.

Therefore:

> Mandatory Alternative Explanation Check != Mandatory Alternative Explanation Generation

An alternative is not “anything the model can imagine.” It must be materially compatible with the current evidence or arise from a documented unresolved evidence ambiguity. Alternative Explanations remain separate hypothesis artifacts unless distinct Admissible Evidence and `ClaimDecision` authorize them as Findings.

## 16. Causal Claim Boundary

Causal claims form a restricted, separately admitted class:

```text
Descriptive / Mechanical / Diagnostic
────────────────────────────────────
CAUSAL BOUNDARY
────────────────────────────────────
Separate causal identification standard required
```

The diagnostic workflow MUST NOT be represented as `Observed -> Mechanical -> Diagnostic -> Causal`. Diagnostic support does not accumulate into causal permission.

The following do not by themselves identify causality:

- historical transactional data;
- temporal sequence;
- correlation or association;
- statistical significance;
- segment differences;
- concentration;
- mathematical decomposition;
- predictive performance;
- elimination of some alternatives; or
- a high LLM confidence statement.

Causal wording, including **caused**, **led to**, **resulted in**, **because of**, **due to**, and **drove**, MUST be refused unless a separately governed causal identification and admission standard exists and is satisfied. R1 neither defines nor authorizes such a standard.

## 17. Diagnostic Evidence Requirements

Required Evidence MUST be defined for the exact diagnostic proposition, claim class, scope, population, periods, method, and intended material use. A generic list of columns is insufficient.

At minimum, the evidence requirement MUST specify and evaluate:

| Dimension | Required question |
|---|---|
| Relevance | Does the evidence bear directly on the exact diagnostic proposition? |
| Semantic validity | Do fields and values mean what the proposition and method require? |
| Source authority | Is the source authorized for this material use? |
| Completeness | Are material records, periods, entities, and values sufficiently complete? |
| Temporal alignment | Do explanatory and outcome evidence cover the governed, comparable time basis required by the test? |
| Population alignment | Do evidence and outcome refer to the same governed population or an explicitly valid relationship between populations? |
| Metric compatibility | Are authoritative Metric definitions, exclusions, aggregation rules, and intended uses compatible? |
| Unit and currency compatibility | Are units and currencies known, governed, and comparable where material? |
| Measurement validity | Does the evidence measure the intended concept rather than a proxy with undisclosed limitations? |
| Missingness | Is missingness measured and non-blocking for the intended claim? |
| Provenance | Can evidence be traced to dataset, transformation, execution, validation, and claim use? |
| Validation status | Have all applicable deterministic checks passed for the intended use? |

Additional proposition-specific dimensions MAY be required. Omitting a material dimension blocks promotion.

> Field exists != Required Evidence satisfied

For example, a field named `discount` does not establish whether it is a percentage or absolute amount, which gross or list price it references, which transactions are eligible, how refunds are handled, whether semantics are stable across periods, or whether missing values are material. Until those requirements are governed and satisfied, the field cannot authorize a discount explanation.

## 18. Evidence Admissibility

Diagnostic evidence is admissible for a proposition only when the existing Evidence Contract requirements and all proposition-specific requirements in Section 17 are satisfied.

The evaluator MUST distinguish:

- evidence that exists from evidence that is materially available;
- materially available evidence from Admissible Evidence;
- a Validated Result from evidence admissible for diagnostic use;
- evidence admissible for one proposition from evidence admissible for another; and
- a non-blocking qualification from a blocking gap.

Evidence admissibility MUST be proposition- and intended-use-specific. A validated descriptive result MAY be a required basis for a diagnostic test but MUST NOT alone authorize the diagnostic proposition. Equal values, similar field names, or evidence from a different request, dataset, period, population, scope, execution, validation chain, or policy version MUST NOT substitute authority.

Contradictory evidence MUST remain visible. When admissible evidence contains an unresolved material contradiction, promotion is blocked with an explicit **Contradictory Evidence**, **Conflicting Evidence**, or semantically equivalent governed disposition. It MUST NOT be classified merely as Missing Evidence. An independently complete narrower proposition may proceed only when it excludes the contradiction and is explicitly scoped accordingly.

## 19. Hypothesis Promotion Rules

### 19.1 Promotion predicate

A Diagnostic Hypothesis may be promoted to a Supported Diagnostic Finding if and only if every condition below is true for the exact proposition:

```text
P = RE_DEFINED
    AND RE_MATERIALLY_AVAILABLE
    AND EVIDENCE_ADMISSIBLE
    AND SEMANTICS_VALID
    AND PERIOD_ALIGNED
    AND POPULATION_ALIGNED
    AND METRIC_UNIT_CURRENCY_COMPATIBLE
    AND MEASUREMENT_VALID
    AND PROVENANCE_COMPLETE
    AND TEST_GOVERNED
    AND TEST_EXECUTED
    AND TEST_RESULT_VALIDATED
    AND SUPPORT_CRITERION_MET
    AND MATERIAL_CONTRADICTION_ABSENT
    AND ALTERNATIVE_CHECK_COMPLETED
    AND CLAIM_REPRESENTABLE
    AND CLAIMDECISION_AUTHORIZES
```

All terms are Boolean admission conditions, not confidence scores. **Promotion is permitted only when `P = true`.** If any condition is false or unresolved, promotion is prohibited.

`CLAIMDECISION_AUTHORIZES` means the existing authoritative deterministic `ClaimDecision` mechanism, under a future separately approved diagnostic policy, returns an admissible decision for the exact structured proposition and evidence references. R1 does not authorize the current v0.2.0 policy to do so.

### 19.2 Deterministic decision order

Evaluators MUST apply the following precedence so identical material inputs produce the same material outcome:

1. **Restricted or unsupported claim class:** if causal permission is requested without a separately governed causal standard, output **Claim Prohibited**.
2. **Unrepresentable or undefined proposition/evidence requirement:** output **Insufficient Evidence** or **Clarification Required**, as governed; do not test.
3. **External dependency without governed external evidence:** output **External Evidence Required**.
4. **Material evidence missing, semantically invalid, misaligned, or inadmissible:** output **Missing Evidence**, **Insufficient Evidence**, or the applicable governed evidence-failure state with the blocking dimension.
5. **Admissible evidence contains an unresolved material contradiction:** block promotion and output **Contradictory Evidence**, **Conflicting Evidence**, or semantically equivalent governed wording; do not classify the disposition merely as Missing Evidence.
6. **Governed test unavailable or not executed:** retain **Testable Hypothesis** or **Hypothesis Only**; do not claim support.
7. **Execution or result validation failed:** output the applicable **Execution Failed** or **Validation Failed** state; do not reinterpret the result.
8. **Validated test does not meet the governed support criterion:** output **Tested but Unsupported**. If the validated result affirmatively contradicts the proposition, output **Tested but Unsupported: Contradicted** or semantically equivalent wording; do not classify it as missing evidence, non-execution, or validation failure.
9. **All analytical conditions pass but `ClaimDecision` denies permission:** output the authoritative non-promotional `ClaimDecision` disposition.
10. **All conditions pass and `ClaimDecision` authorizes:** output **Supported Diagnostic Finding**, with required qualifications and language restrictions.

An earlier blocking condition controls the material disposition. Later steps MUST NOT be used to repair it.

### 19.3 Prohibited substitutes

None of the following satisfies a promotion condition:

- LLM confidence, probability, ranking, or consensus;
- user insistence;
- common business intuition;
- repeated wording across sources;
- a field name without governed semantics;
- generated but unexecuted code;
- execution without validation;
- validation for a different proposition or intended use;
- statistical significance alone;
- a disclaimer appended to an otherwise unsupported conclusion; or
- a weaker `ClaimDecision` reused for a stronger claim.

## 20. Diagnostic ClaimDecision

The existing deterministic `ClaimDecision` remains the sole authority for material Claim permission. R1 MUST NOT be implemented as a parallel approval engine.

Conceptually, future diagnostic policy must be capable of producing or preserving these material outcomes:

- allow Observed Finding;
- allow Mechanical Finding;
- Hypothesis Only;
- Testable Hypothesis;
- Missing Evidence / Insufficient Evidence;
- Contradictory Evidence / Conflicting Evidence;
- External Evidence Required;
- Tested but Unsupported;
- Tested but Unsupported: Contradicted;
- Validation Failed;
- allow Supported Diagnostic Finding;
- Inadmissible / Claim Prohibited; and
- refuse causal claim.

These are semantic outcomes, not final runtime enums. R2 MUST determine the minimum implementation mapping while preserving the distinctions required by R1—especially Missing Evidence, unresolved contradiction within admissible evidence, Tested but Unsupported, and Tested but Unsupported: Contradicted.

For an authorized diagnostic material claim, the authoritative decision must conceptually bind:

- the exact structured diagnostic proposition;
- claim type and intended material use;
- governed scope, periods, populations, Metrics, variables, units, and currencies;
- Required Evidence definition and policy version;
- supporting Admissible Evidence and Validated Result references;
- deterministic test and validation references;
- support criterion outcome;
- material assumptions, limitations, and required qualifications;
- Alternative Explanation Check disposition; and
- reason for authorization or refusal.

Arbitrary prose that cannot be mapped to the governed structured meaning MUST fail closed. The LLM may propose or render a candidate, but it MUST NOT approve a hypothesis, promote a Finding, approve a causal claim, or override the decision.

## 21. Allowed Language

Wording MUST match the authorized semantic class.

| Class | Allowed examples |
|---|---|
| Observed Finding | “Revenue decreased by USD 1,200.” |
| Mechanical context | “Orders and AOV both declined during the comparison period.” |
| Mechanical Contribution | “Under the defined decomposition method, the Orders component accounts for X of the measured Revenue change.” |
| Diagnostic Hypothesis | “One possible explanation is a shift toward lower-priced products.” |
| Testable Hypothesis | “This hypothesis can be tested using the defined product-level evidence and method; it has not yet been tested.” |
| Missing Evidence | “Product mix cannot currently be tested because required product-level evidence is unavailable.” |
| Tested but Unsupported | “The governed test did not support the discounting hypothesis within the tested scope.” |
| Supported Diagnostic Finding | “The observed product-mix shift is consistent with the decline in AOV.” |
| Supported Diagnostic Finding | “The available evidence supports a diagnostic association between the product-mix shift and the observed AOV decline.” |
| Supported Diagnostic Finding | “A product-mix pattern was observed alongside the decline in AOV within the tested scope.” |
| External Hypothesis | “This hypothesis requires governed external evidence that is not currently available.” |
| Insufficient Evidence | “Insufficient evidence to conclude whether discounting is associated with the observed decline.” |
| Causal refusal | “The available diagnostic evidence does not identify a cause.” |

Words such as **consistent with**, **associated with**, **coincided with**, **observed alongside**, and **diagnostic pattern involving** are permitted only when they accurately describe an authorized diagnostic proposition. They are not generic safe-harbor phrases. Unsupported content remains unsupported even when softened. R1 v1 does not authorize a Supported Diagnostic Finding to state that one factor **explains** another or is **the explanation**.

## 22. Forbidden and Restricted Language

Unless a separately governed causal admission standard explicitly authorizes the exact claim, diagnostic output MUST NOT use:

- caused;
- led to;
- resulted in;
- because of;
- due to;
- drove;
- explains;
- was the explanation;
- the reason was;
- main cause;
- primary cause;
- most likely reason;
- customers preferred;
- customers wanted;
- demand weakened;
- competition intensified;
- the economy caused; or
- equivalent wording that materially implies causal mechanism, motive, uniqueness, or primacy.

In R1 v1, **contributed to** is prohibited for diagnostic explanations. It is permitted only for an explicitly identified governed mathematical or mechanical decomposition under Section 8. A future attribution methodology requires separate governance before diagnostic use of that phrase.

CommerceLens MUST NOT invent or report:

- confidence percentages;
- probabilities;
- evidence-strength scores;
- “high/medium/low confidence” labels;
- statistical certainty not produced by a governed reproducible method; or
- comparative likelihood such as “most likely” without a separately governed ranking and admission methodology.

Customer intent, preference, motivation, market behavior, and external conditions MUST remain hypotheses unless directly supported by admissible evidence appropriate to those claims.

## 23. Semantic Transition Model

R1 defines the following conceptual model only:

```text
Observed Finding
      ↓
Diagnostic Hypothesis
      ↓
Required Evidence and admissible test defined
      ↓
Testable Hypothesis
      ↓
Evidence admitted and deterministic test executed
      ↓
Validated result
      ├── support criterion met + ClaimDecision authorizes
      │       → Supported Diagnostic Finding
      ├── support criterion not met
      │       → Tested but Unsupported
      ├── result contradicts proposition
      │       → Tested but Unsupported: Contradicted
      └── validation or permission fails
              → Validation Failed / Inadmissible

Branches before testing:
Missing Evidence / Contradictory Evidence / External Evidence Required /
Insufficient Evidence / Clarification Required / Claim Prohibited
```

Mechanical Findings are a parallel governed class derived from validated decomposition, not a required step in every diagnostic inquiry. The Causal Boundary is outside this transition model. R2 MUST NOT copy this diagram into a runtime state machine without separately determining the minimum necessary implementation model.

## 24. Fail-Closed Conditions

The affected diagnostic chain MUST fail closed when any of the following applies:

- Required Evidence is undefined;
- Required Evidence is materially unavailable;
- evidence semantics or mapping are ambiguous;
- comparison periods are invalid or materially non-comparable;
- evidence and outcome populations are mismatched;
- material source coverage is incomplete;
- unit or currency is unknown, inconsistent, or mismatched where material;
- measurement semantics are unclear or invalid;
- material missingness is unresolved;
- provenance or source authority is insufficient;
- the deterministic test is undefined, unavailable, or not executed;
- execution fails;
- applicable validation fails or remains unresolved;
- admissible evidence contains an unresolved material contradiction, in which case promotion is blocked with an explicit contradiction or conflicting-evidence disposition rather than Missing Evidence;
- a governed deterministic test affirmatively contradicts the hypothesis, in which case the disposition is **Tested but Unsupported: Contradicted** or semantically equivalent wording;
- only association evidence exists but causal wording is requested;
- an External Hypothesis lacks governed external evidence;
- multiple material interpretations remain but the proposed claim asserts a unique or primary cause;
- required evidence, fields, results, confidence, or context are fabricated or inferred from nonexistent data;
- a material Claim cannot be structurally represented;
- `ClaimDecision` does not authorize the exact claim; or
- the requested wording exceeds the authorized claim class.

The default material response is **“Insufficient evidence to conclude.”** or the more specific governed non-promotional outcome determined by Section 19.2. When admissible evidence conflicts or a validated test affirmatively contradicts the proposition, the applicable contradiction disposition MUST be preserved and MUST NOT collapse into generic insufficiency. A failure MUST NOT be silently downgraded into free-form explanatory prose. Accurate Process Statements, missing-evidence details, and independently supported weaker Findings MAY still be reported.

## 25. Evidence Contract Integration

R1 extends, rather than duplicates, the existing Evidence Contract:

```text
Existing Evidence Contract
→ proposition-specific diagnostic Required Evidence
→ diagnostic evidence admissibility
→ deterministic test and validation
→ diagnostic Claim admissibility
→ ClaimDecision
```

Existing authority remains responsible for Business Question, scope, Metric definitions, Data Sufficiency, provenance, execution, validation, Validated Results, Admissible Evidence, assumptions, limitations, Alternative Explanations, auditability, reproducibility, and retained-evidence integrity.

R1 adds only the diagnostic constraints needed to determine:

- what evidence an exact diagnostic proposition requires;
- whether that evidence is semantically and contextually fit for diagnostic use;
- whether a governed deterministic test supports that proposition; and
- which diagnostic wording the resulting `ClaimDecision` permits.

Every Supported Diagnostic Finding MUST remain traceable through the existing lineage to its Business Question, scope, Required Evidence, dataset, Metric or method references, execution, validation, Validated Results, Admissible Evidence, and authoritative `ClaimDecision`.

## 26. ClaimDecision Integration

R1 preserves these boundaries:

```text
LLM / Skill proposes structured hypothesis or ClaimCandidate
→ governed evidence and deterministic test path
→ deterministic ClaimDecision
→ authorized rendering or non-promotional outcome
```

`ClaimDecision` MUST remain the final material permission gate. Diagnostic policy MUST NOT recompute Metrics, redefine decomposition, act as a second statistical validator, or use an LLM-as-judge. It MUST evaluate explicit governed policy against authentic evidence and test authority.

The current P8 v0.2.0 policy supports positive permission for `ClaimType.DESCRIPTIVE` only. R1 specifies future diagnostic behavior but does not change that implementation fact or authorize a policy update.

## 27. v0.2.0 Compatibility

Current behavior is conforming:

> Insufficient evidence to conclude why Revenue declined.

R1 MUST NOT classify this refusal as defective. v0.2.0 correctly permits an independently supported descriptive Revenue Change while refusing positive diagnostic permission with an Inadmissible `ClaimDecision`.

Future structured resolution may add detail without weakening refusal safety:

```text
Observed:
Revenue declined.

Mechanical:
Orders and AOV both declined.

Diagnostic:
Product mix cannot currently be tested because required product-level evidence
is unavailable.

Next required evidence:
Governed product identifier, selling price, quantity, and period evidence.

Conclusion:
Insufficient evidence to conclude the underlying reason.
```

The improvement target is more structured diagnostic resolution, not fewer refusals. Until a later approved implementation satisfies R1 and updates diagnostic `ClaimDecision` policy, positive diagnostic explanations remain unsupported.

## 28. Deterministic Enforcement Boundaries

The following future controls MUST NOT depend on unrestricted LLM judgment:

- KPI values and Metric semantics;
- comparison-period validity and alignment;
- eligible populations and population alignment;
- decomposition definitions and arithmetic;
- required-field availability;
- schema and semantic-mapping validity;
- source authority and provenance;
- evidence alignment and completeness checks;
- data-quality and missingness checks;
- unit and currency compatibility;
- measurement compatibility where governable;
- test selection from an approved test/method registry;
- test execution and statistical computation;
- reconciliation and result validation;
- support-criterion evaluation;
- causal-class prohibition;
- structured wording-class eligibility;
- authentic evidence and result binding; and
- `ClaimDecision` eligibility and permission.

The LLM MAY:

- propose hypothesis candidates;
- explain a hypothesis without promoting it;
- propose candidate evidence requirements for deterministic/governed approval;
- propose next analytical tests from approved capabilities;
- identify candidate Alternative Explanations for the mandatory check; and
- render user-facing language within the exact authorized class and qualifications.

The LLM MUST NOT invent evidence, fields, test results, confidence values, probabilities, or causal authority; approve its own hypothesis; promote a Finding; or override a deterministic outcome.

## 29. Evaluation Requirements

### 29.1 Evaluator input

Conformance evaluation MUST provide both evaluators the same:

- structured claim or hypothesis;
- requested wording and claim class;
- governed scope, populations, periods, Metrics, units, and currencies;
- Required Evidence definition;
- Available and Admissible Evidence states;
- provenance and validation state;
- deterministic test definition, execution state, result, and support criterion;
- material assumptions, limitations, contradictions, and competing interpretations;
- `ClaimDecision` policy version and result; and
- expected materiality boundary.

If these inputs differ, different judgments do not establish evaluator inconsistency.

### 29.2 Required consistency tests

A conforming evaluator MUST pass all of the following:

1. **Classification consistency:** classify the same material proposition into the same controlling semantic class.
2. **Promotion consistency:** apply Section 19 and agree whether promotion is permitted.
3. **Language consistency:** permit bounded wording such as “consistent with” only for an authorized proposition and prohibit unauthorized causal wording such as “caused.”
4. **Fail-closed consistency:** produce non-promotion when any blocking condition is missing, invalid, failed, or unresolved.
5. **External-evidence consistency:** keep External Hypotheses unsupported without admitted governed external evidence.
6. **Alternative-explanation consistency:** complete an Alternative Explanation Check before every proposed Supported Diagnostic Finding is promoted, preserve material competing interpretations, prohibit unique-cause language when more than one remains admissible, and do not fabricate an alternative when none is identified under the governed evidence.
7. **Missing-versus-tested-versus-contradicted consistency:** distinguish inability to evaluate, unresolved contradiction within admissible evidence, a completed test that did not support the hypothesis, and a validated test that affirmatively contradicted the proposition.
8. **Mechanical-versus-causal consistency:** permit governed decomposition language without treating it as business causality.
9. **Association consistency:** refuse automatic diagnostic or causal promotion from association alone.
10. **Backward compatibility:** treat current v0.2.0 diagnostic refusal as conforming.

### 29.3 Material judgment record

For each case, an evaluator MUST produce a reviewable record containing:

- semantic classification;
- each promotion-predicate condition as pass, fail, or not applicable with reason;
- controlling non-promotional outcome, if any;
- permitted claim strength;
- permitted and prohibited wording class;
- additional evidence required, if any;
- Alternative Explanation Check result;
- causal-boundary result; and
- final `ClaimDecision` disposition or required future decision.

Conformance concerns material judgment, not identical prose. Two evaluators may use different wording only when both wordings remain within the same authorized class, scope, qualifications, and evidence status.

## 30. Future Fixture Requirements

R5 SHOULD create synthetic cases covering at least:

1. observed result only;
2. mechanical decomposition only;
3. Diagnostic Hypothesis with missing evidence;
4. fully specified Testable Hypothesis before execution;
5. Supported Diagnostic Finding;
6. Tested but Unsupported Hypothesis;
7. contradicted hypothesis;
8. multiple supported diagnostic patterns with no unique explanation;
9. External Hypothesis without admitted external evidence;
10. causal-language trap;
11. diagnostic “contributed to” trap;
12. customer-intent inference trap;
13. unsupported confidence-score or probability trap;
14. nonexistent-field hallucination trap;
15. Alternative Explanation required;
16. Alternative Explanation Check completed with no generation justified;
17. field-present-but-semantically-invalid evidence;
18. temporal-alignment failure;
19. population-alignment failure;
20. unit or currency mismatch;
21. validated association that is insufficient for causal wording;
22. current v0.2.0 diagnostic refusal; and
23. independent observed chain surviving a blocked diagnostic chain.

R1 defines case requirements only. It does not create fixtures, expected runtime enums, or benchmark scoring.

## 31. Risks and Mitigations

| Risk | Governance mitigation | Residual limitation |
|---|---|---|
| Diagnostic claims drift into causal claims | Separate causal boundary, forbidden-language rules, deterministic claim-class eligibility | Natural language can imply causality indirectly; future renderers require conformance review |
| Mechanical decomposition is misread as business causality | Method-relative wording and explicit Mechanical Contribution != Causal Contribution rule | Users may still over-interpret arithmetic without clear presentation |
| Taxonomy becomes overly complex | Semantic vocabulary is not the runtime model; R2 minimizes implementation states | Over-compression in R2 could erase required distinctions |
| Required Evidence becomes a superficial field checklist | Require semantic, temporal, population, measurement, provenance, and validation dimensions | Proposition-specific matrices remain future R3 work |
| Alternative logic causes hallucination | Mandatory check but conditional generation; evidence compatibility required | Some genuine alternatives may remain unknown |
| Statistical association is over-interpreted | Association alone cannot authorize diagnostic uniqueness or causality | A future methods catalog must define claim-specific support criteria |
| LLM language exceeds `ClaimDecision` | Renderer bounded by structured authorized class and qualifications | Arbitrary prose control is not fully designed in R1 |
| R1 expands into R2–R5 | Explicit non-scope and conceptual-only transition model | Later milestones must preserve R1 semantics without copying unnecessary complexity |
| Diagnostic wording is unintentionally causal | Prohibited terms plus material-meaning review, not keyword matching alone | Equivalent causal implications require evaluator coverage |
| Evidence semantics are mistaken for column presence | Explicit `Field exists != Required Evidence satisfied` rule | Semantic validation mechanisms remain future work |

## 32. Open Questions

No unresolved question blocks R1 semantic completion. The following implementation-allocation questions are intentionally deferred:

1. **Minimum R2 runtime representation.** Which semantic distinctions require enums, state transitions, metadata, or presentation-only handling? This matters because Missing Evidence, unresolved contradiction within admissible evidence, Tested but Unsupported, and Tested but Unsupported: Contradicted must remain materially distinguishable without forcing the entire R1 vocabulary into code. It affects R2 only.
2. **R3 evidence-requirement encoding.** How will proposition-specific Required Evidence dimensions and semantic checks be represented without becoming a field checklist? This affects the R3 matrix and later deterministic policy.
3. **Approved diagnostic method registry.** Which deterministic tests, validation rules, and support criteria will be authorized for each future hypothesis family? This affects R3–R5 and cannot be assumed by R1.
4. **Rendered-language enforcement.** What minimum structured templates or post-render checks are needed to ensure user-facing wording does not exceed `ClaimDecision` without introducing an LLM-as-judge? This affects R2 and later integration.

These questions do not reopen any owner-approved R1 decision and do not authorize implementation assumptions.

## 33. Success Criteria and Conformance Checklist

R1 is conforming only when all statements below are true:

- [x] Descriptive, mechanical, diagnostic, and causal classes are explicitly separated.
- [x] Supported Diagnostic Finding is explicitly not equivalent to Identified Cause.
- [x] Diagnostic use of “contributed to” is prohibited in v1.
- [x] Mechanical Contribution is separately governed and method-relative.
- [x] Causal claims sit behind a separate higher-evidence boundary rather than a natural diagnostic progression.
- [x] Hypothesis is not Finding, and LLM plausibility or confidence cannot promote it.
- [x] Missing Evidence, unresolved contradiction within admissible evidence, Tested but Unsupported, and Tested but Unsupported: Contradicted are semantically distinct without requiring separate runtime enums.
- [x] Statistical association alone does not authorize diagnostic or causal promotion.
- [x] Required Evidence evaluates semantics, alignment, measurement, provenance, and validation—not field existence alone.
- [x] Alternative Explanation Check is mandatory before promotion of every proposed Supported Diagnostic Finding.
- [x] Alternative Explanation Generation is conditional and must not be fabricated.
- [x] External Hypotheses remain unsupported without governed admitted external evidence.
- [x] Confidence scores, probabilities, and evidence-strength ratings may not be invented.
- [x] The promotion predicate and deterministic decision precedence are explicit.
- [x] Fail-closed conditions and non-promotional outcomes are explicit.
- [x] Deterministic enforcement points and LLM boundaries are explicit.
- [x] Existing Evidence Contract terminology and lineage are preserved.
- [x] Existing `ClaimDecision` remains the sole material Claim-permission authority.
- [x] Current v0.2.0 diagnostic refusal remains valid and conforming.
- [x] Semantic vocabulary is explicitly not the future R2 runtime state model.
- [x] Evaluator inputs, judgment records, and decision rules are sufficient for two conforming evaluators to reach the same material judgment from the same material evidence.

## 34. Dependencies and Next Milestone

R1 is a specification milestone and requires Main Project Review before downstream implementation work.

Dependencies preserved by this document:

- Frozen Evidence Contract and Architecture semantics remain authoritative;
- current Metric, execution, validation, Evidence, and `ClaimDecision` authority remain unchanged;
- v0.2.0 continues to refuse positive diagnostic claims; and
- P15 does not become a blanket blocker for private future R6 research/design.

R2 may begin only after separate authorization and must define the minimum runtime representation needed to preserve R1 material distinctions. R1 does not authorize R2, R3, R4, R5, or public diagnostic integration.

Future R6 Governed Hypothesis Generation MUST distinguish private **R6 Research / Design** from **R6 Public Product Integration**. Research/design may proceed under its future authorized dependencies; public integration requires its later validation and decision gate. This dependency note does not design R6.

---

**End of R1 Diagnostic Reasoning Specification**
